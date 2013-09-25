# Embedded file name: scripts/client/gui/shared/gui_items/Tankman.py
import pickle
from helpers.i18n import convert
from items import tankmen, vehicles, ITEM_TYPE_NAMES
from gui import nationCompareByIndex
from gui.shared.utils.functions import getShortDescr
from gui.shared.gui_items import HasStrCD, GUIItem, ItemsCollection, _ICONS_MASK
from gui.shared.gui_items.serializers import g_itemSerializer

class TankmenCollection(ItemsCollection):
    """
    Tankmen collection class.
    """

    def _filterItem(self, item, nation = None, role = None, isInTank = None):
        """
        Overriden method to filter collection items.
        
        @param item: item to check fo filtering
        @param nation: nation id to filter
        @param role: tankman role to filter
        @param isInTank: only tankmen in vehicles
        @return: is item match given conditions <bool>
        """
        if role is not None and item.descriptor.role != role:
            return False
        elif isInTank is not None and item.isInTank != isInTank:
            return False
        else:
            return ItemsCollection._filterItem(self, item, nation)


class Tankman(GUIItem, HasStrCD):
    ROLE_ICON_PATH_BIG = '../maps/icons/tankmen/roles/big'
    ROLE_ICON_PATH_SMALL = '../maps/icons/tankmen/roles/small'
    RANK_ICON_PATH_BIG = '../maps/icons/tankmen/ranks/big'
    RANK_ICON_PATH_SMALL = '../maps/icons/tankmen/ranks/small'
    PORTRAIT_ICON_PATH_BIG = '../maps/icons/tankmen/icons/big'
    PORTRAIT_ICON_PATH_SMALL = '../maps/icons/tankmen/icons/small'
    PORTRAIT_ICON_PATH_BARRACKS = '../maps/icons/tankmen/icons/barracks'

    class ROLES:
        """ Tankmen vehicle roles constants. """
        COMMANDER = 'commander'
        RADIOMAN = 'radioman'
        DRIVER = 'driver'
        GUNNER = 'gunner'
        LOADER = 'loader'

    TANKMEN_ROLES_ORDER = {ROLES.COMMANDER: 0,
     ROLES.GUNNER: 1,
     ROLES.DRIVER: 2,
     ROLES.RADIOMAN: 3,
     ROLES.LOADER: 4}

    def __init__(self, strCompactDescr, inventoryID = -1, vehicle = None, proxy = None):
        """
        Ctor.
        
        @param strCompactDescr: string compact descriptor
        @param inventoryID: tankman's inventory id
        @param vehicle: tankman's vehicle where it has been seat
        @param proxy: instance of ItemsRequester
        """
        GUIItem.__init__(self, proxy)
        HasStrCD.__init__(self, strCompactDescr)
        self.__descriptor = None
        self.invID = inventoryID
        self.nationID = self.descriptor.nationID
        self.itemTypeID = vehicles._TANKMAN
        self.itemTypeName = ITEM_TYPE_NAMES[self.itemTypeID]
        self.combinedRoles = (self.descriptor.role,)
        self.vehicleNativeDescr = vehicles.VehicleDescr(typeID=(self.nationID, self.descriptor.vehicleTypeID))
        self.vehicleInvID = -1
        self.vehicleDescr = None
        self.vehicleBonuses = dict()
        self.vehicleSlotIdx = -1
        if vehicle is not None:
            self.vehicleInvID = vehicle.invID
            self.vehicleDescr = vehicle.descriptor
            self.vehicleBonuses = dict(vehicle.bonuses)
            self.vehicleSlotIdx = vehicle.crewIndices.get(inventoryID, -1)
            crewRoles = self.vehicleDescr.type.crewRoles
            if -1 < self.vehicleSlotIdx < len(crewRoles):
                self.combinedRoles = crewRoles[self.vehicleSlotIdx]
        self.skills = self._buildSkills(proxy)
        if proxy is not None:
            pass
        return

    def _buildSkills(self, proxy):
        """
        Returns list of `TankmanSkill` objects build
        according to the tankman's skills.
        """
        return [ TankmanSkill(skill, self, proxy) for skill in self.descriptor.skills ]

    @property
    def realRoleLevel(self):
        """
        Returns real tankman role level calculated with
        bonuses and penalties.
        
        @return: (
                real role level,
                (
                        commander bonus,
                        brotherhood bonus,
                        equipments bonus,
                        optional devices bonus,
                        not native vehicle penalty,
                )
        )
        """
        effRoleLevel = self.efficiencyRoleLevel
        penalty = effRoleLevel - self.roleLevel
        commBonus = self.vehicleBonuses.get('commander', 0)
        if self.descriptor.role == self.ROLES.COMMANDER:
            commBonus = 0
        brothersBonus = self.vehicleBonuses.get('brotherhood', 0)
        eqsBonus = self.vehicleBonuses.get('equipment', 0)
        optDevsBonus = self.vehicleBonuses.get('optDevices', 0)
        realRoleLevel = effRoleLevel + commBonus + brothersBonus + eqsBonus
        return (realRoleLevel, (commBonus,
          brothersBonus,
          eqsBonus,
          optDevsBonus,
          penalty))

    @property
    def descriptor(self):
        if self.__descriptor is None or self.__descriptor.dossierCompactDescr != self.strCompactDescr:
            self.__descriptor = tankmen.TankmanDescr(compactDescr=self.strCompactDescr)
        return self.__descriptor

    @property
    def isInTank(self):
        """ Is tankman in vehicle. """
        return self.vehicleDescr is not None

    @property
    def roleLevel(self):
        """ Tankman's role level. """
        return self.descriptor.roleLevel

    @property
    def icon(self):
        """ Tankman's portrait icon filename. """
        return tankmen.getNationConfig(self.nationID)['icons'][self.descriptor.iconID]

    @property
    def iconRank(self):
        """ Tankman's rank icon filepath. """
        return tankmen.getNationConfig(self.nationID)['ranks'][self.descriptor.rankID]['icon']

    @property
    def iconRole(self):
        """ Tankman's role icon filename. """
        return tankmen.getSkillsConfig()[self.descriptor.role]['icon']

    @property
    def firstUserName(self):
        """ Tankman's firstname represented as user-friendly string. """
        return convert(tankmen.getNationConfig(self.nationID)['firstNames'][self.descriptor.firstNameID])

    @property
    def lastUserName(self):
        """ Tankman's lastname represented as user-friendly string. """
        return convert(tankmen.getNationConfig(self.nationID)['lastNames'][self.descriptor.lastNameID])

    @property
    def rankUserName(self):
        """ Tankman's rank represented as user-friendly string. """
        return convert(tankmen.getNationConfig(self.nationID)['ranks'][self.descriptor.rankID]['userString'])

    @property
    def roleUserName(self):
        """ Tankman's role represented as user-friendly string. """
        return convert(tankmen.getSkillsConfig()[self.descriptor.role]['userString'])

    @property
    def hasNewSkill(self):
        return self.roleLevel == tankmen.MAX_SKILL_LEVEL and (self.descriptor.lastSkillLevel == tankmen.MAX_SKILL_LEVEL or not len(self.skills))

    @property
    def newSkillCount(self):
        """
        Returns number of skills to study and last new skill level.
        
        @return: ( number of new skills, last new skill level )
        """
        if self.hasNewSkill:
            tmanDescr = tankmen.TankmanDescr(self.strCD)
            i = 0
            skills_list = list(tankmen.ACTIVE_SKILLS)
            while tmanDescr.roleLevel == 100 and (tmanDescr.lastSkillLevel == 100 or len(tmanDescr.skills) == 0) and len(skills_list) > 0:
                skillname = skills_list.pop()
                if skillname not in tmanDescr.skills:
                    tmanDescr.addSkill(skillname)
                    i += 1

            return (i, tmanDescr.lastSkillLevel)
        return (0, 0)

    @property
    def efficiencyRoleLevel(self):
        """
        Returns tankman's role level on current vehicle.
        """
        factor, addition = (1, 0)
        if self.isInTank:
            factor, addition = self.descriptor.efficiencyOnVehicle(self.vehicleDescr)
        return round(self.roleLevel * factor + addition)

    def __cmp__(self, other):
        if other is None:
            return -1
        res = nationCompareByIndex(self.nationID, other.nationID)
        if res:
            return res
        elif self.isInTank and not other.isInTank:
            return -1
        elif not self.isInTank and other.isInTank:
            return 1
        if self.isInTank and other.isInTank:
            if self.vehicleInvID != other.vehicleInvID:
                return -1
            res = self.TANKMEN_ROLES_ORDER[self.descriptor.role] - self.TANKMEN_ROLES_ORDER[other.descriptor.role]
            if res:
                return res
        if self.lastUserName < other.lastUserName:
            return -1
        elif self.lastUserName > other.lastUserName:
            return 1
        else:
            return 0

    def __eq__(self, other):
        if other is None or not isinstance(other, Tankman):
            return False
        else:
            return self.invID == other.invID

    def __repr__(self):
        return 'Tankman<id:%d, nation:%d, vehicleID:%d>' % (self.invID, self.nationID, self.vehicleInvID)

    def toDict(self):
        result = GUIItem.toDict(self)

        def vehicleIcon(vDescr, subtype = ''):
            return _ICONS_MASK % {'type': 'vehicle',
             'subtype': subtype,
             'unicName': vDescr.name.replace(':', '-')}

        nativeVehicleData = {'typeCompDescr': self.vehicleNativeDescr.type.compactDescr,
         'userName': self.vehicleNativeDescr.type.shortUserString,
         'icon': vehicleIcon(self.vehicleNativeDescr),
         'iconContour': vehicleIcon(self.vehicleNativeDescr, 'contour/')}
        currentVehicleData = None
        if self.isInTank:
            currentVehicleData = {'inventoryID': self.vehicleInvID,
             'typeCompDescr': self.vehicleDescr.type.compactDescr,
             'userName': self.vehicleDescr.type.shortUserString,
             'icon': vehicleIcon(self.vehicleDescr),
             'iconContour': vehicleIcon(self.vehicleDescr, 'contour/')}
        result.update({'strCD': pickle.dumps(self.strCD),
         'inventoryID': self.invID,
         'nationID': self.nationID,
         'firstUserName': self.firstUserName,
         'lastUserName': self.lastUserName,
         'roleName': self.descriptor.role,
         'rankUserName': self.rankUserName,
         'roleUserName': self.roleUserName,
         'skills': [ g_itemSerializer.pack(skill) for skill in self.skills ],
         'efficiencyRoleLevel': self.efficiencyRoleLevel,
         'realRoleLevel': self.realRoleLevel,
         'roleLevel': self.roleLevel,
         'icon': {'big': '%s/%s' % (self.PORTRAIT_ICON_PATH_BIG, self.icon),
                  'small': '%s/%s' % (self.PORTRAIT_ICON_PATH_SMALL, self.icon),
                  'barracks': '%s/%s' % (self.PORTRAIT_ICON_PATH_BARRACKS, self.icon)},
         'iconRole': {'big': '%s/%s' % (self.ROLE_ICON_PATH_BIG, self.iconRole),
                      'small': '%s/%s' % (self.ROLE_ICON_PATH_SMALL, self.iconRole)},
         'iconRank': {'big': '%s/%s' % (self.RANK_ICON_PATH_BIG, self.iconRank),
                      'small': '%s/%s' % (self.RANK_ICON_PATH_SMALL, self.iconRank)},
         'isInTank': self.isInTank,
         'newSkillsCount': self.newSkillCount,
         'nativeVehicle': nativeVehicleData,
         'currentVehicle': currentVehicleData})
        return result

    def getCtorArgs(self):
        return [self.strCD, self.invID]

    def fromDict(self, d):
        GUIItem.fromDict(self, d)


class TankmanSkill(GUIItem):
    """
    Tankman's skill class.
    """
    ICON_PATH_BIG = '../maps/icons/tankmen/skills/big'
    ICON_PATH_SMALL = '../maps/icons/tankmen/skills/small'

    def __init__(self, skillName, tankman = None, proxy = None):
        super(TankmanSkill, self).__init__(proxy)
        self.name = skillName
        self.isPerk = self.name in tankmen.PERKS
        self.level = 0
        self.roleType = None
        self.isActive = False
        self.isEnable = False
        if tankman is not None:
            tdescr = tankman.descriptor
            self.level = tdescr.lastSkillLevel if tdescr.skills.index(self.name) == len(tdescr.skills) - 1 else tankmen.MAX_SKILL_LEVEL
            self.roleType = self.__getSkillRoleType(skillName)
            self.isActive = self.__getSkillActivity(tankman)
            self.isEnable = self.__getEnabledSkill(tankman)
        return

    def __getEnabledSkill(self, tankman):
        for role in tankman.combinedRoles:
            roleSkills = tankmen.SKILLS_BY_ROLES.get(role, tuple())
            if self.name in roleSkills:
                return True

        return False

    def __getSkillRoleType(self, skillName):
        if skillName in tankmen.COMMON_SKILLS:
            return 'common'
        else:
            for role, skills in tankmen.SKILLS_BY_ROLES.iteritems():
                if skillName in skills:
                    return role

            return None

    def __getSkillActivity(self, tankman):
        """
        Returns skill activity. Skill is active in following cases:
         1. skill is not perk;
         2. skill is `brotherhood` skill and it is active on tankman's vehicle;
         3. skill is onot `brotherhood` and it is researched to max.
        """
        if tankman is None:
            return True
        else:
            isBrotherhood = tankman.vehicleBonuses.get('brotherhood', 0) > 0
            return not self.isPerk or self.name == 'brotherhood' and isBrotherhood or self.name != 'brotherhood' and self.level == tankmen.MAX_SKILL_LEVEL

    @property
    def userName(self):
        """ Returns skill name represented as user-friendly string. """
        return tankmen.getSkillsConfig()[self.name]['userString']

    @property
    def description(self):
        """ Returns skill description represented as user-friendly string. """
        return convert(tankmen.getSkillsConfig()[self.name]['description'])

    @property
    def shortDescription(self):
        """ Returns skill short description represented as user-friendly string. """
        return getShortDescr(self.description)

    @property
    def icon(self):
        """ Returns skill icon filename. """
        return convert(tankmen.getSkillsConfig()[self.name]['icon'])

    def __repr__(self):
        return 'TankmanSkill<name:%s, level:%d, isActive:%s>' % (self.name, self.level, str(self.isActive))

    def toDict(self):
        result = GUIItem.toDict(self)
        roleIcon = 'noImage.png'
        if self.roleType in tankmen.getSkillsConfig():
            roleIcon = tankmen.getSkillsConfig()[self.roleType]['icon']
        result.update({'name': self.name,
         'level': self.level,
         'userName': self.userName,
         'description': self.description,
         'shortDescription': self.shortDescription,
         'icon': {'big': '%s/%s' % (self.ICON_PATH_BIG, self.icon),
                  'small': '%s/%s' % (self.ICON_PATH_SMALL, self.icon),
                  'role': '%s/%s' % (Tankman.ROLE_ICON_PATH_SMALL, roleIcon)},
         'isActive': self.isActive,
         'isEnable': self.isEnable,
         'roleType': self.roleType,
         'isPerk': self.isPerk})
        return result

    def getCtorArgs(self):
        return [self.name]

    def fromDict(self, d):
        GUIItem.fromDict(self, d)
        self.level = d.get('level', 0)
        self.isActive = d.get('isActive', True)
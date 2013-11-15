# 2013.11.15 11:26:47 EST
# Embedded file name: scripts/client/gui/shared/gui_items/__init__.py
import BigWorld
from debug_utils import *
from helpers import i18n
from items import ITEM_TYPE_NAMES, vehicles, getTypeInfoByName, ITEM_TYPE_INDICES
from gui import nationCompareByIndex, GUI_SETTINGS
from gui.shared.utils import ItemsParameters, CONST_CONTAINER
from gui.shared.utils.functions import getShortDescr, stripShortDescrTags
CLAN_LOCK = 1
_ICONS_MASK = '../maps/icons/%(type)s/%(subtype)s%(unicName)s.png'
GUI_ITEM_TYPE_NAMES = tuple(ITEM_TYPE_NAMES) + tuple(['reserved'] * (16 - len(ITEM_TYPE_NAMES)))
GUI_ITEM_TYPE_NAMES += ('dossierAccount', 'dossierVehicle', 'dossierTankman', 'achievement', 'tankmanSkill')
GUI_ITEM_TYPE_INDICES = dict(((n, idx) for idx, n in enumerate(GUI_ITEM_TYPE_NAMES)))

class GUI_ITEM_TYPE(CONST_CONTAINER):
    VEHICLE = GUI_ITEM_TYPE_INDICES['vehicle']
    CHASSIS = GUI_ITEM_TYPE_INDICES['vehicleChassis']
    TURRET = GUI_ITEM_TYPE_INDICES['vehicleTurret']
    GUN = GUI_ITEM_TYPE_INDICES['vehicleGun']
    ENGINE = GUI_ITEM_TYPE_INDICES['vehicleEngine']
    FUEL_TANK = GUI_ITEM_TYPE_INDICES['vehicleFuelTank']
    RADIO = GUI_ITEM_TYPE_INDICES['vehicleRadio']
    TANKMAN = GUI_ITEM_TYPE_INDICES['tankman']
    OPTIONALDEVICE = GUI_ITEM_TYPE_INDICES['optionalDevice']
    SHELL = GUI_ITEM_TYPE_INDICES['shell']
    EQUIPMENT = GUI_ITEM_TYPE_INDICES['equipment']
    COMMON = tuple(ITEM_TYPE_INDICES.keys())
    ARTEFACTS = (EQUIPMENT, OPTIONALDEVICE)
    ACCOUNT_DOSSIER = GUI_ITEM_TYPE_INDICES['dossierAccount']
    VEHICLE_DOSSIER = GUI_ITEM_TYPE_INDICES['dossierVehicle']
    TANKMAN_DOSSIER = GUI_ITEM_TYPE_INDICES['dossierTankman']
    ACHIEVEMENT = GUI_ITEM_TYPE_INDICES['achievement']
    SKILL = GUI_ITEM_TYPE_INDICES['tankmanSkill']
    GUI = (ACCOUNT_DOSSIER,
     VEHICLE_DOSSIER,
     TANKMAN_DOSSIER,
     ACHIEVEMENT,
     SKILL)
    VEHICLE_MODULES = (GUN,
     TURRET,
     ENGINE,
     CHASSIS,
     RADIO)
    VEHICLE_COMPONENTS = VEHICLE_MODULES + ARTEFACTS + (SHELL,)


class ItemsCollection(dict):

    def filter(self, criteria):
        result = self.__class__()
        for intCD, item in self.iteritems():
            if criteria(item):
                result.update({intCD: item})

        return result

    def __repr__(self):
        return '%s<size:%d>' % (self.__class__.__name__, len(self.items()))


def getVehicleComponentsByType(vehicle, itemTypeIdx):
    """
    Returns collection of vehicle's installed items.
    
    @param vehicle: target vehicle
    @param itemTypeIdx: items.ITEM_TYPE_NAMES index
    
    @return: ItemsCollection instance
    """

    def packModules(modules):
        """ Helper function to pack item ot items list to the collection """
        if not isinstance(modules, list):
            modules = [modules]
        return ItemsCollection([ (module.intCD, module) for module in modules if module is not None ])

    if itemTypeIdx == vehicles._CHASSIS:
        return packModules(vehicle.chassis)
    if itemTypeIdx == vehicles._TURRET:
        return packModules(vehicle.turret)
    if itemTypeIdx == vehicles._GUN:
        return packModules(vehicle.gun)
    if itemTypeIdx == vehicles._ENGINE:
        return packModules(vehicle.engine)
    if itemTypeIdx == vehicles._FUEL_TANK:
        return packModules(vehicle.fuelTank)
    if itemTypeIdx == vehicles._RADIO:
        return packModules(vehicle.radio)
    if itemTypeIdx == vehicles._TANKMAN:
        from gui.shared.gui_items.Tankman import TankmenCollection
        return TankmenCollection([ (t.invID, t) for slotIdx, t in vehicle.crew ])
    if itemTypeIdx == vehicles._OPTIONALDEVICE:
        return packModules(vehicle.optDevices)
    if itemTypeIdx == vehicles._SHELL:
        return packModules(vehicle.shells)
    if itemTypeIdx == vehicles._EQUIPMENT:
        return packModules(vehicle.eqs)
    return ItemsCollection()


def getVehicleSuitablesByType(vehDescr, itemTypeId, turretPID = 0):
    """
    Returns all suitable items for given @vehicle.
    
    @param vehDescr: vehicle descriptor
    @param itemTypeId: requested items types
    @param turretPID: vehicle's turret id
    
    @return: ( descriptors list, current vehicle's items compact descriptors list )
    """
    descriptorsList = list()
    current = list()
    if itemTypeId == vehicles._CHASSIS:
        current = [vehDescr.chassis['compactDescr']]
        descriptorsList = vehDescr.type.chassis
    elif itemTypeId == vehicles._ENGINE:
        current = [vehDescr.engine['compactDescr']]
        descriptorsList = vehDescr.type.engines
    elif itemTypeId == vehicles._RADIO:
        current = [vehDescr.radio['compactDescr']]
        descriptorsList = vehDescr.type.radios
    elif itemTypeId == vehicles._FUEL_TANK:
        current = [vehDescr.fuelTank['compactDescr']]
        descriptorsList = vehDescr.type.fuelTanks
    elif itemTypeId == vehicles._TURRET:
        current = [vehDescr.turret['compactDescr']]
        descriptorsList = vehDescr.type.turrets[turretPID]
    elif itemTypeId == vehicles._OPTIONALDEVICE:
        devs = vehicles.g_cache.optionalDevices()
        current = vehDescr.optionalDevices
        descriptorsList = [ dev for dev in devs.itervalues() if dev.checkCompatibilityWithVehicle(vehDescr)[0] ]
    elif itemTypeId == vehicles._EQUIPMENT:
        eqs = vehicles.g_cache.equipments()
        current = list()
        descriptorsList = [ eq for eq in eqs.itervalues() if eq.checkCompatibilityWithVehicle(vehDescr)[0] ]
    elif itemTypeId == vehicles._GUN:
        current = [vehDescr.gun['compactDescr']]
        for gun in vehDescr.turret['guns']:
            descriptorsList.append(gun)

        for turret in vehDescr.type.turrets[turretPID]:
            if turret is not vehDescr.turret:
                for gun in turret['guns']:
                    descriptorsList.append(gun)

    elif itemTypeId == vehicles._SHELL:
        for shot in vehDescr.gun['shots']:
            current.append(shot['shell']['compactDescr'])

        for gun in vehDescr.turret['guns']:
            for shot in gun['shots']:
                descriptorsList.append(shot['shell'])

        for turret in vehDescr.type.turrets[turretPID]:
            if turret is not vehDescr.turret:
                for gun in turret['guns']:
                    for shot in gun['shots']:
                        descriptorsList.append(shot['shell'])

    return (descriptorsList, current)


class GUIItem(object):
    """
    Root gui items class. Provides common interface for
    serialization and deserialization.
    """

    def __init__(self, proxy = None):
        pass

    def toDict(self):
        """ Returns dict representation of vital object data """
        return dict()

    def fromDict(self, d):
        """
        Unpack object data from give @d dictionary. (Packed with
        @GUIItem.toDict method).
        
        @param d: packed object data dictionary
        """
        pass

    def getCtorArgs(self):
        """
        Returns list of args used to build new object of items
        instance. Will be overriden by inherited classes.
        
        @return: list of constructor arguments
        """
        return list()

    def __repr__(self):
        return self.__class__.__name__


class HasIntCD(object):
    """
    Abstract class of items which contains int compact descriptor.
    """

    def __init__(self, intCompactDescr):
        self.intCompactDescr = intCompactDescr
        self.itemTypeID, self.nationID, self.innationID = self._parseIntCompDescr(self.intCompactDescr)

    def _parseIntCompDescr(self, intCompactDescr):
        """
        Parses int compact descriptor. Will be overidden by
        inherited items classes.
        
        @return: ( item type id, nation id, innation id )
        """
        return vehicles.parseIntCompactDescr(intCompactDescr)

    @property
    def intCD(self):
        """
        Returns item's int compact descriptor.
        
        @return: int compact descriptor
        """
        return self.intCompactDescr

    @property
    def itemTypeName(self):
        return ITEM_TYPE_NAMES[self.itemTypeID]

    def __cmp__(self, other):
        """
        Compares items by nation and types.
        """
        if self is other:
            return 1
        res = nationCompareByIndex(self.nationID, other.nationID)
        if res:
            return res
        return 0


class HasStrCD(object):
    """
    Abstract class of items which contains string compact descriptor.
    """

    def __init__(self, strCompactDescr):
        self.strCompactDescr = strCompactDescr

    @property
    def strCD(self):
        return self.strCompactDescr


class FittingItem(GUIItem, HasIntCD):
    """
    Root item which can be bought and installed.
    """

    def __init__(self, intCompactDescr, proxy = None, isBoughtForCredits = False):
        """
        @param intCompactDescr: item's int compact descriptor
        @param proxy: instance of ItemsRequester
        """
        GUIItem.__init__(self, proxy)
        HasIntCD.__init__(self, intCompactDescr)
        self.buyPrice = (0, 0)
        self.sellPrice = (0, 0)
        self.actionPrice = (0, 0)
        self.isHidden = False
        self.inventoryCount = 0
        self.sellForGold = False
        self.isUnlocked = False
        self.isBoughtForCredits = isBoughtForCredits
        if proxy is not None:
            self.buyPrice, self.isHidden, self.sellForGold = proxy.shop.getItem(self.intCompactDescr)
            if self.buyPrice is None:
                self.buyPrice = (0, 0)
            self.sellPrice = BigWorld.player().shop.getSellPrice(self.buyPrice, proxy.shop.sellPriceModifiers(intCompactDescr), self.itemTypeID)
            self.inventoryCount = proxy.inventory.getItems(self.itemTypeID, self.intCompactDescr)
            if self.inventoryCount is None:
                self.inventoryCount = 0
            self.isUnlocked = self.intCD in proxy.stats.unlocks
            self.actionPrice = self._getActionPrice(self.buyPrice, proxy)
        return

    def _getActionPrice(self, buyPrice, proxy):
        """
        @param buyPrice: module buying price
        @param proxy: instance of ItemsRequester
        @return:
        """
        return buyPrice

    @property
    def descriptor(self):
        return vehicles.getDictDescr(self.intCompactDescr)

    @property
    def isRemovable(self):
        """ Item can be removed from vehicle for free. Otherwise for gold. """
        return True

    @property
    def userType(self):
        """ Returns item's type represented as user-friendly string. """
        return getTypeInfoByName(self.itemTypeName)['userString']

    @property
    def userName(self):
        """ Returns item's name represented as user-friendly string. """
        return self.descriptor.get('userString', '')

    @property
    def longUserName(self):
        """ Returns item's long name represented as user-friendly string. """
        return self.userType + ' ' + self.userName

    @property
    def shortUserName(self):
        """ Returns item's short name represented as user-friendly string. """
        return self.descriptor.get('shortUserString', '')

    @property
    def shortDescription(self):
        """
        @return: first occurrence of short description from string.
        """
        return getShortDescr(self.descriptor.get('description', ''))

    @property
    def fullDescription(self):
        """
        @return: Strips short description tags from passed string and return full description body.
        """
        return stripShortDescrTags(self.descriptor.get('description', ''))

    @property
    def name(self):
        """ Returns item's tech-name. """
        return self.descriptor.get('name', '')

    @property
    def level(self):
        """ Returns item's level number value. """
        return self.descriptor.get('level', 0)

    @property
    def isInInventory(self):
        return self.inventoryCount > 0

    def _getShortInfo(self, vehicle = None):
        """
        Returns string with item's parameters.
        
        @param vehicle: vehicle which will be passes to the self.getParams method
        @return: fromatted user-string
        """
        try:
            description = i18n.makeString('#menu:descriptions/' + self.itemTypeName)
            itemParams = dict(ItemsParameters.g_instance.getParameters(self.descriptor, vehicle.descriptor if vehicle is not None else None))
            if self.itemTypeName == vehicles._VEHICLE:
                itemParams['caliber'] = BigWorld.wg_getIntegralFormat(self.descriptor.gun['shots'][0]['shell']['caliber'])
            return description % itemParams
        except Exception:
            LOG_CURRENT_EXCEPTION()
            return ''

        return

    def getShortInfo(self, vehicle = None):
        """
        Returns string with item's parameters or
        empty string if parameters is not available.
        """
        if not GUI_SETTINGS.technicalInfo:
            return ''
        return self._getShortInfo(vehicle)

    def getParams(self, vehicle = None):
        """ Returns dictionary of item's parameters to show in GUI. """
        return dict(ItemsParameters.g_instance.get(self.descriptor, vehicle.descriptor if vehicle is not None else None))

    @property
    def icon(self):
        """ Returns item's icon path. """
        return _ICONS_MASK % {'type': self.itemTypeName,
         'subtype': '',
         'unicName': self.name.replace(':', '-')}

    @property
    def iconContour(self):
        """ Returns item's contour icon path. """
        return _ICONS_MASK % {'type': self.itemTypeName,
         'subtype': 'contour/',
         'unicName': self.name.replace(':', '-')}

    @property
    def iconSmall(self):
        return _ICONS_MASK % {'type': self.itemTypeName,
         'subtype': 'small/',
         'unicName': self.name.replace(':', '-')}

    def mayInstall(self, vehicle, slotIdx = 0):
        """
        Item can be installed on @vehicle. Can be overriden
        by inherited classes.
        
        @param vehicle: installation vehicle
        @param slotIdx: slot index to install. Used for
                                        equipments and optional devices.
        @return: ( can be installed <bool>, error msg <str> )
        """
        return vehicle.descriptor.mayInstallComponent(self.intCD)

    def mayRemove(self, vehicle):
        """
        Item can be removed from @vehicle. Can be overriden
        by inherited classes.
        
        @param vehicle: removal vehicle
        @return: ( can be removed <bool>, error msg <str> )
        """
        return (True, '')

    def _sortByType(self, other):
        return -1

    def __cmp__(self, other):
        if other is None:
            return 1
        res = HasIntCD.__cmp__(self, other)
        if res:
            return res
        res = self._sortByType(other)
        if res:
            return res
        res = self.level - other.level
        if res:
            return res
        res = self.buyPrice[1] - other.buyPrice[1]
        if res:
            return res
        res = self.buyPrice[0] - other.buyPrice[0]
        if res:
            return res
        elif self.userName < other.userName:
            return -1
        elif self.userName > other.userName:
            return 1
        else:
            return 0

    def __eq__(self, other):
        if other is None:
            return False
        else:
            return self.intCompactDescr == other.intCompactDescr

    def __repr__(self):
        return '%s<intCD:%d, type:%s, nation:%d>' % (self.__class__.__name__,
         self.intCD,
         self.itemTypeName,
         self.nationID)

    def getCtorArgs(self):
        """
        Usefull method for serialization. Returns list of
        constructor arguments which will be passed to the
        object while unserializatin. Used in serializators.
        
        @return: list of ctor arguments
        """
        return [self.intCD]

    def toDict(self):
        result = GUIItem.toDict(self)
        result.update({'buyPrice': self.buyPrice,
         'sellPrice': self.sellPrice,
         'inventoryCount': self.inventoryCount,
         'isHidden': self.isHidden,
         'isRemovable': self.isRemovable,
         'intCD': self.intCD,
         'itemTypeName': self.itemTypeName,
         'itemTypeID': self.itemTypeID,
         'userName': self.userName,
         'description': self.fullDescription,
         'level': self.level,
         'nationID': self.nationID,
         'innationID': self.innationID})
        return result

    def fromDict(self, d):
        GUIItem.fromDict(self, d)
        self.buyPrice = d.get('buyPrice', (0, 0))
        self.sellPrice = d.get('sellPrice', (0, 0))
        self.inventoryCount = d.get('inventoryCount', 0)
        self.isHidden = d.get('isHidden', False)
# okay decompyling res/scripts/client/gui/shared/gui_items/__init__.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:26:47 EST

# Embedded file name: scripts/common/items/tankmen.py
from functools import partial
import math
import ResMgr
import random, struct
import nations, items
from items import _xml
from debug_utils import *
from constants import IS_CLIENT, ITEM_DEFS_PATH
from vehicles import VEHICLE_CLASS_TAGS
if IS_CLIENT:
    from helpers import i18n
SKILL_NAMES = ('reserved',
 'commander',
 'radioman',
 'driver',
 'gunner',
 'loader',
 'repair',
 'fireFighting',
 'camouflage',
 'brotherhood',
 'reserved',
 'reserved',
 'reserved',
 'reserved',
 'reserved',
 'reserved',
 'commander_tutor',
 'commander_eagleEye',
 'commander_sixthSense',
 'commander_expert',
 'commander_universalist',
 'reserved',
 'reserved',
 'reserved',
 'reserved',
 'reserved',
 'reserved',
 'reserved',
 'driver_virtuoso',
 'driver_smoothDriving',
 'driver_badRoadsKing',
 'driver_rammingMaster',
 'driver_tidyPerson',
 'reserved',
 'reserved',
 'reserved',
 'reserved',
 'gunner_gunsmith',
 'gunner_sniper',
 'gunner_smoothTurret',
 'gunner_rancorous',
 'gunner_woodHunter',
 'reserved',
 'reserved',
 'reserved',
 'reserved',
 'loader_pedant',
 'loader_desperado',
 'loader_intuition',
 'reserved',
 'reserved',
 'reserved',
 'reserved',
 'radioman_inventor',
 'radioman_finder',
 'radioman_retransmitter',
 'radioman_lastEffort',
 'reserved',
 'reserved',
 'reserved',
 'reserved')
SKILL_INDICES = dict(((x[1], x[0]) for x in enumerate(SKILL_NAMES) if not x[1].startswith('reserved')))
ROLES = frozenset(('commander',
 'radioman',
 'driver',
 'gunner',
 'loader'))
COMMON_SKILLS = frozenset(('repair',
 'fireFighting',
 'camouflage',
 'brotherhood'))
ROLES_AND_COMMON_SKILLS = ROLES | COMMON_SKILLS
SKILLS_BY_ROLES = {'commander': COMMON_SKILLS.union(('commander_tutor',
               'commander_expert',
               'commander_universalist',
               'commander_sixthSense',
               'commander_eagleEye')),
 'driver': COMMON_SKILLS.union(('driver_tidyPerson',
            'driver_smoothDriving',
            'driver_virtuoso',
            'driver_badRoadsKing',
            'driver_rammingMaster')),
 'gunner': COMMON_SKILLS.union(('gunner_smoothTurret',
            'gunner_sniper',
            'gunner_rancorous',
            'gunner_gunsmith')),
 'loader': COMMON_SKILLS.union(('loader_pedant', 'loader_desperado', 'loader_intuition')),
 'radioman': COMMON_SKILLS.union(('radioman_finder',
              'radioman_inventor',
              'radioman_lastEffort',
              'radioman_retransmitter'))}
ACTIVE_SKILLS = SKILLS_BY_ROLES['commander'] | SKILLS_BY_ROLES['radioman'] | SKILLS_BY_ROLES['driver'] | SKILLS_BY_ROLES['gunner'] | SKILLS_BY_ROLES['loader']
PERKS = frozenset(('brotherhood',
 'commander_sixthSense',
 'commander_expert',
 'driver_tidyPerson',
 'gunner_rancorous',
 'gunner_woodHunter',
 'gunner_sniper',
 'loader_pedant',
 'loader_desperado',
 'loader_intuition',
 'radioman_lastEffort'))
MAX_SKILL_LEVEL = 100
MIN_ROLE_LEVEL = 50
SKILL_LEVELS_PER_RANK = 50
COMMANDER_ADDITION_RATIO = 10
_MAX_FREE_XP = 2000000000
_LEVELUP_K1 = 50.0
_LEVELUP_K2 = 100.0

def init(preloadEverything):
    if preloadEverything:
        getSkillsConfig()
        for nationID in xrange(len(nations.NAMES)):
            getNationConfig(nationID)


def getSkillsConfig():
    global _g_skillsConfig
    if _g_skillsConfig is None:
        _g_skillsConfig = _readSkillsConfig(ITEM_DEFS_PATH + 'tankmen/tankmen.xml')
    return _g_skillsConfig


def getNationConfig(nationID):
    global _g_nationsConfig
    if _g_nationsConfig[nationID] is None:
        nationName = nations.NAMES[nationID]
        if nationName not in nations.AVAILABLE_NAMES:
            _g_nationsConfig[nationID] = {}
        else:
            _g_nationsConfig[nationID] = _readNationConfig(ITEM_DEFS_PATH + 'tankmen/' + nationName + '.xml')
    return _g_nationsConfig[nationID]


def generatePassport(nationID, isPremium = False):
    isPremium = False
    groups = getNationConfig(nationID)['normalGroups' if not isPremium else 'premiumGroups']
    w = random.random()
    summWeight = 0.0
    for group in groups:
        weight = group['weight']
        if summWeight <= w < summWeight + weight:
            break
        summWeight += weight

    return (nationID,
     isPremium,
     group['isFemales'],
     random.choice(group['firstNamesList']),
     random.choice(group['lastNamesList']),
     random.choice(group['iconsList']))


def generateTankmen(nationID, vehicleTypeID, roles, isPremium, roleLevel, addTankmanSkills):
    tankmenList = []
    prevPassports = []
    for i in xrange(len(roles)):
        role = roles[i]
        for j in xrange(10):
            passport = generatePassport(nationID, isPremium)
            for prevPassport in prevPassports:
                if passport[5] == prevPassport[5]:
                    break
                if passport[3:5] == prevPassport[3:5]:
                    break
            else:
                break

        prevPassports.append(passport)
        skills = []
        if addTankmanSkills:
            tankmanSkills = set()
            for i in xrange(len(role)):
                tankmanSkills.update(SKILLS_BY_ROLES[role[i]])

            skills.extend(tankmanSkills)
        tmanCompDescr = generateCompactDescr(passport, vehicleTypeID, role[0], roleLevel, skills)
        tankmenList.append(tmanCompDescr)

    return tankmenList


def generateCompactDescr(passport, vehicleTypeID, role, roleLevel, skills = [], lastSkillLevel = MAX_SKILL_LEVEL, dossierCompactDescr = ''):
    pack = struct.pack
    raise MIN_ROLE_LEVEL <= roleLevel <= MAX_SKILL_LEVEL or AssertionError
    nationID, isPremium, isFemale, firstNameID, lastNameID, iconID = passport
    header = items.ITEM_TYPE_INDICES['tankman'] + (nationID << 4)
    cd = pack('4B', header, vehicleTypeID, SKILL_INDICES[role], roleLevel)
    numSkills = len(skills)
    skills = [ SKILL_INDICES[s] for s in skills ]
    cd += pack((str(1 + numSkills) + 'B'), numSkills, *skills)
    cd += chr(lastSkillLevel if numSkills else 0)
    rank, levelsToNextRank = divmod(roleLevel - MIN_ROLE_LEVEL, SKILL_LEVELS_PER_RANK)
    levelsToNextRank = SKILL_LEVELS_PER_RANK - levelsToNextRank
    isFemale = 1 if isFemale else 0
    isPremium = 1 if isPremium else 0
    flags = isFemale | isPremium << 1
    cd += pack('<B4Hi', flags, firstNameID, lastNameID, iconID, rank | levelsToNextRank << 5, 0)
    cd += dossierCompactDescr
    return cd


def stripNonBattle(compactDescr):
    return compactDescr[:6 + ord(compactDescr[4])]


def parseNationSpecAndRole(compactDescr):
    return (ord(compactDescr[0]) >> 4 & 15, ord(compactDescr[1]), ord(compactDescr[2]))


def compareMastery(tankmanDescr1, tankmanDescr2):
    return cmp(tankmanDescr1.totalXP(), tankmanDescr2.totalXP())


def commanderTutorXpBonusFactorForCrew(crew):
    tutorLevel = 0
    haveBrotherhood = True
    for t in crew:
        if t.role == 'commander':
            tutorLevel = t.skillLevel('commander_tutor')
            if not tutorLevel:
                return 0.0
        if t.skillLevel('brotherhood') != MAX_SKILL_LEVEL:
            haveBrotherhood = False

    skillsConfig = getSkillsConfig()
    if haveBrotherhood:
        tutorLevel += skillsConfig['brotherhood']['crewLevelIncrease']
    return tutorLevel * skillsConfig['commander_tutor']['xpBonusFactorPerLevel']


def fixObsoleteNames(compactDescr):
    cd = compactDescr
    header = ord(cd[0])
    if not header & 15 == items.ITEM_TYPE_INDICES['tankman']:
        raise AssertionError
        nationID = header >> 4 & 15
        conf = getNationConfig(nationID)
        namesOffset = ord(cd[4]) + 7
        firstNameID, lastNameID = struct.unpack('<2H', cd[namesOffset:namesOffset + 4])
        hasChanges = False
        if firstNameID not in conf['firstNames']:
            hasChanges = True
            firstNameID = generatePassport(nationID)[3]
        if lastNameID not in conf['lastNames']:
            hasChanges = True
            lastNameID = generatePassport(nationID)[4]
        return hasChanges or cd
    return cd[:namesOffset] + struct.pack('<2H', firstNameID, lastNameID) + cd[namesOffset + 4:]


class TankmanDescr(object):

    def __init__(self, compactDescr, battleOnly = False):
        self.__initFromCompactDescr(compactDescr, battleOnly)

    def efficiencyOnVehicle(self, vehicleDescr):
        nationID, vehicleTypeID = vehicleDescr.type.id
        if not nationID == self.nationID:
            raise AssertionError
            factor = 1.0
            if vehicleTypeID != self.vehicleTypeID:
                isPremium, isSameClass = self.__paramsOnVehicle(vehicleDescr.type)
                factor = isSameClass and (1.0 if isPremium else 0.75)
            else:
                factor = 0.75 if isPremium else 0.5
        addition = vehicleDescr.miscAttrs['crewLevelIncrease']
        return (factor, addition)

    def battleXpGain(self, xp, vehicleType, tankmanHasSurvived, commanderTutorXpBonusFactor):
        nationID, vehicleTypeID = vehicleType.id
        if not nationID == self.nationID:
            raise AssertionError
            if vehicleTypeID != self.vehicleTypeID:
                isPremium, isSameClass = self.__paramsOnVehicle(vehicleType)
                if isPremium:
                    xp *= 1.0 if isSameClass else 0.5
                else:
                    xp *= 0.5 if isSameClass else 0.25
            xp *= vehicleType.crewXpFactor
            if not tankmanHasSurvived:
                xp *= 0.9
            self.role != 'commander' and xp *= 1.0 + commanderTutorXpBonusFactor
        return int(xp)

    @staticmethod
    def levelUpXpCost(fromSkillLevel, skillSeqNum):
        costs = _g_levelXpCosts
        return 2 ** skillSeqNum * (costs[fromSkillLevel + 1] - costs[fromSkillLevel])

    def skillLevel(self, skillName):
        if skillName not in self.skills:
            return None
        elif skillName != self.skills[-1]:
            return MAX_SKILL_LEVEL
        else:
            return self.lastSkillLevel

    def totalXP(self):
        levelCosts = _g_levelXpCosts
        xp = self.freeXP + levelCosts[self.roleLevel]
        numSkills = len(self.skills)
        if numSkills:
            xp += levelCosts[self.lastSkillLevel] * 2 ** numSkills
            for idx in xrange(1, numSkills):
                xp += levelCosts[MAX_SKILL_LEVEL] * 2 ** idx

        return xp

    def addXP(self, xp):
        self.freeXP = min(_MAX_FREE_XP, self.freeXP + xp)
        while self.roleLevel < MAX_SKILL_LEVEL:
            xpCost = self.levelUpXpCost(self.roleLevel, 0)
            if xpCost > self.freeXP:
                break
            self.freeXP -= xpCost
            self.roleLevel += 1
            self.__updateRankAtSkillLevelUp()

        if self.roleLevel == MAX_SKILL_LEVEL and self.skills:
            self.__levelUpLastSkill()

    def addSkill(self, skillName):
        if skillName in self.skills:
            raise ValueError, skillName
        if skillName not in ACTIVE_SKILLS:
            raise ValueError, skillName
        if self.roleLevel != MAX_SKILL_LEVEL:
            raise ValueError, self.roleLevel
        if self.skills and self.lastSkillLevel != MAX_SKILL_LEVEL:
            raise ValueError, self.lastSkillLevel
        self.skills.append(skillName)
        self.lastSkillLevel = 0
        self.__levelUpLastSkill()

    def dropSkills(self, xpReuseFraction = 0.0):
        if not 0.0 <= xpReuseFraction <= 1.0:
            raise AssertionError
            prevTotalXP = self.totalXP()
            if self.numLevelsToNextRank != 0:
                self.numLevelsToNextRank += self.lastSkillLevel
                numSkills = len(self.skills)
                if numSkills > 1:
                    self.numLevelsToNextRank += MAX_SKILL_LEVEL * (numSkills - 1)
            del self.skills[:]
            self.lastSkillLevel = 0
            xpReuseFraction != 0.0 and self.addXP(int(xpReuseFraction * (prevTotalXP - self.totalXP())))

    def dropSkill(self, skillName, xpReuseFraction = 0.0):
        if not 0.0 <= xpReuseFraction <= 1.0:
            raise AssertionError
            idx = self.skills.index(skillName)
            prevTotalXP = self.totalXP()
            numSkills = len(self.skills)
            levelsDropped = MAX_SKILL_LEVEL
            if numSkills == 1:
                levelsDropped = self.lastSkillLevel
                self.lastSkillLevel = 0
            elif idx + 1 == numSkills:
                levelsDropped = self.lastSkillLevel
                self.lastSkillLevel = MAX_SKILL_LEVEL
            del self.skills[idx]
            if self.numLevelsToNextRank != 0:
                self.numLevelsToNextRank += levelsDropped
            xpReuseFraction != 0.0 and self.addXP(int(xpReuseFraction * (prevTotalXP - self.totalXP())))

    def respecialize(self, newVehicleTypeID, minNewRoleLevel, vehicleChangeRoleLevelLoss, classChangeRoleLevelLoss, becomesPremium):
        if not 0 <= minNewRoleLevel <= MAX_SKILL_LEVEL:
            raise AssertionError
            raise 0.0 <= vehicleChangeRoleLevelLoss <= 1.0 or AssertionError
            if not 0.0 <= classChangeRoleLevelLoss <= 1.0:
                raise AssertionError
                from items import vehicles
                newVehTags = vehicles.g_list.getList(self.nationID)[newVehicleTypeID]['tags']
                roleLevelLoss = 0.0 if newVehicleTypeID == self.vehicleTypeID else vehicleChangeRoleLevelLoss
                isSameClass = len(self.__vehicleTags & newVehTags & vehicles.VEHICLE_CLASS_TAGS)
                isSameClass or roleLevelLoss += classChangeRoleLevelLoss
            newRoleLevel = int(round(self.roleLevel * (1.0 - roleLevelLoss)))
            newRoleLevel = max(minNewRoleLevel, newRoleLevel)
            self.vehicleTypeID = newVehicleTypeID
            self.__vehicleTags = newVehTags
            newRoleLevel > self.roleLevel and self.__updateRankAtSkillLevelUp(newRoleLevel - self.roleLevel)
            self.roleLevel = newRoleLevel
            self.freeXp = 0
        elif newRoleLevel < self.roleLevel:
            if self.numLevelsToNextRank != 0:
                self.numLevelsToNextRank += self.roleLevel - newRoleLevel
            self.roleLevel = newRoleLevel
            self.addXP(0)

    def replacePassport(self, isFemale = None, firstNameID = None, lastNameID = None, iconID = None):
        if isFemale is None:
            isFemale = self.isFemale
        if firstNameID is None:
            firstNameID = self.firstNameID
        if lastNameID is None:
            lastNameID = self.lastNameID
        if iconID is None:
            iconID = self.iconID
        isOk = False
        config = getNationConfig(self.nationID)
        for group in config['normalGroups'] + config['premiumGroups']:
            if bool(group['isFemales']) != bool(isFemale):
                continue
            if firstNameID not in group['firstNames']:
                continue
            if lastNameID in group['lastNames'] and iconID in group['icons']:
                isOk = True
            break

        if isOk:
            self.isFemale = isFemale
            self.firstNameID = firstNameID
            self.lastNameID = lastNameID
            self.iconID = iconID
        return isOk

    def makeCompactDescr(self):
        pack = struct.pack
        header = items.ITEM_TYPE_INDICES['tankman'] + (self.nationID << 4)
        cd = pack('4B', header, self.vehicleTypeID, SKILL_INDICES[self.role], self.roleLevel)
        numSkills = len(self.skills)
        skills = [ SKILL_INDICES[s] for s in self.skills ]
        cd += pack((str(1 + numSkills) + 'B'), numSkills, *skills)
        cd += chr(self.lastSkillLevel if numSkills else 0)
        isFemale = 1 if self.isFemale else 0
        isPremium = 1 if self.isPremium else 0
        flags = isFemale | isPremium << 1
        cd += pack('<B4Hi', flags, self.firstNameID, self.lastNameID, self.iconID, self.__rankIdx & 31 | (self.numLevelsToNextRank & 2047) << 5, self.freeXP)
        cd += self.dossierCompactDescr
        return cd

    def __initFromCompactDescr(self, compactDescr, battleOnly):
        cd = compactDescr
        unpack = struct.unpack
        try:
            header, self.vehicleTypeID, roleID, self.roleLevel, numSkills = unpack('5B', cd[:5])
            cd = cd[5:]
            if not header & 15 == items.ITEM_TYPE_INDICES['tankman']:
                raise AssertionError
                nationID = header >> 4 & 15
                nations.NAMES[nationID]
                self.nationID = nationID
                from items import vehicles
                self.__vehicleTags = vehicles.g_list.getList(nationID)[self.vehicleTypeID]['tags']
                self.role = SKILL_NAMES[roleID]
                if self.role not in ROLES:
                    raise KeyError, self.role
                if self.roleLevel > MAX_SKILL_LEVEL:
                    raise ValueError, self.roleLevel
                self.skills = []
                if numSkills == 0:
                    self.lastSkillLevel = 0
                else:
                    for skillID in unpack(str(numSkills) + 'B', cd[:numSkills]):
                        skillName = SKILL_NAMES[skillID]
                        if skillName not in ACTIVE_SKILLS:
                            raise KeyError, (skillName, self.role)
                        self.skills.append(skillName)

                    self.lastSkillLevel = ord(cd[numSkills])
                    if self.lastSkillLevel > MAX_SKILL_LEVEL:
                        raise ValueError, self.lastSkillLevel
                cd = cd[numSkills + 1:]
                if battleOnly:
                    return
                nationConfig = getNationConfig(nationID)
                flags, self.firstNameID, self.lastNameID, self.iconID, rank, self.freeXP = unpack('<B4Hi', cd[:13])
                cd = cd[13:]
                self.dossierCompactDescr = cd
                self.isFemale = bool(flags & 1)
                self.isPremium = bool(flags & 2)
                self.__rankIdx = rank & 31
                self.numLevelsToNextRank = rank >> 5
                self.rankID = nationConfig['roleRanks'][self.role][self.__rankIdx]
                if self.firstNameID not in nationConfig['firstNames']:
                    raise KeyError, self.firstNameID
                if self.lastNameID not in nationConfig['lastNames']:
                    raise KeyError, self.lastNameID
                raise self.iconID not in nationConfig['icons'] and KeyError, self.iconID
        except Exception:
            LOG_ERROR('(compact description to XML mismatch?)', compactDescr)
            raise

    def __paramsOnVehicle(self, vehicleType):
        isPremium = 'premium' in vehicleType.tags
        isSameClass = len(VEHICLE_CLASS_TAGS & vehicleType.tags & self.__vehicleTags)
        return (isPremium, isSameClass)

    def __updateRankAtSkillLevelUp(self, numLevels = 1):
        if numLevels < self.numLevelsToNextRank:
            self.numLevelsToNextRank -= numLevels
            return
        rankIDs = getNationConfig(self.nationID)['roleRanks'][self.role]
        maxRankIdx = len(rankIDs) - 1
        while numLevels >= self.numLevelsToNextRank > 0:
            numLevels -= self.numLevelsToNextRank
            self.__rankIdx = min(self.__rankIdx + 1, maxRankIdx)
            self.rankID = rankIDs[self.__rankIdx]
            self.numLevelsToNextRank = SKILL_LEVELS_PER_RANK if self.__rankIdx < maxRankIdx else 0

    def __levelUpLastSkill(self):
        numSkills = len(self.skills)
        while self.lastSkillLevel < MAX_SKILL_LEVEL:
            xpCost = self.levelUpXpCost(self.lastSkillLevel, numSkills)
            if xpCost > self.freeXP:
                break
            self.freeXP -= xpCost
            self.lastSkillLevel += 1
            self.__updateRankAtSkillLevelUp()


def _readNationConfig(xmlPath):
    section = ResMgr.openSection(xmlPath)
    if section is None:
        _xml.raiseWrongXml(None, xmlPath, 'can not open or read')
    res = _readNationConfigSection((None, xmlPath), section)
    section = None
    ResMgr.purge(xmlPath, True)
    return res


def _readNationConfigSection(xmlCtx, section):
    res = {}
    firstNames = {}
    lastNames = {}
    icons = {}
    for kindName in ('normalGroups', 'premiumGroups'):
        groups = []
        res[kindName] = groups
        totalWeight = 0.0
        for sname, subsection in _xml.getChildren(xmlCtx, section, kindName):
            ctx = (xmlCtx, kindName + '/' + sname)
            group = {'isFemales': 'female' == _xml.readNonEmptyString(ctx, subsection, 'sex'),
             'firstNames': _readIDs((ctx, 'firstNames'), _xml.getChildren(ctx, subsection, 'firstNames'), firstNames, _parseName),
             'lastNames': _readIDs((ctx, 'lastNames'), _xml.getChildren(ctx, subsection, 'lastNames'), lastNames, _parseName),
             'icons': _readIDs((ctx, 'icons'), _xml.getChildren(ctx, subsection, 'icons'), icons, _parseIcon)}
            group['firstNamesList'] = list(group['firstNames'])
            group['lastNamesList'] = list(group['lastNames'])
            group['iconsList'] = list(group['icons'])
            weight = _xml.readNonNegativeFloat(ctx, subsection, 'weight')
            totalWeight += weight
            group['weight'] = weight
            groups.append(group)

        totalWeight = max(0.001, totalWeight)
        for group in groups:
            group['weight'] /= totalWeight

    ranks, rankIDsByNames = _readRanks((xmlCtx, 'ranks'), _xml.getChildren(xmlCtx, section, 'ranks'))
    res['roleRanks'] = _readRoleRanks((xmlCtx, 'roleRanks'), _xml.getSubsection(xmlCtx, section, 'roleRanks'), rankIDsByNames)
    if IS_CLIENT:
        res['firstNames'] = firstNames
        res['lastNames'] = lastNames
        res['icons'] = icons
        res['ranks'] = ranks
    else:
        res['firstNames'] = frozenset(firstNames)
        res['lastNames'] = frozenset(lastNames)
        res['icons'] = frozenset(icons)
    return res


def _readRanks(xmlCtx, subsections):
    ranks = []
    rankIDsByNames = {}
    for sname, subsection in subsections:
        if rankIDsByNames.has_key(sname):
            _xml.raiseWrong(xmlCtx, sname, 'is not unique')
        ctx = (xmlCtx, sname)
        rankIDsByNames[sname] = len(ranks)
        if not IS_CLIENT:
            ranks.append(None)
        else:
            ranks.append({'userString': i18n.makeString(_xml.readNonEmptyString(ctx, subsection, 'userString')),
             'icon': _parseIcon((ctx, 'icon'), _xml.getSubsection(ctx, subsection, 'icon'))})

    return (ranks, rankIDsByNames)


def _readRoleRanks(xmlCtx, section, rankIDsByNames):
    res = {}
    for roleName in ROLES:
        rankIDs = []
        res[roleName] = rankIDs
        for rankName in _xml.readNonEmptyString(xmlCtx, section, roleName).split():
            rankIDs.append(rankIDsByNames[rankName])

    return res


def _readIDs(xmlCtx, subsections, accumulator, parser):
    res = set()
    for sname, subsection in subsections:
        try:
            id = int(sname[1:])
        except Exception:
            id = -1

        if sname[0] != '_' or not 0 <= id <= 65535:
            _xml.raiseWrongSection(xmlCtx, sname)
        if id in accumulator:
            _xml.raiseWrongXml(xmlCtx, sname, 'ID is not unique')
        accumulator[id] = parser((xmlCtx, sname), subsection)
        res.add(id)

    if not res:
        _xml.raiseWrongXml(xmlCtx, '', 'is empty')
    return res


if not IS_CLIENT:

    def _parseName(xmlCtx, section):
        return None


    _parseIcon = _parseName
else:

    def _parseName(xmlCtx, section):
        return i18n.makeString(_xml.readNonEmptyString(xmlCtx, section, ''))


    def _parseIcon(xmlCtx, section):
        return _xml.readNonEmptyString(xmlCtx, section, '')


def _readSkillsConfig(xmlPath):
    xmlCtx = (None, xmlPath)
    section = ResMgr.openSection(xmlPath)
    if section is None:
        _xml.raiseWrongXml(None, xmlPath, 'can not open or read')
    res = {}
    for skillName in ROLES:
        res[skillName] = _readRole(xmlCtx, section, 'roles/' + skillName)

    section = _xml.getSubsection(xmlCtx, section, 'skills')
    xmlCtx = (xmlCtx, 'skills')
    for skillName in ACTIVE_SKILLS:
        res[skillName] = _g_skillConfigReaders[skillName](xmlCtx, section, skillName)

    section = None
    ResMgr.purge(xmlPath, True)
    return res


def _readSkillBasics(xmlCtx, section, subsectionName):
    section = _xml.getSubsection(xmlCtx, section, subsectionName)
    xmlCtx = (xmlCtx, subsectionName)
    res = {}
    if IS_CLIENT:
        res['userString'] = i18n.makeString(section.readString('userString'))
        res['description'] = i18n.makeString(section.readString('description'))
        res['icon'] = _xml.readNonEmptyString(xmlCtx, section, 'icon')
    return (res, xmlCtx, section)


def _readRole(xmlCtx, section, subsectionName):
    res, xmlCtx, section = _readSkillBasics(xmlCtx, section, subsectionName)
    return res


def _readSkillInt(paramName, minVal, xmlCtx, section, subsectionName):
    res, xmlCtx, section = _readSkillBasics(xmlCtx, section, subsectionName)
    res[paramName] = _xml.readInt(xmlCtx, section, paramName, minVal)
    return res


def _readSkillNonNegFloat(paramName, xmlCtx, section, subsectionName):
    res, xmlCtx, section = _readSkillBasics(xmlCtx, section, subsectionName)
    res[paramName] = _xml.readNonNegativeFloat(xmlCtx, section, paramName)
    return res


def _readSkillFraction(paramName, xmlCtx, section, subsectionName):
    res, xmlCtx, section = _readSkillBasics(xmlCtx, section, subsectionName)
    res[paramName] = _xml.readFraction(xmlCtx, section, paramName)
    return res


def _readGunnerRancorous(xmlCtx, section, subsectionName):
    res, xmlCtx, section = _readSkillBasics(xmlCtx, section, subsectionName)
    res['duration'] = _xml.readPositiveFloat(xmlCtx, section, 'duration')
    res['sectorHalfAngle'] = math.radians(_xml.readPositiveFloat(xmlCtx, section, 'sectorHalfAngle'))
    return res


def _readGunnerGunsmith(xmlCtx, section, subsectionName):
    res, xmlCtx, section = _readSkillBasics(xmlCtx, section, subsectionName)
    res['shotDispersionFactorPerLevel'] = _xml.readPositiveFloat(xmlCtx, section, 'shotDispersionFactorPerLevel')
    return res


def _readCommanderEagleEye(xmlCtx, section, subsectionName):
    res, xmlCtx, section = _readSkillBasics(xmlCtx, section, subsectionName)
    res['distanceFactorPerLevelWhenDeviceWorking'] = _xml.readPositiveFloat(xmlCtx, section, 'distanceFactorPerLevelWhenDeviceWorking')
    res['distanceFactorPerLevelWhenDeviceDestroyed'] = _xml.readPositiveFloat(xmlCtx, section, 'distanceFactorPerLevelWhenDeviceDestroyed')
    return res


def _readLoaderDesperado(xmlCtx, section, subsectionName):
    res, xmlCtx, section = _readSkillBasics(xmlCtx, section, subsectionName)
    res['vehicleHealthFraction'] = _xml.readFraction(xmlCtx, section, 'vehicleHealthFraction')
    res['gunReloadTimeFactor'] = _xml.readPositiveFloat(xmlCtx, section, 'gunReloadTimeFactor')
    return res


def _readBadRoadsKing(xmlCtx, section, subsectionName):
    res, xmlCtx, section = _readSkillBasics(xmlCtx, section, subsectionName)
    res['softGroundResistanceFactorPerLevel'] = _xml.readPositiveFloat(xmlCtx, section, 'softGroundResistanceFactorPerLevel')
    res['mediumGroundResistanceFactorPerLevel'] = _xml.readPositiveFloat(xmlCtx, section, 'mediumGroundResistanceFactorPerLevel')
    return res


_g_skillConfigReaders = {'repair': _readRole,
 'fireFighting': _readRole,
 'camouflage': _readRole,
 'brotherhood': partial(_readSkillInt, 'crewLevelIncrease', 0),
 'commander_tutor': partial(_readSkillNonNegFloat, 'xpBonusFactorPerLevel'),
 'commander_universalist': partial(_readSkillFraction, 'efficiency'),
 'commander_expert': partial(_readSkillNonNegFloat, 'delay'),
 'commander_sixthSense': partial(_readSkillNonNegFloat, 'delay'),
 'commander_eagleEye': _readCommanderEagleEye,
 'driver_tidyPerson': partial(_readSkillNonNegFloat, 'fireStartingChanceFactor'),
 'driver_smoothDriving': partial(_readSkillNonNegFloat, 'shotDispersionFactorPerLevel'),
 'driver_virtuoso': partial(_readSkillNonNegFloat, 'rotationSpeedFactorPerLevel'),
 'driver_badRoadsKing': _readBadRoadsKing,
 'driver_rammingMaster': partial(_readSkillNonNegFloat, 'rammingBonusFactorPerLevel'),
 'gunner_smoothTurret': partial(_readSkillNonNegFloat, 'shotDispersionFactorPerLevel'),
 'gunner_sniper': partial(_readSkillFraction, 'deviceChanceToHitBoost'),
 'gunner_rancorous': _readGunnerRancorous,
 'gunner_woodHunter': partial(_readSkillNonNegFloat, 'curtainEffectDistanceBonus'),
 'gunner_gunsmith': _readGunnerGunsmith,
 'loader_pedant': partial(_readSkillNonNegFloat, 'ammoBayHealthFactor'),
 'loader_desperado': _readLoaderDesperado,
 'loader_intuition': partial(_readSkillFraction, 'chance'),
 'radioman_finder': partial(_readSkillNonNegFloat, 'visionRadiusFactorPerLevel'),
 'radioman_inventor': partial(_readSkillNonNegFloat, 'radioDistanceFactorPerLevel'),
 'radioman_lastEffort': partial(_readSkillInt, 'duration', 1),
 'radioman_retransmitter': partial(_readSkillNonNegFloat, 'distanceFactorPerLevel')}
_g_skillsConfig = None
_g_nationsConfig = [ None for x in xrange(len(nations.NAMES)) ]

def _makeLevelXpCosts():
    costs = [0] * (MAX_SKILL_LEVEL + 1)
    prevCost = 0
    for level in xrange(1, len(costs)):
        prevCost += int(round(_LEVELUP_K1 * pow(_LEVELUP_K2, float(level - 1) / MAX_SKILL_LEVEL)))
        costs[level] = prevCost

    return costs


_g_levelXpCosts = _makeLevelXpCosts()
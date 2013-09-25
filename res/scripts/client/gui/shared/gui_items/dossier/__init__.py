import BigWorld
import math
import itertools
import constants
from gui.shared.utils.dossiers_utils import checkWhiteTigerMedal
import nations
from items import tankmen, vehicles
from helpers import i18n
from debug_utils import LOG_ERROR, LOG_CURRENT_EXCEPTION, LOG_DEBUG
from gui.shared.gui_items import GUIItem
from gui.shared.utils import dossiers_utils
from gui.shared.gui_items.dossier.achievements import MARK_OF_MASTERY
from gui.shared.gui_items.dossier.factories import getAchievementFactory, _SequenceAchieveFactory
from dossiers.achievements import ACHIEVEMENT_SECTIONS_INDICES, ACHIEVEMENT_SECTION
_BATTLE_SECTION = ACHIEVEMENT_SECTIONS_INDICES[ACHIEVEMENT_SECTION.BATTLE]
_EPIC_SECTION = ACHIEVEMENT_SECTIONS_INDICES[ACHIEVEMENT_SECTION.EPIC]
_NEAREST_ACHIEVEMENTS = ['tankExpert', 'mechanicEngineer']
_NEAREST_ACHIEVEMENTS_COUNT = 5
_TANK_EXPERTS_ACHIEVEMENTS = []
_MECHANIC_ENGINEER_ACHIEVEMENTS = []
for nationID, nation in enumerate(nations.NAMES):
    _TANK_EXPERTS_ACHIEVEMENTS.append('tankExpert%d' % nationID)
    _MECHANIC_ENGINEER_ACHIEVEMENTS.append('mechanicEngineer%d' % nationID)

_NEAREST_ACHIEVEMENTS += _TANK_EXPERTS_ACHIEVEMENTS
_NEAREST_ACHIEVEMENTS += _MECHANIC_ENGINEER_ACHIEVEMENTS
_NEAREST_ACHIEVEMENTS += ['mousebane',
 'beasthunter',
 'pattonValley',
 'sinai',
 'medalKnispel',
 'medalCarius',
 'medalAbrams',
 'medalPoppel',
 'medalKay',
 'medalEkins',
 'medalLeClerc',
 'medalLavrinenko']
_SIGNIFICANT_ACHIEVEMENTS_PER_SECTION = 3

class _Dossier(GUIItem):

    def __init__(self, dossier, dossierType, proxy = None):
        super(GUIItem, self).__init__()
        self.dossier = dossier
        self.dossierType = dossierType
        self.proxy = proxy

    def getRecord(self, recordName):
        return self.dossier[recordName]

    def getAchievements(self, isInDossier = True):
        result = []
        for section in dossiers_utils.getAchievementsLayout(self.dossierType):
            sectionAchieves = []
            for achieveName in section:
                if achieveName == 'markOfMastery':
                    continue
                if achieveName == 'whiteTiger' and not checkWhiteTigerMedal(self.dossier):
                    continue
                try:
                    factory = getAchievementFactory(achieveName, self)
                    if isInDossier is None or factory.isInDossier() and isInDossier or not factory.isInDossier() and not isInDossier:
                        if isinstance(factory, _SequenceAchieveFactory):
                            sectionAchieves.extend(factory.create(self.proxy).values())
                        else:
                            sectionAchieves.append(factory.create(self.proxy))
                except Exception:
                    LOG_ERROR('There is exception while achievement creating', achieveName)
                    LOG_CURRENT_EXCEPTION()
                    continue

            result.append(tuple(sorted(sectionAchieves)))

        return tuple(result)

    def getAchievement(self, achieveName):
        try:
            factory = getAchievementFactory(achieveName, self)
            return factory.create(self.proxy)
        except Exception:
            LOG_ERROR('There is exception while achievement creating', achieveName)
            LOG_CURRENT_EXCEPTION()

        return None

    def getNearestAchievements(self):
        achievements = map(lambda x: self.getAchievement(x), _NEAREST_ACHIEVEMENTS)
        uncompleted_achievements = itertools.ifilter(lambda x: x.progress < 1.0, achievements)
        result = sorted(uncompleted_achievements, key=lambda x: x.progress, reverse=True)[:_NEAREST_ACHIEVEMENTS_COUNT]
        return tuple(result)

    def getSignificantAchievements(self):
        sections = self.getAchievements()
        battleAchievements = sections[_BATTLE_SECTION]
        epicAchievements = sections[_EPIC_SECTION]
        otherAchievements = itertools.chain(*itertools.ifilter(lambda x: sections.index(x) not in (_BATTLE_SECTION, _EPIC_SECTION), sections))
        achievementsQuery = (battleAchievements, epicAchievements, tuple(otherAchievements))

        def mapQueryEntry(entry):
            return sorted(entry, key=lambda x: x.weight)[:_SIGNIFICANT_ACHIEVEMENTS_PER_SECTION]

        result = itertools.chain(*map(mapQueryEntry, achievementsQuery))
        return tuple(result)

    def getBattlesCount(self):
        return self.getRecord('battlesCount')

    def getWinsCount(self):
        return self.getRecord('wins')

    def getXP(self):
        return self.getRecord('xp')

    def getDamageDealt(self):
        return self.getRecord('damageDealt')

    def getDamageReceived(self):
        return self.getRecord('damageReceived')

    def getShotsCount(self):
        return self.getRecord('shots')

    def getHitsCount(self):
        return self.getRecord('hits')

    def getSurvivedBattlesCount(self):
        return self.getRecord('survivedBattles')

    def getFragsCount(self):
        return self.getRecord('frags')

    def getDeathsCount(self):
        return self.getBattlesCount() - self.getSurvivedBattlesCount()

    def getMaxFrags(self):
        return (self.getRecord('maxFrags'), self.getRecord('maxFragsVehicle'))

    def getMaxXP(self):
        return (self.getRecord('maxXP'), self.getRecord('maxXPVehicle'))

    def getMaxVehicleFrags(self):
        return self.getRecord('maxFrags')

    def getMaxVehicleXP(self):
        return self.getRecord('maxXP')

    def getSpottedEnemiesCount(self):
        return self.getRecord('spotted')

    def getAvgDamage(self):
        return self._getAvgValue(self.getBattlesCount, self.getDamageDealt)

    def getAvgXP(self):
        return self._getAvgValue(self.getBattlesCount, self.getXP)

    def getAvgFrags(self):
        return self._getAvgValue(self.getBattlesCount, self.getFragsCount)

    def getAvgDamageDealt(self):
        return self._getAvgValue(self.getBattlesCount, self.getDamageDealt)

    def getAvgDamageReceived(self):
        return self._getAvgValue(self.getBattlesCount, self.getDamageReceived)

    def getAvgEnemiesSpotted(self):
        return self._getAvgValue(self.getBattlesCount, self.getSpottedEnemiesCount)

    def getHitsEfficiency(self):
        return self._getAvgValue(self.getShotsCount, self.getHitsCount)

    def getSurvivalEfficiency(self):
        return self._getAvgValue(self.getBattlesCount, self.getSurvivedBattlesCount)

    def getWinsEfficiency(self):
        return self._getAvgValue(self.getBattlesCount, self.getWinsCount)

    def getLossesEfficiency(self):
        return self._getAvgValue(self.getBattlesCount, lambda : self.getBattlesCount() - self.getWinsCount())

    def getFragsEfficiency(self):
        return self._getAvgValue(self.getDeathsCount, self.getFragsCount)

    def getDamageEfficiency(self):
        return self._getAvgValue(self.getDamageReceived, self.getDamageDealt)

    def _getAvgValue(self, allOccursGetter, effectiveOccursGetter):
        if allOccursGetter():
            return float(effectiveOccursGetter()) / allOccursGetter()
        return 0


class VehicleDossier(_Dossier):

    def __init__(self, dossier):
        super(VehicleDossier, self).__init__(dossier, constants.DOSSIER_TYPE.VEHICLE)


class AccountDossier(_Dossier):

    def __init__(self, dossier, isCurrentUser, proxy = None):
        super(AccountDossier, self).__init__(dossier, constants.DOSSIER_TYPE.ACCOUNT, proxy)
        self.isCurrentUser = isCurrentUser
        self._vehsAvgXp = {}
        if isCurrentUser and proxy is not None:
            for intCD in self.getRecord('vehDossiersCut').iterkeys():
                vehDossier = proxy.getVehicleDossier(intCD)
                if vehDossier:
                    self._vehsAvgXp[intCD] = vehDossier.getAvgXP()

        return

    def getGlobalRating(self):
        from gui.shared import g_itemsCache
        return g_itemsCache.items.stats.getGlobalRating()

    def getVehicles(self):
        result = {}
        for intCD, (battlesCount, wins, markOfMastery, xp) in self.getRecord('vehDossiersCut').iteritems():
            avg = int(xp / battlesCount) if battlesCount else 0
            if intCD in self._vehsAvgXp:
                avg = self._vehsAvgXp[intCD]
            result[intCD] = (battlesCount,
             wins,
             markOfMastery,
             avg)

        return result

    def getMarksOfMastery(self):
        result = [0] * len(MARK_OF_MASTERY.ALL())
        for vehTypeCompDescr, (_, _, markOfMastery, _) in self.getVehicles().iteritems():
            if markOfMastery != 0:
                result[markOfMastery - 1] += 1

        return result

    def getBattlesStats(self):
        vehsByType = dict(((t, 0) for t in vehicles.VEHICLE_CLASS_TAGS))
        vehsByNation = dict(((str(idx), 0) for idx, n in enumerate(nations.NAMES)))
        vehsByLevel = dict(((str(k), 0) for k in xrange(1, constants.MAX_VEHICLE_LEVEL + 1)))
        for vehTypeCompDescr, (battlesCount, _, _, _) in self.getVehicles().iteritems():
            vehType = vehicles.getVehicleType(vehTypeCompDescr)
            vehsByNation[str(vehType.id[0])] += battlesCount
            vehsByLevel[str(vehType.level)] += battlesCount
            vehsByType[set(vehType.tags & vehicles.VEHICLE_CLASS_TAGS).pop()] += battlesCount

        return (vehsByType, vehsByNation, vehsByLevel)


class TankmanDossier(_Dossier):

    def __init__(self, tmanDescr, tmanDossier, extDossier):
        """
        @param tmanDescr: tankman descriptor
        @param tmanDossier: tankman dossier descriptor
        @param extDossier: account or vehicle dossier descriptor. Used for
                                                some calculations.
        """
        super(TankmanDossier, self).__init__(tmanDossier, constants.DOSSIER_TYPE.TANKMAN)
        self.tmanDescr = tmanDescr
        self.extDossier = extDossier

    def getNextSkillXPLeft(self):
        """
        @return: value of xp need to next skill level
        """
        if self.tmanDescr.roleLevel != tankmen.MAX_SKILL_LEVEL or not self.__isNewSkillReady():
            return self.__getSkillNextLevelCost()
        return 0

    def getAvgXP(self):
        return self.extDossier.getAvgXP()

    def getNextSkillBattlesLeft(self):
        """
        @return: value of battles need to level up last skill to 1 point.
                                Return 0 if last skill is max level. Returns None
                                if tankman and extDossier has no battles
        """
        if not self.getBattlesCount() or not self.extDossier.getBattlesCount() or not self.extDossier.getXP():
            return None
        else:
            avgExp = self.getAvgXP()
            if self.tmanDescr.roleLevel == tankmen.MAX_SKILL_LEVEL:
                newSkillReady = len(self.tmanDescr.skills) == 0 or self.tmanDescr.lastSkillLevel == tankmen.MAX_SKILL_LEVEL
                return avgExp and not newSkillReady and math.ceil(self.__getSkillNextLevelCost() / avgExp)
            return 0

    def getStats(self):
        """
        Collecting stats data for personal case
        @return: list of stats items
        """
        nextSkillsBattlesLeft = self.getNextSkillBattlesLeft()
        if nextSkillsBattlesLeft is not None:
            nextSkillsBattlesLeft = BigWorld.wg_getIntegralFormat(nextSkillsBattlesLeft)
        nextSkillBattlesLeftExtra = ''
        if not self.getBattlesCount() or not self.extDossier.getBattlesCount():
            nextSkillBattlesLeftExtra = '(%s)' % i18n.makeString('#menu:profile/stats/items/unknown')
        skillImgType, skillImg = self.__getCurrentSkillIcon()
        return ({'label': 'common',
          'stats': (self.__packStat('battlesCount', BigWorld.wg_getNiceNumberFormat(self.getBattlesCount())),)}, {'label': 'studying',
          'stats': (self.__packStat('nextSkillXPLeft', BigWorld.wg_getIntegralFormat(self.getNextSkillXPLeft()), imageType=skillImgType, image=skillImg), self.__packStat('avgExperience', BigWorld.wg_getIntegralFormat(self.getAvgXP())), self.__packStat('nextSkillBattlesLeft', nextSkillsBattlesLeft, nextSkillBattlesLeftExtra))})

    def __isNewSkillReady(self):
        """
        @return: role level is max and no skills or last skill is max
        """
        return self.tmanDescr.roleLevel == tankmen.MAX_SKILL_LEVEL and (not len(self.tmanDescr.skills) or self.tmanDescr.lastSkillLevel == tankmen.MAX_SKILL_LEVEL)

    def __getSkillNextLevelCost(self):
        """
        @return: value of xp need to next skill level
        """
        skillsCount = len(self.tmanDescr.skills)
        lastSkillLevel = self.tmanDescr.lastSkillLevel
        if not skillsCount or self.tmanDescr.roleLevel != tankmen.MAX_SKILL_LEVEL:
            lastSkillLevel = self.tmanDescr.roleLevel
        return self.tmanDescr.levelUpXpCost(lastSkillLevel, skillsCount if self.tmanDescr.roleLevel == tankmen.MAX_SKILL_LEVEL else 0) - self.tmanDescr.freeXP

    def __getCurrentSkillIcon(self):
        """
        Returns current studying skill type and icon filename
        (icon type, icon filename)
        """
        if self.__isNewSkillReady():
            return ('new_skill', 'new_skill.png')
        if self.tmanDescr.roleLevel != tankmen.MAX_SKILL_LEVEL or not len(self.tmanDescr.skills):
            return ('role', '%s.png' % self.tmanDescr.role)
        return ('skill', tankmen.getSkillsConfig()[self.tmanDescr.skills[-1]]['icon'])

    @classmethod
    def __packStat(cls, name, value, extra = '', imageType = None, image = None):
        return {'name': name,
         'value': value,
         'extra': extra,
         'imageType': imageType,
         'image': image}

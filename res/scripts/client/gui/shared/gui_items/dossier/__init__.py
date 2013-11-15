# 2013.11.15 11:26:47 EST
# Embedded file name: scripts/client/gui/shared/gui_items/dossier/__init__.py
import BigWorld
import math
import itertools
import constants
import nations
from items import tankmen, vehicles
from helpers import i18n
from debug_utils import LOG_ERROR, LOG_CURRENT_EXCEPTION, LOG_DEBUG
from gui.shared.gui_items import GUIItem, GUI_ITEM_TYPE
from gui.shared.utils import dossiers_utils
from gui.shared.gui_items.dossier import stats
from gui.shared.gui_items.dossier.achievements import MARK_OF_MASTERY
from gui.shared.gui_items.dossier.factories import getAchievementFactory, _SequenceAchieveFactory
from dossiers2.ui.achievements import ACHIEVEMENT_SECTIONS_INDICES, ACHIEVEMENT_SECTION
_BATTLE_SECTION = ACHIEVEMENT_SECTIONS_INDICES[ACHIEVEMENT_SECTION.BATTLE]
_EPIC_SECTION = ACHIEVEMENT_SECTIONS_INDICES[ACHIEVEMENT_SECTION.EPIC]
_ACTION_SECTION = ACHIEVEMENT_SECTIONS_INDICES[ACHIEVEMENT_SECTION.ACTION]
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
_NEAREST_ACHIEVEMENTS = tuple(set(_NEAREST_ACHIEVEMENTS) & set(itertools.chain(*dossiers_utils.getAccountAchievementsLayout())))
_SIGNIFICANT_ACHIEVEMENTS_PER_SECTION = 3

class _Dossier(GUIItem):

    def __init__(self, dossier, dossierType, isInRoaming = False, proxy = None):
        super(GUIItem, self).__init__()
        self.dossier = dossier
        self.dossierType = dossierType
        self.isInRoaming = isInRoaming
        self.proxy = proxy
        self.achievements = dossier['achievements']

    def getDossierDescr(self):
        return self.dossier

    def getAchievementsBlock(self):
        return self.achievements

    def getRecord(self, recordName):
        return self.dossier[recordName]

    def getAchievementRecord(self, achieveName):
        return self.achievements[achieveName]

    def getAchievements(self, isInDossier = True):
        result = []
        for section in dossiers_utils.getAchievementsLayout(self.dossierType):
            sectionAchieves = []
            for achieveName in section:
                if not dossiers_utils.isAchieveValid(achieveName, self):
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
        uncompletedAchievements = itertools.ifilter(lambda x: not x.isDone and dossiers_utils.isAchieveValid(x.name, self) and x.isInNear, achievements)

        def nearestComparator(x, y):
            if x.lvlUpValue == 1 or y.lvlUpValue == 1:
                if x.lvlUpValue == y.lvlUpValue:
                    return cmp(x.progress, y.progress)
                elif x.lvlUpValue == 1:
                    return 1
                else:
                    return -1
            else:
                return cmp(x.progress, y.progress)

        result = sorted(uncompletedAchievements, cmp=nearestComparator, reverse=True)[:_NEAREST_ACHIEVEMENTS_COUNT]
        return tuple(result)

    def getSignificantAchievements(self):
        sections = self.getAchievements()
        battleAchievements = sections[_BATTLE_SECTION]
        epicAchievements = sections[_EPIC_SECTION]
        otherAchievements = itertools.chain(*itertools.ifilter(lambda x: sections.index(x) not in (_BATTLE_SECTION, _EPIC_SECTION, _ACTION_SECTION), sections))
        achievementsQuery = (battleAchievements, epicAchievements, tuple(otherAchievements))

        def mapQueryEntry(entry):
            return sorted(entry, key=lambda x: x.weight)[:_SIGNIFICANT_ACHIEVEMENTS_PER_SECTION]

        result = itertools.chain(*map(mapQueryEntry, achievementsQuery))
        return tuple(result)


class VehicleDossier(_Dossier, stats.VehicleDossierStats):

    def __init__(self, dossier):
        super(VehicleDossier, self).__init__(dossier, GUI_ITEM_TYPE.VEHICLE_DOSSIER)

    def _getDossierDescr(self):
        return self.getDossierDescr()


class AccountDossier(_Dossier, stats.AccountDossierStats):

    def __init__(self, dossier, isCurrentUser, isInRoaming = False, proxy = None):
        super(AccountDossier, self).__init__(dossier, GUI_ITEM_TYPE.ACCOUNT_DOSSIER, isInRoaming, proxy)
        self.isCurrentUser = isCurrentUser

    def getGlobalRating(self):
        from gui.shared import g_itemsCache
        return g_itemsCache.items.stats.getGlobalRating()

    def _getDossierDescr(self):
        return self.getDossierDescr()


class TankmanDossier(_Dossier, stats.TankmanDossierStats):

    def __init__(self, tmanDescr, tmanDossier, extDossier):
        """
        @param tmanDescr: tankman descriptor
        @param tmanDossier: tankman dossier descriptor
        @param extDossier: account or vehicle dossier descriptor. Used for
                                                some calculations.
        """
        super(TankmanDossier, self).__init__(tmanDossier, GUI_ITEM_TYPE.TANKMAN_DOSSIER)
        self.tmanDescr = tmanDescr
        self.extStats = extDossier.getTotalStats()
        self.addStats = extDossier.getTeam7x7Stats()

    def getNextSkillXPLeft(self):
        """
        @return: value of xp need to next skill level
        """
        if self.tmanDescr.roleLevel != tankmen.MAX_SKILL_LEVEL or not self.__isNewSkillReady():
            return self.__getSkillNextLevelCost()
        return 0

    def getAvgXP(self):
        return (self.extStats.getAvgXP() + self.addStats.getAvgXP()) / 2

    def getBattlesCount(self):
        return self.getTotalStats().getBattlesCount()

    def getNextSkillBattlesLeft(self):
        """
        @return: value of battles need to level up last skill to 1 point.
                                Return 0 if last skill is max level. Returns None
                                if tankman and extDossier has no battles
        """
        if not self.getBattlesCount() or not self.extStats.getBattlesCount() or not self.extStats.getXP():
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
        if not self.getBattlesCount() or not self.extStats.getBattlesCount():
            nextSkillBattlesLeftExtra = '(%s)' % i18n.makeString('#menu:profile/stats/items/unknown')
        skillImgType, skillImg = self.__getCurrentSkillIcon()
        return ({'label': 'common',
          'stats': (self.__packStat('battlesCount', BigWorld.wg_getNiceNumberFormat(self.getBattlesCount())),)}, {'label': 'studying',
          'stats': (self.__packStat('nextSkillXPLeft', BigWorld.wg_getIntegralFormat(self.getNextSkillXPLeft()), imageType=skillImgType, image=skillImg), self.__packStat('avgExperience', BigWorld.wg_getIntegralFormat(self.getAvgXP())), self.__packStat('nextSkillBattlesLeft', nextSkillsBattlesLeft, nextSkillBattlesLeftExtra))})

    def _getDossierDescr(self):
        return self.getDossierDescr()

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
# okay decompyling res/scripts/client/gui/shared/gui_items/dossier/__init__.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:26:48 EST

# 2013.11.15 11:26:48 EST
# Embedded file name: scripts/client/gui/shared/gui_items/dossier/achievements.py
from collections import namedtuple
import BigWorld
from gui import nationCompareByIndex
from gui.shared.utils.RareAchievementsCache import g_rareAchievesCache
from helpers import i18n
from items import vehicles
from debug_utils import LOG_DEBUG
from gui.shared.utils import dossiers_utils, CONST_CONTAINER
from gui.shared.gui_items import GUIItem
from dossiers2.custom.config import RECORD_CONFIGS
from dossiers2.custom.cache import getCache as getDossiersCache
from dossiers2.custom.helpers import getTankExpertRequirements, getMechanicEngineerRequirements

class MARK_OF_MASTERY(CONST_CONTAINER):
    MASTER = 4
    STEP_1 = 3
    STEP_2 = 2
    STEP_3 = 1


class RegularAchievement(GUIItem):
    ICON_PATH_BIG = '../maps/icons/achievement'
    ICON_PATH_SMALL = '../maps/icons/achievement'
    ICON_DEFAULT = '../maps/icons/achievement/noImage.png'

    def __init__(self, name, dossier, proxy = None):
        super(RegularAchievement, self).__init__(proxy)
        self.name = name
        self.value = self._readValue(dossier)
        self.lvlUpTotalValue = self._readLevelUpTotalValue(dossier, proxy)
        self.lvlUpValue = self._readLevelUpValue(dossier, proxy)
        self._progress = self._calculateProgress(dossier, proxy)
        self.isDone = self._getDoneStatus(dossier, proxy)

    def __repr__(self):
        return '%s<name=%s; value=%s; levelUpValue=%s levelUpTotalValue=%s isDone=%s>' % (self.__class__.__name__,
         self.name,
         str(self.value),
         str(self.lvlUpValue),
         str(self.lvlUpTotalValue),
         str(self.isDone))

    def __cmp__(self, other):
        if isinstance(other, RegularAchievement):
            return cmp(self.weight, other.weight)
        return 1

    def getType(self):
        return dossiers_utils.getAchievementType(self.name)

    def getSection(self):
        return dossiers_utils.getAchievementSection(self.name)

    def getRecord(self):
        return dossiers_utils.getAchievementRecord(self.name)

    def getCurrentRecord(self):
        return dossiers_utils.getAchievementCurRecord(self.name)

    @property
    def icon(self):
        return {'big': '%s/%s.png' % (self.ICON_PATH_BIG, self._getIconName()),
         'small': '%s/%s.png' % (self.ICON_PATH_SMALL, self._getIconName())}

    @property
    def weight(self):
        return dossiers_utils.getAchievementWeight(self.name)

    @property
    def userName(self):
        return i18n.makeString('#achievements:%s' % self._getActualName())

    @property
    def description(self):
        return i18n.makeString('#achievements:%s_descr' % self._getActualName())

    @property
    def heroInfo(self):
        infoKey = '%s_heroInfo' % self._getActualName()
        msg = i18n.makeString('#achievements:%s' % infoKey)
        if msg == infoKey:
            return ''
        return msg

    @classmethod
    def isInDossier(cls, name, dossier):
        if dossier is not None:
            return bool(dossier.getAchievementRecord(name))
        else:
            return False

    @property
    def progress(self):
        return self._progress

    def toDict(self):
        result = super(RegularAchievement, self).toDict()
        result.update({'name': self.name,
         'userName': self.userName,
         'description': self.description,
         'type': self.getType(),
         'section': self.getSection(),
         'value': self.value,
         'levelUpValue': self.lvlUpValue,
         'isDone': self.isDone,
         'icon': self.icon})
        return result

    def _readValue(self, dossier):
        if dossier is not None:
            return dossier.getAchievementRecord(self.name)
        else:
            return 0

    def _readLevelUpValue(self, dossier, proxy):
        return None

    def _readLevelUpTotalValue(self, dossier, proxy):
        return None

    def _getIconName(self):
        return self._getActualName()

    def _calculateProgress(self, dossier, proxy):
        return 0.0

    def _getActualName(self):
        return self.name

    def _getDoneStatus(self, dossier, proxy):
        return self._progress == 1.0


class SeriesAchievement(RegularAchievement):

    def _readValue(self, dossier):
        record = self.getRecord()
        if dossier is not None and record is not None:
            return dossier.getAchievementRecord(record)
        else:
            return 0

    def _readLevelUpTotalValue(self, dossier, proxy):
        return self.value + 1

    def _readLevelUpValue(self, dossier, proxy):
        record = self.getCurrentRecord()
        if dossier is not None and record is not None:
            return self.lvlUpTotalValue - dossier.getAchievementRecord(record)
        else:
            return 0


class ClassAchievement(RegularAchievement):

    def _readLevelUpValue(self, dossier, proxy):
        record = self.getRecord()
        if dossier is None or record is None:
            return 0
        elif self.value == 1:
            return
        else:
            config = RECORD_CONFIGS[self.name]
            recordValue = dossier.getTotalStats().getRecord(record)
            return config[len(config) - self.value + 1] - recordValue

    def _getIconName(self):
        return '%s%d' % (self.name, self.value)

    @property
    def userName(self):
        userName = super(ClassAchievement, self).userName
        return userName % i18n.makeString('#achievements:achievement/rank%d' % self.value)


class HasVehiclesList(object):
    VehicleData = namedtuple('VehicleData', 'name nation level type')

    def __init__(self, dossier, proxy = None):
        self.__vehiclesCompDescrs = self._getVehiclesDescrsList(dossier, proxy)

    def _getVehiclesDescrsList(self, dossier, proxy):
        return []

    def getVehiclesData(self):
        result = []
        for vCD in self.__vehiclesCompDescrs:
            vType = vehicles.getVehicleType(vCD)
            classTag = tuple(vehicles.VEHICLE_CLASS_TAGS & vType.tags)[0]
            result.append(self.VehicleData(vType.userString, vType.id[0], vType.level, classTag)._asdict())

        return result


class SimpleProgressAchievement(RegularAchievement):

    def __init__(self, name, dossier, proxy = None):
        self._progressValue = self._readProgressValue(dossier)
        super(SimpleProgressAchievement, self).__init__(name, dossier, proxy)

    def _readLevelUpValue(self, dossier, proxy):
        minValue = RECORD_CONFIGS[self.name]
        medals, series = divmod(self._progressValue, minValue)
        return minValue - series

    def _readLevelUpTotalValue(self, dossier, proxy):
        return RECORD_CONFIGS[self.name]

    def _calculateProgress(self, dossier, proxy):
        if self.lvlUpTotalValue == 0:
            return 1.0
        return 1 - float(self.lvlUpValue) / float(self.lvlUpTotalValue)

    def _readProgressValue(self, dossier):
        return 0

    @property
    def isInNear(self):
        return self.progress >= 0.95 or self.lvlUpValue == 1


class NationSpecificAchievement(SimpleProgressAchievement):

    def __init__(self, namePrefix, nationID, dossier, isCurrentUser, proxy = None):
        if nationID != -1:
            namePrefix += str(nationID)
        self.nationID = nationID
        self.isCurrentUser = isCurrentUser
        super(NationSpecificAchievement, self).__init__(namePrefix, dossier, proxy)

    def _getVehiclesDescrsList(self, dossier, proxy):
        return ()

    def _readValue(self, dossier):
        return None

    def _readLevelUpValue(self, dossier, proxy):
        return len(self._getVehiclesDescrsList(dossier, proxy))

    def _readLevelUpTotalValue(self, dossier, proxy):
        cache = getDossiersCache()
        if self.nationID != -1:
            return len(cache['vehiclesInTreesByNation'][self.nationID])
        else:
            return len(cache['vehiclesInTrees'])

    def _getDoneStatus(self, dossier, proxy):
        return bool(dossier.getAchievementRecord(self.name))


class TankExpertAchievement(NationSpecificAchievement, HasVehiclesList):

    def __init__(self, nationID, dossier, isCurrentUser, proxy = None):
        NationSpecificAchievement.__init__(self, 'tankExpert', nationID, dossier, isCurrentUser, proxy)
        HasVehiclesList.__init__(self, dossier, proxy)

    def __cmp__(self, other):
        if isinstance(other, TankExpertAchievement):
            if self.nationID == -1:
                return -1
            elif other.nationID == -1:
                return 1
            else:
                return nationCompareByIndex(self.nationID, other.nationID)
        return super(TankExpertAchievement, self).__cmp__(other)

    def _getVehiclesDescrsList(self, dossier, proxy):
        return getTankExpertRequirements(dossier.getRecord('vehTypeFrags')).get(self.name, [])


class MechEngineerAchievement(NationSpecificAchievement, HasVehiclesList):

    def __init__(self, nationID, dossier, isCurrentUser, proxy = None):
        NationSpecificAchievement.__init__(self, 'mechanicEngineer', nationID, dossier, isCurrentUser, proxy)
        HasVehiclesList.__init__(self, dossier, proxy)

    def __cmp__(self, other):
        if isinstance(other, MechEngineerAchievement):
            if self.nationID == -1:
                return -1
            elif other.nationID == -1:
                return 1
            else:
                return nationCompareByIndex(self.nationID, other.nationID)
        return super(MechEngineerAchievement, self).__cmp__(other)

    def _getVehiclesDescrsList(self, dossier, proxy):
        if proxy is not None and self.isCurrentUser:
            return getMechanicEngineerRequirements(set(), proxy.stats.unlocks, self.nationID).get(self.name, [])
        else:
            return []


class WhiteTigerAchievement(RegularAchievement):
    WHITE_TIGER_COMP_DESCR = 56337

    def __init__(self, dossier, proxy = None):
        super(WhiteTigerAchievement, self).__init__('whiteTiger', dossier, proxy)

    @classmethod
    def __getWhiteTigerKillings(cls, dossier):
        return dossier.getRecord('vehTypeFrags').get(cls.WHITE_TIGER_COMP_DESCR, 0)

    def _readValue(self, dossier):
        if dossier is not None:
            return self.__getWhiteTigerKillings(dossier)
        else:
            return 0

    @classmethod
    def isInDossier(cls, name, dossier):
        return bool(cls.__getWhiteTigerKillings(dossier))


class MousebaneAchievement(SimpleProgressAchievement):

    def __init__(self, dossier, proxy = None):
        super(MousebaneAchievement, self).__init__('mousebane', dossier, proxy)

    def _readProgressValue(self, dossier):
        return dossier.getRecord('vehTypeFrags').get(getDossiersCache()['mausTypeCompDescr'], 0)


class BeasthunterAchievement(SimpleProgressAchievement):

    def __init__(self, dossier, proxy = None):
        super(BeasthunterAchievement, self).__init__('beasthunter', dossier, proxy)

    def _readProgressValue(self, dossier):
        return dossier.getAchievementRecord('fragsBeast')


class PattonValleyAchievement(SimpleProgressAchievement):

    def __init__(self, dossier, proxy = None):
        super(PattonValleyAchievement, self).__init__('pattonValley', dossier, proxy)

    def _readProgressValue(self, dossier):
        return dossier.getAchievementRecord('fragsPatton')


class SinaiAchievement(SimpleProgressAchievement):

    def __init__(self, dossier, proxy = None):
        super(SinaiAchievement, self).__init__('sinai', dossier, proxy)

    def _readProgressValue(self, dossier):
        return dossier.getAchievementRecord('fragsSinai')


class ClassProgressAchievement(SimpleProgressAchievement):
    MIN_LVL = 4

    def __init__(self, name, dossier, proxy = None):
        self._currentProgressValue = self._readCurrentProgressValue(dossier)
        super(ClassProgressAchievement, self).__init__(name, dossier, proxy)

    def _readLevelUpTotalValue(self, dossier, proxy):
        progressValue = self._progressValue if self._progressValue else 5
        medalCfg = RECORD_CONFIGS[self.name]
        maxMedalClass = len(medalCfg)
        nextMedalClass = progressValue - 1
        nextMedalClassIndex = maxMedalClass - nextMedalClass
        if nextMedalClass <= 0:
            return 0.0
        elif nextMedalClass <= maxMedalClass:
            return medalCfg[nextMedalClassIndex]
        else:
            return 1.0

    def _readLevelUpValue(self, dossier, proxy):
        if self._progressValue == 1:
            return 0.0
        else:
            return float(self.lvlUpTotalValue) - float(self._currentProgressValue)

    def _calculateProgress(self, dossier, proxy):
        if self._progressValue == 1:
            return 1.0
        elif self.lvlUpTotalValue == 0:
            return 1.0
        else:
            return 1 - float(self.lvlUpValue) / float(self.lvlUpTotalValue)

    def _readCurrentProgressValue(self, dossier):
        return 0

    def _getActualName(self):
        return '%s%d' % (self.name, self.value or self.MIN_LVL)


class MedalKnispelAchievement(ClassProgressAchievement):

    def __init__(self, dossier, proxy = None):
        super(MedalKnispelAchievement, self).__init__('medalKnispel', dossier, proxy)

    def _readProgressValue(self, dossier):
        return dossier.getAchievementRecord('medalKnispel')

    def _readCurrentProgressValue(self, dossier):
        total = dossier.getTotalStats()
        _7x7 = dossier.getTeam7x7Stats()
        return total.getDamageDealt() + total.getDamageReceived() + _7x7.getDamageDealt() + _7x7.getDamageReceived()


class MedalCariusAchievement(ClassProgressAchievement):

    def __init__(self, dossier, proxy = None):
        super(MedalCariusAchievement, self).__init__('medalCarius', dossier, proxy)

    def _readProgressValue(self, dossier):
        return dossier.getAchievementRecord('medalCarius')

    def _readCurrentProgressValue(self, dossier):
        total = dossier.getTotalStats()
        _7x7 = dossier.getTeam7x7Stats()
        return total.getFragsCount() + _7x7.getFragsCount()


class MedalAbramsAchievement(ClassProgressAchievement):

    def __init__(self, dossier, proxy = None):
        super(MedalAbramsAchievement, self).__init__('medalAbrams', dossier, proxy)

    def _readProgressValue(self, dossier):
        return dossier.getAchievementRecord('medalAbrams')

    def _readCurrentProgressValue(self, dossier):
        total = dossier.getTotalStats()
        _7x7 = dossier.getTeam7x7Stats()
        return total.getWinAndSurvived() + _7x7.getWinAndSurvived()


class MedalPoppelAchievement(ClassProgressAchievement):

    def __init__(self, dossier, proxy = None):
        super(MedalPoppelAchievement, self).__init__('medalPoppel', dossier, proxy)

    def _readProgressValue(self, dossier):
        return dossier.getAchievementRecord('medalPoppel')

    def _readCurrentProgressValue(self, dossier):
        total = dossier.getTotalStats()
        _7x7 = dossier.getTeam7x7Stats()
        return total.getSpottedEnemiesCount() + _7x7.getSpottedEnemiesCount()


class MedalKayAchievement(ClassProgressAchievement):

    def __init__(self, dossier, proxy = None):
        super(MedalKayAchievement, self).__init__('medalKay', dossier, proxy)

    def _readProgressValue(self, dossier):
        return dossier.getAchievementRecord('medalKay')

    def _readCurrentProgressValue(self, dossier):
        return dossier.getAchievementRecord('battleHeroes')


class MedalEkinsAchievement(ClassProgressAchievement):

    def __init__(self, dossier, proxy = None):
        super(MedalEkinsAchievement, self).__init__('medalEkins', dossier, proxy)

    def _readProgressValue(self, dossier):
        return dossier.getAchievementRecord('medalEkins')

    def _readCurrentProgressValue(self, dossier):
        total = dossier.getTotalStats()
        _7x7 = dossier.getTeam7x7Stats()
        return total.getFrags8p() + _7x7.getFrags8p()


class MedalLeClercAchievement(ClassProgressAchievement):

    def __init__(self, dossier, proxy = None):
        super(MedalLeClercAchievement, self).__init__('medalLeClerc', dossier, proxy)

    def _readProgressValue(self, dossier):
        return dossier.getAchievementRecord('medalLeClerc')

    def _readCurrentProgressValue(self, dossier):
        total = dossier.getTotalStats()
        _7x7 = dossier.getTeam7x7Stats()
        return total.getCapturePoints() + _7x7.getCapturePoints()


class MedalLavrinenkoAchievement(ClassProgressAchievement):

    def __init__(self, dossier, proxy = None):
        super(MedalLavrinenkoAchievement, self).__init__('medalLavrinenko', dossier, proxy)

    def _readProgressValue(self, dossier):
        return dossier.getAchievementRecord('medalLavrinenko')

    def _readCurrentProgressValue(self, dossier):
        total = dossier.getTotalStats()
        _7x7 = dossier.getTeam7x7Stats()
        return total.getDroppedCapturePoints() + _7x7.getDroppedCapturePoints()


class RareAchievement(RegularAchievement):

    def __init__(self, rareID, dossier, proxy = None):
        super(RareAchievement, self).__init__('rareAchievements', dossier, proxy)
        self.rareID = rareID

    @property
    def userName(self):
        return g_rareAchievesCache.getTitle(self.rareID)

    @property
    def description(self):
        return g_rareAchievesCache.getDescription(self.rareID)

    @classmethod
    def isInDossier(cls, rareID, dossier):
        if dossier is not None:
            return rareID in dossier.getRecord('rareAchievements')
        else:
            return False

    def requestImageID(self):
        import imghdr, uuid
        g_rareAchievesCache.request([self.rareID])
        iconId = None
        iconData = g_rareAchievesCache.getImageData(self.rareID)
        if iconData and imghdr.what(None, iconData) is not None:
            iconId = str(uuid.uuid4())
            BigWorld.wg_addTempScaleformTexture(iconId, iconData)
        return iconId

    def _getIconName(self):
        return 'actionUnknown'

    def _readValue(self, dossier):
        return None

    def __repr__(self):
        return '%s<rareID=%s>' % (self.__class__.__name__, str(self.rareID))
# okay decompyling res/scripts/client/gui/shared/gui_items/dossier/achievements.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:26:48 EST

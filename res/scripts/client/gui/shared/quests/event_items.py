import time
from datetime import datetime
from abc import ABCMeta
import constants
from helpers import getLocalizedData, i18n, time_utils
from debug_utils import LOG_DEBUG
from gui.shared.quests.bonuses import getBonusObj
from gui.shared.quests.conditions import getConditionObj
from gui.Scaleform.locale.QUESTS import QUESTS

class ServerEventAbstract(object):
    __metaclass__ = ABCMeta

    def __init__(self, eID, data):
        self._id = eID
        self._data = data

    def getID(self):
        return self._id

    def getType(self):
        return self._data.get('type', 0)

    def getStartTime(self):
        if 'startTime' in self._data:
            return time_utils.makeLocalServerTime(self._data['startTime'])
        return time.time()

    def getFinishTime(self):
        if 'finishTime' in self._data:
            return time_utils.makeLocalServerTime(self._data['finishTime'])
        return time.time()

    def getCreationTime(self):
        if 'gStartTime' in self._data:
            return time_utils.makeLocalServerTime(self._data['gStartTime'])
        return time.time()

    def getDestroyingTime(self):
        if 'gFinishTime' in self._data:
            return time_utils.makeLocalServerTime(self._data['gFinishTime'])
        return time.time()

    def getCreationTimeLeft(self):
        return self._getTimeLeft(self.getCreationTime())

    def getDestroyingTimeLeft(self):
        return self._getTimeLeft(self.getDestroyingTime())

    def getUserName(self):
        return getLocalizedData(self._data, 'name')

    def getDescription(self):
        return getLocalizedData(self._data, 'description')

    def getProgressExpiryTime(self):
        return self._data.get('progressExpiryTime', time.time())

    def _getTimeLeft(self, t):
        if t and datetime.utcfromtimestamp(t) > datetime.utcnow():
            delta = datetime.utcfromtimestamp(t) - datetime.utcnow()
            return delta.days * 3600 * 24 + delta.seconds
        return 0


class Quest(ServerEventAbstract):
    STRATEGIC_QUEST_IDX = 0

    def __init__(self, qID, data, progress = None, group = None):
        super(Quest, self).__init__(qID, data)
        self._progress = progress
        self._isPrevTaskCompleted = True
        self._groupIDs = []
        self._isSerial = False
        self._isParallel = False

    def isIGR(self):
        return self._data.get('isIGR', False)

    def isDaily(self):
        bonus = self._data.get('conditions', {}).get('bonus', {})
        return 'daily' in bonus

    def isCompleted(self):
        groupBy = self.getCumulativeGroup()
        if groupBy is None:
            return self.getBonusCount() == self.getBonusLimit()
        else:
            return False

    def isAvailable(self):
        if not self._isPrevTaskCompleted:
            return False
        from gui import game_control
        if self.isIGR() and game_control.g_instance.igr.getRoomType() != constants.IGR_TYPE.PREMIUM:
            return False
        if self.getStartTimeLeft() > 0:
            return False
        if not self._checkForInvVehicles():
            return False
        return True

    def getGroup(self):
        return list(self._groupIDs)

    def setGroup(self, questsGroup):

        def sorting(a, b):
            if a.isStrategic():
                return -1
            if b.isStrategic():
                return 1
            return a.getSeqID() - b.getSeqID()

        group = sorted(questsGroup, sorting)
        self._groupIDs = tuple((q.getID() for q in group))
        if self.isStrategic() or self.isSubtask():
            seqIDs = tuple((q.getSeqID() for q in group))
            self._isSerial = -1 not in seqIDs
            self._isParallel = not self._isSerial
        if self.isSubtask() and self.getSeqID() > -1:
            for idx, q in enumerate(group):
                prevTask = group[idx - 1]
                if q.getID() == self.getID() and not q.isStrategic() and not prevTask.isStrategic():
                    self._isPrevTaskCompleted = prevTask.isCompleted()
                    break

    def getSeqID(self):
        return self._data.get('seqID', -1)

    def getGroupID(self):
        return self._data.get('groupID') or None

    def isStrategic(self):
        return self.getGroupID() is not None and self.getSeqID() == self.STRATEGIC_QUEST_IDX

    def isSubtask(self):
        return self.getGroupID() is not None and self.getSeqID() != self.STRATEGIC_QUEST_IDX

    def getCumulativeGroup(self):
        bonus = self._data.get('conditions', {}).get('bonus', {})
        return bonus.get('groupBy', {}).get('value')

    def isCumulativeUnit(self):
        bonus = self._data.get('conditions', {}).get('bonus', {})
        return 'unit' in bonus

    def isSerialGroup(self):
        return self._isSerial

    def isParallelGroup(self):
        return self._isParallel

    def getUserType(self):
        if self.getType() == constants.EVENT_TYPE.ACTION:
            return i18n.makeString(QUESTS.ITEM_TYPE_ACTION)
        if self.getType() == constants.EVENT_TYPE.BATTLE_QUEST:
            if self.isStrategic():
                return i18n.makeString('#quests:item/type/questStrategic')
            else:
                return i18n.makeString(QUESTS.ITEM_TYPE_QUEST)
        return ''

    def getStartTimeLeft(self):
        return self._getTimeLeft(self.getStartTime())

    def getFinishTimeLeft(self):
        return self._getTimeLeft(self.getFinishTime())

    def getBonusCount(self):
        if self._progress is not None:
            groupBy = self.getCumulativeGroup()
            if groupBy is None:
                return self._progress.get(None, {}).get('bonusCount', 0)
            return sum((p.get('bonusCount', 0) for p in self._progress.itervalues()))
        else:
            return 0

    def getProgressData(self):
        return self._progress or {}

    def getProgress(self):
        for condName, cond in self.getConditions().iteritems():
            return cond.getProgress()

        return None

    def getBonusLimit(self):
        bonus = self._data.get('conditions', {}).get('bonus', {})
        return bonus.get('bonusLimit', {}).get('value')

    def getBonuses(self, getAll = False):
        result = {}
        for n, v in self._data.get('bonus', {}).iteritems():
            if n == 'meta' and self.isIGR() and not getAll:
                continue
            b = getBonusObj(n, v)
            if b is not None:
                result[n] = b

        return result

    def getConditions(self):
        return self.__parseConditions(self._data.get('conditions', {}))

    def _checkForInvVehicles(self):
        c = self.getConditions().get('/preBattle/vehicle/vehicleDescr')
        if c is None:
            return True
        else:
            for v in c.parse():
                if v.invID > 0:
                    return True

            return False

    def __parseConditions(self, data, rootPrefix = ''):
        result = {}
        if isinstance(data, dict):
            for n, v in data.iteritems():
                name = '%s/%s' % (rootPrefix, n)
                c = getConditionObj(n, v, self)
                if c is not None:
                    result[name] = c
                else:
                    result.update(self.__parseConditions(v, name))

        return result

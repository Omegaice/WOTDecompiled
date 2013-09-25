# Embedded file name: scripts/client/gui/shared/quests/conditions.py
import operator
import constants
import nations
from helpers import getLocalizedData
from debug_utils import LOG_DEBUG
from gui.shared import g_itemsCache, REQ_CRITERIA
from gui.shared.utils import CONST_CONTAINER

class RELATIONS(CONST_CONTAINER):
    GT = 'greater'
    LS = 'less'
    EQ = 'equal'
    LSQ = 'lessOrEqual'
    GTQ = 'greaterOrEqual'


class SimpleCondition(object):

    def __init__(self, name, value, quest):
        self._name = name
        self._value = value
        self._progress = self._parseProgress(value, quest)
        self.__cachedValue = None
        return

    def getName(self):
        return self._name

    def getValue(self):
        return self._value

    def getProgress(self):
        return self._progress

    def parse(self):
        if self.__cachedValue is not None:
            return self.__cachedValue
        else:
            self.__cachedValue = self._parse()
            return self.__cachedValue

    def isShowInGUI(self):
        return False

    def _parse(self):
        return str(self._value)

    def _parseProgress(self, value, quest):
        return None

    def _parseGroupedProgress(self, optName, value, quest):
        groupByKey, current, total, otherProgs = (None,
         0,
         value,
         [])
        groupBy = quest.getCumulativeGroup()
        if groupBy is None:
            current, otherProgs = quest.getProgressData().get(None, {}).get(optName, 0), []
        else:
            bonusLimit = quest.getBonusLimit()
            progresses = []
            for gByKey, progress in quest.getProgressData().iteritems():
                if progress.get('bonusCount', 0) < bonusLimit:
                    progresses.append((gByKey, progress.get(optName, 0), progress))

            progresses = sorted(progresses, key=operator.itemgetter(1), reverse=True)
            if len(progresses):
                groupByKey, current, progress = progresses[0]
                otherProgs = tuple((k for k, _, _ in progresses[1:]))
        return (groupByKey,
         current,
         total,
         otherProgs)


class MetaCondition(SimpleCondition):

    def isShowInGUI(self):
        return True

    def _parse(self):
        return getLocalizedData({'value': self._value}, 'value')


class VehsCondition(SimpleCondition):

    def __init__(self, name, value, quest):
        self._relation = self.__parseRelation(value)
        super(VehsCondition, self).__init__(name, value, quest)

    def isShowInGUI(self):
        return True

    def _getCustomFilter(self):
        return REQ_CRITERIA.EMPTY

    def _parse(self):
        criteria = ~REQ_CRITERIA.HIDDEN | self._getCustomFilter()
        if 'types' in self._value:
            criteria |= REQ_CRITERIA.VEHICLE.SPECIFIC(self._value['types']['value'])
        else:
            if 'nations' in self._value:
                criteria |= REQ_CRITERIA.NATIONS(self._value['nations']['value'])
            if 'levels' in self._value:
                criteria |= REQ_CRITERIA.VEHICLE.LEVELS(self._value['levels']['value'])
            if 'classes' in self._value:
                criteria |= REQ_CRITERIA.VEHICLE.TYPES(self._value['classes']['value'])
        return sorted(g_itemsCache.items.getVehicles(criteria).itervalues())

    def __parseRelation(self, value):
        res = set(RELATIONS.ALL()) & set(value.keys())
        if len(res):
            return res.pop()
        else:
            return None


class VehsKillsCondition(VehsCondition):

    def _parseProgress(self, value, quest):
        groupByKey, current, total, otherProgs = self._parseGroupedProgress('vehicleKills', value.get(self._relation, {}).get('value', 0), quest)
        return (groupByKey,
         current,
         total,
         'kills',
         otherProgs)


class VehsDescrCondition(VehsCondition):

    def __init__(self, name, value, quest):
        super(VehsDescrCondition, self).__init__(name, value, quest)
        self._isPremium = self._isPremium = quest._data['conditions']['preBattle']['vehicle'].get('premium', {}).get('value')

    def _getCustomFilter(self):
        if self._isPremium is not None:
            if self._isPremium:
                return REQ_CRITERIA.VEHICLE.PREMIUM
            else:
                return ~REQ_CRITERIA.VEHICLE.PREMIUM
        return REQ_CRITERIA.EMPTY


class BattlesCondition(SimpleCondition):

    def _parseProgress(self, value, quest):
        label = 'battles'
        if quest._data.get('conditions', {}).get('postBattle', {}).get('win'):
            label = 'wins'
        groupByKey, current, total, otherProgs = self._parseGroupedProgress('battlesCount', value.get('value', 0), quest)
        return (groupByKey,
         current,
         total,
         label,
         otherProgs)


class CumulativeCondition(SimpleCondition):

    def _parseProgress(self, value, quest):
        optName, optVal = value.get('value', (None, 0))
        if optName is None:
            return
        else:
            if quest.isCumulativeUnit():
                optName = 'unit_%s' % optName
            groupByKey, current, total, otherProgs = self._parseGroupedProgress(optName, optVal, quest)
            return (groupByKey,
             current,
             total,
             optName,
             otherProgs)


class PremiumCondition(SimpleCondition):

    def _parse(self):
        if self._value is not None:
            return self._value.get('value')
        else:
            return


_CONDITIONS = {'meta': MetaCondition,
 'vehicleDescr': VehsDescrCondition,
 'vehicleKills': VehsKillsCondition,
 'vehiclesUnlocked': VehsCondition,
 'battles': BattlesCondition,
 'cumulative': CumulativeCondition,
 'premium': PremiumCondition}

def getConditionObj(name, value, quest):
    if name in _CONDITIONS:
        return _CONDITIONS[name](name, value, quest)
    else:
        return None
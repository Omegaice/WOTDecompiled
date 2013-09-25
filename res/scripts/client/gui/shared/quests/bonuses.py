import BigWorld
from debug_utils import LOG_DEBUG
from helpers import getLocalizedData, i18n
from gui import makeHtmlString
from gui.shared import g_itemsCache

class SimpleBonus(object):

    def __init__(self, name, value):
        self._name = name
        self._value = value

    def getName(self):
        return self._name

    def getValue(self):
        return self._value

    def formatValue(self):
        return str(self._value)

    def format(self):
        if self._name is not None:
            text = makeHtmlString('html_templates:lobby/quests/bonuses', self._name, {'value': self.formatValue()})
            if text != self._name:
                return text
        return self.formatValue()


class IntegralBonus(SimpleBonus):

    def formatValue(self):
        return BigWorld.wg_getIntegralFormat(self._value)


class FloatBonus(SimpleBonus):

    def formatValue(self):
        return BigWorld.wg_getNiceNumberFormat(self._value)


class GoldBonus(SimpleBonus):

    def formatValue(self):
        return BigWorld.wg_getGoldFormat(self._value)


class MetaBonus(SimpleBonus):

    def formatValue(self):
        return getLocalizedData({'value': self._value}, 'value')


class ItemsBonus(SimpleBonus):

    def format(self):
        result = []
        if self._value is not None:
            for intCD, count in self._value.iteritems():
                item = g_itemsCache.items.getItemByCD(intCD)
                if item is not None:
                    result.append(i18n.makeString('#quests:bonuses/items/name', name=item.userName, count=count))

        return ', '.join(result)


class VehiclesBonus(SimpleBonus):
    DEFAULT_CREW_LVL = 50

    def format(self):
        result = []
        if self._value is not None:
            for intCD, crew in self._value.iteritems():
                item = g_itemsCache.items.getItemByCD(intCD)
                if item is not None:
                    crewLvl = i18n.makeString('#quests:bonuses/vehicles/crewLvl', crew.get('crewLvl', self.DEFAULT_CREW_LVL))
                    result.append(i18n.makeString('#quests:bonuses/vehicles/name', name=item.userName, crew=crewLvl))

        return ', '.join(result)


_BONUSES = {'credits': IntegralBonus,
 'gold': GoldBonus,
 'xp': IntegralBonus,
 'freeXP': IntegralBonus,
 'tankmenXP': IntegralBonus,
 'xpFactor': FloatBonus,
 'creditsFactor': FloatBonus,
 'freeXPFactor': FloatBonus,
 'tankmenXPFactor': FloatBonus,
 'dailyXPFactor': FloatBonus,
 'items': ItemsBonus,
 'slots': IntegralBonus,
 'berths': IntegralBonus,
 'premium': IntegralBonus,
 'vehicles': VehiclesBonus,
 'meta': MetaBonus}

def getBonusObj(name, value):
    if name in _BONUSES:
        return _BONUSES[name](name, value)
    else:
        return None

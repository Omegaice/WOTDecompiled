# Embedded file name: scripts/client/gui/Scaleform/daapi/view/lobby/techtree/__init__.py
from collections import namedtuple, defaultdict
from items import ITEM_TYPE_NAMES, getTypeInfoByName
from items.vehicles import _VEHICLE, _TURRET, _GUN, _CHASSIS, _RADIO, _ENGINE
from items.vehicles import VEHICLE_CLASS_TAGS
import nations
SMALL_ICONS_PATH = '../maps/icons/%(type)s/small/%(unicName)s.png'
TREE_SHARED_REL_FILE_PATH = 'gui/flash/techtree/tree-shared.xml'
NATION_TREE_REL_FILE_PATH = 'gui/flash/techtree/%s-tree.xml'
USE_XML_DUMPING = False
_VEHICLE_TYPE_NAME = ITEM_TYPE_NAMES[_VEHICLE]
_GUN_TYPE_NAME = ITEM_TYPE_NAMES[_GUN]
_TURRET_TYPE_NAME = ITEM_TYPE_NAMES[_TURRET]
_PREMIUM_TAGS = frozenset(['premium'])
_RESEARCH_ITEMS = (_GUN,
 _TURRET,
 _RADIO,
 _ENGINE,
 _CHASSIS)
MAX_PATH_LIMIT = 5

class NODE_STATE:
    LOCKED = 1
    NEXT_2_UNLOCK = 2
    UNLOCKED = 4
    ENOUGH_XP = 8
    ENOUGH_MONEY = 16
    IN_INVENTORY = 32
    WAS_IN_BATTLE = 64
    ELITE = 128
    PREMIUM = 256
    SELECTED = 512
    AUTO_UNLOCKED = 1024
    INSTALLED = 2048
    SHOP_ACTION = 4096
    CAN_SELL = 8192

    @classmethod
    def add(cls, state, flag):
        if not state & flag:
            state |= flag
            return state
        return -1

    @classmethod
    def addIfNot(cls, state, flag):
        if not state & flag:
            state |= flag
        return state

    @classmethod
    def remove(cls, state, flag):
        if state & flag > 0:
            state ^= flag
            return state
        return -1

    @classmethod
    def removeIfHas(cls, state, flag):
        if state & flag > 0:
            state ^= flag
        return state

    @classmethod
    def isAvailable2Unlock(cls, state):
        return not state & cls.UNLOCKED and state & cls.NEXT_2_UNLOCK and state & cls.ENOUGH_XP

    @classmethod
    def isAvailable2Buy(cls, state):
        return not state & cls.IN_INVENTORY and state & cls.UNLOCKED and state & cls.ENOUGH_MONEY

    @classmethod
    def isBuyForCredits(cls, state):
        return state & cls.UNLOCKED and not state & cls.IN_INVENTORY and not state & cls.PREMIUM

    @classmethod
    def isBuyForGold(cls, state):
        return state & cls.UNLOCKED and not state & cls.IN_INVENTORY and state & cls.PREMIUM

    @classmethod
    def change2Unlocked(cls, state):
        if state & NODE_STATE.UNLOCKED > 0:
            return -1
        if state & cls.LOCKED > 0:
            state ^= cls.LOCKED
        if state & cls.NEXT_2_UNLOCK > 0:
            state ^= cls.NEXT_2_UNLOCK
            if state & cls.ENOUGH_XP > 0:
                state ^= cls.ENOUGH_XP
        state |= cls.UNLOCKED
        return state


class UnlockProps(namedtuple('UnlockProps', 'parentID unlockIdx xpCost required')):

    def _makeTuple(self):
        return (self.parentID,
         self.unlockIdx,
         self.xpCost,
         list(self.required))


def makeDefUnlockProps():
    return UnlockProps(0, -1, 0, set())


class SelectedNation(object):
    __index = None

    @classmethod
    def byDefault(cls):
        if cls.__index is None:
            from CurrentVehicle import g_currentVehicle
            cls.__index = g_currentVehicle.item.nationID if g_currentVehicle.isPresent() else 0
        return

    @classmethod
    def select(cls, index):
        cls.__index = index

    @classmethod
    def getIndex(cls):
        return cls.__index

    @classmethod
    def getName(cls):
        return nations.NAMES[cls.__index]


class RequestState(object):
    __states = set()

    @classmethod
    def sent(cls, name):
        cls.__states.add(name)

    @classmethod
    def received(cls, name):
        if name in cls.__states:
            cls.__states.remove(name)

    @classmethod
    def inProcess(cls, name):
        return name in cls.__states


class VehicleClassInfo(object):
    __slots__ = ('__info',)

    def __init__(self):
        super(VehicleClassInfo, self).__init__()
        self.__info = defaultdict(lambda : {'userString': '',
         'name': ''})
        for tag in VEHICLE_CLASS_TAGS:
            info = getTypeInfoByName(_VEHICLE_TYPE_NAME)['tags'][tag]
            self.__info[frozenset((tag,))] = {'userString': info['userString'],
             'name': info['name']}

    def getInfoByTags(self, tags):
        return self.__info[VEHICLE_CLASS_TAGS & tags]

    def clear(self):
        self.__info.clear()


__all__ = ['USE_XML_DUMPING',
 'NODE_STATE',
 'RequestState',
 'SelectedNation',
 'UnlockProps',
 'makeDefUnlockProps',
 'listeners',
 'VehicleClassInfo',
 'tech_tree_dp',
 'customs_items',
 'dumpers',
 'data',
 'MAX_PATH_LIMIT',
 '_VEHICLE',
 '_VEHICLE_TYPE_NAME',
 '_PREMIUM_TAGS',
 '_RESEARCH_ITEMS',
 '_TURRET',
 '_TURRET_TYPE_NAME',
 '_GUN',
 '_GUN_TYPE_NAME',
 'SMALL_ICONS_PATH',
 'TREE_SHARED_REL_FILE_PATH',
 'NATION_TREE_REL_FILE_PATH']
# 2013.11.15 11:25:44 EST
# Embedded file name: scripts/client/gui/prb_control/info.py
import BigWorld
from collections import namedtuple
import itertools
import weakref
from UnitBase import UNIT_STATE, UNIT_ROLE
from account_helpers import getPlayerDatabaseID, getPlayerID
from constants import PREBATTLE_ACCOUNT_STATE, PREBATTLE_TEAM_STATE
from gui.LobbyContext import g_lobbyContext
from gui.prb_control import events_dispatcher
from gui.prb_control.settings import DEFAULT_PREBATTLE_COOLDOWN
from gui.shared import g_itemsCache, REQ_CRITERIA
from gui.shared.gui_items.Vehicle import Vehicle

class PlayerPrbInfo(object):
    __slots__ = ('accID', 'name', 'dbID', 'state', 'time', 'vehCompDescr', 'clanDBID', 'clanAbbrev', 'roster', 'isCreator', 'regionCode')

    def __init__(self, accID, name = '', dbID = 0L, state = PREBATTLE_ACCOUNT_STATE.UNKNOWN, time = 0.0, vehCompDescr = 0, clanDBID = 0L, clanAbbrev = '', roster = 0, functional = None):
        self.accID = accID
        self.name = name
        self.dbID = dbID
        self.state = state
        self.time = time
        self.vehCompDescr = vehCompDescr
        self.clanDBID = clanDBID
        self.clanAbbrev = clanAbbrev
        self.roster = roster
        if functional is not None:
            self.isCreator = functional.isCreator(pDatabaseID=self.dbID)
        else:
            self.isCreator = False
        return

    def __repr__(self):
        return 'PlayerPrbInfo(accID = {0:n}, dbID = {1:n}, fullName = {2:>s}, state = {3:n}, isCreator = {4!r:s}, time = {5:n}, vehCompDescr = {6!r:s})'.format(self.accID, self.dbID, self.getFullName(), self.state, self.isCreator, self.time, self.getVehicle().name if self.isVehicleSpecified() else None)

    def getFullName(self, isClan = True, isRegion = True):
        if isClan:
            clanAbbrev = self.clanAbbrev
        else:
            clanAbbrev = None
        if isRegion:
            pDBID = self.dbID
        else:
            pDBID = None
        return g_lobbyContext.getPlayerFullName(self.name, clanAbbrev=clanAbbrev, pDBID=pDBID)

    def isVehicleSpecified(self):
        return self.isReady() or self.inBattle()

    def getVehicle(self):
        return Vehicle(self.vehCompDescr)

    def isCurrentPlayer(self):
        if self.dbID > 0:
            result = self.dbID == getPlayerDatabaseID()
        else:
            result = self.accID == getPlayerID()
        return result

    def isReady(self):
        return self.state & PREBATTLE_ACCOUNT_STATE.READY != 0

    def inBattle(self):
        return self.state & PREBATTLE_ACCOUNT_STATE.IN_BATTLE != 0

    def isOffline(self):
        return self.state & PREBATTLE_ACCOUNT_STATE.OFFLINE != 0


class TeamStateInfo(object):
    __slots__ = ('state',)

    def __init__(self, state):
        super(TeamStateInfo, self).__init__()
        self.state = state

    def __repr__(self):
        return 'TeamStateInfo(state = {0:n}, isNotReady = {1!r:s}, isReady = {2!r:s}, isLocked = {3!r:s}, isInQueue = {4:n}'.format(self.state, self.isNotReady(), self.isReady(), self.isLocked(), self.isInQueue())

    def isNotReady(self):
        return self.state is PREBATTLE_TEAM_STATE.NOT_READY

    def isReady(self):
        return self.state is PREBATTLE_TEAM_STATE.READY

    def isLocked(self):
        return self.state is PREBATTLE_TEAM_STATE.LOCKED

    def isInQueue(self):
        return self.state in [PREBATTLE_TEAM_STATE.READY, PREBATTLE_TEAM_STATE.LOCKED]


PlayersStateStats = namedtuple('PlayersStateStats', ('notReadyCount', 'haveInBattle', 'playersCount', 'limitMaxCount'))

class PrbPropsInfo(object):
    __slots__ = ('wins', 'battlesCount', 'createTime')

    def __init__(self, wins = None, battlesCount = 0, createTime = None):
        super(PrbPropsInfo, self).__init__()
        self.wins = wins or [0, 0, 0]
        self.battlesCount = battlesCount
        self.createTime = createTime

    def getBattlesScore(self):
        return '%d:%d' % (self.wins[1], self.wins[2])

    def __repr__(self):
        return 'PrbPropsInfo(wins = {0!r:s}, battlesCount = {1:n}, createTime = {2:n}'.format(self.wins, self.battlesCount, self.createTime)


class PlayerUnitInfo(object):
    __slots__ = ('dbID', 'unitIdx', 'unit', 'name', 'rating', 'role', 'accID', 'vehDict', 'isReady', 'isInSlot', 'slotIdx', 'regionCode', 'clanAbbrev')

    def __init__(self, dbID, unitIdx, unit, nickName = '', rating = 0, role = 0, accountID = 0, vehDict = None, isReady = False, isInSlot = False, slotIdx = -1, clanAbbrev = None, **kwargs):
        self.dbID = dbID
        self.unitIdx = unitIdx
        self.unit = weakref.proxy(unit)
        self.name = nickName
        self.rating = rating
        self.role = role
        self.accID = accountID
        self.vehDict = vehDict or {}
        self.isReady = isReady
        self.isInSlot = isInSlot
        self.slotIdx = slotIdx
        self.clanAbbrev = clanAbbrev

    def __repr__(self):
        return 'PlayerUnitInfo(dbID = {0:n}, fullName = {1:>s}, unitIdx = {2:n} rating = {3:n}, isCreator = {4!r:s}, role = {5:n}, accID = {6:n}, isReady={7!r:s}, isInSlot={8!r:s})'.format(self.dbID, self.getFullName(), self.unitIdx, self.rating, self.isCreator(), self.role, self.accID, self.isReady, self.isInSlot)

    def getFullName(self):
        return g_lobbyContext.getPlayerFullName(self.name, clanAbbrev=self.clanAbbrev, pDBID=self.dbID)

    def isCreator(self):
        return self.role & UNIT_ROLE.COMMANDER_UPDATES > 0

    def isInvite(self):
        return self.role & UNIT_ROLE.INVITED > 0

    def isInArena(self):
        return self.role & UNIT_ROLE.IN_ARENA > 0

    def isOffline(self):
        return self.role & UNIT_ROLE.OFFLINE > 0

    def isCurrentPlayer(self):
        return self.dbID == getPlayerDatabaseID()

    def getVehiclesToSlots(self, allSlots = False):
        slots = self.unit._freeSlots
        if allSlots:
            slots = set(list(slots) + self.unit._playerSlots.values())
        if self.isCurrentPlayer():
            vehicles = g_itemsCache.items.getVehicles(REQ_CRITERIA.INVENTORY).keys()
        else:
            vehicles = self.vehDict.keys()
        if vehicles:
            return self.unit._roster.matchVehicleListToSlotList(vehicles, slots)
        return {}

    def getAvailableSlots(self, allSlots = False):
        matches = self.getVehiclesToSlots(allSlots)
        return set(itertools.chain(*matches.values()))

    def getSlotsToVehicles(self, allSlots = False):
        matches = self.getVehiclesToSlots(allSlots)
        slots = set(itertools.chain(*matches.values()))
        result = {}
        for slot in slots:
            result[slot] = list(itertools.ifilter(lambda v: slot in matches[v], matches.iterkeys()))

        return result


class VehicleInfo(object):
    __slots__ = ('vehInvID', 'vehTypeCD', 'vehLevel')

    def __init__(self, vehInvID = 0, vehTypeCompDescr = 0, vehLevel = 0, **kwargs):
        super(VehicleInfo, self).__init__()
        self.vehInvID = vehInvID
        self.vehTypeCD = vehTypeCompDescr
        self.vehLevel = vehLevel

    def __repr__(self):
        return 'VehicleInfo(vehInvID = {0:n}, vehTypeCD = {1:n})'.format(self.vehInvID, self.vehTypeCD)

    def isEmpty(self):
        return not self.vehInvID

    def isReadyToBattle(self):
        result = False
        if self.vehInvID:
            vehicle = g_itemsCache.items.getVehicle(self.vehInvID)
            if vehicle:
                result = vehicle.isReadyToPrebattle
        return result


class SlotState(object):
    __slots__ = ('isClosed', 'isFree')

    def __init__(self, isClosed = False, isFree = True):
        super(SlotState, self).__init__()
        self.isClosed = isClosed
        self.isFree = isFree

    def __repr__(self):
        return 'SlotState(isClosed = {0!r:s}, isFree = {1!r:s})'.format(self.isClosed, self.isFree)


class SlotInfo(object):
    __slots__ = ('index', 'state', 'player', 'vehicle')

    def __init__(self, index, state, player = None, vehicle = None):
        super(SlotInfo, self).__init__()
        self.index = index
        self.state = state
        self.player = player
        self.vehicle = vehicle

    def __repr__(self):
        return 'SlotInfo(index = {0:n}, state = {1!r:s}, player = {2!r:s}, vehicle = {3!r:s})'.format(self.index, self.state, self.player, self.vehicle)


class UnitState(object):
    __slots__ = ('__state', '__isReady')

    def __init__(self, state, isReady = False):
        super(UnitState, self).__init__()
        self.__state = state
        self.__isReady = isReady

    def __repr__(self):
        return 'UnitState(bitmask = {0!r:s}, isReady = {1!r:s})'.format(self.__state, self.__isReady)

    def __eq__(self, other):
        return self.__state == other.state

    def isLocked(self):
        return self.__state & UNIT_STATE.LOCKED > 0

    def isOpened(self):
        return self.__state & UNIT_STATE.INVITE_ONLY == 0

    def isInSearch(self):
        return self.__state & UNIT_STATE.IN_SEARCH > 0 or self.__state & UNIT_STATE.PRE_SEARCH > 0

    def isInQueue(self):
        return self.__state & UNIT_STATE.IN_QUEUE > 0 or self.__state & UNIT_STATE.PRE_QUEUE > 0

    def isInIdle(self):
        return self.__state & UNIT_STATE.MODAL_STATES > 0

    def isReady(self):
        return self.__isReady

    def isDevMode(self):
        return self.__state & UNIT_STATE.DEV_MODE > 0

    def isInArena(self):
        return self.__state & UNIT_STATE.IN_ARENA > 0


UnitStats = namedtuple('UnitStats', ('readyCount', 'occupiedSlotsCount', 'openedSlotsCount', 'freeSlotsCount', 'curTotalLevel', 'maxTotalLevel'))

def getPlayersComparator():

    def comparator(player, other):
        if player.isCreator ^ other.isCreator:
            result = -1 if player.isCreator else 1
        else:
            result = cmp(player.time, other.time)
        return result

    return comparator


_g_coolDowns = {}

def isRequestInCoolDown(requestID):
    global _g_coolDowns
    result = False
    if requestID in _g_coolDowns:
        result = _g_coolDowns[requestID] >= BigWorld.time()
    return result


def getRequestCoolDown(requestID):
    result = 0
    if requestID in _g_coolDowns:
        result = max(0, round(_g_coolDowns[requestID] - BigWorld.time()))
    return result


def setRequestCoolDown(requestID, coolDown = DEFAULT_PREBATTLE_COOLDOWN):
    _g_coolDowns[requestID] = BigWorld.time() + coolDown
    events_dispatcher.fireCoolDownEvent(requestID, coolDown=coolDown)
# okay decompyling res/scripts/client/gui/prb_control/info.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:25:44 EST

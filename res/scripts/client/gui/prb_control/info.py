import BigWorld
from collections import namedtuple
from account_helpers import getPlayerDatabaseID, getPlayerID
from constants import PREBATTLE_ACCOUNT_STATE, PREBATTLE_TEAM_STATE
from gui.prb_control import events_dispatcher
from gui.prb_control.settings import DEFAULT_PREBATTLE_COOLDOWN
from gui.shared.gui_items.Vehicle import Vehicle

class PlayerPrbInfo(object):
    __slots__ = ('accID', 'name', 'dbID', 'state', 'time', 'vehCompDescr', 'clanDBID', 'clanAbbrev', 'roster', 'isCreator')

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

    def getFullName(self):
        if self.clanAbbrev:
            fullName = '{0:>s}[{1:>s}]'.format(self.name, self.clanAbbrev)
        else:
            fullName = self.name
        return fullName

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


def setRequestCoolDown(requestID, coolDown = DEFAULT_PREBATTLE_COOLDOWN):
    _g_coolDowns[requestID] = BigWorld.time() + coolDown
    events_dispatcher.fireCoolDownEvent(requestID, coolDown=coolDown)

# 2013.11.15 11:25:42 EST
# Embedded file name: scripts/client/gui/prb_control/functional/interfaces.py
from debug_utils import LOG_DEBUG
from gui.prb_control import info
from gui.prb_control.restrictions.interfaces import IPrbPermissions
from gui.prb_control.restrictions.interfaces import IUnitPermissions
from gui.prb_control.settings import PREBATTLE_ROSTER, makePrebattleSettings
from gui.prb_control.settings import FUNCTIONAL_EXIT

class IPrbEntry(object):

    def doAction(self, action, dispatcher = None):
        return False

    def create(self, ctx, callback = None):
        pass

    def join(self, ctx, callback = None):
        pass


class IPrbListUpdater(object):

    def start(self, callback):
        pass

    def stop(self):
        pass


class IPrbListRequester(IPrbListUpdater):

    def request(self, ctx = None):
        pass


class IClientFunctional(object):

    def init(self, **kwargs):
        pass

    def fini(self, **kwargs):
        pass

    def isPlayerJoined(self, ctx):
        return False

    def addListener(self, listener):
        pass

    def removeListener(self, listener):
        pass

    def canPlayerDoAction(self):
        return (True, '')

    def doAction(self, action = None, dispatcher = None):
        return False

    def doLeaveAction(self, dispatcher, ctx = None):
        pass

    def showGUI(self):
        return False

    def isConfirmToChange(self, exit = FUNCTIONAL_EXIT.NO_FUNC):
        return False

    def getConfirmDialogMeta(self):
        return None

    def getID(self):
        return 0

    def getPrbType(self):
        return 0

    def getPrbTypeName(self):
        return 'N/A'

    def hasEntity(self):
        return False

    def hasLockedState(self):
        return False

    def isCreator(self, dbID = None):
        return False

    def leave(self, ctx, callback = None):
        pass

    def request(self, ctx, callback = None):
        pass

    def reset(self):
        pass


class IPrbFunctional(IClientFunctional):

    def __del__(self):
        LOG_DEBUG('Prebattle functional deleted:', self)

    def init(self, clientPrb = None, ctx = None):
        pass

    def fini(self, clientPrb = None, woEvents = False):
        pass

    def getSettings(self):
        return makePrebattleSettings()

    def getRosterKey(self, pID = None):
        return PREBATTLE_ROSTER.UNKNOWN

    def getRosters(self, keys = None):
        return {}

    def getPlayerInfo(self, pID = None, rosterKey = None):
        return info.PlayerPrbInfo(-1L)

    def getPlayerInfoByDbID(self, dbID):
        return info.PlayerPrbInfo(-1L)

    def getPlayerTeam(self, pID = None):
        return 0

    def getTeamState(self, team = None):
        return info.TeamStateInfo(0)

    def getPlayersStateStats(self):
        return info.PlayersStateStats(0, False, 0, 0)

    def getRoles(self, pDatabaseID = None):
        return 0

    def getPermissions(self, pID = None):
        return IPrbPermissions()

    def getLimits(self):
        return None

    def exitFromRandomQueue(self):
        return False

    def hasGUIPage(self):
        return False

    def isGUIProcessed(self):
        return False


class IQueueFunctional(object):

    def canPlayerDoAction(self):
        pass

    def doAction(self, action = None, dispatcher = None):
        return False

    def onChanged(self):
        pass


class IPrbListener(object):

    def onPrbFunctionalInited(self):
        pass

    def onPrbFunctionalFinished(self):
        pass

    def onSettingUpdated(self, functional, settingName, settingValue):
        pass

    def onTeamStatesReceived(self, functional, team1State, team2State):
        pass

    def onPlayerAdded(self, functional, playerInfo):
        pass

    def onPlayerRemoved(self, functional, playerInfo):
        pass

    def onRostersChanged(self, functional, rosters, full):
        pass

    def onPlayerTeamNumberChanged(self, functional, team):
        pass

    def onPlayerRosterChanged(self, functional, actorInfo, playerInfo):
        pass

    def onPlayerStateChanged(self, functional, roster, accountInfo):
        pass


class IUnitFunctional(IClientFunctional):

    def __del__(self):
        LOG_DEBUG('Unit functional deleted:', self)

    def init(self):
        pass

    def fini(self, woEvents = False):
        pass

    def rejoin(self):
        pass

    def initEvents(self, listener):
        pass

    def getUnitIdx(self):
        return 0

    def getExit(self):
        return FUNCTIONAL_EXIT.NO_FUNC

    def setExit(self, exit):
        pass

    def getPermissions(self, dbID = None, unitIdx = None):
        return IUnitPermissions()

    def getUnit(self, unitIdx = None):
        return (0, None)

    def getPlayerInfo(self, dbID = None, unitIdx = None):
        return info.PlayerUnitInfo(-1L, 0, None)

    def getReadyStates(self, unitIdx = None):
        return []

    def getSlotState(self, slotIdx, unitIdx = None):
        return info.SlotState(-1)

    def getPlayers(self, unitIdx = None):
        return {}

    def getCandidates(self, unitIdx = None):
        return {}

    def getRoster(self, unitIdx = None):
        return None

    def getVehicleInfo(self, dbID = None, unitIdx = None):
        return info.VehicleInfo()

    def getSlotsInfo(self, unitIdx = None):
        return []

    def getState(self, unitIdx = None):
        return info.UnitState(0)

    def getStats(self, unitIdx = None):
        return info.UnitStats(0, 0, 0, 0, 0, 0)

    def getComment(self, unitIdx = None):
        return ''


class IIntroUnitListener(object):

    def onIntroUnitFunctionalInited(self):
        pass

    def onIntroUnitFunctionalFinished(self):
        pass

    def onUnitAutoSearchStarted(self, timeLeft):
        pass

    def onUnitAutoSearchFinished(self):
        pass

    def onUnitAutoSearchSuccess(self, acceptDelta):
        pass

    def onUnitBrowserErrorReceived(self, errorCode):
        pass


class IUnitListener(object):

    def onUnitFunctionalInited(self):
        pass

    def onUnitFunctionalFinished(self):
        pass

    def onUnitUpdated(self):
        pass

    def onUnitStateChanged(self, state, timeLeft):
        pass

    def onUnitPlayerStateChanged(self, pInfo):
        pass

    def onUnitPlayerRolesChanged(self, pInfo, pPermissions):
        pass

    def onUnitPlayerOnlineStatusChanged(self, pInfo):
        pass

    def onUnitRosterChanged(self):
        pass

    def onUnitMembersListChanged(self):
        pass

    def onUnitPlayersListChanged(self):
        pass

    def onUnitVehicleChanged(self, dbID, vInfo):
        pass

    def onUnitSettingChanged(self, opCode, value):
        pass

    def onUnitErrorReceived(self, errorCode):
        pass


class IGlobalListener(IPrbListener, IIntroUnitListener, IUnitListener):
    pass
# okay decompyling res/scripts/client/gui/prb_control/functional/interfaces.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:25:42 EST

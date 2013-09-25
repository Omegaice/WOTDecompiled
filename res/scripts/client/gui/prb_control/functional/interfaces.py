# Embedded file name: scripts/client/gui/prb_control/functional/interfaces.py
from debug_utils import LOG_DEBUG
from gui.prb_control.info import TeamStateInfo, PlayersStateStats, PlayerPrbInfo
from gui.prb_control.restrictions.interfaces import IPermissions
from gui.prb_control.settings import PREBATTLE_ROSTER, makePrebattleSettings

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


class IPrbFunctional(object):

    def __del__(self):
        LOG_DEBUG('Prebattle functional deleted:', self)

    def init(self, clientPrb = None, ctx = None):
        pass

    def fini(self, clientPrb = None, woEvents = False):
        pass

    def addListener(self, listener):
        pass

    def removeListener(self, listener):
        pass

    def getID(self):
        return 0

    def getPrbType(self):
        return 0

    def getPrbTypeName(self):
        return 'N/A'

    def getSettings(self):
        return makePrebattleSettings()

    def getRosterKey(self, pID = None):
        return PREBATTLE_ROSTER.UNKNOWN

    def getRosters(self, keys = None):
        return {}

    def getPlayerInfo(self, pID = None, rosterKey = None):
        return PlayerPrbInfo(-1L)

    def getPlayerInfoByDbID(self, dbID):
        return PlayerPrbInfo(-1L)

    def getPlayerTeam(self, pID = None):
        return 0

    def getTeamState(self, team = None):
        return TeamStateInfo(0)

    def getPlayersStateStats(self):
        return PlayersStateStats(0, False, 0, 0)

    def getRoles(self, pDatabaseID = None):
        return 0

    def getPermissions(self, pID = None):
        return IPermissions()

    def isCreator(self, pDatabaseID = None):
        return False

    def hasEntity(self):
        return False

    def getLimits(self):
        return None

    def canPlayerDoAction(self):
        return (True, '')

    def doAction(self, action = None, dispatcher = None):
        return False

    def exitFromRandomQueue(self):
        return False

    def hasGUIPage(self):
        return False

    def showGUI(self):
        return False

    def isConfirmToChange(self):
        return False

    def getConfirmDialogMeta(self):
        return None

    def leave(self, ctx, callback = None):
        pass

    def request(self, ctx, callback = None):
        pass

    def reset(self):
        pass


class IQueueFunctional:

    def canPlayerDoAction(self):
        pass

    def doAction(self, action = None):
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
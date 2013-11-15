# 2013.11.15 11:25:42 EST
# Embedded file name: scripts/client/gui/prb_control/functional/squad.py
import BigWorld
from account_helpers import gameplay_ctx
from constants import JOIN_FAILURE, REQUEST_COOLDOWN
from debug_utils import LOG_ERROR, LOG_DEBUG
from gui import DialogsInterface, prb_control, SystemMessages
from gui.Scaleform.daapi.view.dialogs import I18nConfirmDialogMeta
from gui.prb_control import events_dispatcher, context, getPrebattleRosters, info
from gui.prb_control.formatters import messages
from gui.prb_control.functional.decorators import vehicleAmmoCheck
from gui.prb_control.functional.default import PrbEntry, PrbFunctional
from gui.prb_control.info import PlayerPrbInfo
from gui.prb_control.restrictions.permissions import SquadPrbPermissions
from gui.prb_control.settings import PREBATTLE_ROSTER, REQUEST_TYPE
from gui.prb_control.settings import PREBATTLE_ACTION_NAME
from gui.shared import g_eventBus, EVENT_BUS_SCOPE
from gui.shared.events import ChannelCarouselEvent

class SquadEntry(PrbEntry):

    def doAction(self, action, dispatcher = None):
        result = False
        if action.actionName == PREBATTLE_ACTION_NAME.SQUAD:
            ctx = context.SquadSettingsCtx(waitingID='prebattle/create')
            if dispatcher is not None:
                if dispatcher._setRequestCtx(ctx):
                    self.create(ctx)
            else:
                LOG_ERROR('Prebattle dispatcher is required')
            result = True
        return result

    def create(self, ctx, callback = None):
        if not isinstance(ctx, context.SquadSettingsCtx):
            LOG_ERROR('Invalid context to create squad', ctx)
            if callback:
                callback(False)
        elif info.isRequestInCoolDown(REQUEST_TYPE.CREATE):
            SystemMessages.pushMessage(messages.getJoinFailureMessage(JOIN_FAILURE.COOLDOWN), type=SystemMessages.SM_TYPE.Error)
            if callback:
                callback(False)
        elif prb_control.getClientPrebattle() is None or ctx.isForced():
            ctx.startProcessing(callback=callback)
            BigWorld.player().prb_createSquad()
            info.setRequestCoolDown(REQUEST_TYPE.CREATE, coolDown=REQUEST_COOLDOWN.PREBATTLE_CREATION)
        else:
            LOG_ERROR('First, player has to confirm exit from the current prebattle', prb_control.getPrebattleType())
            if callback:
                callback(False)
        return

    def join(self, ctx, callback = None):
        LOG_ERROR('Player can join to squad by invite')
        if callback:
            callback(False)


class SquadFunctional(PrbFunctional):

    def __init__(self, settings):
        requests = {REQUEST_TYPE.SET_TEAM_STATE: self.setTeamState,
         REQUEST_TYPE.SET_PLAYER_STATE: self.setPlayerState,
         REQUEST_TYPE.KICK: self.kickPlayer,
         REQUEST_TYPE.SEND_INVITE: self.sendInvites}
        super(SquadFunctional, self).__init__(settings, permClass=SquadPrbPermissions, requestHandlers=requests)
        self.__doTeamReady = False

    def init(self, clientPrb = None, ctx = None):
        super(SquadFunctional, self).init(clientPrb=clientPrb)
        isInvitesOpen = False
        if ctx is not None:
            isInvitesOpen = ctx.getRequestType() is REQUEST_TYPE.CREATE
        if self.getPlayerInfo().isReady() and self.getTeamState(team=1).isInQueue():
            events_dispatcher.loadBattleQueue()
        else:
            events_dispatcher.loadHangar()
        events_dispatcher.loadSquad(isInvitesOpen=isInvitesOpen)
        g_eventBus.addListener(ChannelCarouselEvent.CAROUSEL_INITED, self.__handleCarouselInited, scope=EVENT_BUS_SCOPE.LOBBY)
        return

    def canPlayerDoAction(self):
        if self.getTeamState().isInQueue():
            return (False, '')
        return (True, '')

    def isGUIProcessed(self):
        return True

    def fini(self, clientPrb = None, woEvents = False):
        super(SquadFunctional, self).fini(clientPrb=clientPrb, woEvents=woEvents)
        if not woEvents:
            events_dispatcher.unloadSquad()
        else:
            events_dispatcher.removeSquadFromCarousel()
        g_eventBus.removeListener(ChannelCarouselEvent.CAROUSEL_INITED, self.__handleCarouselInited, scope=EVENT_BUS_SCOPE.LOBBY)

    @vehicleAmmoCheck
    def setPlayerState(self, ctx, callback = None):
        super(SquadFunctional, self).setPlayerState(ctx, callback)

    def showGUI(self):
        events_dispatcher.loadSquad()

    def getPlayersStateStats(self):
        return self._getPlayersStateStats(PREBATTLE_ROSTER.ASSIGNED_IN_TEAM1)

    def getRosters(self, keys = None):
        rosters = getPrebattleRosters()
        result = {PREBATTLE_ROSTER.ASSIGNED_IN_TEAM1: []}
        if PREBATTLE_ROSTER.ASSIGNED_IN_TEAM1 in rosters:
            result[PREBATTLE_ROSTER.ASSIGNED_IN_TEAM1] = map(lambda accInfo: PlayerPrbInfo(accInfo[0], functional=self, roster=PREBATTLE_ROSTER.ASSIGNED_IN_TEAM1, **accInfo[1]), rosters[PREBATTLE_ROSTER.ASSIGNED_IN_TEAM1].iteritems())
        return result

    def doAction(self, action = None, dispatcher = None):
        if self.isCreator():
            stats = self.getPlayersStateStats()
            if stats.haveInBattle:
                DialogsInterface.showI18nInfoDialog('squadHavePlayersInBattle', lambda result: None)
                return True
            notReadyCount = stats.notReadyCount
            if not self.getPlayerInfo().isReady():
                notReadyCount -= 1
            if notReadyCount > 0:
                DialogsInterface.showDialog(I18nConfirmDialogMeta('squadHaveNotReadyPlayers', messageCtx={'notReadyCount': notReadyCount,
                 'playersCount': stats.playersCount}), self.__setCreatorReady)
                return True
            self.__setCreatorReady(True)
        elif self.getPlayerInfo().isReady():
            self.setPlayerState(context.SetPlayerStateCtx(False, waitingID='prebattle/player_not_ready'))
        else:
            self.setPlayerState(context.SetPlayerStateCtx(True, waitingID='prebattle/player_ready'))
        return True

    def exitFromRandomQueue(self):
        if self.isCreator():
            self.setTeamState(context.SetTeamStateCtx(1, False, waitingID='prebattle/team_not_ready'))
        else:
            self.setPlayerState(context.SetPlayerStateCtx(False, waitingID='prebattle/player_not_ready'))
        return True

    def prb_onPlayerStateChanged(self, pID, roster):
        super(SquadFunctional, self).prb_onPlayerStateChanged(pID, roster)
        if self.__doTeamReady:
            self.__doTeamReady = False
            self.__setTeamReady()
        events_dispatcher.updateUI()

    def prb_onPlayerRosterChanged(self, pID, prevRoster, roster, actorID):
        super(SquadFunctional, self).prb_onPlayerRosterChanged(pID, prevRoster, roster, actorID)
        events_dispatcher.updateUI()

    def prb_onPlayerRemoved(self, pID, roster, name):
        super(SquadFunctional, self).prb_onPlayerRemoved(pID, roster, name)
        events_dispatcher.updateUI()

    def prb_onTeamStatesReceived(self):
        super(SquadFunctional, self).prb_onTeamStatesReceived()
        events_dispatcher.updateUI()
        if self.getPlayerInfo().isReady() or self.isCreator():
            if self.getTeamState(team=1).isInQueue():
                events_dispatcher.loadBattleQueue()
            else:
                events_dispatcher.loadHangar()

    def __setCreatorReady(self, result):
        if not result:
            return
        if self.getPlayerInfo().isReady():
            self.__setTeamReady()
        else:
            self.setPlayerState(context.SetPlayerStateCtx(True, waitingID='prebattle/player_ready'), callback=self.__onCreatorReady)

    def __setTeamReady(self):
        if self.isCreator():
            self.setTeamState(context.SetTeamStateCtx(1, True, waitingID='prebattle/team_ready', gamePlayMask=gameplay_ctx.getMask()))

    def __onCreatorReady(self, result):
        self.__doTeamReady = result

    def __handleCarouselInited(self, _):
        events_dispatcher.addSquadToCarousel()
# okay decompyling res/scripts/client/gui/prb_control/functional/squad.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:25:43 EST

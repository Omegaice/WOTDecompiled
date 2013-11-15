# 2013.11.15 11:25:43 EST
# Embedded file name: scripts/client/gui/prb_control/functional/training.py
from functools import partial
import BigWorld
from PlayerEvents import g_playerEvents
from adisp import process
from constants import PREBATTLE_TYPE, PREBATTLE_CACHE_KEY, JOIN_FAILURE
from constants import REQUEST_COOLDOWN
from debug_utils import LOG_ERROR, LOG_DEBUG
from gui import SystemMessages, prb_control
from gui.prb_control import events_dispatcher, info
from gui.prb_control.formatters import messages
from gui.prb_control.functional.default import PrbEntry, PrbFunctional
from gui.prb_control.functional.interfaces import IPrbListUpdater
from gui.prb_control.context import SetPlayerStateCtx, TrainingSettingsCtx, LeavePrbCtx
from gui.prb_control.info import PlayerPrbInfo, setRequestCoolDown, isRequestInCoolDown
from gui.prb_control.restrictions.limits import TrainingLimits
from gui.prb_control.sequences import PrbListIterator
from gui.prb_control.restrictions.permissions import TrainingPrbPermissions
from gui.prb_control.settings import PREBATTLE_ROSTER, REQUEST_TYPE
from gui.prb_control.settings import PREBATTLE_SETTING_NAME
from gui.prb_control.settings import PREBATTLE_ACTION_NAME, GUI_EXIT
from gui.shared import g_eventBus, EVENT_BUS_SCOPE
from gui.shared.events import LoadEvent
from gui.shared.utils.functions import checkAmmoLevel
from prebattle_shared import decodeRoster

class TrainingEntry(PrbEntry):

    def doAction(self, action, dispatcher = None):
        if action.actionName == PREBATTLE_ACTION_NAME.LEAVE_TRAINING_LIST:
            events_dispatcher.loadHangar()
        elif prb_control.getClientPrebattle() is None:
            self.__loadTrainingList()
        elif prb_control.isTraining():
            if dispatcher is not None:
                self.__loadTrainingRoom(dispatcher)
            else:
                LOG_ERROR('Dispatcher not found')
        else:
            LOG_ERROR('Player is joined to prebattle', prb_control.getPrebattleType())
        return True

    def create(self, ctx, callback = None):
        if not isinstance(ctx, TrainingSettingsCtx):
            LOG_ERROR('Invalid context to create training', ctx)
            if callback:
                callback(False)
        elif info.isRequestInCoolDown(REQUEST_TYPE.CREATE):
            SystemMessages.pushMessage(messages.getJoinFailureMessage(JOIN_FAILURE.COOLDOWN), type=SystemMessages.SM_TYPE.Error)
            if callback:
                callback(False)
        elif prb_control.getClientPrebattle() is None or ctx.isForced():
            ctx.startProcessing(callback=callback)
            BigWorld.player().prb_createTraining(ctx.getArenaTypeID(), ctx.getRoundLen(), ctx.isOpened(), ctx.getComment())
            info.setRequestCoolDown(REQUEST_TYPE.CREATE, coolDown=REQUEST_COOLDOWN.PREBATTLE_CREATION)
        else:
            LOG_ERROR('First, player has to confirm exit from the current prebattle', prb_control.getPrebattleType())
            if callback:
                callback(False)
        return

    @process
    def __loadTrainingList(self):
        result = yield checkAmmoLevel()
        if result:
            events_dispatcher.loadTrainingList()

    @process
    def __loadTrainingRoom(self, dispatcher):
        result = yield dispatcher.sendPrbRequest(SetPlayerStateCtx(True, waitingID='prebattle/player_not_ready'))
        if result:
            events_dispatcher.loadTrainingRoom()


class TrainingListRequester(IPrbListUpdater):
    UPDATE_LIST_TIMEOUT = 5

    def __init__(self):
        super(TrainingListRequester, self).__init__()
        self.__callbackID = None
        self.__callback = None
        return

    def start(self, callback):
        if self.__callbackID is not None:
            LOG_ERROR('TrainingListRequester already started')
            return
        else:
            if callback is not None and callable(callback):
                g_playerEvents.onPrebattlesListReceived += self.__pe_onPrebattlesListReceived
                self.__callback = callback
                self.__request()
            else:
                LOG_ERROR('Callback is None or is not callable')
                return
            return

    def stop(self):
        g_playerEvents.onPrebattlesListReceived -= self.__pe_onPrebattlesListReceived
        self.__callback = None
        if self.__callbackID is not None:
            BigWorld.cancelCallback(self.__callbackID)
            self.__callbackID = None
        return

    def __request(self):
        self.__callbackID = None
        if hasattr(BigWorld.player(), 'requestPrebattles'):
            BigWorld.player().requestPrebattles(PREBATTLE_TYPE.TRAINING, PREBATTLE_CACHE_KEY.CREATE_TIME, False, 0, 50)
        return

    def __setTimeout(self):
        self.__callbackID = BigWorld.callback(self.UPDATE_LIST_TIMEOUT, self.__request)

    def __pe_onPrebattlesListReceived(self, prbType, prbsCount, prebattles):
        if prbType != PREBATTLE_TYPE.TRAINING:
            return
        LOG_DEBUG('onPrebattlesListReceived', prbsCount)
        self.__callback(PrbListIterator(prebattles))
        self.__setTimeout()


class TrainingFunctional(PrbFunctional):
    __loadEvents = (LoadEvent.LOAD_HANGAR,
     LoadEvent.LOAD_INVENTORY,
     LoadEvent.LOAD_SHOP,
     LoadEvent.LOAD_TECHTREE,
     LoadEvent.LOAD_BARRACKS)

    def __init__(self, settings):
        requests = {REQUEST_TYPE.ASSIGN: self.assign,
         REQUEST_TYPE.SET_TEAM_STATE: self.setTeamState,
         REQUEST_TYPE.SET_PLAYER_STATE: self.setPlayerState,
         REQUEST_TYPE.CHANGE_SETTINGS: self.changeSettings,
         REQUEST_TYPE.SWAP_TEAMS: self.swapTeams,
         REQUEST_TYPE.CHANGE_ARENA_VOIP: self.changeArenaVoip,
         REQUEST_TYPE.KICK: self.kickPlayer,
         REQUEST_TYPE.SEND_INVITE: self.sendInvites}
        self._guiExit = GUI_EXIT.UNKNOWN
        super(TrainingFunctional, self).__init__(settings, permClass=TrainingPrbPermissions, limits=TrainingLimits(self), requestHandlers=requests)
        self.__settingRecords = []

    def init(self, clientPrb = None, ctx = None):
        super(TrainingFunctional, self).init(clientPrb=clientPrb)
        add = g_eventBus.addListener
        for event in self.__loadEvents:
            add(event, self.__handleViewLoad, scope=EVENT_BUS_SCOPE.LOBBY)

        self.__enterTrainingRoom()

    def fini(self, clientPrb = None, woEvents = False):
        super(TrainingFunctional, self).fini(clientPrb=clientPrb, woEvents=woEvents)
        remove = g_eventBus.removeListener
        for event in self.__loadEvents:
            remove(event, self.__handleViewLoad, scope=EVENT_BUS_SCOPE.LOBBY)

        if not woEvents:
            if self._guiExit == GUI_EXIT.TRAINING_LIST:
                events_dispatcher.loadTrainingList()
            elif self._guiExit == GUI_EXIT.HANGAR:
                events_dispatcher.loadHangar()
            else:
                events_dispatcher.exitFromTrainingRoom()
        events_dispatcher.requestToDestroyPrbChannel(PREBATTLE_TYPE.TRAINING)

    def getRosters(self, keys = None):
        rosters = prb_control.getPrebattleRosters()
        if keys is None:
            result = {PREBATTLE_ROSTER.ASSIGNED_IN_TEAM1: [],
             PREBATTLE_ROSTER.ASSIGNED_IN_TEAM2: [],
             PREBATTLE_ROSTER.UNASSIGNED: []}
        else:
            result = {}
            for key in keys:
                if PREBATTLE_ROSTER.UNASSIGNED & key != 0:
                    result[PREBATTLE_ROSTER.UNASSIGNED] = []
                else:
                    result[key] = []

        hasTeam1 = PREBATTLE_ROSTER.ASSIGNED_IN_TEAM1 in result
        hasTeam2 = PREBATTLE_ROSTER.ASSIGNED_IN_TEAM2 in result
        hasUnassigned = PREBATTLE_ROSTER.UNASSIGNED in result
        for key, roster in rosters.iteritems():
            accounts = map(lambda accInfo: PlayerPrbInfo(accInfo[0], functional=self, roster=key, **accInfo[1]), roster.iteritems())
            team, assigned = decodeRoster(key)
            if assigned:
                if hasTeam1 and team is 1:
                    result[PREBATTLE_ROSTER.ASSIGNED_IN_TEAM1] = accounts
                elif hasTeam2 and team is 2:
                    result[PREBATTLE_ROSTER.ASSIGNED_IN_TEAM2] = accounts
            elif hasUnassigned:
                result[PREBATTLE_ROSTER.UNASSIGNED] = accounts

        return result

    def canPlayerDoAction(self):
        return (True, '')

    def doAction(self, action = None, dispatcher = None):
        self.__enterTrainingRoom()
        return True

    def doLeaveAction(self, dispatcher, ctx = None):
        if ctx is None:
            ctx = LeavePrbCtx(guiExit=GUI_EXIT.HANGAR, waitingID='prebattle/leave')
        if dispatcher._setRequestCtx(ctx):
            self.leave(ctx)
        return

    def leave(self, ctx, callback = None):
        ctx.startProcessing(callback)
        self._guiExit = ctx.getGuiExit()
        BigWorld.player().prb_leave(ctx.onResponseReceived)

    def hasGUIPage(self):
        return True

    def showGUI(self):
        self.__enterTrainingRoom()

    def changeSettings(self, ctx, callback = None):
        if ctx.getRequestType() != REQUEST_TYPE.CHANGE_SETTINGS:
            LOG_ERROR('Invalid context for request changeSettings', ctx)
            if callback:
                callback(False)
            return
        if isRequestInCoolDown(REQUEST_TYPE.CHANGE_SETTINGS):
            SystemMessages.pushMessage(messages.getRequestInCoolDownMessage(REQUEST_TYPE.CHANGE_SETTINGS), type=SystemMessages.SM_TYPE.Error)
            if callback:
                callback(False)
            return
        player = BigWorld.player()
        pPermissions = self.getPermissions()
        self.__settingRecords = []
        rejected = False
        isOpenedChanged = ctx.isOpenedChanged(self._settings)
        isCommentChanged = ctx.isCommentChanged(self._settings)
        isArenaTypeIDChanged = ctx.isArenaTypeIDChanged(self._settings)
        isRoundLenChanged = ctx.isRoundLenChanged(self._settings)
        if isOpenedChanged:
            if pPermissions.canMakeOpenedClosed():
                self.__settingRecords.append('isOpened')
            else:
                LOG_ERROR('Player can not make training opened/closed', pPermissions)
                rejected = True
        if isCommentChanged:
            if pPermissions.canChangeComment():
                self.__settingRecords.append('comment')
            else:
                LOG_ERROR('Player can not change comment', pPermissions)
                rejected = True
        if isArenaTypeIDChanged:
            if pPermissions.canChangeArena():
                self.__settingRecords.append('arenaTypeID')
            else:
                LOG_ERROR('Player can not change comment', pPermissions)
                rejected = True
        if isRoundLenChanged:
            if pPermissions.canChangeArena():
                self.__settingRecords.append('roundLength')
            else:
                LOG_ERROR('Player can not change comment', pPermissions)
                rejected = True
        if rejected:
            self.__settingRecords = []
            if callback:
                callback(False)
            return
        if not len(self.__settingRecords):
            if callback:
                callback(False)
            return
        ctx.startProcessing(callback=callback)
        if isOpenedChanged:
            player.prb_changeOpenStatus(ctx.isOpened(), partial(self.__onSettingChanged, record='isOpened', callback=ctx.stopProcessing))
        if isCommentChanged:
            player.prb_changeComment(ctx.getComment(), partial(self.__onSettingChanged, record='comment', callback=ctx.stopProcessing))
        if isArenaTypeIDChanged:
            player.prb_changeArena(ctx.getArenaTypeID(), partial(self.__onSettingChanged, record='arenaTypeID', callback=ctx.stopProcessing))
        if isRoundLenChanged:
            player.prb_changeRoundLength(ctx.getRoundLen(), partial(self.__onSettingChanged, record='roundLength', callback=ctx.stopProcessing))
        if not len(self.__settingRecords):
            if callback:
                callback(False)
        else:
            setRequestCoolDown(REQUEST_TYPE.CHANGE_SETTINGS)

    def changeArenaVoip(self, ctx, callback = None):
        if ctx.getChannels() == self._settings[PREBATTLE_SETTING_NAME.ARENA_VOIP_CHANNELS]:
            if callback:
                callback(True)
            return
        if isRequestInCoolDown(REQUEST_TYPE.CHANGE_ARENA_VOIP):
            SystemMessages.pushMessage(messages.getRequestInCoolDownMessage(REQUEST_TYPE.CHANGE_ARENA_VOIP), type=SystemMessages.SM_TYPE.Error)
            if callback:
                callback(False)
            return
        pPermissions = self.getPermissions()
        if pPermissions.canChangeArenaVOIP():
            ctx.startProcessing(callback=callback)
            BigWorld.player().prb_changeArenaVoip(ctx.getChannels(), ctx.onResponseReceived)
            setRequestCoolDown(REQUEST_TYPE.CHANGE_ARENA_VOIP)
        else:
            LOG_ERROR('Player can not change arena VOIP', pPermissions)
            if callback:
                callback(False)

    def __enterTrainingRoom(self):
        self.setPlayerState(SetPlayerStateCtx(True, waitingID='prebattle/player_ready'), self.__onPlayerReady)

    def __onPlayerReady(self, result):
        if result:
            events_dispatcher.loadTrainingRoom()
        else:
            events_dispatcher.loadHangar()

    def __onSettingChanged(self, code, record = '', callback = None):
        if code < 0:
            LOG_ERROR('Server return error for training change', code, record)
            if callback:
                callback(False)
            return
        if record in self.__settingRecords:
            self.__settingRecords.remove(record)
        if not len(self.__settingRecords) and callback:
            callback(True)

    def __handleViewLoad(self, _):
        self.setPlayerState(SetPlayerStateCtx(False, waitingID='prebattle/player_not_ready'))
# okay decompyling res/scripts/client/gui/prb_control/functional/training.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:25:44 EST

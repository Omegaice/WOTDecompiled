# Embedded file name: scripts/client/gui/prb_control/functional/company.py
import BigWorld
from PlayerEvents import g_playerEvents
from account_helpers import gameplay_ctx
from account_helpers.AccountSettings import AccountSettings
from constants import PREBATTLE_TYPE, PREBATTLE_CACHE_KEY, JOIN_FAILURE
from constants import PREBATTLE_COMPANY_DIVISION, REQUEST_COOLDOWN
from debug_utils import LOG_ERROR, LOG_DEBUG
from gui import SystemMessages, prb_control, DialogsInterface
from gui.Scaleform.daapi.view.dialogs import I18nConfirmDialogMeta
from gui.prb_control.context import CompanySettingsCtx
from gui.prb_control.formatters import messages
from gui.prb_control.functional.interfaces import IPrbListRequester
from gui.prb_control.info import setRequestCoolDown, isRequestInCoolDown, PlayerPrbInfo
from gui.prb_control.sequences import PrbListIterator
from gui.shared import g_eventBus, EVENT_BUS_SCOPE
from gui.shared.events import ChannelCarouselEvent
from gui.prb_control import events_dispatcher, info, context
from gui.prb_control.restrictions.limits import CompanyLimits
from gui.prb_control.settings import PREBATTLE_REQUEST, PREBATTLE_ROSTER
from gui.prb_control.settings import PREBATTLE_SETTING_NAME
from gui.prb_control.prb_helpers import vehicleAmmoCheck
from gui.prb_control.functional.default import PrbEntry, PrbFunctional
from gui.prb_control.restrictions.permissions import CompanyPermissions

class CompanyEntry(PrbEntry):

    def doAction(self, action, dispatcher = None):
        events_dispatcher.loadCompaniesWindow()
        return True

    def create(self, ctx, callback = None):
        if not isinstance(ctx, CompanySettingsCtx):
            LOG_ERROR('Invalid context to create company', ctx)
            if callback:
                callback(False)
        elif info.isRequestInCoolDown(PREBATTLE_REQUEST.CREATE):
            SystemMessages.pushMessage(messages.getJoinFailureMessage(JOIN_FAILURE.COOLDOWN), type=SystemMessages.SM_TYPE.Error)
            if callback:
                callback(False)
        elif prb_control.getClientPrebattle() is None or ctx.isForced():
            ctx.startProcessing(callback=callback)
            BigWorld.player().prb_createCompany(ctx.isOpened(), ctx.getComment(), ctx.getDivision())
            info.setRequestCoolDown(PREBATTLE_REQUEST.CREATE, coolDown=REQUEST_COOLDOWN.PREBATTLE_CREATION)
        else:
            LOG_ERROR('First, player has to confirm exit from the current prebattle', prb_control.getPrebattleType())
            if callback:
                callback(False)
        return


class CompanyListRequester(IPrbListRequester):

    def __init__(self):
        super(CompanyListRequester, self).__init__()
        self.__callback = None
        return

    def start(self, callback):
        if callback is not None and callable(callback):
            self.__callback = callback
        else:
            LOG_ERROR('Callback is None or is not callable')
            return
        g_playerEvents.onPrebattlesListReceived += self.__pe_onPrebattlesListReceived
        return

    def stop(self):
        g_playerEvents.onPrebattlesListReceived -= self.__pe_onPrebattlesListReceived
        self.__callback = None
        return

    def request(self, ctx = None):
        if isRequestInCoolDown(PREBATTLE_REQUEST.PREBATTLES_LIST):
            SystemMessages.pushMessage(messages.getRequestInCoolDownMessage(PREBATTLE_REQUEST.PREBATTLES_LIST), type=SystemMessages.SM_TYPE.Error)
            return
        LOG_DEBUG('Request prebattle', ctx)
        setRequestCoolDown(PREBATTLE_REQUEST.PREBATTLES_LIST)
        if ctx.byDivision():
            BigWorld.player().requestPrebattlesByDivision(ctx.isNotInBattle, ctx.division)
        elif ctx.byName():
            BigWorld.player().requestPrebattlesByName(PREBATTLE_TYPE.COMPANY, ctx.isNotInBattle, ctx.creatorMask)
        else:
            BigWorld.player().requestPrebattles(PREBATTLE_TYPE.COMPANY, PREBATTLE_CACHE_KEY.CREATE_TIME, ctx.isNotInBattle, -50, 0)

    def __pe_onPrebattlesListReceived(self, prbType, prbsCount, prebattles):
        if prbType != PREBATTLE_TYPE.COMPANY:
            return
        LOG_DEBUG('onPrebattlesListReceived', prbsCount)
        self.__callback(PrbListIterator(reversed(prebattles)))


class CompanyFunctional(PrbFunctional):

    def __init__(self, settings):
        requests = {PREBATTLE_REQUEST.ASSIGN: self.assign,
         PREBATTLE_REQUEST.SET_TEAM_STATE: self.setTeamState,
         PREBATTLE_REQUEST.SET_PLAYER_STATE: self.setPlayerState,
         PREBATTLE_REQUEST.CHANGE_OPENED: self.changeOpened,
         PREBATTLE_REQUEST.CHANGE_COMMENT: self.changeComment,
         PREBATTLE_REQUEST.CHANGE_DIVISION: self.changeDivision,
         PREBATTLE_REQUEST.KICK: self.kickPlayer,
         PREBATTLE_REQUEST.SEND_INVITE: self.sendInvites}
        super(CompanyFunctional, self).__init__(settings, permClass=CompanyPermissions, limits=CompanyLimits(self), requestHandlers=requests)
        self.__doTeamReady = False

    def init(self, clientPrb = None, ctx = None):
        super(CompanyFunctional, self).init(clientPrb=clientPrb)
        isInvitesOpen = False
        if ctx is not None:
            isInvitesOpen = ctx.getRequestType() is PREBATTLE_REQUEST.CREATE
        events_dispatcher.loadCompany(isInvitesOpen=isInvitesOpen)
        g_eventBus.addListener(ChannelCarouselEvent.CAROUSEL_INITED, self.__handleCarouselInited, scope=EVENT_BUS_SCOPE.LOBBY)
        return

    def fini(self, clientPrb = None, woEvents = False):
        super(CompanyFunctional, self).fini(clientPrb=clientPrb)
        if not woEvents:
            events_dispatcher.unloadCompany()
        else:
            events_dispatcher.removeCompanyFromCarousel()
        g_eventBus.removeListener(ChannelCarouselEvent.CAROUSEL_INITED, self.__handleCarouselInited, scope=EVENT_BUS_SCOPE.LOBBY)

    @vehicleAmmoCheck
    def setPlayerState(self, ctx, callback = None):
        super(CompanyFunctional, self).setPlayerState(ctx, callback)

    def getPlayersStateStats(self):
        return self._getPlayersStateStats(PREBATTLE_ROSTER.ASSIGNED_IN_TEAM1)

    def getRosters(self, keys = None):
        rosters = prb_control.getPrebattleRosters()
        if keys is None:
            result = {PREBATTLE_ROSTER.ASSIGNED_IN_TEAM1: [],
             PREBATTLE_ROSTER.UNASSIGNED_IN_TEAM1: []}
        else:
            result = {}
            for key in keys:
                if key in [PREBATTLE_ROSTER.ASSIGNED_IN_TEAM1, PREBATTLE_ROSTER.UNASSIGNED_IN_TEAM1]:
                    result[key] = []

        for key, roster in rosters.iteritems():
            if key in result:
                result[key] = map(lambda accInfo: PlayerPrbInfo(accInfo[0], functional=self, roster=key, **accInfo[1]), roster.iteritems())

        return result

    def canPlayerDoAction(self):
        isValid, notValidReason = True, ''
        if self.isCreator():
            isValid, notValidReason = self._limits.isTeamValid()
        return (isValid, notValidReason)

    def doAction(self, action = None, dispatcher = None):
        if self.isCreator():
            if self.getRosterKey() != PREBATTLE_ROSTER.ASSIGNED_IN_TEAM1:
                DialogsInterface.showI18nInfoDialog('teamDoesNotHaveCommander', lambda result: None)
                return True
            stats = self.getPlayersStateStats()
            creatorWeight = 1 if not self.getPlayerInfo().isReady() else 0
            readyCount = stats.playersCount - stats.notReadyCount
            if readyCount < stats.limitMaxCount - creatorWeight:
                DialogsInterface.showDialog(I18nConfirmDialogMeta('teamHaveNotReadyPlayers', messageCtx={'readyCount': readyCount,
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

    def showGUI(self):
        events_dispatcher.loadCompany()

    def changeOpened(self, ctx, callback = None):
        if ctx.getRequestType() != PREBATTLE_REQUEST.CHANGE_OPENED:
            LOG_ERROR('Invalid context for request changeOpened', ctx)
            if callback:
                callback(False)
            return
        if not ctx.isOpenedChanged(self._settings):
            if callback:
                callback(False)
            return
        if isRequestInCoolDown(PREBATTLE_REQUEST.CHANGE_SETTINGS):
            SystemMessages.pushMessage(messages.getRequestInCoolDownMessage(PREBATTLE_REQUEST.CHANGE_SETTINGS), type=SystemMessages.SM_TYPE.Error)
            if callback:
                callback(False)
            return
        pPermissions = self.getPermissions()
        if not pPermissions.canMakeOpenedClosed():
            LOG_ERROR('Player can not change opened/closed', pPermissions)
            if callback:
                callback(False)
            return
        ctx.startProcessing(callback)
        BigWorld.player().prb_changeOpenStatus(ctx.isOpened(), ctx.onResponseReceived)
        setRequestCoolDown(PREBATTLE_REQUEST.CHANGE_SETTINGS)

    def changeComment(self, ctx, callback = None):
        if ctx.getRequestType() != PREBATTLE_REQUEST.CHANGE_COMMENT:
            LOG_ERROR('Invalid context for request changeComment', ctx)
            if callback:
                callback(False)
            return
        if not ctx.isCommentChanged(self._settings):
            if callback:
                callback(False)
            return
        if isRequestInCoolDown(PREBATTLE_REQUEST.CHANGE_SETTINGS):
            SystemMessages.pushMessage(messages.getRequestInCoolDownMessage(PREBATTLE_REQUEST.CHANGE_SETTINGS), type=SystemMessages.SM_TYPE.Error)
            if callback:
                callback(False)
            return
        pPermissions = self.getPermissions()
        if not pPermissions.canChangeComment():
            LOG_ERROR('Player can not change comment', pPermissions)
            if callback:
                callback(False)
            return
        ctx.startProcessing(callback)
        BigWorld.player().prb_changeComment(ctx.getComment(), ctx.onResponseReceived)
        setRequestCoolDown(PREBATTLE_REQUEST.CHANGE_SETTINGS)

    def changeDivision(self, ctx, callback = None):
        if ctx.getRequestType() != PREBATTLE_REQUEST.CHANGE_DIVISION:
            LOG_ERROR('Invalid context for request changeDivision', ctx)
            if callback:
                callback(False)
            return
        if not ctx.isDivisionChanged(self._settings):
            if callback:
                callback(False)
            return
        if isRequestInCoolDown(PREBATTLE_REQUEST.CHANGE_SETTINGS):
            SystemMessages.pushMessage(messages.getRequestInCoolDownMessage(PREBATTLE_REQUEST.CHANGE_SETTINGS), type=SystemMessages.SM_TYPE.Error)
            if callback:
                callback(False)
            return
        if ctx.getDivision() not in PREBATTLE_COMPANY_DIVISION.RANGE:
            LOG_ERROR('Division is invalid', ctx)
            if callback:
                callback(False)
            return
        if self.getTeamState().isInQueue():
            LOG_ERROR('Team is ready or locked', ctx)
            if callback:
                callback(False)
            return
        pPermissions = self.getPermissions()
        if not pPermissions.canChangeDivision():
            LOG_ERROR('Player can not change division', pPermissions)
            if callback:
                callback(False)
            return
        ctx.startProcessing(callback)
        BigWorld.player().prb_changeDivision(ctx.getDivision(), ctx.onResponseReceived)
        setRequestCoolDown(PREBATTLE_REQUEST.CHANGE_SETTINGS)

    def prb_onSettingUpdated(self, settingName):
        super(CompanyFunctional, self).prb_onSettingUpdated(settingName)
        if settingName == PREBATTLE_SETTING_NAME.LIMITS:
            events_dispatcher.updateUI()

    def prb_onPlayerStateChanged(self, pID, roster):
        super(CompanyFunctional, self).prb_onPlayerStateChanged(pID, roster)
        if self.__doTeamReady:
            self.__doTeamReady = False
            self.__setTeamReady()
        events_dispatcher.updateUI()

    def prb_onRosterReceived(self):
        super(CompanyFunctional, self).prb_onRosterReceived()
        events_dispatcher.updateUI()

    def prb_onPlayerRosterChanged(self, pID, prevRoster, roster, actorID):
        super(CompanyFunctional, self).prb_onPlayerRosterChanged(pID, prevRoster, roster, actorID)
        events_dispatcher.updateUI()

    def prb_onTeamStatesReceived(self):
        super(CompanyFunctional, self).prb_onTeamStatesReceived()
        playerInfo = self.getPlayerInfo()
        if playerInfo.isReady() or self.isCreator():
            if self.getTeamState(team=1).isInQueue() and playerInfo.roster == PREBATTLE_ROSTER.ASSIGNED_IN_TEAM1:
                events_dispatcher.loadBattleQueue()
            else:
                events_dispatcher.loadHangar()

    def prb_onPlayerAdded(self, pID, roster):
        super(CompanyFunctional, self).prb_onPlayerAdded(pID, roster)
        events_dispatcher.updateUI()

    def prb_onPlayerRemoved(self, pID, roster, name):
        super(CompanyFunctional, self).prb_onPlayerRemoved(pID, roster, name)
        events_dispatcher.updateUI()

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
        events_dispatcher.addCompanyToCarousel()
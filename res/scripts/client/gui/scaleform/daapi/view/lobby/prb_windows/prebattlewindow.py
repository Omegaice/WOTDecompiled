from CurrentVehicle import g_currentVehicle
from adisp import process
from debug_utils import LOG_ERROR
from gui.Scaleform.daapi.view.lobby.prb_windows.sf_settings import PRB_WINDOW_VIEW_ALIAS
from gui.Scaleform.daapi.view.meta.PrebattleWindowMeta import PrebattleWindowMeta
from gui.Scaleform.daapi.view.meta.WindowViewMeta import WindowViewMeta
from gui.Scaleform.framework import AppRef, VIEW_TYPE
from gui.Scaleform.framework.entities.View import View
from gui.Scaleform.framework.managers.containers import POP_UP_CRITERIA
from gui.Scaleform.managers.windows_stored_data import DATA_TYPE, TARGET_ID
from gui.Scaleform.managers.windows_stored_data import stored_window
from gui.prb_control import context, info
from gui.prb_control.formatters import messages
from gui.prb_control.prb_helpers import PrbListener
from gui.shared import events, EVENT_BUS_SCOPE
from helpers import int2roman
from messenger import g_settings, MessengerEntry
from messenger.ext import channel_num_gen
from messenger.gui.Scaleform.sf_settings import MESSENGER_VIEW_ALIAS
from messenger.m_constants import USER_GUI_TYPE
from messenger.proto.bw import find_criteria
from messenger.proto.events import g_messengerEvents
from messenger.storage import storage_getter
from prebattle_shared import decodeRoster

@stored_window(DATA_TYPE.CAROUSEL_WINDOW, TARGET_ID.CHANNEL_CAROUSEL)

class PrebattleWindow(View, WindowViewMeta, PrebattleWindowMeta, PrbListener, AppRef):

    def __init__(self, prbName = 'prebattle'):
        super(PrebattleWindow, self).__init__()
        self.__prbName = prbName
        self.__clientID = channel_num_gen.getClientID4Prebattle(self.prbFunctional.getPrbType())

    def onWindowClose(self):
        chat = self.chat
        if chat:
            chat.minimize()
        self.destroy()

    def onWindowMinimize(self):
        chat = self.chat
        if chat:
            chat.minimize()
        self.destroy()

    @storage_getter('users')
    def usersStorage(self):
        return None

    @process
    def requestToReady(self, value):
        if value:
            waitingID = 'prebattle/player_ready'
        else:
            waitingID = 'prebattle/player_not_ready'
        result = yield self.prbDispatcher.sendPrbRequest(context.SetPlayerStateCtx(value, waitingID=waitingID))
        if result:
            self.as_toggleReadyBtnS(not value)

    @process
    def requestToLeave(self):
        yield self.prbDispatcher.leave(context.LeavePrbCtx(waitingID='prebattle/leave'))

    def showPrebattleSendInvitesWindow(self):
        if self.canSendInvite():
            self.fireEvent(events.ShowWindowEvent(events.ShowWindowEvent.SHOW_SEND_INVITES_WINDOW, {'prbName': self.__prbName}), scope=EVENT_BUS_SCOPE.LOBBY)

    def showFAQWindow(self):
        self.fireEvent(events.ShowWindowEvent(events.ShowWindowEvent.SHOW_FAQ_WINDOW), scope=EVENT_BUS_SCOPE.LOBBY)

    def getClientID(self):
        return self.__clientID

    def requestToKickPlayer(self, value):
        pass

    def canSendInvite(self):
        return self.prbFunctional.getPermissions().canSendInvite()

    def isPlayerReady(self):
        return self.prbFunctional.getPlayerInfo().isReady()

    def isPlayerCreator(self):
        return self.prbFunctional.isCreator()

    def isReadyBtnEnabled(self):
        functional = self.prbFunctional
        team, assigned = decodeRoster(functional.getRosterKey())
        return g_currentVehicle.isReadyToPrebattle() and functional.getTeamState().isInQueue() and not assigned

    def isLeaveBtnEnabled(self):
        functional = self.prbFunctional
        team, assigned = decodeRoster(functional.getRosterKey())
        return functional.getTeamState().isInQueue() and functional.getPlayerInfo().isReady() and not assigned

    def startListening(self):
        self.startPrbListening()
        g_currentVehicle.onChanged += self._handleCurrentVehicleChanged
        g_messengerEvents.users.onUserRosterChanged += self._onUserRosterChanged

    def stopListening(self):
        self.stopPrbListening()
        self.removeListener(events.MessengerEvent.PRB_CHANNEL_CTRL_INITED, self.__handlePrbChannelControllerInited, scope=EVENT_BUS_SCOPE.LOBBY)
        g_currentVehicle.onChanged -= self._handleCurrentVehicleChanged
        g_messengerEvents.users.onUserRosterChanged -= self._onUserRosterChanged

    @property
    def chat(self):
        chat = None
        if MESSENGER_VIEW_ALIAS.CHANNEL_COMPONENT in self.components:
            chat = self.components[MESSENGER_VIEW_ALIAS.CHANNEL_COMPONENT]
        return chat

    def onPrbFunctionalFinished(self):
        self._closeSendInvitesWindow()

    def onPlayerAdded(self, functional, playerInfo):
        chat = self.chat
        if chat and not playerInfo.isCurrentPlayer():
            chat.as_addMessageS(messages.getPlayerAddedMessage(self.__prbName, playerInfo))

    def onPlayerRemoved(self, functional, playerInfo):
        chat = self.chat
        if chat and not playerInfo.isCurrentPlayer():
            chat.as_addMessageS(messages.getPlayerRemovedMessage(self.__prbName, playerInfo))

    def onPlayerRosterChanged(self, functional, actorInfo, playerInfo):
        chat = self.chat
        if chat:
            chat.as_addMessageS(messages.getPlayerAssignFlagChanged(actorInfo, playerInfo))

    def onPlayerStateChanged(self, functional, roster, playerInfo):
        team, assigned = decodeRoster(roster)
        data = {'uid': playerInfo.dbID,
         'state': playerInfo.state,
         'icon': '',
         'vShortName': '',
         'vLevel': '',
         'vType': ''}
        if playerInfo.isVehicleSpecified():
            vehicle = playerInfo.getVehicle()
            data.update({'icon': vehicle.iconContour,
             'vShortName': vehicle.shortUserName,
             'vLevel': int2roman(vehicle.level),
             'vType': vehicle.type})
        self.as_setPlayerStateS(team, assigned, data)
        if playerInfo.isCurrentPlayer():
            self.as_toggleReadyBtnS(not playerInfo.isReady())
        else:
            chat = self.chat
            if chat:
                chat.as_addMessageS(messages.getPlayerStateChangedMessage(self.__prbName, playerInfo))

    def _populate(self):
        super(PrebattleWindow, self)._populate()
        self.startListening()
        self.as_enableReadyBtnS(self.isReadyBtnEnabled())

    def _dispose(self):
        super(PrebattleWindow, self)._dispose()
        self.stopListening()

    def _closeSendInvitesWindow(self):
        container = self.app.containerManager.getContainer(VIEW_TYPE.WINDOW)
        if container is not None:
            window = container.getView(criteria={POP_UP_CRITERIA.VIEW_ALIAS: PRB_WINDOW_VIEW_ALIAS.SEND_INVITES_WINDOW})
            if window is not None:
                window.destroy()
        return

    def _setRosterList(self, rosters):
        raise NotImplementedError

    def _makeAccountsData(self, accounts):
        result = []
        isPlayerSpeaking = self.app.voiceChatManager.isPlayerSpeaking
        getUser = self.usersStorage.getUser
        getColors = g_settings.getColorScheme('rosters').getColors
        accounts = sorted(accounts, cmp=info.getPlayersComparator())
        for account in accounts:
            vContourIcon = ''
            vShortName = ''
            vLevel = ''
            vType = ''
            user = getUser(account.dbID)
            if user is not None:
                key = user.getGuiType()
            else:
                key = USER_GUI_TYPE.OTHER
            if account.isVehicleSpecified():
                vehicle = account.getVehicle()
                vContourIcon = vehicle.iconContour
                vShortName = vehicle.shortUserName
                vLevel = int2roman(vehicle.level)
                vType = vehicle.type
            result.append({'accID': account.accID,
             'uid': account.dbID,
             'userName': account.name,
             'fullName': account.getFullName(),
             'time': account.time,
             'himself': account.isCurrentPlayer(),
             'isCreator': account.isCreator,
             'state': account.state,
             'icon': vContourIcon,
             'vShortName': vShortName,
             'vLevel': vLevel,
             'vType': vType,
             'chatRoster': user.getRoster() if user else 0,
             'isPlayerSpeaking': isPlayerSpeaking(account.dbID),
             'colors': getColors(key)})

        return result

    def _handleCurrentVehicleChanged(self):
        self.as_enableReadyBtnS(self.isReadyBtnEnabled())

    def _onUserRosterChanged(self, actionIndex, user):
        self._setRosterList(self.prbFunctional.getRosters())

    def _onRegisterFlashComponent(self, viewPy, alias):
        if alias == MESSENGER_VIEW_ALIAS.CHANNEL_COMPONENT:
            channels = MessengerEntry.g_instance.gui.channelsCtrl
            controller = None
            if channels:
                prbType = self.prbFunctional.getPrbType()
                if prbType:
                    controller = channels.getControllerByCriteria(find_criteria.BWPrbChannelFindCriteria(prbType))
            if controller is not None:
                controller.setView(viewPy)
            else:
                self.addListener(events.MessengerEvent.PRB_CHANNEL_CTRL_INITED, self.__handlePrbChannelControllerInited, scope=EVENT_BUS_SCOPE.LOBBY)
        return

    def __handlePrbChannelControllerInited(self, ctx):
        prbType = ctx.get('prbType', 0)
        if prbType is 0:
            LOG_ERROR('Prebattle type is not defined', ctx)
            return
        else:
            controller = ctx.get('controller')
            if controller is None:
                LOG_ERROR('Channel controller is not defined', ctx)
                return
            if prbType is self.prbFunctional.getPrbType():
                controller.setView(self)
            return

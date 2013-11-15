# 2013.11.15 11:26:07 EST
# Embedded file name: scripts/client/gui/Scaleform/daapi/view/lobby/prb_windows/invite_post_actions.py
import BigWorld
from ConnectionManager import connectionManager
from adisp import process
from debug_utils import LOG_DEBUG, LOG_ERROR
from gui.LobbyContext import g_lobbyContext
from gui.Scaleform.Waiting import Waiting
from gui.Scaleform.daapi.settings import VIEW_ALIAS
from gui.Scaleform.framework import AppRef, VIEW_TYPE
from gui.prb_control.context import LeavePrbCtx
from gui.prb_control.dispatcher import g_prbLoader
from gui.shared import g_eventBus, EVENT_BUS_SCOPE
from gui.shared.actions_chain import Action
from gui.shared.events import LoginEventEx
from predefined_hosts import g_preDefinedHosts
CONNECT_TO_PERIPHERY_DELAY = 2.0

class LeavePrebattle(Action):

    def __init__(self):
        super(LeavePrebattle, self).__init__()
        self._running = False

    def invoke(self):
        dispatcher = g_prbLoader.getDispatcher()
        if dispatcher:
            functional = dispatcher.getPrbFunctional()
            if functional.hasEntity():
                self._running = True
                self.__doLeave(dispatcher)
            else:
                LOG_DEBUG('Leave prebattle. Player has not prebattle')
                self._completed = True

    def isInstantaneous(self):
        return False

    @process
    def __doLeave(self, dispatcher):
        self._completed = yield dispatcher.leave(LeavePrbCtx(waitingID='prebattle/leave'))
        if self._completed:
            LOG_DEBUG('Leave prebattle. Player left prebattle')
        else:
            LOG_ERROR('Leave prebattle. Action was failed')
        self._running = False


class DisconnectFromPeriphery(Action, AppRef):

    def __init__(self):
        super(DisconnectFromPeriphery, self).__init__()

    def isInstantaneous(self):
        return False

    def invoke(self):
        self._running = True
        self.app.logoff()

    def isRunning(self):
        view = self.app.containerManager.getView(VIEW_TYPE.DEFAULT)
        if view and view.settings.alias == VIEW_ALIAS.LOGIN and view._isCreated() and connectionManager.isDisconnected():
            LOG_DEBUG('Disconnect action. Player came to login')
            self._completed = True
            self._running = False
        return self._running


class ConnectToPeriphery(Action, AppRef):

    def __init__(self, peripheryID):
        super(ConnectToPeriphery, self).__init__()
        self.__host = g_preDefinedHosts.periphery(peripheryID)
        self.__endTime = None
        self.__credentials = g_lobbyContext.getCredentials()
        return

    def isInstantaneous(self):
        return False

    def isRunning(self):
        if self.__endTime and self.__endTime <= BigWorld.time():
            self.__endTime = None
            self.__doConnect()
        return super(ConnectToPeriphery, self).isRunning()

    def invoke(self):
        if self.__host and self.__credentials:
            if len(self.__credentials) < 2:
                self._completed = False
                LOG_ERROR('Connect action. Login info is invalid')
                return
            login, token2 = self.__credentials
            if not login or not token2:
                self._completed = False
                LOG_ERROR('Connect action. Login info is invalid')
                return
            self._running = True
            self.__endTime = BigWorld.time() + CONNECT_TO_PERIPHERY_DELAY
            Waiting.show('login')
        else:
            LOG_ERROR('Connect action. Login info is invalid')
            self._completed = False
            self._running = False

    def __doConnect(self):
        login, token2 = self.__credentials
        self.__addHandlers()
        connectionManager.connect(self.__host.url, login, '', self.__host.keyPath, token2=token2)

    def __addHandlers(self):
        g_eventBus.addListener(LoginEventEx.ON_LOGIN_QUEUE_CLOSED, self.__onLoginQueueClosed, scope=EVENT_BUS_SCOPE.LOBBY)
        connectionManager.connectionStatusCallbacks += self.__onConnectionStatus

    def __removeHandlers(self):
        g_eventBus.removeListener(LoginEventEx.ON_LOGIN_QUEUE_CLOSED, self.__onLoginQueueClosed, scope=EVENT_BUS_SCOPE.LOBBY)
        connectionManager.connectionStatusCallbacks -= self.__onConnectionStatus

    def __onConnectionStatus(self, stage, status, serverMsg, isAutoRegister):
        self.__removeHandlers()
        if stage == 1 and status == 'LOGGED_ON':
            self._completed = True
            LOG_DEBUG('Connect action. Player login to periphery')
        else:
            LOG_DEBUG('Connect action. Player can not login to periphery')
            self._completed = False
        self._running = False

    def __onLoginQueueClosed(self, _):
        self.__removeHandlers()
        self._completed = False
        self._running = False
        LOG_DEBUG('Connect action. Player exit from login queue')


class PrbInvitesInit(Action):

    def __init__(self):
        super(PrbInvitesInit, self).__init__()

    def isInstantaneous(self):
        return False

    def invoke(self):
        invitesManager = g_prbLoader.getInvitesManager()
        if invitesManager:
            if invitesManager.isInited():
                LOG_DEBUG('Invites init action. Invites init action. List of invites is build')
                self._completed = True
            else:
                self._running = True
                invitesManager.onReceivedInviteListInited += self.__onInvitesListInited
        else:
            LOG_ERROR('Invites init action. Invites manager not found')
            self._completed = False

    def __onInvitesListInited(self):
        invitesManager = g_prbLoader.getInvitesManager()
        if invitesManager:
            LOG_DEBUG('Invites init action. List of invites is build')
            invitesManager.onReceivedInviteListInited -= self.__onInvitesListInited
        else:
            LOG_ERROR('Invites manager not found')
        self._completed = True
        self._running = False
# okay decompyling res/scripts/client/gui/scaleform/daapi/view/lobby/prb_windows/invite_post_actions.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:26:08 EST

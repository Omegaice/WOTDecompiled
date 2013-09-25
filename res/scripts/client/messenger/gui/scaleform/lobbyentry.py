# Embedded file name: scripts/client/messenger/gui/Scaleform/LobbyEntry.py
from debug_utils import LOG_ERROR
from gui import DialogsInterface, SystemMessages
from gui.Scaleform.daapi.view import dialogs
from gui.Scaleform.managers.windows_stored_data import g_windowsStoredData, TARGET_ID, DATA_TYPE
from gui.shared import EVENT_BUS_SCOPE, g_eventBus
from gui.shared.events import MessengerEvent
from messenger.formatters.users_messages import getUserRosterChangedMessage
from messenger.gui import events_dispatcher
from messenger.gui.Scaleform import channels
from messenger.gui.Scaleform.data.ChannelsCarouselHandler import ChannelsCarouselHandler
from messenger.gui.interfaces import IGUIEntry
from messenger.m_constants import LAZY_CHANNEL, MESSENGER_SCOPE
from messenger.proto.events import g_messengerEvents
from messenger.storage import storage_getter

class LobbyEntry(IGUIEntry):

    def __init__(self):
        super(LobbyEntry, self).__init__()
        self.__channelsCtrl = None
        self.__carouselHandler = None
        return

    @storage_getter('channels')
    def channelsStorage(self):
        return None

    @property
    def channelsCtrl(self):
        return self.__channelsCtrl

    def init(self):
        self.__channelsCtrl = channels.LobbyControllers()
        self.__channelsCtrl.init()
        self.__carouselHandler = ChannelsCarouselHandler(self)
        self.__carouselHandler.init()
        g_messengerEvents.channels.onMessageReceived += self.__me_onMessageReceived
        add = g_eventBus.addListener
        add(MessengerEvent.LAZY_CHANNEL_CTRL_INITED, self.__handleLazyChannelCtlInited, scope=EVENT_BUS_SCOPE.LOBBY)
        add(MessengerEvent.LAZY_CHANNEL_CTRL_DESTROYED, self.__handleLazyChannelCtlDestroyed, scope=EVENT_BUS_SCOPE.LOBBY)
        add(MessengerEvent.LOBBY_CHANNEL_CTRL_INITED, self.__handleLobbyChannelCtlInited, scope=EVENT_BUS_SCOPE.LOBBY)
        add(MessengerEvent.LOBBY_CHANNEL_CTRL_DESTROYED, self.__handleLobbyChannelCtlDestroyed, scope=EVENT_BUS_SCOPE.LOBBY)

    def clear(self):
        if self.__channelsCtrl is not None:
            self.__channelsCtrl.clear()
            self.__channelsCtrl = None
        if self.__carouselHandler is not None:
            self.__carouselHandler.clear()
            self.__carouselHandler = None
        g_messengerEvents.channels.onMessageReceived -= self.__me_onMessageReceived
        remove = g_eventBus.removeListener
        remove(MessengerEvent.LAZY_CHANNEL_CTRL_INITED, self.__handleLazyChannelCtlInited, scope=EVENT_BUS_SCOPE.LOBBY)
        remove(MessengerEvent.LAZY_CHANNEL_CTRL_DESTROYED, self.__handleLazyChannelCtlDestroyed, scope=EVENT_BUS_SCOPE.LOBBY)
        remove(MessengerEvent.LOBBY_CHANNEL_CTRL_INITED, self.__handleLobbyChannelCtlInited, scope=EVENT_BUS_SCOPE.LOBBY)
        remove(MessengerEvent.LOBBY_CHANNEL_CTRL_DESTROYED, self.__handleLobbyChannelCtlDestroyed, scope=EVENT_BUS_SCOPE.LOBBY)
        return

    def show(self):
        self.__carouselHandler.start()
        cEvents = g_messengerEvents.channels
        cEvents.onPlayerEnterChannelByAction += self.__me_onPlayerEnterChannelByAction
        cEvents.onConnectingToSecureChannel += self.__me_onConnectingToSecureChannel
        cEvents.onChannelInfoUpdated += self.__me_onChannelInfoUpdated
        g_messengerEvents.users.onUserRosterChanged += self.__me_onUsersRosterChanged
        g_messengerEvents.onServerErrorReceived += self.__me_onServerErrorReceived

    def close(self, nextScope):
        storedData = g_windowsStoredData.getMap(TARGET_ID.CHANNEL_CAROUSEL, DATA_TYPE.CHANNEL_WINDOW)
        for controller in self.__channelsCtrl.getControllersIterator():
            channel = controller.getChannel()
            key = (channel.getProtoType(), channel.getID())
            if key in storedData:
                storedData[key].setTrusted(True)
            controller.deactivate(entryClosing=True)

        self.__carouselHandler.stop()
        if nextScope is MESSENGER_SCOPE.LOGIN:
            self.__channelsCtrl.removeControllers()
            self.__carouselHandler.removeChannels()
        cEvents = g_messengerEvents.channels
        cEvents.onPlayerEnterChannelByAction -= self.__me_onPlayerEnterChannelByAction
        cEvents.onConnectingToSecureChannel -= self.__me_onConnectingToSecureChannel
        cEvents.onChannelInfoUpdated -= self.__me_onChannelInfoUpdated
        g_messengerEvents.users.onUserRosterChanged -= self.__me_onUsersRosterChanged
        g_messengerEvents.onServerErrorReceived -= self.__me_onServerErrorReceived

    def addClientMessage(self, message, isCurrentPlayer = False):
        pass

    def __me_onMessageReceived(self, message, channel):
        if channel:
            clientID = channel.getClientID()
            controller = self.__channelsCtrl.getController(clientID)
            if controller and not controller.addMessage(message):
                self.__carouselHandler.notifyChannel(channel)

    def __me_onPlayerEnterChannelByAction(self, channel):
        controller = self.channelsCtrl.getController(channel.getClientID())
        if controller is None:
            LOG_ERROR('Controller not found', channel)
        else:
            events_dispatcher.showLobbyChannelWindow(channel.getClientID())
        return

    def __me_onConnectingToSecureChannel(self, channel):
        events_dispatcher.showConnectToSecureChannelWindow(channel)

    def __me_onChannelInfoUpdated(self, channel):
        self.__carouselHandler.updateChannel(channel)

    def __me_onUsersRosterChanged(self, action, user):
        message = getUserRosterChangedMessage(action, user)
        if message:
            SystemMessages.pushMessage(message)

    def __me_onServerErrorReceived(self, error):
        if error.isModal():
            DialogsInterface.showDialog(dialogs.SimpleDialogMeta(error.getTitle(), error.getMessage(), dialogs.I18nInfoDialogButtons('common/error')), lambda *args: None)
        else:
            SystemMessages.pushMessage(error.getMessage(), type=SystemMessages.SM_TYPE.Error)

    def __handleLazyChannelCtlInited(self, event):
        ctx = event.ctx
        controller = ctx.get('controller')
        if controller is None:
            LOG_ERROR('Controller is not defined', ctx)
            return
        else:
            channel = controller.getChannel()
            if channel.getName() == LAZY_CHANNEL.COMMON:
                self.__carouselHandler.addChannel(channel, lazy=True)
            return

    def __handleLazyChannelCtlDestroyed(self, event):
        ctx = event.ctx
        controller = ctx.get('controller')
        if controller is None:
            LOG_ERROR('Controller is not defined', ctx)
            return
        else:
            self.__carouselHandler.removeChannel(controller.getChannel())
            return

    def __handleLobbyChannelCtlInited(self, event):
        ctx = event.ctx
        controller = ctx.get('controller')
        if controller is None:
            LOG_ERROR('Controller is not defined', ctx)
            return
        else:
            self.__carouselHandler.addChannel(controller.getChannel())
            return

    def __handleLobbyChannelCtlDestroyed(self, event):
        ctx = event.ctx
        controller = ctx.get('controller')
        if controller is None:
            LOG_ERROR('Controller is not defined', ctx)
            return
        else:
            self.__carouselHandler.removeChannel(controller.getChannel())
            return
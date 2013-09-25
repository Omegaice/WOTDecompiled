import Event
from messenger.m_constants import PROTO_TYPE
from messenger.proto import proto_getter
from messenger.proto.events import g_messengerEvents
POPUPS_STATE = 0
LIST_STATE = 1

class NotificationsModel:

    def __init__(self):
        self.__layoutSettings = {'paddingRight': 0,
         'paddingBottom': 0}
        self.__currentDisplayState = None
        self.__notifiedMessagesCount = 0
        self.onLayoutSettingsChanged = Event.Event()
        self.onDisplayStateChanged = Event.Event()
        self.onMessageReceived = Event.Event()
        self.onNotifiedMessagesCountChanged = Event.Event()
        channel = g_messengerEvents.serviceChannel
        channel.onServerMessageReceived += self.__onMessageReceived
        channel.onClientMessageReceived += self.__onMessageReceived
        self.__setDisplayState(POPUPS_STATE, {})
        return

    @proto_getter(PROTO_TYPE.BW)
    def proto(self):
        return None

    def setListDisplayState(self, data = None):
        self.__setDisplayState(LIST_STATE, data)

    def setPopupsDisplayState(self, data = None):
        self.__setDisplayState(POPUPS_STATE, data)

    def __setDisplayState(self, newState, data):
        if newState != self.__currentDisplayState:
            oldState = self.__currentDisplayState
            self.__currentDisplayState = newState
            self.onDisplayStateChanged(oldState, newState, data)

    def getDisplayState(self):
        return self.__currentDisplayState

    def setLayoutSettings(self, paddingRight, paddingBottom):
        self.__layoutSettings = {'paddingRight': paddingRight,
         'paddingBottom': paddingBottom}
        self.onLayoutSettingsChanged(self.__layoutSettings)

    def getLayoutSettings(self):
        return self.__layoutSettings

    def __onMessageReceived(self, message, isPriority, notify, auxData):
        self.onMessageReceived(message, isPriority, notify, auxData)
        self.__decrementUnreadMessagesCount()

    def incrementNotifiedMessagesCount(self):
        self.__notifiedMessagesCount += 1
        self.onNotifiedMessagesCountChanged(self.__notifiedMessagesCount)

    def resetNotifiedMessagesCount(self):
        self.__notifiedMessagesCount = 0
        self.onNotifiedMessagesCountChanged(0)

    def decrementNotifiedMessagesCount(self):
        self.__notifiedMessagesCount -= 1
        self.onNotifiedMessagesCountChanged(self.__notifiedMessagesCount)

    def getNotifiedMessagesCount(self):
        return self.__notifiedMessagesCount

    def getMessagesList(self):
        return self.proto.serviceChannel.getServiceMessagesFullData()

    def requestUnreadMessages(self):
        self.proto.serviceChannel.fireReceiveMessageEvents()

    def __decrementUnreadMessagesCount(self):
        self.proto.serviceChannel.decrementUnreadCount()

    def cleanUp(self):
        channel = g_messengerEvents.serviceChannel
        channel.onServerMessageReceived -= self.__onMessageReceived
        channel.onClientMessageReceived -= self.__onMessageReceived
        self.onLayoutSettingsChanged.clear()
        self.onDisplayStateChanged.clear()
        self.onMessageReceived.clear()
        self.onNotifiedMessagesCountChanged.clear()


g_instance = None

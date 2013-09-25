from collections import deque
import BigWorld
from chat_shared import CHAT_ACTIONS
from constants import IS_DEVELOPMENT
from debug_utils import *
from messenger import formatters
from messenger.m_constants import SCH_MSGS_MAX_LENGTH, MESSENGER_SCOPE
from messenger.proto.bw.ChatActionsListener import ChatActionsListener
from messenger.proto.bw.wrappers import ServiceChannelMessage
from messenger.proto.events import g_messengerEvents
from adisp import process

class ServiceChannelManager(ChatActionsListener):
    __messages = deque([], SCH_MSGS_MAX_LENGTH)

    def __init__(self):
        ChatActionsListener.__init__(self)
        self.__unreadMessageCount = 0

    def addListeners(self):
        self.addListener(self.onReceiveSysMessage, CHAT_ACTIONS.sysMessage)
        self.addListener(self.onReceivePersonalSysMessage, CHAT_ACTIONS.personalSysMessage)

    def clear(self):
        self.__messages.clear()

    def switch(self, scope):
        if scope is MESSENGER_SCOPE.LOBBY:
            self.requestLastServiceMessages()

    @process
    def __addServerMessage(self, message):
        yield lambda callback: callback(True)
        formatter = formatters.SCH_SERVER_FORMATTERS_DICT.get(message.type)
        if formatter:
            try:
                notify = formatter.notify()
                isAsync = formatter.isAsync()
                if isAsync:
                    formatted = yield formatter.format(message)
                else:
                    formatted = formatter.format(message)
                if formatted is not None:
                    formatted.update({'msgTypeId': message.type})
            except:
                LOG_CURRENT_EXCEPTION()
                return

            if formatted:
                priority = message.isHighImportance and message.active
                self.__messages.append((formatted,
                 True,
                 priority,
                 notify,
                 []))
                self.__unreadMessageCount += 1
                g_messengerEvents.serviceChannel.onServerMessageReceived(formatted.copy(), message.isHighImportance and message.active, notify, [])
            elif IS_DEVELOPMENT:
                LOG_WARNING('Not enough data to format. Action data : ', message)
        elif IS_DEVELOPMENT:
            LOG_WARNING('Formatter not found. Action data : ', message)
        return

    def __addClientMessage(self, message, msgType, isPriority = False, auxData = None):
        if auxData is None:
            auxData = []
        formatter = formatters.SCH_CLIENT_FORMATTERS_DICT.get(msgType)
        if formatter:
            try:
                formatted = formatter.format(message, auxData)
                notify = formatter.notify()
            except:
                LOG_CURRENT_EXCEPTION()
                return

            self.__messages.append((formatted,
             False,
             isPriority,
             notify,
             auxData))
            self.__unreadMessageCount += 1
            g_messengerEvents.serviceChannel.onClientMessageReceived(formatted.copy(), isPriority, notify, auxData[:])
        elif IS_DEVELOPMENT:
            LOG_WARNING('Formatter not found:', msgType, message)
        return

    def requestLastServiceMessages(self):
        BigWorld.player().requestLastSysMessages()

    def onReceiveSysMessage(self, chatAction):
        message = ServiceChannelMessage.fromChatAction(chatAction)
        self.__addServerMessage(message)

    def onReceivePersonalSysMessage(self, chatAction):
        message = ServiceChannelMessage.fromChatAction(chatAction, personal=True)
        self.__addServerMessage(message)

    def pushClientSysMessage(self, message, msgType, isPriority = False):
        self.__addClientMessage(message, formatters.SCH_CLIENT_MSG_TYPE.SYS_MSG_TYPE, isPriority=isPriority, auxData=[msgType.name()])

    def pushClientMessage(self, message, msgType, isPriority = False, auxData = None):
        self.__addClientMessage(message, msgType, isPriority=isPriority, auxData=auxData)

    def getServiceMessagesCount(self):
        return len(self.__messages)

    def getServiceMessages(self):
        return map(lambda item: item[0], self.__messages)

    def getServiceMessagesFullData(self):
        result = []
        for message, isServerMsg, flag, notify, auxData in self.__messages:
            result.append((message.copy(),
             isServerMsg,
             flag,
             notify,
             auxData[:]))

        return result

    def fireReceiveMessageEvents(self):
        if not self.__unreadMessageCount:
            return
        unreadMessages = list(self.__messages)[-self.__unreadMessageCount:]
        serviceChannel = g_messengerEvents.serviceChannel
        onServerMessageReceived = serviceChannel.onServerMessageReceived
        onClientMessageReceived = serviceChannel.onClientMessageReceived
        for message, isServerMsg, flag, notify, auxData in unreadMessages:
            if isServerMsg:
                onServerMessageReceived(message.copy(), flag, notify, auxData[:])
            else:
                onClientMessageReceived(message.copy(), flag, notify, auxData[:])

    def resetUnreadCount(self):
        self.__unreadMessageCount = 0

    def decrementUnreadCount(self):
        self.__unreadMessageCount -= 1
        if self.__unreadMessageCount < 0:
            LOG_WARNING('Unread messages count could not be less then 0! Check it!')

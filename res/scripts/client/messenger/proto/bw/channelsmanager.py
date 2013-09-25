import BigWorld
import Event
from chat_shared import CHAT_ACTIONS, CHAT_RESPONSES
from constants import USER_ACTIVE_CHANNELS_LIMIT
from debug_utils import LOG_DEBUG, LOG_WARNING
from messenger import g_settings
from messenger.m_constants import LAZY_CHANNEL, MESSENGER_SCOPE
from messenger.proto.bw.ChatActionsListener import ChatActionsListener
from messenger.proto.bw import entities
from messenger.proto.bw.errors import ChannelNotFound
from messenger.proto.bw import find_criteria
from messenger.proto.bw.filters import BWFiltersChain
from messenger.proto.bw.wrappers import ChatActionWrapper
from messenger.proto.events import g_messengerEvents
from messenger.storage import storage_getter

class CREATE_CHANNEL_RESULT(object):
    doRequest, activeChannelLimitReached = range(2)


class ChannelsManager(ChatActionsListener):

    def __init__(self):
        ChatActionsListener.__init__(self, {CHAT_RESPONSES.channelNotExists: '_ChannelsManager__onChannelNotExists',
         CHAT_RESPONSES.commandInCooldown: '_ChannelsManager__onCommandInCooldown'})
        self.__eventManager = Event.EventManager()
        self.onRequestChannelsComplete = Event.Event(self.__eventManager)
        self.onFindChannelsFailed = Event.Event(self.__eventManager)
        self._filtersChain = BWFiltersChain()
        self.__channels = {}
        self.__creationInfo = {}

    @storage_getter('channels')
    def channelsStorage(self):
        return None

    def addListeners(self):
        self._filtersChain.addListeners()
        self.addListener(self.__onRequestChannels, CHAT_ACTIONS.requestChannels)
        self.addListener(self.__onBroadcast, CHAT_ACTIONS.broadcast)
        self.addListener(self.__onSelfEnterChat, CHAT_ACTIONS.selfEnter)
        self.addListener(self.__onEnterChat, CHAT_ACTIONS.enter)
        self.addListener(self.__onSelfLeaveChat, CHAT_ACTIONS.selfLeave)
        self.addListener(self.__onLeaveChat, CHAT_ACTIONS.leave)
        self.addListener(self.__onChannelDestroyed, CHAT_ACTIONS.channelDestroyed)
        self.addListener(self.__onRequestChannelMembers, CHAT_ACTIONS.requestMembers)
        self.addListener(self.__onReceiveMembersDelta, CHAT_ACTIONS.receiveMembersDelta)
        self.addListener(self.__onMemberStatusUpdate, CHAT_ACTIONS.memberStatusUpdate)
        self.addListener(self.__onChannelInfoUpdated, CHAT_ACTIONS.channelInfoUpdated)
        self.addListener(self.__onChatChannelCreated, CHAT_ACTIONS.createChannel)
        g_settings.onUserPreferencesUpdated += self.__ms_onUserPreferencesUpdated

    def removeAllListeners(self):
        self._filtersChain.removeListeners()
        super(ChannelsManager, self).removeAllListeners()
        g_settings.onUserPreferencesUpdated -= self.__ms_onUserPreferencesUpdated

    def switch(self, scope):
        if scope is MESSENGER_SCOPE.BATTLE:
            self.exitFromLazyChannels()
        self._filtersChain.switch(scope)

    def clear(self):
        self.__creationInfo.clear()
        self.__eventManager.clear()
        self.__channels.clear()

    def sendMessage(self, channelID, message):
        message = self._filtersChain.chainOut(message)
        if not len(message):
            return
        BigWorld.player().broadcast(channelID, message)

    def requestChannelMembers(self, channelID):
        BigWorld.player().requestChatChannelMembers(channelID)

    def joinToChannel(self, channelID, password = None):
        channel = self.channelsStorage.getChannel(entities.BWChannelLightEntity(channelID))
        if not channel and channelID in self.__channels:
            channel = self.__channels[channelID]
        if not channel:
            raise ChannelNotFound(channelID)
        if channel.isJoined():
            g_messengerEvents.channels.onPlayerEnterChannelByAction(channel)
            return
        if channel and channel.getProtoData().isSecured and not password:
            g_messengerEvents.channels.onConnectingToSecureChannel(channel)
            return
        BigWorld.player().enterChat(channelID, password)

    def exitFromChannel(self, channelID):
        BigWorld.player().leaveChat(channelID)

    def createChannel(self, name, password = None):
        channels = self.channelsStorage.getChannelsByCriteria(find_criteria.BWActiveChannelFindCriteria())
        if USER_ACTIVE_CHANNELS_LIMIT <= len(channels):
            return CREATE_CHANNEL_RESULT.activeChannelLimitReached
        if name.startswith('#'):
            name = name[1:]
        if password:
            self.__creationInfo[name] = password
        BigWorld.player().createChatChannel(name, password)
        return CREATE_CHANNEL_RESULT.doRequest

    def findChannels(self, token, requestID = None):
        BigWorld.player().findChatChannels(token, requestID=requestID)

    def exitFromLazyChannels(self):
        channels = self.channelsStorage.getChannelsByCriteria(find_criteria.BWLazyChannelFindCriteria(LAZY_CHANNEL.ALL))
        for channel in channels:
            if channel.isJoined():
                LOG_DEBUG('Send request to exit from lazy channel', channel.getName().encode('utf-8'))
                self.exitFromChannel(channel.getID())

    def removeChannelFromClient(self, channel):
        if channel.isJoined():
            LOG_WARNING('Client is removing channel to which player is joined', channel)
        if self.channelsStorage.removeChannel(channel):
            g_messengerEvents.channels.onChannelDestroyed(channel)

    def __onRequestChannels(self, chatAction, join = False):
        chatActionDict = dict(chatAction)
        data = chatActionDict.get('data', [])
        requestID = chatActionDict.get('requestID', -1)
        channels = set()
        isStore = requestID == -1
        for channelData in data:
            received = entities.BWChannelEntity(dict(channelData))
            channel = self.channelsStorage.getChannel(received)
            if channel:
                channel.update(other=received)
                if not isStore:
                    self.__channels[received.getID()] = received
            else:
                if isStore:
                    if self.channelsStorage.addChannel(received):
                        g_messengerEvents.channels.onChannelInited(received)
                else:
                    self.__channels[received.getID()] = received
                channel = received
            channels.add(channel)
            if join:
                self.joinToChannel(channel.getID())

        self.onRequestChannelsComplete(requestID, channels)

    def __onBroadcast(self, chatAction):
        wrapper = ChatActionWrapper(**dict(chatAction))
        self._filtersChain.chainIn(wrapper)
        if len(wrapper.data) == 0:
            return
        channel = self.channelsStorage.getChannel(entities.BWChannelLightEntity(wrapper.channel))
        g_messengerEvents.channels.onMessageReceived(wrapper, channel)

    def __onSelfEnterChat(self, chatAction):
        wrapper = ChatActionWrapper(**dict(chatAction))
        channelID = wrapper.channel
        channel = self.channelsStorage.getChannel(entities.BWChannelLightEntity(channelID))
        if not channel and channelID in self.__channels:
            channel = self.__channels[channelID]
            if self.channelsStorage.addChannel(channel):
                g_messengerEvents.channels.onChannelInited(channel)
                g_messengerEvents.channels.onPlayerEnterChannelByAction(channel)
        if not channel:
            raise ChannelNotFound(channelID)
        if not channel.isJoined():
            channel.setJoined(True)
            g_messengerEvents.channels.onConnectStateChanged(channel)
            self.requestChannelMembers(channelID)
        else:
            channel.clearHistory()

    def __onEnterChat(self, chatAction):
        wrapper = ChatActionWrapper(**dict(chatAction))
        channel = self.channelsStorage.getChannel(entities.BWChannelLightEntity(wrapper.channel))
        if channel:
            channel.addMembers([entities.BWMemberEntity(wrapper.originator, nickName=wrapper.originatorNickName)])

    def __onSelfLeaveChat(self, chatAction):
        """
        Event handler.
        When current player exit from channel, remove page for this channel
        """
        LOG_DEBUG('onSelfLeaveChat:%s' % (dict(chatAction),))
        wrapper = ChatActionWrapper(**dict(chatAction))
        channel = self.channelsStorage.getChannel(entities.BWChannelLightEntity(wrapper.channel))
        if channel:
            channel.setJoined(False)
            g_messengerEvents.channels.onConnectStateChanged(channel)

    def __onLeaveChat(self, chatAction):
        wrapper = ChatActionWrapper(**dict(chatAction))
        channel = self.channelsStorage.getChannel(entities.BWChannelLightEntity(wrapper.channel))
        if channel:
            channel.removeMembers([wrapper.originator])

    def __onChannelDestroyed(self, chatAction):
        LOG_DEBUG('onChannelDestroyed : %s' % (dict(chatAction),))
        wrapper = ChatActionWrapper(**dict(chatAction))
        channel = self.channelsStorage.getChannel(entities.BWChannelLightEntity(wrapper.channel))
        if channel and self.channelsStorage.removeChannel(channel):
            g_messengerEvents.channels.onChannelDestroyed(channel)

    def __onRequestChannelMembers(self, chatAction):
        wrapper = ChatActionWrapper(**dict(chatAction))
        channel = self.channelsStorage.getChannel(entities.BWChannelLightEntity(wrapper.channel))
        if channel is not None:
            channel.addMembers(map(lambda memberData: self.__makeMemberFromDict(dict(memberData)), wrapper.data))
        return

    def __onReceiveMembersDelta(self, chatAction):
        wrapper = ChatActionWrapper(**dict(chatAction))
        channel = self.channelsStorage.getChannel(entities.BWChannelLightEntity(wrapper.channel))
        if channel is None:
            return
        else:
            added = []
            removed = []
            for dbID, data in wrapper.data:
                if data[0] == 1:
                    added.append(entities.BWMemberEntity(dbID, nickName=data[1], status=data[2]))
                elif data[0] == 0:
                    removed.append(dbID)

            if len(added):
                channel.addMembers(added)
            if len(removed):
                channel.removeMembers(removed)
            return

    def __onMemberStatusUpdate(self, chatAction):
        wrapper = ChatActionWrapper(**dict(chatAction))
        channel = self.channelsStorage.getChannel(entities.BWChannelLightEntity(wrapper.channel))
        if channel:
            member = channel.getMember(wrapper.originator)
            if member:
                member.setStatus(int(wrapper.data))

    def __onChannelInfoUpdated(self, chatAction):
        result = chatAction['data'] if chatAction.has_key('data') else {}
        received = entities.BWChannelEntity(result)
        channel = self.channelsStorage.getChannel(received)
        if channel:
            channel.update(other=received)
            g_messengerEvents.channels.onChannelInfoUpdated(channel)

    def __onChatChannelCreated(self, chatAction):
        result = chatAction['data'] if chatAction.has_key('data') else {}
        created = entities.BWChannelEntity(dict(result))
        channel = self.channelsStorage.getChannel(created)
        if channel is None:
            self.__channels[created.getID()] = created
            password = None
            if created.getName() in self.__creationInfo:
                password = self.__creationInfo.pop(created.getName())
            self.joinToChannel(created.getID(), password=password)
        return

    def __onChannelNotExists(self, _, chatAction):
        channelID = chatAction['channel']
        LOG_DEBUG('channelId : %s' % (channelID,))
        self.__onChannelDestroyed(chatAction)
        return True

    def __onCommandInCooldown(self, actionResponse, chatAction):
        data = chatAction.get('data', {'command': None,
         'cooldownPeriod': -1})
        result = False
        if data['command'] == 'findChatChannels':
            result = True
            self.onFindChannelsFailed(chatAction.get('requestID', -1), actionResponse, data)
        return result

    def __ms_onUserPreferencesUpdated(self):
        channels = self.channelsStorage.getChannelsByCriteria(find_criteria.BWAllChannelFindCriteria())
        for channel in channels:
            if channel.invalidateName():
                g_messengerEvents.channels.onChannelInfoUpdated(channel)

    def __makeMemberFromDict(self, memberData):
        member = None
        if 'id' in memberData:
            kwargs = {}
            if 'nickName' in memberData:
                kwargs['nickName'] = memberData['nickName']
            if 'status' in memberData:
                kwargs['status'] = memberData['status']
            member = entities.BWMemberEntity(memberData['id'], **kwargs)
        return member

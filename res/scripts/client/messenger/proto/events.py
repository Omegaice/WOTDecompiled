import Event

class _ChannelsSharedEvents(object):

    def __init__(self):
        super(_ChannelsSharedEvents, self).__init__()
        self.__eventManager = Event.EventManager()
        self.onChannelInited = Event.Event(self.__eventManager)
        self.onPlayerEnterChannelByAction = Event.Event(self.__eventManager)
        self.onChannelDestroyed = Event.Event(self.__eventManager)
        self.onConnectingToSecureChannel = Event.Event(self.__eventManager)
        self.onChannelInfoUpdated = Event.Event(self.__eventManager)
        self.onConnectStateChanged = Event.Event(self.__eventManager)
        self.onMessageReceived = Event.Event(self.__eventManager)
        self.onCommandReceived = Event.Event(self.__eventManager)

    def clear(self):
        self.__eventManager.clear()


class ChannelEvents(object):
    __slots__ = ('onConnectStateChanged', 'onChannelInfoUpdated', 'onMembersListChanged', 'onMemberStatusChanged', '__eventManager')

    def __init__(self):
        super(ChannelEvents, self).__init__()
        self.__eventManager = Event.EventManager()
        self.onConnectStateChanged = Event.Event(self.__eventManager)
        self.onChannelInfoUpdated = Event.Event(self.__eventManager)
        self.onMembersListChanged = Event.Event(self.__eventManager)
        self.onMemberStatusChanged = Event.Event(self.__eventManager)

    def clear(self):
        self.__eventManager.clear()


class MemberEvents(object):
    __slots__ = ('onMemberStatusChanged', '__eventManager')

    def __init__(self):
        super(MemberEvents, self).__init__()
        self.__eventManager = Event.EventManager()
        self.onMemberStatusChanged = Event.Event(self.__eventManager)

    def clear(self):
        self.__eventManager.clear()


class _UsersSharedEvents(object):

    def __init__(self):
        super(_UsersSharedEvents, self).__init__()
        self.__eventManager = Event.EventManager()
        self.onUsersRosterReceived = Event.Event()
        self.onUserRosterChanged = Event.Event(self.__eventManager)
        self.onUserRosterStatusUpdated = Event.Event(self.__eventManager)
        self.onClanMembersListChanged = Event.Event(self.__eventManager)
        self.onClanMembersStatusesChanged = Event.Event(self.__eventManager)

    def clear(self):
        self.__eventManager.clear()


class _ServiceChannelEvents(object):

    def __init__(self):
        super(_ServiceChannelEvents, self).__init__()
        self.__eventManager = Event.EventManager()
        self.onServerMessageReceived = Event.Event(self.__eventManager)
        self.onClientMessageReceived = Event.Event(self.__eventManager)

    def clear(self):
        self.__eventManager.clear()


class _MessengerEvents(object):
    __slots__ = ('__channels', '__users', '__serviceChannel', 'onServerErrorReceived')

    def __init__(self):
        super(_MessengerEvents, self).__init__()
        self.__channels = _ChannelsSharedEvents()
        self.__users = _UsersSharedEvents()
        self.__serviceChannel = _ServiceChannelEvents()
        self.onServerErrorReceived = Event.Event()

    @property
    def channels(self):
        return self.__channels

    @property
    def users(self):
        return self.__users

    @property
    def serviceChannel(self):
        return self.__serviceChannel

    def clear(self):
        self.__channels.clear()
        self.__users.clear()
        self.__serviceChannel.clear()
        self.onServerErrorReceived.clear()


g_messengerEvents = _MessengerEvents()

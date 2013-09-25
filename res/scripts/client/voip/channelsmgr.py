import BigWorld
from debug_utils import LOG_DEBUG, LOG_ERROR, verify
from wotdecorators import noexcept
import Event
import messages
import constants
import threading

class ChannelsMgr:
    STATE_NONE = 0
    STATE_INITIALIZING = 1
    STATE_INITIALIZED = 2
    STATE_LOGGING_IN = 3
    STATE_LOGGED_IN = 4
    STATE_LOGGING_OUT = 5
    STATE_JOINING_CHANNEL = 6
    STATE_JOINED_CHANNEL = 7
    STATE_LEAVING_CHANNEL = 8
    states = ('STATE_NONE', 'STATE_INITIALIZING', 'STATE_INITIALIZED', 'STATE_LOGGING_IN', 'STATE_LOGGED_IN', 'STATE_LOGGING_OUT', 'STATE_JOINING_CHANNEL', 'STATE_JOINED_CHANNEL', 'STATE_LEAVING_CHANNEL')
    loginName = property(lambda self: self.user[0])
    password = property(lambda self: self.user[1])

    def __init__(self):
        self.domain = ''
        self.user = ['', '']
        self.channel = ['', '']
        self.enabled = False
        self.loggedIn = False
        self.currentChannel = ''
        self.initialized = False
        self.state = self.STATE_NONE
        self.onCaptureDevicesUpdated = Event.Event()
        self.onParticipantAdded = Event.Event()
        self.onParticipantRemoved = Event.Event()
        self.onParticipantUpdated = Event.Event()
        self.onJoinedChannel = Event.Event()
        self.onLeftChannel = Event.Event()
        self.onInitialized = Event.Event()
        self.onLogined = Event.Event()
        self.onStateChanged = Event.Event()

    def _clearUser(self):
        self.user = ['', '']

    def _clearDesiredChannel(self):
        self.channel = ['', '']

    def isInDesiredChannel(self):
        return self.channel[0] == self.currentChannel

    def onConnected(self):
        pass

    def initialize(self, domain):
        verify(self.domain or not self.initialized)
        verify(self.state == self.STATE_NONE)
        self.domain = domain
        self._changeState()

    def destroy(self):
        BigWorld.VOIP.finalise()

    def login(self, name, password):
        self.user = [name, password]
        self._changeState()

    def logout(self):
        self._clearUser()
        self._clearDesiredChannel()
        self._changeState()

    def enterChannel(self, name, password):
        self.channel = [name, password]
        self._changeState()

    def leaveChannel(self):
        self._clearDesiredChannel()
        self._changeState()

    def enable(self, enabled):
        self.enabled = enabled
        if not self.enabled:
            self._clearUser()
        elif self.channel[0] != '':
            BigWorld.player().requestVOIPCredentials()
        self._changeState()

    def setState(self, newState):
        if newState == self.state:
            return
        LOG_DEBUG('__changeState %s on %s' % (self.states[self.state], self.states[newState]))
        self.state = newState
        self.onStateChanged(self.state, newState)

    def __resetToInitializedState(self, isNetworkFailure = False):
        self.setState(self.STATE_INITIALIZED)
        if self.currentChannel != '':
            self.onLeftChannel({})
            self.currentChannel = ''
        self._clearUser()
        self._changeState()
        if isNetworkFailure and BigWorld.player() is not None:
            BigWorld.player().requestVOIPCredentials()
        return

    def _changeState(self, **args):
        if self.state in (self.STATE_LOGGED_IN,
         self.STATE_JOINING_CHANNEL,
         self.STATE_JOINED_CHANNEL,
         self.STATE_LEAVING_CHANNEL,
         self.STATE_LOGGING_OUT) and not self.loggedIn:
            self.__resetToInitializedState(self.state != self.STATE_LOGGING_OUT)
        elif self.state == self.STATE_NONE and not self.initialized and self.domain != '':
            self.setState(self.STATE_INITIALIZING)
            self._initialize()
        elif self.state == self.STATE_INITIALIZING and self.initialized:
            self.__resetToInitializedState()
        elif self.state == self.STATE_INITIALIZED and self.user[0] != '':
            self.setState(self.STATE_LOGGING_IN)
            self._loginUser()
        elif self.state == self.STATE_LOGGING_IN:
            if self.loggedIn:
                self.setState(self.STATE_LOGGED_IN)
                if self.channel[0] != '':
                    self._changeState()
            elif args.get('wrongCredentials', False):
                self.setState(self.STATE_INITIALIZED)
        elif self.state == self.STATE_LOGGED_IN:
            if self.user[0] == '':
                self.setState(self.STATE_LOGGING_OUT)
                BigWorld.VOIP.logout()
            elif self.channel[0] != '' and self.enabled:
                self.setState(self.STATE_JOINING_CHANNEL)
                self._joinChannel(self.channel[0], self.channel[0])
        elif self.state == self.STATE_JOINING_CHANNEL:
            if self.currentChannel:
                self.setState(self.STATE_JOINED_CHANNEL)
                if not self.isInDesiredChannel():
                    self.setState(self.STATE_LEAVING_CHANNEL)
                    self.__sendLeaveChannelCommand(self.currentChannel)
                self._changeState()
            elif not self.channel[0]:
                self.setState(self.STATE_LOGGED_IN)
                self._changeState()
        elif self.state == self.STATE_JOINED_CHANNEL:
            if not self.isInDesiredChannel() or not self.enabled or not self.currentChannel:
                self.setState(self.STATE_LEAVING_CHANNEL)
                self.__sendLeaveChannelCommand(self.currentChannel)
        elif self.state == self.STATE_LEAVING_CHANNEL:
            if not self.currentChannel:
                self.setState(self.STATE_LOGGED_IN)
                self._changeState()
        else:
            LOG_DEBUG('__changeState  state not changed - ', self.state)

    def _initialize(self):
        pass

    def _loginUser(self):
        pass

    def _joinChannel(self, channelURI, password):
        BigWorld.VOIP.command({'command': 'hangup'})
        BigWorld.VOIP.joinChannel(channelURI, password, {})
        self.debug("Joining channel '%s'" % channelURI)
        self._changeState()

    def __sendLeaveChannelCommand(self, channel):
        if channel:
            BigWorld.VOIP.leaveChannel(channel)
        self.debug("Leaving channel '%s'" % channel)
        self._changeState()

    def debug(self, text):
        prefix = 'VRH: '
        LOG_DEBUG('\n%s%s\n' % (prefix, text))

    @noexcept
    def __call__(self, message, data = {}):
        pass

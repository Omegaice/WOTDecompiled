# Embedded file name: scripts/client/VOIP/Vivox/VivoxHandler.py
import BigWorld
from VOIP.ChannelsMgr import ChannelsMgr
from VOIP import messages
from VOIP import constants
import threading
from debug_utils import LOG_DEBUG
from wotdecorators import noexcept
from debug_utils import verify

class VivoxHandler(ChannelsMgr):

    def _initialize(self):
        vinit = {'vivox_server': 'http://%s/api2' % self.domain,
         'minimum_port': '0',
         'maximum_port': '0',
         'log_prefix': 'vivox',
         'log_suffix': '.txt',
         'log_folder': '.',
         'log_level': '0'}
        threading.Thread(target=BigWorld.VOIP.initialise, name='initialization', args=[vinit]).start()
        self.__loginAttemptsRemained = 0

    def onConnected(self):
        self.__loginAttemptsRemained = 2

    def _loginUser(self):
        cmd = {}
        cmd[constants.KEY_PARTICIPANT_PROPERTY_FREQUENCY] = '100'
        BigWorld.VOIP.login(self.user[0], self.user[1], cmd)
        LOG_DEBUG('Login Request:', self.user)

    def __reloginUser(self):
        self.__loginAttemptsRemained -= 1
        LOG_DEBUG('Requesting user reregistration, attempts remained: %d' % self.__loginAttemptsRemained)
        if self.enabled:
            BigWorld.player().requestVOIPCredentials(1)

    @noexcept
    def __call__(self, message, data = {}):
        if message not in [messages.vxParticipantUpdated]:
            msg = '::Message: %d [%s], Data: %s' % (message, messages.MESSAGE_IDS[message], data)
            self.debug(msg)
        if message == messages.vxConnectorCreated:
            if data[constants.KEY_CONNECTOR_HANDLE] != '':
                self.initialized = True
                self.onInitialized(data)
                self._changeState()
        elif message == messages.vxSessionGroupAdded:
            self.loggedIn = True
            self._changeState()
        elif message == messages.vxSessionGroupRemoved:
            pass
        elif message == messages.vxMediaStreamUpdated:
            state = int(data[constants.KEY_STATE])
            self.debug('CHANNEL DATA: %s' % data)
            if state == constants.SESSION_MEDIA_CONNECTED:
                self.currentChannel = data[constants.KEY_CHANNEL_URI]
                self.onJoinedChannel(data)
                self._changeState()
            elif state == constants.SESSION_MEDIA_DISCONNECTED:
                self.__handleSessionMediaDisconnect(data)
        elif message == messages.vxParticipantRemoved:
            self.onParticipantRemoved(data)
        elif message == messages.vxParticipantAdded:
            self.onParticipantAdded(data)
        elif message == messages.vxParticipantUpdated:
            self.onParticipantUpdated(data)
        elif message == messages.vxAuxGetCaptureDevices:
            self.onCaptureDevicesUpdated(data)
        elif message == messages.vxSessionAdded:
            pass
        elif message == messages.vxSessionRemoved:
            pass
        elif message == messages.vxAccountLogin:
            if data[constants.KEY_STATUS_CODE] == '20200':
                if self.__loginAttemptsRemained > 0:
                    self.__reloginUser()
                self.loggedIn = False
                self._clearUser()
                self._changeState(wrongCredentials=True)
            elif data[constants.KEY_RETURN_CODE] == '0':
                self.onLogined()
            else:
                self.loggedIn = False
                self._clearUser()
                self._changeState(wrongCredentials=True)
        elif message == messages.vxAccountLogout:
            pass
        elif message == messages.vxAccountLoginStateChange:
            if data[constants.KEY_STATE] == '0' and data[constants.KEY_STATUS_CODE] != '20200':
                self.debug('vxAccountLoginStateChange, logout: %s' % data)
                self.loggedIn = False
                self._changeState()
        elif message == messages.vxAuxGetVADProperties:
            self.debug('vxAuxGetVADProperties: %s', str(data))

    def __handleSessionMediaDisconnect(self, data):
        self.onLeftChannel(data)
        statusCode = int(data[constants.KEY_STATUS_CODE])
        if statusCode > 400:
            self.debug('vxMediaStreamUpdated, SessionMedia disconnected, code: %d, message: %s' % (statusCode, data[constants.KEY_STATUS_STRING]))
            if not self.currentChannel or self.isInDesiredChannel():
                self._clearDesiredChannel()
        self.currentChannel = ''
        self._changeState()
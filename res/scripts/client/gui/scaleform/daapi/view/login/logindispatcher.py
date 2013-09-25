import json
from ConnectionManager import connectionManager
from Event import Event
from PlayerEvents import g_playerEvents
from gui.Scaleform.Waiting import Waiting
from account_helpers import pwd_token
from account_helpers.SteamAccount import g_steamAccount
from debug_utils import LOG_DEBUG, LOG_CURRENT_EXCEPTION, LOG_ERROR
from external_strings_utils import isAccountLoginValid, isPasswordValid, _LOGIN_NAME_MIN_LENGTH, isAccountNameValid, _ACCOUNT_NAME_MIN_LENGTH_REG
from gui.Scaleform.framework.entities.DisposableEntity import DisposableEntity
from gui import SystemMessages, GUI_SETTINGS, makeHtmlString
from gui.doc_loaders.LoginDataLoader import LoginDataLoader
from gui.Scaleform.locale.BAN_REASON import BAN_REASON
from gui.Scaleform.locale.MENU import MENU
from gui.Scaleform.locale.WAITING import WAITING
from gui.Scaleform.locale.SYSTEM_MESSAGES import SYSTEM_MESSAGES
from gui import DialogsInterface
from gui.prb_control.dispatcher import g_prbLoader
from helpers import i18n
from helpers.i18n import makeString
from helpers.links import openMigrationWebsite
from helpers.time_utils import makeLocalServerTime
from predefined_hosts import g_preDefinedHosts, AUTO_LOGIN_QUERY_URL, AUTO_LOGIN_QUERY_TIMEOUT
import BigWorld
import ResMgr
import constants
import Settings
__author__ = 'd_trofimov'

class LoginDispatcher(DisposableEntity):
    __autoLoginTimerID = None
    __lg_Timeout = 0
    __lg_maxTimeout = 20
    __lg_increment = 5
    IS_FIRST_RUN = True
    __isAutoLoginTimerSet = False
    __isAutoLoginShow = False
    __APPLICATION_CLOSE_DELAY_DEFAULT = 15
    EVENTS = ('onSetOptions', 'onAfterAutoLoginTimerClearing', 'onCancelQueue', 'onHandleUpdateClientSoftwareNeeded', 'onSetStatus', 'onHandleLoginRejectedRateLimited', 'onHandleActivating', 'onShowCreateAnAccountDialog', 'onHandleAutoRegisterInvalidPass', 'onHandleAutoRegisterActivating', 'onHandleAutoLoginQueryFailed', 'onHandleAutoRegisterJSONParsingFailed', 'onDoAutoLogin', 'onHandleKickWhileLogin', 'onAccountNameIsInvalid', 'onNicknameTooSmall', 'onHandleQueue', 'onConfigLoaded', 'onHandleInvalidPasswordWithToken', 'onLoginAppFailed')
    __logOnFailedHandlers = {'LOGIN_REJECTED_BAN': 'handleLoginRejectedBan',
     'LOGIN_CUSTOM_DEFINED_ERROR': 'handleLoginRejectedBan',
     'LOGIN_REJECTED_RATE_LIMITED': 'handleLoginRejectedRateLimited',
     'LOGIN_REJECTED_USERS_LIMIT': 'handleLoginRejectedUsersLimited',
     'LOGIN_REJECTED_LOGINS_NOT_ALLOWED': 'handleLoginAppFailed',
     'LOGIN_REJECTED_BASEAPP_TIMEOUT': 'handleLoginAppFailed',
     'CONNECTION_FAILED': 'handleLoginAppFailed',
     'DNS_LOOKUP_FAILED': 'handleLoginAppFailed',
     'LOGIN_REJECTED_NOT_REGISTERED': 'handleNotRegistered',
     'LOGIN_REJECTED_ACTIVATING': 'handleActivating',
     'LOGIN_REJECTED_INVALID_PASSWORD': 'handleInvalidPassword'}
    __logOnFailedDefaultHandler = 'handleLogOnFailed'
    __logAutoRegisterHandlers = {'LOGIN_REJECTED_INVALID_PASSWORD': 'handleAutoRegisterInvalidPass',
     'LOGIN_REJECTED_UNABLE_TO_PARSE_JSON': 'handleAutoRegisterJSONParsingFailed',
     'LOGIN_REJECTED_ACTIVATING': 'handleAutoRegisterActivating'}
    __logOnSuccess = {'LOGGED_ON': 'handleLogOnSuccess'}
    onSetOptions = Event()
    onAfterAutoLoginTimerClearing = Event()
    onCancelQueue = Event()
    onHandleUpdateClientSoftwareNeeded = Event()
    onSetStatus = Event()
    onHandleLoginRejectedRateLimited = Event()
    onHandleActivating = Event()
    onShowCreateAnAccountDialog = Event()
    onHandleAutoRegisterInvalidPass = Event()
    onHandleAutoRegisterActivating = Event()
    onHandleAutoLoginQueryFailed = Event()
    onHandleAutoRegisterJSONParsingFailed = Event()
    onDoAutoLogin = Event()
    onHandleKickWhileLogin = Event()
    onAccountNameIsInvalid = Event()
    onNicknameTooSmall = Event()
    onHandleQueue = Event()
    onConfigLoaded = Event()
    onHandleInvalidPasswordWithToken = Event()
    onLoginAppFailed = Event()
    ALL_VALID = 0
    LOGIN_INVALID = 1
    PWD_INVALID = 2
    SERVER_INVALID = 4
    LOGIN_PWD_INVALID = LOGIN_INVALID | PWD_INVALID

    def __init__(self):
        super(LoginDispatcher, self).__init__()
        DisposableEntity.__init__(self)
        self.__kickedFromServer = False
        self.__closeCallbackId = None
        self.__accNotReady = False
        self.__onLoggingTryingEndHdlr = None
        self.__securityMsgType = None
        return

    def _populate(self):
        super(LoginDispatcher, self)._populate()
        self.__loginDataLoader = LoginDataLoader()
        self.__loginDataLoader.onConfigLoaded += self.onConfigLoaded
        self.__loginDataLoader.loadUserConfig()
        connectionManager.connectionStatusCallbacks += self.__handleConnectionStatus
        connectionManager.searchServersCallbacks += self.__serversFind
        connectionManager.onConnected += self.__onConnected
        connectionManager.onDisconnected -= LoginDispatcher.__onDisconnected
        connectionManager.startSearchServers()
        g_preDefinedHosts.readScriptConfig(Settings.g_instance.scriptConfig)
        g_playerEvents.onLoginQueueNumberReceived += self.handleQueue
        g_playerEvents.onAccountBecomePlayer += self.__pe_onAccountBecomePlayer
        g_playerEvents.onKickWhileLoginReceived += self.handleKickWhileLogin
        if self.__loginDataLoader.host == '' and len(g_preDefinedHosts.shortList()):
            self.__loginDataLoader.host = g_preDefinedHosts.shortList()[0][0]
        self.onSetOptions(g_preDefinedHosts.shortList(), self.__loginDataLoader.host)

    def _dispose(self):
        super(LoginDispatcher, self)._dispose()
        connectionManager.connectionStatusCallbacks -= self.__handleConnectionStatus
        connectionManager.searchServersCallbacks -= self.__serversFind
        connectionManager.onConnected -= self.__onConnected
        connectionManager.onDisconnected += LoginDispatcher.__onDisconnected
        connectionManager.stopSearchServers()
        g_playerEvents.onLoginQueueNumberReceived -= self.handleQueue
        g_playerEvents.onAccountBecomePlayer -= self.__pe_onAccountBecomePlayer
        g_playerEvents.onKickWhileLoginReceived -= self.handleKickWhileLogin
        self.__loginDataLoader.onConfigLoaded -= self.onConfigLoaded
        self.__loginDataLoader = None
        self.__onLoggingTryingEndHdlr = None
        return

    def onLogin(self, user, password, host, hdlr):
        self.__onLoggingTryingEndHdlr = hdlr
        self.__kickedFromServer = False
        if self.__closeCallbackId:
            BigWorld.cancelCallback(self.__closeCallbackId)
            self.__closeCallbackId = None
        if g_steamAccount.isValid:
            user, password = g_steamAccount.getCredentials()
        else:
            user = user.lower().strip()
            if len(user) < _LOGIN_NAME_MIN_LENGTH:
                self.onSetStatus(i18n.makeString(MENU.LOGIN_STATUS_INVALID_LOGIN_LENGTH) % {'count': _LOGIN_NAME_MIN_LENGTH}, self.LOGIN_INVALID)
                return
            if not isAccountLoginValid(user) and not constants.IS_DEVELOPMENT:
                self.onSetStatus(i18n.makeString(MENU.LOGIN_STATUS_INVALID_LOGIN), self.LOGIN_INVALID)
                return
            password = password.strip()
            if not isPasswordValid(password) and not constants.IS_DEVELOPMENT and not len(self.__loginDataLoader.token2):
                self.onSetStatus(i18n.makeString(MENU.LOGIN_STATUS_INVALID_PASSWORD), self.LOGIN_PWD_INVALID)
                return
        Waiting.show('login')
        self.__loginDataLoader.host = host
        self.__loginDataLoader.user = user
        self.__loginDataLoader.passLength = len(password)
        if constants.IS_VIETNAM:
            self.__pass = password
        self.__loginDataLoader.saveUserConfig(user, self.__loginDataLoader.host)
        password = pwd_token.generate(password)
        if len(self.__loginDataLoader.token2):
            password = ''
        if AUTO_LOGIN_QUERY_URL == host:
            g_preDefinedHosts.autoLoginQuery(lambda host: connectionManager.connect(host.url, user, password, host.keyPath, nickName=None, token2=self.__loginDataLoader.token2))
            return
        else:
            host = g_preDefinedHosts.byUrl(host)
            urls = host.urlIterator
            if urls is not None:
                if urls.end():
                    urls.cursor = 0
                host = urls.next()
                LOG_DEBUG('Gets next LoginApp url:', host)
            connectionManager.connect(host.url, user, password, host.keyPath, nickName=None, token2=self.__loginDataLoader.token2)
            return

    def onExitFromAutoLogin(self):
        self.__clearAutoLoginTimer(clearInFlash=False)
        self.__resetLgTimeout()
        g_preDefinedHosts.resetQueryResult()

    def onTryCreateAnAccount(self, nickname):
        if len(nickname) < _ACCOUNT_NAME_MIN_LENGTH_REG:
            self.onNicknameTooSmall()
            return
        elif not isAccountNameValid(nickname):
            self.onAccountNameIsInvalid()
            return
        else:
            host = g_preDefinedHosts.byUrl(self.__loginDataLoader.host)
            password = pwd_token.generate(self.__pass)
            urls = host.urlIterator
            if urls is not None:
                if urls.end():
                    urls.cursor = 0
                host = urls.next()
                LOG_DEBUG('Gets next LoginApp url:', host)
            LOG_DEBUG('Try create an account: url=%s; login=%s; password=%s; nickName=%s' % (host.url,
             self.__loginDataLoader.user,
             password,
             nickname))
            connectionManager.connect(host.url, self.__loginDataLoader.user, password, host.keyPath, nickName=nickname, token2='')
            return

    def resetToken(self):
        self.__loginDataLoader.passLength = 0
        self.__loginDataLoader.token2 = ''

    def isToken(self):
        return len(self.__loginDataLoader.token2) > 0

    def steamLogin(self):
        if LoginDispatcher.IS_FIRST_RUN and g_steamAccount.isValid:
            LoginDispatcher.IS_FIRST_RUN = False
            self.__loginDataLoader.loadUserConfig()
            host = self.__loginDataLoader.host
            if not g_preDefinedHosts.predefined(host):
                host = g_preDefinedHosts.first().url
            self.onLogin('', '', host)

    def setRememberPwd(self, remember):
        self.__loginDataLoader.rememberPwd = bool(remember)

    def __handleConnectionStatus(self, stage, status, serverMsg, isAutoRegister):
        if self.__onLoggingTryingEndHdlr:
            self.__onLoggingTryingEndHdlr()
        STATUS_LOGGED_ON = 'LOGGED_ON'
        LOG_DEBUG('__handleConnectionStatus %s %s %s' % (stage, status, isAutoRegister))
        if stage == 1:
            if status == STATUS_LOGGED_ON:
                handlerFunc = self.__logOnSuccess[status]
            elif isAutoRegister:
                handlerFunc = self.__logAutoRegisterHandlers.get(status, self.__logOnFailedDefaultHandler)
                if status == 'DNS_LOOKUP_FAILED':
                    self.onLoginAppFailed(status, serverMsg)
            else:
                handlerFunc = self.__logOnFailedHandlers.get(status, self.__logOnFailedDefaultHandler)
                if status != 'LOGIN_REJECTED_LOGIN_QUEUE':
                    self.__clearAutoLoginTimer()
                if status != 'LOGIN_REJECTED_RATE_LIMITED':
                    self.__resetLgTimeout()
                self.onCancelQueue(False, False)
                g_preDefinedHosts.clearPeripheryTL()
            try:
                getattr(self, handlerFunc)(status, serverMsg)
            except:
                LOG_ERROR('Handle logon status error: status = %r, message = %r' % (status, serverMsg))
                LOG_CURRENT_EXCEPTION()
                Waiting.hide('login')

            if connectionManager.isUpdateClientSoftwareNeeded():
                self.onHandleUpdateClientSoftwareNeeded()
            elif status != STATUS_LOGGED_ON:
                connectionManager.disconnect()
        elif stage == 6:
            if not self.__kickedFromServer:
                self.onCancelQueue(False, False)
            msg = MENU.LOGIN_STATUS_DISCONNECTED
            if self.__accNotReady:
                msg = MENU.LOGIN_STATUS_ACCOUNTNOTREADY
                self.__accNotReady = False
            self.onSetStatus(i18n.convert(i18n.makeString(msg)), self.ALL_VALID)
            connectionManager.disconnect()

    def handleLogOnSuccess(self, status, message):
        try:
            LOG_DEBUG('handleLogOnSuccess', message)
            if not len(message):
                return
            msg_dict = json.loads(message)
            if not isinstance(msg_dict, dict):
                raise Exception, ''
            else:
                self.__securityMsgType = msg_dict.get('security_msg')
                self.showSecurityMessage()
        except Exception:
            self.handleLoginCustomDefinedError(status, message)
            LOG_CURRENT_EXCEPTION()
            return

        token2 = str(msg_dict.get('token2', ''))
        g_prbLoader.getInvitesManager().setCredentials(self.__loginDataLoader.user, token2)
        self.__loginDataLoader.saveUserToken(self.__loginDataLoader.passLength, token2)

    def showSecurityMessage(self):
        if self.__securityMsgType is not None:
            securityLink = ''
            if 'securitySettingsURL' in GUI_SETTINGS and len(GUI_SETTINGS.securitySettingsURL):
                linkText = makeString(SYSTEM_MESSAGES.SECURITYMESSAGE_CHANGE_SETINGS)
                securityLink = makeHtmlString('html_templates:lobby/system_messages', 'link', {'text': linkText,
                 'linkType': 'securityLink'})
            SystemMessages.pushI18nMessage('#system_messages:securityMessage/%s' % self.__securityMsgType, type=SystemMessages.SM_TYPE.Warning, link=securityLink)
            self.__securityMsgType = None
        return

    def __onConnected(self):
        Waiting.hide('login')
        g_preDefinedHosts.resetQueryResult()
        self.__loginQueue = False
        LOG_DEBUG('onConnected')

        def iCallback():
            BigWorld.disconnect()
            BigWorld.clearEntitiesAndSpaces()
            Waiting.close()

        Waiting.show('enter', interruptCallback=iCallback)

    @staticmethod
    def __onDisconnected():
        DialogsInterface.showDisconnect()

    def __serversFind(self, servers = None):
        list = g_preDefinedHosts.shortList()
        if servers is not None:
            for name, key in servers:
                if not g_preDefinedHosts.predefined(key):
                    list.append((key, name))

        self.onSetOptions(list, self.__loginDataLoader.host)
        return

    def __getApplicationCloseDelay(self):
        prefs = Settings.g_instance.userPrefs
        if prefs is None:
            delay = LoginDispatcher.__APPLICATION_CLOSE_DELAY_DEFAULT
        else:
            if not prefs.has_key(Settings.APPLICATION_CLOSE_DELAY):
                prefs.writeInt(Settings.APPLICATION_CLOSE_DELAY, LoginDispatcher.__APPLICATION_CLOSE_DELAY_DEFAULT)
            delay = prefs.readInt(Settings.APPLICATION_CLOSE_DELAY)
        return delay

    def handleLoginRejectedBan(self, status, message):
        try:
            LOG_DEBUG('handleLoginRejectedBan', message)
            msg_dict = json.loads(message)
            if not isinstance(msg_dict, dict):
                self.handleLoginCustomDefinedError(status, message)
                return
            self.__loginDataLoader.token2 = msg_dict.get('token2', '')
            self.__loginDataLoader.saveUserToken(self.__loginDataLoader.passLength, self.__loginDataLoader.token2)
            json_dict = msg_dict.get('bans')
            msg_dict = json.loads(json_dict)
        except Exception:
            LOG_CURRENT_EXCEPTION()
            self.handleLoginCustomDefinedError(status, message)
            return

        expiryTime = 0
        reason = ''
        if isinstance(msg_dict, dict):
            expiryTime = int(msg_dict.get('expiryTime', 0))
            reason = msg_dict.get('reason', '').encode('utf-8')
        if reason == BAN_REASON.CHINA_MIGRATION:
            self.__handleMigrationNeeded()
        if reason.startswith('#'):
            reason = i18n.makeString(reason)
        if expiryTime > 0:
            expiryTime = makeLocalServerTime(expiryTime)
            expiryTime = BigWorld.wg_getLongDateFormat(expiryTime) + ' ' + BigWorld.wg_getLongTimeFormat(expiryTime)
            errorMessage = i18n.makeString(MENU.LOGIN_STATUS_LOGIN_REJECTED_BAN, time=expiryTime, reason=reason)
        else:
            errorMessage = i18n.makeString(MENU.LOGIN_STATUS_LOGIN_REJECTED_BAN_UNLIMITED, reason=reason)
        self.onSetStatus(errorMessage, self.ALL_VALID)

    def handleLoginRejectedRateLimited(self, status, message):
        errorMessage = i18n.makeString(MENU.LOGIN_STATUS_LOGIN_REJECTED_RATE_LIMITED)
        self.onSetStatus(errorMessage, self.ALL_VALID)
        urls = g_preDefinedHosts.urlIterator(self.__loginDataLoader.host)
        if urls is not None and urls.end():
            urls.cursor = 0
        message = i18n.makeString(WAITING.MESSAGE_AUTOLOGIN, connectionManager.serverUserName)
        self.onHandleLoginRejectedRateLimited(message)
        self.__setAutoLoginTimer(self.__getLgNextTimeout())
        return

    def handleLoginRejectedUsersLimited(self, status, message):
        errorMessage = i18n.makeString(MENU.LOGIN_STATUS_LOGIN_REJECTED_USERS_LIMIT)
        self.onSetStatus(errorMessage, self.ALL_VALID)

    def handleLoginAppFailed(self, status, message):
        self.onLoginAppFailed(status, message)
        if self.handleAutoLoginQueryFailed(status):
            return
        if not self.__loginToNextLoginApp():
            self.handleLogOnFailed(status, message)

    def handleNotRegistered(self, status, message):
        if constants.IS_VIETNAM:
            self.onShowCreateAnAccountDialog()
        Waiting.close()

    def handleLoginCustomDefinedError(self, _, message):
        errorMessage = i18n.makeString(MENU.LOGIN_STATUS_LOGIN_CUSTOM_DEFINED_ERROR, message)
        self.onSetStatus(errorMessage, self.ALL_VALID)

    def handleAutoRegisterInvalidPass(self, status, message):
        self.onHandleAutoRegisterInvalidPass()
        Waiting.close()

    def handleAutoRegisterJSONParsingFailed(self, status, message):
        self.onHandleAutoRegisterJSONParsingFailed()
        Waiting.close()

    def handleActivating(self, status, message):
        message = i18n.makeString(WAITING.MESSAGE_AUTO_LOGIN_ACTIVATING)
        self.onHandleActivating(message)
        self.__setAutoLoginTimer(self.__getLgNextTimeout())

    def handleAutoRegisterActivating(self, status, message):
        self.onHandleAutoRegisterActivating()
        self.handleActivating(status, message)

    def __handleMigrationNeeded(self):
        if not constants.IS_DEVELOPMENT:
            self.__closeCallbackId = BigWorld.callback(self.__getApplicationCloseDelay(), BigWorld.quit)
            try:
                openMigrationWebsite(self.__loginDataLoader.user)
            except Exception:
                LOG_CURRENT_EXCEPTION()

    def handleAutoLoginQueryFailed(self, status):
        result = False
        if AUTO_LOGIN_QUERY_URL == self.__loginDataLoader.host:
            result = True
            message = i18n.makeString(WAITING.MESSAGE_AUTO_LOGIN_QUERY_FAILED, server=connectionManager.serverUserName, reason=i18n.makeString(MENU.login_status(status)))
            self.onHandleAutoLoginQueryFailed(message)
        self.__setAutoLoginTimer(AUTO_LOGIN_QUERY_TIMEOUT)
        return result

    def __loginToNextLoginApp(self):
        urls = g_preDefinedHosts.urlIterator(self.__loginDataLoader.host)
        result = False
        if urls is not None:
            result = not urls.end()
            if result:
                Waiting.hide('login')
                self.__setAutoLoginTimer(0)
            else:
                urls.cursor = 0
        return result

    def handleKickWhileLogin(self, peripheryID):
        if peripheryID == -1:
            self.__accNotReady = True
            return
        else:
            g_preDefinedHosts.savePeripheryTL(peripheryID)
            self.__kickedFromServer = True
            messageType = 'another_periphery' if peripheryID else 'checkout_error'
            errorMessage = i18n.makeString(SYSTEM_MESSAGES.all(messageType))
            self.onSetStatus(errorMessage, self.ALL_VALID)
            urls = g_preDefinedHosts.urlIterator(self.__loginDataLoader.host)
            if urls is not None and urls.end():
                urls.cursor = 0
            message = i18n.makeString(WAITING.message(messageType), connectionManager.serverUserName)
            self.onHandleKickWhileLogin(messageType, message)
            self.__setAutoLoginTimer(self.__getLgNextTimeout())
            return

    def handleQueue(self, queueNumber):
        if not self.__loginQueue:
            Waiting.hide('enter')
            self.__loginQueue = True
        message = i18n.makeString(WAITING.MESSAGE_QUEUE, connectionManager.serverUserName, BigWorld.wg_getIntegralFormat(queueNumber))
        self.onHandleQueue(message)

    def handleInvalidPassword(self, status, message):
        errorMessage = i18n.makeString(MENU.login_status(status))
        errCode = self.LOGIN_PWD_INVALID
        if len(self.__loginDataLoader.token2):
            self.resetToken()
            self.onHandleInvalidPasswordWithToken(self.__loginDataLoader.user, self.__loginDataLoader.rememberPwd)
            errorMessage = i18n.makeString(MENU.LOGIN_STATUS_SESSION_END)
            errCode = self.ALL_VALID
        self.onSetStatus(errorMessage, errCode)

    def handleLogOnFailed(self, status, _):
        self.onSetStatus(i18n.makeString(MENU.login_status(status)), self.ALL_VALID)

    def __pe_onAccountBecomePlayer(self):
        self.onCancelQueue(True, True)

    def __clearAutoLoginTimer(self, clearInFlash = True):
        if self.__isAutoLoginTimerSet:
            LOG_DEBUG('__clearAutoLoginTimer')
            if self.__autoLoginTimerID is not None:
                BigWorld.cancelCallback(self.__autoLoginTimerID)
                self.__autoLoginTimerID = None
            self.__isAutoLoginTimerSet = False
        if self.__isAutoLoginShow:
            self.onAfterAutoLoginTimerClearing(self.__loginDataLoader.host, clearInFlash)
            if clearInFlash:
                self.__isAutoLoginShow = False
        return

    def __resetLgTimeout(self):
        self.__lg_Timeout = 0

    def __getLgNextTimeout(self):
        self.__lg_Timeout = min(self.__lg_maxTimeout, self.__lg_Timeout + self.__lg_increment)
        return self.__lg_Timeout

    def __setAutoLoginTimer(self, time):
        if self.__isAutoLoginTimerSet:
            return
        self.__isAutoLoginTimerSet = True
        LOG_DEBUG('__setAutoLoginTimer', time)
        self.__isAutoLoginShow = True
        if time > 0:
            self.__autoLoginTimerID = BigWorld.callback(time, self.__doAutologin)
        else:
            self.__doAutologin()

    def __doAutologin(self):
        self.__isAutoLoginTimerSet = False
        self.__autoLoginTimerID = None
        self.onDoAutoLogin()
        return

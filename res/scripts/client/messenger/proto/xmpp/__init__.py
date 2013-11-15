# 2013.11.15 11:27:16 EST
# Embedded file name: scripts/client/messenger/proto/xmpp/__init__.py
import BigWorld
import Account
from collections import namedtuple
import random
import cPickle
from chat_shared import USERS_ROSTER_FRIEND
from debug_utils import LOG_DEBUG, LOG_ERROR
from ids_generators import SequenceIDGenerator
from messenger.m_constants import USER_ROSTER_ACTION, MESSENGER_SCOPE
from messenger.proto.events import g_messengerEvents
from messenger.proto.interfaces import IProtoPlugin
from messenger.proto.xmpp.RosterItem import RosterItem
from messenger.storage import storage_getter
__author__ = 'd_dichkovsky'
XmppConnectionModel = namedtuple('XmppConnectionModel', 'host port resourceName isConnected connection token')

class XmppPlugin(IProtoPlugin):
    DISCONNECT_BY_REQUEST = 0
    DISCONNECT_AUTHENTICATION = 1
    DISCONNECT_OTHER_ERROR = 2
    USE_MOCK_DATA = False
    ALLOWED_ROSTER_ACTIONS = [USER_ROSTER_ACTION.AddToFriend,
     USER_ROSTER_ACTION.AddToIgnored,
     USER_ROSTER_ACTION.RemoveFromFriend,
     USER_ROSTER_ACTION.RemoveFromIgnored]

    def __init__(self):
        self.__client = BigWorld.XmppClient()
        self.__currentUser = None
        self.__xmppRoster = None
        self.__usersMgr = None
        self.__model = None
        self.__bwRoster = None
        self.__reconnectCount = 0
        self.__reconnectCallbackId = None
        self.__bwConnected = False
        self.__isEnabled = False
        self.__idsGen = SequenceIDGenerator()
        self.__pendingBattleMode = None
        self.__databaseID = None
        return

    @storage_getter('users')
    def usersStorage(self):
        return None

    @property
    def isConnected(self):
        """
        Shows current XMPP connection status
        """
        if self.__model is not None:
            return self.__model.isConnected
        else:
            return False

    def logState(self):
        if self.__isEnabled:
            if self.__model is not None and self.__model.isConnected:
                itemsStrList = ['XMPP:logState - XMPP is connected. Logging XMPP roster state:']
                itemsStrList.append('Curr.User JID: {0}  Status: {1}'.format(self.__currentUser.bareJid, self.__currentUser.getPresenceStr(self.__currentUser.presence)))
                for jid, item in self.__xmppRoster.items():
                    itemsStrList.append('Contact   JID: {0}  Status: {1}  Name: {2}'.format(jid, item.getPresenceStr(item.presence), item.name))

                LOG_DEBUG('\n'.join(itemsStrList))
            else:
                LOG_DEBUG('XMPP:logState - XMPP is not connected yet. Try to run your command later')
        else:
            LOG_DEBUG('XMPP:logState - You are not logged in or connection to XMPP is disabled by server settings')
        return

    def connect(self, scope = None):
        if scope is not None:
            self._setBattleMode(scope)
        if self.isConnected:
            return
        else:
            self.__bwConnected = True
            self._cancelReconnectCallback()
            settings = self._getServerSettings()
            if settings.get('xmpp_enabled', False):
                self.__isEnabled = bool(int(settings.get('jdCutouts', 0)))
                if self.__isEnabled:
                    self._subscribeToActions()
                    LOG_DEBUG('XMPP:connect - XMPP functionality is enabled. Starting connection to XMPP server')
                    if self.__model is None:
                        self.__model = XmppConnectionModel(settings.get('xmpp_host'), settings.get('xmpp_port'), settings.get('xmpp_resource'), False, None, None)
                    else:
                        self.__model = self.__model._replace(host=settings.get('xmpp_host'), port=settings.get('xmpp_port'), resourceName=settings.get('xmpp_resource'), isConnected=False)
                    if self.__model.host is None:
                        raise Exception, 'XMPP: server xmpp_host is not defined'
                    connections = settings.get('xmpp_connections', [])
                    if len(connections) > 0:
                        self.__model = self.__model._replace(connection=random.choice(connections))
                    else:
                        self.__model = self.__model._replace(connection=(self.__model.host, self.__model.port))
                        LOG_DEBUG('XMPP:connect - no xmpp_connections are passed - using default connection', self.__model.connection)
                    if self.__model.token is None:
                        Account.g_accountRepository and Account.g_accountRepository.onChatTokenReceived.clear()
                        Account.g_accountRepository.onChatTokenReceived += self._tokenCallback
                    BigWorld.player().requestChatToken(self.__idsGen.next())
                else:
                    LOG_DEBUG('XMPP:connect - trying to connect using token from previous connection')
                    self._tokenCallback(cPickle.dumps({'error': None,
                     'token': self.__model.token,
                     'databaseID': self.__databaseID}))
            else:
                LOG_DEBUG('XMPP:connect - XMPP functionality is disabled. Stopping execution')
            return

    def disconnect(self):
        LOG_DEBUG('XMPP:disconnect')
        if Account.g_accountRepository:
            Account.g_accountRepository.onChatTokenReceived.clear()
        self.__bwConnected = False
        if self.isConnected:
            self.__client.disconnect()
        else:
            self.onDisconnect()

    def onConnect(self):
        """
        Called after successful connection, encryption setup and authentication.
        """
        LOG_DEBUG('XMPP:onConnect - Successfully connected to XMPP server')
        self.__model = self.__model._replace(isConnected=True)
        self.__reconnectCount = 0
        self._cancelReconnectCallback()
        if self.__pendingBattleMode is not None:
            self._setBattleMode(self.__pendingBattleMode)
            self.__pendingBattleMode = None
        self._doRostersSync()
        return

    def onDisconnect(self, reason = DISCONNECT_BY_REQUEST, description = None):
        """
        Called if connection is closed or attempt to connect is failed.
        Additional description (in English) of disconnect reason is given. If
        description is empty then disconnect was caused by user (i.e. by
        explicit call to disconnect()).
        """
        LOG_DEBUG('XMPP:onDisconnect - Disconnected', reason, description)
        self._cancelReconnectCallback()
        if reason == self.DISCONNECT_AUTHENTICATION:
            self.__model = self.__model._replace(token=None)
        if self.__bwConnected:
            if self.__isEnabled:
                self.__model = self.__model._replace(isConnected=False)
                self.__reconnectCount += 1
                reconnectDelay = max(random.random() * 2 * self.__reconnectCount, 10.0)
                self.__reconnectCallbackId = BigWorld.callback(reconnectDelay, self.connect)
                LOG_DEBUG('XMPP:onDisconnect - will try to reconnect in {0} seconds'.format(reconnectDelay), description)
        else:
            if self.__isEnabled:
                self._unsubscribeFromActions()
            self.__client.xmppHandler = None
            self.__currentUser = None
            self.__xmppRoster = None
            self.__model = None
            self.__bwRoster = None
            self.__isEnabled = False
            self.__reconnectCount = 0
            self.__databaseID = None
        return

    def onNewRosterItem(self, bareJid, name, groups, subscriptionTo, subscriptionFrom):
        """
        Called when the contact is changed or added.
        
        name is custom contact name chosen by user.
        
        groups is set of groups (strings) which contact belongs to.
        
        subscriptionTo is presence subscription state in direction "contact
        TO user". One of SUBSCRIPTION_* values is used.
        
        subscriptionFrom is presence subscription state in direction "FROM user
        to contact". Either SUBSCRIPTION_ON or SUBSCRIPTION_OFF is used here.
        See onSubscribe() event.
        """
        LOG_DEBUG('XMPP:onNewRosterItem - New roster item added', bareJid, name)
        if self.__bwRoster is not None:
            if bareJid in self.__bwRoster:
                self._addToLocalXmppRoster(bareJid, name, groups, subscriptionTo, subscriptionFrom)
            else:
                self._doXmppRosterAction(bareJid, USER_ROSTER_ACTION.RemoveFromFriend)
        else:
            self._addToLocalXmppRoster(bareJid, name, groups, subscriptionTo, subscriptionFrom)
        return

    def onRosterItemRemove(self, bareJid):
        """
        Called when the contact is removed.
        """
        LOG_DEBUG('XMPP:onRosterItemRemove', bareJid)
        if self.__bwRoster is not None:
            if bareJid not in self.__bwRoster:
                self._removeFromLocalXmppRoster(bareJid)
            else:
                user = self.__bwRoster[bareJid]
                action = USER_ROSTER_ACTION.AddToFriend if bool(user.getRoster() & USERS_ROSTER_FRIEND) else USER_ROSTER_ACTION.AddToIgnored
                self._doXmppRosterAction(bareJid, action, user.getName())
        else:
            self._removeFromLocalXmppRoster(bareJid)
        return

    def onNewRosterResource(self, fullJid, priority, status, presence):
        """
        Called when contact resource is changed or added.
        
        You should compare fullJid of resource with fullJid of client to
        determine if this resource change is actually server acknowledgement of
        user presence change.
        
        Exact value of resource priority depends solely on contact's choice.
        
        status can be arbitrary text.
        
        Resource presence is defined by one of PRESENCE_* values.
        """
        LOG_DEBUG('XMPP:onNewRosterResource', fullJid, priority, status, presence)
        fullJidParts = fullJid.split('/')
        if len(fullJidParts) > 1:
            bareJid, resourceName = fullJidParts[0:2]
            if fullJid != self.__client.fullJid:
                if bareJid not in self.__xmppRoster:
                    self.__xmppRoster[bareJid] = RosterItem(bareJid)
                self.__xmppRoster[bareJid].updateResource(resourceName, priority, status, presence)
            else:
                self.__currentUser.updateResource(resourceName, priority, status, presence)

    def onRosterResourceRemove(self, fullJid):
        """
        Called when contact resource is removed (i.e. contact has gone offline).
        """
        LOG_DEBUG('XMPP:onRosterResourceRemove', fullJid)
        fullJidParts = fullJid.split('/')
        if len(fullJidParts) > 1:
            bareJid, resourceName = fullJidParts[0:2]
            if fullJid != self.__client.fullJid:
                if bareJid in self.__xmppRoster:
                    self.__xmppRoster[bareJid].removeResource(resourceName)
            else:
                self.__currentUser.removeResource(resourceName)

    def onSubscribe(self, bareJid, message):
        """
        Called when a contact (from roster or not) asks for subscription to user
        status updates.
        
        Call setSubscribed() or setUnsubscribed() to allow or disallow sending
        user status updates to the contact. Roster item will be automatically
        updated by onNewRosterItem event.
        
        Note that transition of subscriptionFrom attribute of contact from
        SUBSCRIPTION_OFF state to SUBSCRIPTION_PENDING state should be done
        manually in this callback. This event shouldn't be generated if
        subscriptionFrom is SUBSCRIPTION_ON, however it's possible.
        """
        LOG_DEBUG('XMPP:onSubscribe - Subscription request received', bareJid, message)
        self.__client.setSubscribed(bareJid)

    def _subscribeToActions(self):
        """
        Adds subscription to UsersManager events
        """
        self.__usersMgr = g_messengerEvents.users
        self.__usersMgr.onUsersRosterReceived += self._onRosterReceived
        self.__usersMgr.onUserRosterChanged += self._onRosterUpdate

    def _unsubscribeFromActions(self):
        """
        Removes subscription to UsersManager events
        """
        if self.__usersMgr:
            self.__usersMgr.onUsersRosterReceived -= self._onRosterReceived
            self.__usersMgr.onUserRosterChanged -= self._onRosterUpdate
            self.__usersMgr = None
        return

    def _getServerSettings(self):
        """
        Gets server setting values
        """
        if self.USE_MOCK_DATA:
            settings = {'jdCutouts': 1,
             'xmpp_connections': [('jbr-wowpkis11.pershastudia.org', 5222)],
             'xmpp_host': 'jbr-wowpkis11.pershastudia.org',
             'xmpp_port': 5222,
             'xmpp_resource': 'wot',
             'xmpp_enabled': True}
        elif Account.g_accountRepository:
            settings = Account.g_accountRepository.serverSettings
        else:
            settings = {'jdCutouts': 0,
             'xmpp_enabled': False}
        return settings

    def _tokenCallback(self, data):
        """
        Callback for PlayerAccount.requestChatToken method call
        """
        data = cPickle.loads(data)
        errorStr = data.get('error', None)
        if errorStr is None:
            self.__model = self.__model._replace(token=data.get('token'))
            self.__databaseID = data.get('databaseID')
            host, port = self.__model.connection
            if self.USE_MOCK_DATA:
                bareJid = '{0}@{1}'.format('admin1', self.__model.host)
            else:
                bareJid = '{0}@{1}'.format(self.__databaseID, self.__model.host)
            fullJid = '{0}/{1}'.format(bareJid, self.__model.resourceName)
            self.__currentUser = RosterItem(bareJid, 'Self', [], BigWorld.XmppClient.SUBSCRIPTION_OFF, BigWorld.XmppClient.SUBSCRIPTION_OFF)
            LOG_DEBUG('XMPP:_tokenCallback - Token received - connecting to XMPP server', fullJid, self.__model.token, host, port)
            self.__client.xmppHandler = self
            self.__xmppRoster = {}
            self.__client.connect(fullJid, str(self.__model.token), host, port)
        else:
            self.onDisconnect()
            LOG_ERROR('XMPP:_tokenCallback - Error while getting XMPP connection token', errorStr)
        return

    def _cancelReconnectCallback(self):
        try:
            if self.__reconnectCallbackId is not None:
                BigWorld.cancelCallback(self.__reconnectCallbackId)
        except:
            pass
        finally:
            self.__reconnectCallbackId = None

        return

    def _onRosterReceived(self):
        """
        Listener for UsersManager.onUsersRosterReceived
        """
        self.__bwRoster = {}
        contacts = self.usersStorage.all()
        LOG_DEBUG('XMPP:_onRosterReceived - BW rooster received', contacts)
        for user in contacts:
            if user.isCurrentPlayer():
                continue
            if self.USE_MOCK_DATA:
                bareJid = '{0}@{1}'.format('admin2', self.__model.host)
            else:
                bareJid = '{0}@{1}'.format(user.getID(), self.__model.host)
            self.__bwRoster[bareJid] = user

        self._doRostersSync()

    def _onRosterUpdate(self, action, user):
        """
        Listener for UsersManager.onUsersRosterUpdate
        """
        if action in self.ALLOWED_ROSTER_ACTIONS:
            if self.USE_MOCK_DATA:
                bareJid = '{0}@{1}'.format('admin2', self.__model.host)
            else:
                bareJid = '{0}@{1}'.format(user.getID(), self.__model.host)
            LOG_DEBUG('XMPP:_onRosterUpdate - BW rooster update', action, user)
            if action in [USER_ROSTER_ACTION.AddToFriend, USER_ROSTER_ACTION.AddToIgnored]:
                self.__bwRoster[bareJid] = user
            elif bareJid in self.__bwRoster:
                del self.__bwRoster[bareJid]
            self._doXmppRosterAction(bareJid, action, user.getName())

    def _doRostersSync(self):
        """
        Performs XMPP roster synchronization with BW roster (BW is Master)
        """
        if self.__bwRoster is not None and self.isConnected:
            bwJidSet = set(self.__bwRoster)
            xmppJidSet = set(self.__xmppRoster)
            LOG_DEBUG('XMPP:_doRostersSync - Syncing BW and XMPP rosters')
            LOG_DEBUG('XMPP:_doRostersSync - BW roster', bwJidSet)
            LOG_DEBUG('XMPP:_doRostersSync - XMPP roster', xmppJidSet)
            toRemove = xmppJidSet - bwJidSet
            toAdd = bwJidSet - xmppJidSet
            for jid in toRemove:
                self._doXmppRosterAction(jid, USER_ROSTER_ACTION.RemoveFromFriend)

            for jid in toAdd:
                user = self.__bwRoster[jid]
                action = USER_ROSTER_ACTION.AddToFriend if bool(user.getRoster() & USERS_ROSTER_FRIEND) else USER_ROSTER_ACTION.AddToIgnored
                self._doXmppRosterAction(jid, action, user.getName())

        return

    def _addToLocalXmppRoster(self, bareJid, name, groups, subscriptionTo, subscriptionFrom):
        """
        Adds new item to local XMPP roster
        """
        if bareJid in self.__xmppRoster:
            LOG_DEBUG('XMPP:_addToLocalXmppRoster - Updating item in local XMPP roster', bareJid, name, groups, subscriptionTo, subscriptionFrom)
            item = self.__xmppRoster.get(bareJid)
            item.name, item.groups, item.subscriptionTo, item.subscriptionFrom = (name,
             groups,
             subscriptionTo,
             subscriptionFrom)
        else:
            LOG_DEBUG('XMPP:_addToLocalXmppRoster - Adding item to local XMPP roster', bareJid, name, groups, subscriptionTo, subscriptionFrom)
            self.__xmppRoster[bareJid] = RosterItem(bareJid, name, groups, subscriptionTo, subscriptionFrom)

    def _removeFromLocalXmppRoster(self, bareJid):
        """
        Removes item from local XMPP roster
        """
        LOG_DEBUG('XMPP:_removeFromLocalXmppRoster - Roster item is removed from local XMPP roster', bareJid, self.__xmppRoster[bareJid].name)
        del self.__xmppRoster[bareJid]

    def _doXmppRosterAction(self, bareJid, action, userName = 'Unknown'):
        """
        Triggers needed roster action with XMPP chat server basing on passes action type
        """
        if action in [USER_ROSTER_ACTION.AddToFriend, USER_ROSTER_ACTION.AddToIgnored]:
            LOG_DEBUG('XMPP:_doXmppRosterAction - adding user from BW rooster to XMPP roster', bareJid, userName)
            self.__client.add(bareJid, userName)
            self.__client.subscribe(bareJid)
        elif action in [USER_ROSTER_ACTION.RemoveFromFriend, USER_ROSTER_ACTION.RemoveFromIgnored]:
            LOG_DEBUG('XMPP:_doXmppRosterAction - user is removed from BW rooster. Removing from XMPP roster', bareJid)
            self.__client.remove(bareJid)
            self.__client.unsubscribe(bareJid)

    def _setBattleMode(self, mode):
        LOG_DEBUG('XMPP:_setBattleMode', mode)
        if self.isConnected:
            self.__client.presence = BigWorld.XmppClient.PRESENCE_DND if mode == MESSENGER_SCOPE.BATTLE else BigWorld.XmppClient.PRESENCE_AVAILABLE
        else:
            self.__pendingBattleMode = mode
            self.onDisconnect()
# okay decompyling res/scripts/client/messenger/proto/xmpp/__init__.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:27:16 EST

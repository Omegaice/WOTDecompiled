# 2013.11.15 11:25:44 EST
# Embedded file name: scripts/client/gui/prb_control/invites.py
from collections import namedtuple
import BigWorld
from ConnectionManager import connectionManager
from PlayerEvents import g_playerEvents
from account_helpers import getPlayerDatabaseID, isRoamingEnabled
from adisp import process
import constants
from debug_utils import LOG_ERROR, LOG_WARNING, LOG_DEBUG
from gui.ClientUpdateManager import g_clientUpdateManager
from gui.LobbyContext import g_lobbyContext
from gui.shared import g_itemsCache
from gui.shared.actions import ActionsChain
from gui.shared.utils.requesters import StatsRequester
from ids_generators import SequenceIDGenerator
from helpers import time_utils
from messenger import g_settings
import Event
from messenger.proto.events import g_messengerEvents
from messenger.storage import storage_getter
from predefined_hosts import g_preDefinedHosts
_PrbInviteData = namedtuple('_PrbInviteData', ' '.join(['id',
 'createTime',
 'type',
 'comment',
 'creator',
 'creatorDBID',
 'creatorClanAbbrev',
 'receiver',
 'receiverDBID',
 'receiverClanAbbrev',
 'state',
 'count',
 'peripheryID']))

class PrbInviteWrapper(_PrbInviteData):

    @staticmethod
    def __new__(cls, id = -1L, createTime = None, type = 0, comment = str(), creator = str(), creatorDBID = -1L, creatorClanAbbrev = None, receiver = str(), receiverDBID = -1L, receiverClanAbbrev = None, state = None, count = 0, peripheryID = 0, **kwargs):
        if createTime is not None:
            createTime = time_utils.makeLocalServerTime(createTime)
        result = _PrbInviteData.__new__(cls, id, createTime, type, comment, creator, creatorDBID, creatorClanAbbrev, receiver, receiverDBID, receiverClanAbbrev, state, count, peripheryID)
        return result

    @property
    def creatorFullName(self):
        return g_lobbyContext.getPlayerFullName(self.creator, clanAbbrev=self.creatorClanAbbrev, pDBID=self.creatorDBID)

    @property
    def receiverFullName(self):
        return g_lobbyContext.getPlayerFullName(self.receiver, clanAbbrev=self.receiverClanAbbrev, pDBID=self.receiverDBID)

    @property
    def anotherPeriphery(self):
        return connectionManager.peripheryID != self.peripheryID

    def _merge(self, other):
        data = {}
        if other.createTime is not None:
            data['createTime'] = time_utils.makeLocalServerTime(other.createTime)
        if other.state > 0:
            data['state'] = other.state
        if other.count > 0:
            data['count'] = other.count
        if len(other.comment):
            data['comment'] = other.comment
        return self._replace(**data)

    def isPlayerSender(self):
        return False

    def isActive(self):
        return self.state == constants.PREBATTLE_INVITE_STATE.ACTIVE


class _AcceptInvitesPostActions(ActionsChain):

    def __init__(self, peripheryID, prebattleID, actions):
        self.peripheryID = peripheryID
        self.prebattleID = prebattleID
        super(_AcceptInvitesPostActions, self).__init__(actions)


class InvitesManager(object):
    __clanInfo = None

    def __init__(self):
        from gui.prb_control.formatters.invites import PrbInviteLinkFormatter
        self.__linkFormatter = PrbInviteLinkFormatter()
        self._IDGen = SequenceIDGenerator()
        self._IDMap = {'inviteIDs': {},
         'prbIDs': {}}
        self.__receivedInvites = {}
        self.__unreadInvitesCount = 0
        self.__eventManager = Event.EventManager()
        self.__acceptChain = None
        self.onReceivedInviteListInited = Event.Event(self.__eventManager)
        self.onReceivedInviteListModified = Event.Event(self.__eventManager)
        return

    def init(self):
        self.__isUsersRostersInited = False
        self.__isInvitesListBuild = False
        g_messengerEvents.users.onUsersRosterReceived += self.__me_onUsersRosterReceived
        g_playerEvents.onPrebattleInvitesChanged += self.__pe_onPrebattleInvitesChanged

    def fini(self):
        self.__clearAcceptChain()
        self.__isUsersRostersInited = False
        self.__isInvitesListBuild = False
        g_messengerEvents.users.onUsersRosterReceived += self.__me_onUsersRosterReceived
        g_playerEvents.onPrebattleInvitesChanged -= self.__pe_onPrebattleInvitesChanged
        self.clear()

    def clear(self):
        self.__isUsersRostersInited = False
        self.__isInvitesListBuild = False
        self.__receivedInvites.clear()
        self.__unreadInvitesCount = 0
        self._IDMap = {'inviteIDs': {},
         'prbIDs': {}}
        self.__eventManager.clear()

    @process
    def onAccountShowGUI(self):
        clanInfo = yield StatsRequester().getClanInfo()
        self._setClanInfo(clanInfo)
        g_clientUpdateManager.addCallbacks({'stats.clanInfo': self._setClanInfo})

    def onAvatarBecomePlayer(self):
        g_clientUpdateManager.removeObjectCallbacks(self)
        self.__clearAcceptChain()

    @storage_getter('users')
    def users(self):
        return None

    def isInited(self):
        return self.__isUsersRostersInited and self.__isInvitesListBuild

    def acceptInvite(self, inviteID, postActions = None):
        try:
            prebattleID, peripheryID = self._IDMap['inviteIDs'][inviteID]
        except KeyError:
            LOG_ERROR('Invite ID is invalid', inviteID, self._IDMap)
            return

        self.__clearAcceptChain()
        if not postActions:
            self._doAccept(prebattleID, peripheryID)
        else:
            self.__acceptChain = _AcceptInvitesPostActions(peripheryID, prebattleID, postActions)
            self.__acceptChain.onStopped += self.__accept_onPostActionsStopped
            self.__acceptChain.start()
        if self.__unreadInvitesCount > 0:
            self.__unreadInvitesCount -= 1

    def declineInvite(self, inviteID):
        try:
            prebattleID, peripheryID = self._IDMap['inviteIDs'][inviteID]
        except KeyError:
            LOG_ERROR('Invite ID is invalid', inviteID, self._IDMap)
            return

        BigWorld.player().prb_declineInvite(prebattleID, peripheryID)
        if self.__unreadInvitesCount > 0:
            self.__unreadInvitesCount -= 1

    def canAcceptInvite(self, invite):
        result = False
        if invite.id in self.__receivedInvites:
            from gui.prb_control.dispatcher import g_prbLoader
            dispatcher = g_prbLoader.getDispatcher()
            if dispatcher:
                prbFunctional = dispatcher.getPrbFunctional()
                unitFunctional = dispatcher.getUnitFunctional()
                return (prbFunctional and prbFunctional.hasLockedState() or unitFunctional and unitFunctional.hasLockedState()) and False
        another = invite.anotherPeriphery
        if another:
            if g_preDefinedHosts.periphery(invite.peripheryID) is None:
                LOG_ERROR('Periphery not found')
                result = False
            elif g_lobbyContext.getCredentials() is None:
                LOG_ERROR('Login info not found')
                result = False
            elif g_preDefinedHosts.isRoamingPeriphery(invite.peripheryID) and not isRoamingEnabled(g_itemsCache.items.stats.attributes):
                LOG_ERROR('Roaming is not supported')
                result = False
            elif invite.id > 0:
                result = invite.isActive()
            else:
                result = invite.id > 0 and invite.isActive()
        return result

    def canDeclineInvite(self, invite):
        result = False
        if invite.id in self.__receivedInvites:
            result = invite.id > 0 and invite.isActive()
        return result

    def getInviteInfo(self, inviteID):
        try:
            prebattleID, peripheryID = self._IDMap['inviteIDs'][inviteID]
            return (prebattleID, peripheryID)
        except KeyError:
            return (0, 0)

    def getReceivedInviteCount(self):
        return len(self.__receivedInvites)

    def getReceivedInvite(self, inviteID):
        return self.__receivedInvites.get(inviteID)

    def getReceivedInvites(self, IDs = None):
        result = self.__receivedInvites.values()
        if IDs is not None:
            result = filter(lambda item: item[0].id in IDs, result)
        return result

    def getUnreadCount(self):
        return self.__unreadInvitesCount

    def resetUnreadCount(self):
        self.__unreadInvitesCount = 0

    def _doAccept(self, prebattleID, peripheryID):
        if connectionManager.peripheryID == peripheryID:
            BigWorld.player().prb_acceptInvite(prebattleID, peripheryID)
        else:
            LOG_ERROR('Invalid periphery', (prebattleID, peripheryID), connectionManager.peripheryID)

    def _makeInviteID(self, prebattleID, peripheryID):
        inviteID = self._IDMap['prbIDs'].get((prebattleID, peripheryID))
        if inviteID is None:
            inviteID = self._IDGen.next()
            self._IDMap['inviteIDs'][inviteID] = (prebattleID, peripheryID)
            self._IDMap['prbIDs'][prebattleID, peripheryID] = inviteID
        return inviteID

    def _addInvite(self, invite, userGetter):
        if g_settings.userPrefs.invitesFromFriendsOnly:
            user = userGetter(invite.creatorDBID)
            if user is None or not user.isFriend():
                LOG_DEBUG('Invite to be ignored:', invite)
                return False
        link = self.__linkFormatter.format(invite)
        if not len(link):
            if constants.IS_DEVELOPMENT:
                LOG_WARNING('Formatter not found. Invite data : ', invite)
            return False
        else:
            self.__receivedInvites[invite.id] = (invite, link)
            if invite.isActive():
                self.__unreadInvitesCount += 1
            return True

    def _updateInvite(self, other, userGetter):
        inviteID = other.id
        invite, _ = self.__receivedInvites[inviteID]
        if other.isActive() and g_settings.userPrefs.invitesFromFriendsOnly:
            user = userGetter(invite.creatorDBID)
            if user is None or not user.isFriend():
                LOG_DEBUG('Invite to be ignored:', invite)
                return False
        prevCount = invite.count
        invite = invite._merge(other)
        link = self.__linkFormatter.format(invite)
        self.__receivedInvites[inviteID] = (invite, link)
        if invite.isActive() and prevCount < invite.count:
            self.__unreadInvitesCount += 1
        return True

    def _delInvite(self, inviteID):
        result = inviteID in self.__receivedInvites
        if result:
            self.__receivedInvites.pop(inviteID)
        return result

    def _buildReceivedInvitesList(self, invitesData):
        self.__isInvitesListBuild = True
        self.__receivedInvites.clear()
        self.__unreadInvitesCount = 0
        receiver = BigWorld.player().name
        receiverDBID = getPlayerDatabaseID()
        receiverClanAbbrev = g_lobbyContext.getClanAbbrev(self.__clanInfo)
        userGetter = self.users.getUser
        for (prebattleID, peripheryID), data in invitesData.iteritems():
            inviteID = self._makeInviteID(prebattleID, peripheryID)
            invite = PrbInviteWrapper(id=inviteID, receiver=receiver, receiverDBID=receiverDBID, receiverClanAbbrev=receiverClanAbbrev, peripheryID=peripheryID, **data)
            self._addInvite(invite, userGetter)

    def _setClanInfo(self, clanInfo):
        self.__clanInfo = clanInfo
        if not self.__isUsersRostersInited:
            return
        receiverClanAbbrev = g_lobbyContext.getClanAbbrev(self.__clanInfo)
        changed = []
        for inviteID, (invite, _) in self.__receivedInvites.iteritems():
            if invite.receiverClanAbbrev != receiverClanAbbrev:
                invite = invite._replace(receiverClanAbbrev=receiverClanAbbrev)
                link = self.__linkFormatter.format(invite)
                self.__receivedInvites[inviteID] = (invite, link)
                changed.append(inviteID)

        if len(changed) > 0:
            self.onReceivedInviteListModified([], changed, [])

    def __clearAcceptChain(self):
        if self.__acceptChain is not None:
            self.__acceptChain.onStopped -= self.__accept_onPostActionsStopped
            self.__acceptChain.stop()
            self.__acceptChain = None
        return

    def __me_onUsersRosterReceived(self):
        if not self.__isUsersRostersInited:
            invitesData = getattr(BigWorld.player(), 'prebattleInvites', {})
            LOG_DEBUG('Users roster received, list of invites is available', invitesData)
            self.__isUsersRostersInited = True
            self._buildReceivedInvitesList(invitesData)
            self.onReceivedInviteListInited()

    def __pe_onPrebattleInvitesChanged(self, diff):
        if not self.__isUsersRostersInited:
            LOG_DEBUG('Received invites ignored. Manager waits for client will receive a roster list')
            return
        else:
            prbInvites = diff.get(('prebattleInvites', '_r'))
            if prbInvites is not None:
                self._buildReceivedInvitesList(prbInvites)
            prbInvites = diff.get('prebattleInvites')
            if prbInvites is not None:
                self.__updatePrebattleInvites(prbInvites)
            return

    def __updatePrebattleInvites(self, prbInvites):
        receiver = BigWorld.player().name
        receiverDBID = getPlayerDatabaseID()
        receiverClanAbbrev = g_lobbyContext.getClanAbbrev(self.__clanInfo)
        added = []
        changed = []
        deleted = []
        modified = False
        rosterGetter = self.users.getUser
        for (prebattleID, peripheryID), data in prbInvites.iteritems():
            inviteID = self._makeInviteID(prebattleID, peripheryID)
            if data is None:
                if self._delInvite(inviteID):
                    modified = True
                    deleted.append(inviteID)
                continue
            invite = PrbInviteWrapper(id=inviteID, receiver=receiver, receiverDBID=receiverDBID, receiverClanAbbrev=receiverClanAbbrev, peripheryID=peripheryID, **data)
            inList = inviteID in self.__receivedInvites
            if not inList:
                if self._addInvite(invite, rosterGetter):
                    modified = True
                    added.append(inviteID)
            elif self._updateInvite(invite, rosterGetter):
                modified = True
                changed.append(inviteID)

        if modified:
            self.onReceivedInviteListModified(added, changed, deleted)
        return

    def __accept_onPostActionsStopped(self, isCompleted):
        if not isCompleted:
            return
        prebattleID = self.__acceptChain.prebattleID
        peripheryID = self.__acceptChain.peripheryID
        if (prebattleID, peripheryID) in self._IDMap['prbIDs']:
            self._doAccept(prebattleID, peripheryID)
            if self.__unreadInvitesCount > 0:
                self.__unreadInvitesCount -= 1
        else:
            LOG_ERROR('Prebattle invite not found', prebattleID, peripheryID)
# okay decompyling res/scripts/client/gui/prb_control/invites.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:25:45 EST

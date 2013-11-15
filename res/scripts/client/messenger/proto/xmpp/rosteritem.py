# 2013.11.15 11:27:16 EST
# Embedded file name: scripts/client/messenger/proto/xmpp/RosterItem.py
import BigWorld
from debug_utils import LOG_ERROR, LOG_DEBUG
from messenger.proto.xmpp.XmppResource import XmppResource

class RosterItem:

    def __init__(self, bareJid, name = 'Unknown', groups = None, subscriptionTo = BigWorld.XmppClient.SUBSCRIPTION_OFF, subscriptionFrom = BigWorld.XmppClient.SUBSCRIPTION_OFF):
        self.__bareJid = bareJid
        self.__name = name
        self.__groups = groups
        self.__subscriptionTo = subscriptionTo
        self.__subscriptionFrom = subscriptionFrom
        self.__resources = {}

    def updateResource(self, name, priority, status, presence):
        """Adds new or updates existing resource data"""
        if name not in self.__resources:
            self.__resources[name] = XmppResource(name, priority, status, presence)
        else:
            resource = self.__resources[name]
            resource.priority = priority
            resource.status = status
            resource.presence = presence
        self.__tracePresence()

    def removeResource(self, name):
        """Removes resource data"""
        if name in self.__resources:
            del self.__resources[name]
        else:
            LOG_ERROR('XMPP: resource remove error: resource {0} is not in list of resources for {1}'.format(name, self.bareJid))
        self.__tracePresence()

    def getPriorityResource(self):
        result = None
        if len(self.__resources) > 0:
            result = sorted(self.__resources.values(), cmp=self.__resourceComparator)[0]
        return result

    @property
    def bareJid(self):
        """Contact bare JID, i.e. in format "user@domain" (without resource)."""
        return self.__bareJid

    @property
    def fullJid(self):
        """
        Constructs fullJID, basing on registered resources (top priority resource is used)
        """
        result = None
        resource = self.getPriorityResource()
        if resource is not None:
            result = '{0}/{1}'.format(self.bareJid, resource.name)
        return result

    @property
    def presence(self):
        """
        Returns presence state for RosterItem, basing on registered resources (top priority resource is used)
        """
        result = BigWorld.XmppClient.PRESENCE_UNKNOWN
        resource = self.getPriorityResource()
        if resource is not None:
            result = resource.presence
        return result

    @property
    def name(self):
        """Custom contact name chosen by user."""
        return self.__name

    @name.setter
    def name(self, value):
        self.__name = value

    @property
    def groups(self):
        """List of groups (strings) which contact belongs to."""
        return self.__groups

    @groups.setter
    def groups(self, value):
        self.__groups = value

    @property
    def subscriptionTo(self):
        """
        Presence subscription status in direction "contact TO user".
        One of SUBSCRIPTION_* values is returned.
        """
        return self.__subscriptionTo

    @subscriptionTo.setter
    def subscriptionTo(self, value):
        self.__subscriptionTo = value

    @property
    def subscriptionFrom(self):
        """
        Presence subscription status in direction "FROM user to contact".
        One of SUBSCRIPTION_* values is returned.
        """
        return self.__subscriptionFrom

    @subscriptionFrom.setter
    def subscriptionFrom(self, value):
        self.__subscriptionFrom = value

    def getPresenceStr(self, presence):
        names = ['unknown',
         'online',
         'available for chat',
         'away',
         'DND',
         'extended away',
         'unavailable']
        return names[presence]

    def __resourceComparator(self, item, other):
        presenceRank = [BigWorld.XmppClient.PRESENCE_AVAILABLE,
         BigWorld.XmppClient.PRESENCE_CHAT,
         BigWorld.XmppClient.PRESENCE_AWAY,
         BigWorld.XmppClient.PRESENCE_DND,
         BigWorld.XmppClient.PRESENCE_XA,
         BigWorld.XmppClient.PRESENCE_UNAVAILABLE,
         BigWorld.XmppClient.PRESENCE_UNKNOWN]
        if item.presence ^ other.presence:
            result = cmp(presenceRank.index(item.presence), presenceRank.index(other.presence))
        elif item.priority ^ other.priority:
            result = cmp(other.priority, item.priority)
        else:
            result = cmp(item.name, other.name)
        return result

    def __tracePresence(self):
        LOG_DEBUG('XMPP: Roster item presence changed', self.bareJid, self.name, self.getPresenceStr(self.presence))
# okay decompyling res/scripts/client/messenger/proto/xmpp/rosteritem.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:27:17 EST

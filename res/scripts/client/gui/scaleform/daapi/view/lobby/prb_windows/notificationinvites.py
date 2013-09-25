from gui.Scaleform.daapi.view.meta.WindowViewMeta import WindowViewMeta
from gui.Scaleform.daapi.view.meta.NotificationInvitesWindowMeta import NotificationInvitesWindowMeta
from gui.Scaleform.framework import AppRef
from gui.Scaleform.framework.entities.View import View
from gui.Scaleform.managers.windows_stored_data import DATA_TYPE, TARGET_ID
from gui.Scaleform.managers.windows_stored_data import stored_window
from gui.prb_control.prb_helpers import InjectPrebattle, prbInvitesProperty
from gui.shared import events
from gui.shared.event_bus import EVENT_BUS_SCOPE
__author__ = 'd_savitski'

@stored_window(DATA_TYPE.UNIQUE_WINDOW, TARGET_ID.CHAT_MANAGEMENT)

class NotificationInvitesWindow(View, WindowViewMeta, NotificationInvitesWindowMeta, AppRef):
    __metaclass__ = InjectPrebattle

    @prbInvitesProperty
    def prbInvites(self):
        pass

    def __init__(self):
        super(NotificationInvitesWindow, self).__init__()

    def onWindowClose(self):
        self.destroy()

    def requestInvites(self):
        self.__parseInviteMessages()

    def selectedInvite(self, value):
        self.app.fireEvent(events.ShowWindowEvent(events.ShowWindowEvent.SHOW_RECEIVED_INVITE_WINDOW, {'inviteID': int(value)}), scope=EVENT_BUS_SCOPE.LOBBY)

    def _populate(self):
        super(NotificationInvitesWindow, self)._populate()
        self.prbInvites.onReceivedInviteListModified += self.__unreadMessagesHandler
        self.addListener(events.HideWindowEvent.HIDE_NOTIFICATION_INVITES_WINDOW, self.__handleNotificationWindowHide, scope=EVENT_BUS_SCOPE.LOBBY)

    def _dispose(self):
        super(NotificationInvitesWindow, self)._dispose()
        self.prbInvites.onReceivedInviteListModified -= self.__unreadMessagesHandler
        self.removeListener(events.HideWindowEvent.HIDE_NOTIFICATION_INVITES_WINDOW, self.__handleNotificationWindowHide, scope=EVENT_BUS_SCOPE.LOBBY)

    def __unreadMessagesHandler(self, added, changed, deleted):
        self.__parseInviteMessages()

    def __comparator(self, data, other):
        return cmp(data[0].createTime, other[0].createTime)

    def __parseInviteMessages(self):
        self.prbInvites.resetUnreadCount()
        invites = self.prbInvites.getReceivedInvites()
        invites = sorted(invites, cmp=self.__comparator)
        links = map(lambda item: item[1], invites)
        self.as_setInvitesS('\n'.join(links))

    def __handleNotificationWindowHide(self, *args):
        self.onWindowClose()

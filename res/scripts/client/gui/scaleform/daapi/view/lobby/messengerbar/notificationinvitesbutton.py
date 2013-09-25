import BigWorld
from debug_utils import LOG_CURRENT_EXCEPTION
from gui.Scaleform.daapi.view.meta.NotificationInvitesButtonMeta import NotificationInvitesButtonMeta
from gui.Scaleform.framework import AppRef, VIEW_TYPE, g_entitiesFactories
from gui.Scaleform.framework.managers.containers import POP_UP_CRITERIA
from gui.prb_control.prb_helpers import InjectPrebattle, prbInvitesProperty
from gui.shared import events, EVENT_BUS_SCOPE
__author__ = 'd_savitski'

class NotificationInvitesButton(NotificationInvitesButtonMeta, AppRef):
    __metaclass__ = InjectPrebattle

    def __init__(self):
        super(NotificationInvitesButton, self).__init__()

    @prbInvitesProperty
    def prbInvites(self):
        pass

    def handleClick(self):
        self.as_setStateS(False)
        self.prbInvites.resetUnreadCount()
        window = self.__getWindow()
        if window is None:
            self.fireEvent(events.ShowWindowEvent(events.ShowWindowEvent.SHOW_NOTIFICATION_INVITES_WINDOW), scope=EVENT_BUS_SCOPE.LOBBY)
        else:
            window.onWindowClose()
        return

    def _populate(self):
        super(NotificationInvitesButton, self)._populate()
        self.__onInviteListInited()
        self.prbInvites.onReceivedInviteListInited += self.__onInviteListInited
        self.prbInvites.onReceivedInviteListModified += self.__onInviteListModified

    def _dispose(self):
        self.prbInvites.onReceivedInviteListInited -= self.__onInviteListInited
        self.prbInvites.onReceivedInviteListModified -= self.__onInviteListModified
        super(NotificationInvitesButton, self)._dispose()

    def __notifyClient(self):
        try:
            BigWorld.WGWindowsNotifier.onInvitation()
        except AttributeError:
            LOG_CURRENT_EXCEPTION()

    def __onInviteListInited(self):
        haveUnread = self.prbInvites.getUnreadCount() > 0
        if haveUnread:
            self.__notifyClient()
        if self.__getWindow() is None:
            self.as_setStateS(haveUnread)
        return

    def __onInviteListModified(self, *args):
        self.__notifyClient()
        if self.__getWindow() is None:
            self.as_setStateS(self.prbInvites.getUnreadCount() > 0)
        return

    def __getWindow(self):
        return self.app.containerManager.getView(VIEW_TYPE.WINDOW, criteria={POP_UP_CRITERIA.VIEW_ALIAS: g_entitiesFactories.getAliasByEvent(events.ShowWindowEvent.SHOW_NOTIFICATION_INVITES_WINDOW)})

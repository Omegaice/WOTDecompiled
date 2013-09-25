from gui.Scaleform.daapi.view.meta.MessengerBarMeta import MessengerBarMeta
from gui.Scaleform.framework import AppRef, VIEW_TYPE, g_entitiesFactories
from gui.Scaleform.framework.managers.containers import POP_UP_CRITERIA
from gui.shared import events
from gui.shared.event_bus import EVENT_BUS_SCOPE

class MessengerBar(MessengerBarMeta, AppRef):

    def __init__(self):
        super(MessengerBar, self).__init__()

    def channelButtonClick(self):
        eventType = events.ShowWindowEvent.SHOW_CHANNEL_MANAGEMENT_WINDOW
        if not self.__manageWindow(eventType):
            self.fireEvent(events.ShowWindowEvent(eventType), scope=EVENT_BUS_SCOPE.LOBBY)

    def contactsButtonClick(self):
        eventType = events.ShowWindowEvent.SHOW_CONTACTS_WINDOW
        if not self.__manageWindow(eventType):
            self.fireEvent(events.ShowWindowEvent(eventType), scope=EVENT_BUS_SCOPE.LOBBY)

    def __manageWindow(self, eventType):
        manager = self.app.containerManager
        window = manager.getView(VIEW_TYPE.WINDOW, {POP_UP_CRITERIA.VIEW_ALIAS: g_entitiesFactories.getAliasByEvent(eventType)})
        result = window is not None
        if result:
            name = window.uniqueName
            isOnTop = manager.as_isOnTopS(VIEW_TYPE.WINDOW, name)
            if not isOnTop:
                manager.as_bringToFrontS(VIEW_TYPE.WINDOW, name)
            else:
                window.onWindowClose()
        return result

from gui.Scaleform.framework.entities.EventSystemEntity import EventSystemEntity
from gui.shared.events import ShowWindowEvent
from notification.BaseMessagesController import BaseMessagesController
from notification import NotificationsModel

class ListController(BaseMessagesController, EventSystemEntity):

    def __init__(self, model):
        BaseMessagesController.__init__(self, model)
        self._model.onDisplayStateChanged += self.__displayStateChangeHandler

    def __displayStateChangeHandler(self, oldState, newState, data):
        if newState == NotificationsModel.LIST_STATE:
            self._model.resetNotifiedMessagesCount()
            self.fireEvent(ShowWindowEvent(ShowWindowEvent.SHOW_NOTIFICATIONS_LIST, {'model': self._model,
             'closeCallBack': self.__listCloseHandler}))

    def __listCloseHandler(self):
        if self._model.getDisplayState() == NotificationsModel.LIST_STATE:
            self._model.setPopupsDisplayState()

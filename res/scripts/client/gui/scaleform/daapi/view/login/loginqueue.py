from debug_utils import LOG_DEBUG
from gui.Scaleform.daapi.view.meta.LoginQueueWindowMeta import LoginQueueWindowMeta
from gui.Scaleform.framework import AppRef
from gui.Scaleform.framework.entities.View import View
from gui.shared import EVENT_BUS_SCOPE
from gui.shared.events import LoginEvent, LoginEventEx
__author__ = 'd_trofimov'

class LoginQueue(View, LoginQueueWindowMeta, AppRef):

    def __init__(self, title, message, cancelLabel):
        super(LoginQueue, self).__init__()
        self.__title = title
        self.__message = message
        self.__cancelLabel = cancelLabel

    def _populate(self):
        super(LoginQueue, self)._populate()
        self.as_setTitleS(self.__title)
        self.as_setMessageS(self.__message)
        self.as_setCancelLabelS(self.__cancelLabel)
        self.addListener(LoginEvent.CANCEL_LGN_QUEUE, self.__onCancelLoginQueue)

    def _dispose(self):
        self.removeListener(LoginEvent.CANCEL_LGN_QUEUE, self.__onCancelLoginQueue)
        super(LoginQueue, self)._dispose()

    def onWindowClose(self):
        self.__windowClosing()

    def onCancelClick(self):
        self.__windowClosing()

    def __windowClosing(self):
        self.fireEvent(LoginEventEx(LoginEventEx.ON_LOGIN_QUEUE_CLOSED, '', '', '', ''), EVENT_BUS_SCOPE.LOBBY)
        self.app.disconnect(True)
        self.destroy()

    def __onCancelLoginQueue(self, event):
        self.destroy()

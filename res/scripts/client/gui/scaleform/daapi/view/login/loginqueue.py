# 2013.11.15 11:26:24 EST
# Embedded file name: scripts/client/gui/Scaleform/daapi/view/login/LoginQueue.py
from debug_utils import LOG_DEBUG
from gui.Scaleform.daapi.view.meta.LoginQueueWindowMeta import LoginQueueWindowMeta
from gui.Scaleform.framework import AppRef
from gui.Scaleform.framework.entities.View import View
from gui.shared import EVENT_BUS_SCOPE
from gui.shared.events import LoginEvent, LoginEventEx, ArgsEvent
__author__ = 'd_trofimov'

class LoginQueue(View, LoginQueueWindowMeta, AppRef):

    def __init__(self, title, message, cancelLabel):
        super(LoginQueue, self).__init__()
        self.__updateData(title, message, cancelLabel)

    def __updateData(self, title, message, cancelLabel):
        self.__title = title
        self.__message = message
        self.__cancelLabel = cancelLabel

    def __updateTexts(self):
        self.as_setTitleS(self.__title)
        self.as_setMessageS(self.__message)
        self.as_setCancelLabelS(self.__cancelLabel)

    def _populate(self):
        super(LoginQueue, self)._populate()
        self.__updateTexts()
        self.addListener(LoginEvent.CANCEL_LGN_QUEUE, self.__onCancelLoginQueue)
        self.addListener(ArgsEvent.UPDATE_ARGS, self.__onUpdateArgs, EVENT_BUS_SCOPE.LOBBY)

    def _dispose(self):
        self.removeListener(LoginEvent.CANCEL_LGN_QUEUE, self.__onCancelLoginQueue)
        self.removeListener(ArgsEvent.UPDATE_ARGS, self.__onUpdateArgs, EVENT_BUS_SCOPE.LOBBY)
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

    def __onUpdateArgs(self, event):
        ctx = event.ctx
        LOG_DEBUG(str(event.alias) + ' ' + str(self.alias))
        if event.alias == self.alias:
            self.__updateData(**ctx)
            self.__updateTexts()
# okay decompyling res/scripts/client/gui/scaleform/daapi/view/login/loginqueue.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:26:24 EST

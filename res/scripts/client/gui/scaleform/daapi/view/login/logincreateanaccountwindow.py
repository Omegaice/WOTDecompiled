# 2013.11.15 11:26:23 EST
# Embedded file name: scripts/client/gui/Scaleform/daapi/view/login/LoginCreateAnAccountWindow.py
from debug_utils import LOG_DEBUG
from gui.Scaleform.daapi.view.meta.LoginCreateAnAccountWindowMeta import LoginCreateAnAccountWindowMeta
from gui.Scaleform.daapi.view.meta.WindowViewMeta import WindowViewMeta
from gui.Scaleform.framework import AppRef
from gui.Scaleform.framework.entities.View import View
import BigWorld
import ResMgr
import sys
from gui.shared import EVENT_BUS_SCOPE
from gui.shared.events import LoginEvent, LoginEventEx, LoginCreateEvent
__author__ = 'd_trofimov'

class LoginCreateAnAccountWindow(View, WindowViewMeta, LoginCreateAnAccountWindowMeta, AppRef):

    def __init__(self, title, message, submitLabel):
        super(LoginCreateAnAccountWindow, self).__init__()
        self.__title = title
        self.__message = message
        self.__submitLabel = submitLabel

    def _populate(self):
        super(LoginCreateAnAccountWindow, self)._populate()
        self.as_updateTextsS('', self.__title, self.__message, self.__submitLabel)
        self.addListener(LoginEvent.CLOSE_CREATE_AN_ACCOUNT, self.__onCreateAccResponse)

    def onWindowClose(self):
        self.destroy()

    def onRegister(self, nickname):
        self.fireEvent(LoginCreateEvent(LoginCreateEvent.CREATE_AN_ACCOUNT_REQUEST, View.alias, self.__title, nickname, self.__submitLabel), EVENT_BUS_SCOPE.LOBBY)

    def _dispose(self):
        self.removeListener(LoginEvent.CLOSE_CREATE_AN_ACCOUNT, self.__onCreateAccResponse)
        super(LoginCreateAnAccountWindow, self)._dispose()

    def __onCreateAccResponse(self, event):
        self.as_registerResponseS(event.isSuccess, event.errorMsg)
# okay decompyling res/scripts/client/gui/scaleform/daapi/view/login/logincreateanaccountwindow.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:26:23 EST

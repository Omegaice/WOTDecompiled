# 2013.11.15 11:25:56 EST
# Embedded file name: scripts/client/gui/Scaleform/daapi/view/dialogs/SimpleDialog.py
from gui.Scaleform.daapi.view.dialogs import DIALOG_BUTTON_ID
from gui.Scaleform.daapi.view.meta.SimpleDialogMeta import SimpleDialogMeta
from gui.Scaleform.daapi.view.meta.WindowViewMeta import WindowViewMeta
from gui.Scaleform.framework import VIEW_SCOPE
from gui.Scaleform.framework.entities.View import View

class SimpleDialog(View, SimpleDialogMeta, WindowViewMeta):

    def __init__(self, message, title, buttons, handler, canViewSkip = True, dialogScope = VIEW_SCOPE.DEFAULT):
        super(SimpleDialog, self).__init__()
        self.__message = message
        self.__title = title
        self.__buttons = buttons
        self.__handler = handler
        self.setCanViewSkip(canViewSkip)
        self.__dialogScope = dialogScope

    def __callHandler(self, buttonID):
        if self.__handler is not None:
            self.__handler(buttonID == DIALOG_BUTTON_ID.SUBMIT)
        return

    def getCurrentScope(self):
        if self.__dialogScope is not None:
            self.setCurrentScope(self.__dialogScope)
            self.__dialogScope = None
        return super(SimpleDialog, self).getCurrentScope()

    def _populate(self):
        super(SimpleDialog, self)._populate()
        self.as_setTextS(self.__message)
        self.as_setTitleS(self.__title)
        self.as_setButtonsS(self.__buttons)
        self.setCurrentScope(self.__dialogScope)
        self.__dialogScope = None
        return

    def _dispose(self):
        self.__message = None
        self.__title = None
        self.__buttons = None
        self.__handler = None
        super(SimpleDialog, self)._dispose()
        return

    def onButtonClick(self, buttonID):
        self.__callHandler(buttonID)
        self.destroy()

    def onWindowClose(self):
        self.__callHandler(DIALOG_BUTTON_ID.CLOSE)
        self.destroy()
# okay decompyling res/scripts/client/gui/scaleform/daapi/view/dialogs/simpledialog.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:25:56 EST

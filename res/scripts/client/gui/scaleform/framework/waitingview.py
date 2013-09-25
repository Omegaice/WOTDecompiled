# Embedded file name: scripts/client/gui/Scaleform/framework/WaitingView.py
import Keys
from gui import InputHandler
from gui.Scaleform.framework.entities.View import View
from gui.Scaleform.daapi.view.meta.WaitingViewMeta import WaitingViewMeta

class WaitingView(WaitingViewMeta, View):

    def __init__(self):
        super(WaitingView, self).__init__()
        InputHandler.g_instance.onKeyUp += self.handleKeyUpEvent
        self.__callback = None
        return

    def handleKeyUpEvent(self, event):
        if event.key == Keys.KEY_ESCAPE:
            if self.__callback:
                self.__callback()

    def close(self):
        self.__callback = None
        self.hideS(None)
        return

    def destroy(self):
        self.__callback = None
        InputHandler.g_instance.onKeyUp -= self.handleKeyUpEvent
        super(WaitingView, self).destroy()
        return

    def setCallback(self, value):
        self.__callback = value
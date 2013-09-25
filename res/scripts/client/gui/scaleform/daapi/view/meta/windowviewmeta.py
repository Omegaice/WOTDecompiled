# Embedded file name: scripts/client/gui/Scaleform/daapi/view/meta/WindowViewMeta.py
from gui.Scaleform.framework.entities.DAAPIModule import DAAPIModule

class WindowViewMeta(DAAPIModule):

    def onWindowClose(self):
        self._printOverrideError('onWindowClose')

    def onWindowMinimize(self):
        self._printOverrideError('onWindowMinimize')

    def as_showWaitingS(self, msg, props):
        if self._isDAAPIInited():
            return self.flashObject.as_showWaiting(msg, props)

    def as_hideWaitingS(self):
        if self._isDAAPIInited():
            return self.flashObject.as_hideWaiting()

    def as_getGeometryS(self):
        if self._isDAAPIInited():
            return self.flashObject.as_getGeometry()

    def as_setGeometryS(self, x, y, width, height):
        if self._isDAAPIInited():
            return self.flashObject.as_setGeometry(x, y, width, height)
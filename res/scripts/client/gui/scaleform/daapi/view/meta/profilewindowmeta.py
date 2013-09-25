# Embedded file name: scripts/client/gui/Scaleform/daapi/view/meta/ProfileWindowMeta.py
from gui.Scaleform.framework.entities.DAAPIModule import DAAPIModule

class ProfileWindowMeta(DAAPIModule):

    def as_setInitDataS(self, data):
        if self._isDAAPIInited():
            return self.flashObject.as_setInitData(data)

    def as_updateS(self, data):
        if self._isDAAPIInited():
            return self.flashObject.as_update(data)
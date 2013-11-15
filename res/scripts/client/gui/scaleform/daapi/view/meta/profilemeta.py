# 2013.11.15 11:26:26 EST
# Embedded file name: scripts/client/gui/Scaleform/daapi/view/meta/ProfileMeta.py
from gui.Scaleform.framework.entities.DAAPIModule import DAAPIModule

class ProfileMeta(DAAPIModule):

    def onCloseProfile(self):
        self._printOverrideError('onCloseProfile')

    def as_updateS(self, data):
        if self._isDAAPIInited():
            return self.flashObject.as_update(data)
# okay decompyling res/scripts/client/gui/scaleform/daapi/view/meta/profilemeta.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:26:26 EST

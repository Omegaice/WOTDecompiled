# 2013.11.15 11:26:26 EST
# Embedded file name: scripts/client/gui/Scaleform/daapi/view/meta/ProfileTechniqueMeta.py
from gui.Scaleform.framework.entities.DAAPIModule import DAAPIModule

class ProfileTechniqueMeta(DAAPIModule):

    def as_responseVehicleDossierS(self, data):
        if self._isDAAPIInited():
            return self.flashObject.as_responseVehicleDossier(data)
# okay decompyling res/scripts/client/gui/scaleform/daapi/view/meta/profiletechniquemeta.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:26:26 EST

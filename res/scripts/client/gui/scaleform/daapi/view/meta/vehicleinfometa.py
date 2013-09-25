from gui.Scaleform.framework.entities.DAAPIModule import DAAPIModule

class VehicleInfoMeta(DAAPIModule):

    def getVehicleInfo(self):
        self._printOverrideError('getVehicleInfo')

    def onCancelClick(self):
        self._printOverrideError('onCancelClick')

    def as_setVehicleInfoS(self, vehicleInfo):
        if self._isDAAPIInited():
            return self.flashObject.as_setVehicleInfo(vehicleInfo)

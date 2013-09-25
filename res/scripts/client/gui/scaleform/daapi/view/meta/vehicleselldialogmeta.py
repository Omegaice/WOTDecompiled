# Embedded file name: scripts/client/gui/Scaleform/daapi/view/meta/VehicleSellDialogMeta.py
from gui.Scaleform.framework.entities.DAAPIModule import DAAPIModule

class VehicleSellDialogMeta(DAAPIModule):

    def getDialogSettings(self):
        self._printOverrideError('getDialogSettings')

    def setDialogSettings(self, isOpen):
        self._printOverrideError('setDialogSettings')

    def sell(self, vehicleData, shells, eqs, optDevices, inventory, isDismissCrew):
        self._printOverrideError('sell')

    def setUserInput(self, value):
        self._printOverrideError('setUserInput')

    def setResultCredit(self, value):
        self._printOverrideError('setResultCredit')

    def as_setDataS(self, vehicle, modules, shells, removePrice, gold):
        if self._isDAAPIInited():
            return self.flashObject.as_setData(vehicle, modules, shells, removePrice, gold)

    def as_checkGoldS(self, gold):
        if self._isDAAPIInited():
            return self.flashObject.as_checkGold(gold)

    def as_visibleControlBlockS(self, value):
        if self._isDAAPIInited():
            return self.flashObject.as_visibleControlBlock(value)

    def as_enableButtonS(self, value):
        if self._isDAAPIInited():
            return self.flashObject.as_enableButton(value)

    def as_setCtrlQuestionS(self, value):
        if self._isDAAPIInited():
            return self.flashObject.as_setCtrlQuestion(value)

    def as_setControlNumberS(self, value):
        if self._isDAAPIInited():
            return self.flashObject.as_setControlNumber(value)
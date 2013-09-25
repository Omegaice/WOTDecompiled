from gui.Scaleform.framework.entities.DAAPIModule import DAAPIModule

class ExchangeFreeToTankmanXpWindowMeta(DAAPIModule):

    def apply(self):
        self._printOverrideError('apply')

    def onValueChanged(self, data):
        self._printOverrideError('onValueChanged')

    def calcValueRequest(self, value):
        self._printOverrideError('calcValueRequest')

    def as_setInitDataS(self, value):
        if self._isDAAPIInited():
            return self.flashObject.as_setInitData(value)

    def as_setCalcValueResponseS(self, value):
        if self._isDAAPIInited():
            return self.flashObject.as_setCalcValueResponse(value)

from gui.Scaleform.framework.entities.DAAPIModule import DAAPIModule

class DismissTankmanDialogMeta(DAAPIModule):

    def sendControlNumber(self, value):
        self._printOverrideError('sendControlNumber')

    def as_enabledButtonS(self, value):
        if self._isDAAPIInited():
            return self.flashObject.as_enabledButton(value)

    def as_tankManS(self, value):
        if self._isDAAPIInited():
            return self.flashObject.as_tankMan(value)

    def as_setQuestionForUserS(self, value):
        if self._isDAAPIInited():
            return self.flashObject.as_setQuestionForUser(value)

    def as_controlTextInputS(self, value):
        if self._isDAAPIInited():
            return self.flashObject.as_controlTextInput(value)

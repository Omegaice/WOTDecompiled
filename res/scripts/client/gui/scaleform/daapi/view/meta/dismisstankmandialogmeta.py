# 2013.11.15 11:26:24 EST
# Embedded file name: scripts/client/gui/Scaleform/daapi/view/meta/DismissTankmanDialogMeta.py
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
# okay decompyling res/scripts/client/gui/scaleform/daapi/view/meta/dismisstankmandialogmeta.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:26:25 EST

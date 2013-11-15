# 2013.11.15 11:26:25 EST
# Embedded file name: scripts/client/gui/Scaleform/daapi/view/meta/LoginCreateAnAccountWindowMeta.py
from gui.Scaleform.framework.entities.DAAPIModule import DAAPIModule

class LoginCreateAnAccountWindowMeta(DAAPIModule):

    def onRegister(self, nickname):
        self._printOverrideError('onRegister')

    def as_updateTextsS(self, defValue, titleText, messageText, submitText):
        if self._isDAAPIInited():
            return self.flashObject.as_updateTexts(defValue, titleText, messageText, submitText)

    def as_registerResponseS(self, success, message):
        if self._isDAAPIInited():
            return self.flashObject.as_registerResponse(success, message)
# okay decompyling res/scripts/client/gui/scaleform/daapi/view/meta/logincreateanaccountwindowmeta.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:26:25 EST

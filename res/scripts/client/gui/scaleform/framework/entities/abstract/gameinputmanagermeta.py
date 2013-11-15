# 2013.11.15 11:26:27 EST
# Embedded file name: scripts/client/gui/Scaleform/framework/entities/abstract/GameInputManagerMeta.py
from gui.Scaleform.framework.entities.DAAPIModule import DAAPIModule

class GameInputManagerMeta(DAAPIModule):

    def handleGlobalKeyEvent(self, keyCode, eventType):
        self._printOverrideError('handleGlobalKeyEvent')

    def as_addKeyHandlerS(self, keyCode, eventType, ignoreText, cancelEventType):
        if self._isDAAPIInited():
            return self.flashObject.as_addKeyHandler(keyCode, eventType, ignoreText, cancelEventType)

    def as_clearKeyHandlerS(self, keyCode, eventType):
        if self._isDAAPIInited():
            return self.flashObject.as_clearKeyHandler(keyCode, eventType)
# okay decompyling res/scripts/client/gui/scaleform/framework/entities/abstract/gameinputmanagermeta.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:26:27 EST

# 2013.11.15 11:26:25 EST
# Embedded file name: scripts/client/gui/Scaleform/daapi/view/meta/LobbyPageMeta.py
from gui.Scaleform.framework.entities.DAAPIModule import DAAPIModule

class LobbyPageMeta(DAAPIModule):

    def moveSpace(self, x, y, delta):
        self._printOverrideError('moveSpace')

    def as_showHelpLayoutS(self):
        if self._isDAAPIInited():
            return self.flashObject.as_showHelpLayout()

    def as_closeHelpLayoutS(self):
        if self._isDAAPIInited():
            return self.flashObject.as_closeHelpLayout()
# okay decompyling res/scripts/client/gui/scaleform/daapi/view/meta/lobbypagemeta.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:26:25 EST

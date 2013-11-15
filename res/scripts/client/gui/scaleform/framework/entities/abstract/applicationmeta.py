# 2013.11.15 11:26:27 EST
# Embedded file name: scripts/client/gui/Scaleform/framework/entities/abstract/ApplicationMeta.py
from gui.Scaleform.framework.entities.DAAPIModule import DAAPIModule

class ApplicationMeta(DAAPIModule):

    def setLoaderMgr(self, mgr):
        self._printOverrideError('setLoaderMgr')

    def setGlobalVarsMgr(self, mgr):
        self._printOverrideError('setGlobalVarsMgr')

    def setSoundMgr(self, mgr):
        self._printOverrideError('setSoundMgr')

    def setContainerMgr(self, mgr):
        self._printOverrideError('setContainerMgr')

    def setContextMenuMgr(self, mgr):
        self._printOverrideError('setContextMenuMgr')

    def setColorSchemeMgr(self, mgr):
        self._printOverrideError('setColorSchemeMgr')

    def setTooltipMgr(self, mgr):
        self._printOverrideError('setTooltipMgr')

    def setStatsStorage(self, mgr):
        self._printOverrideError('setStatsStorage')

    def setGuiItemsMgr(self, mgr):
        self._printOverrideError('setGuiItemsMgr')

    def setVoiceChatMgr(self, mgr):
        self._printOverrideError('setVoiceChatMgr')

    def setUtilsMgr(self, mgr):
        self._printOverrideError('setUtilsMgr')

    def setGameInputMgr(self, mgr):
        self._printOverrideError('setGameInputMgr')

    def handleGlobalKeyEvent(self, command):
        self._printOverrideError('handleGlobalKeyEvent')

    def as_populateS(self):
        if self._isDAAPIInited():
            return self.flashObject.as_populate()

    def as_disposeS(self):
        if self._isDAAPIInited():
            return self.flashObject.as_dispose()

    def as_registerManagersS(self):
        if self._isDAAPIInited():
            return self.flashObject.as_registerManagers()

    def as_updateStageS(self, w, h):
        if self._isDAAPIInited():
            return self.flashObject.as_updateStage(w, h)
# okay decompyling res/scripts/client/gui/scaleform/framework/entities/abstract/applicationmeta.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:26:27 EST

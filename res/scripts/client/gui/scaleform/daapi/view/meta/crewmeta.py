# Embedded file name: scripts/client/gui/Scaleform/daapi/view/meta/CrewMeta.py
from gui.Scaleform.framework.entities.DAAPIModule import DAAPIModule

class CrewMeta(DAAPIModule):

    def onShowRecruitWindowClick(self, rendererData, menuEnabled):
        self._printOverrideError('onShowRecruitWindowClick')

    def unloadTankman(self, tankmanID):
        self._printOverrideError('unloadTankman')

    def unloadAllTankman(self):
        self._printOverrideError('unloadAllTankman')

    def equipTankman(self, tankmanID, slot):
        self._printOverrideError('equipTankman')

    def openPersonalCase(self, value, tabNumber):
        self._printOverrideError('openPersonalCase')

    def updateTankmen(self):
        self._printOverrideError('updateTankmen')

    def as_tankmenResponseS(self, roles, tankmen):
        if self._isDAAPIInited():
            return self.flashObject.as_tankmenResponse(roles, tankmen)
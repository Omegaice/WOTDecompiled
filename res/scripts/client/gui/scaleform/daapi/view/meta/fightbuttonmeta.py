# Embedded file name: scripts/client/gui/Scaleform/daapi/view/meta/FightButtonMeta.py
from gui.Scaleform.framework.entities.DAAPIModule import DAAPIModule

class FightButtonMeta(DAAPIModule):

    def fightClick(self, mapID, actionName):
        self._printOverrideError('fightClick')

    def fightSelectClick(self, actionName):
        self._printOverrideError('fightSelectClick')

    def demoClick(self):
        self._printOverrideError('demoClick')

    def as_disableFightButtonS(self, isDisabled, toolTip):
        if self._isDAAPIInited():
            return self.flashObject.as_disableFightButton(isDisabled, toolTip)

    def as_setFightButtonS(self, label, menu, fightTypes):
        if self._isDAAPIInited():
            return self.flashObject.as_setFightButton(label, menu, fightTypes)

    def as_setDemonstratorButtonS(self, isVisible):
        if self._isDAAPIInited():
            return self.flashObject.as_setDemonstratorButton(isVisible)
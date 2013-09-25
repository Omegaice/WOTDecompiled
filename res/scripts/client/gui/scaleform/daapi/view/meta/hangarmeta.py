# Embedded file name: scripts/client/gui/Scaleform/daapi/view/meta/HangarMeta.py
from gui.Scaleform.framework.entities.DAAPIModule import DAAPIModule

class HangarMeta(DAAPIModule):

    def onEscape(self):
        self._printOverrideError('onEscape')

    def checkMoney(self):
        self._printOverrideError('checkMoney')

    def showHelpLayout(self):
        self._printOverrideError('showHelpLayout')

    def closeHelpLayout(self):
        self._printOverrideError('closeHelpLayout')

    def as_readyToFightS(self, ready, hangarMessageText, stateLevel, hasVehicle, isSquad, isCrewFull, isInHangar, isBroken):
        if self._isDAAPIInited():
            return self.flashObject.as_readyToFight(ready, hangarMessageText, stateLevel, hasVehicle, isSquad, isCrewFull, isInHangar, isBroken)

    def as_showHelpLayoutS(self):
        if self._isDAAPIInited():
            return self.flashObject.as_showHelpLayout()

    def as_closeHelpLayoutS(self):
        if self._isDAAPIInited():
            return self.flashObject.as_closeHelpLayout()

    def as_setIsIGRS(self, value):
        if self._isDAAPIInited():
            return self.flashObject.as_setIsIGR(value)
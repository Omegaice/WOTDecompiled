# 2013.11.15 11:26:25 EST
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

    def as_readyToFightS(self, ready, hangarMessageText, stateLevel, hasVehicle, isSquad, isCrewFull, isInHangar, isBroken, isDisabledInRoaming):
        if self._isDAAPIInited():
            return self.flashObject.as_readyToFight(ready, hangarMessageText, stateLevel, hasVehicle, isSquad, isCrewFull, isInHangar, isBroken, isDisabledInRoaming)

    def as_showHelpLayoutS(self):
        if self._isDAAPIInited():
            return self.flashObject.as_showHelpLayout()

    def as_closeHelpLayoutS(self):
        if self._isDAAPIInited():
            return self.flashObject.as_closeHelpLayout()

    def as_setIsIGRS(self, value, text):
        if self._isDAAPIInited():
            return self.flashObject.as_setIsIGR(value, text)
# okay decompyling res/scripts/client/gui/scaleform/daapi/view/meta/hangarmeta.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:26:25 EST

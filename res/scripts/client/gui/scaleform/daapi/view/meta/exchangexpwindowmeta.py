# 2013.11.15 11:26:25 EST
# Embedded file name: scripts/client/gui/Scaleform/daapi/view/meta/ExchangeXpWindowMeta.py
from gui.Scaleform.framework.entities.DAAPIModule import DAAPIModule

class ExchangeXpWindowMeta(DAAPIModule):

    def as_vehiclesDataChangedS(self, isHaveElite, data):
        if self._isDAAPIInited():
            return self.flashObject.as_vehiclesDataChanged(isHaveElite, data)

    def as_totalExperienceChangedS(self, value):
        if self._isDAAPIInited():
            return self.flashObject.as_totalExperienceChanged(value)

    def as_setWalletStatusS(self, walletStatus):
        if self._isDAAPIInited():
            return self.flashObject.as_setWalletStatus(walletStatus)
# okay decompyling res/scripts/client/gui/scaleform/daapi/view/meta/exchangexpwindowmeta.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:26:25 EST

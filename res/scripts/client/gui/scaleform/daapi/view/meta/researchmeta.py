# 2013.11.15 11:26:26 EST
# Embedded file name: scripts/client/gui/Scaleform/daapi/view/meta/ResearchMeta.py
from gui.Scaleform.framework.entities.DAAPIModule import DAAPIModule

class ResearchMeta(DAAPIModule):

    def requestNationData(self):
        self._printOverrideError('requestNationData')

    def getResearchItemsData(self, vehCD, rootChanged):
        self._printOverrideError('getResearchItemsData')

    def onResearchItemsDrawn(self):
        self._printOverrideError('onResearchItemsDrawn')

    def request4Install(self, itemCD):
        self._printOverrideError('request4Install')

    def requestModuleInfo(self, pickleDump):
        self._printOverrideError('requestModuleInfo')

    def goToTechTree(self, nation):
        self._printOverrideError('goToTechTree')

    def exitFromResearch(self):
        self._printOverrideError('exitFromResearch')

    def as_drawResearchItemsS(self, nation, vehCD):
        if self._isDAAPIInited():
            return self.flashObject.as_drawResearchItems(nation, vehCD)

    def as_setFreeXPS(self, freeXP):
        if self._isDAAPIInited():
            return self.flashObject.as_setFreeXP(freeXP)

    def as_setInstalledItemsS(self, data):
        if self._isDAAPIInited():
            return self.flashObject.as_setInstalledItems(data)

    def as_setWalletStatusS(self, walletStatus):
        if self._isDAAPIInited():
            return self.flashObject.as_setWalletStatus(walletStatus)
# okay decompyling res/scripts/client/gui/scaleform/daapi/view/meta/researchmeta.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:26:26 EST

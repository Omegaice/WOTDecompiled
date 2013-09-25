from gui.Scaleform.framework.entities.DAAPIModule import DAAPIModule

class TechnicalMaintenanceMeta(DAAPIModule):

    def getEquipment(self, id1, currency1, id2, currency2, id3, currency3, installSlotIndex):
        self._printOverrideError('getEquipment')

    def repair(self):
        self._printOverrideError('repair')

    def setRefillSettings(self, vehicleCompact, repair, shells, equipment):
        self._printOverrideError('setRefillSettings')

    def showModuleInfo(self, moduleId):
        self._printOverrideError('showModuleInfo')

    def fillVehicle(self, needRepair, needAmmo, needEquipment, isPopulate, isUnload, isOrderChanged, shells, equipment):
        self._printOverrideError('fillVehicle')

    def as_setDataS(self, data):
        if self._isDAAPIInited():
            return self.flashObject.as_setData(data)

    def as_setEquipmentS(self, installed, setup, modules):
        if self._isDAAPIInited():
            return self.flashObject.as_setEquipment(installed, setup, modules)

    def as_onAmmoInstallS(self):
        if self._isDAAPIInited():
            return self.flashObject.as_onAmmoInstall()

    def as_setCreditsS(self, credits):
        if self._isDAAPIInited():
            return self.flashObject.as_setCredits(credits)

    def as_setGoldS(self, gold):
        if self._isDAAPIInited():
            return self.flashObject.as_setGold(gold)

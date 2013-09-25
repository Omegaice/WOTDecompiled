import BigWorld
from abc import abstractmethod, ABCMeta
from CurrentVehicle import g_currentVehicle
from debug_utils import LOG_DEBUG
from gui import SystemMessages
from gui.Scaleform.daapi.view.lobby.customization.BaseTimedCustomizationInterface import BaseTimedCustomizationInterface
from gui.Scaleform.daapi.view.lobby.customization.VehicleCustonizationModel import VehicleCustomizationModel
from gui.Scaleform.daapi.view.lobby.customization.data_providers import InscriptionDataProvider, InscriptionRentalPackageDataProvider, InscriptionGroupsDataProvider
from gui.Scaleform.locale.SYSTEM_MESSAGES import SYSTEM_MESSAGES
from gui.shared.utils.HangarSpace import g_hangarSpace
from helpers import time_utils, i18n

class InscriptionInterface(BaseTimedCustomizationInterface):
    __metaclass__ = ABCMeta

    def __init__(self, name, nationId, position):
        super(InscriptionInterface, self).__init__(name, nationId, position)
        self.isTurret = False
        self._isEnabled = False
        self._vehicleLevel = 1
        self._positionShift = 0

    def __del__(self):
        LOG_DEBUG('InscriptionInterface deleted')

    def getCurrentItem(self):
        self.locateCameraOnSlot()
        return super(InscriptionInterface, self).getCurrentItem()

    def isEnabled(self):
        return self._isEnabled

    def locateCameraOnSlot(self):
        res = g_hangarSpace.space.locateCameraOnEmblem(not self.isTurret, 'inscription', self._position - self._positionShift, self.ZOOM_FACTOR)

    def getRealPosition(self):
        if not self.isTurret:
            return self._position - self._positionShift
        return 2 + self._position

    @abstractmethod
    def getRentalPackagesDP(self):
        pass

    @abstractmethod
    def getGroupsDP(self):
        pass

    @abstractmethod
    def getItemsDP(self):
        pass

    def getItemPriceFactor(self, vehType):
        return self._vehicleLevel

    def updateVehicleCustomization(self, itemID = None):
        space = g_hangarSpace.space
        if space is not None and g_currentVehicle.isInHangar():
            VehicleCustomizationModel.updateVehicleSticker('inscription', itemID, self.getRealPosition(), self._rentalPackageDP.selectedPackage.get('periodDays'))
            space.updateVehicleSticker(VehicleCustomizationModel.getVehicleModel())
        return

    def fetchCurrentItem(self, vehDescr):
        if vehDescr is not None:
            self._vehicleLevel = vehDescr.type.level
            slotsCount = self.getSlotsCount(vehDescr.turret, 'inscription')
            self.isTurret = slotsCount > self._position
            if self._position == 1 and slotsCount == 1:
                self._positionShift = 1
            if not self.isTurret:
                slotsCount += self.getSlotsCount(vehDescr.hull, 'inscription')
            self._isEnabled = slotsCount > self._position
            inscription = vehDescr.playerInscriptions[self.getRealPosition()]
            if inscription is not None and inscription[0] is not None:
                self._currentItemID, startTime, days, _ = inscription
                startTime = time_utils.makeLocalServerTime(startTime)
                self._currentLifeCycle = (startTime, days)
        return

    def change(self, vehInvID, section):
        if self._newItemID is None:
            message = i18n.makeString(SYSTEM_MESSAGES.CUSTOMIZATION_INSCRIPTION_NOT_SELECTED)
            self.onCustomizationChangeFailed(message)
            return
        elif self._rentalPackageDP.selectedPackage is None:
            message = i18n.makeString(SYSTEM_MESSAGES.CUSTOMIZATION_INSCRIPTION_DAYS_NOT_SELECTED)
            self.onCustomizationChangeFailed(message)
            return
        else:
            cost, isGold = self._itemsDP.getCost(self._newItemID)
            if cost < 0:
                message = i18n.makeString(SYSTEM_MESSAGES.CUSTOMIZATION_INSCRIPTION_COST_NOT_FOUND)
                self.onCustomizationChangeFailed(message)
                return
            BigWorld.player().inventory.changeVehicleInscription(vehInvID, self.getRealPosition(), self._newItemID, self._rentalPackageDP.selectedPackage.get('periodDays'), 1, lambda resultID: self.__onChangeVehicleInscription(resultID, (cost, isGold)))
            return

    def drop(self, vehInvID, kind):
        if self._currentItemID is None:
            message = i18n.makeString(SYSTEM_MESSAGES.CUSTOMIZATION_INSCRIPTION_NOT_FOUND_TO_DROP)
            self.onCustomizationDropFailed(message)
            return
        else:
            BigWorld.player().inventory.changeVehicleInscription(vehInvID, self.getRealPosition(), 0, 0, 1, self.__onDropVehicleInscription)
            return

    def update(self, vehicleDescr):
        inscription = vehicleDescr.playerInscriptions[self.getRealPosition()]
        inscriptionID = inscription[0] if inscription is not None else None
        if inscriptionID != self._currentItemID:
            self._currentItemID = inscriptionID
            self._itemsDP.currentItemID = self._currentItemID
            if inscription is not None:
                _, startTime, days, colorId = inscription
                startTime = time_utils.makeLocalServerTime(startTime)
                self._currentLifeCycle = (startTime, days)
            else:
                self._currentLifeCycle = None
            self.onCurrentItemChange(self._name)
        return

    def _populate(self):
        super(InscriptionInterface, self)._populate()

    def _dispose(self):
        super(InscriptionInterface, self)._dispose()

    def __onChangeVehicleInscription(self, resultID, price):
        if resultID < 0:
            message = i18n.makeString(SYSTEM_MESSAGES.CUSTOMIZATION_INSCRIPTION_CHANGE_SERVER_ERROR)
            self.onCustomizationChangeFailed(message)
            return
        else:
            self._currentItemID = self._newItemID
            self._currentLifeCycle = None
            self._newItemID = None
            self._itemsDP.currentItemID = self._currentItemID
            cost, isGold = price
            if isGold:
                key = SYSTEM_MESSAGES.CUSTOMIZATION_INSCRIPTION_CHANGE_SUCCESS_GOLD
                fCost = BigWorld.wg_getGoldFormat(cost)
                type = SystemMessages.SM_TYPE.CustomizationForGold
            else:
                key = SYSTEM_MESSAGES.CUSTOMIZATION_INSCRIPTION_CHANGE_SUCCESS_CREDITS
                fCost = BigWorld.wg_getIntegralFormat(cost)
                type = SystemMessages.SM_TYPE.CustomizationForCredits
            str = i18n.makeString(key, fCost)
            self.onCustomizationChangeSuccess(str, type)
            return

    def __onDropVehicleInscription(self, resultID):
        if resultID < 0:
            message = i18n.makeString(SYSTEM_MESSAGES.CUSTOMIZATION_INSCRIPTION_DROP_SERVER_ERROR)
            self.onCustomizationDropFailed(message)
            return
        else:
            self._currentItemID = None
            self._currentLifeCycle = None
            self._itemsDP.currentItemID = None
            message = i18n.makeString(SYSTEM_MESSAGES.CUSTOMIZATION_INSCRIPTION_DROP_SUCCESS)
            self.onCustomizationDropSuccess(message)
            return


class InscriptionLeftInterface(InscriptionInterface):

    def getItemsDP(self):
        dp = InscriptionDataProvider(self._nationID)
        dp.setFlashObject(self.flashObject.inscriptionLeftDP)
        return dp

    def getRentalPackagesDP(self):
        dp = InscriptionRentalPackageDataProvider(self._nationID)
        dp.setFlashObject(self.flashObject.inscriptionLeftRentalPackageDP)
        return dp

    def getGroupsDP(self):
        dp = InscriptionGroupsDataProvider(self._nationID)
        dp.setFlashObject(self.flashObject.inscriptionLeftGroupsDataProvider)
        return dp


class InscriptionRightInterface(InscriptionInterface):

    def getItemsDP(self):
        dp = InscriptionDataProvider(self._nationID)
        dp.setFlashObject(self.flashObject.inscriptionRightDP)
        return dp

    def getRentalPackagesDP(self):
        dp = InscriptionRentalPackageDataProvider(self._nationID)
        dp.setFlashObject(self.flashObject.inscriptionRightRentalPackageDP)
        return dp

    def getGroupsDP(self):
        dp = InscriptionGroupsDataProvider(self._nationID)
        dp.setFlashObject(self.flashObject.inscriptionRightGroupsDataProvider)
        return dp

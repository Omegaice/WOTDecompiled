# 2013.11.15 11:25:59 EST
# Embedded file name: scripts/client/gui/Scaleform/daapi/view/lobby/customization/EmblemInterface.py
import BigWorld
from abc import abstractmethod, ABCMeta
import time
from CurrentVehicle import g_currentVehicle
from debug_utils import LOG_DEBUG
from gui import SystemMessages
from gui.Scaleform.daapi.view.lobby.customization.BaseTimedCustomizationInterface import BaseTimedCustomizationInterface
from gui.Scaleform.daapi.view.lobby.customization.VehicleCustonizationModel import VehicleCustomizationModel
from gui.Scaleform.daapi.view.lobby.customization.data_providers import EmblemsDataProvider, EmblemRentalPackageDataProvider, EmblemGroupsDataProvider
from gui.Scaleform.framework import AppRef
from gui.Scaleform.locale.SYSTEM_MESSAGES import SYSTEM_MESSAGES
from gui.shared.utils.HangarSpace import g_hangarSpace
from helpers import time_utils, i18n

class EmblemInterface(BaseTimedCustomizationInterface, AppRef):
    __metaclass__ = ABCMeta

    def __init__(self, name, nationId, position):
        super(EmblemInterface, self).__init__(name, nationId, position)
        self.defaultPlayerEmblemID = None
        self.isTurret = False
        self._isEnabled = False
        self._vehicleLevel = 1
        self._positionShift = 0
        return

    def __del__(self):
        LOG_DEBUG('EmblemInterface deleted')

    def getCurrentItem(self):
        self.locateCameraOnSlot()
        item = super(EmblemInterface, self).getCurrentItem()
        if self.defaultPlayerEmblemID == item.get('id'):
            item['canDrop'] = False
        return item

    def isEnabled(self):
        if self.app.varsManager.isInRoaming():
            return False
        return self._isEnabled

    def locateCameraOnSlot(self):
        res = g_hangarSpace.space.locateCameraOnEmblem(not self.isTurret, 'player', self._position - self._positionShift, self.ZOOM_FACTOR)
        LOG_DEBUG('EmblemLeftInterface g_hangarSpace.space.locateCameraOnEmblem', self._position, res)

    def getRealPosition(self):
        if not self.isTurret:
            return self._position - self._positionShift
        return self._position + 2

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
            VehicleCustomizationModel.updateVehicleSticker('player', itemID, self.getRealPosition(), self._rentalPackageDP.selectedPackage.get('periodDays'))
            space.updateVehicleSticker(VehicleCustomizationModel.getVehicleModel())
        return

    def fetchCurrentItem(self, vehDescr):
        if vehDescr is not None:
            self._vehicleLevel = vehDescr.type.level
            slotsCount = self.getSlotsCount(vehDescr.turret, 'player')
            self.isTurret = slotsCount > self._position
            if self._position == 1 and slotsCount == 1:
                self._positionShift = 1
            if not self.isTurret:
                slotsCount += self.getSlotsCount(vehDescr.hull, 'player')
            self._isEnabled = slotsCount > self._position
            self.defaultPlayerEmblemID = vehDescr.type.defaultPlayerEmblemID
            emblem = vehDescr.playerEmblems[self.getRealPosition()]
            if emblem is not None:
                self._currentItemID, startTime, days = emblem
                startTime = time_utils.makeLocalServerTime(startTime)
                self._currentLifeCycle = (startTime, days)
        return

    def change(self, vehInvID, section):
        if self._newItemID is None:
            message = i18n.makeString(SYSTEM_MESSAGES.CUSTOMIZATION_EMBLEM_NOT_SELECTED)
            self.onCustomizationChangeFailed(message)
            return
        elif self._rentalPackageDP.selectedPackage is None:
            message = i18n.makeString(SYSTEM_MESSAGES.CUSTOMIZATION_EMBLEM_DAYS_NOT_SELECTED)
            self.onCustomizationChangeFailed(message)
            return
        else:
            cost, isGold = self._itemsDP.getCost(self._newItemID)
            if cost < 0:
                message = i18n.makeString(SYSTEM_MESSAGES.CUSTOMIZATION_EMBLEM_COST_NOT_FOUND)
                self.onCustomizationChangeFailed(message)
                return
            BigWorld.player().inventory.changeVehicleEmblem(vehInvID, self.getRealPosition(), self._newItemID, self._rentalPackageDP.selectedPackage.get('periodDays'), lambda resultID: self.__onChangeVehicleEmblem(resultID, (cost, isGold)))
            return

    def drop(self, vehInvID, kind):
        if self._currentItemID is None:
            message = i18n.makeString(SYSTEM_MESSAGES.CUSTOMIZATION_EMBLEM_NOT_FOUND_TO_DROP)
            self.onCustomizationDropFailed(message)
            return
        else:
            BigWorld.player().inventory.changeVehicleEmblem(vehInvID, self.getRealPosition(), 0, 0, self.__onDropVehicleEmblem)
            return

    def update(self, vehicleDescr):
        emblem = vehicleDescr.playerEmblems[self.getRealPosition()]
        emblemID = emblem[0] if emblem is not None else None
        if emblemID != self._currentItemID:
            self._currentItemID = emblemID
            self._itemsDP.currentItemID = self._currentItemID
            if emblem is not None:
                _, startTime, days = emblem
                startTime = time_utils.makeLocalServerTime(startTime)
                self._currentLifeCycle = (startTime, days)
            else:
                self._currentLifeCycle = None
            self.onCurrentItemChange(self._name)
        return

    def _populate(self):
        super(EmblemInterface, self)._populate()

    def _dispose(self):
        super(EmblemInterface, self)._dispose()

    def __onChangeVehicleEmblem(self, resultID, price):
        if resultID < 0:
            message = i18n.makeString(SYSTEM_MESSAGES.CUSTOMIZATION_EMBLEM_CHANGE_SERVER_ERROR)
            self.onCustomizationChangeFailed(message)
            return
        else:
            self._currentItemID = self._newItemID
            self._currentLifeCycle = (round(time.time()), 0)
            self._newItemID = None
            self._itemsDP.currentItemID = self._currentItemID
            cost, isGold = price
            if isGold:
                key = SYSTEM_MESSAGES.CUSTOMIZATION_EMBLEM_CHANGE_SUCCESS_GOLD
                fCost = BigWorld.wg_getGoldFormat(cost)
                type = SystemMessages.SM_TYPE.CustomizationForGold
            else:
                key = SYSTEM_MESSAGES.CUSTOMIZATION_EMBLEM_CHANGE_SUCCESS_CREDITS
                fCost = BigWorld.wg_getIntegralFormat(cost)
                type = SystemMessages.SM_TYPE.CustomizationForCredits
            str = i18n.makeString(key, fCost)
            self.onCustomizationChangeSuccess(str, type)
            return

    def __onDropVehicleEmblem(self, resultID):
        if resultID < 0:
            message = i18n.makeString(SYSTEM_MESSAGES.CUSTOMIZATION_EMBLEM_DROP_SERVER_ERROR)
            self.onCustomizationDropFailed(message)
            return
        else:
            self._currentItemID = self.defaultPlayerEmblemID
            self._currentLifeCycle = None
            self._itemsDP.currentItemID = self.defaultPlayerEmblemID
            message = i18n.makeString(SYSTEM_MESSAGES.CUSTOMIZATION_EMBLEM_DROP_SUCCESS)
            self.onCustomizationDropSuccess(message)
            self.onCurrentItemChange(self._name)
            return


class EmblemLeftInterface(EmblemInterface):

    def getItemsDP(self):
        dp = EmblemsDataProvider()
        dp.setFlashObject(self.flashObject.emblemLeftDP)
        return dp

    def getRentalPackagesDP(self):
        dp = EmblemRentalPackageDataProvider(self._nationID)
        dp.setFlashObject(self.flashObject.emblemLeftRentalPackageDP)
        return dp

    def getGroupsDP(self):
        dp = EmblemGroupsDataProvider()
        dp.setFlashObject(self.flashObject.emblemLeftGroupsDataProvider)
        return dp


class EmblemRightInterface(EmblemInterface):

    def getItemsDP(self):
        dp = EmblemsDataProvider()
        dp.setFlashObject(self.flashObject.emblemRightDP)
        return dp

    def getRentalPackagesDP(self):
        dp = EmblemRentalPackageDataProvider(self._nationID)
        dp.setFlashObject(self.flashObject.emblemRightRentalPackageDP)
        return dp

    def getGroupsDP(self):
        dp = EmblemGroupsDataProvider()
        dp.setFlashObject(self.flashObject.emblemRightGroupsDataProvider)
        return dp
# okay decompyling res/scripts/client/gui/scaleform/daapi/view/lobby/customization/embleminterface.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:25:59 EST

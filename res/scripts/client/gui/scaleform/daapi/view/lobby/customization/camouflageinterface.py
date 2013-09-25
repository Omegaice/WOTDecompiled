# Embedded file name: scripts/client/gui/Scaleform/daapi/view/lobby/customization/CamouflageInterface.py
import BigWorld
import functools
from datetime import timedelta
from math import ceil
import time
from CurrentVehicle import g_currentVehicle
from debug_utils import LOG_DEBUG
from gui import SystemMessages, g_tankActiveCamouflage
from gui.Scaleform.daapi.view.lobby.customization.BaseTimedCustomizationInterface import BaseTimedCustomizationInterface
from gui.Scaleform.daapi.view.lobby.customization.data_providers import CamouflageGroupsDataProvider, CamouflagesDataProvider, CamouflageRentalPackageDataProvider
from gui.Scaleform.locale.MENU import MENU
from gui.Scaleform.locale.SYSTEM_MESSAGES import SYSTEM_MESSAGES
from gui.shared.utils.HangarSpace import g_hangarSpace
from helpers import i18n, time_utils
from items.vehicles import CAMOUFLAGE_KINDS

class CamouflageInterface(BaseTimedCustomizationInterface):

    def __init__(self, name, nationId, position):
        super(CamouflageInterface, self).__init__(name, nationId, position)
        self.currentItemsByKind = {}
        self.indexToKind = {}
        self.resetCurrentItems()

    def resetCurrentItems(self):
        for k, v in CAMOUFLAGE_KINDS.iteritems():
            self.setCurrentItem(v, None, None, None, None)
            self.indexToKind[v] = k

        return

    def setCurrentItem(self, kindIdx, ID, lifeCycle, newItemID, packageIdx):
        self.currentItemsByKind[kindIdx] = {'id': ID,
         'lifeCycle': lifeCycle,
         'newItemID': newItemID,
         'packageIdx': packageIdx}

    def __del__(self):
        LOG_DEBUG('CamouflageInterface deleted')

    def getRentalPackagesDP(self):
        dp = CamouflageRentalPackageDataProvider(self._nationID)
        dp.setFlashObject(self.flashObject.camouflageRentalPackageDP)
        return dp

    def getGroupsDP(self):
        dp = CamouflageGroupsDataProvider(self._nationID)
        dp.setFlashObject(self.flashObject.camouflageGroupsDataProvider)
        return dp

    def getItemsDP(self):
        dp = CamouflagesDataProvider(self._nationID)
        dp.setFlashObject(self.flashObject.camouflageDP)
        return dp

    def getItemPriceFactor(self, vehType):
        return vehType.camouflagePriceFactor

    def invalidateViewData(self, vehType, refresh = False):
        if vehType is not None:
            self._groupsDP.buildList()
            self._itemsDP.setVehicleTypeParams(self.getItemPriceFactor(vehType), self.currentItemsByKind.get(0, {'id': None}).get('id'))
        self._rentalPackageDP.getRentalPackages(refresh)
        return

    def isNewItemSelected(self):
        return self.getSelectedItemsCount() > 0

    def getSelectedItemCost(self):
        newItemsCosts = [ self.getItemCost(item.get('newItemID'), item.get('packageIdx')) for kind, item in self.currentItemsByKind.iteritems() if item.get('newItemID') is not None ]
        return newItemsCosts

    def getSelectedItemsCount(self, *args):
        if len(args):
            newItems = []
            for kind, item in self.currentItemsByKind.iteritems():
                if item.get('newItemID') is not None:
                    cost = self.getItemCost(item.get('newItemID'), item.get('packageIdx'))
                    if cost.get('isGold') == args[0]:
                        newItems.append(item)

        else:
            newItems = [ item for kind, item in self.currentItemsByKind.iteritems() if item.get('newItemID') is not None ]
        return len(newItems)

    def isCurrentItemRemove(self):
        currentItems = [ item for kind, item in self.currentItemsByKind.iteritems() if item.get('id') is not None and item.get('newItemID') is not None ]
        return len(currentItems) > 0

    def getCurrentItem(self):
        space = g_hangarSpace.space
        if space is not None:
            space.locateCameraToPreview()
        items = []
        for key, item in self.currentItemsByKind.iteritems():
            items.append(self._itemsDP.makeItem(item.get('id'), True, item.get('lifeCycle'), self._makeTimeLeftString(item=item), key))

        return items

    def onSetID(self, itemID, kind, packageIdx):
        item = self.currentItemsByKind.get(kind)
        if item.get('id') == itemID:
            item['newItemID'] = None
        else:
            item['newItemID'] = itemID
        item['packageIdx'] = packageIdx
        self.updateVehicleCustomization(itemID)
        return

    def _onRentalPackagesDataInited(self, selectedPackage, refresh):
        if selectedPackage:
            self._itemsDP.setDefaultCost(selectedPackage.get('cost'), selectedPackage.get('isGold'))
        if refresh:
            for kind, item in self.currentItemsByKind.iteritems():
                item['newItemID'] = None

            self._rentalPackageDP.refresh()
            self._itemsDP.refresh()
        LOG_DEBUG('CamouflageInterface data inited', self._name)
        self.onDataInited(self._name)
        return

    def _makeTimeLeftString(self, **kwargs):
        result = ''
        item = kwargs.get('item')
        if item.get('lifeCycle') is not None:
            startTime, days = item.get('lifeCycle')
            if days > 0:
                timeLeft = startTime + days * 86400 - time.time()
                if timeLeft > 0:
                    delta = timedelta(0, timeLeft)
                    if delta.days > 0:
                        result = i18n.makeString(MENU.CUSTOMIZATION_LABELS_CAMOUFLAGE_TIMELEFT_DAYS, delta.days + 1 if delta.seconds > 0 else delta.days)
                    else:
                        result = i18n.makeString(MENU.CUSTOMIZATION_LABELS_CAMOUFLAGE_TIMELEFT_HOURS, ceil(delta.seconds / 3600.0))
        return result

    def updateVehicleCustomization(self, itemID = None):
        space = g_hangarSpace.space
        if space is not None and g_currentVehicle.isInHangar():
            space.updateVehicleCamouflage(camouflageID=itemID)
        return

    def fetchCurrentItem(self, vehDescr):
        if vehDescr is not None:
            camouflages = vehDescr.camouflages
            if camouflages is not None:
                for camouflage in camouflages:
                    itemId, startTime, days = camouflage
                    if itemId is not None:
                        lifeCycle = None if itemId is None else (time_utils.makeLocalServerTime(startTime), days)
                        camouflageObject = self._itemsDP.getCamouflageDescr(itemId)
                        self.setCurrentItem(camouflageObject.get('kind'), itemId, lifeCycle, None, self._rentalPackageDP.getIndexByDays(days))

        return

    def change(self, vehInvID, section):
        if self._rentalPackageDP.selectedPackage is None:
            message = i18n.makeString(SYSTEM_MESSAGES.CUSTOMIZATION_CAMOUFLAGE_DAYS_NOT_SELECTED)
            self.onCustomizationChangeFailed(message)
            return
        else:
            isNewItemFound = False
            for kind, item in self.currentItemsByKind.iteritems():
                if item.get('newItemID', None) is None:
                    continue
                elif not isNewItemFound:
                    isNewItemFound = True
                price = self.getItemCost(item.get('newItemID'), item.get('packageIdx'))
                if price.get('cost') < 0:
                    message = i18n.makeString(SYSTEM_MESSAGES.CUSTOMIZATION_CAMOUFLAGE_COST_NOT_FOUND)
                    self.onCustomizationChangeFailed(message)
                    return
                localKind = kind
                pricePackage = self._rentalPackageDP.pyRequestItemAt(item.get('packageIdx'))
                BigWorld.player().inventory.changeVehicleCamouflage(vehInvID, localKind, item.get('newItemID'), pricePackage.get('periodDays'), functools.partial(self.__onChangeVehicleCamouflage, (price.get('cost'), price.get('isGold')), localKind))

            if not isNewItemFound:
                message = i18n.makeString(SYSTEM_MESSAGES.CUSTOMIZATION_CAMOUFLAGE_NOT_SELECTED)
                self.onCustomizationChangeFailed(message)
            return

    def drop(self, vehInvID, kind):
        if self.currentItemsByKind.get(kind) is None:
            message = i18n.makeString(SYSTEM_MESSAGES.CUSTOMIZATION_CAMOUFLAGE_NOT_FOUND_TO_DROP)
            self.onCustomizationDropFailed(message)
            return
        else:
            BigWorld.player().inventory.changeVehicleCamouflage(vehInvID, kind, 0, 0, lambda resultID: self.__onDropVehicleCamouflage(resultID, kind))
            return

    def update(self, vehicleDescr):
        camouflages = vehicleDescr.camouflages
        isUpdated = False
        for index, camouflage in enumerate(camouflages):
            camouflageID = camouflage[0] if camouflage is not None else None
            item = self.currentItemsByKind[index]
            if camouflageID != item.get('id'):
                isUpdated = True
                item['id'] = camouflageID
                if camouflage is not None:
                    _, startTime, days = camouflage
                    startTime = time_utils.makeLocalServerTime(startTime)
                    item['lifeCycle'] = (startTime, days)
                else:
                    item['lifeCycle'] = None
                if CAMOUFLAGE_KINDS.get(self._itemsDP.currentGroup) == index:
                    self._itemsDP.currentItemID = item['id']

        if isUpdated:
            self.onCurrentItemChange(self._name)
        return

    def _populate(self):
        super(CamouflageInterface, self)._populate()

    def _dispose(self):
        if self.isNewItemSelected():
            self.updateVehicleCustomization()
        self.resetCurrentItems()
        super(CamouflageInterface, self)._dispose()

    def __onChangeVehicleCamouflage(self, price, kind, resultID):
        if resultID < 0:
            message = i18n.makeString(SYSTEM_MESSAGES.CUSTOMIZATION_CAMOUFLAGE_CHANGE_SERVER_ERROR)
            self.onCustomizationChangeFailed(message)
            return
        else:
            item = self.currentItemsByKind.get(kind)
            g_tankActiveCamouflage[g_currentVehicle.item.intCD] = kind
            item['id'] = item.get('newItemID')
            item['lifeCycle'] = None
            item['newItemID'] = None
            if CAMOUFLAGE_KINDS.get(self._itemsDP.currentGroup) == kind:
                self._itemsDP.currentItemID = item['id']
            cost, isGold = price
            if isGold:
                key = SYSTEM_MESSAGES.CUSTOMIZATION_CAMOUFLAGE_CHANGE_SUCCESS_GOLD
                fCost = BigWorld.wg_getGoldFormat(cost)
                typeValue = SystemMessages.SM_TYPE.CustomizationForGold
            else:
                key = SYSTEM_MESSAGES.CUSTOMIZATION_CAMOUFLAGE_CHANGE_SUCCESS_CREDITS
                fCost = BigWorld.wg_getIntegralFormat(cost)
                typeValue = SystemMessages.SM_TYPE.CustomizationForCredits
            str = i18n.makeString(key, fCost)
            self.onCustomizationChangeSuccess(str, typeValue)
            return

    def __onDropVehicleCamouflage(self, resultID, kind):
        if resultID < 0:
            message = i18n.makeString(SYSTEM_MESSAGES.CUSTOMIZATION_CAMOUFLAGE_DROP_SERVER_ERROR)
            self.onCustomizationDropFailed(message)
            return
        else:
            item = self.currentItemsByKind.get(kind)
            if g_tankActiveCamouflage.has_key(g_currentVehicle.item.intCD):
                del g_tankActiveCamouflage[g_currentVehicle.item.intCD]
            item['id'] = None
            item['lifeCycle'] = None
            if CAMOUFLAGE_KINDS.get(self._itemsDP.currentGroup) == kind:
                self._itemsDP.currentItemID = None
            message = i18n.makeString(SYSTEM_MESSAGES.CUSTOMIZATION_CAMOUFLAGE_DROP_SUCCESS)
            self.onCustomizationDropSuccess(message)
            return
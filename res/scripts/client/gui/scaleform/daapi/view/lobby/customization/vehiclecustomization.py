# Embedded file name: scripts/client/gui/Scaleform/daapi/view/lobby/customization/VehicleCustomization.py
import gui
from CurrentVehicle import g_currentVehicle
from PlayerEvents import g_playerEvents
from adisp import process
from debug_utils import LOG_ERROR
from gui import SystemMessages, DialogsInterface
from gui.ClientUpdateManager import g_clientUpdateManager
from gui.Scaleform.Waiting import Waiting
from gui.Scaleform.daapi.view.lobby.customization.VehicleCustonizationModel import VehicleCustomizationModel
from gui.Scaleform.daapi.view.lobby.customization import _VEHICLE_CUSTOMIZATIONS
from gui.Scaleform.daapi.view.meta.VehicleCustomizationMeta import VehicleCustomizationMeta
from gui.Scaleform.framework import AppRef
from gui.Scaleform.daapi.view.dialogs import I18nConfirmDialogMeta, I18nInfoDialogMeta
from gui.Scaleform.framework.entities.View import View
from gui.Scaleform.locale.SYSTEM_MESSAGES import SYSTEM_MESSAGES
from gui.shared import events
from gui.shared.event_bus import EVENT_BUS_SCOPE
from gui.shared.utils.HangarSpace import g_hangarSpace
from gui.shared.utils.requesters import StatsRequester
from helpers import i18n
from items import vehicles
from items.vehicles import VehicleDescr

class VehicleCustomization(VehicleCustomizationMeta, View, AppRef):

    def __init__(self):
        super(VehicleCustomization, self).__init__()
        self.__interfaces = {}
        self.__prevCameraLocation = None
        self.__steps = 0
        self.__messages = []
        self.__credits = 0
        self.__gold = 0
        self.__returnHangar = False
        self.__lockUpdate = False
        self.__onceDataInited = False
        return

    def getInterface(self, section):
        return self.__interfaces.get(section)

    @process
    def _populate(self):
        View._populate(self)
        credits = yield StatsRequester().getCredits()
        gold = yield StatsRequester().getGold()
        self.as_setCreditsS(credits)
        self.as_setGoldS(gold)
        g_clientUpdateManager.addCallbacks({'stats.gold': self.onGoldUpdate,
         'stats.credits': self.onCreditsUpdate,
         'account.attrs': self.onCameraUpdate,
         'inventory.1.compDescr': self.onVehiclesUpdate})
        g_playerEvents.onShopResync += self.__pe_onShopResync
        g_currentVehicle.onChanged += self.__cv_onChanged
        vehDescr = None
        vehType = None
        if g_currentVehicle.isPresent():
            vehDescr = g_currentVehicle.item.descriptor
            vehType = vehDescr.type
            VehicleCustomizationModel.setVehicleDescriptor(vehDescr)
        self.__steps = len(_VEHICLE_CUSTOMIZATIONS)
        for customization in _VEHICLE_CUSTOMIZATIONS:
            sectionName = customization['sectionName']
            interface = customization['interface'](sectionName, vehDescr.type.id[0], customization['position'])
            interface.onDataInited += self.__ci_onDataInited
            interface.onCustomizationChangeSuccess += self.__ci_onCustomizationChangeSuccess
            interface.onCustomizationChangeFailed += self.__ci_onCustomizationChangeFailed
            interface.onCustomizationDropSuccess += self.__ci_onCustomizationDropSuccess
            interface.onCustomizationDropFailed += self.__ci_onCustomizationDropFailed
            interface.onCurrentItemChange += self.__ci_onCurrentItemChanged
            self.__interfaces[sectionName] = interface
            interface.setFlashObject(self.flashObject, setScript=False)
            interface.fetchCurrentItem(vehDescr)
            interface.invalidateViewData(vehType)

        if not self.__steps:
            self.__finishInitData()
        return

    def _dispose(self):
        self.__resetPreviewMode()
        for interface in self.__interfaces.itervalues():
            interface.destroy()
            interface.onDataInited -= self.__ci_onDataInited
            interface.onCustomizationChangeSuccess -= self.__ci_onCustomizationChangeSuccess
            interface.onCustomizationChangeFailed -= self.__ci_onCustomizationChangeFailed
            interface.onCustomizationDropSuccess -= self.__ci_onCustomizationDropSuccess
            interface.onCustomizationDropFailed -= self.__ci_onCustomizationDropFailed
            interface.onCurrentItemChange -= self.__ci_onCurrentItemChanged

        self.__interfaces.clear()
        self.__onceDataInited = False
        g_playerEvents.onShopResync -= self.__pe_onShopResync
        g_currentVehicle.onChanged -= self.__cv_onChanged
        g_clientUpdateManager.removeObjectCallbacks(self)
        View._dispose(self)

    def __onServerResponsesReceived(self):
        self.as_onServerResponsesReceivedS()
        self.__lockUpdate = False
        Waiting.hide('customizationApply')
        for type, message in self.__messages:
            SystemMessages.pushMessage(message, type=type)

        self.__messages = []
        if self.__returnHangar:
            self.closeWindow()

    def __finishInitData(self):
        if not self.__onceDataInited:
            self.__requestMoney()
            self.as_onInitS(self._getSections())
            if g_currentVehicle.isLocked() or g_currentVehicle.isBroken():
                self.as_setActionsLockedS(True)
            self.__setPreviewMode()
            self.__onceDataInited = True

    @process
    def __requestMoney(self):
        self.__credits = yield StatsRequester().getCredits()
        self.__gold = yield StatsRequester().getGold()

    def _getSections(self):
        res = []
        for customization in _VEHICLE_CUSTOMIZATIONS:
            res.append({'sectionName': customization['sectionName'],
             'sectionLabel': customization['sectionUserString'],
             'priceLabel': customization['priceUserString'],
             'linkage': customization['linkage'],
             'enabled': self.getInterface(customization['sectionName']).isEnabled()})

        return res

    def __setPreviewMode(self):
        space = g_hangarSpace.space
        if space is not None:
            self.__prevCameraLocation = space.getCameraLocation()
            space.locateCameraToPreview()
        else:
            LOG_ERROR("ClientHangarSpace isn't initialized")
        return

    def __resetPreviewMode(self):
        space = g_hangarSpace.space
        if space is not None and self.__prevCameraLocation is not None:
            space.setCameraLocation(**self.__prevCameraLocation)
            space.clearSelectedEmblemInfo()
        return

    def closeWindow(self):
        self.fireEvent(events.LoadEvent(events.LoadEvent.LOAD_HANGAR), scope=EVENT_BUS_SCOPE.LOBBY)

    def __ci_onDataInited(self, _):
        self.__steps -= 1
        if not self.__steps:
            self.__finishInitData()

    def __ci_onCustomizationChangeFailed(self, message):
        self.__returnHangar = False
        self.__messages.append((SystemMessages.SM_TYPE.Error, message))
        self.__steps -= 1
        if not self.__steps:
            self.__onServerResponsesReceived()

    def __ci_onCustomizationChangeSuccess(self, message, type):
        self.as_onChangeSuccessS()
        self.__messages.append((type, message))
        self.__steps -= 1
        if not self.__steps:
            self.__onServerResponsesReceived()

    def __ci_onCustomizationDropFailed(self, message):
        Waiting.hide('customizationDrop')
        self.__lockUpdate = False
        SystemMessages.pushMessage(message, type=SystemMessages.SM_TYPE.Error)

    def __ci_onCurrentItemChanged(self, section):
        self.as_onCurrentChangedS(section)

    def __ci_onCustomizationDropSuccess(self, message):
        self.as_onDropSuccessS()
        Waiting.hide('customizationDrop')
        self.__lockUpdate = False
        SystemMessages.pushMessage(message, type=SystemMessages.SM_TYPE.Information)

    def onGoldUpdate(self, value):
        self.__gold = value
        self.as_setGoldS(value)

    def onCreditsUpdate(self, value):
        self.__credits = value
        self.as_setCreditsS(value)

    def onCameraUpdate(self, *args):
        self.__prevCameraLocation.update({'yaw': None,
         'pitch': None})
        return

    def onVehiclesUpdate(self, vehicles):
        if vehicles is None or self.__lockUpdate:
            return
        else:
            vehCompDescr = vehicles.get(g_currentVehicle.invID)
            if vehCompDescr is not None:
                vehDescr = VehicleDescr(compactDescr=vehCompDescr)
                for interface in self.__interfaces.itervalues():
                    interface.update(vehDescr)

            return

    def __pe_onShopResync(self):
        if not g_currentVehicle.isPresent():
            return
        self.__steps = len(_VEHICLE_CUSTOMIZATIONS)
        vehType = vehicles.g_cache.vehicle(*g_currentVehicle.item.descriptor.type.id)
        self.as_onResetNewItemS()
        for interface in self.__interfaces.itervalues():
            interface.invalidateViewData(vehType, refresh=True)

    def __cv_onChanged(self):
        if not g_currentVehicle.isReadyToFight():
            if g_currentVehicle.isCrewFull() and not g_currentVehicle.isBroken():
                self.closeWindow()
        else:
            self.as_setActionsLockedS(g_currentVehicle.isLocked() or g_currentVehicle.isBroken())

    def setNewItemId(self, section, itemId, kind, packageIdx):
        interface = self.__interfaces.get(section)
        if interface is not None:
            interface.onSetID(int(itemId), int(kind), int(packageIdx))
        return

    def getCurrentItem(self, section):
        interface = self.__interfaces.get(section)
        if interface is not None:
            return interface.getCurrentItem()
        else:
            return
            return

    def getItemCost(self, section, itemId, priceIndex):
        interface = self.__interfaces.get(section)
        if interface is not None:
            return interface.getItemCost(itemId, priceIndex)
        else:
            return
            return

    @process
    def applyCustomization(self, sections):
        if g_currentVehicle.isLocked():
            SystemMessages.pushI18nMessage(SYSTEM_MESSAGES.CUSTOMIZATION_VEHICLE_LOCKED, type=SystemMessages.SM_TYPE.Error)
            yield lambda callback = None: callback
        if g_currentVehicle.isBroken():
            SystemMessages.pushI18nMessage(SYSTEM_MESSAGES.customization_vehicle(g_currentVehicle.item.getState()), type=SystemMessages.SM_TYPE.Error)
            yield lambda callback = None: callback
        notSelected = []
        selected = []
        remove = []
        selectedNames = []
        totalGold = 0
        totalCredits = 0
        for section in sections:
            interface = self.__interfaces.get(section.sectionName)
            if interface is not None:
                if interface.isNewItemSelected():
                    costValue = interface.getSelectedItemCost()
                    if type(costValue) is list:
                        for price in costValue:
                            cost = price.get('cost')
                            isGold = price.get('isGold')
                            if cost > 0:
                                if isGold and section.isGold:
                                    totalGold += cost
                                elif not isGold and not section.isGold:
                                    totalCredits += cost

                    else:
                        cost, isGold = costValue
                        if cost > 0:
                            if isGold:
                                totalGold += cost
                            else:
                                totalCredits += cost
                    if section.sectionName not in selectedNames:
                        selected.append(i18n.makeString('#menu:customization/change/{0:>s}'.format(section.sectionName)))
                        selectedNames.append(section.sectionName)
                    if interface.isCurrentItemRemove():
                        remove.append(gui.makeHtmlString('html_templates:lobby/customization', 'remove-{0:>s}'.format(section.sectionName)))
                else:
                    notSelected.append(i18n.makeString('#menu:customization/items/{0:>s}'.format(section.sectionName)))
            else:
                LOG_ERROR('Section not found', section.sectionName)

        if len(notSelected) > 0:
            DialogsInterface.showI18nInfoDialog('customization/selectNewItems', lambda success: None, I18nInfoDialogMeta('customization/selectNewItems', messageCtx={'items': ', '.join(notSelected)}))
            yield lambda callback = None: callback
        creditsNotEnough = totalCredits > self.__credits
        goldNotEnough = totalGold > self.__gold
        if creditsNotEnough or goldNotEnough:
            if creditsNotEnough and goldNotEnough:
                key = SYSTEM_MESSAGES.CUSTOMIZATION_CREDITS_AND_GOLD_NOT_ENOUGH
            elif goldNotEnough:
                key = SYSTEM_MESSAGES.CUSTOMIZATION_GOLD_NOT_ENOUGH
            else:
                key = SYSTEM_MESSAGES.CUSTOMIZATION_CREDITS_NOT_ENOUGH
            SystemMessages.pushI18nMessage(key, type=SystemMessages.SM_TYPE.Error)
            yield lambda callback = None: callback
        isConfirmed = yield DialogsInterface.showDialog(I18nConfirmDialogMeta('customization/changeConfirmation', messageCtx={'selected': ', '.join(selected),
         'remove': '\n'.join(remove)}))
        if isConfirmed:
            self.__returnHangar = True
            vehInvID = g_currentVehicle.invID
            self.__steps = 0
            self.__messages = []
            self.flashObject.applyButton.disabled = True
            if len(sections) > 0:
                Waiting.show('customizationApply')
                self.__lockUpdate = True
            selectedNames = []
            for section in sections:
                interface = self.__interfaces.get(section.sectionName)
                if interface is not None:
                    self.__steps += interface.getSelectedItemsCount(section.isGold)
                    if section.sectionName not in selectedNames:
                        interface.change(vehInvID, section)
                        selectedNames.append(section.sectionName)
                else:
                    LOG_ERROR('Change operation, section not found', section)
                    self.__steps -= 1

            if not self.__steps:
                self.__onServerResponsesReceived()
        return

    @process
    def dropCurrentItemInSection(self, section, kind):
        if g_currentVehicle.isLocked():
            SystemMessages.pushI18nMessage(SYSTEM_MESSAGES.CUSTOMIZATION_VEHICLE_LOCKED, type=SystemMessages.SM_TYPE.Error)
            return
        elif g_currentVehicle.isBroken():
            SystemMessages.pushI18nMessage(SYSTEM_MESSAGES.customization_vehicle(g_currentVehicle.item.getState()), type=SystemMessages.SM_TYPE.Error)
            return
        else:
            dialog = 'customization/{0:>s}Drop'.format(section)
            isConfirmed = yield DialogsInterface.showI18nConfirmDialog(dialog)
            if isConfirmed:
                interface = self.__interfaces.get(section)
                if interface is not None:
                    self.__returnHangar = False
                    self.__lockUpdate = True
                    Waiting.show('customizationDrop')
                    interface.drop(g_currentVehicle.invID, kind)
                else:
                    LOG_ERROR('Drop operation, section not found', section)
            return
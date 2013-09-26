from CurrentVehicle import g_currentVehicle
from adisp import process
from debug_utils import LOG_DEBUG, LOG_ERROR
from gui import SystemMessages
from gui.Scaleform.Waiting import Waiting
from gui.Scaleform.daapi.view.meta.AmmunitionPanelMeta import AmmunitionPanelMeta
from gui.Scaleform.framework import AppRef
from gui.shared.event_bus import EVENT_BUS_SCOPE
from gui.shared.gui_items import GUI_ITEM_TYPE
from gui.shared.gui_items.processors.module import ModuleBuyer, getInstallerProcessor
from gui.shared.utils import gui_items, EXTRA_MODULE_INFO, CLIP_ICON_PATH
from gui.shared.utils.functions import isModuleFitVehicle, findConflictedEquipmentForModule
from gui.shared.utils.requesters import Requester, VehicleItemsRequester, AvailableItemsRequester, StatsRequester, ShopRequester
from gui.shared import events, g_itemsCache
from gui.shared.events import ShowWindowEvent, LoadEvent, LobbySimpleEvent
from gui.Scaleform.locale.MENU import MENU
from gui.Scaleform.locale.ITEM_TYPES import ITEM_TYPES
from items import ITEM_TYPE_NAMES

class AmmunitionPanel(AmmunitionPanelMeta, AppRef):
    __FITTING_SLOTS = (ITEM_TYPE_NAMES[2],
     ITEM_TYPE_NAMES[3],
     ITEM_TYPE_NAMES[4],
     ITEM_TYPE_NAMES[5],
     ITEM_TYPE_NAMES[7],
     ITEM_TYPE_NAMES[9],
     ITEM_TYPE_NAMES[11])
    __ARTEFACTS_SLOTS = (ITEM_TYPE_NAMES[9], ITEM_TYPE_NAMES[11])

    def _populate(self):
        super(AmmunitionPanel, self)._populate()
        self.update()

    def update(self):
        self.__updateAmmo()
        if g_currentVehicle.isPresent():
            self.as_setVehicleHasTurretS(g_currentVehicle.item.hasTurrets)
            self.__requestsCount = len(AmmunitionPanel.__FITTING_SLOTS)
            for type in AmmunitionPanel.__FITTING_SLOTS:
                self.__requestAvailableItems(type)

    def __getModuleInventoryAndVehicleCounts(self, vehiclesModules, inventoryModules, module, type):
        invCount, vehCount = (0, 0)
        try:
            invCount = inventoryModules[inventoryModules.index(module)].count
            vehCount = vehiclesModules[vehiclesModules.index(module)].count
        except Exception:
            pass

        return (invCount, vehCount)

    @process
    def __updateAmmo(self):
        Waiting.show('updateAmmo')
        credits = yield StatsRequester().getCredits()
        shopRqs = yield ShopRequester().request()
        ammo = {'gunName': '',
         'maxAmmo': 0,
         'reserved1': False,
         'reserved2': False,
         'defaultAmmoCount': 0,
         'reserved3': 0,
         'vehicleLocked': True,
         'stateMsg': False,
         'stateLevel': False,
         'shells': []}
        if g_currentVehicle.isPresent():
            vehicle = g_currentVehicle.item
            default_ammo_count = 0
            default_ammo = dict(((s.intCD, s.defaultCount) for s in vehicle.shells))
            for compactDescr, count in default_ammo.iteritems():
                default_ammo_count += count

            msg, msgLvl = g_currentVehicle.getHangarMessage()
            ammo.update({'gunName': vehicle.gun.longUserName,
             'maxAmmo': vehicle.gun.descriptor['maxAmmo'],
             'reserved1': not g_currentVehicle.isLocked(),
             'reserved2': not g_currentVehicle.isBroken(),
             'defaultAmmoCount': default_ammo_count,
             'reserved3': 0,
             'vehicleLocked': g_currentVehicle.isLocked(),
             'stateMsg': msg,
             'stateLevel': msgLvl})
            iAmmo = yield Requester('shell').getFromInventory()
            sAmmo = yield Requester('shell').getFromShop()
            iVehicles = yield Requester('vehicle').getFromInventory()
            oldStyleVehicle = None
            for v in iVehicles:
                if v.inventoryId == vehicle.invID:
                    oldStyleVehicle = v
                    break

            shells = ammo.get('shells')
            for shell in oldStyleVehicle.shells:
                shopShell = sAmmo[sAmmo.index(shell)] if shell in sAmmo else None
                goldAmmoForCredits = shopRqs.isEnabledBuyingGoldShellsForCredits
                if shopShell:
                    iCount = iAmmo[iAmmo.index(shell)].count if shell in iAmmo else 0
                    sPrice = (yield shopShell.getPrice()) if shell is not shopShell else (0, 0)
                    if goldAmmoForCredits:
                        shopShell.priceOrder = (sPrice[0] + sPrice[1] * shopRqs.exchangeRateForShellsAndEqs, sPrice[1])
                    buyCount = max(shell.default - iCount - shell.count, 0)
                    shells.append({'id': gui_items.compactItem(shopShell),
                     'type': shell.type,
                     'label': ITEM_TYPES.shell_kindsabbreviation(shell.type),
                     'icon': '../maps/icons/ammopanel/ammo/%s' % shell.descriptor['icon'][0],
                     'count': shell.count,
                     'defaultCount': shell.default,
                     'inventoryCount': iCount,
                     'price': sPrice[0 if not sPrice[1] else 1],
                     'currentcy': 'credits' if not sPrice[1] else 'gold',
                     'ammoName': shell.longName,
                     'tableName': shell.tableName})

        self.as_setAmmoS(ammo)
        Waiting.hide('updateAmmo')

    @process
    def __requestAvailableItems(self, type):
        myVehicles = yield Requester('vehicle').getFromInventory()
        modulesAllVehicle = VehicleItemsRequester(myVehicles).getItems([type])
        oldStyleVehicle = None
        for v in myVehicles:
            if v.inventoryId == g_currentVehicle.invID:
                oldStyleVehicle = v
                break

        newStyleVehicle = g_currentVehicle.item
        modulesAllInventory = yield Requester(type).getFromInventory()
        data = yield AvailableItemsRequester(oldStyleVehicle, type).request()
        if type in AmmunitionPanel.__ARTEFACTS_SLOTS:
            unlocks = [ m for m in data if m.isCurrent ]
        else:
            unlocks = yield StatsRequester().getUnlocks()
        data.sort(reverse=True)
        if type in AmmunitionPanel.__ARTEFACTS_SLOTS:
            dataProvider = [[], [], []]
        else:
            dataProvider = []
        credits = yield StatsRequester().getCredits()
        gold = yield StatsRequester().getGold()
        for module in data:
            price = yield module.getPrice()
            inventoryCount, vehicleCount = self.__getModuleInventoryAndVehicleCounts(modulesAllVehicle, modulesAllInventory, module, type)
            moduleData = {'id': gui_items.compactItem(module),
             'type': type,
             'name': module.name if type in AmmunitionPanel.__ARTEFACTS_SLOTS else module.longName,
             'desc': module.getTableName(oldStyleVehicle),
             'target': 2 if type == ITEM_TYPE_NAMES[3] and not oldStyleVehicle.hasTurrets else module.target,
             'price': price[0] if price[1] == 0 else price[1],
             'currency': 'credits' if price[1] == 0 else 'gold',
             'icon': module.icon if type in AmmunitionPanel.__ARTEFACTS_SLOTS else module.level,
             'inventoryCount': inventoryCount,
             'vehicleCount': vehicleCount}
            if type == ITEM_TYPE_NAMES[4]:
                if module.isClipGun(oldStyleVehicle.descriptor):
                    moduleData[EXTRA_MODULE_INFO] = CLIP_ICON_PATH
            if type in AmmunitionPanel.__ARTEFACTS_SLOTS:
                moduleData['removable'] = module.isRemovable
                moduleData['slotIndex'] = module.index
                for i in xrange(3):
                    md = moduleData.copy()
                    fits = isModuleFitVehicle(module, newStyleVehicle, price, (credits, gold), unlocks, i)
                    if md.get('target') == 1:
                        md['status'] = MENU.MODULEFITS_WRONG_SLOT if i != md.get('slotIndex') else fits[1]
                        md['isSelected'] = i == md.get('slotIndex')
                    else:
                        md['status'] = fits[1]
                        md['isSelected'] = False
                    md['slotIndex'] = md['slotIndex'] or i
                    dataProvider[i].append(md)

            else:
                fits = isModuleFitVehicle(module, newStyleVehicle, price, (credits, gold), unlocks)
                moduleData['removable'] = True
                moduleData['isSelected'] = moduleData.get('target') == 1
                moduleData['status'] = fits[1]
                dataProvider.append(moduleData)

        self.as_setDataS(dataProvider, type)

    def showTechnicalMaintenance(self):
        self.fireEvent(ShowWindowEvent(ShowWindowEvent.SHOW_TECHNICAL_MAINTENANCE))

    def showCustomization(self):
        self.fireEvent(LoadEvent(LoadEvent.LOAD_CUSTOMIZATION), EVENT_BUS_SCOPE.LOBBY)

    def highlightParams(self, type):
        self.fireEvent(LobbySimpleEvent(LobbySimpleEvent.HIGHLIGHT_TANK_PARAMS, {'type': type}), EVENT_BUS_SCOPE.LOBBY)

    def showModuleInfo(self, moduleId):
        if moduleId is None:
            LOG_ERROR('There is error while attempting to show module info window: ', str(moduleId))
        else:
            self.fireEvent(events.ShowWindowEvent(events.ShowWindowEvent.SHOW_MODULE_INFO_WINDOW, {'moduleId': moduleId,
             'vehicleDescr': g_currentVehicle.item.descriptor}))

    @process
    def setVehicleModule(self, newId, slotIdx, oldId, isRemove):
        if isRemove:
            isUseGold = oldId is not None
            newComponent = gui_items.getItemByCompact(newId)
            newComponentItem = g_itemsCache.items.getItemByCD(newComponent.compactDescr)
            if newComponentItem is None:
                pass
        else:
            oldComponentItem = None
            if oldId:
                oldComponent = gui_items.getItemByCompact(oldId)
                oldComponentItem = g_itemsCache.items.getItemByCD(oldComponent.compactDescr)
            if not isRemove and oldComponentItem and oldComponentItem.itemTypeID == GUI_ITEM_TYPE.OPTIONALDEVICE:
                result = yield getInstallerProcessor(g_currentVehicle.item, oldComponentItem, slotIdx, False, True).request()
                if result and result.auxData:
                    for m in result.auxData:
                        SystemMessages.g_instance.pushI18nMessage(m.userMsg, type=m.sysMsgType)

                if result and len(result.userMsg):
                    SystemMessages.g_instance.pushI18nMessage(result.userMsg, type=result.sysMsgType)
                if not result.success:
                    pass
            iVehicles = yield Requester(ITEM_TYPE_NAMES[1]).getFromInventory()
            oldStyleVehicle = None
            for v in iVehicles:
                if v.inventoryId == g_currentVehicle.invID:
                    oldStyleVehicle = v
                    break

            conflictedEqs = findConflictedEquipmentForModule(newComponent, oldStyleVehicle)
            if isinstance(newComponent, gui_items.ShopItem):
                Waiting.show('buyItem')
                buyResult = yield ModuleBuyer(newComponentItem, count=1, buyForCredits=True, conflictedEqs=conflictedEqs, install=True).request()
                if len(buyResult.userMsg):
                    SystemMessages.g_instance.pushI18nMessage(buyResult.userMsg, type=buyResult.sysMsgType)
                if buyResult.success:
                    newComponentItem = g_itemsCache.items.getItemByCD(newComponent.compactDescr)
                Waiting.hide('buyItem')
                if not buyResult.success:
                    pass
            Waiting.show('applyModule')
            result = yield getInstallerProcessor(g_currentVehicle.item, newComponentItem, slotIdx, not isRemove, isUseGold, conflictedEqs).request()
            if result and result.auxData:
                for m in result.auxData:
                    SystemMessages.g_instance.pushI18nMessage(m.userMsg, type=m.sysMsgType)

            if result and len(result.userMsg):
                SystemMessages.g_instance.pushI18nMessage(result.userMsg, type=result.sysMsgType)
            if result and result.success and newComponentItem.itemTypeID in (GUI_ITEM_TYPE.TURRET, GUI_ITEM_TYPE.GUN):
                iAmmo = yield Requester(ITEM_TYPE_NAMES[10]).getFromInventory()
                iVehicles = yield Requester(ITEM_TYPE_NAMES[1]).getFromInventory()
                for iVehicle in iVehicles:
                    if iVehicle.inventoryId == g_currentVehicle.invID:
                        installAmmoVehicle = iVehicle

                for shell in installAmmoVehicle.shells:
                    iCount = iAmmo[iAmmo.index(shell)].count if shell in iAmmo else 0
                    if shell.default > iCount:
                        success, message = False, '#system_messages:charge/inventory_error'
                        break
                else:
                    success, message = yield installAmmoVehicle.loadShells(None)

                SystemMessages.g_instance.pushI18nMessage(message, type=SystemMessages.SM_TYPE.Information if success else SystemMessages.SM_TYPE.Warning)
            Waiting.hide('applyModule')

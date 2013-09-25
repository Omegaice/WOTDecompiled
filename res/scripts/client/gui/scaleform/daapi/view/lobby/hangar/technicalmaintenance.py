# Embedded file name: scripts/client/gui/Scaleform/daapi/view/lobby/hangar/TechnicalMaintenance.py
from AccountCommands import LOCK_REASON
from CurrentVehicle import g_currentVehicle
from PlayerEvents import g_playerEvents
from debug_utils import LOG_ERROR, LOG_DEBUG
from gui import SystemMessages, DialogsInterface
from gui.ClientUpdateManager import g_clientUpdateManager
from gui.Scaleform.daapi.view.meta.TechnicalMaintenanceMeta import TechnicalMaintenanceMeta
from gui.Scaleform.daapi.view.meta.WindowViewMeta import WindowViewMeta
from gui.Scaleform.framework.entities.View import View
from gui.Scaleform.daapi.view.dialogs import I18nConfirmDialogMeta
from gui.shared.gui_items.processors.vehicle import VehicleLayoutProcessor
from gui.shared.utils import decorators
from gui.shared.utils.functions import getShortDescr, isModuleFitVehicle
from gui.shared.utils.gui_items import getVehicleFullName, VehicleItem, compactItem, getItemByCompact, InventoryItem
from gui.shared.utils.requesters import StatsRequester, Requester, ShopRequester, StatsRequesterr, AvailableItemsRequester, VehicleItemsRequester
from gui.shared import events
from helpers import i18n
from helpers.i18n import makeString

class TechnicalMaintenance(View, TechnicalMaintenanceMeta, WindowViewMeta):

    def __init__(self):
        super(TechnicalMaintenance, self).__init__()
        self.__currentVehicleId = None
        return

    def onCancelClick(self):
        self.destroy()

    def onWindowClose(self):
        self.destroy()

    def _populate(self):
        super(View, self)._populate()
        g_playerEvents.onShopResync += self._onShopResync
        g_clientUpdateManager.addCallbacks({'stats.credits': self.onCreditsChange,
         'stats.gold': self.onGoldChange})
        g_currentVehicle.onChanged += self.__onCurrentVehicleChanged
        if g_currentVehicle.isPresent():
            self.__currentVehicleId = g_currentVehicle.invID
        self.populateTechnicalMaintenance()
        self.populateTechnicalMaintenanceEquipmentDefaults()

    def _dispose(self):
        g_playerEvents.onShopResync -= self._onShopResync
        g_clientUpdateManager.removeObjectCallbacks(self)
        g_currentVehicle.onChanged -= self.__onCurrentVehicleChanged
        super(View, self)._dispose()

    def onCreditsChange(self, credits):
        self.as_setCreditsS(credits)

    def onGoldChange(self, gold):
        self.as_setGoldS(gold)

    def _onShopResync(self):
        self.populateTechnicalMaintenance()

    def getEquipment(self, eId1, currency1, eId2, currency2, eId3, currency3, slotIndex):
        eIdsCD = []
        for item in [ getItemByCompact(x) for x in (eId1, eId2, eId3) ]:
            if item is None:
                eIdsCD.append(None)
            else:
                eIdsCD.append(item.compactDescr)

        self.populateTechnicalMaintenanceEquipment(eIdsCD[0], currency1, eIdsCD[1], currency2, eIdsCD[2], currency3, slotIndex)
        return

    @decorators.process('loadStats')
    def setRefillSettings(self, vehicleCompact, repair, shells, equipment):
        vcls = yield Requester('vehicle').getFromInventory()
        vehicle = getItemByCompact(vehicleCompact)
        for v in vcls:
            if v.inventoryId == vehicle.inventoryId:
                vehicle = v

        if vehicle.isAutoRepair != repair:
            yield vehicle.setAutoRepair(repair)
        if vehicle.isAutoLoad != shells:
            yield vehicle.setAutoLoad(shells)
        if vehicle.isAutoEquip != equipment:
            yield vehicle.setAutoEquip(equipment)

    def showModuleInfo(self, moduleId):
        if moduleId is None:
            return LOG_ERROR('There is error while attempting to show module info window: ', str(moduleId))
        else:
            self.fireEvent(events.ShowWindowEvent(events.ShowWindowEvent.SHOW_MODULE_INFO_WINDOW, {'moduleId': moduleId,
             'vehicleDescr': g_currentVehicle.item.descriptor}))
            return

    @decorators.process('techMaintenance')
    def populateTechnicalMaintenance(self):
        shopRqs = yield ShopRequester().request()
        statsRqs = yield StatsRequesterr().request()
        goldShellsForCredits = shopRqs.isEnabledBuyingGoldShellsForCredits
        data = {'gold': statsRqs.gold,
         'credits': statsRqs.credits}
        if g_currentVehicle.isPresent():
            iVehicles = yield Requester('vehicle').getFromInventory()
            for v in iVehicles:
                if v.inventoryId == g_currentVehicle.invID:
                    vehicle = v
                    break

            gun = VehicleItem(vehicle.descriptor.gun)
            iAmmo = yield Requester('shell').getFromInventory()
            sAmmo = yield Requester('shell').getFromShop()
            casseteCount = vehicle.descriptor.gun['clip'][0]
            data.update({'vehicleId': vehicle.pack(),
             'repairCost': vehicle.repairCost,
             'maxRepairCost': vehicle.descriptor.getMaxRepairCost(),
             'autoRepair': vehicle.isAutoRepair,
             'maxAmmo': gun.descriptor['maxAmmo'],
             'casseteFieldText': '' if casseteCount == 1 else makeString('#menu:technicalMaintenance/ammoTitleEx') % casseteCount,
             'shells': []})
            shells = data.get('shells')
            for shell in vehicle.shells:
                shopShell = sAmmo[sAmmo.index(shell)] if shell in sAmmo else None
                if shopShell:
                    iCount = iAmmo[iAmmo.index(shell)].count if shell in iAmmo else 0
                    sPrice = (yield shopShell.getPrice()) if shell is not shopShell else (0, 0)
                    if goldShellsForCredits:
                        sPrice = (sPrice[0] + sPrice[1] * shopRqs.exchangeRateForShellsAndEqs, sPrice[1])
                    priceCurrency = 'gold'
                    if sPrice[1] == 0 or goldShellsForCredits and shell.boughtForCredits:
                        priceCurrency = 'credits'
                    buyCount = max(shell.default - iCount - shell.count, 0)
                    shells.append({'id': compactItem(shopShell),
                     'compactDescr': shopShell.compactDescr,
                     'type': shell.type,
                     'icon': '../maps/icons/ammopanel/ammo/%s' % shell.descriptor['icon'][0],
                     'count': shell.count,
                     'userCount': shell.default,
                     'step': casseteCount,
                     'inventoryCount': iCount,
                     'goldShellsForCredits': goldShellsForCredits,
                     'prices': list(sPrice)[:2],
                     'currency': priceCurrency,
                     'ammoName': shell.longName,
                     'tableName': shell.tableName,
                     'maxAmmo': gun.descriptor['maxAmmo']})

            data.update({'autoShells': vehicle.isAutoLoad,
             'autoEqip': vehicle.isAutoEquip})
        self.as_setDataS(data)
        return

    def populateTechnicalMaintenanceEquipmentDefaults(self):
        """
        Loads layout and sets equipment according to it as a default
        """
        params = {}
        for i, e in enumerate(g_currentVehicle.item.eqsLayout):
            params['eId%s' % (i + 1)] = e.intCD if e else None

        self.populateTechnicalMaintenanceEquipment(**params)
        return

    @decorators.process('techMaintenance')
    def populateTechnicalMaintenanceEquipment(self, eId1 = None, currency1 = None, eId2 = None, currency2 = None, eId3 = None, currency3 = None, slotIndex = None):
        shopRqs = yield ShopRequester().request()
        goldEqsForCredits = shopRqs.isEnabledBuyingGoldEqsForCredits
        gold = yield StatsRequester().getGold()
        credits = yield StatsRequester().getCredits()
        myVehicles = yield Requester('vehicle').getFromInventory()
        modulesAllVehicle = VehicleItemsRequester(myVehicles).getItems(['equipment'])
        oldStyleVehicle = None
        for v in myVehicles:
            if v.inventoryId == g_currentVehicle.invID:
                oldStyleVehicle = v
                break

        newStyleVehicle = g_currentVehicle.item
        availableData = yield AvailableItemsRequester(oldStyleVehicle, 'equipment').request()
        shopEqs = yield Requester('equipment').getFromShop()
        invEqs = yield Requester('equipment').getFromInventory()
        eqs = oldStyleVehicle.equipmentsLayout

        def getShopModule(module):
            for eq in shopEqs:
                if eq == module:
                    return eq

            return None

        def getInventoryModule(module):
            for eq in invEqs:
                if eq == module:
                    return eq

            return None

        def getModuleByCD(compactDescr):
            for eq in availableData:
                if eq.compactDescr == compactDescr:
                    return eq

            return None

        installed = [ m for m in availableData if m.isCurrent ]
        currencies = [None, None, None]
        if eId1 is not None or eId2 is not None or eId3 is not None or slotIndex is not None:
            installed = [ getModuleByCD(id) for id in (eId1, eId2, eId3) if id is not None ]
            currencies = [currency1, currency2, currency3]
        data = []
        for item in availableData:
            if item in installed:
                invEq = getInventoryModule(item)
                shopModule = getShopModule(item)
                i = InventoryItem(itemTypeName='equipment', compactDescr=item.compactDescr, count=invEq.count if invEq is not None else 0, priceOrder=shopModule.priceOrder if shopModule is not None else (0, 0))
                if item == getModuleByCD(eId1):
                    i.index = 0
                elif item == getModuleByCD(eId2):
                    i.index = 1
                elif item == getModuleByCD(eId3):
                    i.index = 2
                else:
                    i.index = item.index
                i.isCurrent = True
            elif isinstance(item, InventoryItem):
                i = InventoryItem(itemTypeName='equipment', compactDescr=item.compactDescr, count=item.count, priceOrder=item.priceOrder)
            else:
                i = item
            data.append(i)

        unlocks = [ m for m in data if m.isCurrent ]
        data.sort(reverse=True)
        installed = [0, 0, 0]
        for m in availableData:
            if m.isCurrent:
                installed[m.index] = m.compactDescr

        setup = [0, 0, 0]
        modules = []
        if len(eqs):
            setup = eqs
        for module in data:
            vehCount = 0
            try:
                vehCount = modulesAllVehicle[modulesAllVehicle.index(module)].count
            except Exception:
                pass

            invCount = 0
            try:
                invCount = invEqs[invEqs.index(module)].count
            except Exception:
                pass

            shopModule = getShopModule(module)
            price = (yield shopModule.getPrice()) if shopModule is not None else (0, 0)
            if goldEqsForCredits:
                price = (price[0] + price[1] * shopRqs.exchangeRateForShellsAndEqs, price[1])
            priceCurrency = 'gold'
            if not price[1]:
                priceCurrency = 'credits'
            elif goldEqsForCredits and module.index is not None:
                if module.index < len(eqs) and eqs[module.index] < 0:
                    priceCurrency = 'credits'
                elif currencies[module.index] is not None:
                    priceCurrency = currencies[module.index]
            fits = []
            for i in xrange(3):
                fits.append(isModuleFitVehicle(module, newStyleVehicle, price, (credits, gold), unlocks, i)[1])

            modules.append({'id': compactItem(module),
             'name': module.name,
             'desc': getShortDescr(module.getTableName(oldStyleVehicle)),
             'target': module.target,
             'compactDescr': module.compactDescr,
             'prices': list(price)[:2],
             'currency': priceCurrency,
             'icon': module.icon,
             'index': module.index,
             'inventoryCount': invCount,
             'vehicleCount': vehCount,
             'count': module.count if isinstance(module, InventoryItem) else 0,
             'fits': fits,
             'goldEqsForCredits': goldEqsForCredits})

        self.as_setEquipmentS(installed, setup, modules)
        return

    @decorators.process('updateMyVehicles')
    def repair(self):
        myVehicles = yield Requester('vehicle').getFromInventory()
        oldStyleVehicle = None
        for v in myVehicles:
            if v.inventoryId == g_currentVehicle.invID:
                oldStyleVehicle = v
                break

        if oldStyleVehicle.repairCost > 0:
            success, message = yield oldStyleVehicle.repair()
            SystemMessages.g_instance.pushMessage(message, SystemMessages.SM_TYPE.Repair if success else SystemMessages.SM_TYPE.Error)
        return

    def fillVehicle(self, needRepair, needAmmo, needEquipment, isPopulate, isUnload, isOrderChanged, shells, equipment):
        if not needRepair and not needAmmo and not needEquipment and not isPopulate and not isUnload and not isOrderChanged:
            self.__fillTechnicalMaintenance(shells, equipment)
        else:
            msgPrefix = '{0}'
            if needRepair:
                msgPrefix = msgPrefix.format('_repair{0}')
            if isPopulate:
                msgPrefix = msgPrefix.format('_populate')
            elif isUnload:
                msgPrefix = msgPrefix.format('_unload')
            elif isOrderChanged:
                msgPrefix = msgPrefix.format('_order_change')
            else:
                msgPrefix = msgPrefix.format('')
            msg = i18n.makeString(''.join(['#dialogs:technicalMaintenanceConfirm/msg', msgPrefix]))

            def fillConfirmationCallback(isConfirmed):
                if isConfirmed:
                    if needRepair:
                        self.repair()
                    self.__fillTechnicalMaintenance(shells, equipment)

            DialogsInterface.showDialog(I18nConfirmDialogMeta('technicalMaintenanceConfirm', messageCtx={'content': msg}), fillConfirmationCallback)

    def __onCurrentVehicleChanged(self):
        if g_currentVehicle.isLocked() or not g_currentVehicle.isPresent():
            self.destroy()
        else:
            self.populateTechnicalMaintenance()
            if g_currentVehicle.isPresent() and g_currentVehicle.invID != self.__currentVehicleId:
                self.populateTechnicalMaintenanceEquipmentDefaults()
                self.__currentVehicleId = g_currentVehicle.invID

    def __fillTechnicalMaintenance(self, ammo, equipment):
        shellsLayout = []
        eqsLayout = []
        for shell in ammo:
            buyGoldShellForCredits = shell.goldShellsForCredits and shell.prices[1] > 0 and shell.currency == 'credits'
            shellsLayout.append(shell.compactDescr if not buyGoldShellForCredits else -shell.compactDescr)
            shellsLayout.append(int(shell.userCount))

        for ei in equipment:
            if ei is not None:
                item = getItemByCompact(ei.id)
                buyGoldEqForCredits = ei.goldEqsForCredits and ei.prices[1] > 0 and ei.currency == 'credits'
                eqsLayout.append(item.compactDescr if not buyGoldEqForCredits else -item.compactDescr)
                eqsLayout.append(1)
            else:
                eqsLayout.append(0)
                eqsLayout.append(0)

        self.__setVehicleLayouts(g_currentVehicle.item, shellsLayout, eqsLayout)
        return

    @decorators.process('techMaintenance')
    def __setVehicleLayouts(self, vehicle, shellsLayout = list(), eqsLayout = list()):
        LOG_DEBUG('setVehicleLayouts', shellsLayout, eqsLayout)
        result = yield VehicleLayoutProcessor(vehicle, shellsLayout, eqsLayout).request()
        if result and result.auxData:
            for m in result.auxData:
                SystemMessages.g_instance.pushI18nMessage(m.userMsg, type=m.sysMsgType)

        if result and len(result.userMsg):
            SystemMessages.g_instance.pushI18nMessage(result.userMsg, type=result.sysMsgType)
        self.destroy()
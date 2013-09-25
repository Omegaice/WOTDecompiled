from account_helpers.AccountSettings import AccountSettings
import constants
from debug_utils import LOG_ERROR, LOG_DEBUG
from gui import getNationIndex, DialogsInterface
from gui.ClientUpdateManager import g_clientUpdateManager
from gui.Scaleform.Waiting import Waiting
from gui.Scaleform.daapi.view.dialogs.ConfirmModuleMeta import SellModuleMeta
from gui.Scaleform.daapi.view.meta.InventoryMeta import InventoryMeta
from gui.Scaleform.daapi.view.lobby.store import Store
from gui.Scaleform.genConsts.STORE_TYPES import STORE_TYPES
from gui.Scaleform.locale.MENU import MENU
from gui.shared.events import ShowWindowEvent
from gui.shared.utils import CLIP_ICON_PATH, EXTRA_MODULE_INFO
from gui.shared import g_itemsCache
from gui.shared.utils.gui_items import InventoryVehicle, VehicleItem
from adisp import process
from gui.shared.utils.functions import getShortDescr
from gui.shared.utils.gui_items import getItemByCompact, compactItem
from gui.shared.utils.requesters import Requester, VehicleItemsRequester, _getComponentsByType, StatsRequester, ShopRequester, StatsRequesterr
from helpers.i18n import makeString
from items import ITEM_TYPE_INDICES
from items import vehicles
import nations
__author__ = 'd_trofimov'

class Inventory(Store, InventoryMeta):

    def __init__(self):
        super(Inventory, self).__init__()
        self.__tableData = []

    def _populate(self):
        g_clientUpdateManager.addCallbacks({'': self._onTableUpdate})
        super(Inventory, self)._populate()

    def getName(self):
        return STORE_TYPES.INVENTORY

    def _dispose(self):
        super(Inventory, self)._dispose()
        self.__clearTableData()

    def __clearTableData(self):
        while len(self.__tableData):
            obj = self.__tableData.pop()
            if type(obj) is not str:
                obj.clear()

        self.__tableData = None
        return

    def _update(self, diff = {}):
        self.as_updateS()

    @process
    def __sellItem(self, itemTypeCompactDescr):
        isOk, args = yield DialogsInterface.showDialog(SellModuleMeta(itemTypeCompactDescr))
        LOG_DEBUG('Sell module confirm dialog results', isOk, args)

    def sellItem(self, data):
        item = getItemByCompact(data.id)
        if ITEM_TYPE_INDICES[item.itemTypeName] == vehicles._VEHICLE:
            self.fireEvent(ShowWindowEvent(ShowWindowEvent.SHOW_VEHICLE_SELL_DIALOG, {'vehInvID': int(item.inventoryId)}))
        else:
            self.__sellItem(item.compactDescr)

    @process
    def requestTableData(self, nation, type, filter):
        Waiting.show('updateInventory')
        AccountSettings.setFilter('inventory_current', (nation, type))
        AccountSettings.setFilter('inventory_' + type, filter)
        nation = int(nation) if nation >= 0 else None
        if nation is not None:
            nation = getNationIndex(nation)
        filter = list(filter)
        requestType = [type]
        checkFits = None
        checkFitsArtefacts = None
        checkExtra = False
        modulesFits = {}
        vehicleFits = []
        extra = []
        modulesAllVehicle = []
        if type == self._MODULE:
            typeSize = int(filter.pop(0))
            requestType = filter[0:typeSize]
            filter = filter[typeSize:]
            fitsType = filter.pop(0)
            fitsVehicle = getItemByCompact(filter.pop(0))
            checkExtra = True
            extra = filter[:]
            checkFits = True if fitsType != 'otherVehicles' else False
            myVehicles = yield Requester(self._VEHICLE).getFromInventory()
            modulesAllVehicle = VehicleItemsRequester(myVehicles).getItems(requestType)
            if fitsType == 'myVehicle':
                if fitsVehicle:
                    for rType in requestType:
                        modulesFits.update(_getComponentsByType(fitsVehicle, ITEM_TYPE_INDICES[rType]))

            else:
                for vehicle in myVehicles:
                    for rType in requestType:
                        modulesFits.update(_getComponentsByType(vehicle, ITEM_TYPE_INDICES[rType]))

            filter = requestType
        elif type == self._SHELL:
            filterSize = int(filter.pop(0))
            fitsType = filter.pop(filterSize)
            fitsVehicle = getItemByCompact(filter.pop(filterSize))
            checkFits = True if fitsType != 'otherGuns' else False
            if fitsType == 'myVehicleGun':
                for shoot in fitsVehicle.descriptor.gun['shots']:
                    modulesFits[shoot[self._SHELL]['compactDescr']] = True

            elif fitsType == 'myInventoryGuns':
                myGuns = yield Requester('vehicleGun').getFromInventory()
                for gun in myGuns:
                    for shoot in gun.descriptor['shots']:
                        modulesFits[shoot[self._SHELL]['compactDescr']] = True

            else:
                myGuns = yield Requester('vehicleGun').getFromInventory()
                for gun in myGuns:
                    for shoot in gun.descriptor['shots']:
                        modulesFits[shoot[self._SHELL]['compactDescr']] = True

                myVehicles = yield Requester(self._VEHICLE).getFromInventory()
                for vehicle in myVehicles:
                    for shoot in vehicle.descriptor.gun['shots']:
                        modulesFits[shoot[self._SHELL]['compactDescr']] = True

        elif type == self._VEHICLE:
            filterSize = int(filter.pop(0))
            extra = filter[filterSize:]
            checkExtra = True
            filter = filter[0:filterSize]
        else:
            fitsType = filter.pop(0)
            compact = filter.pop(0)
            fitsVehicle = getItemByCompact(compact)
            extra = filter
            checkExtra = type in (self._OPTIONAL_DEVICE, self._EQUIPMENT)
            checkFitsArtefacts = True if fitsType != 'otherVehicles' else False
            myVehicles = yield Requester(self._VEHICLE).getFromInventory()
            modulesAllVehicle = VehicleItemsRequester(myVehicles).getItems(requestType)
            if fitsType == 'myVehicle':
                vehicleFits = [fitsVehicle]
            else:
                vehicleFits = myVehicles
            filter = requestType
        filter = map(lambda w: w.lower(), filter)
        modulesAll = list()
        modulesShop = list()
        for rType in requestType:
            inv = yield Requester(rType).getFromInventory()
            shp = yield Requester(rType).getFromShop()
            modulesShop.extend(shp)
            modulesAll.extend(inv)

        vehPrices = {}
        if type == self._VEHICLE:
            compactDescrs = [ v.compactDescr for v in modulesAll ]
            vehPrices = yield StatsRequester().getVehiclesPrices(compactDescrs)
            vehPrices = dict(zip(compactDescrs, vehPrices))
        if type in (self._MODULE, self._OPTIONAL_DEVICE, self._EQUIPMENT):
            for vehModule in modulesAllVehicle:
                if vehModule not in modulesAll:
                    if modulesShop.count(vehModule) != 0:
                        modulesAll.append(vehModule)

        self.__clearTableData()
        self.__tableData = [type]
        excludeModules = []
        for module in modulesAll:
            if modulesShop.count(module) != 0:
                module.priceOrder = modulesShop[modulesShop.index(module)].priceOrder
            elif constants.IS_DEVELOPMENT:
                excludeModules.append(module)
                LOG_ERROR("Not found module %s '%s' (%r) in shop." % (module.type, module.unicName, module.compactDescr))

        modulesAll.sort()
        shopRqs = yield ShopRequester().request()
        for module in modulesAll:
            extraModuleInfo = None
            if module in excludeModules:
                continue
            if nation is not None:
                if module.nation != nation and module.nation != nations.NONE_INDEX:
                    continue
                if module.type.lower() not in filter:
                    continue
                if checkFits is not None:
                    if (module.compactDescr in modulesFits.keys()) != checkFits:
                        continue
                if module.isClipGun():
                    extraModuleInfo = CLIP_ICON_PATH
                if checkFitsArtefacts is not None:
                    compatible = False
                    for veh in vehicleFits:
                        if nation is not None and veh.nation != nation:
                            continue
                        compatible |= module.descriptor.checkCompatibilityWithVehicle(veh.descriptor)[0]

                    if compatible != checkFitsArtefacts:
                        continue
                inventoryCount = 0
                vehicleCount = 0
                if isinstance(module, VehicleItem):
                    vehicleCount = module.count
                else:
                    inventoryCount = module.count
                    if type in (self._MODULE, self._OPTIONAL_DEVICE, self._EQUIPMENT) and module in modulesAllVehicle:
                        vehModule = modulesAllVehicle[modulesAllVehicle.index(module)]
                        vehicleCount = vehModule.count
                if checkExtra:
                    if type == self._VEHICLE and 'brocken' not in extra:
                        if module.repairCost > 0:
                            continue
                    if type == self._VEHICLE and 'locked' not in extra:
                        if module.lock != 0:
                            continue
                    if 'onVehicle' not in extra:
                        if vehicleCount > 0 and inventoryCount == 0:
                            continue
                disable = ''
                if type == self._VEHICLE and not module.canSell:
                    disable = makeString(MENU.tankcarousel_vehiclestates(module.getState()))
                elif type in (self._MODULE, self._OPTIONAL_DEVICE, self._EQUIPMENT) and isinstance(module, VehicleItem):
                    if type == self._OPTIONAL_DEVICE:
                        if not module.descriptor['removable']:
                            disable = makeString(MENU.INVENTORY_DEVICE_ERRORS_NOT_REMOVABLE)
                        else:
                            disable = makeString(MENU.INVENTORY_DEVICE_ERRORS_RESERVED)
                    else:
                        disable = makeString(MENU.INVENTORY_ERRORS_RESERVED)
                sellPrice = isinstance(module, InventoryVehicle) and vehPrices.get(module.compactDescr, (0, 0))
            else:
                sellPrice = (0, 0)
                item = g_itemsCache.items.getItemByCD(module.compactDescr)
                if item is not None:
                    sellPrice = item.sellPrice
            valueElement = {'id': compactItem(module),
             'name': module.name if type in (self._OPTIONAL_DEVICE, self._EQUIPMENT) else module.longName,
             'desc': getShortDescr(module.tableName),
             'inventoryId': module.inventoryId if isinstance(module, InventoryVehicle) else None,
             'inventoryCount': inventoryCount,
             'vehicleCount': vehicleCount,
             'credits': sellPrice[0],
             'gold': sellPrice[1],
             'price': sellPrice,
             'currency': 'credits' if sellPrice[1] == 0 else 'gold',
             'level': module.level,
             'nation': module.nation,
             'type': module.itemTypeName if type not in (self._VEHICLE,
                      self._OPTIONAL_DEVICE,
                      self._SHELL,
                      self._EQUIPMENT) else module.icon,
             'disabled': disable,
             'statusLevel': module.getStateLevel() if isinstance(module, InventoryVehicle) else InventoryVehicle.STATE_LEVEL.INFO,
             'removable': module.descriptor['removable'] if type == self._OPTIONAL_DEVICE else True,
             'tankType': module.type if type == self._VEHICLE else type,
             'isPremium': module.isPremium if type == self._VEHICLE else False,
             'isElite': self.app.tooltipManager.isVehicleElite(module) if type == self._VEHICLE else False,
             'itemTypeName': module.itemTypeName,
             'goldShellsForCredits': shopRqs.isEnabledBuyingGoldShellsForCredits,
             'goldEqsForCredits': shopRqs.isEnabledBuyingGoldEqsForCredits,
             EXTRA_MODULE_INFO: extraModuleInfo}
            self.__tableData.append(valueElement)

        requester = yield StatsRequesterr().request()
        self._table.as_setGoldS(requester.gold)
        self._table.as_setCreditsS(requester.credits)
        self._table.as_setTableS(self.__tableData)
        Waiting.hide('updateInventory')
        return

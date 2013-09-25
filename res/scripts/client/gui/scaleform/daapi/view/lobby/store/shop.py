from PlayerEvents import g_playerEvents
from gui.Scaleform.daapi.view.dialogs.ConfirmModuleMeta import BuyModuleMeta
from gui.Scaleform.genConsts.STORE_TYPES import STORE_TYPES
from gui.Scaleform.locale.MENU import MENU
from gui.shared.utils import EXTRA_MODULE_INFO, CLIP_ICON_PATH
from items import vehicles
from debug_utils import LOG_ERROR, LOG_DEBUG
from gui.ClientUpdateManager import g_clientUpdateManager
from account_helpers.AccountSettings import AccountSettings
from adisp import process
from gui import getNationIndex, DialogsInterface
from gui.Scaleform.Waiting import Waiting
from gui.Scaleform.daapi.view.meta.ShopMeta import ShopMeta
from gui.Scaleform.daapi.view.lobby.store import Store
from gui.shared.events import ShowWindowEvent
from gui.shared.utils.gui_items import compactItem, getItemByCompact, InventoryVehicle
from gui.shared.utils.requesters import Requester, VehicleItemsRequester, _getComponentsByType, StatsRequester, ShopRequester, StatsRequesterr
import BigWorld
from items import ITEM_TYPE_INDICES
from gui.shared.utils.functions import getShortDescr
__author__ = 'd_trofimov'

class Shop(Store, ShopMeta):

    def __init__(self):
        super(Shop, self).__init__()
        self.__tableData = []

    def _populate(self):
        g_clientUpdateManager.addCallbacks({'stats.credits': self._onTableUpdate,
         'stats.gold': self._onTableUpdate})
        g_playerEvents.onCenterIsLongDisconnected += self._update
        super(Shop, self)._populate()

    def _dispose(self):
        super(Shop, self)._dispose()
        self.__clearTableData()
        g_playerEvents.onCenterIsLongDisconnected -= self._update

    def __clearTableData(self):
        while len(self.__tableData):
            obj = self.__tableData.pop()
            if type(obj) is not str:
                obj.clear()

        self.__tableData = None
        return

    @process
    def __buyItem(self, typeCompactDescr):
        stats = yield StatsRequesterr().request()
        isOk, args = yield DialogsInterface.showDialog(BuyModuleMeta(typeCompactDescr, (stats.credits, stats.gold)))
        LOG_DEBUG('Buy module confirm dialog results: success = ', isOk, args)

    def buyItem(self, data):
        dataCompactId = data.id
        item = getItemByCompact(dataCompactId)
        if ITEM_TYPE_INDICES[item.itemTypeName] == vehicles._VEHICLE:
            self.fireEvent(ShowWindowEvent(ShowWindowEvent.SHOW_VEHICLE_BUY_WINDOW, {'nationID': item.nation,
             'itemID': item.compactDescr}))
        else:
            self.__buyItem(item.compactDescr)

    @process
    def requestTableData(self, nation, type, filter):
        Waiting.show('updateShop')
        AccountSettings.setFilter('shop_current', (nation, type))
        AccountSettings.setFilter('shop_' + type, filter)
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
            compact = filter.pop(0)
            if compact == '0':
                LOG_ERROR('compact value has invalid value: ', compact)
                Waiting.hide('updateShop')
                return
            fitsVehicle = getItemByCompact(compact)
            checkExtra = True
            extra = filter[:]
            checkFits = True if fitsType != 'otherVehicles' else None
            myVehicles = yield Requester(self._VEHICLE).getFromInventory()
            modulesAllVehicle = VehicleItemsRequester(myVehicles).getItems(requestType)
            if fitsType == 'myVehicle':
                for rType in requestType:
                    modulesFits.update(_getComponentsByType(fitsVehicle, ITEM_TYPE_INDICES[rType]))

            elif fitsType != 'otherVehicles':
                for vehicle in myVehicles:
                    for rType in requestType:
                        modulesFits.update(_getComponentsByType(vehicle, ITEM_TYPE_INDICES[rType]))

            filter = requestType
        elif type == self._SHELL:
            filterSize = int(filter.pop(0))
            fitsType = filter.pop(filterSize)
            compact = filter.pop(filterSize)
            if compact == '0':
                LOG_ERROR('compact value has invalid value: ', compact)
                Waiting.hide('updateShop')
                return
            fitsVehicle = getItemByCompact(compact)
            checkFits = True if fitsType != 'otherGuns' else None
            if fitsType == 'myVehicleGun':
                for shoot in fitsVehicle.descriptor.gun['shots']:
                    modulesFits[shoot[self._SHELL]['compactDescr']] = True

            elif fitsType == 'myInventoryGuns':
                myGuns = yield Requester('vehicleGun').getFromInventory()
                for gun in myGuns:
                    for shoot in gun.descriptor['shots']:
                        modulesFits[shoot[self._SHELL]['compactDescr']] = True

            elif fitsType != 'otherGuns':
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
            if compact == '0':
                LOG_ERROR('compact value has invalid value: ', compact)
                Waiting.hide('updateShop')
                return
            fitsVehicle = getItemByCompact(compact)
            extra = filter
            checkExtra = type in (self._OPTIONAL_DEVICE, self._EQUIPMENT)
            checkFitsArtefacts = True if fitsType != 'otherVehicles' else None
            myVehicles = yield Requester(self._VEHICLE).getFromInventory()
            modulesAllVehicle = VehicleItemsRequester(myVehicles).getItems(requestType)
            if fitsType == 'myVehicle':
                vehicleFits = [fitsVehicle]
            elif fitsType != 'otherVehicles':
                vehicleFits = [ v for v in myVehicles if v.nation == nation ] if nation != None else myVehicles
            filter = requestType
        filter = map(lambda w: w.lower(), filter)
        modulesAll = list()
        modulesAllInventory = list()
        for rType in requestType:
            inv = yield Requester(rType).getFromInventory()
            modulesAllInventory.extend(inv)
            shp = yield Requester(rType).getFromShop(nation=nation)
            modulesAll.extend(shp)

        unlocks = yield StatsRequester().getUnlocks()
        shopRqs = yield ShopRequester().request()
        self.__clearTableData()
        self.__tableData = [type]
        modulesAll.sort()
        for module in modulesAll:
            extraModuleInfo = None
            if module.hidden:
                continue
            if module.type.lower() not in filter:
                continue
            if checkFits is not None:
                if (module.compactDescr in modulesFits.keys()) != checkFits:
                    continue
            if checkFitsArtefacts is not None:
                for veh in vehicleFits:
                    if module.descriptor.checkCompatibilityWithVehicle(veh.descriptor)[0] == checkFitsArtefacts:
                        break
                else:
                    continue

            if module.isClipGun():
                extraModuleInfo = CLIP_ICON_PATH
            inventoryCount = 0
            vehicleCount = 0
            installedIn = ''
            if module in modulesAllInventory:
                inventoryCount = 1
                if type != self._VEHICLE:
                    inventoryModule = modulesAllInventory[modulesAllInventory.index(module)]
                    inventoryCount = inventoryModule.count
            if type in (self._MODULE, self._OPTIONAL_DEVICE, self._EQUIPMENT) and module in modulesAllVehicle:
                vehModule = modulesAllVehicle[modulesAllVehicle.index(module)]
                vehicleCount = vehModule.count
                installedIn = ', '.join([ v.shortName for v in vehModule.vehicles ])
            if checkExtra:
                if 'locked' not in extra:
                    if type == self._VEHICLE:
                        compdecs = module.descriptor.type.compactDescr
                        if compdecs not in unlocks:
                            continue
                    elif type not in (self._SHELL, self._OPTIONAL_DEVICE, self._EQUIPMENT) and module.compactDescr not in unlocks:
                        continue
                if 'inHangar' not in extra and type not in (self._OPTIONAL_DEVICE, self._EQUIPMENT):
                    if inventoryCount > 0:
                        continue
                if 'onVehicle' not in extra:
                    if vehicleCount > 0:
                        continue
            disabled = ''
            if type == self._VEHICLE:
                if BigWorld.player().isLongDisconnectedFromCenter:
                    disabled = MENU.SHOP_ERRORS_CENTERISDOWN
                if inventoryCount > 0:
                    disabled = MENU.SHOP_ERRORS_INHANGAR
                else:
                    compdecs = module.descriptor.type.compactDescr
                    if compdecs not in unlocks:
                        disabled = MENU.SHOP_ERRORS_UNLOCKNEEDED
            elif type not in (self._SHELL, self._OPTIONAL_DEVICE, self._EQUIPMENT) and module.compactDescr not in unlocks:
                disabled = MENU.SHOP_ERRORS_UNLOCKNEEDED
            if not (shopRqs.isEnabledBuyingGoldShellsForCredits and module.itemTypeName == 'shell'):
                goldAmmoForCredits = shopRqs.isEnabledBuyingGoldEqsForCredits and module.itemTypeName == 'equipment'
                module.priceOrder = goldAmmoForCredits and (module.priceOrder[0] + module.priceOrder[1] * shopRqs.exchangeRateForShellsAndEqs, module.priceOrder[1])
            valueElement = {'id': compactItem(module),
             'name': module.name if type in (self._OPTIONAL_DEVICE, self._EQUIPMENT) else module.longName,
             'desc': getShortDescr(module.tableName),
             'inventoryId': None,
             'inventoryCount': inventoryCount,
             'vehicleCount': vehicleCount,
             'credits': module.priceOrder[0],
             'gold': module.priceOrder[1],
             'price': module.priceOrder,
             'currency': 'credits' if module.priceOrder[1] == 0 else 'gold',
             'level': module.level,
             'nation': module.nation,
             'type': module.itemTypeName if type not in (self._VEHICLE,
                      self._OPTIONAL_DEVICE,
                      self._SHELL,
                      self._EQUIPMENT) else module.icon,
             'disabled': disabled,
             'statusLevel': InventoryVehicle.STATE_LEVEL.WARNING,
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
        Waiting.hide('updateShop')
        return

    def requestFilterData(self, filterType):
        self._updateFilterOptions(filterType)

    def _update(self, diff = {}):
        self.as_updateS()

    def getName(self):
        return STORE_TYPES.SHOP

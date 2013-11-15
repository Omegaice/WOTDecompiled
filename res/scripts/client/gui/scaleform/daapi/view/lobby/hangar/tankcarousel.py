# 2013.11.15 11:26:03 EST
# Embedded file name: scripts/client/gui/Scaleform/daapi/view/lobby/hangar/TankCarousel.py
from debug_utils import LOG_ERROR, LOG_CURRENT_EXCEPTION, LOG_DEBUG
from gui.Scaleform.daapi.view.meta.TankCarouselMeta import TankCarouselMeta
import BigWorld
from PlayerEvents import g_playerEvents
from CurrentVehicle import g_currentVehicle
from account_helpers.AccountSettings import AccountSettings, CAROUSEL_FILTER
from adisp import process
from items.vehicles import VEHICLE_CLASS_TAGS
from gui.shared.gui_items.processors.vehicle import VehicleSlotBuyer, VehicleFavoriteProcessor
from gui.shared import events, EVENT_BUS_SCOPE, g_itemsCache, REQ_CRITERIA
from gui.shared.utils import decorators
from gui.shared.gui_items import GUI_ITEM_TYPE
from gui.shared.gui_items.Vehicle import VEHICLE_CLASS_NAME, VEHICLE_TYPES_ORDER
from gui.Scaleform import getVehicleTypeAssetPath
from gui.Scaleform.Waiting import Waiting
from gui import SystemMessages

class TankCarousel(TankCarouselMeta):
    UPDATE_LOCKS_PERIOD = 60

    def __init__(self):
        super(TankCarousel, self).__init__()
        self.__updateVehiclesTimerId = None
        defaults = AccountSettings.getFilterDefault(CAROUSEL_FILTER)
        from account_helpers.SettingsCore import g_settingsCore
        filters = g_settingsCore.serverSettings.getSection(CAROUSEL_FILTER, defaults)
        tankTypeIsNegative = filters['tankTypeIsNegative']
        del filters['tankTypeIsNegative']
        if tankTypeIsNegative:
            intTankType = -filters['tankType']
        else:
            intTankType = filters['tankType']
        filters['tankType'] = 'none'
        for idx, type in enumerate(VEHICLE_CLASS_TAGS):
            if idx == intTankType:
                filters['tankType'] = type
                break

        nationIsNegative = filters['nationIsNegative']
        del filters['nationIsNegative']
        if nationIsNegative:
            filters['nation'] = -filters['nation']
        self.vehiclesFilter = filters
        return

    def _populate(self):
        super(TankCarousel, self)._populate()
        g_playerEvents.onShopResync += self.__onShopResync
        if self.__updateVehiclesTimerId is not None:
            BigWorld.cancelCallback(self.__updateVehiclesTimerId)
            self.__updateVehiclesTimerId = None
        self.as_setCarouselFilterS(self.vehiclesFilter)
        return

    def _dispose(self):
        if self.__updateVehiclesTimerId is not None:
            BigWorld.cancelCallback(self.__updateVehiclesTimerId)
            self.__updateVehiclesTimerId = None
        g_playerEvents.onShopResync -= self.__onShopResync
        super(TankCarousel, self)._dispose()
        return

    def showVehicleInfo(self, vehInvID):
        vehicle = g_itemsCache.items.getVehicle(int(vehInvID))
        if vehicle is not None:
            self.fireEvent(events.ShowWindowEvent(events.ShowWindowEvent.SHOW_VEHICLE_INFO_WINDOW, {'vehicleDescr': vehicle.descriptor}))
        return

    def toResearch(self, compactDescr):
        if compactDescr is not None:
            Event = events.LoadEvent
            exitEvent = Event(Event.LOAD_HANGAR)
            loadEvent = Event(Event.LOAD_RESEARCH, ctx={'rootCD': compactDescr,
             'exit': exitEvent})
            self.fireEvent(loadEvent, scope=EVENT_BUS_SCOPE.LOBBY)
        else:
            LOG_ERROR("Can't go to Research because id for current vehicle is None")
        return

    def vehicleSell(self, vehInvID):
        self.fireEvent(events.ShowWindowEvent(events.ShowWindowEvent.SHOW_VEHICLE_SELL_DIALOG, {'vehInvID': int(vehInvID)}))

    def vehicleChange(self, vehInvID):
        g_currentVehicle.selectVehicle(int(vehInvID))

    @decorators.process('buySlot')
    def buySlot(self):
        result = yield VehicleSlotBuyer().request()
        if len(result.userMsg):
            SystemMessages.g_instance.pushI18nMessage(result.userMsg, type=result.sysMsgType)

    def buyTankClick(self):
        shopFilter = list(AccountSettings.getFilter('shop_current'))
        shopFilter[1] = 'vehicle'
        AccountSettings.setFilter('shop_current', tuple(shopFilter))
        self.fireEvent(events.LoadEvent(events.LoadEvent.LOAD_SHOP), EVENT_BUS_SCOPE.LOBBY)

    def getVehicleTypeProvider(self):
        all = self.__getProviderObject('none')
        all['label'] = self.__getVehicleTypeLabel('all')
        result = [all]
        for vehicleType in VEHICLE_TYPES_ORDER:
            result.append(self.__getProviderObject(vehicleType))

        return result

    def __getProviderObject(self, vehicleType):
        assetPath = {'label': self.__getVehicleTypeLabel(vehicleType),
         'data': vehicleType,
         'icon': getVehicleTypeAssetPath(vehicleType)}
        return assetPath

    def __getVehicleTypeLabel(self, vehicleType):
        return '#menu:carousel_tank_filter/' + vehicleType

    @process
    def favoriteVehicle(self, vehInvID, isFavorite):
        vehicle = g_itemsCache.items.getVehicle(int(vehInvID))
        if vehicle is not None:
            result = yield VehicleFavoriteProcessor(vehicle, bool(isFavorite)).request()
            if not result.success:
                LOG_ERROR('Cannot set selected vehicle as favorite due to following error: ', result.userMsg)
        self.updateVehicles(True)
        return

    def setVehiclesFilter(self, nation, tankType, ready):
        self.vehiclesFilter['nation'] = nation
        self.vehiclesFilter['ready'] = ready
        self.vehiclesFilter['tankType'] = tankType
        filters = {'nation': abs(nation),
         'nationIsNegative': nation < 0,
         'ready': ready}
        intTankType = -1
        for idx, type in enumerate(VEHICLE_CLASS_TAGS):
            if type == tankType:
                intTankType = idx
                break

        filters['tankTypeIsNegative'] = intTankType < 0
        filters['tankType'] = abs(intTankType)
        from account_helpers.SettingsCore import g_settingsCore
        g_settingsCore.serverSettings.setSection(CAROUSEL_FILTER, filters)
        self.updateVehicles(True)

    def updateVehicles(self, resetPos = False):
        Waiting.show('updateMyVehicles')
        filterCriteria = REQ_CRITERIA.INVENTORY
        if self.vehiclesFilter['nation'] != -1:
            filterCriteria |= REQ_CRITERIA.NATIONS([self.vehiclesFilter['nation']])
        if self.vehiclesFilter['tankType'] != 'none':
            filterCriteria |= REQ_CRITERIA.VEHICLE.CLASSES([self.vehiclesFilter['tankType']])
        if self.vehiclesFilter['ready']:
            filterCriteria |= REQ_CRITERIA.VEHICLE.FAVORITE
        items = g_itemsCache.items
        newVehs = items.getVehicles(REQ_CRITERIA.INVENTORY)
        filteredVehs = items.getVehicles(filterCriteria)
        vehsData = []

        def sorting(v1, v2):
            if v1.isFavorite and not v2.isFavorite:
                return -1
            if not v1.isFavorite and v2.isFavorite:
                return 1
            return v1.__cmp__(v2)

        for vehicle in sorted(filteredVehs.itervalues(), sorting):
            try:
                vState, vStateLvl = vehicle.getState()
                v = {'id': vehicle.invID,
                 'inventoryId': vehicle.invID,
                 'label': vehicle.userName,
                 'image': vehicle.icon,
                 'nation': vehicle.nationID,
                 'level': vehicle.level,
                 'stat': vState,
                 'stateLevel': vStateLvl,
                 'doubleXPReceived': vehicle.dailyXPFactor,
                 'compactDescr': vehicle.intCD,
                 'favorite': vehicle.isFavorite,
                 'canSell': vehicle.canSell,
                 'clanLock': vehicle.clanLock,
                 'elite': vehicle.isElite,
                 'premium': vehicle.isPremium,
                 'tankType': vehicle.type,
                 'exp': vehicle.xp,
                 'current': 0,
                 'enabled': True}
            except Exception:
                LOG_ERROR("Exception while '%s' vehicle processing" % vehicle.descriptor.type.name)
                LOG_CURRENT_EXCEPTION()
                continue

            vehsData.append(v)

        self.as_vehiclesResponseS({'slotPrice': items.shop.getVehicleSlotsPrice(items.stats.vehicleSlots),
         'availableSlotsForBuy': items.stats.vehicleSlots - len(newVehs),
         'allTanksCount': len(newVehs),
         'selectedTankID': g_currentVehicle.invID,
         'slots': vehsData})
        isVehTypeLock = sum((len(v) for v in items.stats.vehicleTypeLocks.itervalues()))
        isGlobalVehLock = sum((len(v) for v in items.stats.globalVehicleLocks.itervalues()))
        if self.__updateVehiclesTimerId is None and (isVehTypeLock or isGlobalVehLock):
            self.__updateVehiclesTimerId = BigWorld.callback(self.UPDATE_LOCKS_PERIOD, self.updateLockTimers)
            LOG_DEBUG('Lock timer updated')
        Waiting.hide('updateMyVehicles')
        return

    def updateLockTimers(self):
        self.__updateVehiclesTimerId = None
        self.updateVehicles()
        return

    def __onShopResync(self):
        self.updateVehicles()
# okay decompyling res/scripts/client/gui/scaleform/daapi/view/lobby/hangar/tankcarousel.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:26:03 EST

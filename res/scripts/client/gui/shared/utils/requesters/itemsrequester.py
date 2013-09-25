# Embedded file name: scripts/client/gui/shared/utils/requesters/ItemsRequester.py
import weakref
from abc import ABCMeta, abstractmethod
from collections import defaultdict
import BigWorld
import dossiers
import nations
import constants
from items import vehicles, tankmen, getTypeOfCompactDescr
from adisp import async, process
from debug_utils import LOG_WARNING, LOG_DEBUG
from gui.Scaleform.Waiting import Waiting
from gui.shared.utils.requesters.StatsRequesterr import StatsRequesterr
from gui.shared.utils.requesters.ShopRequester import ShopRequester
from gui.shared.utils.requesters.InventoryRequester import InventoryRequester
from gui.shared.utils.requesters.DossierRequester import DossierRequester
from gui.shared.gui_items import GUI_ITEM_TYPE, GUI_ITEM_TYPE_NAMES, ItemsCollection, getVehicleSuitablesByType
from gui.shared.gui_items.dossier import TankmanDossier, AccountDossier, VehicleDossier
from gui.shared.gui_items.vehicle_modules import Shell, VehicleGun, VehicleChassis, VehicleEngine, VehicleRadio, VehicleTurret
from gui.shared.gui_items.artefacts import Equipment, OptionalDevice
from gui.shared.gui_items.Vehicle import Vehicle
from gui.shared.gui_items.Tankman import Tankman

class _CriteriaCondition(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def __call__(self, item):
        pass


class PredicateCondition(_CriteriaCondition):

    def __init__(self, predicate):
        self.predicate = predicate

    def __call__(self, item):
        return self.predicate(item)


class RequestCriteria(object):

    def __init__(self, *args):
        self._conditions = args

    def __call__(self, item):
        for c in self._conditions:
            if not c(item):
                return False

        return True

    def __or__(self, other):
        raise isinstance(other, RequestCriteria) or AssertionError
        return RequestCriteria(*(self._conditions + other.getConditions()))

    def __invert__(self):
        invertedConds = []
        for c in self.getConditions():
            invertedConds.append(lambda item: not c(item))

        return RequestCriteria(*invertedConds)

    def getConditions(self):
        return self._conditions


class NegativeCriteria(RequestCriteria):

    def __call__(self, item):
        for c in self._conditions:
            if c(item):
                return False

        return True


class VehsSuitableCriteria(RequestCriteria):

    def __init__(self, vehsItems, itemTypeIDs = None):
        super(VehsSuitableCriteria, self).__init__(PredicateCondition(self._checkItem))
        itemTypeIDs = itemTypeIDs or GUI_ITEM_TYPE.VEHICLE_MODULES
        self.suitableCompDescrs = set()
        for vehicle in vehsItems:
            for itemTypeID in itemTypeIDs:
                for descr in getVehicleSuitablesByType(vehicle.descriptor, itemTypeID)[0]:
                    self.suitableCompDescrs.add(descr['compactDescr'])

    def _checkItem(self, item):
        return item.intCD in self.suitableCompDescrs


class REQ_CRITERIA:
    EMPTY = RequestCriteria()
    HIDDEN = RequestCriteria(PredicateCondition(lambda item: item.isHidden))
    UNLOCKED = RequestCriteria(PredicateCondition(lambda item: item.isUnlocked))
    REMOVABLE = RequestCriteria(PredicateCondition(lambda item: item.isRemovable))
    INVENTORY = RequestCriteria(PredicateCondition(lambda item: item.inventoryCount > 0))
    NATIONS = staticmethod(lambda nationIDs = nations.INDICES.keys(): RequestCriteria(PredicateCondition(lambda item: item.nationID in nationIDs)))
    ITEM_TYPES = staticmethod(lambda *args: RequestCriteria(PredicateCondition(lambda item: item.itemTypeID in args)))

    class VEHICLE:
        FAVORITE = RequestCriteria(PredicateCondition(lambda item: item.isFavorite))
        PREMIUM = RequestCriteria(PredicateCondition(lambda item: item.isPremium))
        TYPES = staticmethod(lambda types = constants.VEHICLE_CLASS_INDICES.keys(): RequestCriteria(PredicateCondition(lambda item: item.type in types)))
        LEVELS = staticmethod(lambda levels = range(1, constants.MAX_VEHICLE_LEVEL + 1): RequestCriteria(PredicateCondition(lambda item: item.level in levels)))
        SPECIFIC = staticmethod(lambda typeCompDescrs: RequestCriteria(PredicateCondition(lambda item: item.intCD in typeCompDescrs)))
        SUITABLE = staticmethod(lambda vehsItems, itemTypeIDs = None: VehsSuitableCriteria(vehsItems, itemTypeIDs))

    class TANKMAN:
        IN_TANK = RequestCriteria(PredicateCondition(lambda item: item.isInTank))
        ROLES = staticmethod(lambda roles = tankmen.ROLES: RequestCriteria(PredicateCondition(lambda item: item.descriptor.role in roles)))


class ItemsRequester(object):
    """
    GUI items getting interface. Before using any method
    must be completed async server request (ItemsRequester.request).
    """
    ITEM_TYPES_MAPPING = {GUI_ITEM_TYPE.SHELL: Shell,
     GUI_ITEM_TYPE.EQUIPMENT: Equipment,
     GUI_ITEM_TYPE.OPTIONALDEVICE: OptionalDevice,
     GUI_ITEM_TYPE.GUN: VehicleGun,
     GUI_ITEM_TYPE.CHASSIS: VehicleChassis,
     GUI_ITEM_TYPE.TURRET: VehicleTurret,
     GUI_ITEM_TYPE.ENGINE: VehicleEngine,
     GUI_ITEM_TYPE.RADIO: VehicleRadio,
     GUI_ITEM_TYPE.VEHICLE: Vehicle,
     GUI_ITEM_TYPE.TANKMAN: Tankman}

    def __init__(self):
        self.shop = ShopRequester()
        self.inventory = InventoryRequester()
        self.stats = StatsRequesterr()
        self.dossiers = DossierRequester()
        self.__itemsCache = defaultdict(dict)

    @async
    @process
    def request(self, callback = None):
        Waiting.show('download/inventory')
        yield self.stats.request()
        yield self.inventory.request()
        Waiting.hide('download/inventory')
        Waiting.show('download/shop')
        yield self.shop.request()
        Waiting.hide('download/shop')
        Waiting.show('download/dossier')
        yield self.dossiers.request()
        Waiting.hide('download/dossier')
        callback(self)

    @async
    @process
    def requestUserDossier(self, userName, callback):
        dr = self.dossiers.getUserDossierRequester(userName)
        userAccDossier = yield dr.getAccountDossier()
        container = self.__itemsCache[GUI_ITEM_TYPE.ACCOUNT_DOSSIER]
        container[userName] = userAccDossier
        callback((userAccDossier, dr.isHidden))

    @async
    @process
    def requestUserVehicleDossier(self, userName, vehTypeCompDescr, callback):
        dr = self.dossiers.getUserDossierRequester(userName)
        userVehDossier = yield dr.getVehicleDossier(vehTypeCompDescr)
        container = self.__itemsCache[GUI_ITEM_TYPE.VEHICLE_DOSSIER]
        container[userName, vehTypeCompDescr] = userVehDossier
        callback(userVehDossier)

    def clear(self):
        self.inventory.clear()
        self.shop.clear()
        self.stats.clear()
        self.dossiers.clear()

    def invalidateCache(self, diff = None):
        if diff is None:
            LOG_DEBUG('Gui items cache full invalidation')
            self.__itemsCache.clear()
        else:
            uniqueIDs = set()
            for statName, data in diff.get('stats', {}).iteritems():
                if statName in ('unlocks', 'eliteVehicles'):
                    uniqueIDs.update(data)
                elif statName in ('vehTypeXP', 'vehTypeLocks'):
                    uniqueIDs.update(data.keys())

            self._invalidateItems(GUI_ITEM_TYPE.VEHICLE, uniqueIDs)
            for cacheType, data in diff.get('cache', {}).iteritems():
                if cacheType == 'vehsLock':
                    uniqueIDs = set()
                    for vehInvID in data.keys():
                        vehData = self.inventory.getVehicleData(vehInvID)
                        if vehData is not None:
                            uniqueIDs.add(vehData.descriptor.type.compactDescr)

                    self._invalidateItems(GUI_ITEM_TYPE.VEHICLE, uniqueIDs)

            for itemTypeID, itemsDiff in diff.get('inventory', {}).iteritems():
                uniqueIDs = set()
                if itemTypeID == GUI_ITEM_TYPE.VEHICLE:
                    if 'compDescr' in itemsDiff:
                        for strCD in itemsDiff['compDescr'].itervalues():
                            if strCD is not None:
                                uniqueIDs.add(vehicles.getVehicleTypeCompactDescr(strCD))

                    for data in itemsDiff.itervalues():
                        for vehInvID in data.iterkeys():
                            vehData = self.inventory.getVehicleData(vehInvID)
                            if vehData is not None:
                                uniqueIDs.add(vehData.descriptor.type.compactDescr)

                elif itemTypeID == GUI_ITEM_TYPE.TANKMAN:
                    for data in itemsDiff.itervalues():
                        uniqueIDs.update(data.keys())

                else:
                    uniqueIDs.update(itemsDiff.keys())
                self._invalidateItems(itemTypeID, uniqueIDs)

            for itemTypeID in GUI_ITEM_TYPE.GUI:
                self.__itemsCache[itemTypeID].clear()

        return

    def getVehicle(self, vehInvID):
        vehInvData = self.inventory.getVehicleData(vehInvID)
        if vehInvData is not None:
            return self.__makeVehicle(vehInvData.descriptor.type.compactDescr, vehInvData)
        else:
            return

    def getTankman(self, tmanInvID):
        tmanInvData = self.inventory.getTankmanData(tmanInvID)
        if tmanInvData is not None:
            return self.__makeTankman(tmanInvID, tmanInvData)
        else:
            return

    def getItems(self, itemTypeID = None, criteria = REQ_CRITERIA.EMPTY):
        from gui.shared.utils.requesters import ShopDataParser
        shopParser = ShopDataParser(self.shop.getItemsData())
        result = ItemsCollection()
        for intCD, _, _, _ in shopParser.getItemsIterator(itemTypeID=itemTypeID):
            item = self.getItemByCD(intCD)
            if criteria(item):
                result[intCD] = item

        return result

    def getTankmen(self, criteria = REQ_CRITERIA.EMPTY):
        result = ItemsCollection()
        tmanInvData = self.inventory.getItemsData(GUI_ITEM_TYPE.TANKMAN)
        for invID, invData in tmanInvData.iteritems():
            item = self.__makeTankman(invID, invData)
            if criteria(item):
                result[invID] = item

        return result

    def getVehicles(self, criteria = REQ_CRITERIA.EMPTY):
        return self.getItems(GUI_ITEM_TYPE.VEHICLE, criteria=criteria)

    def getItemByCD(self, typeCompDescr):
        """
        Trying to return item from inventory by item int
        compact descriptor, otherwise - from shop.
        
        @param typeCompDescr: item int compact descriptor
        @return: item object
        """
        if getTypeOfCompactDescr(typeCompDescr) == GUI_ITEM_TYPE.VEHICLE:
            return self.__makeVehicle(typeCompDescr)
        return self.__makeSimpleItem(typeCompDescr)

    def getItem(self, itemTypeID, nationID, innationID):
        """
        Returns item from inventory by given criteria or
        from shop.
        
        @param itemTypeID: item type index from common.items.ITEM_TYPE_NAMES
        @param nationID: nation index from nations.NAMES
        @param innationID: item index within its nation
        @return: gui item
        """
        typeCompDescr = vehicles.makeIntCompactDescrByID(GUI_ITEM_TYPE_NAMES[itemTypeID], nationID, innationID)
        if itemTypeID == GUI_ITEM_TYPE.VEHICLE:
            return self.__makeVehicle(typeCompDescr)
        return self.__makeSimpleItem(typeCompDescr)

    def getTankmanDossier(self, tmanInvID):
        """
        Returns tankman dossier item by given tankman
        inventory id
        
        @param tmanInvID: tankman inventory id
        @return: TankmanDossier object
        """
        tankman = self.getTankman(tmanInvID)
        tmanDossier = self.__getTankmanDossierDescr(tmanInvID)
        if tankman.isInTank:
            extDossier = self.getVehicleDossier(tankman.vehicleDescr.type.compactDescr)
        else:
            extDossier = self.getAccountDossier()
        return TankmanDossier(tankman.descriptor, tmanDossier, extDossier)

    def getVehicleDossier(self, vehTypeCompDescr, userName = None):
        """
        Returns vehicle dossier item by given vehicle type
        int compact descriptor
        
        @param vehTypeCompDescr: vehicle type in compact descriptor
        @return: VehicleDossier object
        """
        if userName is None:
            return VehicleDossier(self.__getVehicleDossierDescr(vehTypeCompDescr))
        container = self.__itemsCache[GUI_ITEM_TYPE.VEHICLE_DOSSIER]
        dossier = container.get((userName, vehTypeCompDescr))
        if dossier is None:
            LOG_WARNING("Trying to get empty user vehicle' dossier", vehTypeCompDescr, userName)
            return
        else:
            return VehicleDossier(dossier)

    def getAccountDossier(self, userName = None):
        """
        Returns account dossier item
        
        @return: AccountDossier object
        """
        if userName is None:
            dossierDescr = self.__getAccountDossierDescr()
            return AccountDossier(dossierDescr, True, weakref.proxy(self))
        container = self.__itemsCache[GUI_ITEM_TYPE.ACCOUNT_DOSSIER]
        dossier = container.get(userName)
        if dossier is None:
            LOG_WARNING('Trying to get empty user dossier', userName)
            return
        else:
            return AccountDossier(dossier, False)

    def _invalidateItems(self, itemTypeID, uniqueIDs):
        cache = self.__itemsCache[itemTypeID]
        for uid in uniqueIDs:
            invRes = self.inventory.invalidateItem(itemTypeID, uid)
            if uid in cache:
                LOG_DEBUG('Item marked as invalid', uid, cache[uid], invRes)
                del cache[uid]
                return
            LOG_DEBUG('No cached item', uid, invRes)

    def __getAccountDossierDescr(self):
        """
        @return: account descriptor
        """
        return dossiers.getAccountDossierDescr(self.stats.accountDossier)

    def __getTankmanDossierDescr(self, tmanInvID):
        """
        @param tmanInvID: tankman inventory id
        @return: tankman dossier descriptor
        """
        tmanData = self.inventory.getTankmanData(tmanInvID)
        if tmanData is not None:
            return dossiers.getTankmanDossierDescr(tmanData.descriptor.dossierCompactDescr)
        else:
            return dossiers.getTankmanDossierDescr()

    def __getVehicleDossierDescr(self, vehTypeCompDescr):
        """
        @param vehTypeCompDescr: vehicle type int compact descriptor
        @return : vehicle dossier descriptor
        """
        return dossiers.getVehicleDossierDescr(self.dossiers.getVehicleDossier(vehTypeCompDescr))

    def __makeItem(self, itemTypeIdx, uid, *args, **kwargs):
        container = self.__itemsCache[itemTypeIdx]
        if uid in container:
            return container[uid]
        else:
            item = None
            cls = ItemsRequester.ITEM_TYPES_MAPPING.get(itemTypeIdx)
            if cls is not None:
                container[uid] = item = cls(*args, **kwargs)
            return item

    def __makeVehicle(self, typeCompDescr, vehInvData = None):
        if not vehInvData:
            vehInvData = self.inventory.getItemData(typeCompDescr)
            return vehInvData is not None and self.__makeItem(GUI_ITEM_TYPE.VEHICLE, typeCompDescr, strCompactDescr=vehInvData.compDescr, inventoryID=vehInvData.invID, proxy=self)
        else:
            return self.__makeItem(GUI_ITEM_TYPE.VEHICLE, typeCompDescr, typeCompDescr=typeCompDescr, proxy=self)

    def __makeTankman(self, tmanInvID, tmanInvData = None):
        if not tmanInvData:
            tmanInvData = self.inventory.getTankmanData(tmanInvID)
            if tmanInvData is not None:
                vehicle = None
                vehicle = tmanInvData.vehicle > 0 and self.getVehicle(tmanInvData.vehicle)
            return self.__makeItem(GUI_ITEM_TYPE.TANKMAN, tmanInvID, strCompactDescr=tmanInvData.compDescr, inventoryID=tmanInvID, vehicle=vehicle, proxy=self)
        else:
            return

    def __makeSimpleItem(self, typeCompDescr):
        return self.__makeItem(getTypeOfCompactDescr(typeCompDescr), typeCompDescr, intCompactDescr=typeCompDescr, proxy=self)
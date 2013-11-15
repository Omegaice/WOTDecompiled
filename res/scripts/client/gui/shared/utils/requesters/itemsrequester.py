# 2013.11.15 11:27:05 EST
# Embedded file name: scripts/client/gui/shared/utils/requesters/ItemsRequester.py
import weakref
from abc import ABCMeta, abstractmethod
from collections import defaultdict
import BigWorld
import dossiers2
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
    SECRET = RequestCriteria(PredicateCondition(lambda item: item.isSecret))
    UNLOCKED = RequestCriteria(PredicateCondition(lambda item: item.isUnlocked))
    REMOVABLE = RequestCriteria(PredicateCondition(lambda item: item.isRemovable))
    INVENTORY = RequestCriteria(PredicateCondition(lambda item: item.inventoryCount > 0))
    NATIONS = staticmethod(lambda nationIDs = nations.INDICES.keys(): RequestCriteria(PredicateCondition(lambda item: item.nationID in nationIDs)))
    ITEM_TYPES = staticmethod(lambda *args: RequestCriteria(PredicateCondition(lambda item: item.itemTypeID in args)))

    class VEHICLE:
        FAVORITE = RequestCriteria(PredicateCondition(lambda item: item.isFavorite))
        PREMIUM = RequestCriteria(PredicateCondition(lambda item: item.isPremium))
        READY = RequestCriteria(PredicateCondition(lambda item: item.isReadyToFight))
        CLASSES = staticmethod(lambda types = constants.VEHICLE_CLASS_INDICES.keys(): RequestCriteria(PredicateCondition(lambda item: item.type in types)))
        LEVELS = staticmethod(lambda levels = range(1, constants.MAX_VEHICLE_LEVEL + 1): RequestCriteria(PredicateCondition(lambda item: item.level in levels)))
        SPECIFIC_BY_CD = staticmethod(lambda typeCompDescrs: RequestCriteria(PredicateCondition(lambda item: item.intCD in typeCompDescrs)))
        SPECIFIC_BY_NAME = staticmethod(lambda typeNames: RequestCriteria(PredicateCondition(lambda item: item.name in typeNames)))
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

    def isSynced(self):
        return self.stats.isSynced() and self.inventory.isSynced() and self.shop.isSynced() and self.dossiers.isSynced()

    @async
    @process
    def requestUserDossier(self, databaseID, callback):
        dr = self.dossiers.getUserDossierRequester(databaseID)
        userAccDossier = yield dr.getAccountDossier()
        container = self.__itemsCache[GUI_ITEM_TYPE.ACCOUNT_DOSSIER]
        container[databaseID] = userAccDossier
        callback((userAccDossier, dr.isHidden))

    @async
    @process
    def requestUserVehicleDossier(self, databaseID, vehTypeCompDescr, callback):
        dr = self.dossiers.getUserDossierRequester(databaseID)
        userVehDossier = yield dr.getVehicleDossier(vehTypeCompDescr)
        container = self.__itemsCache[GUI_ITEM_TYPE.VEHICLE_DOSSIER]
        container[databaseID, vehTypeCompDescr] = userVehDossier
        callback(userVehDossier)

    def clear(self):
        self.__itemsCache.clear()
        self.inventory.clear()
        self.shop.clear()
        self.stats.clear()
        self.dossiers.clear()

    def invalidateCache(self, diff = None):
        if diff is None:
            LOG_DEBUG('Gui items cache full invalidation')
            for itemTypeID, cache in self.__itemsCache.iteritems():
                if itemTypeID not in (GUI_ITEM_TYPE.ACCOUNT_DOSSIER, GUI_ITEM_TYPE.VEHICLE_DOSSIER):
                    cache.clear()

        else:
            invalidate = defaultdict(set)
            for statName, data in diff.get('stats', {}).iteritems():
                if statName in ('unlocks', 'eliteVehicles'):
                    invalidate[GUI_ITEM_TYPE.VEHICLE].update(data)
                elif statName in ('vehTypeXP', 'vehTypeLocks'):
                    invalidate[GUI_ITEM_TYPE.VEHICLE].update(data.keys())
                elif statName in (('multipliedXPVehs', '_r'),):
                    inventoryVehiclesCDs = map(lambda v: vehicles.getVehicleTypeCompactDescr(v['compDescr']), self.inventory.getItems(GUI_ITEM_TYPE.VEHICLE).itervalues())
                    invalidate[GUI_ITEM_TYPE.VEHICLE].update(inventoryVehiclesCDs)

            for cacheType, data in diff.get('cache', {}).iteritems():
                if cacheType == 'vehsLock':
                    for vehInvID in data.keys():
                        vehData = self.inventory.getVehicleData(vehInvID)
                        if vehData is not None:
                            invalidate[GUI_ITEM_TYPE.VEHICLE].add(vehData.descriptor.type.compactDescr)

            for itemTypeID, itemsDiff in diff.get('inventory', {}).iteritems():
                if itemTypeID == GUI_ITEM_TYPE.VEHICLE:
                    if 'compDescr' in itemsDiff:
                        for strCD in itemsDiff['compDescr'].itervalues():
                            if strCD is not None:
                                invalidate[itemTypeID].add(vehicles.getVehicleTypeCompactDescr(strCD))

                    for data in itemsDiff.itervalues():
                        for vehInvID in data.iterkeys():
                            vehData = self.inventory.getVehicleData(vehInvID)
                            if vehData is not None:
                                invalidate[itemTypeID].add(vehData.descriptor.type.compactDescr)
                                invalidate[GUI_ITEM_TYPE.TANKMAN].update(self.__getTankmenIDsForVehicle(vehData))

                elif itemTypeID == GUI_ITEM_TYPE.TANKMAN:
                    for data in itemsDiff.itervalues():
                        invalidate[itemTypeID].update(data.keys())
                        for tmanInvID in data.keys():
                            tmanData = self.inventory.getTankmanData(tmanInvID)
                            if tmanData is not None and tmanData.vehicle != -1:
                                invalidate[GUI_ITEM_TYPE.VEHICLE].update(self.__getVehicleCDForTankman(tmanData))
                                invalidate[GUI_ITEM_TYPE.TANKMAN].update(self.__getTankmenIDsForTankman(tmanData))

                else:
                    invalidate[itemTypeID].update(itemsDiff.keys())

            for itemTypeID, uniqueIDs in invalidate.iteritems():
                self._invalidateItems(itemTypeID, uniqueIDs)

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

    def getVehicleDossier(self, vehTypeCompDescr, databaseID = None):
        """
        Returns vehicle dossier item by given vehicle type
        int compact descriptor
        
        @param vehTypeCompDescr: vehicle type in compact descriptor
        @return: VehicleDossier object
        """
        if databaseID is None:
            return VehicleDossier(self.__getVehicleDossierDescr(vehTypeCompDescr))
        container = self.__itemsCache[GUI_ITEM_TYPE.VEHICLE_DOSSIER]
        dossier = container.get((int(databaseID), vehTypeCompDescr))
        if dossier is None:
            LOG_WARNING("Trying to get empty user vehicle' dossier", vehTypeCompDescr, databaseID)
            return
        else:
            return VehicleDossier(dossier)

    def getAccountDossier(self, databaseID = None):
        """
        Returns account dossier item
        @return: AccountDossier object
        """
        if databaseID is None:
            dossierDescr = self.__getAccountDossierDescr()
            return AccountDossier(dossierDescr, True, proxy=weakref.proxy(self))
        else:
            container = self.__itemsCache[GUI_ITEM_TYPE.ACCOUNT_DOSSIER]
            dossier = container.get(int(databaseID))
            if dossier is None:
                LOG_WARNING('Trying to get empty user dossier', databaseID)
                return
            from gui import game_control
            isInRoaming = game_control.g_instance.roaming.isInRoaming() or game_control.g_instance.roaming.isPlayerInRoaming(databaseID)
            return AccountDossier(dossier, False, isInRoaming)

    def _invalidateItems(self, itemTypeID, uniqueIDs):
        cache = self.__itemsCache[itemTypeID]
        for uid in uniqueIDs:
            invRes = self.inventory.invalidateItem(itemTypeID, uid)
            if uid in cache:
                LOG_DEBUG('Item marked as invalid', uid, cache[uid], invRes)
                del cache[uid]
            else:
                LOG_DEBUG('No cached item', uid, invRes)

    def __getAccountDossierDescr(self):
        """
        @return: account descriptor
        """
        return dossiers2.getAccountDossierDescr(self.stats.accountDossier)

    def __getTankmanDossierDescr(self, tmanInvID):
        """
        @param tmanInvID: tankman inventory id
        @return: tankman dossier descriptor
        """
        tmanData = self.inventory.getTankmanData(tmanInvID)
        if tmanData is not None:
            return dossiers2.getTankmanDossierDescr(tmanData.descriptor.dossierCompactDescr)
        else:
            return dossiers2.getTankmanDossierDescr()

    def __getVehicleDossierDescr(self, vehTypeCompDescr):
        """
        @param vehTypeCompDescr: vehicle type int compact descriptor
        @return : vehicle dossier descriptor
        """
        return dossiers2.getVehicleDossierDescr(self.dossiers.getVehicleDossier(vehTypeCompDescr))

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

    def __getTankmenIDsForVehicle(self, vehData):
        vehTmanIDs = set()
        for tmanInvID in vehData.crew:
            if tmanInvID is not None:
                vehTmanIDs.add(tmanInvID)

        return vehTmanIDs

    def __getTankmenIDsForTankman(self, tmanData):
        vehData = self.inventory.getVehicleData(tmanData.vehicle)
        if vehData is not None:
            return self.__getTankmenIDsForVehicle(vehData)
        else:
            return set()

    def __getVehicleCDForTankman(self, tmanData):
        vehData = self.inventory.getVehicleData(tmanData.vehicle)
        if vehData is not None:
            return set([vehData.descriptor.type.compactDescr])
        else:
            return set()
# okay decompyling res/scripts/client/gui/shared/utils/requesters/itemsrequester.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:27:06 EST

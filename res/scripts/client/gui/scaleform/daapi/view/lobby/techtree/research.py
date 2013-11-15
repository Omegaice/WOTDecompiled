# 2013.11.15 11:26:18 EST
# Embedded file name: scripts/client/gui/Scaleform/daapi/view/lobby/techtree/Research.py
import weakref
from AccountCommands import RES_SUCCESS
from PlayerEvents import g_playerEvents
from adisp import process
import BigWorld
from CurrentVehicle import g_currentVehicle
from constants import IS_DEVELOPMENT
from debug_utils import LOG_ERROR, LOG_DEBUG
from gui import SystemMessages, DialogsInterface, game_control
from gui.Scaleform.Waiting import Waiting
from gui.Scaleform.daapi.view.dialogs.ConfirmModuleMeta import LocalSellModuleMeta
from gui.Scaleform.daapi.view.meta.ResearchMeta import ResearchMeta
from gui.Scaleform.daapi.view.lobby.techtree import _TURRET, _GUN
from gui.Scaleform.daapi.view.lobby.techtree.ResearchView import ResearchView
from gui.Scaleform.daapi.view.lobby.techtree.listeners import StatsListener, InventoryListener, INV_ITEM_VCDESC_KEY
from gui.Scaleform.daapi.view.lobby.techtree import custom_items
from gui.shared import events, EVENT_BUS_SCOPE, g_itemsCache
from gui.shared.gui_items.processors.module import ModuleBuyer, getInstallerProcessor
from gui.shared.utils import functions
from items import ITEM_TYPE_NAMES, vehicles
from gui.Scaleform.daapi.view.lobby.techtree import _VEHICLE_TYPE_NAME, _VEHICLE, _RESEARCH_ITEMS, USE_XML_DUMPING, SelectedNation, RequestState
from gui.Scaleform.daapi.view.lobby.techtree.data import ResearchItemsData
from gui.Scaleform.daapi.view.lobby.techtree import dumpers
from gui.shared.utils.requesters import StatsRequester, Requester, ShopDataParser
from functools import partial
import nations

class Research(ResearchView, ResearchMeta):

    def __init__(self, ctx = None):
        data = ResearchItemsData()
        if USE_XML_DUMPING and IS_DEVELOPMENT:
            dumper = dumpers.ResearchItemsXMLDumper()
        else:
            dumper = dumpers.ResearchItemsObjDumper()
        data.setDumper(dumper)
        super(Research, self).__init__(data)
        self._statsListener = StatsListener()
        self._invListener = InventoryListener()
        self._resolveLoadCtx(ctx=ctx)

    def __del__(self):
        LOG_DEBUG('ResearchPage deleted')

    def _resolveLoadCtx(self, ctx = None):
        rootCD = ctx['rootCD'] if ctx is not None and 'rootCD' in ctx else None
        if rootCD is None:
            if g_currentVehicle.isPresent():
                self._data.setRootCD(g_currentVehicle.item.intCD)
        else:
            self._data.setRootCD(rootCD)
        SelectedNation.select(self._data.getNationID())
        return

    def _populate(self):
        super(Research, self)._populate()
        selfProxy = weakref.proxy(self)
        self._statsListener.startListen(selfProxy)
        self._invListener.startListen(selfProxy)
        g_playerEvents.onShopResync += self.__shop_onResync
        g_playerEvents.onCenterIsLongDisconnected += self.__center_onIsLongDisconnected
        self.as_setWalletStatusS(game_control.g_instance.wallet.componentsStatuses)
        game_control.g_instance.wallet.onWalletStatusChanged += self.__setWalletCallback

    def _dispose(self):
        self._statsListener.stopListen()
        self._invListener.stopListen()
        g_playerEvents.onShopResync -= self.__shop_onResync
        g_playerEvents.onCenterIsLongDisconnected -= self.__center_onIsLongDisconnected
        game_control.g_instance.wallet.onWalletStatusChanged -= self.__setWalletCallback
        Waiting.hide('draw_research_items')
        super(Research, self)._dispose()

    def requestNationData(self):
        self.__startDataCollect()
        return True

    def getResearchItemsData(self, vehCD, rootChanged):
        Waiting.show('draw_research_items', isSingle=True)
        if rootChanged:
            self._data.setRootCD(vehCD)
        self._data.load()
        return self._data.dump()

    def redrawResearchItems(self):
        self.as_drawResearchItemsS(nations.NAMES[self._data.getNationID()], self._data.getRootCD())

    def onResearchItemsDrawn(self):
        Waiting.hide('draw_research_items')

    def request4Unlock(self, itemCD, parentID, unlockIdx, xpCost):
        self.unlockItem(int(itemCD), int(parentID), int(unlockIdx), int(xpCost))

    def request4Buy(self, itemCD):
        itemCD = int(itemCD)
        itemTypeID, _, _ = vehicles.parseIntCompactDescr(itemCD)
        if itemTypeID == _VEHICLE:
            self.buyVehicle(itemCD)
        else:
            if RequestState.inProcess('buyAndInstall'):
                SystemMessages.pushI18nMessage('#system_messages:shop/item/buy_and_equip_in_processing', type=SystemMessages.SM_TYPE.Warning)
            self.buyAndInstallItem(itemCD, 'buyAndInstall')

    def request4Sell(self, itemCD):
        itemCD = int(itemCD)
        itemTypeID, _, _ = vehicles.parseIntCompactDescr(itemCD)
        if itemTypeID == _VEHICLE:
            self.sellVehicle(itemCD)
        else:
            self.sellItem(itemCD)

    def request4Install(self, itemCD):
        if RequestState.inProcess('install'):
            SystemMessages.pushI18nMessage('#system_messages:inventory/item/equip_in_processing', type=SystemMessages.SM_TYPE.Warning)
        itemCD = int(itemCD)
        self.buyAndInstallItem(itemCD, 'install', inInventory=True)

    def requestModuleInfo(self, pickleDump):
        self.showModuleInfo(pickleDump)

    def requestVehicleInfo(self, pickleDump):
        self.showVehicleInfo(pickleDump)

    def goToTechTree(self, nation):
        self.fireEvent(events.LoadEvent(events.LoadEvent.LOAD_TECHTREE, ctx={'nation': nation}), scope=EVENT_BUS_SCOPE.LOBBY)

    def exitFromResearch(self):
        self.fireEvent(events.LoadEvent(events.LoadEvent.EXIT_FROM_RESEARCH), scope=EVENT_BUS_SCOPE.LOBBY)

    def showSystemMessage(self, typeString, message):
        self.pushSystemMessage(typeString, message)

    @process
    def buyAndInstallItem(self, itemCD, state, inInventory = False):
        itemTypeID, nationID, itemID = vehicles.parseIntCompactDescr(itemCD)
        raise itemTypeID in _RESEARCH_ITEMS or AssertionError
        oldStyleVehicle = self._data.getInvItem(self._data.getRootCD())
        if not oldStyleVehicle is not None:
            raise AssertionError, 'Vehicle has be in inventory'
            eqs = functions.findConflictedEquipments(itemCD, itemTypeID, oldStyleVehicle)
            item = g_itemsCache.items.getItemByCD(itemCD)
            vehicle = g_itemsCache.items.getItemByCD(self._data.getRootCD())
            if not inInventory:
                Waiting.show('buyItem')
                buyResult = yield ModuleBuyer(item, count=1, buyForCredits=True, conflictedEqs=eqs, install=True).request()
                if len(buyResult.userMsg):
                    SystemMessages.g_instance.pushI18nMessage(buyResult.userMsg, type=buyResult.sysMsgType)
                Waiting.hide('buyItem')
            else:
                RequestState.sent(state)
            item = g_itemsCache.items.getItemByCD(itemCD)
            if item is not None and item.isInInventory:
                Waiting.show('applyModule')
                result = yield getInstallerProcessor(vehicle, item).request()
                success = result.success
                if result and result.auxData:
                    for m in result.auxData:
                        SystemMessages.g_instance.pushI18nMessage(m.userMsg, type=m.sysMsgType)

                if result and len(result.userMsg):
                    SystemMessages.g_instance.pushI18nMessage(result.userMsg, type=result.sysMsgType)
                success and itemTypeID in (_GUN, _TURRET) and self.tryLoadShells()
            Waiting.hide('applyModule')
        RequestState.received(state)
        return

    def setInvVehicles(self, data):
        vData = data.get(INV_ITEM_VCDESC_KEY, {})
        currentID = self._data.getNationID()
        rootCD = self._data.getRootCD()
        rootItem = self._data.getInvItem(rootCD)
        inventory = set()
        fullUpdate = False
        if not len(vData):
            invIDs = custom_items._findVehItemsToChange(data)
            mapping = self._data.getInvMapping()
            for invID in invIDs:
                if invID in mapping:
                    vIntCD = mapping[invID]
                    custom_items._changeInventoryVehicle(invID, self._data.getInvItem(vIntCD), data)
                    inventory.add(vIntCD)
                    if vIntCD == rootCD:
                        fullUpdate = True

            return (inventory, fullUpdate)
        else:
            for invID, vStrCD in vData.iteritems():
                if vStrCD is None or not len(vStrCD):
                    vIntCD = self._data.removeInvItem(invID=invID)
                    if vIntCD == rootCD:
                        rootItem = None
                    item = None
                else:
                    vType = vehicles.getVehicleType(vStrCD)
                    nationID, itemID = vType.id
                    if nationID != currentID:
                        continue
                    vIntCD = vehicles.makeIntCompactDescrByID(_VEHICLE_TYPE_NAME, nationID, itemID)
                    item = custom_items._makeInventoryVehicle(invID, vStrCD, data)
                    self._data.setInvItem(vIntCD, item)
                if vIntCD > 0:
                    inventory.add(vIntCD)
                if vIntCD == rootCD:
                    fullUpdate = rootItem is None or item is not None and rootItem.repairCost != item.repairCost

            return (inventory, fullUpdate)

    def setInvItems(self, data):
        currentID = self._data.getNationID()
        result = set()
        for itemCD, count in data.iteritems():
            itemTypeID, nationID, _ = vehicles.parseIntCompactDescr(itemCD)
            if nationID != currentID:
                continue
            if count > 0:
                self._data.setInvItem(itemCD, custom_items._makeInventoryItem(itemTypeID, itemCD, count))
            else:
                self._data.removeInvItem(itemCD=itemCD)
            result.add(itemCD)

        return result

    @process
    def sellItem(self, itemTypeCD):
        if self._data.hasInvItem(itemTypeCD):
            yield DialogsInterface.showDialog(LocalSellModuleMeta(itemTypeCD))
        else:
            self._showMessage4Item(self.MSG_SCOPE.Inventory, 'not_found', itemTypeCD)
            yield lambda callback = None: callback
        return

    @process
    def tryLoadShells(self):
        ammo = yield Requester('shell').getFromInventory()
        message = '#system_messages:charge/inventory_error'
        success = False
        rootCD = self._data.getRootCD()
        item = self._data.getInvItem(rootCD)
        raise item is not None or AssertionError
        for shell in item.shells:
            count = ammo[ammo.index(shell)].count if shell in ammo else 0
            if shell.default > count:
                break
        else:
            success, message = yield item.loadShells(None)

        SystemMessages.pushI18nMessage(message, type=SystemMessages.SM_TYPE.Information if success else SystemMessages.SM_TYPE.Warning)
        return

    def invalidateUnlocks(self, unlocks):
        if self._data.isRedrawNodes(unlocks):
            self.redrawResearchItems()
        else:
            super(Research, self).invalidateUnlocks(unlocks)

    def invalidateInventory(self, data, findItems = False):
        if super(Research, self).invalidateInventory(data, findItems=True):
            self.redrawResearchItems()
            result = True
        else:
            result = self._data.invalidateInstalled()
            if len(result):
                self.as_setInstalledItemsS(result)
        return result

    def invalidateFreeXP(self, freeXP):
        self.as_setFreeXPS(freeXP)
        super(Research, self).invalidateFreeXP(freeXP)

    def invalidateVehLocks(self, locks):
        if self._data.invalidateLocks(locks):
            self.redrawResearchItems()

    @process
    def __startDataCollect(self):
        self._data._xps = yield StatsRequester().getVehicleTypeExperiences()
        self._data._unlocks = yield StatsRequester().getUnlocks()
        self._data._elite = yield StatsRequester().getEliteVehicles()
        self._data._accFreeXP = g_itemsCache.items.stats.actualFreeXP
        self._data._accCredits = g_itemsCache.items.stats.credits
        self._data._accGold = g_itemsCache.items.stats.gold
        accDossier = yield StatsRequester().getAccountDossier()
        if accDossier and accDossier['a15x15Cut']:
            self._data._wereInBattle = set(accDossier['a15x15Cut'].keys())
        BigWorld.player().inventory.getItems(_VEHICLE, self.__onGetVehiclesFromInventory)

    def __onGetVehiclesFromInventory(self, resultID, data):
        if resultID < RES_SUCCESS:
            LOG_ERROR('Server return error inventory vehicle items request: responseCode=', resultID)
            data = {INV_ITEM_VCDESC_KEY: {}}
        self.setInvVehicles(data)
        self.__requestNextInvItems(list(_RESEARCH_ITEMS))

    def __requestNextInvItems(self, itemTypeIDs):
        if len(itemTypeIDs) > 0:
            nextTypeID = itemTypeIDs.pop()
            BigWorld.player().inventory.getItems(nextTypeID, partial(self.__onGetItemsFromInventory, nextTypeID, itemTypeIDs))
        else:
            types = list(_RESEARCH_ITEMS)
            types.append(_VEHICLE)
            self.__requestNextIShopItems(types)

    def __onGetItemsFromInventory(self, itemTypeID, itemTypeIDs, resultID, data):
        if resultID < RES_SUCCESS:
            LOG_ERROR('Server return error inventory %s items request: responseCode=' % ITEM_TYPE_NAMES[itemTypeID], resultID)
            data = {}
        self.setInvItems(data)
        self.__requestNextInvItems(itemTypeIDs)

    def __requestNextIShopItems(self, itemTypeIDs):
        if len(itemTypeIDs) > 0:
            nextTypeID = itemTypeIDs.pop()
            BigWorld.player().shop.getAllItems(partial(self.__onGetItemsFromShop, nextTypeID, itemTypeIDs))
        else:
            self.__stopDataCollect()

    def __onGetItemsFromShop(self, itemTypeID, itemTypeIDs, resultID, data, _):
        if resultID < RES_SUCCESS:
            LOG_ERROR('Server return error shop %s items request: responseCode=' % ITEM_TYPE_NAMES[itemTypeID], resultID)
            data = {}
        parser = ShopDataParser(data)
        for intCD, price, _, _ in parser.getItemsIterator(self._data.getNationID(), itemTypeID):
            self._data.setShopPrice(intCD, price)

        self.__requestNextIShopItems(itemTypeIDs)

    def __stopDataCollect(self):
        if USE_XML_DUMPING and IS_DEVELOPMENT:
            self.as_useXMLDumpingS()
        self.redrawResearchItems()

    def __shop_onResync(self):
        self.__startDataCollect()

    def __center_onIsLongDisconnected(self, isLongDisconnected):
        if not isLongDisconnected:
            self.__startDataCollect()
        else:
            self.redrawResearchItems()

    def __setWalletCallback(self, status):
        self.invalidateFreeXP(g_itemsCache.items.stats.actualFreeXP)
        self.as_setWalletStatusS(status)
# okay decompyling res/scripts/client/gui/scaleform/daapi/view/lobby/techtree/research.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:26:19 EST

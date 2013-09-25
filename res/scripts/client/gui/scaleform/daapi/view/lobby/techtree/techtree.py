# Embedded file name: scripts/client/gui/Scaleform/daapi/view/lobby/techtree/TechTree.py
from functools import partial
import weakref
import BigWorld
from AccountCommands import RES_SUCCESS
import Keys
from PlayerEvents import g_playerEvents
from adisp import process
from constants import IS_DEVELOPMENT
from debug_utils import LOG_DEBUG, LOG_ERROR
from gui.Scaleform.daapi.view.lobby.techtree import custom_items
from gui.Scaleform.daapi.view.lobby.techtree.ResearchView import ResearchView
from gui.Scaleform.daapi.view.meta.TechTreeMeta import TechTreeMeta
from gui.shared.utils.requesters import StatsRequester
from gui.Scaleform.daapi.view.lobby.techtree import dumpers, SelectedNation, _VEHICLE, USE_XML_DUMPING
from gui.Scaleform.daapi.view.lobby.techtree.data import NationTreeData
from gui.Scaleform.daapi.view.lobby.techtree.listeners import StatsListener, InventoryListener, INV_ITEM_VCDESC_KEY
from gui.Scaleform.daapi.view.lobby.techtree.techtree_dp import g_techTreeDP
from gui.shared import events, EVENT_BUS_SCOPE
from items import ITEM_TYPE_NAMES, vehicles
import nations

class TechTree(ResearchView, TechTreeMeta):

    def __init__(self, ctx = None):
        data = NationTreeData()
        if USE_XML_DUMPING and IS_DEVELOPMENT:
            dumper = dumpers.NationXMLDumper()
        else:
            dumper = dumpers.NationObjDumper()
        data.setDumper(dumper)
        super(TechTree, self).__init__(data)
        self._statsListener = StatsListener()
        self._invListener = InventoryListener()
        self._resolveLoadCtx(ctx=ctx)

    def __del__(self):
        LOG_DEBUG('TechTree deleted')

    def _resolveLoadCtx(self, ctx = None):
        nation = ctx['nation'] if ctx is not None and 'nation' in ctx else None
        if nation is not None and nation in nations.INDICES:
            nationIdx = nations.INDICES[nation]
            SelectedNation.select(nationIdx)
        else:
            SelectedNation.byDefault()
        return

    def _populate(self):
        super(TechTree, self)._populate()
        selfProxy = weakref.proxy(self)
        self._statsListener.startListen(selfProxy)
        self._invListener.startListen(selfProxy)
        g_playerEvents.onShopResync += self.__shop_onResync
        g_playerEvents.onCenterIsLongDisconnected += self.__center_onIsLongDisconnected
        if IS_DEVELOPMENT:
            from gui import InputHandler
            InputHandler.g_instance.onKeyUp += self.__handleReloadData

    def _dispose(self):
        self._statsListener.stopListen()
        self._invListener.stopListen()
        g_playerEvents.onShopResync -= self.__shop_onResync
        g_playerEvents.onCenterIsLongDisconnected -= self.__center_onIsLongDisconnected
        if IS_DEVELOPMENT:
            from gui import InputHandler
            InputHandler.g_instance.onKeyUp -= self.__handleReloadData
        super(TechTree, self)._dispose()

    def requestNationTreeData(self):
        if USE_XML_DUMPING and IS_DEVELOPMENT:
            self.as_useXMLDumpingS()
        self.__startDataCollect()
        return True

    def getNationTreeData(self, nationName):
        if nationName not in nations.INDICES:
            LOG_ERROR('Nation not found', nationName)
            return {}
        nationIdx = nations.INDICES[nationName]
        SelectedNation.select(nationIdx)
        self._data.load(nationIdx)
        return self._data.dump()

    def request4Unlock(self, unlockCD, vehCD, unlockIdx, xpCost):
        self.unlockItem(int(unlockCD), int(vehCD), int(unlockIdx), int(xpCost))

    def request4Buy(self, itemCD):
        self.buyVehicle(int(itemCD))

    def request4Sell(self, itemCD):
        self.sellVehicle(int(itemCD))

    def requestVehicleInfo(self, pickleDump):
        self.showVehicleInfo(pickleDump)

    def goToNextVehicle(self, vehCD):
        Event = events.LoadEvent
        exitEvent = Event(Event.LOAD_TECHTREE, ctx={'nation': SelectedNation.getName()})
        loadEvent = Event(Event.LOAD_RESEARCH, ctx={'rootCD': vehCD,
         'exit': exitEvent})
        self.fireEvent(loadEvent, scope=EVENT_BUS_SCOPE.LOBBY)

    def onCloseTechTree(self):
        self.fireEvent(events.LoadEvent(events.LoadEvent.LOAD_HANGAR), scope=EVENT_BUS_SCOPE.LOBBY)

    def showSystemMessage(self, typeString, message):
        self.pushSystemMessage(typeString, message)

    def setInvVehicles(self, data):
        vCDs = data.get(INV_ITEM_VCDESC_KEY, {})
        vTypeName = ITEM_TYPE_NAMES[_VEHICLE]
        result = set()
        for invID, vStrCD in vCDs.iteritems():
            if vStrCD is None or not len(vStrCD):
                vIntCD = self._data.removeInvItem(invID=invID)
            else:
                vType = vehicles.getVehicleType(vStrCD)
                vIntCD = vehicles.makeIntCompactDescrByID(vTypeName, vType.id[0], vType.id[1])
                self._data.setInvItem(vIntCD, custom_items._makeInventoryVehicle(invID, vStrCD, data))
            if vIntCD > 0:
                result.add(vIntCD)

        return (result, False)

    def setInvItems(self, data):
        return set()

    def invalidateVehLocks(self, locks):
        if self._data.invalidateLocks(locks):
            self.as_refreshNationTreeDataS(SelectedNation.getName())

    def invalidateVTypeXP(self, xps):
        super(TechTree, self).invalidateVTypeXP(xps)
        result = self._data.invalidateXpCosts()
        if len(result):
            self.as_setUnlockPropsS(result)

    @process
    def __startDataCollect(self):
        self._data._xps = yield StatsRequester().getVehicleTypeExperiences()
        self._data._unlocks = yield StatsRequester().getUnlocks()
        self._data._elite = yield StatsRequester().getEliteVehicles()
        self._data._accFreeXP = yield StatsRequester().getFreeExperience()
        self._data._accCredits = yield StatsRequester().getCredits()
        self._data._accGold = yield StatsRequester().getGold()
        accDossier = yield StatsRequester().getAccountDossier()
        if accDossier and accDossier['vehDossiersCut']:
            self._data._wereInBattle = set(accDossier['vehDossiersCut'].keys())
        self.__requestVehiclesFromInv()

    def __requestVehiclesFromInv(self):
        BigWorld.player().inventory.getItems(_VEHICLE, self.__onGetVehiclesFromInventory)

    def __onGetVehiclesFromInventory(self, resultID, data):
        if resultID < RES_SUCCESS:
            LOG_ERROR('Server return error inventory vehicle items request: responseCode=', resultID)
            data = {INV_ITEM_VCDESC_KEY: {}}
        self.setInvVehicles(data)
        self.__requestVehiclesFromShop(nations.INDICES.values())

    def __requestVehiclesFromShop(self, nationIDs):
        if len(nationIDs) > 0:
            nextNationID = nationIDs.pop()
            BigWorld.player().shop.getItems(_VEHICLE, nextNationID, partial(self.__onGetVehiclesFromShop, nextNationID, nationIDs))
        else:
            self.__stopDataCollect()

    def __onGetVehiclesFromShop(self, nationID, nationIDs, resultID, data, _):
        if resultID < RES_SUCCESS:
            LOG_ERROR('Server return error shop vehicles request: responseCode=' % resultID)
            data = {}
        dataLen = len(data)
        prices = data[0].iteritems() if dataLen else []
        if dataLen > 1 and 'notInShop' in data[1]:
            self._data.addHidden(nationID, data[1]['notInShop'])
        else:
            self._data.addHidden(nationID, set())
        for innationID, price in prices:
            intCD = vehicles.makeIntCompactDescrByID(ITEM_TYPE_NAMES[_VEHICLE], nationID, innationID)
            self._data.setShopPrice(intCD, price)

        self.__requestVehiclesFromShop(nationIDs)

    def __stopDataCollect(self):
        self.as_setAvailableNationsS(g_techTreeDP.getAvailableNations())
        self.as_setSelectedNationS(SelectedNation.getName())

    def __shop_onResync(self):
        self.__requestVehiclesFromShop(nations.INDICES.values())
        self.as_refreshNationTreeDataS(SelectedNation.getName())

    def __center_onIsLongDisconnected(self, isLongDisconnected):
        if not isLongDisconnected:
            self.__requestVehiclesFromShop(nations.INDICES.values())
        self.as_refreshNationTreeDataS(SelectedNation.getName())

    def __handleReloadData(self, event):
        if event.key is Keys.KEY_R:
            g_techTreeDP.load(isReload=True)
            self.as_refreshNationTreeDataS(SelectedNation.getName())
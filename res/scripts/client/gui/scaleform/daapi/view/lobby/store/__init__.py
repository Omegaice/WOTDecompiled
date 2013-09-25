import MusicController
from CurrentVehicle import g_currentVehicle
from adisp import process
from PlayerEvents import g_playerEvents
from account_helpers.AccountSettings import AccountSettings
from debug_utils import LOG_ERROR, LOG_DEBUG
from gui import GUI_NATIONS, GUI_NATIONS_ORDER_INDEX
from gui.ClientUpdateManager import g_clientUpdateManager
from gui.Scaleform.daapi.view.meta.StoreMeta import StoreMeta
from gui.Scaleform.daapi import LobbySubView
from gui.shared import events, EVENT_BUS_SCOPE
from gui.shared.utils.gui_items import compactItem, getItemByCompact, InventoryVehicle
from gui.shared.utils.requesters import Requester
from items import ITEM_TYPE_INDICES
from items import vehicles
import nations
__author__ = 'd_trofimov'

class Store(LobbySubView, StoreMeta):
    _SHELL = 'shell'
    _MODULE = 'module'
    _VEHICLE = 'vehicle'
    _OPTIONAL_DEVICE = 'optionalDevice'
    _EQUIPMENT = 'equipment'
    _DATA_PROVIDER = 'dataProvider'

    def __init__(self):
        super(Store, self).__init__()
        self.__nations = []
        self.__filterHash = {}
        self.__subFilter = {'current': None,
         self._DATA_PROVIDER: []}
        return

    def _populate(self):
        super(Store, self)._populate()
        self.__filterHash = {'language': -1,
         'type': ''}
        self.__setNations()
        g_clientUpdateManager.addCallbacks({'inventory': self._onFiltersUpdate})
        g_playerEvents.onShopResync += self._update
        MusicController.g_musicController.play(MusicController.MUSIC_EVENT_LOBBY)
        MusicController.g_musicController.play(MusicController.AMBIENT_EVENT_SHOP)
        self.__filterHash = self.__listToNationFilterData(self._getCurrentFilter())
        self._populateFilters(True)

    def _dispose(self):
        super(Store, self)._dispose()
        while len(self.__nations):
            self.__nations.pop()

        self.__nations = None
        self.__filterHash.clear()
        self.__filterHash = None
        self.__clearSubFilter()
        g_playerEvents.onShopResync -= self._update
        g_clientUpdateManager.removeObjectCallbacks(self)
        return

    def __clearSubFilter(self):
        dataProvider = self.__subFilter[self._DATA_PROVIDER]
        while dataProvider:
            dataProvider.pop().clear()

        self.__subFilter.clear()
        self.__subFilter = None
        return

    def _onFiltersUpdate(self, *args):
        pass

    def _update(self, diff = {}):
        pass

    def __setNations(self):
        while len(self.__nations):
            self.__nations.pop()

        for name in GUI_NATIONS:
            if name in nations.AVAILABLE_NAMES:
                self.__nations.append(name)
                self.__nations.append(nations.INDICES[name])

        self.as_setNationsS(self.__nations)

    def getName(self):
        return ''

    def _onRegisterFlashComponent(self, viewPy, alias):
        self._table = viewPy

    @process
    def _populateFilters(self, init = False):
        vehicles = yield Requester(self._VEHICLE).getFromInventory()
        oldStyleVehicle = None
        for v in vehicles:
            if v.inventoryId == g_currentVehicle.invID:
                oldStyleVehicle = v
                break

        filterVehicle = None
        if g_currentVehicle.isPresent():
            filterVehicle = compactItem(oldStyleVehicle)
        filter = self._getCurrentFilter()
        if filter[1] in (self._MODULE, self._SHELL):
            filter = list(AccountSettings.getFilter(self.getName() + '_' + filter[1]))
            typeSize = int(filter.pop(0))
            filterVehicle = filter[typeSize + 1]
        self.__clearSubFilter()
        self.__subFilter = {'current': filterVehicle,
         self._DATA_PROVIDER: []}
        vehicles.sort(reverse=True)
        for v in vehicles:
            filterElement = {'id': compactItem(v),
             'nation': GUI_NATIONS_ORDER_INDEX[nations.NAMES[v.nation]],
             'name': v.name}
            self.__subFilter[self._DATA_PROVIDER].append(filterElement)

        if init:
            lang, itemType = self._getCurrentFilter()
            self.__filterHash.update({'language': lang,
             'type': itemType})
            self.as_setFilterTypeS(self.__filterHash)
        self.as_setSubFilterS(self.__subFilter)
        if init:
            self._updateFilterOptions(self.__filterHash['type'])
            self.as_completeInitS()
        return

    def _onTableUpdate(self, *args):
        params = self._getCurrentFilter()
        filter = AccountSettings.getFilter(self.getName() + '_' + params[1])
        self.requestTableData(params[0], params[1], filter)

    def onCloseButtonClick(self):
        self.fireEvent(events.LoadEvent(events.LoadEvent.LOAD_HANGAR), scope=EVENT_BUS_SCOPE.LOBBY)

    def onShowInfo(self, data):
        vehicleID = data.id
        vehicle = getItemByCompact(vehicleID)
        if vehicle is None:
            return LOG_ERROR('There is error while attempting to show vehicle info window: ', str(vehicleID))
        else:
            if ITEM_TYPE_INDICES[vehicle.itemTypeName] == vehicles._VEHICLE:
                self.fireEvent(events.ShowWindowEvent(events.ShowWindowEvent.SHOW_VEHICLE_INFO_WINDOW, {'vehicleDescr': vehicle.descriptor}))
            else:
                self.fireEvent(events.ShowWindowEvent(events.ShowWindowEvent.SHOW_MODULE_INFO_WINDOW, {'moduleId': vehicle.pack()}))
            return

    def requestFilterData(self, filterType):
        self._updateFilterOptions(filterType)

    def _updateFilterOptions(self, filterType):
        mf = AccountSettings.getFilter(self.getName() + '_' + filterType)
        self.as_setFilterOptionsS(mf)
        self._update()

    def _getCurrentFilter(self):
        outcomeFilter = list(AccountSettings.getFilter(self.getName() + '_current'))
        return [outcomeFilter[0] if outcomeFilter[0] < len(GUI_NATIONS) else -1, outcomeFilter[1]]

    def __listToNationFilterData(self, dataList):
        return {'language': dataList[0],
         'type': dataList[1]}

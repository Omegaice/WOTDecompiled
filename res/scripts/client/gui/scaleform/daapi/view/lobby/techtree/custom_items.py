# Embedded file name: scripts/client/gui/Scaleform/daapi/view/lobby/techtree/custom_items.py
from items import ITEM_TYPE_NAMES, vehicles
from gui.Scaleform.daapi.view.lobby.techtree import _VEHICLE_TYPE_NAME, SMALL_ICONS_PATH
from gui.shared.utils.gui_items import FittingItem, InventoryItem, InventoryVehicle, ShopItem, getItemByCompact
import nations
import pickle
__all__ = ['_makeInventoryItem',
 '_makeInventoryVehicle',
 '_makeShopVehicle',
 '_makeShopItem',
 '_convert4ToolTip']
INVENTORY_ITEM_CREW_IDX = 'crew'
INVENTORY_ITEM_BROKEN_IDX = 'repair'
INVENTORY_ITEM_SETTINGS_IDX = 'settings'
INVENTORY_ITEM_LOCKED_IDX = 'lock'
INVENTORY_ITEM_EQS_IDX = 'eqs'
INVENTORY_ITEM_EQS_LAYOUT_IDX = 'eqsLayout'
INVENTORY_ITEM_SHELLS_IDX = 'shells'
INVENTORY_ITEM_SHELLS_LAYOUT_IDX = 'shellsLayout'

class _ResearchItem(FittingItem):

    def __init__(self, compactDescr):
        self.__descriptor = None
        itemTypeID, nationID, compTypeID = vehicles.parseIntCompactDescr(compactDescr)
        itemTypeName = ITEM_TYPE_NAMES[itemTypeID]
        FittingItem.__init__(self, compactDescr, itemTypeName)
        self.compTypeID = compTypeID
        self.nationID = nationID
        return

    @property
    def descriptor(self):
        if self.__descriptor is None:
            if self.itemTypeName == _VEHICLE_TYPE_NAME:
                self.__descriptor = vehicles.VehicleDescr(typeID=(self.nationID, self.compTypeID))
            else:
                self.__descriptor = vehicles.getDictDescr(self.compactDescr)
        return self.__descriptor

    @property
    def nation(self):
        return self.nationID

    @property
    def nationName(self):
        return nations.NAMES[self.nationID]

    @property
    def smallIcon(self):
        return SMALL_ICONS_PATH % {'type': self.itemTypeName,
         'unicName': self.unicName.replace(':', '-')}

    def pack(self):
        return pickle.dumps([_ResearchItem, (self.compactDescr,)])


class _InventoryItem(InventoryItem):

    @property
    def nationName(self):
        return nations.NAMES[self.nation]

    @property
    def smallIcon(self):
        return SMALL_ICONS_PATH % {'type': self.itemTypeName,
         'unicName': self.unicName.replace(':', '-')}


class _InventoryVehicle(InventoryVehicle):

    @property
    def nationName(self):
        return nations.NAMES[self.nation]

    @property
    def smallIcon(self):
        return SMALL_ICONS_PATH % {'type': self.itemTypeName,
         'unicName': self.unicName.replace(':', '-')}


def _makeInventoryItem(itemTypeID, itemCompactDesc, count):
    return _InventoryItem(itemTypeName=ITEM_TYPE_NAMES[itemTypeID], compactDescr=itemCompactDesc, count=count)


def _makeInventoryVehicle(invID, vCompactDescr, data):
    repairCost, health = data.get(INVENTORY_ITEM_BROKEN_IDX, {}).get(invID, (0, 0))
    lock = data.get(INVENTORY_ITEM_LOCKED_IDX, {}).get(invID, 0)
    if lock is None:
        lock = 0
    return _InventoryVehicle(compactDescr=vCompactDescr, id=invID, crew=data.get(INVENTORY_ITEM_CREW_IDX, {}).get(invID, []), shells=data.get(INVENTORY_ITEM_SHELLS_IDX, {}).get(invID, []), ammoLayout=data.get(INVENTORY_ITEM_SHELLS_LAYOUT_IDX, {}).get(invID, {}), repairCost=repairCost, health=health, lock=lock, equipments=data.get(INVENTORY_ITEM_EQS_IDX, {}).get(invID, [0, 0, 0]), equipmentsLayout=data.get(INVENTORY_ITEM_EQS_LAYOUT_IDX, {}).get(invID, [0, 0, 0]), settings=data.get(INVENTORY_ITEM_SETTINGS_IDX, {}).get(invID, 0))


def _changeInventoryVehicle(invID, item, data):
    repairVehicles = data.get(INVENTORY_ITEM_BROKEN_IDX, {})
    if invID in repairVehicles:
        repair = repairVehicles[invID]
        if repair is not None:
            item.repairCost = repair[0]
            item.health = repair[1]
        else:
            item.repairCost = 0
            item.health = item.descriptor.maxHealth
    shells = data.get(INVENTORY_ITEM_SHELLS_IDX, {}).get(invID)
    if shells is not None:
        item.setShellsList(shells)
    return item


def _findVehItemsToChange(data):
    toChange = set(data.get(INVENTORY_ITEM_BROKEN_IDX, {}).keys())
    toChange |= set(data.get(INVENTORY_ITEM_SHELLS_IDX, {}).keys())
    return toChange


def _makeShopVehicle(itemID, nationID, price):
    return ShopItem(_VEHICLE_TYPE_NAME, itemID, nation=nationID, priceOrder=price)


def _makeShopItem(itemCD, itemTypeID, nationID, price):
    return ShopItem(ITEM_TYPE_NAMES[itemTypeID], itemCD, nation=nationID, priceOrder=price)


def _convert4ToolTip(dump, price):
    item = getItemByCompact(dump)
    if isinstance(item, _ResearchItem):
        itemCD = item.compactDescr
        itemTypeID, nationID, itemID = vehicles.parseIntCompactDescr(itemCD)
        if itemTypeID == vehicles._VEHICLE:
            item = _makeShopVehicle(itemID, nationID, price)
        else:
            item = _makeShopItem(itemCD, itemTypeID, nationID, price)
    return item
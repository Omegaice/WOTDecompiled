# Embedded file name: scripts/client/gui/Scaleform/daapi/view/lobby/techtree/data.py
import BigWorld
from AccountCommands import LOCK_REASON
from CurrentVehicle import g_currentVehicle
from debug_utils import LOG_CURRENT_EXCEPTION, LOG_ERROR, LOG_DEBUG
from gui.Scaleform.daapi.view.lobby.techtree import custom_items
from items import vehicles, getTypeOfCompactDescr, ITEM_TYPE_NAMES
from gui.Scaleform.daapi.view.lobby.techtree import _RESEARCH_ITEMS, _VEHICLE, _TURRET, _GUN, NODE_STATE, makeDefUnlockProps, UnlockProps, MAX_PATH_LIMIT
from gui.Scaleform.daapi.view.lobby.techtree.dumpers import _BaseDumper
from gui.Scaleform.daapi.view.lobby.techtree.techtree_dp import g_techTreeDP
__all__ = ['ResearchItemsData', 'NationTreeData']

class _ItemsData(object):

    def __init__(self):
        super(_ItemsData, self).__init__()
        self._nodes = []
        self._nodesIdx = {}
        self._invItems = {}
        self._shopPrices = {}
        self._accFreeXP = 0
        self._accCredits = 0
        self._accGold = 0
        self._unlocks = set()
        self._xps = {}
        self._elite = set()
        self._wereInBattle = set()
        self._dumper = _BaseDumper()

    def __del__(self):
        LOG_DEBUG('Data deleted:', self)

    def clear(self):
        while len(self._nodes):
            self._nodes.pop().clear()

        self._nodesIdx.clear()
        self._invItems.clear()
        self._shopPrices.clear()
        if self._dumper is not None:
            self._dumper.clear(full=True)
            self._dumper = None
        return

    def setInvItem(self, itemCD, item):
        self._invItems[itemCD] = item

    def getInvItem(self, itemCD):
        return self._invItems.get(itemCD)

    def getItem(self, itemCD):
        if itemCD in self._invItems:
            item = self._invItems[itemCD]
        else:
            item = custom_items._ResearchItem(itemCD)
        return item

    def hasInvItem(self, itemCD):
        return itemCD in self._invItems.keys()

    def removeInvItem(self, itemCD = 0, invID = -1):
        if invID > -1:
            for cd, item in self._invItems.iteritems():
                if item.inventoryId == invID:
                    itemCD = cd
                    break

        if itemCD > 0:
            if self._invItems.pop(itemCD, None) is None:
                itemCD = 0
        return itemCD

    def getInvMapping(self):
        return dict(map(lambda item: (item[1].inventoryId, item[0]), self._invItems.iteritems()))

    def getInventoryItemsCDs(self):
        return self._invItems.keys()

    def setShopPrice(self, itemCD, price):
        self._shopPrices[itemCD] = price

    def getShopPrice(self, itemCD):
        return self._shopPrices.get(itemCD, (0, 0))

    def getVehXP(self, vehCD):
        return self._xps.get(vehCD, 0)

    def isNext2Unlock(self, itemCD):
        raise NotImplementedError, 'Must be overridden in subclass'

    def isUnlocked(self, itemCD):
        return itemCD in self._unlocks

    def setDumper(self, dumper):
        if dumper is not None and isinstance(dumper, _BaseDumper):
            self._dumper = dumper
        return

    def dump(self):
        return self._dumper.dump(self)

    def invalidateCredits(self, accCredits):
        self._accCredits = accCredits
        return self._invalidateMoney(filter(lambda item: NODE_STATE.isBuyForCredits(item['state']), self._getNodesToInvalidate()))

    def invalidateGold(self, gold):
        self._accGold = gold
        return self._invalidateMoney(filter(lambda item: NODE_STATE.isBuyForGold(item['state']), self._getNodesToInvalidate()))

    def invalidateFreeXP(self, freeXP):
        self._accFreeXP = freeXP
        return self._invalidateXP(filter(lambda item: NODE_STATE.NEXT_2_UNLOCK & item['state'], self._getNodesToInvalidate()))

    def invalidateVTypeXP(self, xps):
        self._xps.update(xps)
        filtered = filter(lambda item: NODE_STATE.NEXT_2_UNLOCK & item['state'], self._getNodesToInvalidate())
        return self._invalidateXP(filtered)

    def invalidateElites(self, elites):
        self._elite |= elites
        return self._addStateFlag(filter(lambda node: node['id'] in elites, self._getNodesToInvalidate()), NODE_STATE.ELITE)

    def invalidateInventory(self, nodeCDs):
        result = []
        nodes = filter(lambda node: node['id'] in nodeCDs, self._getNodesToInvalidate())
        for node in nodes:
            nodeCD = node['id']
            state = node['state']
            if self.hasInvItem(nodeCD):
                state = NODE_STATE.addIfNot(state, NODE_STATE.IN_INVENTORY)
                state = NODE_STATE.removeIfHas(state, NODE_STATE.ENOUGH_MONEY)
                if self._canSell(nodeCD):
                    state = NODE_STATE.addIfNot(state, NODE_STATE.CAN_SELL)
                else:
                    state = NODE_STATE.removeIfHas(state, NODE_STATE.CAN_SELL)
            else:
                state = NODE_STATE.removeIfHas(state, NODE_STATE.IN_INVENTORY)
                state = NODE_STATE.removeIfHas(state, NODE_STATE.CAN_SELL)
                state = NODE_STATE.removeIfHas(state, NODE_STATE.SELECTED)
                if self._canBuy(nodeCD):
                    state = NODE_STATE.addIfNot(state, NODE_STATE.ENOUGH_MONEY)
                else:
                    state = NODE_STATE.removeIfHas(state, NODE_STATE.ENOUGH_MONEY)
            node['state'] = state
            result.append((nodeCD, state, self.getItem(nodeCD).pack()))

        return result

    def _getNodesToInvalidate(self):
        return self._nodes

    def _addStateFlag(self, nodes, stateFlag, exclude = None):
        result = []
        for node in nodes:
            nodeCD = node['id']
            state = node['state']
            if not state & stateFlag:
                state |= stateFlag
                if exclude is not None and state & exclude:
                    state ^= exclude
                node['state'] = state
                result.append((nodeCD, state))

        return result

    def _change2Unlocked(self, node):
        state = NODE_STATE.change2Unlocked(node['state'])
        if state < 0:
            return node['state']
        node['state'] = state
        if self._canBuy(node['id']):
            state = NODE_STATE.add(state, NODE_STATE.ENOUGH_MONEY)
        else:
            state = NODE_STATE.remove(state, NODE_STATE.ENOUGH_MONEY)
        if state < 0:
            return node['state']
        node['state'] = state
        return state

    def _canBuy(self, nodeCD):
        gameCredits, gold = self.getShopPrice(nodeCD)
        itemTypeID, _, _ = vehicles.parseIntCompactDescr(nodeCD)
        canBuy = True
        if itemTypeID == _VEHICLE:
            canBuy = not getattr(BigWorld.player(), 'isLongDisconnectedFromCenter', False)
        return canBuy and self._accCredits >= gameCredits and self._accGold >= gold

    def _canSell(self, nodeCD):
        raise NotImplementedError

    def _invalidateMoney(self, nodes):
        result = []
        for node in nodes:
            state = node['state']
            if self._canBuy(node['id']):
                state = NODE_STATE.add(state, NODE_STATE.ENOUGH_MONEY)
            else:
                state = NODE_STATE.remove(state, NODE_STATE.ENOUGH_MONEY)
            if state > -1:
                node['state'] = state
                result.append((node['id'], state))

        return result

    def _invalidateXP(self, nodes):
        result = []
        xpGetter = self._xps.get
        for node in nodes:
            state = node['state']
            props = node['unlockProps']
            xp = xpGetter(props.parentID, 0)
            if self._accFreeXP + xp >= props.xpCost:
                state = NODE_STATE.add(state, NODE_STATE.ENOUGH_XP)
            else:
                state = NODE_STATE.remove(state, NODE_STATE.ENOUGH_XP)
            if state > -1:
                node['state'] = state
                result.append((node['id'], state))

        return result


class ResearchItemsData(_ItemsData):
    _rootCD = None

    def __init__(self):
        super(ResearchItemsData, self).__init__()
        self._autoGunCD = -1
        self._autoTurretCD = -1
        self._topLevel = []
        self._topLevelCDs = {}
        self._installed = []
        self._enableInstallItems = False

    def __loadRoot(self, rootCD):
        item = self.__loadInstalledItems(rootCD)
        node = self._getNodeData(rootCD, self._earnedXP, makeDefUnlockProps(), set(), renderer='root', topLevel=True)
        if item is not None:
            if g_currentVehicle.isPresent() and g_currentVehicle.invID == item.inventoryId:
                node['state'] |= NODE_STATE.SELECTED
        self._nodesIdx[rootCD] = 0
        self._nodes.append(node)
        self.__loadInstalledItems(rootCD)
        return

    def __loadInstalledItems(self, rootCD):
        item = self.getInvItem(rootCD)
        if item is not None:
            self._installed = item.descriptor.getDevices()[1][:]
            self._enableInstallItems = not item.lock and not item.repairCost
        else:
            self._installed = []
            self._enableInstallItems = False
        return item

    def __loadAutoUnlockItems(self, rootCD, autoUnlocks, hasFakeTurrets = False):
        autoUnlocked = dict(map(lambda nodeCD: (vehicles.getDictDescr(nodeCD).get('itemTypeName'), nodeCD), autoUnlocks))
        self._autoGunCD = -1
        self._autoTurretCD = -1
        for itemType in _RESEARCH_ITEMS:
            if itemType > len(ITEM_TYPE_NAMES) - 1:
                continue
            nodeCD = autoUnlocked[ITEM_TYPE_NAMES[itemType]]
            if itemType == _TURRET:
                self._autoTurretCD = nodeCD
                if hasFakeTurrets:
                    continue
            elif itemType == _GUN:
                self._autoGunCD = nodeCD
            node = self._getNodeData(nodeCD, 0, makeDefUnlockProps(), set([rootCD]))
            node['state'] |= NODE_STATE.AUTO_UNLOCKED
            self._nodesIdx[nodeCD] = len(self._nodes)
            self._nodes.append(node)

    def __fixPath(self, itemTypeID, path):
        if self._autoGunCD in path and self._autoTurretCD in path:
            if itemTypeID == _TURRET:
                path.remove(self._autoGunCD)
            elif itemTypeID == _GUN:
                path.remove(self._autoTurretCD)
            elif itemTypeID == _VEHICLE:
                path.remove(self._autoGunCD)
                path.remove(self._autoTurretCD)
        return path

    def __fixLevel(self, itemTypeID, path, maxPath):
        level = -1
        if itemTypeID == _VEHICLE and len(path) <= maxPath:
            level = min(maxPath + 1, MAX_PATH_LIMIT)
        return level

    def __loadItems(self, rootCD, unlocksDs):
        xpGetter = self._xps.get
        maxPath = 0
        nodes = []
        for unlockIdx, data in enumerate(unlocksDs):
            nodeCD = data[1]
            itemTypeID, _, _ = vehicles.parseIntCompactDescr(nodeCD)
            required = set(data[2:])
            required.add(rootCD)
            path = set(data[2:])
            path.add(rootCD)
            path = self.__fixPath(itemTypeID, path)
            maxPath = max(len(path), maxPath)
            nodes.append((nodeCD,
             itemTypeID,
             UnlockProps(rootCD, unlockIdx, data[0], required),
             path))

        invID = g_currentVehicle.invID if g_currentVehicle.isPresent() else -1
        for nodeCD, itemTypeID, props, path in nodes:
            node = self._getNodeData(nodeCD, xpGetter(nodeCD, 0), props, path, level=self.__fixLevel(itemTypeID, path, maxPath))
            if itemTypeID == _VEHICLE:
                item = self.getInvItem(nodeCD)
                if item is not None and invID == item.inventoryId:
                    node['state'] |= NODE_STATE.SELECTED
            self._nodesIdx[nodeCD] = len(self._nodes)
            self._nodes.append(node)

        return

    def __loadTopLevel(self, rootCD):
        xpGetter = self._xps.get
        invID = g_currentVehicle.invID if g_currentVehicle.isPresent() else -1
        while len(self._topLevel):
            self._topLevel.pop().clear()

        self._topLevelCDs.clear()
        for nodeCD in g_techTreeDP.getTopLevel(rootCD):
            node = self._getNodeData(nodeCD, xpGetter(nodeCD, 0), makeDefUnlockProps(), set(), topLevel=True)
            item = self.getInvItem(nodeCD)
            if item is not None and invID == item.inventoryId:
                node['state'] |= NODE_STATE.SELECTED
            self._topLevelCDs[nodeCD] = len(self._topLevel)
            self._topLevel.append(node)

        return

    def _getNodesToInvalidate(self):
        toInvalidate = self._nodes[:]
        toInvalidate.extend(self._topLevel)
        return toInvalidate

    def _findNext2UnlockItems(self, nodes):
        result = []
        topLevelCDs = self._topLevelCDs.keys()
        for node in nodes:
            nodeCD = node['id']
            state = node['state']
            itemTypeID, _, _ = vehicles.parseIntCompactDescr(nodeCD)
            if itemTypeID == _VEHICLE and nodeCD in topLevelCDs:
                available, unlockProps = g_techTreeDP.isNext2Unlock(nodeCD, unlocked=self._unlocks, xps=self._xps, freeXP=self._accFreeXP)
                xp = self._accFreeXP + self._xps.get(unlockProps.parentID, 0)
            else:
                unlockProps = node['unlockProps']
                required = unlockProps.required
                available = len(required) and required.issubset(self._unlocks) and nodeCD not in self._unlocks
                xp = self._accFreeXP + self._earnedXP
            if available and state & NODE_STATE.LOCKED > 0:
                state ^= NODE_STATE.LOCKED
                state = NODE_STATE.addIfNot(state, NODE_STATE.NEXT_2_UNLOCK)
                if xp >= unlockProps.xpCost:
                    state = NODE_STATE.addIfNot(state, NODE_STATE.ENOUGH_XP)
                else:
                    state = NODE_STATE.removeIfHas(state, NODE_STATE.ENOUGH_XP)
                node['state'] = state
                result.append((node['id'], state, unlockProps._makeTuple()))

        return result

    def _canBuy(self, nodeCD):
        result = False
        itemTypeID, _, _ = vehicles.parseIntCompactDescr(nodeCD)
        if (itemTypeID == _VEHICLE or self._enableInstallItems) and super(ResearchItemsData, self)._canBuy(nodeCD):
            result = True
        return result

    def _canSell(self, nodeCD):
        itemTypeID, _, _ = vehicles.parseIntCompactDescr(nodeCD)
        item = self.getInvItem(nodeCD)
        if itemTypeID == _VEHICLE:
            canSell = item.canSell
        else:
            canSell = nodeCD not in self._installed
        return canSell

    def _getNodeData(self, nodeCD, earnedXP, unlockProps, path, level = -1, renderer = None, topLevel = False):
        gameCredits, gold = self.getShopPrice(nodeCD)
        itemTypeID, _, _ = vehicles.parseIntCompactDescr(nodeCD)
        available = False
        xp = 0
        state = NODE_STATE.LOCKED
        if topLevel and itemTypeID == _VEHICLE:
            available, unlockProps = g_techTreeDP.isNext2Unlock(nodeCD, unlocked=self._unlocks, xps=self._xps, freeXP=self._accFreeXP)
            xp = self._accFreeXP + self._xps.get(unlockProps.parentID, 0)
        if nodeCD in self._unlocks:
            state = NODE_STATE.UNLOCKED
            if nodeCD in self._installed:
                state |= NODE_STATE.INSTALLED
            elif nodeCD in self._invItems.keys() and self._invItems[nodeCD].count is not None:
                if len(self._installed) or itemTypeID == _VEHICLE:
                    state |= NODE_STATE.IN_INVENTORY
                if self._canSell(nodeCD):
                    state |= NODE_STATE.CAN_SELL
            elif self._canBuy(nodeCD):
                state |= NODE_STATE.ENOUGH_MONEY
            if nodeCD in self._wereInBattle:
                state |= NODE_STATE.WAS_IN_BATTLE
        elif not topLevel:
            if unlockProps.required.issubset(self._unlocks):
                available = self._rootCD in self._unlocks
                xp = self._accFreeXP + self._earnedXP
            if available:
                state = NODE_STATE.NEXT_2_UNLOCK
                xp >= unlockProps.xpCost and state |= NODE_STATE.ENOUGH_XP
        if nodeCD in self._elite:
            state |= NODE_STATE.ELITE
        if renderer is None:
            renderer = 'vehicle' if itemTypeID == _VEHICLE else 'item'
        return {'id': nodeCD,
         'earnedXP': earnedXP,
         'state': state,
         'unlockProps': unlockProps,
         'shopPrice': (gameCredits, gold),
         'displayInfo': {'path': list(path),
                         'renderer': renderer,
                         'level': level}}

    def clear(self):
        while len(self._topLevel):
            self._topLevel.pop().clear()

        self._topLevelCDs.clear()
        super(ResearchItemsData, self).clear()

    @classmethod
    def setRootCD(cls, cd):
        cls._rootCD = int(cd)

    @classmethod
    def getRootCD(cls):
        return cls._rootCD

    @classmethod
    def clearRootCD(cls):
        cls._rootCD = None
        return

    @classmethod
    def getNationID(cls):
        result = 0
        if cls._rootCD is not None:
            result = vehicles.getVehicleType(cls._rootCD).id[0]
        return result

    def isRedrawNodes(self, unlocks):
        return self._rootCD in unlocks

    def getRootStatusString(self):
        status = ''
        item = self.getInvItem(self._rootCD)
        if item is not None:
            if item.lock == LOCK_REASON.ON_ARENA:
                status = 'battle'
            elif item.lock == LOCK_REASON.PREBATTLE:
                status = 'inPrebattle'
            elif item.repairCost > 0:
                status = 'destroyed'
        return status

    def isEnableInstallItems(self):
        return self._enableInstallItems

    def isNext2Unlock(self, nodeCD):
        itemTypeID, _, _ = vehicles.parseIntCompactDescr(nodeCD)
        topLevelCDs = []
        if itemTypeID == _VEHICLE:
            topLevelCDs = map(lambda node: node['id'], self._topLevel)
        if nodeCD in topLevelCDs:
            result, _ = g_techTreeDP.isNext2Unlock(nodeCD, unlocked=self._unlocks, xps=self._xps, freeXP=self._accFreeXP)
        else:
            try:
                node = self._nodes[self._nodesIdx[nodeCD]]
                result = node['unlockProps'].required.issubset(self._unlocks)
            except (KeyError, IndexError):
                result = False

        return result

    def load(self):
        vTypeCD = self.getRootCD()
        raise vTypeCD is not None or AssertionError
        g_techTreeDP.load()
        while len(self._nodes):
            self._nodes.pop().clear()

        self._nodesIdx.clear()
        root = vehicles.getVehicleType(vTypeCD)
        unlocksDs = root.unlocksDescrs
        vTypeCD = root.compactDescr
        self._earnedXP = self._xps.get(vTypeCD, 0)
        hasFakeTurrets = len(root.hull.get('fakeTurrets', {}).get('lobby', ())) != 0 and root.tags & set(['SPG', 'AT-SPG'])
        self.__loadRoot(vTypeCD)
        self.__loadAutoUnlockItems(vTypeCD, root.autounlockedItems, hasFakeTurrets)
        self.__loadItems(vTypeCD, unlocksDs)
        self.__loadTopLevel(vTypeCD)
        return

    def invalidateVTypeXP(self, xps):
        if self._rootCD in xps:
            self._earnedXP = xps[self._rootCD]
        return super(ResearchItemsData, self).invalidateVTypeXP(xps)

    def invalidateUnlocks(self, unlocks):
        self._unlocks |= unlocks
        mapping = dict(map(lambda item: (item['id'], item), self._getNodesToInvalidate()))
        unlocked = []
        for nodeCD in unlocks:
            if nodeCD in mapping:
                node = mapping[nodeCD]
                unlocked.append((nodeCD, self._change2Unlocked(node)))
                mapping.pop(nodeCD)

        next2Unlock = self._findNext2UnlockItems(mapping.values())
        return (next2Unlock, unlocked)

    def invalidateInstalled(self):
        self.__loadInstalledItems(self._rootCD)
        nodes = self._getNodesToInvalidate()
        result = []
        for node in nodes:
            nodeCD = node['id']
            state = node['state']
            if nodeCD in self._installed:
                state = NODE_STATE.add(state, NODE_STATE.INSTALLED)
            else:
                state = NODE_STATE.remove(state, NODE_STATE.INSTALLED)
            if nodeCD in self._elite:
                state = NODE_STATE.add(state, NODE_STATE.ELITE)
            if state > -1:
                node['state'] = state
                result.append((nodeCD, state, self.getItem(nodeCD).pack()))

        return result

    def invalidateLocks(self, locks):
        result = False
        inventory = self.getInvMapping()
        for invID, lock in locks.iteritems():
            if lock is None:
                lock = 0
            if invID in inventory.keys():
                itemCD = inventory[invID]
                self._invItems[itemCD].lock = lock
                if itemCD in self._nodesIdx or itemCD in self._topLevelCDs:
                    result = True

        return result


class NationTreeData(_ItemsData):

    def __init__(self):
        super(NationTreeData, self).__init__()
        self._displaySettings = {}
        self._scrollIndex = -1
        self._hidden = {}

    def _changeNext2Unlock(self, nodeCD, unlockProps):
        state = NODE_STATE.NEXT_2_UNLOCK
        totalXP = self._accFreeXP + self._xps.get(unlockProps.parentID, 0)
        if totalXP >= unlockProps.xpCost:
            state = NODE_STATE.addIfNot(state, NODE_STATE.ENOUGH_XP)
        else:
            state = NODE_STATE.removeIfHas(state, NODE_STATE.ENOUGH_XP)
        if nodeCD in self._elite:
            state = NODE_STATE.addIfNot(state, NODE_STATE.ELITE)
        try:
            data = self._nodes[self._nodesIdx[nodeCD]]
            data['state'] = state
            data['unlockProps'] = unlockProps
        except KeyError:
            LOG_CURRENT_EXCEPTION()

        return state

    def _change2UnlockedByCD(self, nodeCD):
        try:
            node = self._nodes[self._nodesIdx[nodeCD]]
        except KeyError:
            LOG_CURRENT_EXCEPTION()
            return 0

        return self._change2Unlocked(node)

    def _getNodeData(self, nodeCD, displayInfo, invCDs):
        earnedXP = self._xps.get(nodeCD, 0)
        gameCredits, gold = self.getShopPrice(nodeCD)
        state = NODE_STATE.LOCKED
        available, unlockProps = g_techTreeDP.isNext2Unlock(nodeCD, unlocked=self._unlocks, xps=self._xps, freeXP=self._accFreeXP)
        if nodeCD in self._unlocks:
            state = NODE_STATE.UNLOCKED
            if nodeCD in invCDs:
                state |= NODE_STATE.IN_INVENTORY
                if self._canSell(nodeCD):
                    state |= NODE_STATE.CAN_SELL
            elif self._canBuy(nodeCD):
                state |= NODE_STATE.ENOUGH_MONEY
            if nodeCD in self._wereInBattle:
                state |= NODE_STATE.WAS_IN_BATTLE
        elif available:
            state = NODE_STATE.NEXT_2_UNLOCK
            totalXP = self._accFreeXP + self._xps.get(unlockProps.parentID, 0)
            if totalXP >= unlockProps.xpCost:
                state |= NODE_STATE.ENOUGH_XP
        if nodeCD in self._elite:
            state |= NODE_STATE.ELITE
        return {'id': nodeCD,
         'earnedXP': earnedXP,
         'state': state,
         'unlockProps': unlockProps,
         'shopPrice': (gameCredits, gold),
         'displayInfo': displayInfo}

    def load(self, nationID):
        self._nodes = []
        self._nodesIdx = {}
        self._scrollIndex = -1
        vehicleList = sorted(vehicles.g_list.getList(nationID).values(), key=lambda item: item['level'])
        g_techTreeDP.load()
        self._displaySettings = g_techTreeDP.getDisplaySettings(nationID)
        invCDs = self._invItems.keys()
        getDisplayInfo = g_techTreeDP.getDisplayInfo
        selectedID = ResearchItemsData.getRootCD()
        hidden = self._hidden.get(nationID, set())
        for item in vehicleList:
            nodeCD = item['compactDescr']
            displayInfo = getDisplayInfo(nodeCD)
            if displayInfo is not None:
                index = len(self._nodes)
                if item['id'] in hidden:
                    continue
                if nodeCD == selectedID:
                    self._scrollIndex = index
                self._nodesIdx[nodeCD] = index
                self._nodes.append(self._getNodeData(nodeCD, displayInfo, invCDs))

        ResearchItemsData.clearRootCD()
        if g_currentVehicle.isPresent():
            vehicle = g_currentVehicle.item
            if nationID == vehicle.nationID:
                nodeCD = vehicle.intCD
                if nodeCD in self._nodesIdx.keys():
                    index = self._nodesIdx[nodeCD]
                    node = self._nodes[index]
                    if self._scrollIndex < 0:
                        self._scrollIndex = index
                    if nodeCD in self._invItems.keys():
                        node['state'] |= NODE_STATE.SELECTED
                    else:
                        LOG_ERROR('Current vehicle not found in inventory', nodeCD)
                else:
                    _, _, itemID = vehicles.parseIntCompactDescr(nodeCD)
                    if itemID in hidden:
                        LOG_DEBUG('Current vehicle is hidden. Is it define in nation tree:', nodeCD, getDisplayInfo(nodeCD) is not None)
                    else:
                        LOG_ERROR('Current vehicle not found in nation tree', nodeCD)
        return

    def isNext2Unlock(self, nodeCD):
        result, _ = g_techTreeDP.isNext2Unlock(nodeCD, unlocked=self._unlocks, xps=self._xps, freeXP=self._accFreeXP)
        return result

    def addHidden(self, nationID, indexes):
        self._hidden[nationID] = indexes

    def invalidateUnlocks(self, unlocks):
        self._unlocks |= unlocks
        next2Unlock = []
        unlocked = []
        items = g_techTreeDP.getNext2UnlockByItems(unlocks, unlocked=self._unlocks, xps=self._xps, freeXP=self._accFreeXP)
        if len(items):
            next2Unlock = map(lambda item: (item[0], self._changeNext2Unlock(item[0], item[1]), item[1]._makeTuple()), items.iteritems())
        filtered = filter(lambda unlock: getTypeOfCompactDescr(unlock) == _VEHICLE, unlocks)
        if len(filtered):
            unlocked = map(lambda item: (item, self._change2UnlockedByCD(item)), filtered)
        return (next2Unlock, unlocked)

    def invalidateXpCosts(self):
        result = []
        nodes = filter(lambda item: NODE_STATE.NEXT_2_UNLOCK & item['state'], self._getNodesToInvalidate())
        for node in nodes:
            nodeCD = node['id']
            props = node['unlockProps']
            _, newProps = g_techTreeDP.isNext2Unlock(nodeCD, unlocked=self._unlocks, xps=self._xps, freeXP=self._accFreeXP)
            if newProps.parentID != props.parentID:
                node['unlockProps'] = newProps
                result.append((nodeCD, newProps))

        return result

    def invalidateLocks(self, locks):
        result = False
        inventory = self.getInvMapping()
        for invID, lock in locks.iteritems():
            if lock is None:
                lock = 0
            if invID in inventory.keys():
                itemCD = inventory[invID]
                self._invItems[itemCD].lock = lock
                if itemCD in self._nodesIdx:
                    result = True

        return result

    def _canSell(self, nodeCD):
        return self.getInvItem(nodeCD).canSell
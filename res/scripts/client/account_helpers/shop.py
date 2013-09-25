import AccountCommands
import items
import nations
import constants
import BigWorld
from functools import partial
from math import ceil
from itertools import izip
from items import vehicles, tankmen
from AccountCommands import BUY_VEHICLE_FLAG
from account_shared import AmmoIterator
from SyncController import SyncController
from PlayerEvents import g_playerEvents as events
from debug_utils import *
_VEHICLE = items.ITEM_TYPE_INDICES['vehicle']
_CHASSIS = items.ITEM_TYPE_INDICES['vehicleChassis']
_TURRET = items.ITEM_TYPE_INDICES['vehicleTurret']
_GUN = items.ITEM_TYPE_INDICES['vehicleGun']
_ENGINE = items.ITEM_TYPE_INDICES['vehicleEngine']
_FUEL_TANK = items.ITEM_TYPE_INDICES['vehicleFuelTank']
_RADIO = items.ITEM_TYPE_INDICES['vehicleRadio']
_TANKMAN = items.ITEM_TYPE_INDICES['tankman']
_OPTIONALDEVICE = items.ITEM_TYPE_INDICES['optionalDevice']
_SHELL = items.ITEM_TYPE_INDICES['shell']
_EQUIPMENT = items.ITEM_TYPE_INDICES['equipment']

class Shop(object):

    def __init__(self):
        self.__account = None
        self.__syncController = None
        self.__cache = {}
        self.__ignore = True
        self.__isSynchronizing = False
        self.__syncID = 0
        self.__isFirstSync = True
        return

    def onAccountBecomePlayer(self):
        self.__ignore = False
        self.__isFirstSync = True
        self.synchronize()

    def onAccountBecomeNonPlayer(self):
        self.__ignore = True
        self.__isSynchronizing = False

    def setAccount(self, account):
        self.__account = account
        if self.__syncController is not None:
            self.__syncController.destroy()
            self.__syncController = None
        if account is not None:
            self.__syncController = SyncController(account, self.__sendSyncRequest, self.__onSyncResponse, self.__onSyncComplete)
        return

    def synchronize(self, serverCacheRev = None):
        LOG_MX('Shop.synchronize: cli_rev=%s, serv_rev=%s' % (self.__getCacheRevision(), serverCacheRev))
        if self.__ignore:
            return
        elif self.__getCacheRevision() == serverCacheRev:
            return
        elif self.__isSynchronizing:
            return
        else:
            self.__isSynchronizing = True
            if not self.__isFirstSync:
                events.onShopResyncStarted()
            self.__syncController.request(self.__getNextSyncID(), None)
            return

    def resynchronize(self):
        LOG_MX('resynchronize')
        if self.__ignore:
            return
        else:
            self.__cache.clear()
            self.__isSynchronizing = True
            events.onShopResyncStarted()
            self.__syncController.request(self.__getNextSyncID(), None)
            return

    def waitForSync(self, callback):
        if self.__ignore:
            if callback is not None:
                callback(AccountCommands.RES_NON_PLAYER, None)
            return
        elif not self.__isSynchronizing:
            callback(AccountCommands.RES_CACHE, self.__getCacheRevision())
            return
        else:
            proxy = lambda resultID, data: callback(resultID, self.__getCacheRevision())
            self.__syncController.request(self.__syncID, proxy)
            return

    def getCache(self, callback):
        self.__getValue(None, callback)
        return

    def getItems(self, itemTypeIdx, nationIdx, callback):
        proxy = lambda resultID, items, rev: self.__onGetItemsResponse(resultID, itemTypeIdx, nationIdx, callback)
        self.__getValue('items', proxy)

    def getAllItems(self, callback):
        self.__getValue('items', callback)

    def getSellPriceModifiers(self, compDescr, callback):
        proxy = lambda resultID, _data, rev: self.__onGetSellPriceModifiers(resultID, compDescr, callback)
        self.__getValue('sellPriceModif', proxy)

    def getSellPrice(self, buyPrice, sellPriceModifiers, itemTypeID):
        shopRev, exchangeRate, exchangeRateForShellsAndEqs, sellPriceModif, sellPriceFactor, sellForGold = sellPriceModifiers
        if not shopRev == self.__getCacheRevision():
            raise AssertionError
            if itemTypeID in (_SHELL, _EQUIPMENT):
                exchangeRate = exchangeRateForShellsAndEqs
            sellPrice = sellForGold and (int(ceil(sellPriceFactor * buyPrice[0])), int(ceil(sellPriceFactor * buyPrice[1])))
        else:
            sellPrice = (int(ceil(sellPriceFactor * (buyPrice[0] + buyPrice[1] * exchangeRate))), 0)
        return sellPrice

    def getPrice(self, itemTypeIdx, nationIdx, itemShopID, callback):
        proxy = lambda resultID, items, rev: self.__onGetPriceResponse(resultID, itemTypeIdx, nationIdx, itemShopID, callback)
        self.__getValue('items', proxy)

    def getVehiclePrice(self, vehCompDescr, callback):
        proxy = lambda resultID, items, rev: self.__onGetVehiclePriceResponse(resultID, vehCompDescr, False, callback)
        self.__getValue('items', proxy)

    def getVehicleSellPrice(self, vehCompDescr, callback):
        proxy = lambda resultID, items, rev: self.__onGetVehiclePriceResponse(resultID, vehCompDescr, True, callback)
        self.__getValue('items', proxy)

    def getVehiclesSellPrices(self, vehCompDescrs, callback):
        proxy = lambda resultID, items, rev: self.__onGetVehiclesSellPriceResponse(resultID, vehCompDescrs, callback)
        self.__getValue('items', proxy)

    def getComponentPrice(self, compDescr, callback):
        proxy = lambda resultID, items, rev: self.__onGetComponentPriceResponse(resultID, compDescr, False, callback)
        self.__getValue('items', proxy)

    def getComponentSellPrice(self, compDescr, callback):
        proxy = lambda resultID, items, rev: self.__onGetComponentPriceResponse(resultID, compDescr, True, callback)
        self.__getValue('items', proxy)

    def getComponentsSellPrice(self, compDescrs, callback):
        proxy = lambda resultID, items, rev: self.__onGetComponentsPriceResponse(resultID, compDescrs, callback)
        self.__getValue('items', proxy)

    def getAmmoSellPrice(self, ammo, callback):
        proxy = lambda resultID, items, rev: self.__onGetAmmoSellPriceResponse(resultID, ammo, callback)
        self.__getValue('items', proxy)

    def getDailyXPFactor(self, callback):
        self.__getValue('dailyXPFactor', callback)

    def getSlotsPrices(self, callback):
        self.__getValue('slotsPrices', callback)

    def getNextSlotPrice(self, slots, slotsPrices):
        addSlotNumber = slots - slotsPrices[0]
        if addSlotNumber < 0:
            return 0
        if addSlotNumber < len(slotsPrices[1]):
            return slotsPrices[1][addSlotNumber]
        return slotsPrices[1][-1]

    def getBerthsPrices(self, callback):
        self.__getValue('berthsPrices', callback)

    def getNextBerthPackPrice(self, berths, berthsPrices):
        addPackNumber = (berths - berthsPrices[0]) / berthsPrices[1]
        if addPackNumber < 0:
            return 0
        if addPackNumber < len(berthsPrices[2]):
            return berthsPrices[2][addPackNumber]
        return berthsPrices[2][-1]

    def getExchangeRate(self, callback):
        self.__getValue('exchangeRate', callback)

    def getExchangeRateForShellsAndEqs(self, callback):
        self.__getValue('exchangeRateForShellsAndEqs', callback)

    def isEnabledBuyingGoldShellsForCredits(self, callback):
        self.__getValue('isEnabledBuyingGoldShellsForCredits', callback)

    def isEnabledBuyingGoldEqsForCredits(self, callback):
        self.__getValue('isEnabledBuyingGoldEqsForCredits', callback)

    def getFreeXPToTManXPRate(self, callback):
        self.__getValue('freeXPToTManXPRate', callback)

    def ebankVCoinExchangeRate(self, callback):
        self.__getValue('ebank/vcoinExchangeRate', callback)

    def ebankMinTransactionValue(self, callback):
        self.__getValue('ebank/vcoinMinTransactionValue', callback)

    def ebankMaxTransactionValue(self, callback):
        self.__getValue('ebank/vcoinMaxTransactionValue', callback)

    def getFreeXPConversion(self, callback):
        self.__getValue('freeXPConversion', callback)

    def getPremiumCost(self, callback):
        self.__getValue('premiumCost', callback)

    def getTradeFees(self, callback):
        self.__getValue('tradeFees', callback)

    def getTankmanCost(self, callback):
        self.__getValue('tankmanCost', callback)

    def getDropSkillsCost(self, callback):
        self.__getValue('dropSkillsCost', callback)

    def getPassportChangeCost(self, callback):
        self.__getValue('passportChangeCost', callback)

    def getPaidRemovalCost(self, callback):
        self.__getValue('paidRemovalCost', callback)

    def getCamouflageCost(self, callback):
        self.__getValue('camouflageCost', callback)

    def getPlayerEmblemCost(self, callback):
        self.__getValue('playerEmblemCost', callback)

    def getPlayerInscriptionCost(self, callback):
        self.__getValue('playerInscriptionCost', callback)

    def getHornCost(self, callback):
        self.__getValue('hornCost', callback)

    def getGoldPackets(self, callback):
        return self.__getValue('goldPackets', callback)

    def buy(self, itemTypeIdx, nationIdx, itemShopID, count, goldForCredits, callback):
        if self.__ignore:
            if callback is not None:
                callback(AccountCommands.RES_NON_PLAYER, {})
            return
        elif itemTypeIdx == _VEHICLE:
            self.buyVehicle(nationIdx, itemShopID, False, True, 0, callback)
            return
        else:
            count = int(round(count))
            if callback is not None:
                proxy = lambda requestID, resultID, errorStr, ext = {}: callback(resultID)
            else:
                proxy = None
            self.__account._doCmdInt4(AccountCommands.CMD_BUY_ITEM, self.__getCacheRevision(), itemShopID, count, goldForCredits, proxy)
            return

    def buyAndEquipItem(self, vehInvID, compDescr, slotIdx, isPaidRemoval, gunCompDescr, callback):
        if self.__ignore:
            if callback is not None:
                callback(AccountCommands.RES_NON_PLAYER, '', {})
            return
        else:
            if callback is not None:
                proxy = lambda requestID, resultID, errorStr, ext = {}: callback(resultID, errorStr, ext)
            else:
                proxy = None
            arr = [self.__getCacheRevision(),
             compDescr,
             vehInvID,
             slotIdx,
             isPaidRemoval,
             gunCompDescr]
            self.__account._doCmdIntArr(AccountCommands.CMD_BUY_AND_EQUIP_ITEM, arr, proxy)
            return

    def buyAndEquipTankman(self, vehInvID, slot, tmanCostTypeIdx, callback):
        if self.__ignore:
            if callback is not None:
                callback(AccountCommands.RES_NON_PLAYER, '', {})
            return
        else:
            if callback is not None:
                proxy = lambda requestID, resultID, errorStr, ext = {}: callback(resultID, errorStr, ext)
            else:
                proxy = None
            self.__account._doCmdInt4(AccountCommands.CMD_BUY_AND_EQUIP_TMAN, self.__getCacheRevision(), vehInvID, slot, tmanCostTypeIdx, proxy)
            return

    def buyVehicle(self, nationIdx, innationIdx, buyShells, recruitCrew, tmanCostTypeIdx, callback):
        if self.__ignore:
            if callback is not None:
                callback(AccountCommands.RES_NON_PLAYER, {})
            return
        else:
            typeCompDescr = vehicles.makeIntCompactDescrByID('vehicle', nationIdx, innationIdx)
            flags = BUY_VEHICLE_FLAG.NONE
            if buyShells:
                flags |= BUY_VEHICLE_FLAG.SHELLS
            if recruitCrew:
                flags |= BUY_VEHICLE_FLAG.CREW
            if callback is not None:
                proxy = lambda requestID, resultID, errorStr, ext = {}: callback(resultID)
            else:
                proxy = None
            self.__account._doCmdInt4(AccountCommands.CMD_BUY_VEHICLE, self.__getCacheRevision(), typeCompDescr, flags, tmanCostTypeIdx, proxy)
            return

    def buyTankman(self, nationIdx, innationIdx, role, tmanCostTypeIdx, callback):
        vehTypeCompDescr = vehicles.makeIntCompactDescrByID('vehicle', nationIdx, innationIdx)
        roleIdx = tankmen.SKILL_INDICES[role]
        if callback is not None:
            proxy = lambda requestID, resultID, errorStr, ext = {}: callback(resultID, ext.get('tmanInvID', None), ext.get('tmanCompDescr', None))
        else:
            proxy = None
        self.__account._doCmdInt4(AccountCommands.CMD_BUY_TMAN, self.__getCacheRevision(), vehTypeCompDescr, roleIdx, tmanCostTypeIdx, proxy)
        return

    def __onSyncResponse(self, syncID, resultID, ext = {}):
        if resultID == AccountCommands.RES_NON_PLAYER:
            return
        if syncID != self.__syncID:
            return
        if resultID < 0:
            LOG_ERROR('Shop synchronization failed. Repeating')
            self.resynchronize()
            return
        self.__isSynchronizing = False

    def __onSyncComplete(self, syncID, data):
        if syncID != self.__syncID:
            return
        elif data is None:
            return
        else:
            for nationIdx, nationShop in data['items'].iteritems():
                if nationIdx == nations.NONE_INDEX:
                    continue
                camouflages = vehicles.g_cache.customization(nationIdx).get('camouflages', None)
                if camouflages is None:
                    continue
                vehList = vehicles.g_list.getList(nationIdx)
                vehPrices, _ = nationShop[_VEHICLE]
                for inNationIdx, price in vehPrices.iteritems():
                    if constants.IS_DEVELOPMENT:
                        try:
                            vehList[inNationIdx]
                        except Exception:
                            from gui.Scaleform.Waiting import Waiting
                            LOG_ERROR('Shop synchronization problem: Please, make sure to update your client version.')
                            Waiting.close()

                    vehInfo = vehList[inNationIdx]
                    vehType = vehicles.getVehicleType(vehInfo['compactDescr'])
                    if vehType.camouflagePriceFactor != price[2] or vehType.hornPriceFactor != price[3]:
                        vehType.camouflagePriceFactor = price[2]
                        vehType.hornPriceFactor = price[3]
                    vehPrices[inNationIdx] = (price[0], price[1])

                for id, priceFactor in data['customization'][nationIdx]['camouflages'].iteritems():
                    camouflage = camouflages[id]
                    if camouflage['priceFactor'] != priceFactor:
                        LOG_DZ('Camouflage updated: id=%s, priceFactor:%s->%s' % (id, camouflage['priceFactor'], priceFactor))
                        camouflage['priceFactor'] = priceFactor

            emblemGroups = vehicles.g_cache.playerEmblems()[0]
            for groupName, priceFactor in data.get('playerEmblems', {}).get('groups', {}).iteritems():
                emblemIDs, showInShop, priceFactorOld, groupUserString = emblemGroups[groupName]
                if priceFactorOld != priceFactor:
                    LOG_DZ('Emblem group updated: name=%s, priceFactor:%s->%s' % (groupName, priceFactorOld, priceFactor))
                    emblemGroups[groupName] = (emblemIDs,
                     showInShop,
                     priceFactor,
                     groupUserString)

            self.__cache = data
            self.__isSynchronizing = False
            if self.__isFirstSync:
                self.__isFirstSync = False
            else:
                events.onShopResync()
            return

    def __onGetItemsResponse(self, resultID, itemTypeIdx, nationIdx, callback):
        if resultID < 0:
            items = None
        else:
            items = self.__cache.get('items', {}).get(nationIdx, {}).get(itemTypeIdx, None)
        if callback is not None:
            callback(resultID, items, self.__getCacheRevision())
        return

    def __onGetValueResponse(self, resultID, key, callback):
        if resultID < 0:
            if callback is not None:
                callback(resultID, None, self.__getCacheRevision())
            return
        elif self.__isSynchronizing:
            self.__getValue(key, callback)
            return
        else:
            value = self.__cache if key is None else self.__cache.get(key, None)
            if callback is not None:
                callback(resultID, value, self.__getCacheRevision())
            return

    def __onGetPriceResponse(self, resultID, itemTypeIdx, nationIdx, itemShopID, callback):
        if resultID < 0:
            price = None
        else:
            price = self.__getPriceFromCache(itemTypeIdx, nationIdx, itemShopID)
        if callback is not None:
            callback(resultID, price, self.__getCacheRevision())
        return

    def __onGetVehiclePriceResponse(self, resultID, vehCompDescr, isSellPrice, callback):
        if resultID < 0:
            if callback is not None:
                callback(resultID, None, self.__getCacheRevision())
            return
        else:
            price = self.__getVehiclePriceFromCache(vehCompDescr, None)
            if isSellPrice and price is not None:
                nationIdx, innationIdx = vehicles.parseVehicleCompactDescr(vehCompDescr)
                price = self.getSellPrice(price, self.__getSellPriceModifiersFromCache(_VEHICLE, nationIdx, innationIdx), _VEHICLE)
            if callback is not None:
                callback(resultID, price, self.__getCacheRevision())
            return

    def __onGetVehiclesSellPriceResponse(self, resultID, vehCompDescrs, callback):
        if resultID < 0:
            if callback is not None:
                callback(resultID, None, self.__getCacheRevision())
            return
        else:
            prices = []
            for vehCompDescr in vehCompDescrs:
                price = self.__getVehiclePriceFromCache(vehCompDescr, None)
                if price is None:
                    prices = None
                    break
                nationIdx, innationIdx = vehicles.parseVehicleCompactDescr(vehCompDescr)
                prices.append(self.getSellPrice(price, self.__getSellPriceModifiersFromCache(_VEHICLE, nationIdx, innationIdx), _VEHICLE))

            if callback is not None:
                callback(resultID, prices, self.__getCacheRevision())
            return

    def __onGetComponentPriceResponse(self, resultID, compDescr, isSellPrice, callback):
        if resultID < 0:
            if callback is not None:
                callback(resultID, None, self.__getCacheRevision())
            return
        else:
            itemTypeIdx, nationIdx, innationIdx = vehicles.parseIntCompactDescr(compDescr)
            price = self.__getPriceFromCache(itemTypeIdx, nationIdx, compDescr)
            if isSellPrice:
                price = self.getSellPrice(price, self.__getSellPriceModifiersFromCache(itemTypeIdx, nationIdx, innationIdx), itemTypeIdx)
            if callback is not None:
                callback(resultID, price, self.__getCacheRevision())
            return

    def __onGetComponentsPriceResponse(self, resultID, compDescrs, callback):
        if resultID < 0:
            if callback is not None:
                callback(resultID, None, self.__getCacheRevision())
            return
        else:
            prices = []
            for compDescr in compDescrs:
                itemTypeIdx, nationIdx, innationIdx = vehicles.parseIntCompactDescr(compDescr)
                if itemTypeIdx == _VEHICLE:
                    continue
                price = self.__getPriceFromCache(itemTypeIdx, nationIdx, compDescr, None)
                if price is None:
                    prices = None
                    break
                prices.append(self.getSellPrice(price, self.__getSellPriceModifiersFromCache(itemTypeIdx, nationIdx, innationIdx), itemTypeIdx))

            if callback is not None:
                callback(resultID, prices, self.__getCacheRevision())
            return

    def __onGetAmmoSellPriceResponse(self, resultID, ammo, callback):
        if resultID < 0:
            if callback is not None:
                callback(resultID, None, self.__getCacheRevision())
            return
        else:
            price = 0
            for shellCompDescr, count in AmmoIterator(ammo):
                if count == 0:
                    continue
                itemTypeIdx, nationIdx, innationIdx = vehicles.parseIntCompactDescr(shellCompDescr)
                shellPrice = self.__getPriceFromCache(_SHELL, nationIdx, shellCompDescr)
                shellSellPrice = self.getSellPrice(shellPrice, self.__getSellPriceModifiersFromCache(itemTypeIdx, nationIdx, innationIdx), _SHELL)
                price += shellSellPrice * count

            if callback is not None:
                callback(resultID, price, self.__getCacheRevision())
            return

    def __onGetSellPriceModifiers(self, resultID, compDescr, callback):
        if type(compDescr) == str:
            itemTypeIdx, (nationIdx, innationIdx) = _VEHICLE, vehicles.parseVehicleCompactDescr(compDescr)
        else:
            itemTypeIdx, nationIdx, innationIdx = vehicles.parseIntCompactDescr(compDescr)
        callback(resultID, self.__getSellPriceModifiersFromCache(itemTypeIdx, nationIdx, innationIdx))

    def __getNextSyncID(self):
        self.__syncID += 1
        if self.__syncID > 30000:
            self.__syncID = 1
        return self.__syncID

    def __sendSyncRequest(self, id, proxy):
        if self.__ignore:
            return
        clientRev = self.__getCacheRevision()
        self.__account._doCmdInt3(AccountCommands.CMD_SYNC_SHOP, clientRev, 0, 0, proxy)

    def __getCacheRevision(self):
        return self.__cache.get('rev', 0)

    def __getPriceFromCache(self, itemTypeIdx, nationIdx, itemShopID, default = (0, 0)):
        vehPrices, _ = self.__cache.get('items', {}).get(nationIdx, {}).get(itemTypeIdx, ({}, {}))
        return vehPrices.get(itemShopID, default)

    def __getVehiclePriceFromCache(self, vehCompDescr, default = (0, 0)):
        nationIdx, innationIdx = vehicles.parseVehicleCompactDescr(vehCompDescr)
        price = self.__getPriceFromCache(_VEHICLE, nationIdx, innationIdx, None)
        if price is None:
            return default
        else:
            vehDescr = vehicles.VehicleDescr(compactDescr=vehCompDescr)
            devices = vehDescr.getDevices()
            for defCompDescr, instCompDescr in izip(devices[0], devices[1]):
                if defCompDescr == instCompDescr:
                    continue
                itemTypeIdx, nationIdx, innationIdx = vehicles.parseIntCompactDescr(defCompDescr)
                compPrice = self.__getPriceFromCache(itemTypeIdx, nationIdx, defCompDescr, None)
                if compPrice is None:
                    return default
                price = _subtractPrices(price, compPrice)
                itemTypeIdx, nationIdx, innationIdx = vehicles.parseIntCompactDescr(instCompDescr)
                compPrice = self.__getPriceFromCache(itemTypeIdx, nationIdx, instCompDescr, None)
                if compPrice is None:
                    return default
                price = _summPrices(price, compPrice)

            for optDevCompDescr in devices[2]:
                itemTypeIdx, nationIdx, innationIdx = vehicles.parseIntCompactDescr(optDevCompDescr)
                compPrice = self.__getPriceFromCache(itemTypeIdx, nationIdx, optDevCompDescr, None)
                if compPrice is None:
                    return default
                price = _summPrices(price, compPrice)

            return price

    def __getSellPriceModifiersFromCache(self, itemTypeIdx, nationIdx, inNationIdx):
        cache = self.__cache
        sellPriceModif = cache.get('sellPriceModif', 0)
        _, extData = cache.get('items', {}).get(nationIdx, {}).get(itemTypeIdx, ({}, {}))
        return (self.__getCacheRevision(),
         cache.get('exchangeRate', 0),
         cache.get('exchangeRateForShellsAndEqs', 0),
         sellPriceModif,
         extData.get('sellPriceFactors', {}).get(inNationIdx, sellPriceModif),
         inNationIdx in extData.get('sellForGold', set()))

    def __getValue(self, key, callback):
        if self.__ignore:
            if callback is not None:
                callback(AccountCommands.RES_NON_PLAYER, None, self.__getCacheRevision())
            return
        elif not self.__isSynchronizing:
            self.__onGetValueResponse(AccountCommands.RES_CACHE, key, callback)
            return
        else:
            proxy = lambda resultID, data: self.__onGetValueResponse(resultID, key, callback)
            self.__syncController.request(self.__syncID, proxy)
            return


def _summPrices(price1, price2):
    return (price1[0] + price2[0], price1[1] + price2[1])


def _subtractPrices(price1, price2):
    return (price1[0] - price2[0], price1[1] - price2[1])

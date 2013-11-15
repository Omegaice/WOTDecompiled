# 2013.11.15 11:25:13 EST
# Embedded file name: scripts/client/account_helpers/Stats.py
import AccountCommands
import items
from functools import partial
from AccountSyncData import synchronizeDicts
from items import vehicles
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
_SIMPLE_VALUE_STATS = ('credits', 'gold', 'slots', 'berths', 'freeXP', 'dossier', 'clanInfo', 'accOnline', 'accOffline', 'freeTMenLeft', 'freeVehiclesLeft', 'vehicleSellsLeft', 'captchaTriesLeft', 'hasFinPassword', 'finPswdAttemptsLeft', 'tkillIsSuspected', 'denunciationsLeft', 'tutorialsCompleted', 'battlesTillCaptcha', 'dailyPlayHours', 'playLimits', 'globalRating')
_DICT_STATS = ('vehTypeXP', 'vehTypeLocks', 'restrictions', 'globalVehicleLocks')
_GROWING_SET_STATS = ('unlocks', 'eliteVehicles', 'multipliedXPVehs')
_ACCOUNT_STATS = ('clanDBID', 'attrs', 'premiumExpiryTime', 'autoBanTime')

class Stats(object):

    def __init__(self, syncData):
        self.__account = None
        self.__syncData = syncData
        self.__cache = {}
        self.__ignore = True
        return

    def onAccountBecomePlayer(self):
        self.__ignore = False

    def onAccountBecomeNonPlayer(self):
        self.__ignore = True

    def setAccount(self, account):
        self.__account = account

    def synchronize(self, isFullSync, diff):
        if isFullSync:
            self.__cache.clear()
        cache = self.__cache
        statsDiff = diff.get('stats', None)
        if statsDiff is not None:
            for stat in _SIMPLE_VALUE_STATS:
                if stat in statsDiff:
                    cache[stat] = statsDiff[stat]

            for stat in _DICT_STATS:
                stat_r = (stat, '_r')
                if stat_r in statsDiff:
                    cache[stat] = statsDiff[stat_r]
                if stat in statsDiff:
                    synchronizeDicts(statsDiff[stat], cache.setdefault(stat, dict()))

            for stat in _GROWING_SET_STATS:
                stat_r = (stat, '_r')
                if stat_r in statsDiff:
                    cache[stat] = statsDiff[stat_r]
                if stat in statsDiff:
                    cache.setdefault(stat, set()).update(statsDiff[stat])

        accountDiff = diff.get('account', None)
        if accountDiff is not None:
            for stat in _ACCOUNT_STATS:
                if stat in accountDiff:
                    cache[stat] = accountDiff[stat]

        economicsDiff = diff.get('economics', None)
        if economicsDiff is not None:
            for stat in ('unlocks', 'eliteVehicles'):
                if stat in economicsDiff:
                    cache.setdefault(stat, set()).update(economicsDiff[stat])

        cacheDiff = diff.get('cache', None)
        if cacheDiff is not None:
            for stat in ('isFinPswdVerified', 'mayConsumeWalletResources'):
                if stat in cacheDiff:
                    cache[stat] = cacheDiff[stat]

        return

    def getCache(self, callback = None):
        if self.__ignore:
            if callback is not None:
                callback(AccountCommands.RES_NON_PLAYER, None)
            return
        else:
            self.__syncData.waitForSync(partial(self.__onGetCacheResponse, callback))
            return

    def get(self, statName, callback = None):
        if self.__ignore:
            if callback is not None:
                callback(AccountCommands.RES_NON_PLAYER, None)
            return
        else:
            self.__syncData.waitForSync(partial(self.__onGetResponse, statName, callback))
            return

    def unlock(self, vehTypeCompDescr, unlockIdx, callback = None):
        if self.__ignore:
            if callback is not None:
                callback(AccountCommands.RES_NON_PLAYER)
            return
        else:
            if callback is not None:
                proxy = lambda requestID, resultID, errorStr, ext = {}: callback(resultID)
            else:
                proxy = None
            self.__account._doCmdInt3(AccountCommands.CMD_UNLOCK, vehTypeCompDescr, unlockIdx, 0, proxy)
            return

    def setCurrentVehicle(self, vehInvID, callback = None):
        LOG_WARNING('Deprecated. setCurrentVehicle')

    def exchange(self, gold, callback = None):
        if self.__ignore:
            if callback is not None:
                callback(AccountCommands.RES_NON_PLAYER)
            return
        else:
            self.__account.shop.getExchangeRate(partial(self.__exchange_onGetRate, gold, callback))
            return

    def convertToFreeXP(self, vehTypeCompDescrs, xp, callback = None):
        if self.__ignore:
            if callback is not None:
                callback(AccountCommands.RES_NON_PLAYER)
            return
        else:
            self.__account.shop.getFreeXPConversion(partial(self.__convertToFreeXP_onGetParameters, vehTypeCompDescrs, xp, callback))
            return

    def upgradeToPremium(self, days, callback = None):
        if self.__ignore:
            if callback is not None:
                callback(AccountCommands.RES_NON_PLAYER, 0)
            return
        else:
            self.__account.shop.getPremiumCost(partial(self.__premium_onGetPremCost, days, callback))
            return

    def buySlot(self, callback = None):
        if self.__ignore:
            if callback is not None:
                callback(AccountCommands.RES_NON_PLAYER, 0)
            return
        else:
            self.__account.shop.waitForSync(partial(self.__slot_onShopSynced, callback))
            return

    def buyBerths(self, callback = None):
        if self.__ignore:
            if callback is not None:
                callback(AccountCommands.RES_NON_PLAYER, 0)
            return
        else:
            self.__account.shop.waitForSync(partial(self.__berths_onShopSynced, callback))
            return

    def setMoney(self, credits, gold = 0, freeXP = 0, callback = None):
        if self.__ignore:
            if callback is not None:
                callback(AccountCommands.RES_NON_PLAYER)
            return
        else:
            if callback is not None:
                proxy = lambda requestID, resultID, errorStr, ext = {}: callback(resultID)
            else:
                proxy = None
            self.__account._doCmdInt3(AccountCommands.CMD_SET_MONEY, credits, gold, freeXP, proxy)
            return

    def addExperience(self, vehTypeName, xp, callback = None):
        if self.__ignore:
            if callback is not None:
                callback(AccountCommands.RES_NON_PLAYER)
            return
        else:
            vehTypeCompDescr = vehicles.makeIntCompactDescrByID('vehicle', *vehicles.g_list.getIDsByName(vehTypeName))
            if callback is not None:
                proxy = lambda requestID, resultID, errorStr, ext = {}: callback(resultID)
            else:
                proxy = None
            self.__account._doCmdInt3(AccountCommands.CMD_ADD_XP, vehTypeCompDescr, xp, 0, proxy)
            return

    def unlockAll(self, callback):
        if self.__ignore:
            if callback is not None:
                callback(AccountCommands.RES_NON_PLAYER)
            return
        else:
            if callback is not None:
                proxy = lambda requestID, resultID, errorStr, ext = {}: callback(resultID)
            else:
                proxy = None
            self.__account._doCmdInt3(AccountCommands.CMD_UNLOCK_ALL, 0, 0, 0, proxy)
            return

    def __onGetResponse(self, statName, callback, resultID):
        if resultID < 0:
            if callback is not None:
                callback(resultID, None)
            return
        else:
            if callback is not None:
                callback(resultID, self.__cache.get(statName, None))
            return

    def __onGetCacheResponse(self, callback, resultID):
        if resultID < 0:
            if callback is not None:
                callback(resultID, None)
            return
        else:
            if callback is not None:
                callback(resultID, self.__cache)
            return

    def __exchange_onGetRate(self, gold, callback, resultID, exchRate, shopRev):
        if resultID < 0:
            if callback is not None:
                callback(resultID, None)
            return
        elif exchRate is None:
            LOG_ERROR('Result of the getExchangeRate request is None')
            if callback is not None:
                callback(AccountCommands.RES_FAILURE)
            return
        else:
            if callback is not None:
                proxy = lambda requestID, resultID, errorStr, ext = {}: callback(resultID)
            else:
                proxy = None
            self.__account._doCmdInt3(AccountCommands.CMD_EXCHANGE, shopRev, gold, 0, proxy)
            return

    def __convertToFreeXP_onGetParameters(self, vehTypeCompDescrs, xp, callback, resultID, freeXPConversion, shopRev):
        if resultID < 0:
            if callback is not None:
                callback(resultID, None)
            return
        elif freeXPConversion is None:
            LOG_ERROR('Result of the getFreeXPConversion request is None')
            if callback is not None:
                callback(AccountCommands.RES_FAILURE)
            return
        else:
            arr = [shopRev, xp] + list(vehTypeCompDescrs)
            if callback is not None:
                proxy = lambda requestID, resultID, errorStr, ext = {}: callback(resultID)
            else:
                proxy = None
            self.__account._doCmdIntArr(AccountCommands.CMD_FREE_XP_CONV, arr, proxy)
            return

    def __premium_onGetPremCost(self, days, callback, resultID, premCost, shopRev):
        if resultID < 0:
            if callback is not None:
                callback(resultID, None)
            return
        elif premCost is None:
            LOG_ERROR('Result of the getPremiumCost request is None')
            if callback is not None:
                callback(AccountCommands.RES_FAILURE)
            return
        else:
            gold = premCost.get(days, None)
            if gold is None:
                LOG_ERROR('Wrong days number')
                if callback is not None:
                    callback(AccountCommands.RES_WRONG_ARGS)
                return
            if callback is not None:
                proxy = lambda requestID, resultID, errorStr, ext = {}: callback(resultID)
            else:
                proxy = None
            self.__account._doCmdInt3(AccountCommands.CMD_PREMIUM, shopRev, days, 0, proxy)
            return

    def __slot_onShopSynced(self, callback, resultID, shopRev):
        if resultID < 0:
            if callback is not None:
                callback(resultID)
            return
        else:
            if callback is not None:
                proxy = lambda requestID, resultID, errorStr, ext = {}: callback(resultID)
            else:
                proxy = None
            self.__account._doCmdInt3(AccountCommands.CMD_BUY_SLOT, shopRev, 0, 0, proxy)
            return

    def __berths_onShopSynced(self, callback, resultID, shopRev):
        if resultID < 0:
            if callback is not None:
                callback(resultID)
            return
        else:
            if callback is not None:
                proxy = lambda requestID, resultID, errorStr, ext = {}: callback(resultID)
            else:
                proxy = None
            self.__account._doCmdInt3(AccountCommands.CMD_BUY_BERTHS, shopRev, 0, 0, proxy)
            return
# okay decompyling res/scripts/client/account_helpers/stats.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:25:13 EST

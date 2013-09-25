# Embedded file name: scripts/client/gui/Scaleform/managers/ToolTipManager.py
import pickle
import ResMgr
import BigWorld
import sys
import dossiers
import gui
import constants
from gui.Scaleform.locale.MENU import MENU
from gui.shared.gui_items import GUI_ITEM_TYPE
import nations
from gui.Scaleform.daapi.view.lobby.techtree.custom_items import _convert4ToolTip, _makeShopVehicle
from helpers.i18n import makeString
from adisp import process, async
from PlayerEvents import g_playerEvents
from CurrentVehicle import g_currentVehicle
from gui.Scaleform.daapi.view.lobby.techtree import NODE_STATE
from gui.Scaleform.daapi.view.lobby.techtree.techtree_dp import g_techTreeDP
from gui.shared.utils import ParametersCache, ItemsParameters, dossiers_utils, RELOAD_TIME_PROP_NAME, AIMING_TIME_PROP_NAME, SHELLS_COUNT_PROP_NAME, SHELL_RELOADING_TIME_PROP_NAME, RELOAD_MAGAZINE_TIME_PROP_NAME, GUN_RELOADING_TYPE, CLIP_ICON_PATH, EXTRA_MODULE_INFO, GUN_CAN_BE_CLIP, GUN_CLIP
from gui.shared import g_itemsCache, g_questsCache
from gui.shared.utils.requesters import StatsRequester, Requester, ShopRequester
from gui.shared.utils.gui_items import ShopItem, InventoryVehicle, VehicleItem, _ICONS_MASK, getItemByCompact
from gui.shared.utils.functions import stripShortDescrTags, getShortDescr, isModuleFitVehicle
from gui.shared.utils.dossiers_utils import getAchievementType, getAchievementSection, ACHIEVEMENTS_NEXT_LEVEL_VALUES
from gui.shared.utils.RareAchievementsCache import g_rareAchievesCache
from items import ITEM_TYPE_NAMES, vehicles, artefacts, ITEM_TYPE_INDICES
from items.tankmen import getSkillsConfig, MAX_SKILL_LEVEL, PERKS, SKILLS_BY_ROLES, COMMANDER_ADDITION_RATIO
from gui.ClientUpdateManager import g_clientUpdateManager
from dossiers.achievements import ACHIEVEMENTS
from debug_utils import LOG_ERROR, LOG_DEBUG, LOG_CURRENT_EXCEPTION
from helpers import i18n
from dossiers.achievements import ACHIEVEMENT_TYPE
from gui import game_control

class ToolTipManager(object):
    __CLIP_GUN_MODULE_PARAM = 'vehicleClipGun'
    VEHICLE_PARAMS = {'lightTank': ('speedLimits', 'enginePowerPerTon', 'chassisRotationSpeed', 'circularVisionRadius'),
     'mediumTank': ('speedLimits', 'enginePowerPerTon', 'chassisRotationSpeed', 'damageAvgPerMinute'),
     'heavyTank': ('hullArmor', 'turretArmor', 'damageAvg', 'piercingPower'),
     'SPG': ('damageAvg', 'explosionRadius', 'shotDispersionAngle', 'aimingTime', 'reloadTimeSecs'),
     'AT-SPG': ('speedLimits', 'chassisRotationSpeed', 'damageAvgPerMinute', 'shotDispersionAngle', 'piercingPower'),
     'default': ('speedLimits', 'enginePower', 'chassisRotationSpeed')}
    MODULE_PARAMS = {ITEM_TYPE_NAMES[2]: ('maxLoad', 'rotationSpeed', 'weight'),
     ITEM_TYPE_NAMES[3]: ('armor', 'rotationSpeed', 'circularVisionRadius', 'weight'),
     ITEM_TYPE_NAMES[4]: (RELOAD_TIME_PROP_NAME,
                          'avgPiercingPower',
                          'avgDamage',
                          'dispertionRadius',
                          AIMING_TIME_PROP_NAME,
                          'weight'),
     ITEM_TYPE_NAMES[5]: ('enginePower', 'fireStartingChance', 'weight'),
     ITEM_TYPE_NAMES[7]: ('radioDistance', 'weight'),
     ITEM_TYPE_NAMES[9]: ('weight',),
     __CLIP_GUN_MODULE_PARAM: (SHELLS_COUNT_PROP_NAME,
                               SHELL_RELOADING_TIME_PROP_NAME,
                               RELOAD_MAGAZINE_TIME_PROP_NAME,
                               'avgPiercingPower',
                               'avgDamage',
                               'dispertionRadius',
                               AIMING_TIME_PROP_NAME,
                               'weight')}
    EXTRA_MODULE_PARAMS = {__CLIP_GUN_MODULE_PARAM: (SHELLS_COUNT_PROP_NAME, SHELL_RELOADING_TIME_PROP_NAME, RELOAD_MAGAZINE_TIME_PROP_NAME)}

    class TOOLTIP_TYPE:
        VEHICLE = 'vehicle'
        TANKMAN = 'tankman'
        SKILL = 'skill'
        ACHIEVEMENT = 'achievement'
        ACHIEVEMENT_ATTR = 'achievementAttr'
        MODULE = 'module'
        SHELL = 'shell'
        EFFICIENCY = 'efficiency'
        IGR = 'igr'

    class TOOLTIP_COMPONENT:
        TECH_MAIN = 'technical_maintenance'
        HANGAR = 'hangar'
        SHOP = 'shop'
        INVENTORY = 'inventory'
        PERSONAL_CASE = 'personal_case'
        CAROUSEL = 'carousel'
        RESEARCH = 'research'
        PROFILE = 'profile'
        FINAL_STATISTIC = 'FinalStatistic'

    DEFAUL_DAILY_XP_FACTOR = 2

    def __init__(self):
        super(ToolTipManager, self).__init__()
        self.initialized = False
        self.__eliteVehicles = set()
        self.__unlocks = set()
        self.__unlockPrices = dict()
        self.__xpVehicles = dict()
        self.__priceVehicles = dict()
        self.__inventoryVehicles = dict()
        self.__inventoryVehiclesDescrs = dict()
        self.__vehicleTypeLock = dict()
        self.__multipliedXPVehicles = list()
        self.__dailyXPFactor = self.DEFAUL_DAILY_XP_FACTOR
        self.__dismantlingPrice = 10
        self.__tankmen = dict()
        self.__shop = None
        self.__attrs = 0
        g_clientUpdateManager.addCallbacks({'inventory': self.onInventoryUpdate,
         'stats.unlocks': self.onUnlocksUpdate,
         'stats.vehTypeXP': self.onVehicleXPUpdate,
         'stats.eliteVehicles': self.onEliteVehiclesUpdate,
         'cache.vehsLock': self.onInventoryUpdate})
        g_playerEvents.onShopResync += self.onShopUpdate
        return

    def __del__(self):
        LOG_DEBUG('ToolTipManager deleted')

    def destroy(self):
        g_playerEvents.onShopResync -= self.onShopUpdate
        g_clientUpdateManager.removeObjectCallbacks(self, force=True)
        self.__shop = None
        self.initialized = False
        return

    @async
    @process
    def request(self, callback):
        import time
        startTime = time.time()
        self.initialized = False
        yield self.__getAccountInfo()
        yield self.__getVehiclesInfo()
        self.__readVehiclesData()
        self.__shop = yield ShopRequester().request()
        elapsed = time.time() - startTime
        LOG_DEBUG("ToolTip's cache initialization has been completed. Time elapsed: %.5fs" % elapsed)
        self.initialized = True
        callback(True)

    @async
    @process
    def __getAccountInfo(self, callback):
        self.__dismantlingPrice = yield StatsRequester().getPaidRemovalCost()
        self.__attrs = yield StatsRequester().getAccountAttrs()
        callback(True)

    @async
    @process
    def __getVehiclesInfo(self, callback):
        inventoryVehicles = yield Requester('vehicle').getFromInventory()
        self.__inventoryVehicles = dict([ (v.inventoryId, v) for v in inventoryVehicles ])
        self.__inventoryVehiclesDescrs = dict([ (v.inventoryId, v.compactDescr) for v in inventoryVehicles ])
        vehPrices = yield StatsRequester().getVehiclesPrices(self.__inventoryVehiclesDescrs.values())
        self.__priceVehicles = dict(zip(self.__inventoryVehiclesDescrs.values(), vehPrices))
        self.__xpVehicles = yield StatsRequester().getVehicleTypeExperiences()
        self.__unlocks = yield StatsRequester().getUnlocks()
        self.__eliteVehicles = yield StatsRequester().getEliteVehicles()
        self.__multipliedXPVehicles = yield StatsRequester().getMultipliedXPVehicles()
        self.__vehicleTypeLock = yield StatsRequester().getVehicleTypeLocks()
        self.__globalVehicleLocks = yield StatsRequester().getGlobalVehicleLocks()
        self.__dailyXPFactor = yield StatsRequester().getDailyXPFactor()
        self.__dailyXPFactor = self.__dailyXPFactor or self.DEFAUL_DAILY_XP_FACTOR
        tankmen = yield Requester('tankman').getFromInventory()
        self.__tankmen = dict([ (t.inventoryId, t) for t in tankmen ])
        callback(True)

    def __readVehiclesData(self):
        for nation in nations.AVAILABLE_NAMES:
            for item in vehicles.g_list.getList(nations.INDICES[nation]).itervalues():
                vehicleDescr = vehicles.VehicleDescr(typeName=item['name'])
                for unlockDescr in vehicleDescr.type.unlocksDescrs:
                    prices = self.__unlockPrices.setdefault(unlockDescr[1], dict())
                    prices[vehicleDescr.type.compactDescr] = unlockDescr[0]

    def __getUnlockPrice(self, compactDescr, parentCD = None):
        """
        @return: (isAvailable, unlockPrice, notEnoughXpCount)
        """
        freeXP = g_itemsCache.items.stats.freeXP
        item_type_id, _, _ = vehicles.parseIntCompactDescr(compactDescr)
        pricesDict = self.__getUnlockPrices(compactDescr)

        def getUnlockProps(isAvailable, vehCompDescr):
            unlockPrice = pricesDict.get(vehCompDescr, 0)
            pVehXp = self.__xpVehicles.get(vehCompDescr, 0)
            return (isAvailable, unlockPrice, unlockPrice - pVehXp - freeXP)

        if item_type_id == vehicles._VEHICLE:
            g_techTreeDP.load()
            isAvailable, props = g_techTreeDP.isNext2Unlock(compactDescr, self.__unlocks, self.__xpVehicles, freeXP)
            if parentCD is not None:
                return getUnlockProps(isAvailable, parentCD)
            return getUnlockProps(isAvailable, props.parentID)
        else:
            isAvailable = compactDescr in self.__unlocks
            if not pricesDict:
                return (isAvailable, 0, 0)
            if parentCD is not None:
                return getUnlockProps(isAvailable, parentCD)
            vehsCompDescrs = [ compDescr for compDescr in pricesDict.keys() if compDescr in self.__unlocks ]
            if not vehsCompDescrs:
                vehsCompDescrs = pricesDict.keys()
            minUnlockPrice = sys.maxint
            minUnlockPriceVehCD = None
            for vcd in vehsCompDescrs:
                if pricesDict[vcd] <= minUnlockPrice:
                    minUnlockPrice = pricesDict[vcd]
                    minUnlockPriceVehCD = vcd

            if minUnlockPriceVehCD is None:
                return (isAvailable, 0, 0)
            return getUnlockProps(isAvailable, minUnlockPriceVehCD)
            return

    def __getUnlockPrices(self, compactDescr):
        return self.__unlockPrices.get(compactDescr, dict())

    def onUnlocksUpdate(self, unlocks):
        self.__unlocks |= unlocks

    def onVehicleXPUpdate(self, xps):
        self.__xpVehicles.update(xps)

    def onEliteVehiclesUpdate(self, elites):
        self.__eliteVehicles |= elites

    @process
    def onInventoryUpdate(self, *args):
        yield self.__getVehiclesInfo()

    def __getMoney(self):
        stats = g_itemsCache.items.stats
        return (stats.credits, stats.gold)

    @process
    def onShopUpdate(self, *args):
        self.__shop = yield ShopRequester().request()

    def __getSerializedToolTipData(self, tooltipType, tooltipComponent, data):
        return self.__getToolTipData(tooltipType, tooltipComponent, data)

    def __getToolTipData(self, tooltipType, tooltipComponent, data):
        return {'type': tooltipType,
         'component': tooltipComponent,
         'data': data}

    def __getVehicleStatsBlock(self, vehicle, xp = True, dayliXP = True, unlockPrice = True, buyPrice = True, sellPrice = True, parentCD = None, techTreeNode = None):
        result = list()
        isUnlocked = vehicle.descriptor.type.compactDescr in self.__unlocks
        isInInventory = vehicle.compactDescr in self.__inventoryVehiclesDescrs.values()
        isNextToUnlock = False
        if techTreeNode is not None:
            isNextToUnlock = bool(int(techTreeNode.state) & NODE_STATE.NEXT_2_UNLOCK)
        if xp:
            xpValue = self.__xpVehicles.get(vehicle.descriptor.type.compactDescr, 0)
            if xpValue:
                result.append(['xp', xpValue])
        if dayliXP:
            if self.__attrs & constants.ACCOUNT_ATTR.DAILY_MULTIPLIED_XP and vehicle.descriptor.type.compactDescr not in self.__multipliedXPVehicles:
                result.append(['dailyXPFactor', self.__dailyXPFactor])
        if unlockPrice:
            _, cost, need = self.__getUnlockPrice(vehicle.descriptor.type.compactDescr, parentCD)
            unlockPriceStat = ['unlock_price', cost]
            if isNextToUnlock and not isUnlocked and need > 0:
                unlockPriceStat.append(need)
            if cost > 0:
                result.append(unlockPriceStat)
        if buyPrice:
            price, _ = self.__shop.getItems(ITEM_TYPE_INDICES[vehicle.itemTypeName], *vehicle.descriptor.type.id)
            if price is None:
                price = (0, 0)
            buyPriceStat = ['buy_price', price[1 if vehicle.isPremium else 0]]
            if not isInInventory and (isNextToUnlock or isUnlocked):
                money = self.__getMoney()
                if vehicle.isPremium:
                    need = price[1] - money[1]
                else:
                    need = price[0] - money[0]
                if need > 0:
                    buyPriceStat.append(need)
            result.append(buyPriceStat)
        if sellPrice:
            sellPriceValue = self.__priceVehicles.get(vehicle.compactDescr, 0)
            result.append(['sell_price', sellPriceValue[0] if type(vehicle) != ShopItem else 0])
        return result

    def __getVehicleParameterValue(self, paramName, paramsDict, rawParamsDict):
        if paramName == 'enginePowerPerTon':
            return (paramName, BigWorld.wg_getNiceNumberFormat(rawParamsDict['enginePowerPerTon']))
        if paramName == 'damageAvgPerMinute':
            return (paramName, BigWorld.wg_getIntegralFormat(rawParamsDict[paramName]))
        if paramName == 'damageAvg':
            return (paramName, BigWorld.wg_getNiceNumberFormat(rawParamsDict[paramName]))
        if paramName == 'reloadTimeSecs':
            return (paramName, BigWorld.wg_getIntegralFormat(rawParamsDict[paramName]))
        if paramName in paramsDict:
            return (paramName, paramsDict.get(paramName))
        return (paramName, rawParamsDict.get(paramName))

    def __getVehicleParamsBlock(self, vehicle, params = True, crew = True, eqs = True, devices = True):
        result = list()
        vehicleCommonParams = dict(ItemsParameters.g_instance.getParameters(vehicle.descriptor))
        vehicleRawParams = dict(ParametersCache.g_instance.getParameters(vehicle.descriptor))
        result.append([])
        if params:
            for paramName in self.VEHICLE_PARAMS.get(vehicle.type, 'default'):
                if paramName in vehicleCommonParams or paramName in vehicleRawParams:
                    result[-1].append(self.__getVehicleParameterValue(paramName, vehicleCommonParams, vehicleRawParams))

        result.append([])
        if crew:
            currentCrewSize = 0
            if isinstance(vehicle, InventoryVehicle):
                currentCrewSize = len([ x for x in vehicle.crew if x is not None ])
            result[-1].append({'label': 'crew',
             'current': currentCrewSize,
             'total': len(vehicle.descriptor.type.crewRoles)})
        if eqs:
            result[-1].append({'label': 'equipments',
             'current': len([ x for x in vehicle.equipments if x ]),
             'total': len(vehicle.equipments)})
        if devices:
            result[-1].append({'label': 'devices',
             'current': len([ x for x in vehicle.descriptor.optionalDevices if x ]),
             'total': len(vehicle.descriptor.optionalDevices)})
        return result

    def __getVehicleStatusBlock(self, vehicle, inventoryCount = 0):
        if isinstance(vehicle, ShopItem):
            isUnlocked = vehicle.descriptor.type.compactDescr in self.__unlocks
            isInInventory = vehicle.descriptor.type.compactDescr in [ v.descriptor.type.compactDescr for v in self.__inventoryVehicles.values() ]
            money = self.__getMoney()
            msg = None
            level = InventoryVehicle.STATE_LEVEL.WARNING
            if not isUnlocked:
                msg = 'notUnlocked'
            elif isInInventory:
                msg = 'inHangar'
            elif money[0] < vehicle.priceOrder[0]:
                msg = 'notEnoughCredits'
                level = InventoryVehicle.STATE_LEVEL.CRITICAL
            elif money[1] < vehicle.priceOrder[1]:
                msg = 'notEnoughGold'
                level = InventoryVehicle.STATE_LEVEL.CRITICAL
            if msg is not None:
                header, text = self.__getComplexStatus('#tooltips:vehicleStatus/%s' % msg)
                return {'header': header,
                 'text': text,
                 'level': level}
            return
        else:
            header, text = self.__getComplexStatus('#tooltips:vehicleStatus/%s' % vehicle.getState())
            if header is None and text is None:
                return
            return {'header': header,
             'text': text,
             'level': vehicle.getStateLevel()}

    def __getResearchPageVehicleStatusBlock(self, vehicle, node):
        tooltip = None
        level = InventoryVehicle.STATE_LEVEL.WARNING
        nodeState = int(node.state)
        if not nodeState & NODE_STATE.UNLOCKED:
            if not nodeState & NODE_STATE.NEXT_2_UNLOCK:
                tooltip = '#tooltips:researchPage/vehicle/status/parentModuleIsLocked'
            elif not nodeState & NODE_STATE.ENOUGH_XP:
                tooltip = '#tooltips:researchPage/module/status/notEnoughXP'
                level = InventoryVehicle.STATE_LEVEL.CRITICAL
        else:
            if nodeState & NODE_STATE.IN_INVENTORY:
                vehicle = self.__inventoryVehicles[vehicle.inventoryId]
                return self.__getVehicleStatusBlock(vehicle)
            accMoney = self.__getMoney()
            itemPrice = (0, 0)
            item = g_itemsCache.items.getItemByCD(vehicle.descriptor.type.compactDescr)
            if item is not None:
                itemPrice = item.buyPrice
            if accMoney[0] >= itemPrice[0]:
                isMoneyEnough = accMoney[1] >= itemPrice[1]
                if not isMoneyEnough:
                    level = InventoryVehicle.STATE_LEVEL.CRITICAL
                    tooltip = nodeState & NODE_STATE.PREMIUM and '#tooltips:moduleFits/gold_error'
                else:
                    tooltip = '#tooltips:moduleFits/credit_error'
        if tooltip is not None:
            header, text = self.__getComplexStatus(tooltip)
            return {'header': header,
             'text': text,
             'level': level}
        else:
            return

    def __getVehicleLocksBlock(self, vehicle):
        clanDamageLock = self.__vehicleTypeLock.get(vehicle.descriptor.type.compactDescr, {}).get(1, None)
        clanNewbeLock = self.__globalVehicleLocks.get(1, None)
        return {'CLAN': clanDamageLock or clanNewbeLock}

    def getCarouselVehicleData(self, vehicleID):
        vehicle = self.__inventoryVehicles.get(vehicleID)
        if not vehicle:
            return None
        else:
            vd = vehicle.descriptor
            vcd = vd.type.compactDescr
            return self.__getSerializedToolTipData(self.TOOLTIP_TYPE.VEHICLE, self.TOOLTIP_COMPONENT.CAROUSEL, {'name': vehicle.name,
             'type': vehicle.type,
             'isElite': len(vd.type.unlocksDescrs) == 0 or vcd in self.__eliteVehicles,
             'isPremium': vehicle.isPremium,
             'isFavorite': vehicle.isFavorite,
             'level': vehicle.level,
             'status': self.__getVehicleStatusBlock(vehicle),
             'stats': self.__getVehicleStatsBlock(vehicle, unlockPrice=False, buyPrice=False, sellPrice=True),
             'params': self.__getVehicleParamsBlock(vehicle, params=gui.GUI_SETTINGS.technicalInfo),
             'locks': self.__getVehicleLocksBlock(vehicle)})

    def getTechTreeVehicleData(self, node, parentCD):
        parentCD = int(parentCD)
        try:
            vehicle = _convert4ToolTip(node.pickleDump, (node.shopPrice.credits, node.shopPrice.gold))
            if parentCD is not None:
                children = g_techTreeDP.getNextLevel(parentCD)
                itemCD = vehicle.descriptor.type.compactDescr
                if itemCD == parentCD or itemCD not in children:
                    parentCD = None
        except AttributeError:
            LOG_ERROR('Data for vehicle in techtree is invalid')
            return

        vd = vehicle.descriptor
        vcd = vd.type.compactDescr
        vehicleXP = self.__xpVehicles.get(vcd, 0)
        return self.__getSerializedToolTipData(self.TOOLTIP_TYPE.VEHICLE, self.TOOLTIP_COMPONENT.SHOP, {'name': vehicle.name,
         'type': vehicle.type,
         'isElite': len(vehicle.descriptor.type.unlocksDescrs) == 0 or vcd in self.__eliteVehicles,
         'status': self.__getResearchPageVehicleStatusBlock(vehicle, node=node),
         'isPremium': vehicle.isPremium,
         'level': vehicle.level,
         'stats': self.__getVehicleStatsBlock(vehicle, xp=vehicleXP > 0, dayliXP=False, unlockPrice=True, sellPrice=False, parentCD=parentCD, techTreeNode=node),
         'params': self.__getVehicleParamsBlock(vehicle, eqs=False, devices=False, params=gui.GUI_SETTINGS.technicalInfo),
         'locks': self.__getVehicleLocksBlock(vehicle)})

    def getInventoryVehicleData(self, compact):
        vehicle = getItemByCompact(compact)
        if not isinstance(vehicle, InventoryVehicle):
            return
        else:
            vehicle = self.__inventoryVehicles.get(vehicle.inventoryId)
            if vehicle is None:
                return
            vd = vehicle.descriptor
            vcd = vd.type.compactDescr
            return self.__getSerializedToolTipData(self.TOOLTIP_TYPE.VEHICLE, self.TOOLTIP_COMPONENT.INVENTORY, {'name': vehicle.name,
             'type': vehicle.type,
             'isElite': len(vd.type.unlocksDescrs) == 0 or vcd in self.__eliteVehicles,
             'isPremium': vehicle.isPremium,
             'isFavorite': vehicle.isFavorite,
             'level': vehicle.level,
             'status': self.__getVehicleStatusBlock(vehicle),
             'stats': self.__getVehicleStatsBlock(vehicle, unlockPrice=False, buyPrice=False),
             'params': self.__getVehicleParamsBlock(vehicle, params=gui.GUI_SETTINGS.technicalInfo),
             'locks': self.__getVehicleLocksBlock(vehicle)})

    def getShopVehicleData(self, compact):
        vehicle = getItemByCompact(compact)
        if not vehicle:
            return None
        else:
            vd = vehicle.descriptor
            vcd = vd.type.compactDescr
            isUnlocked = vcd in self.__unlocks
            return self.__getSerializedToolTipData(self.TOOLTIP_TYPE.VEHICLE, self.TOOLTIP_COMPONENT.SHOP, {'name': vehicle.name,
             'type': vehicle.type,
             'isElite': len(vehicle.descriptor.type.unlocksDescrs) == 0 or vehicle.descriptor.type.compactDescr in self.__eliteVehicles,
             'status': self.__getVehicleStatusBlock(vehicle),
             'isPremium': vehicle.isPremium,
             'level': vehicle.level,
             'stats': self.__getVehicleStatsBlock(vehicle, xp=False, dayliXP=False, unlockPrice=not isUnlocked, sellPrice=False),
             'params': self.__getVehicleParamsBlock(vehicle, eqs=False, devices=False, params=gui.GUI_SETTINGS.technicalInfo)})

    def isVehicleElite(self, vehicle):
        return len(vehicle.descriptor.type.unlocksDescrs) == 0 or vehicle.descriptor.type.compactDescr in self.__eliteVehicles

    def getTankmanNewSkillData(self, tankmanID):
        return self.getTankmanSkillData('new_skill', tankmanID)

    def getTankmanSkillData(self, skillID, tankmanID):
        tankman = self.__tankmen.get(tankmanID)
        if skillID == 'new_skill':
            skillsCount, lastSkillLevel = (0, 0)
            if tankman is not None:
                skillsCount, lastSkillLevel = tankman.newSkillCount
            return self.__getToolTipData(self.TOOLTIP_TYPE.SKILL, self.TOOLTIP_COMPONENT.PERSONAL_CASE, {'name': makeString('#tooltips:personal_case/skills/new/header'),
             'shortDescr': makeString('#tooltips:personal_case/skills/new/body'),
             'descr': makeString('#tooltips:personal_case/skills/new/body'),
             'count': skillsCount,
             'level': lastSkillLevel})
        else:
            skill_level = -1
            if tankman is not None:
                if skillID in tankman.skills:
                    skill_level = tankman.lastSkillLevel if tankman.skills.index(skillID) == len(tankman.skills) - 1 else MAX_SKILL_LEVEL
            skill_type = 'skill'
            if skillID in PERKS:
                if skillID == 'brotherhood':
                    skill_type = 'perk_common'
                else:
                    skill_type = 'perk'
            return self.__getToolTipData(self.TOOLTIP_TYPE.SKILL, self.TOOLTIP_COMPONENT.PERSONAL_CASE, {'name': getSkillsConfig()[skillID]['userString'],
             'shortDescr': getShortDescr(getSkillsConfig()[skillID]['description']),
             'descr': stripShortDescrTags(getSkillsConfig()[skillID]['description']),
             'level': skill_level,
             'type': skill_type})

    def __getAchievementParams(self, dossier, name, isVehicleList = True):
        type = getAchievementType(name)
        result = [[]]
        if dossier is None:
            return result
        else:
            pair = ACHIEVEMENTS_NEXT_LEVEL_VALUES.get(name, {})
            recordName = pair.get('name')
            recordFunc = pair.get('func')
            if recordName and recordFunc:
                recordValue = recordFunc(dossier)
                if recordValue and recordValue > 0:
                    result[-1].append([recordName, recordValue])
            if type == 'series':
                recordName = ACHIEVEMENTS[name]['record']
                result[-1].append([recordName, dossier[recordName]])
            handler = dossiers_utils.ACTIVITY_HANDLERS.get(name, lambda *args: (True, None, 0))
            _, vehiclesList, fullVehListLen = handler(name, dossier, self.__unlocks)
            listTitle = 'vehicles'
            if name in dossiers_utils.TANK_EXPERT_GROUP:
                listTitle = 'vehiclesToKill'
            elif name in dossiers_utils.MECH_ENGINEER_GROUP:
                listTitle = 'vehiclesToResearch'
            if vehiclesList is not None and (isVehicleList or name not in dossiers_utils.MECH_ENGINEER_GROUP):
                result[-1].append([listTitle, vehiclesList, fullVehListLen])
            return result

    def __getAchievementStats(self, name):
        result = dict()
        type = getAchievementType(name)
        if type == 'class':
            result['classParams'] = dossiers.RECORD_CONFIGS.get(name)
        return result

    def __getDossier(self, dossierType, dossierCompDescr):
        if dossierCompDescr is None:
            return
        elif dossierType == GUI_ITEM_TYPE.ACCOUNT_DOSSIER:
            return dossiers.getAccountDossierDescr(pickle.loads(dossierCompDescr))
        elif dossierType == GUI_ITEM_TYPE.VEHICLE_DOSSIER:
            return dossiers.getVehicleDossierDescr(pickle.loads(dossierCompDescr))
        elif dossierType == GUI_ITEM_TYPE.TANKMAN_DOSSIER:
            return dossiers.getTankmanDossierDescr(pickle.loads(dossierCompDescr))
        else:
            return

    def __getAchievementsUserName(self, name, rank):
        type = getAchievementType(name)
        userName = makeString('#achievements:%s' % name)
        if type == 'class':
            if name == 'markOfMastery':
                userName %= {'name': makeString('#achievements:achievement/master%d' % rank)}
            else:
                rank = str(rank) if rank != 0 else ''
                userName %= makeString('#achievements:achievement/rank%s' % rank)
        return userName

    def getGlobalRatingData(self):
        key = 'globalRating'
        return self.__getSerializedToolTipData(self.TOOLTIP_TYPE.ACHIEVEMENT, self.TOOLTIP_COMPONENT.PROFILE, {'name': makeString('#achievements:%s' % key),
         'descr': dossiers_utils.getMedalDescription(key)})

    def getAchievmentData(self, doosierType, dossierCompDescr, achieveName, isRare, isVehicleList):
        if isRare:
            return self.getProfileRareAchievementData(doosierType, dossierCompDescr, achieveName)
        else:
            return self.getProfileAchievementData(doosierType, dossierCompDescr, achieveName, isVehicleList)

    def getBattleResultsAchievementData(self, name, rank = 0):
        type = getAchievementType(name)
        iconFileName = name
        if type == 'class':
            iconFileName = '%s%d' % (iconFileName, rank)
        return self.__getSerializedToolTipData(self.TOOLTIP_TYPE.ACHIEVEMENT, self.TOOLTIP_COMPONENT.PROFILE, {'name': self.__getAchievementsUserName(name, rank),
         'icon': '../maps/icons/achievement/%s.png' % iconFileName,
         'type': type,
         'section': getAchievementSection(name),
         'descr': dossiers_utils.getMedalDescription(name),
         'value': rank,
         'heroInfo': dossiers_utils.getMedalHeroInfo(name),
         'inactive': False,
         'params': [[]],
         'stats': self.__getAchievementStats(name)})

    def getProfileAchievementData(self, dossierType, dossierCompDescr, name, isVehicleList = True):
        dossier = self.__getDossier(dossierType, dossierCompDescr)
        type = getAchievementType(name)
        achieveRank = 0
        try:
            achieveRank = dossier[name]
        except Exception:
            pass

        userName = self.__getAchievementsUserName(name, achieveRank)
        isInactive = True
        if dossier is not None:
            handler = dossiers_utils.ACTIVITY_HANDLERS.get(name, lambda *args: (True, None, 0))
            isActive, _, _ = handler(name, dossier, self.__unlocks)
            isInactive = not isActive
        iconFileName = name
        if dossier is not None and type == 'class':
            iconFileName = '%s%d' % (iconFileName, dossier[name])
        return self.__getSerializedToolTipData(self.TOOLTIP_TYPE.ACHIEVEMENT, self.TOOLTIP_COMPONENT.PROFILE, {'name': userName,
         'icon': '../maps/icons/achievement/%s.png' % iconFileName,
         'type': type,
         'section': getAchievementSection(name),
         'descr': dossiers_utils.getMedalDescription(name),
         'value': dossiers_utils.getMedalValue(name, dossier),
         'heroInfo': dossiers_utils.getMedalHeroInfo(name),
         'inactive': isInactive,
         'params': self.__getAchievementParams(dossier, name, isVehicleList),
         'stats': self.__getAchievementStats(name)})

    def getProfileRareAchievementData(self, dossierType, dossierCompDescr, achieveName):
        rareID = 0
        if achieveName.startswith('rare'):
            rareID = int(achieveName.replace('rare', ''))
        return self.__getSerializedToolTipData(self.TOOLTIP_TYPE.ACHIEVEMENT, self.TOOLTIP_COMPONENT.PROFILE, {'name': g_rareAchievesCache.getTitle(int(rareID)),
         'icon': None,
         'type': str(rareID),
         'section': 'action',
         'descr': g_rareAchievesCache.getDescription(int(rareID)),
         'value': None,
         'heroInfo': '',
         'inactive': False,
         'params': None,
         'stats': None})

    def __getGuiItemDossier(self, dossierType, dossierID):
        if dossierType == GUI_ITEM_TYPE.ACCOUNT_DOSSIER:
            return g_itemsCache.items.getAccountDossier(dossierID)
        elif dossierType == GUI_ITEM_TYPE.VEHICLE_DOSSIER:
            return g_itemsCache.items.getVehicleDossier(*dossierID)
        elif dossierType == GUI_ITEM_TYPE.TANKMAN_DOSSIER:
            return g_itemsCache.items.getTankmanDossier(dossierID)
        else:
            return None

    def getAchieveAttrData(self, guiItemID):
        achieveName, dossierID = guiItemID
        dossier = self.__getGuiItemDossier(*dossierID)
        if dossier is None:
            return
        else:
            achieve = dossier.getAchievement(achieveName)
            rareID = None
            if achieveName.startswith('rare'):
                achieveName, rareID = 'rareAchievements', int(achieveName.replace('rare', ''))
                achieve = achieve.get(rareID)
            title = None
            descr = None
            if achieve.getType() == ACHIEVEMENT_TYPE.CLASS:
                title = 'Current step: %d' % achieve.value
                descr = 'Need to do: %d' % achieve.lvlUpValue
            elif achieve.getType() == ACHIEVEMENT_TYPE.SERIES:
                title
            return self.__getSerializedToolTipData(self.TOOLTIP_TYPE.ACHIEVEMENT_ATTR, self.TOOLTIP_COMPONENT.PROFILE, {'name': title,
             'icon': None,
             'type': achieve.name,
             'section': achieve.getSection(),
             'descr': descr,
             'value': None,
             'heroInfo': '',
             'inactive': False,
             'params': None,
             'stats': None})

    def __getModuleParams(self, module, vehicle = None, params = True):
        result = list()
        vDescr = vehicle.descriptor if vehicle is not None else None
        moduleParams = dict(ItemsParameters.g_instance.getParameters(module.descriptor, vDescr))
        isClipGun = False
        paramsKeyName = module.type
        extraParamsKeyName = None
        extraResult = None
        if params:
            if paramsKeyName == ITEM_TYPE_NAMES[4]:
                if moduleParams.get(GUN_RELOADING_TYPE) == GUN_CAN_BE_CLIP:
                    extraParamsKeyName = self.__CLIP_GUN_MODULE_PARAM
                if moduleParams.get(GUN_RELOADING_TYPE) == GUN_CLIP:
                    isClipGun = True
                    paramsKeyName = self.__CLIP_GUN_MODULE_PARAM
            p = self.MODULE_PARAMS.get(paramsKeyName)
            if p is not None:
                result.append([])
                for paramName in p:
                    if paramName in moduleParams:
                        result[-1].append([paramName, moduleParams.get(paramName)])

            extra = self.EXTRA_MODULE_PARAMS.get(extraParamsKeyName)
            if extra is not None:
                extraResult = []
                for paramName in extra:
                    if paramName in moduleParams:
                        extraResult.append([paramName, moduleParams.get(paramName)])

        return (result, isClipGun, extraResult)

    def __getModuleStats(self, module, vehicle = None, sellPrice = None, buyPrice = True, unlockPrice = True, inventoryCount = 0, vehicleCount = 0, researchNode = None):

        def checkState(state):
            if researchNode is not None:
                return bool(int(researchNode.state) & state)
            else:
                return False

        result = list()
        isEqOrDev = module.type in (ITEM_TYPE_NAMES[9], ITEM_TYPE_NAMES[11])
        isNextToUnlock = checkState(NODE_STATE.NEXT_2_UNLOCK)
        isInstalled = checkState(NODE_STATE.INSTALLED)
        isInInventory = checkState(NODE_STATE.IN_INVENTORY)
        isUnlocked = checkState(NODE_STATE.UNLOCKED)
        isAutoUnlock = checkState(NODE_STATE.AUTO_UNLOCKED)
        isEnoughXP = checkState(NODE_STATE.ENOUGH_XP)
        accMoney = self.__getMoney()
        itemPrice = (0, 0)
        item = g_itemsCache.items.getItemByCD(module.compactDescr)
        if item is not None:
            itemPrice = item.buyPrice
        if accMoney[0] >= itemPrice[0]:
            isMoneyEnough = accMoney[1] >= itemPrice[1]
            if unlockPrice and vehicle and not isEqOrDev:
                _, cost, need = self.__getUnlockPrice(module.compactDescr, vehicle.descriptor.type.compactDescr)
                unlockPriceStat = ['unlock_price', cost]
                if not isUnlocked and isNextToUnlock and not isEnoughXP and need > 0:
                    unlockPriceStat.append(need)
                if cost > 0:
                    result.append(unlockPriceStat)
            isShowBuyPrice = buyPrice
            if researchNode is not None:
                isShowBuyPrice = not isAutoUnlock
            if isShowBuyPrice:
                price, _ = self.__shop.getItems(ITEM_TYPE_INDICES[module.itemTypeName], module.nation, module.compactDescr)
                forGold = price[0] == 0
                rootInInv = False
                if vehicle is not None:
                    rootInInv = vehicle.strCD in self.__inventoryVehiclesDescrs.values()
                buyPriceStat = ['buy_price', price[1] if forGold else price[0]]
                if researchNode:
                    if rootInInv and not isMoneyEnough and (isNextToUnlock or isUnlocked):
                        if not isInstalled:
                            showNeeded = not isInInventory
                        else:
                            isModuleUnlocked = module.compactDescr in self.__unlocks
                            isModuleInInventory = g_itemsCache.items.getItemByCD(module.compactDescr) is not None
                            showNeeded = not isModuleInInventory and isModuleUnlocked
                        if isEqOrDev or showNeeded:
                            if forGold:
                                need = price[1] - self.__getMoney()[1]
                            else:
                                need = price[0] - self.__getMoney()[0]
                            if need > 0:
                                buyPriceStat.append(need)
                        result.append(buyPriceStat)
                        if isEqOrDev and self.__shop.isEnabledBuyingGoldEqsForCredits and module.priceOrder[1] > 0:
                            result.append(['textDelimiter/or', ''])
                            price = self.__shop.exchangeRateForShellsAndEqs * module.priceOrder[1]
                            buyPriceActionStat = ['buy_price_action', price]
                            need = price - self.__getMoney()[0]
                            if need > 0:
                                buyPriceActionStat.append(need)
                            result.append(buyPriceActionStat)
                    sellPrice is not None and result.append(['sell_price', sellPrice])
                inventoryCount and result.append(['inventoryCount', inventoryCount])
            vehicleCount and result.append(['vehicleCount', vehicleCount])
        return result

    def __isModuleInstalledOnVehicle(self, module, vehicle):
        if module.itemTypeName == ITEM_TYPE_NAMES[9]:
            devices = [ dev.intCD for dev in g_itemsCache.items.getItemByCD(vehicle.descriptor.type.compactDescr).optDevices if dev is not None ]
            return module.compactDescr in devices
        elif module.itemTypeName == ITEM_TYPE_NAMES[2]:
            return module.compactDescr == vehicle.descriptor.chassis['compactDescr']
        elif module.itemTypeName == ITEM_TYPE_NAMES[3]:
            return module.compactDescr == vehicle.descriptor.turret['compactDescr']
        elif module.itemTypeName == ITEM_TYPE_NAMES[4]:
            return module.compactDescr == vehicle.descriptor.gun['compactDescr']
        elif module.itemTypeName == ITEM_TYPE_NAMES[5]:
            return module.compactDescr == vehicle.descriptor.engine['compactDescr']
        elif module.itemTypeName == ITEM_TYPE_NAMES[6]:
            return module.compactDescr == vehicle.descriptor.fuelTank['compactDescr']
        elif module.itemTypeName == ITEM_TYPE_NAMES[7]:
            return module.compactDescr == vehicle.descriptor.radio['compactDescr']
        else:
            return False

    def __getModuleVehiclesList(self, module):
        result = list()
        for vid, v in self.__inventoryVehicles.iteritems():
            if self.__isModuleInstalledOnVehicle(module, v):
                result.append(v.shortName)

        return result

    def __getResearchPageModuleStatus(self, module, vehicle, node):

        def status(header = None, text = None, level = InventoryVehicle.STATE_LEVEL.WARNING):
            if header is not None or text is not None:
                return {'header': header,
                 'text': text,
                 'level': level}
            else:
                return
                return

        header, text = (None, None)
        level = InventoryVehicle.STATE_LEVEL.WARNING
        nodeState = int(node.state)
        if not nodeState & NODE_STATE.UNLOCKED:
            if vehicle.descriptor.type.compactDescr not in self.__unlocks:
                header, text = self.__getComplexStatus('#tooltips:researchPage/module/status/rootVehicleIsLocked')
            elif not nodeState & NODE_STATE.NEXT_2_UNLOCK:
                header, text = self.__getComplexStatus('#tooltips:researchPage/module/status/parentModuleIsLocked')
            elif not nodeState & NODE_STATE.ENOUGH_XP:
                header, text = self.__getComplexStatus('#tooltips:researchPage/module/status/notEnoughXP')
                level = InventoryVehicle.STATE_LEVEL.CRITICAL
            return status(header, text, level)
        elif vehicle.compactDescr not in self.__inventoryVehiclesDescrs.values():
            header, text = self.__getComplexStatus('#tooltips:researchPage/module/status/needToBuyTank')
            text %= {'vehiclename': vehicle.name}
            return status(header, text, InventoryVehicle.STATE_LEVEL.WARNING)
        elif nodeState & NODE_STATE.INSTALLED:
            return status()
        if vehicle is not None:
            if vehicle.compactDescr in self.__inventoryVehiclesDescrs.values():
                vehicle = self.__inventoryVehicles[vehicle.inventoryId]
                vState = vehicle.getState()
                if vState == 'battle':
                    header, text = self.__getComplexStatus('#tooltips:researchPage/module/status/vehicleIsInBattle')
                elif vState == 'locked':
                    header, text = self.__getComplexStatus('#tooltips:researchPage/module/status/vehicleIsReadyToFight')
                elif vState == 'damaged' or vState == 'exploded' or vState == 'destroyed':
                    header, text = self.__getComplexStatus('#tooltips:researchPage/module/status/vehicleIsBroken')
            if header is not None or text is not None:
                return status(header, text, level)
        if nodeState & NODE_STATE.IN_INVENTORY:
            return status(header, text, level)
        accMoney = self.__getMoney()
        itemPrice = (0, 0)
        item = g_itemsCache.items.getItemByCD(module.compactDescr)
        if item is not None:
            itemPrice = item.buyPrice
        if accMoney[0] >= itemPrice[0]:
            isMoneyEnough = accMoney[1] >= itemPrice[1]
            header, text = not nodeState & NODE_STATE.AUTO_UNLOCKED and not isMoneyEnough and self.__getComplexStatus('#tooltips:moduleFits/credit_error')
            return status(header, text, InventoryVehicle.STATE_LEVEL.CRITICAL)
        else:
            return status()

    def __getComplexStatus(self, statusKey):
        try:
            if not statusKey:
                return (None, None)
            headerKey = statusKey + '/header'
            textKey = statusKey + '/text'
            header = makeString(headerKey)
            text = makeString(textKey)
            if header == headerKey.split(':', 1)[1]:
                header = None
            if text == textKey.split(':', 1)[1]:
                text = None
            return (header, text)
        except Exception:
            LOG_CURRENT_EXCEPTION()
            return (None, None)

        return

    def __getModuleStatus(self, module, vehicle = None, slotIdx = 0, eqsUnlocks = None):
        isEqOrDev = module.type in (ITEM_TYPE_NAMES[9], ITEM_TYPE_NAMES[11])
        newStyleVehicle = None
        if vehicle is not None:
            newStyleVehicle = g_itemsCache.items.getItemByCD(vehicle.descriptor.type.compactDescr)
        currentEqs = eqsUnlocks
        if currentEqs is None and isinstance(vehicle, InventoryVehicle):
            if not eqsUnlocks:
                currentEqs = [ VehicleItem(descriptor=vehicles.getDictDescr(item)) for item in vehicle.equipments if item ]
            isFit, reason, tooltip = isModuleFitVehicle(module, newStyleVehicle, module.priceOrder, self.__getMoney(), self.__unlocks if not isEqOrDev else currentEqs, slotIdx)
            installedVehicles = self.__getModuleVehiclesList(module)
            tooltipHeader, tooltipText = self.__getComplexStatus(tooltip)
            messageLvl = InventoryVehicle.STATE_LEVEL.WARNING
            tooltipText = reason == '#menu:moduleFits/already_installed' and ', '.join(installedVehicles)
        elif reason == '#menu:moduleFits/credit_error' or reason == '#menu:moduleFits/gold_error':
            messageLvl = InventoryVehicle.STATE_LEVEL.CRITICAL
        elif reason == '#menu:moduleFits/not_with_installed_equipment':
            if module.compactDescr in [ eq.compactDescr for eq in currentEqs ]:
                isFit = True
                reason = ''
                tooltipHeader = ''
                tooltipText = ''
            else:
                conflictEqs = list()
                vEqsDescrs = [ eq.compactDescr for eq in currentEqs ]
                for _, e in vehicles.g_cache.equipments().iteritems():
                    if e['compactDescr'] in vEqsDescrs:
                        compatibility = e.checkCompatibilityWithActiveEquipment(module.descriptor)
                        if compatibility:
                            compatibility = module.descriptor.checkCompatibilityWithEquipment(e)
                        if not compatibility:
                            conflictEqs.append(e)

                tooltipText %= {'eqs': ', '.join([ makeString(e.userString) for e in conflictEqs ])}
        if not isFit:
            return {'level': messageLvl,
             'header': tooltipHeader,
             'text': tooltipText}
        elif len(installedVehicles):
            tooltipHeader, _ = self.__getComplexStatus('#tooltips:deviceFits/already_installed' if module.itemTypeName == ITEM_TYPE_NAMES[9] else '#tooltips:moduleFits/already_installed')
            return {'level': InventoryVehicle.STATE_LEVEL.WARNING,
             'header': tooltipHeader,
             'text': ', '.join(installedVehicles)}
        else:
            return

    def __getModuleNote(self, module):
        if module.type in (ITEM_TYPE_NAMES[9], ITEM_TYPE_NAMES[11]):
            if not module.isRemovable:
                return {'title': gui.makeHtmlString('html_templates:lobby/tooltips', 'permanent_module_title'),
                 'text': gui.makeHtmlString('html_templates:lobby/tooltips', 'permanent_module_note', {'gold': self.__dismantlingPrice})}
        return None

    def __getModuleEffect(self, module):
        if module.type in (ITEM_TYPE_NAMES[9], ITEM_TYPE_NAMES[11]):

            def checkLocalization(key):
                localization = makeString('#artefacts:%s' % key)
                return (key != localization, localization)

            onUse = checkLocalization('%s/onUse' % module.descriptor['name'])
            always = checkLocalization('%s/always' % module.descriptor['name'])
            return {'onUse': onUse[1] if onUse[0] else '',
             'always': always[1] if always[0] else ''}
        else:
            return None

    def __isModuleTooHeavy(self, module, vehicle = None, slotIdx = 0):
        newStyleVehicle = None
        if vehicle is not None:
            newStyleVehicle = g_itemsCache.items.getItemByCD(vehicle.descriptor.type.compactDescr)
        isEqOrDev = module.type in (ITEM_TYPE_NAMES[9], ITEM_TYPE_NAMES[11])
        isFit, reason, _ = isModuleFitVehicle(module, newStyleVehicle, module.priceOrder, (sys.maxint, sys.maxint), self.__unlocks if not isEqOrDev else [], slotIdx)
        return reason == '#menu:moduleFits/too_heavy'

    def getTechTreeModuleData(self, node, parentCD):
        parentCD = int(parentCD)

        def checkState(state):
            if node is not None:
                return bool(int(node.state) & state)
            else:
                return False

        try:
            module = _convert4ToolTip(node.pickleDump, (node.shopPrice.credits, node.shopPrice.gold))
        except AttributeError:
            LOG_ERROR('Data for vehicle in techtree is invalid')
            return

        descr = None
        if module.itemTypeName in ('optionalDevice', 'equipment'):
            descr = stripShortDescrTags(module.description)
        isAutoUnlock = checkState(NODE_STATE.AUTO_UNLOCKED)
        isTooHeavy = False
        mapping = dict([ (v.descriptor.type.compactDescr, v) for v in self.__inventoryVehicles.itervalues() ])
        if parentCD in mapping:
            vehicle = mapping[parentCD]
            isTooHeavy = self.__isModuleTooHeavy(module, vehicle)
        else:
            _, nationID, itemID = vehicles.parseIntCompactDescr(parentCD)
            vehicle = _makeShopVehicle(itemID, nationID, (0, 0))
        newStyleVehicle = g_itemsCache.items.getItemByCD(parentCD)
        params, isClipGun, _ = self.__getModuleParams(module, vehicle, params=gui.GUI_SETTINGS.technicalInfo)
        moduleParams = {'name': module.name,
         'type': module.type,
         'removeable': module.isRemovable,
         'gold': module.priceOrder[1] != 0,
         'stats': self.__getModuleStats(module, newStyleVehicle, unlockPrice=not isAutoUnlock, researchNode=node),
         'params': params,
         'descr': descr,
         'level': module.level,
         'status': self.__getResearchPageModuleStatus(module, vehicle, node),
         'tooHeavy': isTooHeavy,
         'note': self.__getModuleNote(module),
         'effect': self.__getModuleEffect(module)}
        if isClipGun:
            self.__extendModuleClipGunParam(moduleParams)
        return self.__getSerializedToolTipData(self.TOOLTIP_TYPE.MODULE, self.TOOLTIP_COMPONENT.SHOP, moduleParams)

    def getShopModuleData(self, compact, inventoryCount = 0, vehicleCount = 0):
        module = getItemByCompact(compact)
        if not module:
            return
        else:
            descr = None
            if module.itemTypeName in ('optionalDevice', 'equipment'):
                descr = stripShortDescrTags(module.description)
            isUnlocked = module.compactDescr in self.__unlocks
            params, isClipGun, extraParams = self.__getModuleParams(module, params=gui.GUI_SETTINGS.technicalInfo)
            moduleParams = {'name': module.name,
             'type': module.type,
             'removeable': module.isRemovable,
             'gold': module.priceOrder[1] != 0,
             'stats': self.__getModuleStats(module, unlockPrice=not isUnlocked, inventoryCount=inventoryCount, vehicleCount=vehicleCount),
             'params': params,
             'descr': descr,
             'level': module.level,
             'status': self.__getModuleStatus(module),
             'tooHeavy': self.__isModuleTooHeavy(module),
             'note': self.__getModuleNote(module),
             'effect': self.__getModuleEffect(module)}
            if isClipGun:
                self.__extendModuleClipGunParam(moduleParams)
            if extraParams is not None:
                imgPathArr = CLIP_ICON_PATH.split('..')
                imgPath = 'img://gui' + imgPathArr[1]
                self.__extendModuleExtraParam(i18n.makeString(MENU.MODULEINFO_PARAMETERSCLIPGUNLABEL, imgPath), moduleParams, extraParams)
            return self.__getSerializedToolTipData(self.TOOLTIP_TYPE.MODULE, self.TOOLTIP_COMPONENT.SHOP, moduleParams)

    def getInventoryModuleData(self, compact, sellPrice, sellCurrency, inventoryCount = 0, vehicleCount = 0):
        module = getItemByCompact(compact)
        if not module:
            return
        else:
            descr = None
            if module.itemTypeName in ('optionalDevice', 'equipment'):
                descr = stripShortDescrTags(module.description)
            params, isClipGun, extraParams = self.__getModuleParams(module, params=gui.GUI_SETTINGS.technicalInfo)
            moduleParams = {'name': module.name,
             'type': module.type,
             'removeable': module.isRemovable,
             'gold': sellCurrency == 'gold',
             'stats': self.__getModuleStats(module, sellPrice=sellPrice, unlockPrice=False, buyPrice=False, inventoryCount=inventoryCount, vehicleCount=vehicleCount),
             'params': params,
             'descr': descr,
             'level': module.level,
             'status': self.__getModuleStatus(module),
             'tooHeavy': self.__isModuleTooHeavy(module),
             'note': self.__getModuleNote(module),
             'effect': self.__getModuleEffect(module)}
            if isClipGun:
                self.__extendModuleClipGunParam(moduleParams)
            if extraParams is not None:
                imgPathArr = CLIP_ICON_PATH.split('..')
                imgPath = 'img://gui' + imgPathArr[1]
                self.__extendModuleExtraParam(i18n.makeString(MENU.MODULEINFO_PARAMETERSCLIPGUNLABEL, imgPath), moduleParams, extraParams)
            return self.__getSerializedToolTipData(self.TOOLTIP_TYPE.MODULE, self.TOOLTIP_COMPONENT.INVENTORY, moduleParams)

    def __isModuleCurrentForVehicle(self, module, vehicle):
        if module.compactDescr == vehicle.descriptor.gun['compactDescr'] or module.compactDescr == vehicle.descriptor.turret['compactDescr'] or module.compactDescr == vehicle.descriptor.engine['compactDescr'] or module.compactDescr == vehicle.descriptor.chassis['compactDescr'] or module.compactDescr == vehicle.descriptor.radio['compactDescr']:
            return True
        return False

    def getHangarModuleData(self, compact, buyPrice, inventoryCount = 0, vehicleCount = 0, slotIdx = 0):
        module = getItemByCompact(compact)
        if not module:
            return
        else:
            vehicle = self.__inventoryVehicles.get(g_currentVehicle.invID)
            newStyleVehicle = g_currentVehicle.item
            descr = None
            if module.itemTypeName in ('optionalDevice', 'equipment'):
                descr = stripShortDescrTags(module.description)
            isUnlocked = module.compactDescr in self.__unlocks
            installed = False
            if vehicle is not None:
                if module.itemTypeName == 'optionalDevice':
                    devices = [ dev.intCD for dev in newStyleVehicle.optDevices if dev is not None ]
                    if not module.compactDescr in devices:
                        installed = inventoryCount > 0
                    elif module.itemTypeName == 'equipment':
                        equipments = [ eq.intCD for eq in newStyleVehicle.eqs if eq is not None ]
                        installed = module.compactDescr in equipments
                    else:
                        installed = self.__isModuleCurrentForVehicle(module, vehicle)
                params, isClipGun, _ = self.__getModuleParams(module, vehicle, params=gui.GUI_SETTINGS.technicalInfo)
                moduleParams = {'name': module.name,
                 'type': module.type,
                 'removeable': module.isRemovable,
                 'gold': module.priceOrder[1] != 0,
                 'params': params,
                 'stats': self.__getModuleStats(module, newStyleVehicle, buyPrice=not installed, unlockPrice=not isUnlocked, inventoryCount=inventoryCount, vehicleCount=vehicleCount),
                 'descr': descr,
                 'level': module.level,
                 'status': self.__getModuleStatus(module, vehicle, slotIdx=int(slotIdx)),
                 'tooHeavy': self.__isModuleTooHeavy(module, vehicle, slotIdx=int(slotIdx)),
                 'note': self.__getModuleNote(module),
                 'effect': self.__getModuleEffect(module)}
                isClipGun and self.__extendModuleClipGunParam(moduleParams)
            return self.__getSerializedToolTipData(self.TOOLTIP_TYPE.MODULE, self.TOOLTIP_COMPONENT.HANGAR, moduleParams)

    def __extendModuleClipGunParam(self, moduleParams):
        moduleParams[EXTRA_MODULE_INFO] = {'source': CLIP_ICON_PATH,
         'text': '<h>' + makeString(MENU.MODULEINFO_CLIPGUNLABEL) + '</h>'}

    def __extendModuleExtraParam(self, headerText, moduleParams, params):
        moduleParams['paramsEx'] = {'headerText': headerText,
         'params': params}

    def getTechMainModuleData(self, compact, buyPrice, inventoryCount = 0, vehicleCount = 0, slotIdx = 0, eqsUnlocks = list()):
        module = getItemByCompact(compact)
        if not module:
            return
        else:
            vehicle = self.__inventoryVehicles.get(g_currentVehicle.invID)
            newStyleVehicle = g_currentVehicle.item
            module.priceOrder = buyPrice
            index = 0
            unlocks = list()
            for eq in eqsUnlocks:
                if eq is not None:
                    e = getItemByCompact(eq)
                    e.index = index
                    unlocks.append(e)
                index += 1

            descr = None
            if module.itemTypeName in ('optionalDevice', 'equipment'):
                descr = stripShortDescrTags(module.description)
            isUnlocked = module.compactDescr in self.__unlocks
            params, isClipGun, _ = self.__getModuleParams(module, vehicle, params=gui.GUI_SETTINGS.technicalInfo)
            moduleParams = {'name': module.name,
             'type': module.type,
             'removeable': module.isRemovable,
             'gold': module.priceOrder[1] != 0,
             'params': params,
             'stats': self.__getModuleStats(module, newStyleVehicle, unlockPrice=not isUnlocked, inventoryCount=inventoryCount, vehicleCount=vehicleCount),
             'descr': descr,
             'level': module.level,
             'status': self.__getModuleStatus(module, vehicle, slotIdx=slotIdx, eqsUnlocks=unlocks),
             'tooHeavy': self.__isModuleTooHeavy(module, vehicle, slotIdx=slotIdx),
             'note': self.__getModuleNote(module),
             'effect': self.__getModuleEffect(module)}
            if isClipGun:
                self.__extendModuleClipGunParam(moduleParams)
            return self.__getSerializedToolTipData(self.TOOLTIP_TYPE.MODULE, self.TOOLTIP_COMPONENT.HANGAR, moduleParams)

    def __getShellStats(self, shell, sellPrice = None, buyPrice = True, inventoryCount = 0):
        result = list()
        if sellPrice is not None:
            result.append(['sell_price', sellPrice])
        if buyPrice:

            def getNeedValue(forGold, value):
                return value - self.__getMoney()[1 if forGold else 0]

            buyPriceValue = ['buy_price', shell.priceOrder[1] if shell.priceOrder[1] else shell.priceOrder[0]]
            need = getNeedValue(shell.priceOrder[1] > 0, buyPriceValue[1])
            if need > 0:
                buyPriceValue.append(need)
            result.append(buyPriceValue)
            if self.__shop.isEnabledBuyingGoldShellsForCredits and shell.priceOrder[1] > 0:
                result.append(['textDelimiter/or', ''])
                buyPriceValue = ['buy_price_action', self.__shop.exchangeRateForShellsAndEqs * shell.priceOrder[1]]
                need = getNeedValue(False, buyPriceValue[1])
                if need > 0:
                    buyPriceValue.append(need)
                result.append(buyPriceValue)
        if inventoryCount:
            result.append(['inventoryCount', inventoryCount])
        return result

    def __getShellParams(self, shell, vehicle = None, params = True, vehicleCount = 0):
        result = list()
        vDescr = vehicle.descriptor if vehicle is not None else None
        result.append([])
        if params:
            result = [ItemsParameters.g_instance.getParameters(shell.descriptor, vDescr)]
        result.append([])
        if vehicle is not None:
            gun = VehicleItem(vehicle.descriptor.gun)
            result[-1].append({'label': 'ammo',
             'current': vehicleCount or getattr(shell, 'count', 0),
             'total': gun.descriptor['maxAmmo']})
        return result

    def getHangarShellData(self, compact, inventoryCount = 0, vehicleCount = 0):
        shell = getItemByCompact(compact)
        if not shell:
            return
        else:
            vehicle = self.__inventoryVehicles.get(g_currentVehicle.invID)
            priceOrder = shell.priceOrder
            price = self.__getMoney()
            status = None
            statusLvl = InventoryVehicle.STATE_LEVEL.WARNING
            if price[0] < priceOrder[0]:
                status = '#tooltips:moduleFits/credit_error'
                statusLvl = InventoryVehicle.STATE_LEVEL.CRITICAL
            elif price[1] < priceOrder[1]:
                status = '#tooltips:moduleFits/gold_error'
                statusLvl = InventoryVehicle.STATE_LEVEL.CRITICAL
            statusHeader, statusText = self.__getComplexStatus(status)
            return self.__getSerializedToolTipData(self.TOOLTIP_TYPE.SHELL, self.TOOLTIP_COMPONENT.HANGAR, {'name': shell.name,
             'type': shell.type,
             'gold': priceOrder[1] != 0,
             'icon': '../maps/icons/ammopanel/ammo/%s' % shell.descriptor['icon'][0],
             'stats': self.__getShellStats(shell, buyPrice=True, inventoryCount=inventoryCount),
             'params': self.__getShellParams(shell, vehicle, vehicleCount=vehicleCount),
             'status': {'header': statusHeader,
                        'text': statusText,
                        'level': statusLvl}})

    def getTechMainShellData(self, compact, buyPrice, inventoryCount = 0, vehicleCount = 0):
        shell = getItemByCompact(compact)
        if not shell:
            return None
        else:
            vehicle = self.__inventoryVehicles.get(g_currentVehicle.invID)
            return self.__getSerializedToolTipData(self.TOOLTIP_TYPE.SHELL, self.TOOLTIP_COMPONENT.HANGAR, {'name': shell.name,
             'type': shell.type,
             'gold': buyPrice[1] != 0,
             'icon': '../maps/icons/ammopanel/ammo/%s' % shell.descriptor['icon'][0],
             'stats': self.__getShellStats(shell, inventoryCount=inventoryCount),
             'params': self.__getShellParams(shell, vehicle, vehicleCount=vehicleCount)})

    def getShopShellData(self, compact, inventoryCount = 0):
        shell = getItemByCompact(compact)
        if not shell:
            return
        else:
            priceOrder = shell.priceOrder
            price = self.__getMoney()
            status = None
            statusLvl = InventoryVehicle.STATE_LEVEL.WARNING
            if price[0] < priceOrder[0]:
                status = '#tooltips:moduleFits/credit_error'
                statusLvl = InventoryVehicle.STATE_LEVEL.CRITICAL
            elif price[1] < priceOrder[1]:
                status = '#tooltips:moduleFits/gold_error'
                statusLvl = InventoryVehicle.STATE_LEVEL.CRITICAL
            statusHeader, statusText = self.__getComplexStatus(status)
            return self.__getSerializedToolTipData(self.TOOLTIP_TYPE.SHELL, self.TOOLTIP_COMPONENT.SHOP, {'name': shell.name,
             'type': shell.type,
             'gold': priceOrder[1] != 0,
             'icon': '../maps/icons/ammopanel/ammo/%s' % shell.descriptor['icon'][0],
             'stats': self.__getShellStats(shell, inventoryCount=inventoryCount),
             'params': self.__getShellParams(shell),
             'status': {'header': statusHeader,
                        'text': statusText,
                        'level': statusLvl}})

    def getInventoryShellData(self, compact, inventoryCount = 0):
        shell = getItemByCompact(compact)
        if not shell:
            return
        else:
            sellPrice = (0, 0)
            item = g_itemsCache.items.getItemByCD(shell.compactDescr)
            if item is not None:
                sellPrice = item.sellPrice
            return self.__getSerializedToolTipData(self.TOOLTIP_TYPE.SHELL, self.TOOLTIP_COMPONENT.INVENTORY, {'name': shell.name,
             'type': shell.type,
             'gold': bool(sellPrice[1]),
             'icon': '../maps/icons/ammopanel/ammo/%s' % shell.descriptor['icon'][0],
             'stats': self.__getShellStats(shell, sellPrice=sellPrice[1] or sellPrice[0], buyPrice=False, inventoryCount=inventoryCount),
             'params': self.__getShellParams(shell)})

    def __getTankmanEnabledSkillOnVehicle(self, tankman, vehicle = None):
        enabledSkills = SKILLS_BY_ROLES[tankman.descriptor.role]
        if vehicle is not None:
            roles = list()
            if tankman.inventoryId in vehicle.crew:
                pos = vehicle.crew.index(tankman.inventoryId)
                roles = vehicle.descriptor.type.crewRoles[pos]
            else:
                for rs in vehicle.descriptor.type.crewRoles:
                    if tankman.descriptor.role in rs:
                        roles = rs
                        break

            for role in roles:
                enabledSkills |= SKILLS_BY_ROLES[role]

        return enabledSkills

    def __getTankmanSkills(self, tankman, vehicle = None):
        result = list()
        enabledSkills = self.__getTankmanEnabledSkillOnVehicle(tankman, vehicle)
        for skill in tankman.skills:
            isLast = tankman.skills.index(skill) == len(tankman.skills) - 1
            result.append({'id': skill,
             'label': getSkillsConfig()[skill]['userString'],
             'level': 100 if not isLast else tankman.lastSkillLevel,
             'enabled': skill in enabledSkills or vehicle is None})

        return result

    def __getTankmanRoleBySkill(self, tankman, skill):
        for role, skills in SKILLS_BY_ROLES.iteritems():
            if skill in skills:
                return role

    def __getTankmanStatus(self, tankman, vehicle = None):
        header = ''
        text = ''
        nativeVehicle = tankman.vehicle
        inactiveRoles = list()
        enabledSkills = self.__getTankmanEnabledSkillOnVehicle(tankman, vehicle)
        for skill in tankman.skills:
            if skill not in enabledSkills:
                role = self.__getTankmanRoleBySkill(tankman, skill)
                if role not in inactiveRoles:
                    inactiveRoles.append(role)

        if vehicle is not None and nativeVehicle.type.id != vehicle.descriptor.type.id:
            if vehicle.isPremium and vehicle.type in nativeVehicle.type.tags:
                header = makeString('#tooltips:tankman/status/wrongPremiumVehicle/header')
                text = makeString('#tooltips:tankman/status/wrongPremiumVehicle/text') % {'vehicle': vehicle.shortName}
            else:
                header = makeString('#tooltips:tankman/status/wrongVehicle/header') % {'vehicle': vehicle.shortName}
                text = makeString('#tooltips:tankman/status/wrongVehicle/text')
        elif len(inactiveRoles):

            def roleFormat(role):
                return makeString('#tooltips:tankman/status/inactiveSkillsRoleFormat') % makeString(getSkillsConfig()[role]['userString'])

            header = makeString('#tooltips:tankman/status/inactiveSkills/header')
            text = makeString('#tooltips:tankman/status/inactiveSkills/text') % {'skills': ', '.join([ roleFormat(role) for role in inactiveRoles ])}
        return {'header': header,
         'text': text,
         'level': InventoryVehicle.STATE_LEVEL.WARNING}

    def getTankmanData(self, tankmanID, isCurrentVehicle = True):
        tankman = self.__tankmen.get(tankmanID)
        if tankman is None:
            return
        else:
            specVehicleDescr = tankman.vehicle
            currentVehicle = self.__inventoryVehicles.get(tankman.vehicleID)
            if isCurrentVehicle:
                currentVehicle = self.__inventoryVehicles.get(g_currentVehicle.invID)
            newSkillsCount, lastNewSkillLevel = tankman.newSkillCount
            currentVehicleContourIcon = None
            efficiencyRoleLevel = tankman.roleLevel
            brotherhoodBonus = getSkillsConfig()['brotherhood']['crewLevelIncrease'] if currentVehicle is not None else 0
            roleBonus = 0
            rolePenalty = 0
            if currentVehicle is not None:
                efficiencyRoleLevel = tankman.efficiencyRoleLevel(currentVehicle.descriptor)
                commanderBonus = 0
                eqsCache = dict([ (e['compactDescr'], e) for _, e in vehicles.g_cache.equipments().iteritems() ])
                for compactDescr in currentVehicle.equipments:
                    eq = eqsCache.get(compactDescr)
                    if eq is not None and isinstance(eq, artefacts.Stimulator):
                        efficiencyRoleLevel += eq['crewLevelIncrease']

                currentVehicleContourIcon = _ICONS_MASK % {'type': 'vehicle',
                 'subtype': 'contour/',
                 'unicName': currentVehicle.descriptor.type.name.replace(':', '-')}
                for i in range(len(currentVehicle.crew)):
                    tankmanID = currentVehicle.crew[i]
                    t = self.__tankmen.get(tankmanID)
                    if tankmanID is None or 'brotherhood' not in t.skills or t.skills.index('brotherhood') == len(t.skills) - 1 and t.lastSkillLevel != MAX_SKILL_LEVEL:
                        brotherhoodBonus = 0
                    if tankmanID is not None and currentVehicle.descriptor.type.crewRoles[i][0] == 'commander':
                        commanderBonus = round((t.efficiencyRoleLevel(currentVehicle.descriptor) + brotherhoodBonus) / COMMANDER_ADDITION_RATIO)

                roleBonus = commanderBonus if tankman.descriptor.role != 'commander' else 0
                rolePenalty = efficiencyRoleLevel - tankman.roleLevel
            return self.__getSerializedToolTipData(self.TOOLTIP_TYPE.TANKMAN, self.TOOLTIP_COMPONENT.HANGAR, {'name': '%s %s' % (tankman.firstname, tankman.lastname),
             'rank': tankman.rank,
             'role': tankman.role,
             'roleLevel': tankman.roleLevel,
             'efficiencyRoleLevel': efficiencyRoleLevel,
             'roleLevelBonus': roleBonus,
             'roleLevelPenalty': rolePenalty,
             'roleLevelBrothers': brotherhoodBonus,
             'vehicleType': tankman.vehicleType,
             'vehicleName': specVehicleDescr.type.userString,
             'currentVehicleName': currentVehicle.descriptor.type.userString if currentVehicle else '',
             'currentVehicleType': currentVehicle.vehicleType if currentVehicle else '',
             'isInTank': tankman.isInTank,
             'iconRole': tankman.iconRole,
             'nation': tankman.nation,
             'skills': self.__getTankmanSkills(tankman, currentVehicle),
             'newSkillsCount': newSkillsCount,
             'vehicleContour': currentVehicleContourIcon,
             'isCurrentVehiclePremium': currentVehicle.isPremium if currentVehicle else False,
             'status': self.__getTankmanStatus(tankman, currentVehicle)})

    def getEfficiencyParam(self, kind, vals):
        return self.__getSerializedToolTipData(self.TOOLTIP_TYPE.EFFICIENCY, self.TOOLTIP_COMPONENT.FINAL_STATISTIC, vals)

    def getIgrInfo(self):
        qLabels = []
        qProgress = []
        quests = []
        if game_control.g_instance.igr.getRoomType() == constants.IGR_TYPE.PREMIUM:
            quests = g_questsCache.getQuests()
            for q in quests.itervalues():
                if q.isIGR():
                    meta = q.getBonuses(True).get('meta')
                    if meta is not None:
                        qLabels.append(meta.format())
                    isWin = q._data['conditions']['postBattle'].get('win', False)
                    battlesCount = q._data['conditions']['bonus'].get('battles')
                    if battlesCount is not None:
                        curProgress = 0
                        if q._progress is not None:
                            curProgress = q._progress.values()[0].get('battlesCount', 0)
                        qProgress.append([curProgress, battlesCount.get('value', 0), makeString('#quests:igr/tooltip/winsLabel') if isWin else makeString('#quests:igr/tooltip/battlesLabel')])

        template = gui.g_htmlTemplates['html_templates:lobby/tooltips']['igr_quest']
        descriptionTemplate = 'igr_description' if len(qLabels) == 0 else 'igr_description_with_quests'
        igrPercent = (game_control.g_instance.igr.getXPFactor() - 1) * 100
        return self.__getSerializedToolTipData(self.TOOLTIP_TYPE.IGR, self.TOOLTIP_COMPONENT.HANGAR, {'title': gui.makeHtmlString('html_templates:lobby/tooltips', 'igr_title', {'msg': makeString('#tooltips:igr/title')}),
         'description': gui.makeHtmlString('html_templates:lobby/tooltips', descriptionTemplate, {'igrValue': '{0}%'.format(BigWorld.wg_getIntegralFormat(igrPercent))}),
         'quests': map(lambda i: i.format(**template.ctx), qLabels),
         'progressHeader': gui.makeHtmlString('html_templates:lobby/tooltips', 'igr_progress_header', {}),
         'progress': qProgress})
import re
import math
import BigWorld
import ArenaType
from account_helpers.AccountSettings import AccountSettings
from debug_utils import LOG_ERROR, LOG_CURRENT_EXCEPTION, LOG_DEBUG
from helpers import i18n
from adisp import async, process
from CurrentVehicle import g_currentVehicle
from arena_achievements import ACHIEVEMENTS, ACHIEVEMENTS_WITH_REWARD
from constants import ARENA_BONUS_TYPE, IS_DEVELOPMENT, ARENA_GUI_TYPE, IGR_TYPE
from dossiers import RECORD_NAMES, RECORD_INDICES
from helpers import time_utils
from gui import makeHtmlString
from gui.shared import g_questsCache, events
from gui.shared.quests import event_items
from gui.shared.utils.dossiers_utils import getMedalDict
from gui.shared.utils.requesters import Requester, StatsRequesterr
from items import vehicles as vehicles_core, vehicles
from gui.shared.utils.requesters import StatsRequester
from gui.Scaleform.framework.entities.View import View
from gui.Scaleform.daapi.view.meta.BattleResultsMeta import BattleResultsMeta
from gui.Scaleform.daapi.view.meta.WindowViewMeta import WindowViewMeta
from messenger.proto.events import g_messengerEvents
from messenger.storage import storage_getter
from gui.shared.gui_items.Vehicle import VEHICLE_BATTLE_TYPES_ORDER_INDICES
from items.vehicles import VEHICLE_CLASS_TAGS
RESULT_ = '#menu:finalStatistic/commonStats/resultlabel/{0}'
BATTLE_RESULTS_STR = '#battle_results:{0}'
FINISH_REASON = BATTLE_RESULTS_STR.format('finish/reason/{0}')
RESULT_LINE_STR = BATTLE_RESULTS_STR.format('details/calculations/{0}')
STATS_KEY_BASE = BATTLE_RESULTS_STR.format('team/stats/labels_{0}')
TIME_STATS_KEY_BASE = BATTLE_RESULTS_STR.format('details/time/lbl_{0}')
XP_TITLE = BATTLE_RESULTS_STR.format('common/details/xpTitle')
XP_TITLE_DAILY = BATTLE_RESULTS_STR.format('common/details/xpTitleFirstVictory')
MILEAGE_STR_KEY = BATTLE_RESULTS_STR.format('team/stats/mileage')
TIME_DURATION_STR = BATTLE_RESULTS_STR.format('details/time/value')
XP_MULTIPLIER_SIGN_KEY = BATTLE_RESULTS_STR.format('common/xpMultiplierSign')
EFFICIENCY_ALLIES_STR = BATTLE_RESULTS_STR.format('common/battleEfficiency/allies')
UNKNOWN_PLAYER_NAME_VALUE = '#ingame_gui:players_panel/unknown_name'
UNKNOWN_VEHICLE_NAME_VALUE = '#ingame_gui:players_panel/unknown_vehicle'
ARENA_TYPE = '#arenas:type/{0}/name'
ARENA_SPECIAL_TYPE = '#menu:loading/battleTypes/{0}'
VEHICLE_ICON_FILE = '../maps/icons/vehicle/{0}.png'
VEHICLE_ICON_SMALL_FILE = '../maps/icons/vehicle/small/{0}.png'
VEHICLE_NO_IMAGE_FILE_NAME = 'noImage'
ARENA_SCREEN_FILE = '../maps/icons/map/stats/{0}.png'
ARENA_NAME_PATTERN = '{0} - {1}'
LINE_BRAKE_STR = '<br/>'
ACHIEVEMENTS_WITH_RIBBON = ('medalOrlik', 'medalOskin', 'medalHalonen', 'medalBurda', 'medalBillotte', 'medalKolobanov', 'medalFadin', 'medalRadleyWalters', 'medalLafayettePool', 'medalLehvaslaiho', 'medalNikolas', 'medalPascucci', 'medalDumitru', 'medalBrunoPietro', 'medalTarczay', 'heroesOfRassenay', 'medalDeLanglade', 'medalTamadaYoshio', 'medalWittmann', 'markOfMastery4')
STATS_KEYS = [('shots', True, None),
 ('hits', True, None),
 ('he_hits', True, None),
 ('pierced', True, None),
 ('damageDealt', True, None),
 ('shotsReceived', True, None),
 ('piercedReceived', True, None),
 ('heHitsReceived', True, None),
 ('noDamageShotsReceived', True, None),
 ('potentialDamageReceived', True, None),
 ('teamHitsDamage', False, None),
 ('spotted', True, None),
 ('damaged', True, None),
 ('kills', True, None),
 ('damageAssisted', True, 'damageAssistedSelf'),
 ('capturePoints', True, None),
 ('droppedCapturePoints', True, None),
 ('mileage', False, None)]
TIME_STATS_KEYS = ['arenaCreateTimeOnlyStr', 'duration', 'playerKilled']

class BattleResultsWindow(View, WindowViewMeta, BattleResultsMeta):
    __playersNameCache = dict()

    def __init__(self, ctx):
        super(BattleResultsWindow, self).__init__()
        self.arenaUniqueID = ctx.get('arenaUniqueID')
        self.stats = None
        self.__openedWindowsArenaID = []
        if IS_DEVELOPMENT:
            self.testData = ctx.get('testData')
        return

    @storage_getter('users')
    def usersStorage(self):
        return None

    @process
    def _populate(self):
        super(BattleResultsWindow, self)._populate()
        g_messengerEvents.users.onUserRosterChanged += self.onUsersRosterUpdated
        self.stats = yield StatsRequesterr().request()
        commonData = yield self.__getCommonData()
        self.as_setDataS(commonData)
        self.__openedWindowsArenaID = None
        return

    def _dispose(self):
        g_messengerEvents.users.onUserRosterChanged -= self.onUsersRosterUpdated
        super(BattleResultsWindow, self)._dispose()

    def onWindowClose(self):
        self.destroy()

    def getDenunciations(self):
        if self.stats is not None:
            return self.stats.denunciationsLeft
        else:
            return 0

    def showQuestsWindow(self, qID):
        self.fireEvent(events.ShowWindowEvent(events.ShowWindowEvent.SHOW_QUESTS_WINDOW, {'questID': qID}))

    def saveSorting(self, iconType, sortDirection):
        AccountSettings.setSettings('statsSorting', {'iconType': iconType,
         'sortDirection': sortDirection})

    def __getPlayerName(self, playerDBID, playersData):
        playerName = self.__playersNameCache.get(playerDBID, None)
        if playerName is None:
            playerInfo = playersData.get(playerDBID, dict())
            playerName = playerInfo.get('name', i18n.makeString(UNKNOWN_PLAYER_NAME_VALUE))
            clanName = playerInfo.get('clanAbbrev', '')
            if len(clanName) > 0:
                playerName = '{0} [{1}]'.format(playerName, clanName)
            self.__playersNameCache[playerDBID] = playerName
        return playerName

    def __getPlayerClan(self, playerDBID, playersData):
        playerInfo = playersData.get(playerDBID, dict())
        clanName = playerInfo.get('clanAbbrev', '')
        return clanName

    def __getVehicleData(self, vehicleCompDesc):
        vehicleName = i18n.makeString(UNKNOWN_VEHICLE_NAME_VALUE)
        vehicleShortName = i18n.makeString(UNKNOWN_VEHICLE_NAME_VALUE)
        vehicleIcon = VEHICLE_ICON_FILE.format(VEHICLE_NO_IMAGE_FILE_NAME)
        vehicleIconSmall = VEHICLE_ICON_SMALL_FILE.format(VEHICLE_NO_IMAGE_FILE_NAME)
        vehicleBalanceWeight = 0
        if vehicleCompDesc:
            vt = vehicles_core.getVehicleType(vehicleCompDesc)
            vehicleName = vt.userString
            vehicleShortName = vt.shortUserString
            nameReplaced = vt.name.replace(':', '-')
            vehicleIcon = VEHICLE_ICON_FILE.format(nameReplaced)
            vehicleIconSmall = VEHICLE_ICON_SMALL_FILE.format(nameReplaced)
            _, nation, nId = vehicles_core.parseIntCompactDescr(vehicleCompDesc)
            vDescr = vehicles_core.VehicleDescr(typeID=(nation, nId))
            vehicleBalanceWeight = vDescr.balanceWeight
        return (vehicleName,
         vehicleShortName,
         vehicleIcon,
         vehicleIconSmall,
         vehicleBalanceWeight)

    def __vehiclesComparator(self, item, other):
        res = 0
        iKiller = item.get('killerID', 0)
        cd = item.get('typeCompDescr')
        if cd is not None:
            iType = vehicles_core.getVehicleType(cd)
            iLevel = iType.level if iType else -1
            iWeight = VEHICLE_BATTLE_TYPES_ORDER_INDICES.get(set(VEHICLE_CLASS_TAGS.intersection(iType.tags)).pop(), 10) if iType else 10
        else:
            iLevel = -1
            iWeight = 10
        oKiller = other.get('killerID', 0)
        cd = other.get('typeCompDescr')
        if cd is not None:
            oType = vehicles_core.getVehicleType(other.get('typeCompDescr', None))
            oLevel = oType.level if oType else -1
            oWeight = VEHICLE_BATTLE_TYPES_ORDER_INDICES.get(set(VEHICLE_CLASS_TAGS.intersection(oType.tags)).pop(), 10) if oType else 10
        else:
            oLevel = -1
            oWeight = 10
        if iKiller == 0 and oKiller == 0 or iKiller != 0 and oKiller != 0:
            res = cmp(oLevel, iLevel) or cmp(iWeight, oWeight) or cmp(item.get('vehicleName', ''), other.get('vehicleName', ''))
        elif not iKiller:
            res = -1
        else:
            res = 1
        return res

    def __getStatsLine(self, label = None, col1 = None, col2 = None, col3 = None, col4 = None):
        if col2 is not None:
            lineType = 'wideLine'
        else:
            lineType = 'normalLine'
        lbl = label + '\n' if label is not None else '\n'
        lblStripped = re.sub('<[^<]+?>', '', lbl)
        return {'label': lbl,
         'labelStripped': lblStripped,
         'col1': col1 if col1 is not None else '\n',
         'col2': col2 if col2 is not None else '\n',
         'col3': col3 if col3 is not None else '\n',
         'col4': col4 if col4 is not None else '\n',
         'lineType': None if label is None else lineType}

    def __resultLabel(self, label):
        return i18n.makeString(RESULT_LINE_STR.format(label))

    def __makeCreditsLabel(self, value, canBeFaded = False):
        valStr = BigWorld.wg_getGoldFormat(round(value))
        if value < 0:
            valStr = self.__makeRedLabel(valStr)
        templateName = 'credits_small_inactive_label' if canBeFaded and value == 0 else 'credits_small_label'
        return makeHtmlString('html_templates:lobby/battle_results', templateName, {'value': valStr})

    def __makeXpLabel(self, value, canBeFaded = False):
        valStr = BigWorld.wg_getIntegralFormat(round(value))
        if value < 0:
            valStr = self.__makeRedLabel(valStr)
        templateName = 'xp_small_inactive_label' if canBeFaded and value == 0 else 'xp_small_label'
        return makeHtmlString('html_templates:lobby/battle_results', templateName, {'value': valStr})

    def __makeFreeXpLabel(self, value, canBeFaded = False):
        valStr = BigWorld.wg_getIntegralFormat(round(value))
        templateName = 'free_xp_small_inactive_label' if canBeFaded and value == 0 else 'free_xp_small_label'
        return makeHtmlString('html_templates:lobby/battle_results', templateName, {'value': valStr})

    def __makeGoldLabel(self, value, canBeFaded = False):
        valStr = BigWorld.wg_getGoldFormat(value)
        templateName = 'gold_small_inactive_label' if canBeFaded and value == 0 else 'gold_small_label'
        return makeHtmlString('html_templates:lobby/battle_results', templateName, {'value': valStr})

    def __makeRedLabel(self, value):
        return makeHtmlString('html_templates:lobby/battle_results', 'negative_value', {'value': value})

    def __populateStatValues(self, node, isSelf = False):
        node['teamHitsDamage'] = self.__makeTeamDamageStr(node)
        node['mileage'] = self.__makeMileageStr(node.get('mileage', 0))
        result = []
        for key, isInt, selfKey in STATS_KEYS:
            if isInt:
                value = node.get(key, 0)
                valueFormatted = BigWorld.wg_getIntegralFormat(value)
                if not value:
                    valueFormatted = makeHtmlString('html_templates:lobby/battle_results', 'empty_stat_value', {'value': valueFormatted})
            else:
                valueFormatted = node.get(key, '')
            if isSelf and selfKey is not None:
                key = selfKey
            result.append({'label': i18n.makeString(STATS_KEY_BASE.format(key)),
             'value': valueFormatted})

        return result

    def __isNoPenaltyApplied(self, commonData, pData):
        winnerTeam = commonData.get('winnerTeam', 0)
        if commonData.get('guiType', 0) == ARENA_GUI_TYPE.RANDOM and winnerTeam != pData.get('team'):
            medalIds = [ p[0] for p in pData.get('dossierPopUps', []) ]
            medalIds.extend(pData.get('achievements', []))
            intersection = set(medalIds).intersection(ACHIEVEMENTS_WITH_REWARD)
            return len(intersection) > 0
        else:
            return False

    def __populateAccounting(self, commonData, pData):
        pData['creditsStr'] = BigWorld.wg_getGoldFormat(pData.get('credits', 0))
        pData['xpStr'] = BigWorld.wg_getIntegralFormat(pData.get('xp', 0))
        pData['xpTitleStr'] = i18n.makeString(XP_TITLE)
        dailyXpFactor = float(pData.get('dailyXPFactor10', 10)) / 10.0
        igrXpFactor = float(pData.get('igrXPFactor10', 10)) / 10.0
        isPremium = pData.get('isPremium', False)
        aogas = float(pData.get('aogasFactor10', 10)) / 10
        if dailyXpFactor > 1:
            pData['xpTitleStr'] += i18n.makeString(XP_TITLE_DAILY, dailyXpFactor)
        noPenaltyLbl = None
        if self.__isNoPenaltyApplied(commonData, pData):
            noPenaltyLbl = makeHtmlString('html_templates:lobby/battle_results', 'noPenalty', {})
        creditsData = []
        creditsPenalty = self.__calculateBaseCreditsPenalty(pData)
        creditsCompensation = self.__calculateBaseCreditsContribution(pData)
        premCreditsF10 = float(pData.get('premiumCreditsFactor10', 10))
        creditsBase = int(self.__calculateBaseCredits(pData))
        creditsCell = creditsBase + creditsPenalty - creditsCompensation
        creditsBaseStr = self.__makeCreditsLabel(creditsCell, not isPremium)
        creditsBasePremStr = self.__makeCreditsLabel(int(creditsBase * premCreditsF10 / 10.0) + int(creditsPenalty * premCreditsF10 / 10.0) - int(creditsCompensation * premCreditsF10 / 10.0), isPremium)
        label = self.__resultLabel('base')
        if noPenaltyLbl is not None:
            label = '{0}{1}'.format(label, noPenaltyLbl)
        creditsData.append(self.__getStatsLine(label, creditsBaseStr, None, creditsBasePremStr, None))
        eventCredits = pData.get('eventCredits', 0)
        eventGold = pData.get('eventGold', 0)
        creditsEventStr = self.__makeCreditsLabel(eventCredits, not isPremium) if eventCredits else None
        creditsEventPremStr = self.__makeCreditsLabel(eventCredits, isPremium) if eventCredits else None
        goldEventStr = self.__makeGoldLabel(eventGold, not isPremium) if eventGold else None
        goldEventPremStr = self.__makeGoldLabel(eventGold, isPremium) if eventGold else None
        if eventCredits > 0 or eventGold > 0:
            creditsData.append(self.__getStatsLine(self.__resultLabel('event'), creditsEventStr, goldEventStr, creditsEventPremStr, goldEventPremStr))
        creditsData.append(self.__getStatsLine())
        creditsPenaltyStr = self.__makeCreditsLabel(int(-creditsPenalty), not isPremium)
        creditsPenaltyPremStr = self.__makeCreditsLabel(int(-creditsPenalty * premCreditsF10 / 10.0), isPremium)
        creditsData.append(self.__getStatsLine(self.__resultLabel('friendlyFirePenalty'), creditsPenaltyStr, None, creditsPenaltyPremStr, None))
        creditsCompensationStr = self.__makeCreditsLabel(int(creditsCompensation), not isPremium)
        creditsCompensationPremStr = self.__makeCreditsLabel(int(creditsCompensation * premCreditsF10 / 10.0), isPremium)
        creditsData.append(self.__getStatsLine(self.__resultLabel('friendlyFireCompensation'), creditsCompensationStr, None, creditsCompensationPremStr, None))
        creditsData.append(self.__getStatsLine())
        if aogas < 1:
            aogasValStr = ''.join([i18n.makeString(XP_MULTIPLIER_SIGN_KEY), BigWorld.wg_getFractionalFormat(aogas)])
            aogasValStr = self.__makeRedLabel(aogasValStr)
            creditsData.append(self.__getStatsLine(self.__resultLabel('aogas'), aogasValStr, None, aogasValStr, None))
        creditsData.append(self.__getStatsLine())
        creditsAutoRepair = pData.get('autoRepairCost', 0)
        if creditsAutoRepair is None:
            creditsAutoRepair = 0
        creditsAutoRepairStr = self.__makeCreditsLabel(-creditsAutoRepair, not isPremium)
        creditsAutoRepairPremStr = self.__makeCreditsLabel(-creditsAutoRepair, isPremium)
        creditsData.append(self.__getStatsLine(self.__resultLabel('autoRepair'), creditsAutoRepairStr, None, creditsAutoRepairPremStr, None))
        autoLoadCost = pData.get('autoLoadCost', (0, 0))
        if autoLoadCost is None:
            autoLoadCost = (0, 0)
        creditsAutoLoad, goldAutoLoad = autoLoadCost
        creditsAutoLoadStr = self.__makeCreditsLabel(-creditsAutoLoad, not isPremium)
        creditsAutoLoadPremStr = self.__makeCreditsLabel(-creditsAutoLoad, isPremium)
        goldAutoLoadStr = self.__makeGoldLabel(-goldAutoLoad, not isPremium)
        goldAutoLoadPremStr = self.__makeGoldLabel(-goldAutoLoad, isPremium)
        creditsData.append(self.__getStatsLine(self.__resultLabel('autoLoad'), creditsAutoLoadStr, goldAutoLoadStr, creditsAutoLoadPremStr, goldAutoLoadPremStr))
        autoEquipCost = pData.get('autoEquipCost', (0, 0))
        if autoEquipCost is None:
            autoEquipCost = (0, 0)
        creditsAutoEquip, goldAutoEquip = autoEquipCost
        creditsAutoEquipStr = self.__makeCreditsLabel(-creditsAutoEquip, not isPremium)
        creditsAutoEquipPremStr = self.__makeCreditsLabel(-creditsAutoEquip, isPremium)
        goldAutoEquipStr = self.__makeGoldLabel(-goldAutoEquip, not isPremium)
        goldAutoEquipPremStr = self.__makeGoldLabel(-goldAutoEquip, isPremium)
        creditsData.append(self.__getStatsLine(self.__resultLabel('autoEquip'), creditsAutoEquipStr, goldAutoEquipStr, creditsAutoEquipPremStr, goldAutoEquipPremStr))
        creditsData.append(self.__getStatsLine())
        creditsNoPremTotal = self.__calculateTotalCredits(pData, creditsBase)
        pData['creditsNoPremStr'] = self.__makeCreditsLabel(creditsNoPremTotal, not isPremium)
        creditsNoPremTotalStr = self.__makeCreditsLabel(creditsNoPremTotal - creditsAutoRepair - creditsAutoEquip - creditsAutoLoad, not isPremium)
        pData['creditsNoPremTotalStr'] = creditsNoPremTotalStr
        creditsPremTotal = self.__calculateTotalCredits(pData, creditsBase, True)
        pData['creditsPremStr'] = self.__makeCreditsLabel(creditsPremTotal, isPremium)
        creditsPremTotalStr = self.__makeCreditsLabel(creditsPremTotal - creditsAutoRepair - creditsAutoEquip - creditsAutoLoad, isPremium)
        pData['creditsPremTotalStr'] = creditsPremTotalStr
        goldTotalStr = self.__makeGoldLabel(eventGold - goldAutoEquip - goldAutoLoad, not isPremium)
        goldTotalPremStr = self.__makeGoldLabel(eventGold - goldAutoEquip - goldAutoLoad, isPremium)
        totalLbl = makeHtmlString('html_templates:lobby/battle_results', 'lightText', {'value': self.__resultLabel('total')})
        creditsData.append(self.__getStatsLine(totalLbl, creditsNoPremTotalStr, goldTotalStr, creditsPremTotalStr, goldTotalPremStr))
        pData['creditsData'] = creditsData
        xpData = []
        xpBase = int(self.__calculateBaseXp(pData))
        xpPenalty = int(self.__calculateBaseXpPenalty(pData))
        premXpMulty = float(pData.get('premiumXPFactor10', 10)) / 10.0
        xpCellStr = self.__makeXpLabel(xpBase + xpPenalty, not isPremium)
        xpCellPremStr = self.__makeXpLabel(int((xpBase + xpPenalty) * premXpMulty), isPremium)
        freeXp = pData.get('originalFreeXP', 0)
        freeXpBaseStr = self.__makeFreeXpLabel(freeXp, not isPremium)
        freeXpBasePremStr = self.__makeFreeXpLabel(int(freeXp * premXpMulty), isPremium)
        medals = pData.get('dossierPopUps', [])
        if RECORD_INDICES.get('maxXP') in map(lambda (id, value): id, medals):
            label = makeHtmlString('html_templates:lobby/battle_results', 'xpRecord', {})
        else:
            label = self.__resultLabel('base')
        if noPenaltyLbl is not None:
            label = '{0}{1}'.format(label, noPenaltyLbl)
        xpData.append(self.__getStatsLine(label, xpCellStr, freeXpBaseStr, xpCellPremStr, freeXpBasePremStr))
        basePenalty = -xpPenalty
        xpPenaltyStr = self.__makeXpLabel(basePenalty, not isPremium)
        xpPenaltyPremStr = self.__makeXpLabel(int(basePenalty * premXpMulty), isPremium)
        xpData.append(self.__getStatsLine(self.__resultLabel('friendlyFirePenalty'), xpPenaltyStr, None, xpPenaltyPremStr, None))
        if igrXpFactor > 1:
            igrBonusLabelStr = makeHtmlString('html_templates:lobby/battle_results', 'igr_bonus_label', {})
            igrBonusStr = makeHtmlString('html_templates:lobby/battle_results', 'igr_bonus', {'value': BigWorld.wg_getNiceNumberFormat(igrXpFactor)})
            xpData.append(self.__getStatsLine(igrBonusLabelStr, igrBonusStr, igrBonusStr, igrBonusStr, igrBonusStr))
        if dailyXpFactor > 1:
            dailyXpStr = makeHtmlString('html_templates:lobby/battle_results', 'multy_xp_small_label', {'value': int(dailyXpFactor)})
            xpData.append(self.__getStatsLine(self.__resultLabel('firstWin'), dailyXpStr, dailyXpStr, dailyXpStr, dailyXpStr))
        eventXP = pData.get('eventXP', 0)
        eventFreeXP = pData.get('eventFreeXP', 0)
        if eventXP > 0 or eventFreeXP > 0:
            eventXPStr = self.__makeXpLabel(eventXP, not isPremium)
            eventXPPremStr = self.__makeXpLabel(eventXP, isPremium)
            eventFreeXPStr = self.__makeFreeXpLabel(eventFreeXP, not isPremium)
            eventFreeXPPremStr = self.__makeFreeXpLabel(eventFreeXP, isPremium)
            xpData.append(self.__getStatsLine(self.__resultLabel('event'), eventXPStr, eventFreeXPStr, eventXPPremStr, eventFreeXPPremStr))
        if aogas < 1:
            aogasValStr = ''.join([i18n.makeString(XP_MULTIPLIER_SIGN_KEY), BigWorld.wg_getFractionalFormat(aogas)])
            aogasValStr = self.__makeRedLabel(aogasValStr)
            xpData.append(self.__getStatsLine(self.__resultLabel('aogas'), aogasValStr, aogasValStr, aogasValStr, aogasValStr))
        if len(xpData) < 3:
            xpData.append(self.__getStatsLine())
        if len(xpData) < 7:
            xpData.append(self.__getStatsLine())
        pData['xpNoPremStr'] = self.__makeXpLabel(self.__calculateTotalXp(pData, xpBase), not isPremium)
        pData['xpPremStr'] = self.__makeXpLabel(self.__calculateTotalXp(pData, xpBase, True), isPremium)
        freeXpTotal = self.__makeFreeXpLabel(self.__calculateTotalFreeXp(pData, freeXp), not isPremium)
        freeXpPremTotal = self.__makeFreeXpLabel(self.__calculateTotalFreeXp(pData, freeXp, True), isPremium)
        xpData.append(self.__getStatsLine(totalLbl, pData['xpNoPremStr'], freeXpTotal, pData['xpPremStr'], freeXpPremTotal))
        pData['xpData'] = xpData
        return

    def __populatePersonalMedals(self, pData):
        pData['dossierType'] = None
        pData['dossierCompDescr'] = None
        achievements = pData.get('dossierPopUps', [])
        pData['achievementsLeft'] = []
        pData['achievementsRight'] = []
        for achievementId, achieveValue in achievements:
            if achievementId == RECORD_INDICES.get('maxXP'):
                continue
            medalDict = getMedalDict(RECORD_NAMES[achievementId], rank=achieveValue)
            medalDict['unic'] = True
            type = medalDict['type']
            if type == 'markOfMastery':
                type = ''.join([type, str(medalDict.get('rank'))])
            medalDict['isEpic'] = type in ACHIEVEMENTS_WITH_RIBBON
            if medalDict['type'] in ACHIEVEMENTS:
                pData['achievementsRight'].append(medalDict)
            else:
                pData['achievementsLeft'].append(medalDict)

        pData['achievementsRight'].sort(key=lambda k: k['isEpic'], reverse=True)
        return

    def __getVehicleIdByAccountID(self, accountDBID, vehiclesData):
        vehicleId = None
        for vId, vInfo in vehiclesData.iteritems():
            if vInfo.get('accountDBID', None) == accountDBID:
                vehicleId = vId
                break

        return vehicleId

    def __populateEfficiency(self, pData, vehiclesData, playersData):
        playerTeam = pData.get('team')
        playerDBID = pData.get('accountDBID')
        playerVehicleId = self.__getVehicleIdByAccountID(playerDBID, vehiclesData)
        efficiency = {1: [],
         2: []}
        details = pData.get('details', dict())
        for vId, iInfo in details.iteritems():
            vInfo = vehiclesData.get(vId, dict())
            pInfo = playersData.get(vInfo.get('accountDBID', -1), dict())
            vehiclePlayerDBID = vInfo.get('accountDBID', None)
            if vehiclePlayerDBID == playerDBID:
                continue
            _, iInfo['vehicleName'], _, iInfo['tankIcon'], iInfo['balanceWeight'] = self.__getVehicleData(vInfo.get('typeCompDescr', None))
            iInfo['playerName'] = self.__getPlayerName(vehiclePlayerDBID, playersData)
            iInfo['vehicleId'] = vId
            iInfo['typeCompDescr'] = vInfo.get('typeCompDescr')
            iInfo['killed'] = bool(vInfo.get('deathReason', -1) != -1)
            team = pInfo.get('team', pData.get('team') % 2 + 1)
            iInfo['isAlly'] = team == playerTeam
            iInfo['isFake'] = False
            iInfo['damageDealtVals'] = makeHtmlString('html_templates:lobby/battle_results', 'tooltip_two_liner', {'line1': BigWorld.wg_getIntegralFormat(iInfo['damageDealt']),
             'line2': BigWorld.wg_getIntegralFormat(iInfo['pierced'])})
            iInfo['damageDealtNames'] = makeHtmlString('html_templates:lobby/battle_results', 'tooltip_two_liner', {'line1': i18n.makeString(BATTLE_RESULTS_STR.format('common/tooltip/damage/part1')),
             'line2': i18n.makeString(BATTLE_RESULTS_STR.format('common/tooltip/damage/part2'))})
            iInfo['damageAssisted'] = iInfo.get('damageAssistedTrack', 0) + iInfo.get('damageAssistedRadio', 0)
            iInfo['damageAssistedVals'] = makeHtmlString('html_templates:lobby/battle_results', 'tooltip_two_liner', {'line1': BigWorld.wg_getIntegralFormat(iInfo['damageAssistedRadio']),
             'line2': BigWorld.wg_getIntegralFormat(iInfo['damageAssistedTrack'])})
            iInfo['damageAssistedNames'] = makeHtmlString('html_templates:lobby/battle_results', 'tooltip_two_liner', {'line1': i18n.makeString(BATTLE_RESULTS_STR.format('common/tooltip/assist/part1')),
             'line2': i18n.makeString(BATTLE_RESULTS_STR.format('common/tooltip/assist/part2'))})
            destroyedTankmen = iInfo['crits'] >> 24 & 255
            destroyedDevices = iInfo['crits'] >> 12 & 4095
            criticalDevices = iInfo['crits'] & 4095
            critsCount = 0
            criticalDevicesList = []
            destroyedDevicesList = []
            destroyedTankmenList = []
            for shift in range(len(vehicles.VEHICLE_DEVICE_TYPE_NAMES)):
                if 1 << shift & criticalDevices:
                    critsCount += 1
                    criticalDevicesList.append(self.__makeTooltipModuleLabel(vehicles.VEHICLE_DEVICE_TYPE_NAMES[shift], 'Critical'))
                if 1 << shift & destroyedDevices:
                    critsCount += 1
                    destroyedDevicesList.append(self.__makeTooltipModuleLabel(vehicles.VEHICLE_DEVICE_TYPE_NAMES[shift], 'Destroyed'))

            for shift in range(len(vehicles.VEHICLE_TANKMAN_TYPE_NAMES)):
                if 1 << shift & destroyedTankmen:
                    critsCount += 1
                    destroyedTankmenList.append(self.__makeTooltipTankmenLabel(vehicles.VEHICLE_TANKMAN_TYPE_NAMES[shift]))

            iInfo['critsCount'] = BigWorld.wg_getIntegralFormat(critsCount)
            iInfo['criticalDevices'] = LINE_BRAKE_STR.join(criticalDevicesList)
            iInfo['destroyedDevices'] = LINE_BRAKE_STR.join(destroyedDevicesList)
            iInfo['destroyedTankmen'] = LINE_BRAKE_STR.join(destroyedTankmenList)
            if not iInfo['isAlly'] or iInfo['isAlly'] and vInfo.get('killerID', 0) == playerVehicleId:
                efficiency[team].append(iInfo)

        enemies = sorted(efficiency[playerTeam % 2 + 1], cmp=self.__vehiclesComparator)
        allies = sorted(efficiency[playerTeam], cmp=self.__vehiclesComparator)
        if len(allies) > 0:
            enemies.append({'playerName': EFFICIENCY_ALLIES_STR,
             'isFake': True})
        pData['details'] = enemies + allies
        return

    def __makeTooltipModuleLabel(self, key, suffix):
        return makeHtmlString('html_templates:lobby/battle_results', 'tooltip_crit_label', {'image': '{0}{1}'.format(key, suffix),
         'value': i18n.makeString('#item_types:{0}/name'.format(key))})

    def __makeTooltipTankmenLabel(self, key):
        return makeHtmlString('html_templates:lobby/battle_results', 'tooltip_crit_label', {'image': '{0}Destroyed'.format(key),
         'value': i18n.makeString('#item_types:tankman/roles/{0}'.format(key))})

    def __populateResultStrings(self, commonData, pData):
        winnerTeam = commonData.get('winnerTeam', 0)
        if not winnerTeam:
            status = 'tie'
        elif winnerTeam == pData.get('team'):
            status = 'win'
        else:
            status = 'lose'
        commonData['resultShortStr'] = status
        commonData['resultStr'] = RESULT_.format(status)
        reason = commonData.get('finishReason', 0)
        if reason == 1:
            commonData['finishReasonStr'] = FINISH_REASON.format(''.join([str(reason), str(status)]))
        else:
            commonData['finishReasonStr'] = FINISH_REASON.format(reason)

    def __populateTankSlot(self, commonData, pData, vehiclesData, playersData):
        commonData['playerNameStr'] = self.__getPlayerName(pData.get('accountDBID', None), playersData)
        commonData['vehicleName'], _, commonData['tankIcon'], _, _ = self.__getVehicleData(pData.get('typeCompDescr', None))
        killerID = pData.get('killerID', 0)
        deathReason = pData.get('deathReason', -1)
        if deathReason > -1:
            commonData['vehicleStateStr'] = i18n.makeString('#battle_results:common/vehicleState/dead{0}'.format(deathReason))
            if killerID:
                killerVehicle = vehiclesData.get(killerID, dict())
                killerPlayerId = killerVehicle.get('accountDBID', None)
                commonData['vehicleStateStr'] = '{0} ({1})'.format(commonData['vehicleStateStr'], self.__getPlayerName(killerPlayerId, playersData))
        else:
            commonData['vehicleStateStr'] = '#battle_results:common/vehicleState/alive'
        return

    def __populateArenaData(self, commonData, pData):
        arenaTypeID = commonData.get('arenaTypeID', 0)
        guiType = commonData.get('guiType', 0)
        arenaType = ArenaType.g_cache[arenaTypeID] if arenaTypeID > 0 else None
        if guiType == ARENA_GUI_TYPE.RANDOM:
            arenaGuiName = ARENA_TYPE.format(arenaType.gameplayName)
        else:
            arenaGuiName = ARENA_SPECIAL_TYPE.format(guiType)
        commonData['arenaStr'] = ARENA_NAME_PATTERN.format(i18n.makeString(arenaType.name), i18n.makeString(arenaGuiName))
        createTime = commonData.get('arenaCreateTime')
        createTime = time_utils.makeLocalServerTime(createTime)
        commonData['arenaCreateTimeStr'] = BigWorld.wg_getShortDateFormat(createTime) + ' ' + BigWorld.wg_getShortTimeFormat(createTime)
        commonData['arenaCreateTimeOnlyStr'] = BigWorld.wg_getShortTimeFormat(createTime)
        commonData['arenaIcon'] = ARENA_SCREEN_FILE.format(arenaType.geometryName)
        duration = commonData.get('duration', 0)
        minutes = int(duration / 60)
        seconds = int(duration % 60)
        commonData['duration'] = i18n.makeString(TIME_DURATION_STR, minutes, seconds)
        commonData['playerKilled'] = '-'
        if pData.get('killerID', 0):
            lifeTime = pData.get('lifeTime', 0)
            minutes = int(lifeTime / 60)
            seconds = int(lifeTime % 60)
            commonData['playerKilled'] = i18n.makeString(TIME_DURATION_STR, minutes, seconds)
        commonData['timeStats'] = []
        for key in TIME_STATS_KEYS:
            commonData['timeStats'].append({'label': i18n.makeString(TIME_STATS_KEY_BASE.format(key)),
             'value': commonData[key]})

        return

    def __makeTeamDamageStr(self, data):
        tkills = data.get('tkills', 0)
        tdamageDealt = data.get('tdamageDealt', 0)
        tDamageStr = '/'.join([str(tkills), str(tdamageDealt)])
        if tkills > 0 or tdamageDealt > 0:
            tDamageStr = self.__makeRedLabel(tDamageStr)
        else:
            tDamageStr = makeHtmlString('html_templates:lobby/battle_results', 'empty_stat_value', {'value': tDamageStr})
        return tDamageStr

    def __makeMileageStr(self, mileage):
        km = float(mileage) / 1000
        val = BigWorld.wg_getFractionalFormat(km) + i18n.makeString(MILEAGE_STR_KEY)
        if not mileage:
            val = makeHtmlString('html_templates:lobby/battle_results', 'empty_stat_value', {'value': val})
        return val

    def __populateTeamsData(self, pData, playersData, vehiclesData, battleType):
        squads = {1: {},
         2: {}}
        stat = {1: [],
         2: []}
        lastSquadId = 0
        squadManCount = 0
        playerSquadId = 0
        playerDBID = pData.get('accountDBID')
        for pId, pInfo in playersData.iteritems():
            row = None
            for vId, vInfo in vehiclesData.iteritems():
                if pId == vInfo.get('accountDBID'):
                    row = pInfo.copy()
                    row.update(vInfo)
                    row['vehicleId'] = vId
                    row['damageAssisted'] = row.get('damageAssistedTrack', 0) + row.get('damageAssistedRadio', 0)
                    row['statValues'] = self.__populateStatValues(row)
                    health = vInfo.get('health', 0)
                    percents = 0
                    if health > 0:
                        percents = math.ceil(health * 100 / float(health + vInfo.get('damageReceived', 0)))
                    row['healthPercents'] = percents
                    row['vehicleFullName'], row['vehicleName'], row['bigTankIcon'], row['tankIcon'], row['balanceWeight'] = self.__getVehicleData(vInfo.get('typeCompDescr', None))
                    row['realKills'] = vInfo.get('kills', 0) - vInfo.get('tkills', 0)
                    achievements = tuple(row.get('achievements', []))
                    row['medalsCount'] = len(achievements)
                    achievementsList = []
                    for achievementId in achievements:
                        medalDict = getMedalDict(RECORD_NAMES[achievementId], 0)
                        medalDict['unic'] = True
                        medalDict['isEpic'] = medalDict['type'] in ACHIEVEMENTS_WITH_RIBBON
                        achievementsList.append(medalDict)

                    achievementsList.sort(key=lambda k: k['isEpic'], reverse=True)
                    row['achievements'] = achievementsList
                    killerID = row.get('killerID', 0)
                    deathReason = row.get('deathReason', -1)
                    if deathReason > -1:
                        row['vehicleStateStr'] = i18n.makeString('#battle_results:common/vehicleState/dead{0}'.format(deathReason))
                        if killerID:
                            killerVehicle = vehiclesData.get(killerID, dict())
                            killerPlayerId = killerVehicle.get('accountDBID', None)
                            row['vehicleStateStr'] = '{0} ({1})'.format(row['vehicleStateStr'], self.__getPlayerName(killerPlayerId, playersData))
                    else:
                        row['vehicleStateStr'] = '#battle_results:common/vehicleState/alive'
                    break

            if row is None:
                row = pInfo.copy()
            row['playerId'] = pId
            row['userName'] = pInfo.get('name')
            row['playerClan'] = self.__getPlayerClan(pId, playersData)
            row['playerName'] = self.__getPlayerName(pId, playersData)
            row['isIGR'] = pInfo.get('igrType') != IGR_TYPE.NONE
            row['playerInfo'] = {}
            row['isSelf'] = playerDBID == pId
            if playerDBID == pId:
                playerSquadId = row.get('prebattleID', 0)
            team = row['team']
            prebattleID = row.get('prebattleID', 0)
            if battleType == ARENA_BONUS_TYPE.REGULAR and prebattleID:
                if not lastSquadId or lastSquadId != prebattleID:
                    squadManCount = 1
                    lastSquadId = prebattleID
                else:
                    squadManCount += 1
                if prebattleID not in squads[team].keys():
                    squads[team][prebattleID] = 1
                else:
                    squads[team][prebattleID] += 1
            stat[team].append(row)

        if battleType == ARENA_BONUS_TYPE.REGULAR:
            squadsSorted = IS_DEVELOPMENT and not squadManCount == len(playersData) and dict()
            squadsSorted[1] = sorted(squads[1].iteritems(), cmp=lambda x, y: cmp(x[0], y[0]))
            squadsSorted[2] = sorted(squads[2].iteritems(), cmp=lambda x, y: cmp(x[0], y[0]))
            squads[1] = [ id for id, num in squadsSorted[1] if 1 < num < 4 ]
            squads[2] = [ id for id, num in squadsSorted[2] if 1 < num < 4 ]
        for team in (1, 2):
            data = sorted(stat[team], cmp=self.__vehiclesComparator)
            sortIdx = len(data)
            for item in data:
                item['vehicleSort'] = sortIdx
                sortIdx -= 1
                if battleType == ARENA_BONUS_TYPE.REGULAR:
                    item['isOwnSquad'] = IS_DEVELOPMENT and not squadManCount == len(playersData) and (playerSquadId == item.get('prebattleID') if playerSquadId != 0 else False)
                    item['squadID'] = squads[team].index(item.get('prebattleID')) + 1 if item.get('prebattleID') in squads[team] else 0
                else:
                    item['squadID'] = 0
                    item['isOwnSquad'] = False

        return (stat[pData.get('team')], stat[pData.get('team') % 2 + 1])

    def __calculateBaseXp(self, pData):
        aogasF10 = float(pData.get('aogasFactor10', 10))
        if not aogasF10:
            return 0
        isPrem = pData.get('isPremium', False)
        xp = float(pData.get('xp', 0))
        dailyF10 = float(pData.get('dailyXPFactor10', 10))
        premF10 = float(pData.get('premiumXPFactor10', 10))
        igrF10 = float(pData.get('igrXPFactor10', 10))
        eventXp = float(pData.get('eventXP', 0))
        baseXp = math.ceil((int(100.0 * xp / aogasF10) - 10.0 * eventXp) / dailyF10)
        if isPrem:
            baseXp = math.ceil(baseXp * 10.0 / premF10)
        if igrF10:
            baseXp = math.ceil(baseXp * 10.0 / igrF10)
        return baseXp

    def __calculateBaseXpPenalty(self, pData):
        aogasF10 = float(pData.get('aogasFactor10', 10))
        if not aogasF10:
            return 0
        isPrem = pData.get('isPremium', False)
        xpPenalty = float(pData.get('xpPenalty', 0))
        dailyF10 = float(pData.get('dailyXPFactor10', 10))
        premF10 = float(pData.get('premiumXPFactor10', 10))
        igrF10 = float(pData.get('igrXPFactor10', 10))
        xpPenalty = math.ceil(int(100.0 * xpPenalty / aogasF10) / dailyF10)
        if isPrem:
            xpPenalty = math.ceil(xpPenalty * 10.0 / premF10)
        if igrF10:
            xpPenalty = math.ceil(xpPenalty * 10.0 / igrF10)
        return xpPenalty

    def __calculateTotalFreeXp(self, pData, baseFreeXp, usePremFactor = False):
        if not baseFreeXp:
            return 0
        isPrem = pData.get('isPremium', False)
        freeXP = float(pData.get('freeXP', 0))
        if isPrem != usePremFactor:
            aogasF10 = float(pData.get('aogasFactor10', 10))
            dailyF10 = float(pData.get('dailyXPFactor10', 10))
            igrF10 = float(pData.get('igrXPFactor10', 10))
            premF10 = float(pData.get('premiumXPFactor10', 10))
            eventFreeXP = float(pData.get('eventFreeXP', 0))
            premMultyplier = premF10 if usePremFactor else 10.0
            freeXP = int((int(int(int(baseFreeXp * (igrF10 / 10.0)) * (premMultyplier / 10.0)) * (dailyF10 / 10.0)) + eventFreeXP) * aogasF10 / 10.0)
        return freeXP

    def __calculateTotalXp(self, pData, baseXp, usePremFactor = False):
        if not baseXp:
            return 0
        isPrem = pData.get('isPremium', False)
        XP = float(pData.get('xp', 0))
        if isPrem != usePremFactor:
            aogasF10 = float(pData.get('aogasFactor10', 10))
            dailyF10 = float(pData.get('dailyXPFactor10', 10))
            igrF10 = float(pData.get('igrXPFactor10', 10))
            premF10 = float(pData.get('premiumXPFactor10', 10))
            eventXP = float(pData.get('eventXP', 0))
            premMultyplier = premF10 if usePremFactor else 10.0
            XP = int((int(int(int(baseXp * (igrF10 / 10.0)) * (premMultyplier / 10.0)) * (dailyF10 / 10.0)) + eventXP) * aogasF10 / 10.0)
        return XP

    def __calculateBaseCredits(self, pData):
        aogasF10 = float(pData.get('aogasFactor10', 10))
        if not aogasF10:
            return 0
        isPrem = pData.get('isPremium', False)
        credits = float(pData.get('credits', 0))
        premF10 = float(pData.get('premiumCreditsFactor10', 10))
        eventCredits = float(pData.get('eventCredits', 0))
        baseCredits = math.ceil(10.0 * credits / aogasF10) - eventCredits
        if isPrem:
            baseCredits = math.ceil(baseCredits * 10.0 / premF10)
        return baseCredits

    def __calculateBaseCreditsPenalty(self, pData):
        isPrem = pData.get('isPremium', False)
        creditsPenalty = float(pData.get('creditsPenalty', 0) + pData.get('creditsContributionOut', 0))
        premF10 = float(pData.get('premiumCreditsFactor10', 10))
        if isPrem:
            creditsPenalty = math.ceil(creditsPenalty * 10.0 / premF10)
        return creditsPenalty

    def __calculateBaseCreditsContribution(self, pData):
        isPrem = pData.get('isPremium', False)
        creditsContribution = float(pData.get('creditsContributionIn', 0))
        premF10 = float(pData.get('premiumCreditsFactor10', 10))
        if isPrem:
            creditsContribution = math.ceil(creditsContribution * 10.0 / premF10)
        return creditsContribution

    def __calculateTotalCredits(self, pData, baseCredits, usePremFactor = False):
        if not baseCredits:
            return 0
        isPrem = pData.get('isPremium', False)
        credits = float(pData.get('credits', 0))
        if isPrem != usePremFactor:
            aogasF10 = float(pData.get('aogasFactor10', 10))
            premF10 = float(pData.get('premiumXPFactor10', 10))
            eventCredits = float(pData.get('eventCredits', 0))
            premMultyplier = premF10 if usePremFactor else 10.0
            credits = int((int(int(baseCredits * (premMultyplier / 10.0))) + eventCredits) * aogasF10 / 10.0)
        return credits

    def selectVehicle(self, inventoryId):
        g_currentVehicle.selectVehicle(inventoryId)
        return g_currentVehicle.invID == inventoryId

    def onUsersRosterUpdated(self, action, user):
        for arenaUniqueId in self.__openedWindowsArenaID:
            wnd = self.getBattleResultsWindow(long(arenaUniqueId))
            if wnd is not None:
                wnd.updatePlayerInfo(user.__dict__)

        return

    def __parseQuestsProgress(self, questsProgress):

        def sortFunc(a, b):
            if a.isCompleted() and not b.isCompleted():
                return -1
            if not a.isCompleted() and b.isCompleted():
                return 1
            if a.isCompleted() and b.isCompleted():
                if a.isStrategic():
                    return -1
                if b.isStrategic():
                    return 1
                aPrevProg = questsProgress[a.getID()][1]
                bPrevProg = questsProgress[b.getID()][1]
                res = a.getBonusCount() - aPrevProg.get('bonusCount', 0) - (b.getBonusCount() - bPrevProg.get('bonusCount', 0))
                if not res:
                    return res
                if a.isSubtask():
                    return 1
                if b.isSubtask():
                    return -1
            return 0

        from gui.Scaleform.daapi.view.lobby.quests import quest_helpers
        quests = g_questsCache.getQuests()
        result = []
        for qID, qProgress in questsProgress.iteritems():
            if qID in quests:
                pGroupBy, pPrev, pCur = qProgress
                progress = {pGroupBy: pCur}
                if max(pCur.itervalues()) == 0:
                    continue
                result.append(event_items.Quest(qID, quests[qID]._data, progress))

        return map(lambda q: quest_helpers.packQuest(q, quests, noProgressTooltip=True), sorted(result, sortFunc))

    @async
    @process
    def __getCommonData(self, callback):
        results = None
        if self.arenaUniqueID:
            results = yield StatsRequester().getBattleResults(int(self.arenaUniqueID))
        elif IS_DEVELOPMENT:
            results = self.testData
            yield lambda callback: callback(None)
        LOG_DEBUG('aaaaaaaaa', results)
        if results:
            from BattleReplay import g_replayCtrl
            g_replayCtrl.onExtendedBattleResultsReceived(results)
            personalData = results.get('personal', dict()).copy()
            playersData = results.get('players', dict()).copy()
            vehiclesData = results.get('vehicles', dict()).copy()
            commonData = results.get('common', dict()).copy()
            statsSorting = AccountSettings.getSettings('statsSorting')
            commonData['iconType'] = statsSorting.get('iconType')
            commonData['sortDirection'] = statsSorting.get('sortDirection')
            self.__populateResultStrings(commonData, personalData)
            self.__populatePersonalMedals(personalData)
            self.__populateArenaData(commonData, personalData)
            personalData['damageAssisted'] = personalData.get('damageAssistedTrack', 0) + personalData.get('damageAssistedRadio', 0)
            personalData['statValues'] = self.__populateStatValues(personalData, True)
            self.__populateAccounting(commonData, personalData)
            self.__populateTankSlot(commonData, personalData, vehiclesData, playersData)
            self.__populateEfficiency(personalData, vehiclesData, playersData)
            team1, team2 = self.__populateTeamsData(personalData, playersData, vehiclesData, commonData.get('bonusType', 0))
            resultingVehicles = []
            dailyXPFactor = 2
            if False:
                try:
                    multipliedXPVehs = yield StatsRequester().getMultipliedXPVehicles()
                    vehicleTypeLocks = yield StatsRequester().getVehicleTypeLocks()
                    globalVehicleLocks = yield StatsRequester().getGlobalVehicleLocks()
                    dailyXPFactor = StatsRequester().getDailyXPFactor() or (yield 2)
                    vehicles = yield Requester('vehicle').getFromInventory()

                    def sorting(first, second):
                        if first.isFavorite and not second.isFavorite:
                            return -1
                        if not first.isFavorite and second.isFavorite:
                            return 1
                        return first.__cmp__(second)

                    vehicles.sort(sorting)
                    vehiclesFiltered = [ vehicle for vehicle in vehicles if vehicle.descriptor.type.compactDescr not in multipliedXPVehs and vehicle.repairCost == 0 and vehicle.lock == 0 and None not in vehicle.crew and vehicle.crew != [] and not vehicleTypeLocks.get(vehicle.descriptor.type.compactDescr, {}).get(1, False) and not globalVehicleLocks.get(1, False) ]
                    for vehicle in vehiclesFiltered:
                        try:
                            vehicleInfo = dict()
                            vehicleInfo['inventoryId'] = vehicle.inventoryId
                            vehicleInfo['label'] = vehicle.name
                            vehicleInfo['selected'] = g_currentVehicle.invID == vehicle.inventoryId
                        except Exception:
                            LOG_ERROR("Exception while '%s' vehicle processing" % vehicle.descriptor.type.name)
                            LOG_CURRENT_EXCEPTION()
                            continue

                        resultingVehicles.append(vehicleInfo)

                except Exception:
                    LOG_CURRENT_EXCEPTION()

            callback({'personal': personalData,
             'common': commonData,
             'team1': team1,
             'team2': team2,
             'vehicles': resultingVehicles,
             'dailyXPFactor': dailyXPFactor,
             'quests': self.__parseQuestsProgress(personalData.get('questsProgress', {}))})
        else:
            callback(None)
        return

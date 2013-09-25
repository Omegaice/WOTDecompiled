# Embedded file name: scripts/client/messenger/formatters/service_channel.py
import types
from adisp import async, process
from debug_utils import LOG_ERROR, LOG_WARNING, LOG_CURRENT_EXCEPTION, LOG_DEBUG
import account_helpers
import ArenaType
import BigWorld
from messenger.formatters import TimeFormatter
from messenger.m_constants import MESSENGER_I18N_FILE
import offers
from constants import INVOICE_ASSET, AUTO_MAINTENANCE_TYPE, AUTO_MAINTENANCE_RESULT, PREBATTLE_TYPE, FINISH_REASON, KICK_REASON_NAMES, KICK_REASON
import dossiers
from gui.prb_control.formatters import getPrebattleFullDescription
from gui.shared.utils.gui_items import formatPrice
from helpers import i18n, html, getClientLanguage, getLocalizedData
from helpers import time_utils
from items import getTypeInfoByIndex, getTypeInfoByName, tankmen
from items import vehicles as vehicles_core
from account_helpers import rare_achievements
import enumerations
from messenger import g_settings

class ServiceChannelFormatter(object):

    def format(self, data, *args):
        return None

    def notify(self):
        return False

    def isAsync(self):
        return False


class ServerRebootFormatter(ServiceChannelFormatter):

    def format(self, message, *args):
        if message.data:
            local_dt = time_utils.utcToLocalDatetime(message.data)
            return g_settings.msgTemplates.format('serverReboot', ctx={'date': local_dt.strftime('%c')})
        else:
            return None
            return None


class ServerRebootCancelledFormatter(ServiceChannelFormatter):

    def format(self, message, *args):
        if message.data:
            local_dt = time_utils.utcToLocalDatetime(message.data)
            return g_settings.msgTemplates.format('serverRebootCancelled', ctx={'date': local_dt.strftime('%c')})
        else:
            return None
            return None


class BattleResultsFormatter(ServiceChannelFormatter):
    __battleResultKeys = {-1: 'battleDefeatResult',
     0: 'battleDrawGameResult',
     1: 'battleVictoryResult'}
    __goldTemplateKey = 'battleResultGold'
    __questsTemplateKey = 'battleQuests'
    __i18n_penalty = i18n.makeString('#%s:serviceChannelMessages/battleResults/penaltyForDamageAllies' % MESSENGER_I18N_FILE)
    __i18n_contribution = i18n.makeString('#%s:serviceChannelMessages/battleResults/contributionForDamageAllies' % MESSENGER_I18N_FILE)

    def notify(self):
        return True

    def format(self, message, *args):
        battleResult = message.data
        arenaTypeID = battleResult.get('arenaTypeID', 0)
        arenaType = ArenaType.g_cache[arenaTypeID] if arenaTypeID > 0 else None
        arenaCreateTime = battleResult.get('arenaCreateTime', None)
        if arenaCreateTime and arenaType:
            ctx = {'arenaName': i18n.makeString(arenaType.name),
             'createdAt': TimeFormatter.getLongDatetimeFormat(arenaCreateTime),
             'vehicleName': 'N/A',
             'xp': '0',
             'credits': '0'}
            vehicleCompDesc = battleResult.get('vehTypeCompDescr', None)
            if vehicleCompDesc:
                vt = vehicles_core.getVehicleType(vehicleCompDesc)
                ctx['vehicleName'] = vt.userString
            xp = battleResult.get('xp')
            if xp:
                ctx['xp'] = BigWorld.wg_getIntegralFormat(xp)
            ctx['xpEx'] = self.__makeXpExString(xp, battleResult)
            ctx['gold'] = self.__makeGoldString(battleResult.get('gold', 0))
            accCredits = battleResult.get('credits')
            if accCredits:
                ctx['credits'] = BigWorld.wg_getIntegralFormat(accCredits)
            ctx['creditsEx'] = self.__makeCreditsExString(accCredits, battleResult)
            ctx['achieves'] = self.__makeAchievementsString(battleResult)
            ctx['lock'] = self.__makeVehicleLockString(ctx['vehicleName'], battleResult)
            ctx['quests'] = self.__makeQuestsAchievesString(message)
            paramData = {'key': 'arenaUniqueID',
             'value': str(int(battleResult.get('arenaUniqueID', 0)))}
            return g_settings.msgTemplates.format(self.__battleResultKeys[battleResult['isWinner']], ctx=ctx, data=paramData)
        else:
            return
            return

    def __makeQuestsAchieve(self, key, **kwargs):
        return g_settings.htmlTemplates.format(key, kwargs)

    def __makeQuestsAchievesString(self, message):
        battleResult = message.data
        result = []
        slots = battleResult.get('slots', 0)
        if slots:
            result.append(self.__makeQuestsAchieve('battleQuestsSlots', slots=BigWorld.wg_getIntegralFormat(slots)))
        berths = battleResult.get('berths', 0)
        if berths:
            result.append(self.__makeQuestsAchieve('battleQuestsBerths', berths=BigWorld.wg_getIntegralFormat(berths)))
        premium = battleResult.get('premium', 0)
        if premium:
            result.append(self.__makeQuestsAchieve('battleQuestsPremium', days=premium))
        items = battleResult.get('items', {})
        itemsNames = []
        for intCD, count in items.iteritems():
            itemDescr = vehicles_core.getDictDescr(intCD)
            itemsNames.append(i18n.makeString('#messenger:serviceChannelMessages/battleResults/quests/items/name', name=itemDescr['userString'], count=BigWorld.wg_getIntegralFormat(count)))

        if len(itemsNames):
            result.append(self.__makeQuestsAchieve('battleQuestsItems', names=', '.join(itemsNames)))
        vehicles = battleResult.get('vehicles', {})
        if vehicles is not None and len(vehicles) > 0:
            exclude = InvoiceReceivedFormatter._makeComptnItemDict(battleResult).get('ex_vehicles', [])
            msg = InvoiceReceivedFormatter._getVehiclesString(vehicles, exclude=exclude, htmlTplPostfix='QuestsReceived')
            if len(msg):
                result.append(msg)
        compensation = battleResult.get('compensation', [])
        if len(compensation):
            msg = InvoiceReceivedFormatter._getComptnString(compensation, htmlTplPostfix='QuestsReceived')
            if len(msg):
                result.append('<br/>' + msg)
        if len(result):
            return g_settings.htmlTemplates.format(self.__questsTemplateKey, {'achieves': ''.join(result)})
        else:
            return ''

    def __makeVehicleLockString(self, vehicle, battleResult):
        expireTime = battleResult.get('vehTypeUnlockTime', 0)
        if not expireTime:
            return ''
        return g_settings.htmlTemplates.format('battleResultLocks', ctx={'vehicleName': vehicle,
         'expireTime': TimeFormatter.getLongDatetimeFormat(expireTime)})

    def __makeXpExString(self, xp, battleResult):
        if not xp:
            return ''
        exStrings = []
        penalty = battleResult.get('xpPenalty', 0)
        if penalty > 0:
            exStrings.append(self.__i18n_penalty % BigWorld.wg_getIntegralFormat(penalty))
        if battleResult['isWinner'] == 1:
            xpFactor = battleResult.get('dailyXPFactor', 1)
            if xpFactor > 1:
                exStrings.append(i18n.makeString('#%s:serviceChannelMessages/battleResults/doubleXpFactor' % MESSENGER_I18N_FILE) % xpFactor)
        if len(exStrings):
            return ' ({0:>s})'.format('; '.join(exStrings))
        return ''

    def __makeCreditsExString(self, accCredits, battleResult):
        if not accCredits:
            return ''
        exStrings = []
        penalty = sum([battleResult.get('creditsPenalty', 0), battleResult.get('creditsContributionOut', 0)])
        if penalty > 0:
            exStrings.append(self.__i18n_penalty % BigWorld.wg_getIntegralFormat(penalty))
        contribution = battleResult.get('creditsContributionIn', 0)
        if contribution > 0:
            exStrings.append(self.__i18n_contribution % BigWorld.wg_getIntegralFormat(contribution))
        if len(exStrings):
            return ' ({0:>s})'.format('; '.join(exStrings))
        return ''

    def __makeGoldString(self, gold):
        if not gold:
            return ''
        return g_settings.htmlTemplates.format(self.__goldTemplateKey, {'gold': BigWorld.wg_getGoldFormat(gold)})

    def __makeAchievementsString(self, battleResult):
        from dossiers.achievements import ACHIEVEMENTS, ACHIEVEMENT_SECTIONS_INDICES

        def sortFunction(a, b):
            aKey = dossiers.RECORD_NAMES[a[0]]
            bKey = dossiers.RECORD_NAMES[b[0]]
            aOrderVal = ACHIEVEMENT_SECTIONS_INDICES[ACHIEVEMENTS.get(aKey, {}).get('section', 'battle')]
            bOrderVal = ACHIEVEMENT_SECTIONS_INDICES[ACHIEVEMENTS.get(bKey, {}).get('section', 'battle')]
            return aOrderVal - bOrderVal

        def filterFunc(item):
            if dossiers.RECORD_NAMES[item[0]] == 'maxXP':
                return False
            return True

        records = battleResult.get('popUpRecords')
        records = filter(filterFunc, records)
        if records is None or not len(records):
            return ''
        else:
            achieveList = []
            for recordIdx, value in sorted(records, cmp=sortFunction):
                achieveKey = dossiers.RECORD_NAMES[recordIdx]
                achieveI18n = i18n.makeString('#achievements:%s' % achieveKey)
                rule = AchievementsFormatRulesDict.get(achieveKey)
                if rule:
                    achieveList.append(rule(achieveI18n, value))
                else:
                    achieveList.append(achieveI18n)

            return g_settings.htmlTemplates.format('battleResultAchieves', {'achieves': ', '.join(achieveList)})


AchievementsFormatRules = enumerations.Enumeration('Achievement format rules', [('showRank', lambda key, count: key % i18n.makeString('#achievements:achievement/rank%d' % int(count))), ('showMaster', lambda key, count: key % {'name': i18n.makeString('#achievements:achievement/master%d' % int(count))})], instance=enumerations.CallabbleEnumItem)
AchievementsFormatRulesDict = {'medalKay': AchievementsFormatRules.showRank,
 'medalCarius': AchievementsFormatRules.showRank,
 'medalKnispel': AchievementsFormatRules.showRank,
 'medalPoppel': AchievementsFormatRules.showRank,
 'medalAbrams': AchievementsFormatRules.showRank,
 'medalLeClerc': AchievementsFormatRules.showRank,
 'medalLavrinenko': AchievementsFormatRules.showRank,
 'medalEkins': AchievementsFormatRules.showRank,
 'markOfMastery': AchievementsFormatRules.showMaster}

class AutoMaintenanceFormatter(ServiceChannelFormatter):
    __messages = {AUTO_MAINTENANCE_RESULT.NOT_ENOUGH_ASSETS: {AUTO_MAINTENANCE_TYPE.REPAIR: '#messenger:serviceChannelMessages/autoRepairError',
                                                 AUTO_MAINTENANCE_TYPE.LOAD_AMMO: '#messenger:serviceChannelMessages/autoLoadError',
                                                 AUTO_MAINTENANCE_TYPE.EQUIP: '#messenger:serviceChannelMessages/autoEquipError'},
     AUTO_MAINTENANCE_RESULT.OK: {AUTO_MAINTENANCE_TYPE.REPAIR: '#messenger:serviceChannelMessages/autoRepairSuccess',
                                  AUTO_MAINTENANCE_TYPE.LOAD_AMMO: '#messenger:serviceChannelMessages/autoLoadSuccess',
                                  AUTO_MAINTENANCE_TYPE.EQUIP: '#messenger:serviceChannelMessages/autoEquipSuccess'},
     AUTO_MAINTENANCE_RESULT.NOT_PERFORMED: {AUTO_MAINTENANCE_TYPE.REPAIR: '#messenger:serviceChannelMessages/autoRepairSkipped',
                                             AUTO_MAINTENANCE_TYPE.LOAD_AMMO: '#messenger:serviceChannelMessages/autoLoadSkipped',
                                             AUTO_MAINTENANCE_TYPE.EQUIP: '#messenger:serviceChannelMessages/autoEquipSkipped'},
     AUTO_MAINTENANCE_RESULT.DISABLED_OPTION: {AUTO_MAINTENANCE_TYPE.REPAIR: '#messenger:serviceChannelMessages/autoRepairDisabledOption',
                                               AUTO_MAINTENANCE_TYPE.LOAD_AMMO: '#messenger:serviceChannelMessages/autoLoadDisabledOption',
                                               AUTO_MAINTENANCE_TYPE.EQUIP: '#messenger:serviceChannelMessages/autoEquipDisabledOption'}}

    def notify(self):
        return True

    def format(self, message, *args):
        vehicleCompDescr = message.data.get('vehTypeCD', None)
        result = message.data.get('result', None)
        typeID = message.data.get('typeID', None)
        cost = message.data.get('cost', (0, 0))
        if vehicleCompDescr is not None and result is not None and typeID is not None:
            vt = vehicles_core.getVehicleType(vehicleCompDescr)
            if typeID == AUTO_MAINTENANCE_TYPE.REPAIR:
                formatMsgType = 'RepairSysMessage'
            else:
                formatMsgType = 'PurchaseForCreditsSysMessage' if cost[1] == 0 else 'PurchaseForGoldSysMessage'
            msg = i18n.makeString(self.__messages[result][typeID]) % vt.userString
            if result == AUTO_MAINTENANCE_RESULT.OK:
                templateName = formatMsgType
            elif result == AUTO_MAINTENANCE_RESULT.NOT_ENOUGH_ASSETS:
                templateName = 'ErrorSysMessage'
            else:
                templateName = 'WarningSysMessage'
            if result == AUTO_MAINTENANCE_RESULT.OK:
                msg += formatPrice((abs(cost[0]), abs(cost[1])))
            return g_settings.msgTemplates.format(templateName, {'text': msg})
        else:
            return
            return


class AchievementFormatter(ServiceChannelFormatter):

    @async
    def __getRareTitle(self, rareID, callback):
        rare_achievements.getRareAchievementText(getClientLanguage(), rareID, lambda rID, text: callback(text.get('title')))

    def notify(self):
        return True

    def isAsync(self):
        return True

    @async
    @process
    def format(self, message, callback):
        yield lambda callback: callback(True)
        achievesList = list()
        achieves = message.data.get('popUpRecords')
        if achieves is not None:
            achievesList.extend([ i18n.makeString('#achievements:%s' % name) for name in achieves ])
        rares = message.data.get('rareAchievements')
        if rares is not None:
            unknownAchieves = 0
            for rareID in rares:
                if rareID > 0:
                    title = yield self.__getRareTitle(rareID)
                    if title is None:
                        unknownAchieves += 1
                    else:
                        achievesList.append(title)

            if unknownAchieves:
                achievesList.append(i18n.makeString('#system_messages:%s/title' % ('actionAchievements' if unknownAchieves > 1 else 'actionAchievement')))
        if not len(achievesList):
            callback(None)
            return
        else:
            callback(g_settings.msgTemplates.format('achievementReceived', {'achieves': ', '.join(achievesList)}))
            return


class GoldReceivedFormatter(ServiceChannelFormatter):

    def format(self, message, *args):
        data = message.data
        gold = data.get('gold', None)
        transactionTime = data.get('date', None)
        if gold and transactionTime:
            return g_settings.msgTemplates.format('goldReceived', {'date': TimeFormatter.getLongDatetimeFormat(transactionTime),
             'gold': BigWorld.wg_getGoldFormat(account_helpers.convertGold(gold))})
        else:
            return
            return


class GiftReceivedFormatter(ServiceChannelFormatter):
    __handlers = {'money': ('_GiftReceivedFormatter__formatMoneyGiftMsg', {1: 'creditsReceivedAsGift',
                2: 'goldReceivedAsGift',
                3: 'creditsAndGoldReceivedAsGift'}),
     'xp': ('_GiftReceivedFormatter__formatXPGiftMsg', 'xpReceivedAsGift'),
     'premium': ('_GiftReceivedFormatter__formatPremiumGiftMsg', 'premiumReceivedAsGift'),
     'item': ('_GiftReceivedFormatter__formatItemGiftMsg', 'itemReceivedAsGift'),
     'vehicle': ('_GiftReceivedFormatter__formatVehicleGiftMsg', 'vehicleReceivedAsGift')}

    def format(self, message, *args):
        data = message.data
        giftType = data.get('type')
        if giftType is not None:
            handlerName, templateKey = self.__handlers.get(giftType, (None, None))
            if handlerName is not None:
                return getattr(self, handlerName)(templateKey, data)
        return

    def __formatMoneyGiftMsg(self, keys, data):
        accCredits = data.get('credits', 0)
        gold = data.get('gold', 0)
        result = None
        ctx = {}
        idx = 0
        if accCredits > 0:
            idx |= 1
            ctx['credits'] = BigWorld.wg_getIntegralFormat(accCredits)
        if gold > 0:
            idx |= 2
            ctx['gold'] = BigWorld.wg_getGoldFormat(gold)
        if idx in keys:
            result = g_settings.msgTemplates.format(keys[idx], ctx)
        return result

    def __formatXPGiftMsg(self, key, data):
        xp = data.get('amount', 0)
        result = None
        if xp > 0:
            result = g_settings.msgTemplates.format(key, ctx={'freeXP': BigWorld.wg_getIntegralFormat(xp)})
        return result

    def __formatPremiumGiftMsg(self, templateKey, data):
        days = data.get('amount', 0)
        result = None
        if days > 0:
            result = g_settings.msgTemplates.format(templateKey, ctx={'days': days})
        return result

    def __formatItemGiftMsg(self, templateKey, data):
        amount = data.get('amount', 0)
        result = None
        itemTypeIdx = data.get('itemTypeIdx')
        itemCompactDesc = data.get('itemCD')
        if amount > 0 and itemTypeIdx is not None and itemCompactDesc is not None:
            result = g_settings.msgTemplates.format(templateKey, ctx={'typeName': getTypeInfoByIndex(itemTypeIdx)['userString'],
             'itemName': vehicles_core.getDictDescr(itemCompactDesc)['userString'],
             'amount': amount})
        return result

    def __formatVehicleGiftMsg(self, templateKey, data):
        vCompDesc = data.get('typeCD', None)
        result = None
        if vCompDesc is not None:
            result = g_settings.msgTemplates.format(templateKey, ctx={'vehicleName': vehicles_core.getVehicleType(vCompDesc).userString})
        return result


class InvoiceReceivedFormatter(ServiceChannelFormatter):
    __assetHandlers = {INVOICE_ASSET.GOLD: '_InvoiceReceivedFormatter__formatAmount',
     INVOICE_ASSET.CREDITS: '_InvoiceReceivedFormatter__formatAmount',
     INVOICE_ASSET.PREMIUM: '_InvoiceReceivedFormatter__formatAmount',
     INVOICE_ASSET.FREE_XP: '_InvoiceReceivedFormatter__formatAmount',
     INVOICE_ASSET.DATA: '_InvoiceReceivedFormatter__formatData'}
    __operationTemplateKeys = {INVOICE_ASSET.GOLD: 'goldAccruedInvoiceReceived',
     INVOICE_ASSET.CREDITS: 'creditsAccruedInvoiceReceived',
     INVOICE_ASSET.PREMIUM: 'premiumAccruedInvoiceReceived',
     INVOICE_ASSET.FREE_XP: 'freeXpAccruedInvoiceReceived',
     INVOICE_ASSET.GOLD | 16: 'goldDebitedInvoiceReceived',
     INVOICE_ASSET.CREDITS | 16: 'creditsDebitedInvoiceReceived',
     INVOICE_ASSET.PREMIUM | 16: 'premiumDebitedInvoiceReceived',
     INVOICE_ASSET.FREE_XP | 16: 'freeXpDebitedInvoiceReceived'}
    __messageTemplateKeys = {INVOICE_ASSET.GOLD: 'financialInvoiceReceived',
     INVOICE_ASSET.CREDITS: 'financialInvoiceReceived',
     INVOICE_ASSET.PREMIUM: 'premiumInvoiceReceived',
     INVOICE_ASSET.FREE_XP: 'freeXpInvoiceReceived',
     INVOICE_ASSET.DATA: 'dataInvoiceReceived'}
    __i18nPiecesString = i18n.makeString('#{0:>s}:serviceChannelMessages/invoiceReceived/pieces'.format(MESSENGER_I18N_FILE))
    __i18nCrewLvlString = i18n.makeString('#{0:>s}:serviceChannelMessages/invoiceReceived/crewLvl'.format(MESSENGER_I18N_FILE))

    def __getOperationTimeString(self, data):
        operationTime = data.get('at', None)
        if operationTime:
            fDatetime = TimeFormatter.getLongDatetimeFormat(time_utils.makeLocalServerTime(operationTime))
        else:
            fDatetime = 'N/A'
        return fDatetime

    def __getFinOperationString(self, assetType, amount):
        templateKey = 0 if amount > 0 else 16
        templateKey |= assetType
        ctx = {}
        if assetType == INVOICE_ASSET.GOLD:
            ctx['amount'] = BigWorld.wg_getGoldFormat(abs(amount))
        else:
            ctx['amount'] = BigWorld.wg_getIntegralFormat(abs(amount))
        return g_settings.htmlTemplates.format(self.__operationTemplateKeys[templateKey], ctx=ctx)

    def __getItemsString(self, items):
        accrued = []
        debited = []
        for itemCompactDescr, count in items.iteritems():
            if count:
                try:
                    item = vehicles_core.getDictDescr(itemCompactDescr)
                    itemString = '{0:>s} "{1:>s}" - {2:d} {3:>s}'.format(getTypeInfoByName(item['itemTypeName'])['userString'], item['userString'], abs(count), self.__i18nPiecesString)
                    if count > 0:
                        accrued.append(itemString)
                    else:
                        debited.append(itemString)
                except:
                    LOG_ERROR('itemCompactDescr can not parse ', itemCompactDescr)
                    LOG_CURRENT_EXCEPTION()

        result = ''
        if len(accrued):
            result = g_settings.htmlTemplates.format('itemsAccruedInvoiceReceived', ctx={'items': ', '.join(accrued)})
        if len(debited):
            if len(result):
                result += '<br/>'
            result += g_settings.htmlTemplates.format('itemsDebitedInvoiceReceived', ctx={'items': ', '.join(debited)})
        return result

    @classmethod
    def _getVehicleNames(cls, vehicles, exclude = None, validateNegative = True, showCrewLvl = True):
        addVehNames = []
        removeVehNames = []
        if exclude is None:
            exclude = []
        vehGetter = getattr(vehicles, 'get', None)
        for vehCompDescr in vehicles:
            if vehCompDescr is not None:
                isNegative = False
                if type(vehCompDescr) is types.IntType:
                    isNegative = vehCompDescr < 0
                    vehCompDescr = abs(vehCompDescr)
                if vehCompDescr in exclude:
                    continue
                crewLvl = 50
                if vehGetter is not None and callable(vehGetter) and showCrewLvl:
                    crewLvl = vehGetter(vehCompDescr, {}).get('crewLvl', 50)
                try:
                    vehUserString = vehicles_core.getVehicleType(vehCompDescr).userString
                    if crewLvl > 50:
                        crewLvl = cls.__i18nCrewLvlString % crewLvl
                        vehUserString = '{0:>s} ({1:>s})'.format(vehUserString, crewLvl)
                    if isNegative and validateNegative:
                        removeVehNames.append(vehUserString)
                    else:
                        addVehNames.append(vehUserString)
                except:
                    LOG_ERROR('Wrong vehicle compact descriptor', vehCompDescr)
                    LOG_CURRENT_EXCEPTION()

        return (addVehNames, removeVehNames)

    @classmethod
    def _getVehiclesString(cls, vehicles, exclude = None, htmlTplPostfix = 'InvoiceReceived'):
        addVehNames, removeVehNames = cls._getVehicleNames(vehicles, exclude=exclude)
        result = ''
        if len(addVehNames):
            result = g_settings.htmlTemplates.format('vehiclesAccrued' + htmlTplPostfix, ctx={'vehicles': ', '.join(addVehNames)})
        if len(removeVehNames):
            if len(result):
                result += '<br/>'
            result += g_settings.htmlTemplates.format('vehiclesDebited' + htmlTplPostfix, ctx={'vehicles': ', '.join(removeVehNames)})
        return result

    @classmethod
    def _getComptnString(cls, comptnList, htmlTplPostfix = 'InvoiceReceived'):
        result = []
        html = g_settings.htmlTemplates
        for itemDict, comptn in comptnList:
            itemNames = []
            values = []
            items = itemDict.get('vehicles')
            if len(items):
                itemNames, _ = cls._getVehicleNames(items, validateNegative=False, showCrewLvl=False)
            gold = comptn.get('gold', 0)
            if gold > 0:
                values.append(html.format('goldCompensation' + htmlTplPostfix, ctx={'amount': BigWorld.wg_getGoldFormat(gold)}))
            accCredits = comptn.get('credits', 0)
            if accCredits > 0:
                values.append(html.format('creditsCompensation' + htmlTplPostfix, ctx={'amount': BigWorld.wg_getIntegralFormat(accCredits)}))
            if len(itemNames) and len(values):
                result.append(html.format('compensationFor' + htmlTplPostfix, ctx={'items': ', '.join(itemNames),
                 'compensation': ', '.join(values)}))

        return '<br/>'.join(result)

    def __getTankmenString(self, tmen):
        tmanUserStrings = []
        skillsConfig = tankmen.getSkillsConfig()
        for tmanCompDescr in tmen:
            try:
                tmanDescr = tankmen.TankmanDescr(tmanCompDescr)
                nationConfig = tankmen.getNationConfig(tmanDescr.nationID)
                tmanUserStrings.append('{0:>s} {1:>s} ({2:>s}, {3:>s}, {4:d}%)'.format(nationConfig['ranks'][tmanDescr.rankID].get('userString', ''), nationConfig['lastNames'][tmanDescr.lastNameID], skillsConfig.get(tmanDescr.role, {}).get('userString', ''), vehicles_core.g_cache.vehicle(tmanDescr.nationID, tmanDescr.vehicleTypeID).userString, tmanDescr.roleLevel))
            except:
                LOG_ERROR('Wrong tankman compact descriptor', tmanCompDescr)
                LOG_CURRENT_EXCEPTION()

        result = ''
        if len(tmanUserStrings):
            result = g_settings.htmlTemplates.format('tankmenInvoiceReceived', ctx={'tankman': ', '.join(tmanUserStrings)})
        return result

    def __getSlotsString(self, slots):
        if slots > 0:
            template = 'slotsAccruedInvoiceReceived'
        else:
            template = 'slotsDebitedInvoiceReceived'
        return g_settings.htmlTemplates.format(template, {'amount': BigWorld.wg_getIntegralFormat(abs(slots))})

    def __getL10nDescription(self, data):
        descr = ''
        lData = getLocalizedData(data.get('data', {}), 'localized_description', defVal=None)
        if lData:
            descr = html.escape(lData.get('description', u'').encode('utf-8'))
            if len(descr):
                descr = '<br/>' + descr
        return descr

    @classmethod
    def _makeComptnItemDict(cls, data):
        result = {}
        for items, comptn in data.get('compensation', []):
            for key, data in items.iteritems():
                exKey = 'ex_{0:>s}'.format(key)
                result.setdefault(exKey, [])
                result[exKey].extend(data)

        return result

    def __formatAmount(self, assetType, data):
        amount = data.get('amount', None)
        if amount is None:
            return
        else:
            return g_settings.msgTemplates.format(self.__messageTemplateKeys[assetType], ctx={'at': self.__getOperationTimeString(data),
             'desc': self.__getL10nDescription(data),
             'op': self.__getFinOperationString(assetType, amount)})

    def __formatData(self, assetType, data):
        dataEx = data.get('data', {})
        if dataEx is None or not len(dataEx):
            return
        else:
            operations = []
            comptnDict = self._makeComptnItemDict(data)
            gold = dataEx.get('gold')
            if gold is not None:
                operations.append(self.__getFinOperationString(INVOICE_ASSET.GOLD, gold))
            accCredtis = dataEx.get('credits')
            if accCredtis is not None:
                operations.append(self.__getFinOperationString(INVOICE_ASSET.CREDITS, accCredtis))
            freeXp = dataEx.get('freeXP')
            if freeXp is not None:
                operations.append(self.__getFinOperationString(INVOICE_ASSET.FREE_XP, freeXp))
            premium = dataEx.get('premium')
            if premium is not None:
                operations.append(self.__getFinOperationString(INVOICE_ASSET.PREMIUM, premium))
            items = dataEx.get('items', {})
            if items is not None and len(items) > 0:
                operations.append(self.__getItemsString(items))
            tmen = dataEx.get('tankmen', {})
            if tmen is not None and len(tmen) > 0:
                operations.append(self.__getTankmenString(tmen))
            vehicles = dataEx.get('vehicles', {})
            if vehicles is not None and len(vehicles) > 0:
                exclude = comptnDict.get('ex_vehicles', [])
                result = self._getVehiclesString(vehicles, exclude=exclude)
                if len(result):
                    operations.append(result)
            compensation = data.get('compensation', [])
            if len(compensation):
                comptnStr = self._getComptnString(compensation)
                if len(comptnStr):
                    operations.append(comptnStr)
            slots = dataEx.get('slots')
            if slots:
                operations.append(self.__getSlotsString(slots))
            return g_settings.msgTemplates.format(self.__messageTemplateKeys[assetType], ctx={'at': self.__getOperationTimeString(data),
             'desc': self.__getL10nDescription(data),
             'op': '<br/>'.join(operations)})

    def format(self, message, *args):
        LOG_DEBUG('invoiceReceived', message)
        data = message.data
        assetType = data.get('assetType', -1)
        handler = self.__assetHandlers.get(assetType)
        if handler is not None:
            return getattr(self, handler)(assetType, data)
        else:
            return
            return


class AdminMessageFormatter(ServiceChannelFormatter):

    def format(self, message, *args):
        if message.data:
            return g_settings.msgTemplates.format('adminMessage', {'text': message.data.decode('utf-8')})
        else:
            return None
            return None


class AccountTypeChangedFormatter(ServiceChannelFormatter):

    def format(self, message, *args):
        data = message.data
        isPremium = data.get('isPremium', None)
        expiryTime = data.get('expiryTime', None)
        result = None
        if isPremium is not None:
            accountTypeName = i18n.makeString('#menu:accountTypes/premium') if isPremium else i18n.makeString('#menu:accountTypes/base')
            expiryDatetime = TimeFormatter.getLongDatetimeFormat(expiryTime) if expiryTime else None
            if expiryDatetime:
                templateKey = 'accountTypeChangedWithExpiration'
                ctx = {'accType': accountTypeName,
                 'expiryTime': expiryDatetime}
            else:
                templateKey = 'accountTypeChanged'
                ctx = {'accType': accountTypeName}
            result = g_settings.msgTemplates.format(templateKey, ctx=ctx)
        return result


class PremiumActionFormatter(ServiceChannelFormatter):
    _templateKey = None

    def _getMessage(self, isPremium, expiryTime):
        pass

    def format(self, message, *args):
        data = message.data
        isPremium = data.get('isPremium', None)
        expiryTime = data.get('expiryTime', None)
        if isPremium is not None:
            return self._getMessage(isPremium, expiryTime)
        else:
            return


class PremiumBoughtFormatter(PremiumActionFormatter):
    _templateKey = 'premiumBought'

    def _getMessage(self, isPremium, expiryTime):
        result = None
        if isPremium is True and expiryTime > 0:
            result = g_settings.msgTemplates.format(self._templateKey, ctx={'expiryTime': TimeFormatter.getLongDatetimeFormat(expiryTime)})
        return result


class PremiumExtendedFormatter(PremiumBoughtFormatter):
    _templateKey = 'premiumExtended'


class PremiumExpiredFormatter(PremiumActionFormatter):
    _templateKey = 'premiumExpired'

    def _getMessage(self, isPremium, expiryTime):
        result = None
        if isPremium is False:
            result = g_settings.msgTemplates.format(self._templateKey)
        return result


class WaresSoldFormatter(ServiceChannelFormatter):

    def notify(self):
        return True

    def format(self, message, *args):
        result = None
        if message.data:
            offer = offers._makeOutOffer(message.data)
            result = g_settings.msgTemplates.format('waresSoldAsGold', ctx={'srcWares': BigWorld.wg_getGoldFormat(offer.srcWares),
             'dstName': offer.dstName,
             'fee': offer.fee})
        return result


class WaresBoughtFormatter(ServiceChannelFormatter):

    def notify(self):
        return True

    def format(self, message, *args):
        result = None
        if message.data:
            offer = offers._makeInOffer(message.data)
            result = g_settings.msgTemplates.format('waresBoughtAsGold', ctx={'srcName': offer.srcName,
             'srcWares': BigWorld.wg_getGoldFormat(offer.srcWares)})
        return result


class PrebattleFormatter(ServiceChannelFormatter):
    __battleTypeByPrebattleType = {PREBATTLE_TYPE.TOURNAMENT: 'tournament',
     PREBATTLE_TYPE.CLAN: 'clan'}
    _battleFinishReasonKeys = {}
    _defaultBattleFinishReasonKey = ('base', True)

    def notify(self):
        return True

    def _getIconId(self, prbType):
        iconId = 'BattleResultIcon'
        if prbType == PREBATTLE_TYPE.CLAN:
            iconId = 'ClanBattleResultIcon'
        elif prbType == PREBATTLE_TYPE.TOURNAMENT:
            iconId = 'TournamentBattleResultIcon'
        return iconId

    def _makeBattleTypeString(self, prbType):
        typeString = self.__battleTypeByPrebattleType.get(prbType, 'prebattle')
        key = '#{0:>s}:serviceChannelMessages/prebattle/battleType/{1:>s}'.format(MESSENGER_I18N_FILE, typeString)
        return i18n.makeString(key)

    def _makeDescriptionString(self, data, showBattlesCount = True):
        if data.has_key('localized_data') and len(data['localized_data']):
            description = getPrebattleFullDescription(data, escapeHtml=True)
        else:
            prbType = data.get('type')
            description = self._makeBattleTypeString(prbType)
        battlesLimit = data.get('battlesLimit', 0)
        if showBattlesCount and battlesLimit > 1:
            battlesCount = data.get('battlesCount')
            if battlesCount > 0:
                key = '#{0:>s}:serviceChannelMessages/prebattle/numberOfBattle'.format(MESSENGER_I18N_FILE)
                numberOfBattleString = i18n.makeString(key, battlesCount)
                description = '{0:>s} {1:>s}'.format(description, numberOfBattleString)
            else:
                LOG_WARNING('Invalid value of battlesCount ', battlesCount)
        return description

    def _getOpponentsString(self, opponents):
        first = opponents.get('1', {}).get('name', '').encode('utf-8')
        second = opponents.get('2', {}).get('name', '').encode('utf-8')
        result = ''
        if len(first) > 0 and len(second) > 0:
            result = g_settings.htmlTemplates.format('prebattleOpponents', ctx={'first': html.escape(first),
             'second': html.escape(second)})
        return result

    def _getBattleResultString(self, winner, team):
        result = 'undefined'
        if 3 > winner > -1 and team in (1, 2):
            if not winner:
                result = 'draftGame'
            else:
                result = 'defeat' if team != winner else 'win'
        return result

    def _makeBattleResultString(self, finishReason, winner, team):
        finishString, showResult = self._battleFinishReasonKeys.get(finishReason, self._defaultBattleFinishReasonKey)
        if showResult:
            resultString = self._getBattleResultString(winner, team)
            key = '#{0:>s}:serviceChannelMessages/prebattle/finish/{1:>s}/{2:>s}'.format(MESSENGER_I18N_FILE, finishString, resultString)
        else:
            key = '#{0:>s}:serviceChannelMessages/prebattle/finish/{1:>s}'.format(MESSENGER_I18N_FILE, finishString)
        return i18n.makeString(key)

    def _makeCreateAtString(self, message):
        if message.createdAt is not None:
            result = message.createdAt.strftime('%c')
        else:
            LOG_WARNING('Invalid value of created_at = None')
            import time
            result = TimeFormatter.getLongDatetimeFormat(time.time())
        return result


class PrebattleArenaFinishFormatter(PrebattleFormatter):
    _battleFinishReasonKeys = {FINISH_REASON.TECHNICAL: ('technical', True),
     FINISH_REASON.FAILURE: ('failure', False),
     FINISH_REASON.UNKNOWN: ('failure', False)}

    def format(self, message, *args):
        LOG_DEBUG('prbArenaFinish', message)
        data = message.data
        prbType = data.get('type')
        winner = data.get('winner')
        team = data.get('team')
        wins = data.get('wins')
        finishReason = data.get('finishReason')
        if None in [prbType,
         winner,
         team,
         wins,
         finishReason]:
            return
        else:
            battleResult = self._makeBattleResultString(finishReason, winner, team)
            subtotal = ''
            battlesLimit = data.get('battlesLimit', 0)
            if battlesLimit > 1:
                battlesCount = data.get('battlesCount', -1)
                winsLimit = data.get('winsLimit', -1)
                if battlesCount == battlesLimit or winsLimit == wins[1] or winsLimit == wins[2]:
                    playerTeamWins = wins[team]
                    otherTeamWins = wins[2 if team == 1 else 1]
                    if winsLimit > 0 and playerTeamWins < winsLimit and otherTeamWins < winsLimit:
                        winner = None
                    elif playerTeamWins == otherTeamWins:
                        winner = 0
                    else:
                        winner = 1 if wins[1] > wins[2] else 2
                    sessionResult = self._makeBattleResultString(-1, winner, team)
                    subtotal = g_settings.htmlTemplates.format('prebattleTotal', ctx={'result': sessionResult,
                     'first': wins[1],
                     'second': wins[2]})
                else:
                    subtotal = g_settings.htmlTemplates.format('prebattleSubtotal', ctx={'first': wins[1],
                     'second': wins[2]})
            return g_settings.msgTemplates.format('prebattleArenaFinish', ctx={'desc': self._makeDescriptionString(data),
             'createdAt': self._makeCreateAtString(message),
             'opponents': self._getOpponentsString(data.get('opponents', {})),
             'result': battleResult,
             'subtotal': subtotal}, data={'icon': self._getIconId(prbType)})


class PrebattleKickFormatter(PrebattleFormatter):

    def format(self, message, *args):
        data = message.data
        result = None
        prbType = data.get('type')
        kickReason = data.get('kickReason')
        if prbType > 0 and kickReason > 0:
            ctx = {}
            key = '#system_messages:prebattle/kick/type/unknown'
            if prbType == PREBATTLE_TYPE.SQUAD:
                key = '#system_messages:prebattle/kick/type/squad'
            elif prbType == PREBATTLE_TYPE.COMPANY:
                key = '#system_messages:prebattle/kick/type/team'
            ctx['type'] = i18n.makeString(key)
            kickName = KICK_REASON_NAMES[kickReason]
            key = '#system_messages:prebattle/kick/reason/{0:>s}'.format(kickName)
            ctx['reason'] = i18n.makeString(key)
            result = g_settings.msgTemplates.format('prebattleKick', ctx=ctx)
        return result


class PrebattleDestructionFormatter(PrebattleFormatter):
    _battleFinishReasonKeys = {KICK_REASON.ARENA_CREATION_FAILURE: ('failure', False),
     KICK_REASON.AVATAR_CREATION_FAILURE: ('failure', False),
     KICK_REASON.VEHICLE_CREATION_FAILURE: ('failure', False),
     KICK_REASON.PREBATTLE_CREATION_FAILURE: ('failure', False),
     KICK_REASON.BASEAPP_CRASH: ('failure', False),
     KICK_REASON.CELLAPP_CRASH: ('failure', False),
     KICK_REASON.UNKNOWN_FAILURE: ('failure', False),
     KICK_REASON.CREATOR_LEFT: ('creatorLeft', False),
     KICK_REASON.PLAYERKICK: ('playerKick', False),
     KICK_REASON.TIMEOUT: ('timeout', False)}

    def format(self, message, *args):
        LOG_DEBUG('prbDestruction', message)
        data = message.data
        prbType = data.get('type')
        team = data.get('team')
        wins = data.get('wins')
        kickReason = data.get('kickReason')
        if None in [prbType,
         team,
         wins,
         kickReason]:
            return
        else:
            playerTeamWins = wins[team]
            otherTeamWins = wins[2 if team == 1 else 1]
            winsLimit = data.get('winsLimit')
            if winsLimit > 0 and playerTeamWins < winsLimit and otherTeamWins < winsLimit:
                winner = None
            elif playerTeamWins == otherTeamWins:
                winner = 0
            else:
                winner = 1 if wins[1] > wins[2] else 2
            battleResult = self._makeBattleResultString(kickReason, winner, team)
            total = ''
            if data.get('battlesLimit', 0) > 1:
                total = '({0:d}:{1:d})'.format(wins[1], wins[2])
            return g_settings.msgTemplates.format('prebattleDestruction', ctx={'desc': self._makeDescriptionString(data, showBattlesCount=False),
             'createdAt': self._makeCreateAtString(message),
             'opponents': self._getOpponentsString(data.get('opponents', {})),
             'result': battleResult,
             'total': total}, data={'icon': self._getIconId(prbType)})


class VehCamouflageTimedOutFormatter(ServiceChannelFormatter):

    def notify(self):
        return True

    def format(self, message, *args):
        data = message.data
        formatted = None
        vehTypeCompDescr = data.get('vehTypeCompDescr')
        if vehTypeCompDescr is not None:
            vType = vehicles_core.getVehicleType(vehTypeCompDescr)
            if vType is not None:
                formatted = g_settings.msgTemplates.format('vehCamouflageTimedOut', ctx={'vehicleName': vType.userString})
        return formatted


class VehEmblemTimedOutFormatter(ServiceChannelFormatter):

    def notify(self):
        return True

    def format(self, message, *args):
        data = message.data
        formatted = None
        vehTypeCompDescr = data.get('vehTypeCompDescr')
        if vehTypeCompDescr is not None:
            vType = vehicles_core.getVehicleType(vehTypeCompDescr)
            if vType is not None:
                formatted = g_settings.msgTemplates.format('vehEmblemTimedOut', ctx={'vehicleName': vType.userString})
        return formatted


class VehInscriptionTimedOutFormatter(ServiceChannelFormatter):

    def notify(self):
        return True

    def format(self, message, *args):
        data = message.data
        formatted = None
        vehTypeCompDescr = data.get('vehTypeCompDescr')
        if vehTypeCompDescr is not None:
            vType = vehicles_core.getVehicleType(vehTypeCompDescr)
            if vType is not None:
                formatted = g_settings.msgTemplates.format('vehInscriptionTimedOut', ctx={'vehicleName': vType.userString})
        return formatted


class ConverterFormatter(ServiceChannelFormatter):

    def __i18nValue(self, key, isReceived, **kwargs):
        key = ('%sReceived' if isReceived else '%sWithdrawn') % key
        key = '#messenger:serviceChannelMessages/sysMsg/converter/%s' % key
        return i18n.makeString(key) % kwargs

    def __vehName(self, vehCompDescr):
        return vehicles_core.getVehicleType(abs(vehCompDescr)).userString

    def format(self, message, *args):
        data = message.data
        text = []
        if data.get('playerInscriptions'):
            text.append(i18n.makeString('#messenger:serviceChannelMessages/sysMsg/converter/inscriptions'))
        if data.get('playerEmblems'):
            text.append(i18n.makeString('#messenger:serviceChannelMessages/sysMsg/converter/emblems'))
        if data.get('camouflages'):
            text.append(i18n.makeString('#messenger:serviceChannelMessages/sysMsg/converter/camouflages'))
        vehicles = data.get('vehicles')
        if vehicles:
            vehiclesReceived = [ self.__vehName(cd) for cd in vehicles if cd > 0 ]
            if len(vehiclesReceived):
                text.append(self.__i18nValue('vehicles', True, vehicles=', '.join(vehiclesReceived)))
            vehiclesWithdrawn = [ self.__vehName(cd) for cd in vehicles if cd < 0 ]
            if len(vehiclesWithdrawn):
                text.append(self.__i18nValue('vehicles', False, vehicles=', '.join(vehiclesWithdrawn)))
        slots = data.get('slots')
        if slots:
            text.append(self.__i18nValue('slots', slots > 0, slots=BigWorld.wg_getIntegralFormat(abs(slots))))
        gold = data.get('gold')
        if gold:
            text.append(self.__i18nValue('gold', gold > 0, gold=BigWorld.wg_getGoldFormat(abs(gold))))
        accCredits = data.get('credits')
        if accCredits:
            text.append(self.__i18nValue('credits', accCredits > 0, credits=BigWorld.wg_getIntegralFormat(abs(accCredits))))
        freeXP = data.get('freeXP')
        if freeXP:
            text.append(self.__i18nValue('freeXP', freeXP > 0, freeXP=BigWorld.wg_getIntegralFormat(abs(freeXP))))
        return g_settings.msgTemplates.format('ConverterNotify', {'text': '<br/>'.join(text)})


class ClientSysMessageFormatter(ServiceChannelFormatter):
    __templateKey = '%sSysMessage'

    def format(self, data, *args):
        if len(args):
            msgType = args[0][0]
        else:
            msgType = 'Error'
        return g_settings.msgTemplates.format(self.__templateKey % msgType, ctx={'text': data})


class PremiumAccountExpiryFormatter(ServiceChannelFormatter):

    def format(self, data, *args):
        return g_settings.msgTemplates.format('durationOfPremiumAccountExpires', ctx={'expiryTime': TimeFormatter.getLongDatetimeFormat(data)})


class AOGASNotifyFormatter(ServiceChannelFormatter):

    def format(self, data, *args):
        return g_settings.msgTemplates.format('AOGASNotify', {'text': i18n.makeString('#AOGAS:{0:>s}'.format(data.name()))})


class VehicleTypeLockExpired(ServiceChannelFormatter):

    def format(self, message, *args):
        result = None
        if message.data:
            ctx = {}
            vehTypeCompDescr = message.data.get('vehTypeCompDescr')
            if vehTypeCompDescr is None:
                templateKey = 'vehiclesAllLockExpired'
            else:
                templateKey = 'vehicleLockExpired'
                ctx['vehicleName'] = vehicles_core.getVehicleType(vehTypeCompDescr).userString
            result = g_settings.msgTemplates.format(templateKey, ctx=ctx)
        return result


class ServerDowntimeCompensation(ServiceChannelFormatter):
    __templateKey = 'serverDowntimeCompensation'

    def format(self, message, *args):
        result = None
        subjects = ''
        data = message.data
        if data is not None:
            for key, value in data.items():
                if value:
                    if len(subjects) > 0:
                        subjects += ', '
                    subjects += i18n.makeString('#%s:serviceChannelMessages/' % MESSENGER_I18N_FILE + self.__templateKey + '/' + key)

            if len(subjects) > 0:
                result = g_settings.msgTemplates.format(self.__templateKey, ctx={'text': i18n.makeString('#%s:serviceChannelMessages/' % MESSENGER_I18N_FILE + self.__templateKey) % subjects})
        return result


class ActionNotificationFormatter(ServiceChannelFormatter):
    __templateKey = 'action%s'

    def format(self, message, *args):
        result = None
        data = message.get('data')
        if data:
            result = g_settings.msgTemplates.format(self.__templateKey % message.get('state', ''), ctx={'text': data}, data={'icon': message.get('type', '')})
        return result


class BattleTutorialResultsFormatter(ServiceChannelFormatter):
    __resultKeyWithBonuses = 'battleTutorialResBonuses'
    __resultKeyWoBonuses = 'battleTutorialResWoBonuses'

    def notify(self):
        return True

    def format(self, data, *args):
        LOG_DEBUG('message data', data)
        finishReason = data.get('finishReason', -1)
        resultKey = data.get('resultKey', None)
        finishKey = data.get('finishKey', None)
        if finishReason > -1 and resultKey and finishKey:
            resultString = i18n.makeString('#{0:>s}:serviceChannelMessages/battleTutorial/results/{1:>s}'.format(MESSENGER_I18N_FILE, resultKey))
            reasonString = i18n.makeString('#{0:>s}:serviceChannelMessages/battleTutorial/reasons/{1:>s}'.format(MESSENGER_I18N_FILE, finishKey))
            arenaTypeID = data.get('arenaTypeID', 0)
            arenaName = 'N/A'
            if arenaTypeID > 0:
                arenaName = ArenaType.g_cache[arenaTypeID].name
            import time
            startedAtTime = data.get('startedAt', time.time())
            vTypeCD = data.get('vTypeCD', None)
            vName = 'N/A'
            if vTypeCD is not None:
                vName = vehicles_core.getVehicleType(vTypeCD).userString
            ctx = {'result': resultString,
             'reason': reasonString,
             'arenaName': i18n.makeString(arenaName),
             'startedAt': TimeFormatter.getLongDatetimeFormat(startedAtTime),
             'vehicleName': vName,
             'freeXP': '0',
             'credits': '0'}
            freeXP = 0
            credits_ = 0
            chapters = data.get('chapters', [])
            for chapter in chapters:
                if chapter.get('received', False):
                    bonus = chapter.get('bonus', {})
                    freeXP += bonus.get('freeXP', 0)
                    credits_ += bonus.get('credits', 0)

            if freeXP:
                ctx['freeXP'] = BigWorld.wg_getIntegralFormat(freeXP)
            if credits_:
                ctx['credits'] = BigWorld.wg_getIntegralFormat(credits_)
            all_ = data.get('areAllBonusesReceived', False)
            if all_ and credits_ <= 0 and freeXP <= 0:
                key = self.__resultKeyWoBonuses
            else:
                key = self.__resultKeyWithBonuses
            return g_settings.msgTemplates.format(key, ctx=ctx, data={'key': 'arenaUniqueID',
             'value': data.get('arenaUniqueID', -1)})
        else:
            return
            return
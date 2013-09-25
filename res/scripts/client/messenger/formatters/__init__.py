# Embedded file name: scripts/client/messenger/formatters/__init__.py
import BigWorld
from messenger import g_settings

class TimeFormatter(object):
    _messageDateTimeFormat = {0: 'getMessageEmptyFormatU',
     1: 'getMessageShortDateFormat',
     2: 'getMessageLongTimeFormat',
     3: 'getMessageLongDatetimeFormat'}

    @classmethod
    def getMessageTimeFormat(cls, time):
        method = cls._messageDateTimeFormat[g_settings.userPrefs.datetimeIdx]
        return getattr(cls, method)(time)

    @classmethod
    def getShortDateFormat(cls, time):
        return '{0:>s}'.format(BigWorld.wg_getShortDateFormat(time))

    @classmethod
    def getLongTimeFormat(cls, time):
        return '{0:>s}'.format(BigWorld.wg_getLongTimeFormat(time))

    @classmethod
    def getLongDatetimeFormat(cls, time):
        return '{0:>s} {1:>s}'.format(BigWorld.wg_getShortDateFormat(time), BigWorld.wg_getLongTimeFormat(time))

    @classmethod
    def getMessageEmptyFormatU(cls, _):
        return u''

    @classmethod
    def getMessageShortDateFormat(cls, time):
        return '({0:>s}) '.format(BigWorld.wg_getShortDateFormat(time)).decode('utf-8', 'ignore')

    @classmethod
    def getMessageLongTimeFormat(cls, time):
        return '({0:>s}) '.format(BigWorld.wg_getLongTimeFormat(time)).decode('utf-8', 'ignore')

    @classmethod
    def getMessageLongDatetimeFormat(cls, time):
        return '({0:>s} {1:>s}) '.format(BigWorld.wg_getShortDateFormat(time), BigWorld.wg_getLongTimeFormat(time)).decode('utf-8', 'ignore')


from chat_shared import SYS_MESSAGE_TYPE
from messenger.formatters import service_channel as sch_formatters
SCH_SERVER_FORMATTERS_DICT = {SYS_MESSAGE_TYPE.serverReboot.index(): sch_formatters.ServerRebootFormatter(),
 SYS_MESSAGE_TYPE.serverRebootCancelled.index(): sch_formatters.ServerRebootCancelledFormatter(),
 SYS_MESSAGE_TYPE.battleResults.index(): sch_formatters.BattleResultsFormatter(),
 SYS_MESSAGE_TYPE.goldReceived.index(): sch_formatters.GoldReceivedFormatter(),
 SYS_MESSAGE_TYPE.invoiceReceived.index(): sch_formatters.InvoiceReceivedFormatter(),
 SYS_MESSAGE_TYPE.adminTextMessage.index(): sch_formatters.AdminMessageFormatter(),
 SYS_MESSAGE_TYPE.accountTypeChanged.index(): sch_formatters.AccountTypeChangedFormatter(),
 SYS_MESSAGE_TYPE.giftReceived.index(): sch_formatters.GiftReceivedFormatter(),
 SYS_MESSAGE_TYPE.autoMaintenance.index(): sch_formatters.AutoMaintenanceFormatter(),
 SYS_MESSAGE_TYPE.waresSold.index(): sch_formatters.WaresSoldFormatter(),
 SYS_MESSAGE_TYPE.waresBought.index(): sch_formatters.WaresBoughtFormatter(),
 SYS_MESSAGE_TYPE.premiumBought.index(): sch_formatters.PremiumBoughtFormatter(),
 SYS_MESSAGE_TYPE.premiumExtended.index(): sch_formatters.PremiumExtendedFormatter(),
 SYS_MESSAGE_TYPE.premiumExpired.index(): sch_formatters.PremiumExpiredFormatter(),
 SYS_MESSAGE_TYPE.prbArenaFinish.index(): sch_formatters.PrebattleArenaFinishFormatter(),
 SYS_MESSAGE_TYPE.prbKick.index(): sch_formatters.PrebattleKickFormatter(),
 SYS_MESSAGE_TYPE.prbDestruction.index(): sch_formatters.PrebattleDestructionFormatter(),
 SYS_MESSAGE_TYPE.vehicleCamouflageTimedOut.index(): sch_formatters.VehCamouflageTimedOutFormatter(),
 SYS_MESSAGE_TYPE.vehiclePlayerEmblemTimedOut.index(): sch_formatters.VehEmblemTimedOutFormatter(),
 SYS_MESSAGE_TYPE.vehiclePlayerInscriptionTimedOut.index(): sch_formatters.VehInscriptionTimedOutFormatter(),
 SYS_MESSAGE_TYPE.vehTypeLockExpired.index(): sch_formatters.VehicleTypeLockExpired(),
 SYS_MESSAGE_TYPE.serverDowntimeCompensation.index(): sch_formatters.ServerDowntimeCompensation(),
 SYS_MESSAGE_TYPE.achievementReceived.index(): sch_formatters.AchievementFormatter(),
 SYS_MESSAGE_TYPE.converter.index(): sch_formatters.ConverterFormatter()}

class SCH_CLIENT_MSG_TYPE(object):
    SYS_MSG_TYPE, PREMIUM_ACCOUNT_EXPIRY_MSG, AOGAS_NOTIFY_TYPE, ACTION_NOTIFY_TYPE, BATTLE_TUTORIAL_RESULTS_TYPE = range(5)


SCH_CLIENT_FORMATTERS_DICT = {SCH_CLIENT_MSG_TYPE.SYS_MSG_TYPE: sch_formatters.ClientSysMessageFormatter(),
 SCH_CLIENT_MSG_TYPE.PREMIUM_ACCOUNT_EXPIRY_MSG: sch_formatters.PremiumAccountExpiryFormatter(),
 SCH_CLIENT_MSG_TYPE.AOGAS_NOTIFY_TYPE: sch_formatters.AOGASNotifyFormatter(),
 SCH_CLIENT_MSG_TYPE.ACTION_NOTIFY_TYPE: sch_formatters.ActionNotificationFormatter(),
 SCH_CLIENT_MSG_TYPE.BATTLE_TUTORIAL_RESULTS_TYPE: sch_formatters.BattleTutorialResultsFormatter()}
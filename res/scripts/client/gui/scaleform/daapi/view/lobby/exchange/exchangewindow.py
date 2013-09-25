import BigWorld
from adisp import process
from gui import SystemMessages
from gui.ClientUpdateManager import g_clientUpdateManager
from gui import DialogsInterface
from gui.Scaleform.Waiting import Waiting
from gui.Scaleform.daapi.view.lobby.exchange.BaseExchangeWindow import BaseExchangeWindow
from gui.Scaleform.daapi.view.meta.ExchangeWindowMeta import ExchangeWindowMeta
from gui.Scaleform.daapi.view.dialogs import HtmlMessageDialogMeta
from gui.shared.utils.gui_items import formatPrice
from gui.shared.utils.requesters import StatsRequester, ItemsRequester, ShopRequester

class ExchangeWindow(ExchangeWindowMeta, BaseExchangeWindow):

    @process
    def _populate(self):
        super(ExchangeWindow, self)._populate()
        inventory = yield ItemsRequester().request()
        stats = inventory.stats
        self.as_setPrimaryCurrencyS(stats.gold)
        self.as_setSecondaryCurrencyS(stats.credits)
        shop = inventory.shop
        self.as_exchangeRateS(shop.exchangeRate, shop.exchangeRate)

    @process
    def exchange(self, gold):
        shop = yield ShopRequester().request()
        isConfirmed = yield DialogsInterface.showI18nConfirmDialog('exchangeGoldConfirmation', meta=HtmlMessageDialogMeta('html_templates:lobby/dialogs', 'confirmExchange', {'primaryCurrencyAmount': BigWorld.wg_getGoldFormat(gold),
         'resultCurrencyAmount': BigWorld.wg_getIntegralFormat(int(gold) * shop.exchangeRate)}))
        if isConfirmed:
            Waiting.show('transferMoney')
            message = '#system_messages:exchange/server_error'
            success = yield StatsRequester().exchange(int(gold))
            if success:
                message = '#system_messages:exchange/success'
                self.onWindowClose()
            SystemMessages.g_instance.pushI18nMessage(message, BigWorld.wg_getGoldFormat(gold), formatPrice((shop.exchangeRate * gold, 0)), type=SystemMessages.SM_TYPE.FinancialTransactionWithGold if success else SystemMessages.SM_TYPE.Error)
            Waiting.hide('transferMoney')

    def _subscribe(self):
        g_clientUpdateManager.addCallbacks({'stats.credits': self.__setCreditsCallBack,
         'stats.gold': self._setGoldCallBack,
         'shop.exchangeRate': self.__setExchangeRateCallBack})

    def __setExchangeRateCallBack(self, rate):
        self.as_exchangeRateS(rate, rate)

    def __setCreditsCallBack(self, credits):
        self.as_setSecondaryCurrencyS(credits)

    def onWindowClose(self):
        self.destroy()

# 2013.11.15 11:26:01 EST
# Embedded file name: scripts/client/gui/Scaleform/daapi/view/lobby/exchange/ExchangeWindow.py
import BigWorld
from adisp import process
from gui import SystemMessages, game_control
from gui.ClientUpdateManager import g_clientUpdateManager
from gui.Scaleform.daapi.view.lobby.exchange.BaseExchangeWindow import BaseExchangeWindow
from gui.Scaleform.daapi.view.meta.ExchangeWindowMeta import ExchangeWindowMeta
from gui.shared import g_itemsCache
from gui.shared.gui_items.processors.common import GoldToCreditsExchanger
from gui.shared.utils import decorators
from gui.shared.utils.requesters import ItemsRequester

class ExchangeWindow(ExchangeWindowMeta, BaseExchangeWindow):

    @process
    def _populate(self):
        super(ExchangeWindow, self)._populate()
        inventory = yield ItemsRequester().request()
        stats = inventory.stats
        self.as_setPrimaryCurrencyS(stats.actualGold)
        self.as_setSecondaryCurrencyS(stats.actualCredits)
        shop = inventory.shop
        self.as_exchangeRateS(shop.exchangeRate, shop.exchangeRate)
        self.as_setWalletStatusS(game_control.g_instance.wallet.componentsStatuses)

    @decorators.process('transferMoney')
    def exchange(self, gold):
        result = yield GoldToCreditsExchanger(gold).request()
        if result and len(result.userMsg):
            SystemMessages.g_instance.pushI18nMessage(result.userMsg, type=result.sysMsgType)
            self.onWindowClose()

    def _subscribe(self):
        g_clientUpdateManager.addCallbacks({'stats.credits': self.__setCreditsCallBack,
         'stats.gold': self._setGoldCallBack,
         'shop.exchangeRate': self.__setExchangeRateCallBack})
        game_control.g_instance.wallet.onWalletStatusChanged += self.__setWalletCallback

    def __setExchangeRateCallBack(self, rate):
        self.as_exchangeRateS(rate, rate)

    def __setCreditsCallBack(self, credits):
        self.as_setSecondaryCurrencyS(credits)

    def __setWalletCallback(self, status):
        self.as_setPrimaryCurrencyS(g_itemsCache.items.stats.actualGold)
        self.as_setWalletStatusS(status)

    def onWindowClose(self):
        self.destroy()

    def _dispose(self):
        game_control.g_instance.wallet.onWalletStatusChanged -= self.__setWalletCallback
        g_clientUpdateManager.removeObjectCallbacks(self)
        super(ExchangeWindow, self)._dispose()
# okay decompyling res/scripts/client/gui/scaleform/daapi/view/lobby/exchange/exchangewindow.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:26:01 EST

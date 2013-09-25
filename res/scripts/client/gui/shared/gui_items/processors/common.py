# Embedded file name: scripts/client/gui/shared/gui_items/processors/common.py
import BigWorld
from debug_utils import *
from gui.SystemMessages import SM_TYPE
from gui.shared.utils.gui_items import formatPrice
from gui.shared.gui_items.processors import Processor, makeI18nError, makeI18nSuccess, plugins

class TankmanBerthsBuyer(Processor):

    def __init__(self, berthsPrice, berthsCount):
        super(TankmanBerthsBuyer, self).__init__((plugins.MessageInformator('barracksExpandNotEnoughMoney', activeHandler=lambda : not plugins.MoneyValidator(berthsPrice).validate().success), plugins.MessageConfirmator('barracksExpand', ctx={'price': berthsPrice[1],
          'count': berthsCount})))
        self.berthsPrice = berthsPrice

    def _errorHandler(self, code, errStr = '', ctx = None):
        if len(errStr):
            return makeI18nError('buy_tankmen_berths/%s' % errStr)
        return makeI18nError('buy_tankmen_berths/server_error')

    def _successHandler(self, code, ctx = None):
        return makeI18nSuccess('buy_tankmen_berths/success', money=formatPrice(self.berthsPrice), type=SM_TYPE.Information)

    def _request(self, callback):
        LOG_DEBUG('Make server request to buy tankman berths')
        BigWorld.player().stats.buyBerths(lambda code: self._response(code, callback))
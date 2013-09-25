from gui.ClientUpdateManager import g_clientUpdateManager
from gui.Scaleform.daapi.view.meta.BaseExchangeWindowMeta import BaseExchangeWindowMeta
from gui.Scaleform.daapi.view.meta.WindowViewMeta import WindowViewMeta
from gui.Scaleform.framework.entities.View import View
from gui.shared.utils.requesters import ItemsRequester
from adisp import process

class BaseExchangeWindow(View, BaseExchangeWindowMeta, WindowViewMeta):

    def __init__(self):
        View.__init__(self)

    def _populate(self):
        super(BaseExchangeWindow, self)._populate()
        self._subscribe()

    def _subscribe(self):
        pass

    def _setGoldCallBack(self, gold):
        self.as_setPrimaryCurrencyS(gold)

    def _dispose(self):
        g_clientUpdateManager.removeObjectCallbacks(self)
        super(BaseExchangeWindow, self)._dispose()

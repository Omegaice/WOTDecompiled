# 2013.11.15 11:25:55 EST
# Embedded file name: scripts/client/gui/Scaleform/daapi/view/dialogs/ConfirmModuleMeta.py
import math
from gui.Scaleform.daapi.view.dialogs import IDialogMeta
import Event
from gui.Scaleform.framework import VIEW_SCOPE
from gui.shared import events
from helpers import i18n
from gui.Scaleform.locale.DIALOGS import DIALOGS
from gui.ClientUpdateManager import g_clientUpdateManager
from gui.shared.utils.decorators import process
from gui.shared.gui_items.processors.module import ModuleBuyer, ModuleSeller
from gui import SystemMessages
MAX_ITEMS_FOR_OPERATION = 1000000

class ConfirmModuleMeta(IDialogMeta):

    def __init__(self, typeCompactDescr, title, submitBtn, cancelBtn):
        self.__typeCompactDescr = typeCompactDescr
        self.__title = title
        self.__submitLabel = submitBtn
        self.__cancelLabel = cancelBtn
        self.onInvalidate = Event.Event()

    def destroy(self):
        self.onInvalidate.clear()

    def submit(self, item, count, currency):
        pass

    def getEventType(self):
        return events.ShowDialogEvent.SHOW_CONFIRM_MODULE

    def getTitle(self):
        return i18n.makeString(self.__title)

    def getSubmitButtonLabel(self):
        return i18n.makeString(self.__submitLabel)

    def getCancelButtonLabel(self):
        return i18n.makeString(self.__cancelLabel)

    def getTypeCompDescr(self):
        return self.__typeCompactDescr

    def getMaxAvailableItemsCount(self, module):
        return (1, 1)

    def getDefaultValue(self, module):
        return -1

    def getActualPrice(self, module):
        return (0, 0)

    def getViewScopeType(self):
        return VIEW_SCOPE.DEFAULT


class SellModuleMeta(ConfirmModuleMeta):

    def __init__(self, typeCompactDescr):
        super(SellModuleMeta, self).__init__(typeCompactDescr, DIALOGS.SELLMODULECONFIRMATION_TITLE, DIALOGS.SELLMODULECONFIRMATION_SUBMIT, DIALOGS.SELLMODULECONFIRMATION_CANCEL)

    def getMaxAvailableItemsCount(self, module):
        """
        The maximum value is the value of items in inventory (no more then MAX_ITEMS_FOR_OPERATION)
        @param module: current item
        @return:
        """
        return (min(module.inventoryCount, MAX_ITEMS_FOR_OPERATION), min(module.inventoryCount, MAX_ITEMS_FOR_OPERATION))

    def getDefaultValue(self, module):
        return module.inventoryCount

    @process('sellItem')
    def submit(self, item, count, currency):
        result = yield ModuleSeller(item, min(count, MAX_ITEMS_FOR_OPERATION)).request()
        if len(result.userMsg):
            SystemMessages.g_instance.pushI18nMessage(result.userMsg, type=result.sysMsgType)

    def getActualPrice(self, module):
        return module.sellPrice


class LocalSellModuleMeta(SellModuleMeta):

    def getViewScopeType(self):
        return VIEW_SCOPE.LOBBY_SUB


class BuyModuleMeta(ConfirmModuleMeta):

    def __init__(self, typeCompactDescr, balance):
        super(BuyModuleMeta, self).__init__(typeCompactDescr, DIALOGS.BUYCONFIRMATION_TITLE, DIALOGS.BUYCONFIRMATION_SUBMIT, DIALOGS.BUYCONFIRMATION_CANCEL)
        self.__balance = list(balance)
        g_clientUpdateManager.addCallbacks({'stats': self.__onStatsChanged})

    def __onStatsChanged(self, stats):
        if 'credits' in stats:
            self.__balance[0] = stats['credits']
            self.onInvalidate()
        if 'gold' in stats:
            self.__balance[1] = stats['gold']
            self.onInvalidate()

    def __getMaxCount(self, module, currencyIdx):
        result = 0
        modulePrice = self.getActualPrice(module)
        if modulePrice[currencyIdx] > 0:
            result = math.floor(self.__balance[currencyIdx] / modulePrice[currencyIdx])
        return min(result, MAX_ITEMS_FOR_OPERATION)

    def destroy(self):
        g_clientUpdateManager.removeObjectCallbacks(self)
        super(BuyModuleMeta, self).destroy()

    def getMaxAvailableItemsCount(self, module):
        return (self.__getMaxCount(module, 0), self.__getMaxCount(module, 1))

    def getDefaultValue(self, module):
        return 1

    def getActualPrice(self, module):
        return module.actionPrice

    @process('buyItem')
    def submit(self, item, count, currency):
        result = yield ModuleBuyer(item, count, currency == 'credits').request()
        if len(result.userMsg):
            SystemMessages.g_instance.pushI18nMessage(result.userMsg, type=result.sysMsgType)
# okay decompyling res/scripts/client/gui/scaleform/daapi/view/dialogs/confirmmodulemeta.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:25:56 EST

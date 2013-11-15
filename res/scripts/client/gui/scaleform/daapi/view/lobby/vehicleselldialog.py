# 2013.11.15 11:26:22 EST
# Embedded file name: scripts/client/gui/Scaleform/daapi/view/lobby/VehicleSellDialog.py
from PlayerEvents import g_playerEvents
from debug_utils import LOG_ERROR, LOG_CURRENT_EXCEPTION
from gui.shared.gui_items import GUI_ITEM_TYPE
from account_helpers.AccountSettings import AccountSettings
from gui import SystemMessages, makeHtmlString
from gui.Scaleform.framework.entities.View import View
from gui.Scaleform.daapi.view.meta.VehicleSellDialogMeta import VehicleSellDialogMeta
from gui.Scaleform.daapi.view.meta.WindowViewMeta import WindowViewMeta
from gui.shared import g_itemsCache, REQ_CRITERIA
from gui.shared.utils.requesters import ShopRequester
from gui.shared.gui_items.serializers import g_itemSerializer
from gui.shared.gui_items.processors.vehicle import VehicleSeller
from gui.shared.utils import decorators
from gui.ClientUpdateManager import g_clientUpdateManager

class VehicleSellDialog(View, VehicleSellDialogMeta, WindowViewMeta):

    def __init__(self, vehInvID):
        """ Ctor """
        super(VehicleSellDialog, self).__init__()
        self.vehInvID = vehInvID
        self.controlNumber = None
        return

    def onWindowClose(self):
        self.destroy()

    def getDialogSettings(self):
        """
        Called from flash.
        @return: <dict> dialog settings dict from `AccountSettings`
        """
        return dict(AccountSettings.getSettings('vehicleSellDialog'))

    def setDialogSettings(self, isOpened):
        """
        Saving given dialog settings. Called from flash.
        @param isOpened: <bool> is dialog opened by default
        """
        settings = self.getDialogSettings()
        settings['isOpened'] = isOpened
        AccountSettings.setSettings('vehicleSellDialog', settings)

    def _populate(self):
        super(VehicleSellDialog, self)._populate()
        g_clientUpdateManager.addCallbacks({'stats.gold': self.onSetGoldHndlr})
        g_playerEvents.onShopResync += self.__shopResyncHandler
        items = g_itemsCache.items
        vehicle = items.getVehicle(self.vehInvID)
        invVehs = items.getVehicles(REQ_CRITERIA.INVENTORY)
        if vehicle.isPremium or vehicle.level >= 3:
            self.as_visibleControlBlockS(True)
            self.__initCtrlQuestion()
        else:
            self.as_visibleControlBlockS(False)
        modules = items.getItems(criteria=REQ_CRITERIA.VEHICLE.SUITABLE([vehicle]) | REQ_CRITERIA.INVENTORY).values()
        shells = items.getItems(criteria=REQ_CRITERIA.VEHICLE.SUITABLE([vehicle], [GUI_ITEM_TYPE.SHELL]) | REQ_CRITERIA.INVENTORY).values()
        otherVehsShells = set()
        for invVeh in invVehs.itervalues():
            if invVeh.invID != self.vehInvID:
                for shot in invVeh.descriptor.gun['shots']:
                    otherVehsShells.add(shot['shell']['compactDescr'])

        pack = g_itemSerializer.pack
        self.as_setDataS(pack(vehicle), [ (pack(m), False) for m in modules ], [ (pack(s), s.intCD in otherVehsShells) for s in shells ], items.shop.paidRemovalCost, items.stats.gold)

    def setUserInput(self, value):
        if value == self.controlNumber:
            self.as_enableButtonS(True)
        else:
            self.as_enableButtonS(False)

    def setResultCredit(self, value):
        self.controlNumber = str(value)
        self.__setControlQuestion()
        self.as_setControlNumberS(self.controlNumber)

    def _dispose(self):
        super(VehicleSellDialog, self)._dispose()
        g_playerEvents.onShopResync -= self.__shopResyncHandler
        g_clientUpdateManager.removeCallback('stats.gold', self.onSetGoldHndlr)

    def onSetGoldHndlr(self, gold):
        self.as_checkGoldS(gold)

    @decorators.process('sellVehicle')
    def __doSellVehicle(self, vehicle, shells, eqs, optDevs, inventory, isDismissCrew):
        shop = yield ShopRequester().request()
        result = yield VehicleSeller(vehicle, shop.paidRemovalCost, shells, eqs, optDevs, inventory, isDismissCrew).request()
        if len(result.userMsg):
            SystemMessages.g_instance.pushMessage(result.userMsg, type=result.sysMsgType)

    def sell(self, vehicle, shells, eqs, optDevs, inventory, isDismissCrew):
        """
        Make server request to sell given @vehicle. Called from flash.
        
        @param vehicle: <dict> vehicle packed data to sell
        @param shells: <list> list of shells items to sell
        @param eqs: <list> list of equipment items to sell
        @param optDevs: <list> list of optional devices to sell
        @param inventory: <list> list of inventory items to sell
        @param isDismissCrew: <bool> is dismiss crew
        """
        unpack = g_itemSerializer.unpack
        try:
            vehicle = unpack(vehicle)
            shells = [ unpack(shell) for shell in shells ]
            eqs = [ unpack(eq) for eq in eqs ]
            optDevs = [ unpack(dev) for dev in optDevs ]
            inventory = [ unpack(module) for module in inventory ]
            self.__doSellVehicle(vehicle, shells, eqs, optDevs, inventory, isDismissCrew)
        except Exception:
            LOG_ERROR('There is error while selling vehicle')
            LOG_CURRENT_EXCEPTION()

    def __initCtrlQuestion(self):
        self.as_enableButtonS(False)

    def __setControlQuestion(self):
        question = makeHtmlString('html_templates:lobby/dialogs', 'vehicleSellQuestion', {'controlNumber': str(int(self.controlNumber))})
        self.as_setCtrlQuestionS(str(question))

    def __shopResyncHandler(self):
        self.onWindowClose()
# okay decompyling res/scripts/client/gui/scaleform/daapi/view/lobby/vehicleselldialog.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:26:22 EST

import BigWorld
from gui.shared.gui_items.processors.vehicle import VehicleBuyer, VehicleSlotBuyer
from account_helpers.AccountSettings import AccountSettings, VEHICLE_BUY_WINDOW_SETTINGS
from debug_utils import LOG_ERROR
from gui.ClientUpdateManager import g_clientUpdateManager
from gui.Scaleform.daapi.view.meta.VehicleBuyWindowMeta import VehicleBuyWindowMeta
from gui.Scaleform.daapi.view.meta.WindowViewMeta import WindowViewMeta
from gui.Scaleform.framework import AppRef
from gui.Scaleform.framework.entities.View import View
from gui import SystemMessages
from gui.shared import g_itemsCache
from gui.shared.utils import decorators
from gui.shared.gui_items import GUI_ITEM_TYPE

class VehicleBuyWindow(View, VehicleBuyWindowMeta, AppRef, WindowViewMeta):

    def __init__(self, ctx):
        super(VehicleBuyWindow, self).__init__()
        self.nationID = ctx.get('nationID')
        self.inNationID = ctx.get('itemID')

    def _populate(self):
        super(VehicleBuyWindow, self)._populate()
        stats = g_itemsCache.items.stats
        self.as_setGoldS(stats.gold)
        self.as_setCreditsS(stats.credits)
        windowExpanded = AccountSettings.getSettings(VEHICLE_BUY_WINDOW_SETTINGS)
        vehicle = g_itemsCache.items.getItem(GUI_ITEM_TYPE.VEHICLE, self.nationID, self.inNationID)
        if vehicle is None:
            LOG_ERROR("Vehicle Item mustn't be None!", 'NationID:', self.nationID, 'InNationID:', self.inNationID)
            return
        else:
            tankMenStudyPrice = g_itemsCache.items.shop.tankmanCost
            tankMenCount = len(vehicle.crew)
            ammoPrice = [0, 0]
            for shell in vehicle.gun.defaultAmmo:
                ammoPrice[0] += shell.buyPrice[0] * shell.defaultCount
                ammoPrice[1] += shell.buyPrice[1] * shell.defaultCount

            initData = {'expanded': windowExpanded,
             'name': vehicle.userName,
             'longName': vehicle.longUserName,
             'description': vehicle.fullDescription,
             'type': vehicle.type,
             'icon': vehicle.icon,
             'nation': self.nationID,
             'level': vehicle.level,
             'isElite': vehicle.isElite,
             'tankmenCount': tankMenCount,
             'studyPriceCredits': tankMenStudyPrice[1]['credits'] * tankMenCount,
             'studyPriceGold': tankMenStudyPrice[2]['gold'] * tankMenCount,
             'vehiclePrices': vehicle.buyPrice,
             'ammoPrice': ammoPrice[0],
             'slotPrice': g_itemsCache.items.shop.getVehicleSlotsPrice(stats.vehicleSlots)}
            self.as_setInitDataS(initData)
            g_clientUpdateManager.addCallbacks({'stats.credits': self.__setCreditsCallBack,
             'stats.gold': self.__setGoldCallBack})
            return

    def storeSettings(self, expanded):
        AccountSettings.setSettings(VEHICLE_BUY_WINDOW_SETTINGS, expanded)

    @decorators.process('buyItem')
    def submit(self, data):
        vehicle = g_itemsCache.items.getItem(GUI_ITEM_TYPE.VEHICLE, self.nationID, self.inNationID)
        if data.buySlot:
            result = yield VehicleSlotBuyer(showConfirm=False, showWarning=False).request()
            if len(result.userMsg):
                SystemMessages.g_instance.pushI18nMessage(result.userMsg, type=result.sysMsgType)
            if not result.success:
                return
        result = yield VehicleBuyer(vehicle, data.buySlot, data.buyAmmo, data.crewType).request()
        if len(result.userMsg):
            SystemMessages.g_instance.pushI18nMessage(result.userMsg, type=result.sysMsgType)
        if result.success:
            self.storeSettings(data.isHasBeenExpanded)
            self.onWindowClose()

    def onWindowClose(self):
        self.destroy()

    def __setGoldCallBack(self, gold):
        self.as_setGoldS(gold)

    def __setCreditsCallBack(self, credits):
        self.as_setCreditsS(credits)

    def _dispose(self):
        g_clientUpdateManager.removeObjectCallbacks(self)
        super(VehicleBuyWindow, self)._dispose()

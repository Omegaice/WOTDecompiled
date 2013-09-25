import BigWorld
from adisp import process, async
from gui import SystemMessages
from gui.ClientUpdateManager import g_clientUpdateManager
from gui.Scaleform import getVehicleTypeAssetPath, getNationsAssetPath, NATION_ICON_PREFIX_131x31
from gui.Scaleform.daapi.view.lobby.exchange.BaseExchangeWindow import BaseExchangeWindow
from gui.Scaleform.daapi.view.meta.ExchangeXpWindowMeta import ExchangeXpWindowMeta
from gui.Scaleform.daapi.view.dialogs import HtmlMessageDialogMeta
from gui.shared.utils.gui_items import VEHICLE_ELITE_STATE, getVehicleEliteState, getItemByCompact, formatPrice
from gui.shared.utils.requesters import StatsRequester, Requester, ItemsRequester
from helpers.i18n import makeString
from gui import DialogsInterface
__author__ = 'y_valasevich'
from gui.Scaleform.Waiting import Waiting

class ExchangeXPWindow(BaseExchangeWindow, ExchangeXpWindowMeta):

    @process
    def _populate(self):
        inventory = yield ItemsRequester().request()
        stats = inventory.stats
        self.as_setPrimaryCurrencyS(stats.gold)
        shop = inventory.shop
        self.as_exchangeRateS(shop.freeXPConversion[0], shop.freeXPConversion[0])
        self.as_totalExperienceChangedS(stats.freeXP)
        self.__prepareAndPassVehiclesData()
        super(ExchangeXPWindow, self)._populate()

    def _subscribe(self):
        g_clientUpdateManager.addCallbacks({'stats.gold': self._setGoldCallBack,
         'shop.freeXPConversion': self.__setXPConversationCallBack,
         'inventory.1': self.__vehiclesDataChangedCallBack,
         'stats.vehTypeXP': self.__vehiclesDataChangedCallBack,
         'stats.freeXP': self.__setFreeXPCallBack})

    def __vehiclesDataChangedCallBack(self, data):
        self.__prepareAndPassVehiclesData()

    def __setFreeXPCallBack(self, value):
        self.as_totalExperienceChangedS(value)

    def __setXPConversationCallBack(self, exchangeXpRate):
        self.as_exchangeRateS(exchangeXpRate[0], exchangeXpRate[0])

    @process
    def __prepareAndPassVehiclesData(self):
        Waiting.show('loadStats')
        eliteVcls = yield StatsRequester().getEliteVehicles()
        isHaveElite = False
        myVehiclesInHangar = yield Requester('vehicle').getFromInventory()
        for myVehicle in myVehiclesInHangar:
            isHaveElite = myVehicle.isGroupElite(eliteVcls)
            if isHaveElite:
                break

        xps = yield StatsRequester().getVehicleTypeExperiences()
        vcls = yield Requester('vehicle').getFromShop()

        def getSmallIcon(vehType):
            return '../maps/icons/vehicle/small/%s.png' % vehType.name.replace(':', '-')

        values = []
        unlocks = yield StatsRequester().getUnlocks()
        for vehicle in vcls:
            if vehicle.descriptor.type.compactDescr in eliteVcls:
                xp = xps.get(vehicle.descriptor.type.compactDescr, 0)
                isSelectCandidate = getVehicleEliteState(vehicle, eliteVcls, unlocks) == VEHICLE_ELITE_STATE.FULLY_ELITE
                if not xp:
                    continue
                vehicleInfo = dict(id=vehicle.pack(), vehicleType=getVehicleTypeAssetPath(vehicle.type), vehicleName=vehicle.shortName, xp=xp, isSelectCandidate=isSelectCandidate, vehicleIco=getSmallIcon(vehicle.descriptor.type), nationIco=getNationsAssetPath(vehicle.nation, namePrefix=NATION_ICON_PREFIX_131x31))
                values.append(vehicleInfo)

        self.as_vehiclesDataChangedS(isHaveElite, values)
        Waiting.hide('loadStats')

    @process
    def exchange(self, data):
        exchangeXP = data.exchangeXp
        vclsCompacts = list(data.selectedVehicles)
        vehTypeCompDescrs = [ getItemByCompact(x).descriptor.type.compactDescr for x in vclsCompacts ]
        success = yield self.__exchangeVehicleXP(exchangeXP, vehTypeCompDescrs)
        if success:
            self.destroy()

    @async
    @process
    def __exchangeVehicleXP(self, exchangeXP, vehTypeCompDescrs, callback):
        vcls = yield Requester('vehicle').getFromShop()
        eliteVcls = yield StatsRequester().getEliteVehicles()
        xps = yield StatsRequester().getVehicleTypeExperiences()
        rate = yield StatsRequester().getFreeXPConversion()
        common_xp = 0
        for vehicle in vcls:
            if vehicle.descriptor.type.compactDescr in eliteVcls:
                common_xp += xps.get(vehicle.descriptor.type.compactDescr, 0)

        xpToExchange = min(common_xp, exchangeXP)
        goldToExchange = round(rate[1] * exchangeXP / rate[0])
        success = False
        isConfirmed = yield DialogsInterface.showI18nConfirmDialog('exchangeXPConfirmation', meta=HtmlMessageDialogMeta('html_templates:lobby/dialogs', 'confirmExchangeXP', {'resultCurrencyAmount': BigWorld.wg_getIntegralFormat(xpToExchange),
         'primaryCurrencyAmount': BigWorld.wg_getGoldFormat(goldToExchange)}))
        if isConfirmed:
            Waiting.show('exchangeVehiclesXP')
            success = yield StatsRequester().convertVehiclesXP(exchangeXP, vehTypeCompDescrs)
            if success:
                SystemMessages.g_instance.pushI18nMessage('#system_messages:exchangeXP/success', BigWorld.wg_getIntegralFormat(exchangeXP), formatPrice((0, goldToExchange)), type=SystemMessages.SM_TYPE.FinancialTransactionWithGold)
            else:
                SystemMessages.pushI18nMessage(makeString('#system_messages:exchangeVehiclesXP/server_error') % int(exchangeXP))
            Waiting.hide('exchangeVehiclesXP')
        callback(success)

    def onWindowClose(self):
        self.destroy()

    def _dispose(self):
        g_clientUpdateManager.removeObjectCallbacks(self)
        super(ExchangeXPWindow, self)._dispose()

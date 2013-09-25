# Embedded file name: scripts/client/gui/shared/gui_items/processors/vehicle.py
import BigWorld
import AccountCommands
from debug_utils import LOG_DEBUG
from AccountCommands import VEHICLE_SETTINGS_FLAG
from gui.SystemMessages import SM_TYPE
from gui.shared import g_itemsCache
from gui.shared.utils.gui_items import formatPrice, getPurchaseSysMessageType
from gui.shared.gui_items.processors import ItemProcessor, Processor, makeI18nSuccess, makeI18nError, plugins, makeSuccess

class VehicleBuyer(ItemProcessor):

    def __init__(self, vehicle, buySlot, buyShell = False, crewType = -1):
        self.price = self.__sumBuyPrice(vehicle, buyShell, crewType)
        super(VehicleBuyer, self).__init__(vehicle, (plugins.VehicleValidator(vehicle),
         plugins.MoneyValidator(self.price),
         plugins.VehicleSlotsConfirmator(not buySlot),
         plugins.VehicleFreeLimitConfirmator(vehicle, crewType)))
        self.buyShell = buyShell
        self.buyCrew = crewType != -1
        self.crewType = crewType
        self.vehicle = vehicle

    def _errorHandler(self, code, errStr = '', ctx = None):
        if not len(errStr):
            msg = 'vehicle_buy/server_error' if code != AccountCommands.RES_CENTER_DISCONNECTED else 'vehicle_buy/server_error_centerDown'
        else:
            msg = 'vehicle_buy/%s' % errStr
        return makeI18nError(msg, vehName=self.item.userName)

    def _successHandler(self, code, ctx = None):
        return makeI18nSuccess('vehicle_buy/success', vehName=self.item.userName, price=formatPrice(self.price), type=self.__getSysMsgType())

    def _request(self, callback):
        LOG_DEBUG('Make request to buy vehicle', self.vehicle, self.crewType, self.buyShell, self.price)
        BigWorld.player().shop.buyVehicle(self.item.nationID, self.item.innationID, self.buyShell, self.buyCrew, self.crewType, lambda code: self._response(code, callback))

    def __getSysMsgType(self):
        if self.item.buyPrice[0] > 0:
            return SM_TYPE.PurchaseForCredits
        return SM_TYPE.PurchaseForGold

    def __sumBuyPrice(self, vehicle, buyShells, crewType):
        result = list(vehicle.buyPrice)
        if crewType != -1:
            tankmenCount = len(vehicle.crew)
            tankmanCost = g_itemsCache.items.shop.tankmanCost[crewType]
            result[0] += tankmanCost['credits'] * tankmenCount
            result[1] += tankmanCost['gold'] * tankmenCount
        if buyShells:
            for shell in vehicle.gun.defaultAmmo:
                result[0] += shell.buyPrice[0] * shell.defaultCount
                result[1] += shell.buyPrice[1] * shell.defaultCount

        return result


class VehicleSlotBuyer(Processor):

    def __init__(self, showConfirm = True, showWarning = True):
        slotCost = self.__getSlotPrice()
        super(VehicleSlotBuyer, self).__init__((plugins.MessageInformator('buySlotNotEnoughCredits', activeHandler=lambda : not plugins.MoneyValidator(slotCost).validate().success, isEnabled=showWarning), plugins.MessageConfirmator('buySlotConfirmation', isEnabled=showConfirm, ctx={'gold': slotCost[1]})))

    def _errorHandler(self, code, errStr = '', ctx = None):
        return makeI18nError('vehicle_slot_buy/server_error')

    def _successHandler(self, code, ctx = None):
        return makeI18nSuccess('vehicle_slot_buy/success', money=formatPrice(self.__getSlotPrice()), type=SM_TYPE.FinancialTransactionWithGold)

    def _request(self, callback):
        LOG_DEBUG('Attempt to request server for buying vehicle slot')
        BigWorld.player().stats.buySlot(lambda code: self._response(code, callback))

    def __getSlotPrice(self):
        return (0, g_itemsCache.items.shop.getVehicleSlotsPrice(g_itemsCache.items.stats.vehicleSlots))


class VehicleSeller(ItemProcessor):

    def __init__(self, vehicle, dismantlingGoldCost, shells = [], eqs = [], optDevs = [], inventory = [], isCrewDismiss = False):
        self.gainMoney, self.spendMoney = self.__getGainSpendMoney(vehicle, shells, eqs, optDevs, inventory, dismantlingGoldCost)
        barracksBerthsNeeded = len(filter(lambda item: item is not None, vehicle.crew))
        super(VehicleSeller, self).__init__(vehicle, (plugins.VehicleValidator(vehicle),
         plugins.MoneyValidator(self.spendMoney),
         plugins.VehicleSellsLeftValidator(vehicle),
         plugins.BarracksSlotsValidator(barracksBerthsNeeded, isEnabled=not isCrewDismiss),
         plugins.MessageConfirmator('vehicleSell/unique', isEnabled=vehicle.isUnique)))
        self.vehicle = vehicle
        self.shells = shells
        self.eqs = eqs
        self.optDevs = optDevs
        self.inventory = inventory
        self.isCrewDismiss = isCrewDismiss
        self.isDismantlingForGold = self.__dismantlingForGoldDevicesCount(vehicle, optDevs) > 0

    def _errorHandler(self, code, errStr = '', ctx = None):
        if len(errStr):
            return makeI18nError('vehicle_sell/%s' % errStr, vehName=self.vehicle.userName)
        return makeI18nError('vehicle_sell/server_error', vehName=self.vehicle.userName)

    def _successHandler(self, code, ctx = None):
        if self.isDismantlingForGold:
            return makeI18nSuccess('vehicle_sell/success_dismantling', vehName=self.vehicle.userName, gainMoney=formatPrice(self.gainMoney), spendMoney=formatPrice(self.spendMoney), type=SM_TYPE.Selling)
        else:
            return makeI18nSuccess('vehicle_sell/success', vehName=self.vehicle.userName, money=formatPrice(self.gainMoney), type=SM_TYPE.Selling)

    def _request(self, callback):
        itemsFromVehicle = list()
        itemsFromInventory = list()
        isSellShells = len(self.shells) > 0
        for shell in self.shells:
            itemsFromVehicle.append(shell.intCD)

        isSellEqs = len(self.eqs) > 0
        for eq in self.eqs:
            itemsFromVehicle.append(eq.intCD)

        isSellFromInv = len(self.inventory) > 0
        for module in self.inventory:
            itemsFromInventory.append(module.intCD)

        isSellOptDevs = len(self.optDevs) > 0
        for dev in self.optDevs:
            itemsFromVehicle.append(dev.intCD)

        LOG_DEBUG('Make server request:', self.vehicle.invID, isSellShells, isSellEqs, isSellFromInv, isSellOptDevs, self.isDismantlingForGold, self.isCrewDismiss, itemsFromVehicle, itemsFromInventory)
        BigWorld.player().inventory.sellVehicle(self.vehicle.invID, self.isCrewDismiss, itemsFromVehicle, itemsFromInventory, lambda code: self._response(code, callback))

    def __dismantlingForGoldDevicesCount(self, vehicle, optDevicesToSell):
        result = 0
        if vehicle is None:
            return result
        else:
            optDevicesToSell = [ dev.intCD for dev in optDevicesToSell ]
            for dev in vehicle.optDevices:
                if dev is None:
                    continue
                if not dev.isRemovable and dev.intCD not in optDevicesToSell:
                    result += 1

            return result

    def __getGainSpendMoney(self, vehicle, vehShells, vehEqs, vehOptDevs, inventory, dismantlingGoldCost):
        moneyGain = vehicle.sellPrice
        for shell in vehShells:
            self.__accumulatePrice(moneyGain, shell.sellPrice, shell.count)

        for module in vehEqs + vehOptDevs:
            self.__accumulatePrice(moneyGain, module.sellPrice)

        for module in inventory:
            self.__accumulatePrice(moneyGain, module.sellPrice, module.inventoryCount)

        moneySpend = (0, self.__dismantlingForGoldDevicesCount(vehicle, vehOptDevs) * dismantlingGoldCost)
        return (moneyGain, moneySpend)

    def __accumulatePrice(self, result, price, count = 1):
        for i in xrange(2):
            result[i] += price[i] * count

        return result


class VehicleSettingsProcessor(ItemProcessor):

    def __init__(self, vehicle, setting, value, plugins = list()):
        self._setting = setting
        self._value = value
        super(VehicleSettingsProcessor, self).__init__(vehicle, plugins)

    def _request(self, callback):
        LOG_DEBUG('Make server request for changing vehicle settings', self.item, self._setting, bool(self._value))
        BigWorld.player().inventory.changeVehicleSetting(self.item.invID, self._setting, bool(self._value), lambda code: self._response(code, callback))


class VehicleTmenXPAccelerator(VehicleSettingsProcessor):

    def __init__(self, vehicle, value):
        super(VehicleTmenXPAccelerator, self).__init__(vehicle, VEHICLE_SETTINGS_FLAG.XP_TO_TMAN, value, (plugins.VehicleValidator(vehicle), plugins.MessageConfirmator('xpToTmenCheckbox', isEnabled=value)))

    def _errorHandler(self, code, errStr = '', ctx = None):
        if len(errStr):
            return makeI18nError('vehicle_tmenxp_accelerator/%s' % errStr, vehName=self.item.userName)
        return makeI18nError('vehicle_tmenxp_accelerator/server_error', vehName=self.item.userName)

    def _successHandler(self, code, ctx = None):
        return makeI18nSuccess('vehicle_tmenxp_accelerator/success' + str(self._value), vehName=self.item.userName, type=SM_TYPE.Information)


class VehicleFavoriteProcessor(VehicleSettingsProcessor):

    def __init__(self, vehicle, value):
        super(VehicleFavoriteProcessor, self).__init__(vehicle, VEHICLE_SETTINGS_FLAG.GROUP_0, value)

    def _errorHandler(self, code, errStr = '', ctx = None):
        if len(errStr):
            return makeI18nError('vehicle_favorite/%s' % errStr, vehName=self.item.userName)
        return makeI18nError('vehicle_favorite/server_error', vehName=self.item.userName)

    def _successHandler(self, code, ctx = None):
        return makeI18nSuccess('vehicle_favorite/success' + str(self._value), vehName=self.item.userName, type=SM_TYPE.Information)


class VehicleLayoutProcessor(Processor):
    """
    Apply equipments and shells layout
    """

    def __init__(self, vehicle, shellsLayout = None, eqsLayout = None):
        """
        Ctor.
        
        @param vehicle: vehicle
        @param shellsLayout: shells
        @param eqsLayout: equipments
        """
        super(VehicleLayoutProcessor, self).__init__()
        self.vehicle = vehicle
        self.shellsLayout = shellsLayout or []
        self.eqsLayout = eqsLayout or []

    def _request(self, callback):
        BigWorld.player().inventory.setAndFillLayouts(self.vehicle.invID, self.shellsLayout, self.eqsLayout, lambda code, errStr, ext: self._response(code, callback, errStr=errStr, ctx=ext))

    def _successHandler(self, code, ctx = None):
        additionalMessages = []
        if len(ctx.get('shells', [])):
            totalPrice = [0, 0]
            for shellCompDescr, price, count in ctx.get('shells', []):
                shell = g_itemsCache.items.getItemByCD(shellCompDescr)
                additionalMessages.append(makeI18nSuccess('shell_buy/success', name=shell.userName, count=count, money=formatPrice(price), type=getPurchaseSysMessageType(price)))
                totalPrice[0] += price[0]
                totalPrice[1] += price[1]

            additionalMessages.append(makeI18nSuccess('layout_apply/success_money_spent', money=formatPrice(totalPrice), type=getPurchaseSysMessageType(totalPrice)))
        if len(ctx.get('eqs', [])):
            for eqCompDescr, price, count in ctx.get('eqs', []):
                equipment = g_itemsCache.items.getItemByCD(eqCompDescr)
                additionalMessages.append(makeI18nSuccess('artefact_buy/success', kind=equipment.userType, name=equipment.userName, count=count, money=formatPrice(price), type=getPurchaseSysMessageType(price)))

        return makeSuccess(auxData=additionalMessages)

    def _errorHandler(self, code, errStr = '', ctx = None):
        if not len(errStr):
            msg = 'server_error' if code != AccountCommands.RES_CENTER_DISCONNECTED else 'server_error_centerDown'
        else:
            msg = errStr
        return makeI18nError('layout_apply/%s' % msg, vehName=self.vehicle.userName, type=SM_TYPE.Error)
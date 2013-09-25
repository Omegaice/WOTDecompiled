from collections import namedtuple
from adisp import process, async
from gui import DialogsInterface
from gui.shared import g_itemsCache, REQ_CRITERIA
from gui.shared.gui_items import GUI_ITEM_TYPE
from gui.Scaleform.daapi.view.dialogs import I18nConfirmDialogMeta, I18nInfoDialogMeta, DIALOG_BUTTON_ID, IconPriceDialogMeta, IconDialogMeta, DemountDeviceDialogMeta, DestroyDeviceDialogMeta, DismissTankmanDialogMeta
PluginResult = namedtuple('PluginResult', 'success errorMsg ctx')

def makeSuccess(**kwargs):
    return PluginResult(True, '', kwargs)


def makeError(msg = '', **kwargs):
    return PluginResult(False, msg, kwargs)


class ProcessorPlugin(object):

    class TYPE:
        """ Plugins type. """
        VALIDATOR = 0
        CONFIRMATOR = 1

    def __init__(self, pluginType, isAsync = False, isEnabled = True):
        """
        Ctor.
        
        @param type: <ProcessorPlugin.TYPE.*> plugin type
        @param isAsync: <bool> asynchronous or not
        @param isEnabled: <bool> plugin enabled or not
        """
        self.type = pluginType
        self.isAsync = isAsync
        self.isEnabled = isEnabled


class SyncValidator(ProcessorPlugin):

    def __init__(self, isEnabled = True):
        super(SyncValidator, self).__init__(self.TYPE.VALIDATOR, isEnabled=isEnabled)

    def validate(self):
        return self._validate()

    def _validate(self):
        return makeSuccess()


class AsyncValidator(ProcessorPlugin):

    def __init__(self, isEnabled = True):
        super(AsyncValidator, self).__init__(self.TYPE.VALIDATOR, True, isEnabled=isEnabled)

    @async
    @process
    def validate(self, callback):
        result = yield self._validate()
        callback(result)

    @async
    def _validate(self, callback):
        callback(makeSuccess())


class AsyncConfirmator(ProcessorPlugin):

    def __init__(self, isEnabled = True):
        super(AsyncConfirmator, self).__init__(self.TYPE.CONFIRMATOR, True, isEnabled=isEnabled)

    @async
    @process
    def confirm(self, callback):
        result = yield self._confirm()
        callback(result)

    @async
    def _confirm(self, callback):
        callback(makeSuccess())


class VehicleValidator(SyncValidator):

    def __init__(self, vehicle, isEnabled = True):
        super(VehicleValidator, self).__init__(isEnabled)
        self.vehicle = vehicle

    def _validate(self):
        if not self.vehicle:
            return makeError('invalid_vehicle')
        if self.vehicle.isBroken:
            return makeError('vehicle_need_repair')
        if self.vehicle.isLocked:
            return makeError('vehicle_locked')
        return makeSuccess()


class VehicleLockValidator(SyncValidator):

    def __init__(self, vehicle, isEnabled = True):
        super(VehicleLockValidator, self).__init__(isEnabled)
        self.vehicle = vehicle

    def _validate(self):
        if not self.vehicle:
            return makeError('invalid_vehicle')
        if self.vehicle.isLocked:
            return makeError('vehicle_locked')
        return makeSuccess()


class ModuleValidator(SyncValidator):

    def __init__(self, module):
        super(ModuleValidator, self).__init__()
        self.module = module

    def _validate(self):
        if not self.module:
            return makeError('invalid_module')
        return makeSuccess()


class ModuleTypeValidator(SyncValidator):

    def __init__(self, module, allowableTypes):
        super(ModuleTypeValidator, self).__init__(self)
        self.module = module
        self.allowableTypes = allowableTypes

    def _validate(self):
        if self.module.itemTypeID not in self.allowableTypes:
            return makeError('invalid_module_type')
        return makeSuccess()


class CompatibilityValidator(SyncValidator):

    def __init__(self, vehicle, module, slotIdx = 0):
        super(CompatibilityValidator, self).__init__()
        self.vehicle = vehicle
        self.module = module
        self.slotIdx = slotIdx

    def _checkCompatibility(self):
        """
        @rtype : tuple
        """
        return makeSuccess()

    def _validate(self):
        success, errMsg = self._checkCompatibility()
        if not success:
            return makeError('error_%s' % errMsg.replace(' ', '_'))
        return makeSuccess()


class CompatibilityInstallValidator(CompatibilityValidator):

    def _checkCompatibility(self):
        return self.module.mayInstall(self.vehicle, self.slotIdx)


class TurretCompatibilityInstallValidator(SyncValidator):

    def __init__(self, vehicle, module, gunCD = 0):
        super(TurretCompatibilityInstallValidator, self).__init__()
        self.vehicle = vehicle
        self.module = module
        self.gunCD = gunCD

    def _checkCompatibility(self):
        """
        @rtype : tuple
        """
        return self.module.mayInstall(self.vehicle, 0, self.gunCD)

    def _validate(self):
        success, errMsg = self._checkCompatibility()
        if not success:
            return makeError('error_%s' % errMsg.replace(' ', '_'))
        return makeSuccess()


class CompatibilityRemoveValidator(CompatibilityValidator):

    def __init__(self, vehicle, module):
        super(CompatibilityRemoveValidator, self).__init__(vehicle, module)

    def _checkCompatibility(self):
        return self.module.mayRemove(self.vehicle)


class MoneyValidator(SyncValidator):

    def __init__(self, price):
        super(MoneyValidator, self).__init__()
        self.price = price

    def _validate(self):
        stats = g_itemsCache.items.stats
        if stats.credits < self.price[0]:
            return makeError('not_enough_credits')
        if stats.gold < self.price[1]:
            return makeError('not_enough_gold')
        return makeSuccess()


class VehicleSellsLeftValidator(SyncValidator):

    def __init__(self, vehicle):
        super(VehicleSellsLeftValidator, self).__init__()
        self.vehicle = vehicle

    def _validate(self):
        if g_itemsCache.items.stats.vehicleSellsLeft <= 0:
            return makeError('vehicle_sell_limit')
        return makeSuccess()


class BarracksSlotsValidator(SyncValidator):

    def __init__(self, berthsNeeded = 1, isEnabled = True):
        super(BarracksSlotsValidator, self).__init__(isEnabled)
        self.berthsNeeded = berthsNeeded

    def _validate(self):
        barracksTmen = g_itemsCache.items.getTankmen(~REQ_CRITERIA.TANKMAN.IN_TANK)
        tmenBerthsCount = g_itemsCache.items.stats.tankmenBerthsCount
        if self.berthsNeeded > 0 and self.berthsNeeded > tmenBerthsCount - len(barracksTmen):
            return makeError('not_enough_space')
        return makeSuccess()


class FreeTankmanValidator(SyncValidator):

    def _validate(self):
        if not g_itemsCache.items.stats.freeTankmenLeft:
            return makeError('free_tankmen_limit')
        return makeSuccess()


class DialogAbstractConfirmator(AsyncConfirmator):

    def __init__(self, activeHandler = None, isEnabled = True):
        super(DialogAbstractConfirmator, self).__init__(isEnabled=isEnabled)
        self.activeHandler = activeHandler or (lambda : True)

    def __del__(self):
        self.activeHandler = None
        return

    def _makeMeta(self):
        raise NotImplementedError

    @async
    def _showDialog(self, callback):
        callback(None)
        return

    def _activeHandler(self):
        return self.activeHandler()

    @async
    @process
    def _confirm(self, callback):
        yield lambda callback: callback(None)
        if self._activeHandler():
            isOk = yield DialogsInterface.showDialog(meta=self._makeMeta())
            if not isOk:
                callback(makeError())
                return
        callback(makeSuccess())


class I18nMessageAbstractConfirmator(DialogAbstractConfirmator):

    def __init__(self, localeKey, ctx = None, activeHandler = None, isEnabled = True):
        super(I18nMessageAbstractConfirmator, self).__init__(activeHandler, isEnabled)
        self.localeKey = localeKey
        self.ctx = ctx


class MessageConfirmator(I18nMessageAbstractConfirmator):

    def _makeMeta(self):
        return I18nConfirmDialogMeta(self.localeKey, self.ctx, self.ctx, focusedID=DIALOG_BUTTON_ID.SUBMIT)


class DismissTankmanConfirmator(I18nMessageAbstractConfirmator):

    def __init__(self, localeKey, tankman):
        super(DismissTankmanConfirmator, self).__init__(localeKey, tankman, None, True)
        return

    def _makeMeta(self):
        return DismissTankmanDialogMeta(self.localeKey, self.ctx, focusedID=DIALOG_BUTTON_ID.SUBMIT)


class IconPriceMessageConfirmator(I18nMessageAbstractConfirmator):
    """
    Invoke dialog window contains icon, text and component with price
    """

    def __init__(self, localeKey, ctx = None, activeHandler = None, isEnabled = True):
        super(IconPriceMessageConfirmator, self).__init__(localeKey, ctx, activeHandler, isEnabled)

    def _makeMeta(self):
        return IconPriceDialogMeta(self.localeKey, self.ctx, self.ctx, focusedID=DIALOG_BUTTON_ID.SUBMIT)


class DemountDeviceConfirmator(IconPriceMessageConfirmator):
    """
    Invoke dialog window contains icon, text and component with price
    """

    def __init__(self, localeKey, ctx = None, activeHandler = None, isEnabled = True):
        super(DemountDeviceConfirmator, self).__init__(localeKey, ctx, activeHandler, isEnabled)

    def _makeMeta(self):
        return DemountDeviceDialogMeta(self.localeKey, self.ctx, self.ctx, focusedID=DIALOG_BUTTON_ID.SUBMIT)


class IconMessageConfirmator(I18nMessageAbstractConfirmator):
    """
    Invoke dialog window contains icon, text and component with price
    """

    def __init__(self, localeKey, ctx = None, activeHandler = None, isEnabled = True):
        super(IconMessageConfirmator, self).__init__(localeKey, ctx, activeHandler, isEnabled)

    def _makeMeta(self):
        return IconDialogMeta(self.localeKey, self.ctx, self.ctx, focusedID=DIALOG_BUTTON_ID.SUBMIT)


class DestroyDeviceConfirmator(IconMessageConfirmator):
    __DESTROY_DEVICE_PATH = '../maps/icons/modules/destroyDevice.png'

    def __init__(self, localeKey, itemName = None, activeHandler = None, isEnabled = True):
        super(DestroyDeviceConfirmator, self).__init__(localeKey, {'name': itemName,
         'icon': self.__DESTROY_DEVICE_PATH}, activeHandler, isEnabled)

    def _makeMeta(self):
        return DestroyDeviceDialogMeta(self.localeKey, self.ctx, self.ctx, focusedID=DIALOG_BUTTON_ID.SUBMIT)


class MessageInformator(I18nMessageAbstractConfirmator):

    def _makeMeta(self):
        return I18nInfoDialogMeta(self.localeKey, self.ctx, self.ctx)


class VehicleSlotsConfirmator(MessageInformator):

    def __init__(self, isEnabled = True):
        super(VehicleSlotsConfirmator, self).__init__('haveNoEmptySlots', isEnabled=isEnabled)

    def _activeHandler(self):
        return g_itemsCache.items.stats.vehicleSlots <= len(g_itemsCache.items.getVehicles(REQ_CRITERIA.INVENTORY))


class VehicleFreeLimitConfirmator(MessageInformator):

    def __init__(self, vehicle, crewType):
        super(VehicleFreeLimitConfirmator, self).__init__('freeVehicleLeftLimit')
        self.vehicle = vehicle
        self.crewType = crewType

    def _activeHandler(self):
        return self.vehicle.buyPrice == (0, 0) and self.crewType < 1 and not g_itemsCache.items.stats.freeVehiclesLeft

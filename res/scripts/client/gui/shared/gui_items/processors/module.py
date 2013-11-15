# 2013.11.15 11:26:49 EST
# Embedded file name: scripts/client/gui/shared/gui_items/processors/module.py
import BigWorld
import itertools
import AccountCommands
from gui.Scaleform.locale.DIALOGS import DIALOGS
from helpers.i18n import makeString
from debug_utils import LOG_DEBUG
from gui.SystemMessages import SM_TYPE
from gui.shared import g_itemsCache, REQ_CRITERIA
from gui.shared.gui_items import GUI_ITEM_TYPE
from gui.shared.gui_items.processors import ItemProcessor, makeI18nSuccess, makeI18nError, VehicleItemProcessor, plugins, makeSuccess
from gui.shared.utils.gui_items import formatPrice, VehicleItem

class ModuleProcessor(ItemProcessor):
    """
    Root module processor
    """
    ITEMS_MSG_PREFIXES = {GUI_ITEM_TYPE.SHELL: 'shell',
     GUI_ITEM_TYPE.EQUIPMENT: 'artefact',
     GUI_ITEM_TYPE.OPTIONALDEVICE: 'artefact'}
    DEFAULT_PREFIX = 'module'

    def __init__(self, item, opType, plugs = tuple()):
        """
        Ctor.
        
        @param item: module to install
        @param opType: operation type
        @param plugs: plugins list
        """
        ItemProcessor.__init__(self, item, plugs + (plugins.ModuleValidator(item),))
        self.opType = opType

    def _getMsgCtx(self):
        raise NotImplemented

    def _formMessage(self, msg):
        LOG_DEBUG('Generating response for ModuleProcessor: ', self.opType, msg)
        return '%(itemType)s_%(opType)s/%(msg)s' % {'itemType': self.ITEMS_MSG_PREFIXES.get(self.item.itemTypeID, self.DEFAULT_PREFIX),
         'opType': self.opType,
         'msg': msg}


class ModuleTradeProcessor(ModuleProcessor):
    """
    Root module trade
    """

    def __init__(self, item, count, opType, plugs = tuple()):
        """
        Ctor.
        
        @param item: module to install
        @param count: buying count
        @param opType: operation type
        @param plugs: plugins list
        """
        super(ModuleTradeProcessor, self).__init__(item, opType, plugs)
        self.count = count

    def _getMsgCtx(self):
        return {'name': self.item.userName,
         'kind': self.item.userType,
         'count': BigWorld.wg_getIntegralFormat(int(self.count)),
         'money': formatPrice(self._getOpPrice())}

    def _getOpPrice(self):
        raise NotImplemented


class ModuleBuyer(ModuleTradeProcessor):
    """
    Module buyer
    """

    def __init__(self, item, count, buyForCredits, conflictedEqs = None, install = False):
        """
        Ctor.
        
        @param item: module to install
        @param count: buying count
        @param buyForCredits: buy gold item for credits
        @param conflictedEqs: conflicted items
        """
        super(ModuleBuyer, self).__init__(item, count, 'buy')
        if not conflictedEqs:
            conflictedEqs = []
            conflictMsg = ''
            conflictMsg = conflictedEqs and makeString(DIALOGS.BUYINSTALLCONFIRMATION_CONFLICTEDMESSAGE, conflicted="', '".join([ VehicleItem(descriptor=eq).name for eq in conflictedEqs ]))
        self.buyForCredits = buyForCredits
        self.addPlugins((plugins.MoneyValidator(self._getOpPrice()), plugins.MessageConfirmator('buyInstallConfirmation', ctx={'name': item.userName,
          'kind': self.item.userType,
          'conflict': conflictMsg,
          'price': self._getOpPrice()[0]}, isEnabled=install)))

    def _isItemBuyingForCredits(self):
        if self.buyForCredits:
            shop = g_itemsCache.items.shop
            if self.item.itemTypeID == GUI_ITEM_TYPE.SHELL and shop.isEnabledBuyingGoldShellsForCredits:
                return True
            if self.item.itemTypeID == GUI_ITEM_TYPE.EQUIPMENT and shop.isEnabledBuyingGoldEqsForCredits:
                return True
        return False

    def _getOpPrice(self):
        if self.buyForCredits:
            return (self.item.actionPrice[0] * self.count, 0)
        return (0, self.item.actionPrice[1] * self.count)

    def _successHandler(self, code, ctx = None):
        sysMsgType = SM_TYPE.PurchaseForCredits if self.buyForCredits else SM_TYPE.PurchaseForGold
        return makeI18nSuccess(self._formMessage('success'), type=sysMsgType, **self._getMsgCtx())

    def _errorHandler(self, code, errStr = '', ctx = None):
        if not len(errStr):
            msg = 'server_error' if code != AccountCommands.RES_CENTER_DISCONNECTED else 'server_error_centerDown'
        else:
            msg = errStr
        return makeI18nError(self._formMessage(msg), **self._getMsgCtx())

    def _request(self, callback):
        LOG_DEBUG('Make server request to buy module', self.item, self.count, self._isItemBuyingForCredits())
        BigWorld.player().shop.buy(self.item.itemTypeID, self.item.nationID, self.item.intCD, self.count, int(self._isItemBuyingForCredits()), lambda code: self._response(code, callback))


class ModuleSeller(ModuleTradeProcessor):
    """
    Module seller
    """

    def __init__(self, item, count):
        """
        Ctor.
        
        @param item: module to install
        @param count: module buying count
        """
        super(ModuleSeller, self).__init__(item, count, 'sell')

    def _getOpPrice(self):
        return (self.item.sellPrice[0] * self.count, self.item.sellPrice[1] * self.count)

    def _successHandler(self, code, ctx = None):
        return makeI18nSuccess(self._formMessage('success'), type=SM_TYPE.Selling, **self._getMsgCtx())

    def _errorHandler(self, code, errStr = '', ctx = None):
        if not len(errStr):
            msg = 'server_error' if code != AccountCommands.RES_CENTER_DISCONNECTED else 'server_error_centerDown'
        else:
            msg = errStr
        return makeI18nError(self._formMessage(msg), **self._getMsgCtx())

    def _request(self, callback):
        LOG_DEBUG('Make server request to sell item', self.item, self.count)
        BigWorld.player().inventory.sell(self.item.itemTypeID, self.item.intCompactDescr, self.count, lambda code: self._response(code, callback))


class ModuleInstallProcessor(ModuleProcessor, VehicleItemProcessor):
    """
    Root modules installer.
    """

    def __init__(self, vehicle, item, itemType, slotIdx, install = True, conflictedEqs = None, plugs = tuple()):
        """
        Ctor.
        
        @param vehicle: vehicle
        @param item: module to install
        @param slotIdx: vehicle equipment slot index to install
        @param itemType: item type
        @param install: flag to designated process
        @param conflictedEqs: conflicted items
        @param plugs: plugins list
        """
        opType = 'apply' if install else 'remove'
        if not conflictedEqs:
            conflictedEqs = tuple()
            ModuleProcessor.__init__(self, item=item, opType=opType, plugs=plugs)
            VehicleItemProcessor.__init__(self, vehicle=vehicle, module=item, allowableTypes=itemType)
            addPlugins = []
            install and addPlugins += (plugins.CompatibilityInstallValidator(vehicle, item, slotIdx), plugins.MessageConfirmator('removeIncompatibleEqs', ctx={'name': "', '".join([ VehicleItem(descriptor=eq).name for eq in conflictedEqs ])}, isEnabled=bool(conflictedEqs)))
        else:
            addPlugins += (plugins.CompatibilityRemoveValidator(vehicle, item),)
        self.install = install
        self.slotIdx = slotIdx
        self.addPlugins(addPlugins)

    def _getMsgCtx(self):
        return {'name': self.item.userName,
         'kind': self.item.userType}

    def _successHandler(self, code, ctx = None):
        return makeI18nSuccess(self._formMessage('success'), type=SM_TYPE.Information, **self._getMsgCtx())

    def _errorHandler(self, code, errStr = '', ctx = None):
        if not len(errStr):
            msg = 'server_error' if code != AccountCommands.RES_CENTER_DISCONNECTED else 'server_error_centerDown'
        else:
            msg = errStr
        return makeI18nError(self._formMessage(msg), **self._getMsgCtx())


class OptDeviceInstaller(ModuleInstallProcessor):
    """
    Vehicle opt devices installer.
    """

    def __init__(self, vehicle, item, slotIdx, install = True, isUseGold = False, conflictedEqs = None):
        """
        Ctor.
        
        @param vehicle: vehicle
        @param item: module to install
        @param slotIdx: vehicle equipment slot index to install
        @param install: flag to designated process
        @param conflictedEqs: conflicted items
        """
        super(OptDeviceInstaller, self).__init__(vehicle, item, (GUI_ITEM_TYPE.OPTIONALDEVICE,), slotIdx, install, conflictedEqs)
        self.cost = g_itemsCache.items.shop.paidRemovalCost
        addPlugins = []
        if install:
            addPlugins += (plugins.MessageConfirmator('installConfirmationNotRemovable', ctx={'name': item.userName}, isEnabled=not item.isRemovable),)
        else:
            addPlugins += (plugins.DemountDeviceConfirmator('removeConfirmationNotRemovableGold', ctx={'name': item.userName,
              'price': self.cost}, isEnabled=not item.isRemovable and isUseGold), plugins.DestroyDeviceConfirmator('removeConfirmationNotRemovable', itemName=item.userName, isEnabled=not item.isRemovable and not isUseGold))
        self.addPlugins(addPlugins)
        self.useGold = isUseGold

    def _successHandler(self, code, ctx = None):
        item = self.item if self.install else None
        self.vehicle.optDevices[self.slotIdx] = item
        if not self.install and not self.item.isRemovable and self.useGold:
            return makeI18nSuccess(self._formMessage('gold_success'), type=SM_TYPE.DismantlingForGold, **self._getMsgCtx())
        else:
            return super(OptDeviceInstaller, self)._successHandler(code, ctx)

    def _request(self, callback):
        itemCD = self.item.intCD if self.install else 0
        BigWorld.player().inventory.equipOptionalDevice(self.vehicle.invID, itemCD, self.slotIdx, self.useGold, lambda code: self._response(code, callback))

    def _getMsgCtx(self):
        return {'name': self.item.userName,
         'kind': self.item.userType,
         'money': self.cost}


class EquipmentInstaller(ModuleInstallProcessor):
    """
    Vehicle equipment installer.
    """

    def __init__(self, vehicle, item, slotIdx, install = True, conflictedEqs = None):
        """
        Ctor.
        
        @param vehicle: vehicle
        @param item: equipment to install
        @param slotIdx: vehicle equipment slot index to install
        @param install: flag to designated process
        @param conflictedEqs: conflicted items
        """
        super(EquipmentInstaller, self).__init__(vehicle, item, (GUI_ITEM_TYPE.EQUIPMENT,), slotIdx, install, conflictedEqs)

    def _successHandler(self, code, ctx = None):
        item = self.item if self.install else None
        self.vehicle.eqs[self.slotIdx] = item
        return super(EquipmentInstaller, self)._successHandler(code, ctx)

    def _request(self, callback):
        itemCD = self.item.intCD if self.install else 0
        newEqsLayout = map(lambda item: (item.intCD if item is not None else 0), self.vehicle.eqs)
        newEqsLayout[self.slotIdx] = itemCD
        BigWorld.player().inventory.equipEquipments(self.vehicle.invID, newEqsLayout, lambda code: self._response(code, callback))


class CommonModuleInstallProcessor(ModuleProcessor, VehicleItemProcessor):
    """
    Vehicle other modules installer.
    """

    def __init__(self, vehicle, item, itemType, install = True, conflictedEqs = None, plugs = tuple()):
        """
        Ctor.
        
        @param vehicle: vehicle
        @param item: equipment to install
        @param itemType: vehicle module type
        @param install: flag to designated process
        @param conflictedEqs: conflicted items
        @param plugs: plugins list
        """
        opType = 'apply' if install else 'remove'
        if not conflictedEqs:
            conflictedEqs = tuple()
            ModuleProcessor.__init__(self, item=item, opType=opType, plugs=plugs)
            VehicleItemProcessor.__init__(self, vehicle=vehicle, module=item, allowableTypes=itemType)
            install and self.addPlugin(plugins.MessageConfirmator('removeIncompatibleEqs', ctx={'name': "', '".join([ VehicleItem(descriptor=eq).name for eq in conflictedEqs ])}, isEnabled=bool(conflictedEqs)))
        self.install = install

    def _getMsgCtx(self):
        return {'name': self.item.userName,
         'kind': self.item.userType}

    def _successHandler(self, code, ctx = None):
        additionalMessages = []
        removedItems = []
        for eqKd in ctx.get('incompatibleEqs', []):
            item = VehicleItem(compactDescr=eqKd)
            removedItems.append(item.name)

        if removedItems:
            additionalMessages.append(makeI18nSuccess(self._formMessage('incompatibleEqs'), items="', '".join(removedItems), type=SM_TYPE.Information))
        additionalMessages.append(makeI18nSuccess(self._formMessage('success'), type=SM_TYPE.Information, auxData=additionalMessages, **self._getMsgCtx()))
        return makeSuccess(auxData=additionalMessages)

    def _errorHandler(self, code, errStr = '', ctx = None):
        if not len(errStr):
            msg = 'server_error' if code != AccountCommands.RES_CENTER_DISCONNECTED else 'server_error_centerDown'
        else:
            msg = errStr
        return makeI18nError(self._formMessage(msg), **self._getMsgCtx())


class TurretInstaller(CommonModuleInstallProcessor):
    """
    Vehicle turret installer.
    """

    def __init__(self, vehicle, item, conflictedEqs = None):
        """
        Ctor.
        
        @param vehicle: vehicle
        @param item: equipment to install
        @param conflictedEqs: conflicted items
        """
        super(TurretInstaller, self).__init__(vehicle, item, (GUI_ITEM_TYPE.TURRET,), True, conflictedEqs)
        self.gunCD = 0
        mayInstallCurrent = item.mayInstall(vehicle, slotIdx=0, gunCD=self.gunCD)
        if not mayInstallCurrent[0]:
            iGuns = sorted(g_itemsCache.items.getItems(REQ_CRITERIA.VEHICLE.SUITABLE([vehicle], [GUI_ITEM_TYPE.GUN]) | REQ_CRITERIA.INVENTORY).keys(), reverse=True)
            for gun in itertools.ifilter(lambda x: x['compactDescr'] in iGuns, item.descriptor['guns']):
                mayInstall = item.mayInstall(vehicle, slotIdx=0, gunCD=gun['compactDescr'])
                if mayInstall[0]:
                    self.gunCD = gun['compactDescr']
                    break

        self.addPlugin(plugins.TurretCompatibilityInstallValidator(vehicle, item, self.gunCD))

    def _request(self, callback):
        BigWorld.player().inventory.equipTurret(self.vehicle.invID, self.item.intCD, self.gunCD, lambda code, ext: self._response(code, callback, ctx=ext))

    def _successHandler(self, code, ctx = None):
        if self.gunCD:
            gun = g_itemsCache.items.getItemByCD(self.gunCD)
            return makeI18nSuccess(self._formMessage('success_gun_change'), type=SM_TYPE.Information, gun=gun.userName, **self._getMsgCtx())
        return super(TurretInstaller, self)._successHandler(code, ctx)


class OtherModuleInstaller(CommonModuleInstallProcessor):
    """
    Vehicle rest modules installer: sheels, fuel tanks, etc.
    """

    def __init__(self, vehicle, item, conflictedEqs = None):
        """
        Ctor.
        
        @param vehicle: vehicle
        @param item: equipment to install
        @param conflictedEqs: conflicted items
        """
        super(OtherModuleInstaller, self).__init__(vehicle, item, (GUI_ITEM_TYPE.CHASSIS,
         GUI_ITEM_TYPE.GUN,
         GUI_ITEM_TYPE.ENGINE,
         GUI_ITEM_TYPE.FUEL_TANK,
         GUI_ITEM_TYPE.RADIO,
         GUI_ITEM_TYPE.SHELL), True, conflictedEqs)
        self.addPlugin(plugins.CompatibilityInstallValidator(vehicle, item, 0))

    def _request(self, callback):
        LOG_DEBUG('Request to equip module', self.vehicle, self.item)
        BigWorld.player().inventory.equip(self.vehicle.invID, self.item.intCD, lambda code, ext: self._response(code, callback, ctx=ext))


def getInstallerProcessor(vehicle, newComponentItem, slotIdx = 0, install = True, isUseGold = False, conflictedEqs = None):
    """
    Select proper installer by type
    """
    if newComponentItem.itemTypeID == GUI_ITEM_TYPE.EQUIPMENT:
        return EquipmentInstaller(vehicle, newComponentItem, slotIdx, install, conflictedEqs)
    elif newComponentItem.itemTypeID == GUI_ITEM_TYPE.OPTIONALDEVICE:
        return OptDeviceInstaller(vehicle, newComponentItem, slotIdx, install, isUseGold, conflictedEqs)
    elif newComponentItem.itemTypeID != GUI_ITEM_TYPE.TURRET:
        return OtherModuleInstaller(vehicle, newComponentItem, conflictedEqs)
    else:
        return TurretInstaller(vehicle, newComponentItem, conflictedEqs)
# okay decompyling res/scripts/client/gui/shared/gui_items/processors/module.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:26:50 EST

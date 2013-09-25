from functools import partial
import BigWorld
from AccountCommands import RES_SUCCESS
from debug_utils import LOG_ERROR, LOG_DEBUG
import enumerations
from gui import SystemMessages, DialogsInterface
from gui.Scaleform.daapi.view.meta.ResearchViewMeta import ResearchViewMeta
from gui.Scaleform.framework import AppRef
from gui.Scaleform.daapi.view.dialogs import HtmlMessageDialogMeta, SimpleDialogMeta
from gui.Scaleform.framework.entities.View import View
from gui.Scaleform.daapi.view.lobby.techtree import _VEHICLE, _RESEARCH_ITEMS, NODE_STATE, RequestState
from gui.shared import events
from gui.shared.utils import gui_items
from gui.Scaleform.Waiting import Waiting
from gui.shared.utils.gui_items import getItemByCompact
from items import getTypeInfoByIndex, vehicles
from helpers import i18n

class ResearchView(View, ResearchViewMeta, AppRef):
    MSG_SCOPE = enumerations.Enumeration('Message scope', [('Unlocks', lambda entity, msg: '#system_messages:unlocks/{0:>s}/{1:>s}'.format(entity, msg)),
     ('Shop', lambda entity, msg: '#system_messages:shop/{0:>s}/{1:>s}'.format(entity, msg)),
     ('Inventory', lambda entity, msg: '#system_messages:inventory/{0:>s}/{1:>s}'.format(entity, msg)),
     ('Dialog', lambda entity, msg: '#dialogs:techtree/{0:>s}/{1:>s}'.format(entity, msg))], instance=enumerations.CallabbleEnumItem)

    def __init__(self, data):
        super(ResearchView, self).__init__()
        self._data = data

    def _dispose(self):
        super(ResearchView, self)._dispose()
        if self._data is not None:
            self._data.clear()
            self._data = None
        return

    def showModuleInfo(self, pickleDump):
        if pickleDump is None:
            LOG_ERROR('There is error while attempting to show module info window: ', str(pickleDump))
        vehicleDescr = self._data.getItem(self._data.getRootCD()).descriptor
        self.fireEvent(events.ShowWindowEvent(events.ShowWindowEvent.SHOW_MODULE_INFO_WINDOW, {'moduleId': pickleDump,
         'vehicleDescr': vehicleDescr}))
        return

    def showVehicleInfo(self, pickleDump):
        vehicle = getItemByCompact(pickleDump)
        if vehicle is None:
            LOG_ERROR('There is error while attempting to show vehicle info window: ', str(pickleDump))
            return
        else:
            self.fireEvent(events.ShowWindowEvent(events.ShowWindowEvent.SHOW_VEHICLE_INFO_WINDOW, {'vehicleDescr': vehicle.descriptor}))
            return

    def unlockItem(self, unlockCD, vehCD, unlockIdx, xpCost):
        if self._validateItem2Unlock(unlockCD, vehCD, unlockIdx, xpCost):
            costCtx = self._getXPCostCtx(self._data.getVehXP(vehCD), xpCost)
            DialogsInterface.showI18nConfirmDialog('confirmUnlock', partial(self._doUnlockItem, unlockCD, vehCD, unlockIdx, xpCost), meta=self._getUnlockConfirmMeta(unlockCD, costCtx))

    def buyVehicle(self, vehCD):
        itemTypeID, nationID, itemID = vehicles.parseIntCompactDescr(vehCD)
        if itemTypeID is not _VEHICLE:
            LOG_ERROR('Value of int-type descriptor is not refer to vehicle', vehCD)
            return
        else:
            if not self._data.hasInvItem(vehCD):
                price = self._data.getShopPrice(vehCD)
                if price is None:
                    self._showMessage4Vehicle(self.MSG_SCOPE.Shop, 'not_found', vehCD)
                    return
                accCredits = self._data._accCredits
                accGold = self._data._accGold
                if (accCredits, accGold) >= price:
                    self.fireEvent(events.ShowWindowEvent(events.ShowWindowEvent.SHOW_VEHICLE_BUY_WINDOW, {'nationID': nationID,
                     'itemID': itemID}))
                else:
                    _credits = price[0] - accCredits if price[0] > 0 else 0
                    _gold = price[1] - accGold if price[1] > 0 else 0
                    self._showMessage4Vehicle(self.MSG_SCOPE.Shop, 'not_enough_money', vehCD, price=gui_items.formatPrice([_credits, _gold]))
            else:
                self._showMessage4Vehicle(self.MSG_SCOPE.Inventory, 'already_exists', vehCD, msgType=SystemMessages.SM_TYPE.Warning)
            return

    def sellVehicle(self, vehCD):
        itemTypeID, nationID, itemID = vehicles.parseIntCompactDescr(vehCD)
        if itemTypeID is not _VEHICLE:
            LOG_ERROR('Value of int-type descriptor is not refer to vehicle', vehCD)
            return
        if self._data.hasInvItem(vehCD):
            self.fireEvent(events.ShowWindowEvent(events.ShowWindowEvent.SHOW_VEHICLE_SELL_DIALOG, {'vehInvID': self._data.getInvItem(vehCD).inventoryId}))
        else:
            self._showMessage4Vehicle(self.MSG_SCOPE.Inventory, 'not_found', vehCD)

    def pushSystemMessage(self, typeString, message):
        msgType = SystemMessages.SM_TYPE.lookup(typeString)
        if msgType is None:
            msgType = SystemMessages.SM_TYPE.Error
        SystemMessages.pushMessage(message, msgType)
        return

    def invalidateCredits(self, accCredits):
        result = self._data.invalidateCredits(accCredits)
        if len(result):
            self.as_setNodesStatesS(NODE_STATE.ENOUGH_MONEY, result)

    def invalidateGold(self, gold):
        result = self._data.invalidateGold(gold)
        if len(result):
            self.as_setNodesStatesS(NODE_STATE.ENOUGH_MONEY, result)

    def invalidateFreeXP(self, freeXP):
        result = self._data.invalidateFreeXP(freeXP)
        if len(result):
            self.as_setNodesStatesS(NODE_STATE.ENOUGH_XP, result)

    def invalidateElites(self, elites):
        result = self._data.invalidateElites(elites)
        if len(result):
            self.as_setNodesStatesS(NODE_STATE.ELITE, result)

    def invalidateVTypeXP(self, xps):
        self.as_setVehicleTypeXPS(xps.items())
        result = self._data.invalidateVTypeXP(xps)
        if len(result):
            self.as_setNodesStatesS(NODE_STATE.ENOUGH_XP, result)

    def invalidateUnlocks(self, unlocks):
        next2Unlock, unlocked = self._data.invalidateUnlocks(unlocks)
        if len(unlocked):
            LOG_DEBUG('unlocked', unlocked)
            self.as_setNodesStatesS(NODE_STATE.UNLOCKED, unlocked)
        if len(next2Unlock):
            LOG_DEBUG('next2Unlock', next2Unlock)
            self.as_setNext2UnlockS(next2Unlock)

    def setInvVehicles(self, data):
        raise NotImplementedError, 'Must be overridden in subclass'

    def setInvItems(self, data):
        raise NotImplementedError, 'Must be overridden in subclass'

    def invalidateInventory(self, data, findItems = False):
        inventory = set()
        if _VEHICLE in data:
            vehicles, fullUpdate = self.setInvVehicles(data[_VEHICLE])
            if fullUpdate:
                return True
            inventory |= vehicles
        if findItems:
            for itemTypeID in _RESEARCH_ITEMS:
                if itemTypeID in data:
                    inventory |= self.setInvItems(data[itemTypeID])

        result = self._data.invalidateInventory(inventory)
        if len(result):
            self.as_setInventoryItemsS(result)
        return False

    def invalidateVehLocks(self, locks):
        raise NotImplementedError, 'Must be overridden in subclass'

    def _getUnlockConfirmMeta(self, itemCD, costCtx):
        itemTypeID, nationID, itemID = vehicles.parseIntCompactDescr(itemCD)
        ctx = {'xpCost': BigWorld.wg_getIntegralFormat(costCtx['xpCost']),
         'freeXP': BigWorld.wg_getIntegralFormat(costCtx['freeXP']),
         'typeString': getTypeInfoByIndex(itemTypeID)['userString']}
        if itemTypeID == _VEHICLE:
            key = 'confirmUnlockVehicle'
            ctx['userString'] = vehicles.getVehicleType(itemCD).userString
        else:
            key = 'confirmUnlockItem'
            ctx['userString'] = vehicles.getDictDescr(itemCD)['userString']
        return HtmlMessageDialogMeta('html_templates:lobby/dialogs', key, ctx=ctx)

    def _getConflictedEqsMeta(self, conflictedEqs):
        if len(conflictedEqs):
            meta = HtmlMessageDialogMeta('html_templates:lobby/dialogs', 'conflictedEqs', ctx={'eqs': "', '".join([ eq['userString'] for eq in conflictedEqs ])})
        else:
            meta = SimpleDialogMeta()
        return meta

    def _getBuyConfirmMeta(self, itemCD, price, conflictedEqs):
        itemTypeID, nationID, itemID = vehicles.parseIntCompactDescr(itemCD)
        conflictedEqs = self._getConflictedEqsMeta(conflictedEqs).getMessage()
        ctx = {'credits': BigWorld.wg_getIntegralFormat(price[0]),
         'typeString': getTypeInfoByIndex(itemTypeID)['userString'],
         'conflictedEqs': conflictedEqs if conflictedEqs else ''}
        if itemTypeID == _VEHICLE:
            ctx['userString'] = vehicles.getVehicleType(itemCD).userString
        else:
            ctx['userString'] = vehicles.getDictDescr(itemCD)['userString']
        return HtmlMessageDialogMeta('html_templates:lobby/dialogs', 'confirmBuyAndInstall', ctx=ctx)

    def _getXPCostCtx(self, vehXP, xpCost):
        xp = vehXP - xpCost
        freeXP = 0
        if xp < 0:
            xp = vehXP
            freeXP = xpCost - xp
        return {'vehXP': xp,
         'freeXP': freeXP,
         'xpCost': xpCost}

    def _showMessage(self, scope, msg, itemCD, msgType = SystemMessages.SM_TYPE.Error, **kwargs):
        itemTypeID, nationID, itemID = vehicles.parseIntCompactDescr(itemCD)
        if itemTypeID == _VEHICLE:
            key = scope('vehicle', msg)
            kwargs['userString'] = vehicles.getVehicleType(itemCD).userString
        else:
            key = scope('item', msg)
            kwargs.update({'typeString': getTypeInfoByIndex(itemTypeID)['userString'],
             'userString': vehicles.getDictDescr(itemCD)['userString']})
        SystemMessages.pushMessage(i18n.makeString(key, **kwargs), type=msgType)

    def _showMessage4Item(self, scope, msg, itemCD, msgType = SystemMessages.SM_TYPE.Error, **kwargs):
        itemTypeID, nationID, itemID = vehicles.parseIntCompactDescr(itemCD)
        raise itemTypeID != _VEHICLE or AssertionError
        key = scope('item', msg)
        kwargs.update({'typeString': getTypeInfoByIndex(itemTypeID)['userString'],
         'userString': vehicles.getDictDescr(itemCD)['userString']})
        SystemMessages.pushMessage(i18n.makeString(key, **kwargs), type=msgType)

    def _showMessage4Vehicle(self, scope, msg, itemCD, msgType = SystemMessages.SM_TYPE.Error, **kwargs):
        itemTypeID, nationID, itemID = vehicles.parseIntCompactDescr(itemCD)
        raise itemTypeID == _VEHICLE or AssertionError
        key = scope('vehicle', msg)
        kwargs['userString'] = vehicles.getVehicleType(itemCD).userString
        SystemMessages.pushMessage(i18n.makeString(key, **kwargs), type=msgType)

    def _showAlreadyUnlockedMsg(self, itemCD):
        self._showMessage(self.MSG_SCOPE.Unlocks, 'already_unlocked', itemCD)

    def _showUnlockItemMsg(self, itemCD, costCtx):
        self._showMessage(self.MSG_SCOPE.Unlocks, 'unlock_success', itemCD, msgType=SystemMessages.SM_TYPE.PowerLevel, **costCtx)

    def _validateItem2Unlock(self, unlockCD, vehCD, unlockIdx, xpCost):
        itemTypeID, nationID, itemID = vehicles.parseIntCompactDescr(vehCD)
        if itemTypeID != _VEHICLE:
            LOG_ERROR('Int compact descriptor is not for vehicle', vehCD)
            return False
        if not self._data.isUnlocked(vehCD):
            LOG_ERROR('Vehicle is not unlocked', unlockCD, vehCD)
            return False
        if self._data.isUnlocked(unlockCD):
            self._showAlreadyUnlockedMsg(vehCD)
            return False
        if not self._data.isNext2Unlock(unlockCD):
            LOG_ERROR('Required items are not unlocked', unlockCD, vehCD)
            return False
        if self._data._accFreeXP + self._data.getVehXP(vehCD) < xpCost:
            LOG_ERROR('XP not enough for unlock', vehCD, unlockIdx, xpCost)
            return False
        if RequestState.inProcess('unlock'):
            SystemMessages.pushI18nMessage('#system_messages:unlocks/in_processing', type=SystemMessages.SM_TYPE.Warning)
            return False
        return True

    def _doUnlockItem(self, unlockCD, vehCD, unlockIdx, xpCost, result):
        if result and self._validateItem2Unlock(unlockCD, vehCD, unlockIdx, xpCost):
            costCtx = self._getXPCostCtx(self._data.getVehXP(vehCD), xpCost)
            Waiting.show('research')
            RequestState.sent('unlock')
            BigWorld.player().stats.unlock(vehCD, unlockIdx, callback=partial(self.__cb_onUnlock, unlockCD, costCtx))

    def __cb_onUnlock(self, itemCD, costCtx, resultID):
        Waiting.hide('research')
        RequestState.received('unlock')
        if RES_SUCCESS == resultID:
            self._showUnlockItemMsg(itemCD, costCtx)
        else:
            self._showMessage(self.MSG_SCOPE.Unlocks, 'server_error', itemCD)

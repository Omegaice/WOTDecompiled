import BigWorld
from debug_utils import LOG_DEBUG
from gui.SystemMessages import SM_TYPE
from gui.shared import g_itemsCache
from gui.shared.gui_items import GUI_ITEM_TYPE
from gui.shared.gui_items.processors import Processor, ItemProcessor, VehicleItemProcessor, makeI18nSuccess, makeI18nError, plugins
from gui.shared.utils.gui_items import formatPrice

class TankmanDismiss(ItemProcessor):

    def __init__(self, tankman):
        vehicle = None
        if tankman.vehicleInvID > 0:
            vehicle = g_itemsCache.items.getVehicle(tankman.vehicleInvID)
        if len(tankman.skills) > 0 or tankman.roleLevel >= 100:
            confirmatorType = plugins.DismissTankmanConfirmator('protectedDismissTankman', tankman)
        else:
            confirmatorType = plugins.MessageConfirmator('dismissTankman')
        raise confirmatorType or AssertionError
        super(TankmanDismiss, self).__init__(tankman, [confirmatorType, plugins.VehicleValidator(vehicle, isEnabled=tankman.vehicleInvID > 0)])
        return

    def _errorHandler(self, code, errStr = '', ctx = None):
        if len(errStr):
            return makeI18nError('dismiss_tankman/%s' % errStr)
        return makeI18nError('dismiss_tankman/server_error')

    def _successHandler(self, code, ctx = None):
        return makeI18nSuccess('dismiss_tankman/success', type=SM_TYPE.Information)

    def _request(self, callback):
        LOG_DEBUG('Make server request to dismiss tankman:', self.item)
        BigWorld.player().inventory.dismissTankman(self.item.invID, lambda code: self._response(code, callback))


class TankmanRecruit(Processor):

    def __init__(self, nationID, vehTypeID, role, tmanCostTypeIdx):
        super(TankmanRecruit, self).__init__([plugins.MoneyValidator(self.__getRecruitPrice(tmanCostTypeIdx)), plugins.FreeTankmanValidator(isEnabled=tmanCostTypeIdx == 0), plugins.BarracksSlotsValidator()])
        self.nationID = nationID
        self.vehTypeID = vehTypeID
        self.role = role
        self.tmanCostTypeIdx = tmanCostTypeIdx

    def _errorHandler(self, code, errStr = '', ctx = None):
        if len(errStr):
            return makeI18nError('recruit_window/%s' % errStr)
        return makeI18nError('recruit_window/server_error', auxData=ctx)

    def _successHandler(self, code, ctx = None):
        tmanCost = self.__getRecruitPrice(self.tmanCostTypeIdx)
        if tmanCost[0] > 0 or tmanCost[1] > 0:
            return makeI18nSuccess('recruit_window/financial_success', price=formatPrice(tmanCost), type=self.__getSysMsgType(), auxData=ctx)
        return makeI18nSuccess('recruit_window/success', type=self.__getSysMsgType(), auxData=ctx)

    def _request(self, callback):
        LOG_DEBUG('Make server request to recruit tankman:', self.nationID, self.vehTypeID, self.role, self.tmanCostTypeIdx)
        BigWorld.player().shop.buyTankman(self.nationID, self.vehTypeID, self.role, self.tmanCostTypeIdx, lambda code, tmanInvID, tmanCompDescr: self._response(code, callback, ctx=tmanInvID))

    def __getRecruitPrice(self, tmanCostTypeIdx):
        upgradeCost = g_itemsCache.items.shop.tankmanCost[tmanCostTypeIdx]
        if tmanCostTypeIdx == 1:
            return (upgradeCost['credits'], 0)
        if tmanCostTypeIdx == 2:
            return (0, upgradeCost['gold'])
        return (0, 0)

    def __getSysMsgType(self):
        tmanCost = self.__getRecruitPrice(self.tmanCostTypeIdx)
        if tmanCost[0] > 0:
            return SM_TYPE.PurchaseForCredits
        if tmanCost[1] > 0:
            return SM_TYPE.PurchaseForGold
        return SM_TYPE.Information


class TankmanEquip(Processor):

    def __init__(self, tankman, vehicle, slot):
        super(TankmanEquip, self).__init__()
        self.tankman = tankman
        self.vehicle = vehicle
        self.slot = slot
        self.isReequip = False
        anotherTankman = dict(vehicle.crew).get(slot)
        if tankman is not None and anotherTankman is not None and anotherTankman.invID != tankman.invID:
            self.isReequip = True
        self.addPlugins([plugins.VehicleLockValidator(vehicle), plugins.ModuleValidator(tankman), plugins.ModuleTypeValidator(tankman, (GUI_ITEM_TYPE.TANKMAN,))])
        return

    def _errorHandler(self, code, errStr = '', ctx = None):
        prefix = self.__getSysMsgPrefix()
        if len(errStr):
            return makeI18nError('%s/%s' % (prefix, errStr))
        return makeI18nError('%s/server_error' % prefix)

    def _successHandler(self, code, ctx = None):
        return makeI18nSuccess('%s/success' % self.__getSysMsgPrefix(), type=SM_TYPE.Information)

    def _request(self, callback):
        LOG_DEBUG('Make server request to equip tankman:', self.tankman, self.vehicle, self.slot, self.isReequip)
        tmanInvID = None
        if self.tankman is not None:
            tmanInvID = self.tankman.invID
        BigWorld.player().inventory.equipTankman(self.vehicle.invID, self.slot, tmanInvID, lambda code: self._response(code, callback))
        return

    def __getSysMsgPrefix(self):
        if not self.isReequip:
            return 'equip_tankman'
        return 'reequip_tankman'


class TankmanUnload(Processor):

    def __init__(self, vehicle, slot = -1):
        """
        Ctor.
        
        @param vehicle: vehicle to unload tankman
        @param slot:    slot in given vehicle to unload. -1 by default,
                                        that means - unload all tankmen from vehicle.
        """
        super(TankmanUnload, self).__init__()
        self.vehicle = vehicle
        self.slot = slot
        berthsNeeded = 1
        if slot == -1:
            berthsNeeded = len(filter(lambda (role, t): t is not None, vehicle.crew))
        self.__sysMsgPrefix = 'unload_tankman' if berthsNeeded == 1 else 'unload_crew'
        self.addPlugins([plugins.VehicleLockValidator(vehicle), plugins.BarracksSlotsValidator(berthsNeeded)])

    def _errorHandler(self, code, errStr = '', ctx = None):
        if len(errStr):
            return makeI18nError('%s/%s' % (self.__sysMsgPrefix, errStr))
        return makeI18nError('%s/server_error' % self.__sysMsgPrefix)

    def _successHandler(self, code, ctx = None):
        return makeI18nSuccess('%s/success' % self.__sysMsgPrefix, type=SM_TYPE.Information)

    def _request(self, callback):
        LOG_DEBUG('Make server request to unload tankman:', self.vehicle, self.slot)
        BigWorld.player().inventory.equipTankman(self.vehicle.invID, self.slot, None, lambda code: self._response(code, callback))
        return


class TankmanRetraining(ItemProcessor):

    def __init__(self, tankman, vehicle, tmanCostTypeIdx):
        vehInInventory = vehicle.invID > 0
        super(TankmanRetraining, self).__init__(tankman, (plugins.VehicleValidator(vehicle), plugins.MessageConfirmator('tankmanRetraining/unknownVehicle', ctx={'tankname': vehicle.userName}, isEnabled=not vehInInventory)))
        self.vehicle = vehicle
        self.tmanCostTypeIdx = tmanCostTypeIdx

    def _errorHandler(self, code, errStr = '', ctx = None):
        if len(errStr):
            makeI18nError('retraining_tankman/%s' % errStr)
        return makeI18nError('retraining_tankman/server_error')

    def _successHandler(self, code, ctx = None):
        tmanCost = self.__getRecruitPrice(self.tmanCostTypeIdx)
        if tmanCost[0] > 0 or tmanCost[1] > 0:
            return makeI18nSuccess('retraining_tankman/financial_success', price=formatPrice(tmanCost), type=self.__getSysMsgType(), auxData=ctx)
        return makeI18nSuccess('retraining_tankman/success', type=self.__getSysMsgType(), auxData=ctx)

    def _request(self, callback):
        LOG_DEBUG('Make server request to retraining tankman:', self.item, self.vehicle, self.tmanCostTypeIdx)
        BigWorld.player().inventory.respecTankman(self.item.invID, self.vehicle.intCD, self.tmanCostTypeIdx, lambda code: self._response(code, callback))

    def __getRecruitPrice(self, tmanCostTypeIdx):
        upgradeCost = g_itemsCache.items.shop.tankmanCost[tmanCostTypeIdx]
        if tmanCostTypeIdx == 1:
            return (upgradeCost['credits'], 0)
        if tmanCostTypeIdx == 2:
            return (0, upgradeCost['gold'])
        return (0, 0)

    def __getSysMsgType(self):
        tmanCost = self.__getRecruitPrice(self.tmanCostTypeIdx)
        if tmanCost[0] > 0:
            return SM_TYPE.PurchaseForCredits
        if tmanCost[1] > 0:
            return SM_TYPE.PurchaseForGold
        return SM_TYPE.Information


class TankmanFreeToOwnXpConvertor(Processor):

    def __init__(self, tankman, selectedXpForConvert):
        super(TankmanFreeToOwnXpConvertor, self).__init__([])
        self.__tankman = tankman
        self.__selectedXpForConvert = selectedXpForConvert

    def _errorHandler(self, code, errStr = '', ctx = None):
        if len(errStr):
            return makeI18nError('free_xp_to_tman_skill/error/%s' % errStr)
        return makeI18nError('free_xp_to_tman_skill/server_error')

    def _successHandler(self, code, ctx = None):
        return makeI18nSuccess('free_xp_to_tman_skill/success', freeXP=BigWorld.wg_getIntegralFormat(self.__selectedXpForConvert), type=SM_TYPE.Information)

    def _request(self, callback):
        LOG_DEBUG('Attempt to request server to exchange Free user XP to tankman XP', self.__tankman, self.__selectedXpForConvert)
        BigWorld.player().inventory.freeXPToTankman(self.__tankman.invID, self.__selectedXpForConvert, lambda errStr, code: self._response(code, callback, errStr=errStr))


class TankmanAddSkill(ItemProcessor):

    def __init__(self, tankman, skillName):
        vehicle = None
        if tankman.vehicleInvID > 0:
            vehicle = g_itemsCache.items.getVehicle(tankman.vehicleInvID)
        super(TankmanAddSkill, self).__init__(tankman, (plugins.VehicleValidator(vehicle, isEnabled=tankman.vehicleInvID > 0),))
        self.skillName = skillName
        return

    def _errorHandler(self, code, errStr = '', ctx = None):
        if len(errStr):
            return makeI18nError('add_tankman_skill/%s' % errStr)
        return makeI18nError('add_tankman_skill/server_error')

    def _successHandler(self, code, ctx = None):
        return makeI18nSuccess('add_tankman_skill/success', type=SM_TYPE.Information)

    def _request(self, callback):
        LOG_DEBUG('Make server request to add tankman skill:', self.item, self.skillName)
        BigWorld.player().inventory.addTankmanSkill(self.item.invID, self.skillName, lambda code: self._response(code, callback))


class TankmanDropSkills(ItemProcessor):

    def __init__(self, tankman, dropSkillCostIdx):
        super(TankmanDropSkills, self).__init__(tankman, (plugins.MessageConfirmator('dropSkill'),))
        self.dropSkillCostIdx = dropSkillCostIdx

    def _errorHandler(self, code, errStr = '', ctx = None):
        if len(errStr):
            return makeI18nError('drop_tankman_skill/%s' % errStr)
        return makeI18nError('drop_tankman_skill/server_error')

    def _successHandler(self, code, ctx = None):
        msgType = self.__getTankmanSysMsgType(self.dropSkillCostIdx)
        price = g_itemsCache.items.shop.dropSkillsCost.get(self.dropSkillCostIdx)
        return makeI18nSuccess('drop_tankman_skill/success', money=formatPrice((price['credits'], price['gold'])), type=msgType)

    def _request(self, callback):
        LOG_DEBUG('Make server request to drop tankman skills:', self.item, self.dropSkillCostIdx)
        BigWorld.player().inventory.dropTankmanSkills(self.item.invID, self.dropSkillCostIdx, lambda code: self._response(code, callback))

    def __getTankmanSysMsgType(self, dropSkillCostIdx):
        if dropSkillCostIdx == 1:
            return SM_TYPE.FinancialTransactionWithCredits
        if dropSkillCostIdx == 2:
            return SM_TYPE.FinancialTransactionWithGold
        return SM_TYPE.Information


class TankmanChangePassport(ItemProcessor):

    def __init__(self, tankman, firstNameID, lastNameID, iconID, isFemale = False):
        vehicle = None
        if tankman.vehicleInvID > 0:
            vehicle = g_itemsCache.items.getVehicle(tankman.vehicleInvID)
        super(TankmanChangePassport, self).__init__(tankman, (plugins.VehicleValidator(vehicle, isEnabled=tankman.vehicleInvID > 0), plugins.MessageConfirmator('replacePassportConfirmation')))
        self.firstNameID = firstNameID
        self.lastNameID = lastNameID
        self.iconID = iconID
        self.isFemale = isFemale
        return

    def _errorHandler(self, code, errStr = '', ctx = None):
        return makeI18nError('replace_tankman/server_error')

    def _successHandler(self, code, ctx = None):
        goldPrice = g_itemsCache.items.shop.passportChangeCost
        return makeI18nSuccess('replace_tankman/success', money=formatPrice((0, goldPrice)), type=SM_TYPE.PurchaseForGold)

    def _request(self, callback):
        LOG_DEBUG('Make server request to change tankman passport:', self.item, self.firstNameID, self.lastNameID, self.iconID, self.isFemale)
        BigWorld.player().inventory.replacePassport(self.item.invID, self.isFemale, self.firstNameID, self.lastNameID, self.iconID, lambda code: self._response(code, callback))

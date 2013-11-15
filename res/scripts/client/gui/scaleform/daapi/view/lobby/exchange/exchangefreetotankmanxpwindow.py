# 2013.11.15 11:26:01 EST
# Embedded file name: scripts/client/gui/Scaleform/daapi/view/lobby/exchange/ExchangeFreeToTankmanXpWindow.py
import BigWorld
from adisp import process
from debug_utils import LOG_DEBUG
from gui.ClientUpdateManager import g_clientUpdateManager
from gui.Scaleform.Waiting import Waiting
from gui.Scaleform.daapi.view.meta.ExchangeFreeToTankmanXpWindowMeta import ExchangeFreeToTankmanXpWindowMeta
from gui.Scaleform.daapi.view.meta.WindowViewMeta import WindowViewMeta
from gui.Scaleform.framework.entities.View import View
from gui.shared import g_itemsCache
from gui.shared.events import SkillDropEvent
from gui.shared.gui_items import GUI_ITEM_TYPE
from gui.shared.gui_items.processors.tankman import TankmanFreeToOwnXpConvertor
from gui.shared.gui_items.serializers import g_itemSerializer
from gui.shared.utils import decorators
from gui.shared.utils.requesters import ItemsRequester
from gui import SystemMessages
from items import vehicles
from items.tankmen import MAX_SKILL_LEVEL

class ExchangeFreeToTankmanXpWindow(ExchangeFreeToTankmanXpWindowMeta, WindowViewMeta, View):

    def __init__(self, ctx):
        super(ExchangeFreeToTankmanXpWindow, self).__init__()
        self.__tankManId = ctx.get('tankManId')
        self.__selectedXpForConvert = 0

    @decorators.process('updatingSkillWindow')
    def apply(self):
        tankman = g_itemsCache.items.getTankman(self.__tankManId)
        xpConverter = TankmanFreeToOwnXpConvertor(tankman, self.__selectedXpForConvert)
        result = yield xpConverter.request()
        if len(result.userMsg):
            SystemMessages.g_instance.pushI18nMessage(result.userMsg, type=result.sysMsgType)
        self.onWindowClose()

    def _populate(self):
        super(ExchangeFreeToTankmanXpWindow, self)._populate()
        g_clientUpdateManager.addCallbacks({'stats.freeXP': self.__onFreeXpChanged,
         'inventory.8.compDescr': self.__onTankmanChanged})
        self.addListener(SkillDropEvent.SKILL_DROPPED_SUCCESSFULLY, self.__skillDropWindowCloseHandler)
        self.__prepareAndSendInitData()

    def __onFreeXpChanged(self, data):
        self.__prepareAndSendInitData()

    def __onTankmanChanged(self, data):
        if self.__tankManId in data:
            if data[self.__tankManId] is None:
                self.destroy()
                return
            self.__prepareAndSendInitData()
        return

    def __prepareAndSendInitData(self):
        Waiting.show('updatingSkillWindow')
        items = g_itemsCache.items
        tankman = items.getTankman(self.__tankManId)
        if len(tankman.skills) == 0:
            Waiting.hide('updatingSkillWindow')
            return
        rate = items.shop.freeXPToTManXPRate
        toNextPrcLeft = self.__getCurrentTankmanLevelCost(tankman)
        toNextPrcLeft = self.__roundByModulo(toNextPrcLeft, rate)
        needMaxXp = max(1, toNextPrcLeft / rate)
        nextSkillLevel = tankman.descriptor.lastSkillLevel + 1
        freeXp = items.stats.freeXP
        if freeXp - needMaxXp > 0:
            while nextSkillLevel < MAX_SKILL_LEVEL:
                needMaxXp += self.__calcLevelUpCost(tankman, nextSkillLevel, len(tankman.skills)) / rate
                if freeXp - needMaxXp <= 0:
                    break
                nextSkillLevel += 1

        else:
            nextSkillLevel -= 1
        data = {'tankmanID': self.__tankManId,
         'currentSkill': g_itemSerializer.pack(tankman.skills[len(tankman.skills) - 1]),
         'lastSkillLevel': tankman.descriptor.lastSkillLevel,
         'nextSkillLevel': nextSkillLevel}
        self.as_setInitDataS(data)
        Waiting.hide('updatingSkillWindow')

    def __getCurrentTankmanLevelCost(self, tankman):
        if tankman.roleLevel != MAX_SKILL_LEVEL or not tankman.hasNewSkill:
            if len(tankman.descriptor.skills) == 0 or tankman.roleLevel != MAX_SKILL_LEVEL:
                nextSkillLevel = tankman.roleLevel
            else:
                nextSkillLevel = tankman.descriptor.lastSkillLevel
            skillSeqNum = 0
            if tankman.roleLevel == MAX_SKILL_LEVEL:
                skillSeqNum = len(tankman.descriptor.skills)
            return self.__calcLevelUpCost(tankman, nextSkillLevel, skillSeqNum) - tankman.descriptor.freeXP
        return 0

    @process
    def calcValueRequest(self, toLevel):
        Waiting.show('updatingSkillWindow')
        items = g_itemsCache.items
        tankman = items.getTankman(self.__tankManId)
        if toLevel == tankman.descriptor.lastSkillLevel:
            self.__selectedXpForConvert = 0
            self.as_setCalcValueResponseS(0)
            Waiting.hide('updatingSkillWindow')
            return
        toLevel = int(toLevel)
        if toLevel > MAX_SKILL_LEVEL:
            toLevel = MAX_SKILL_LEVEL
        needXp = self.__getCurrentTankmanLevelCost(tankman)
        for level in range(int(tankman.descriptor.lastSkillLevel + 1), toLevel, 1):
            needXp += self.__calcLevelUpCost(tankman, level, len(tankman.skills))

        rate = items.shop.freeXPToTManXPRate
        needXp = self.__roundByModulo(needXp, rate)
        needXp /= rate
        self.__selectedXpForConvert = max(1, needXp)
        self.as_setCalcValueResponseS(self.__selectedXpForConvert)
        Waiting.hide('updatingSkillWindow')

    def __calcLevelUpCost(self, tankman, fromLevel, skillSeqNum):
        return tankman.descriptor.levelUpXpCost(fromLevel, skillSeqNum)

    def __roundByModulo(self, targetXp, rate):
        left_rate = targetXp % rate
        if left_rate > 0:
            targetXp += rate - left_rate
        return targetXp

    def onWindowClose(self):
        self.destroy()

    def _dispose(self):
        self.removeListener(SkillDropEvent.SKILL_DROPPED_SUCCESSFULLY, self.__skillDropWindowCloseHandler)
        g_clientUpdateManager.removeObjectCallbacks(self)
        super(ExchangeFreeToTankmanXpWindow, self)._dispose()

    def __skillDropWindowCloseHandler(self, event):
        self.destroy()
# okay decompyling res/scripts/client/gui/scaleform/daapi/view/lobby/exchange/exchangefreetotankmanxpwindow.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:26:01 EST

import pickle
from items import tankmen
from gui import SystemMessages
from gui.Scaleform.framework.entities.View import View
from gui.shared.utils import decorators
from gui.shared.gui_items.serializers import g_itemSerializer
from gui.shared.gui_items.Tankman import Tankman
from gui.shared.gui_items.processors.tankman import TankmanDropSkills
from gui.Scaleform.Waiting import Waiting
from gui.Scaleform.daapi.view.meta.SkillDropMeta import SkillDropMeta
from gui.Scaleform.daapi.view.meta.WindowViewMeta import WindowViewMeta
from gui.shared import events, g_itemsCache
from gui.ClientUpdateManager import g_clientUpdateManager

class SkillDropWindow(View, SkillDropMeta, WindowViewMeta):

    def __init__(self, ctx):
        super(SkillDropWindow, self).__init__()
        self.tmanInvID = ctx.get('tankmanID')

    def __setData(self):
        Waiting.show('updatingSkillWindow')
        items = g_itemsCache.items
        tankman = items.getTankman(self.tmanInvID)
        dropSkillsCost = []
        for k in sorted(items.shop.dropSkillsCost.keys()):
            dropSkillsCost.append(items.shop.dropSkillsCost[k])

        skills_count = list(tankmen.ACTIVE_SKILLS)
        availableSkillsCount = len(skills_count) - len(tankman.skills)
        hasNewSkills = tankman.roleLevel == tankmen.MAX_SKILL_LEVEL and availableSkillsCount and (tankman.descriptor.lastSkillLevel == tankmen.MAX_SKILL_LEVEL or not len(tankman.skills))
        self.as_setDataS({'money': (items.stats.credits, items.stats.gold),
         'tankman': g_itemSerializer.pack(tankman),
         'dropSkillsCost': dropSkillsCost,
         'hasNewSkills': hasNewSkills,
         'defaultSavingMode': 0})
        Waiting.hide('updatingSkillWindow')

    def _populate(self):
        super(SkillDropWindow, self)._populate()
        self.__setData()
        g_clientUpdateManager.addCallbacks({'inventory.8.compDescr': self.onTankmanChanged,
         'stats.credits': self.onCreditsChange,
         'stats.gold': self.onGoldChange})

    def onTankmanChanged(self, data):
        if self.tmanInvID in data:
            if data[self.tmanInvID] is None:
                self.onWindowClose()
                return
            self.__setData()
        return

    def onCreditsChange(self, credits):
        self.as_setCreditsS(credits)

    def onGoldChange(self, gold):
        self.as_setGoldS(gold)

    def onWindowClose(self):
        g_clientUpdateManager.removeObjectCallbacks(self)
        self.destroy()

    def calcDropSkillsParams(self, tmanCompDescrPickle, xpReuseFraction):
        """
        Recalculates tankman skills by given skills reuse fraction
        
        @param tmanCompDescr: tankman string compact descriptor
        @param xpReuseFraction: tankman experience reuse fraction
        @return: (new skills count, last new skill level)
        """
        tmanCompDescr = pickle.loads(tmanCompDescrPickle)
        tmanDescr = tankmen.TankmanDescr(tmanCompDescr)
        tmanDescr.dropSkills(xpReuseFraction)
        tankman = Tankman(tmanDescr.makeCompactDescr())
        return (tankman.roleLevel,) + tankman.newSkillCount

    @decorators.process('deleting')
    def dropSkills(self, dropSkillCostIdx):
        """
        Drops all tankman skill using @dropSkillCostIdx modificator
        @param dropSkillCostIdx: tankman experience modificator index
        """
        tankman = g_itemsCache.items.getTankman(self.tmanInvID)
        proc = TankmanDropSkills(tankman, dropSkillCostIdx)
        result = yield proc.request()
        if len(result.userMsg):
            SystemMessages.g_instance.pushMessage(result.userMsg, type=result.sysMsgType)
        if result.success:
            self.onWindowClose()
            self.fireEvent(events.SkillDropEvent(events.SkillDropEvent.SKILL_DROPPED_SUCCESSFULLY))

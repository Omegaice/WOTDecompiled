# 2013.11.15 11:26:12 EST
# Embedded file name: scripts/client/gui/Scaleform/daapi/view/lobby/quests/QuestsWindow.py
import sys
import math
from collections import defaultdict
import BigWorld
from debug_utils import LOG_DEBUG
from gui import SystemMessages, game_control
from gui.shared import g_questsCache, events
from gui.ClientUpdateManager import g_clientUpdateManager
from gui.Scaleform.daapi.settings import VIEW_ALIAS
from gui.Scaleform.daapi.view.lobby.quests import quest_helpers
from gui.Scaleform.daapi.view.meta.QuestsWindowMeta import QuestsWindowMeta
from gui.Scaleform.daapi.view.meta.WindowViewMeta import WindowViewMeta
from gui.Scaleform.daapi.view.meta.QuestsCurrentTabMeta import QuestsCurrentTabMeta
from gui.Scaleform.framework.entities.View import View

class QuestsWindow(View, QuestsWindowMeta, WindowViewMeta):

    def __init__(self, ctx):
        super(QuestsWindow, self).__init__()
        self.__startQuestID = ctx.get('questID')

    def _onRegisterFlashComponent(self, viewPy, alias):
        if alias == VIEW_ALIAS.QUESTS_CURRENT_TAB:
            self.selectCurrentQuest(self.__startQuestID)
            self.__startQuestID = None
        return

    def onWindowClose(self):
        self.destroy()

    def getCurrentTab(self):
        return self.components.get(VIEW_ALIAS.QUESTS_CURRENT_TAB)

    def getFutureTab(self):
        return self.components.get(VIEW_ALIAS.QUESTS_FUTURE_TAB)

    def selectCurrentQuest(self, questID):
        currentTab = self.getCurrentTab()
        if questID is not None and currentTab is not None:
            currentTab.selectQuest(questID)
        return


class _QuestsTabAbstract(QuestsCurrentTabMeta):

    class SORT_TYPE:
        START_DATE = 0
        FINISH_DATE = 1

    def __init__(self):
        super(_QuestsTabAbstract, self).__init__()
        self.__invalidateCbID = None
        return

    def _populate(self):
        super(_QuestsTabAbstract, self)._populate()
        g_questsCache.onSyncCompleted += self.__onQuestsCacheSyncCompleted
        game_control.g_instance.igr.onIgrTypeChanged += self.__onQuestsUpdated
        g_clientUpdateManager.addCallbacks({'quests': self.__onQuestsUpdated,
         'cache.eventsData': self.__onQuestsUpdated,
         'inventory.1': self.__onQuestsUpdated})
        self.__sortType = self.SORT_TYPE.START_DATE
        self.__hideCompleted = False
        self.__onInvalidateCallback()

    def _dispose(self):
        g_clientUpdateManager.removeObjectCallbacks(self)
        game_control.g_instance.igr.onIgrTypeChanged -= self.__onQuestsUpdated
        g_questsCache.onSyncCompleted -= self.__onQuestsCacheSyncCompleted
        super(_QuestsTabAbstract, self)._dispose()

    def selectQuest(self, questID):
        return self.as_setSelectedQuestS(questID)

    def sort(self, sortType, hideCompleted):
        self.__sortType = sortType
        self.__hideCompleted = hideCompleted
        self.__invalidateQuestData()

    def getQuestInfo(self, questID):
        quests = self._getQuests()
        quest = quests.get(questID)
        quest_helpers.visitQuestsGUI(quest)
        if quest is not None:
            return quest_helpers.packQuestDetails(quest, quests)
        else:
            return

    def _getQuests(self):
        return g_questsCache.getCurrentQuests()

    def __onQuestsUpdated(self, *args):
        quest_helpers.updateQuestSettings(g_questsCache.getQuests())
        self.__invalidateQuestData()

    def __sortFunc(self, a, b):
        result = 1
        if a.isSubtask() and b.isSubtask():
            if a.getSeqID() > -1 and b.getSeqID() > -1:
                return a.getSeqID() - b.getSeqID()
        if a.isCompleted():
            return 1
        if b.isCompleted():
            return -1
        if self.__sortType == self.SORT_TYPE.START_DATE:
            result = int(a.getStartTime() - b.getStartTime())
        elif self.__sortType == self.SORT_TYPE.FINISH_DATE:
            result = int(a.getFinishTimeLeft() - b.getFinishTimeLeft())
        if result == 0:
            result = cmp(a.getID(), b.getID())
        return result

    def __filterFunc(self, a):
        return not self.__hideCompleted or not a.isCompleted()

    def __applyFilters(self, quests):
        return filter(self.__filterFunc, self.__applySort(quests))

    def __applySort(self, quests):
        return sorted(quests, self.__sortFunc)

    def __onQuestsCacheSyncCompleted(self):
        self.__onInvalidateCallback()

    def __makeGroups(self, quests):
        tasks = []
        subtasks = defaultdict(lambda : [])
        for qID, q in quests.iteritems():
            if q.getGroupID() is None or q.isStrategic():
                tasks.append(q)
            else:
                subtasks[q.getGroupID()].append(q)

        return (tasks, subtasks)

    def __invalidateQuestData(self):
        quests = self._getQuests()
        tasks, subtasks = self.__makeGroups(quests)
        result = []
        for q in self.__applyFilters(tasks):
            if q.isStrategic():
                qSubtasks = self.__applySort(subtasks[q.getGroupID()])
                result.append(quest_helpers.packQuest(q, quests, linkDown=False if len(qSubtasks) == 0 else True))
                for idx, subtask in enumerate(qSubtasks):
                    linkDown = idx != len(qSubtasks) - 1
                    result.append(quest_helpers.packQuest(subtask, quests, linkDown=linkDown, linkUp=True))

            else:
                result.append(quest_helpers.packQuest(q, quests))

        self.as_setQuestsDataS(result, len(tasks))

    def __onInvalidateCallback(self):
        self.__invalidateQuestData()


class QuestsCurrentTab(_QuestsTabAbstract):

    def _getQuests(self):
        return g_questsCache.getCurrentQuests()

    def _getInvalidateCallbackDuration(self, q):
        return q.getFinishTimeLeft()


class QuestsFutureTab(_QuestsTabAbstract):

    def _getQuests(self):
        return g_questsCache.getFutureQuests()

    def _getInvalidateCallbackDuration(self, q):
        return q.getStartTimeLeft()
# okay decompyling res/scripts/client/gui/scaleform/daapi/view/lobby/quests/questswindow.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:26:12 EST

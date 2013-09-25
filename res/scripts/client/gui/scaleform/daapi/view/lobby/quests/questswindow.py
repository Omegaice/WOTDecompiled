import sys
import math
from collections import defaultdict
import BigWorld
from debug_utils import LOG_DEBUG
from gui.shared import g_questsCache
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
        self.__sortType = self.SORT_TYPE.START_DATE
        self.__hideCompleted = False
        self.__onInvalidateCallback()

    def _dispose(self):
        self.__clearInvalidateCallback()
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

    def _getInvalidateCallbackDuration(self, q):
        return 0

    def __sortFunc(self, a, b):
        if a.isSubtask() and b.isSubtask():
            if a.getSeqID() > -1 and b.getSeqID() > -1:
                return a.getSeqID() - b.getSeqID()
        if a.isCompleted():
            return 1
        if b.isCompleted():
            return -1
        if self.__sortType == self.SORT_TYPE.START_DATE:
            return int(a.getStartTime() - b.getStartTime())
        if self.__sortType == self.SORT_TYPE.FINISH_DATE:
            return int(a.getFinishTimeLeft() - b.getFinishTimeLeft())
        return 1

    def __filterFunc(self, a):
        return not self.__hideCompleted or not a.isCompleted()

    def __applyFilters(self, quests):
        return filter(self.__filterFunc, sorted(quests, self.__sortFunc))

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
                qSubtasks = self.__applyFilters(subtasks[q.getGroupID()])
                result.append(quest_helpers.packQuest(q, quests, linkDown=True))
                for idx, subtask in enumerate(qSubtasks):
                    linkDown = idx != len(qSubtasks) - 1
                    result.append(quest_helpers.packQuest(subtask, quests, linkDown=linkDown, linkUp=True))

            else:
                result.append(quest_helpers.packQuest(q, quests))

        self.as_setQuestsDataS(result, len(tasks))

    def __loadInvalidateCallback(self, duration):
        LOG_DEBUG('load quest window invalidation callback (secs)', duration)
        self.__clearInvalidateCallback()
        self.__invalidateCbID = BigWorld.callback(math.ceil(duration), self.__onInvalidateCallback)

    def __clearInvalidateCallback(self):
        if self.__invalidateCbID is not None:
            BigWorld.cancelCallback(self.__invalidateCbID)
            self.__invalidateCbID = None
        return

    def __onInvalidateCallback(self):
        self.__clearInvalidateCallback()
        self.__invalidateQuestData()
        minFinishTimeLeft = sys.maxint
        for q in self._getQuests().itervalues():
            minFinishTimeLeft = min(minFinishTimeLeft, self._getInvalidateCallbackDuration(q))

        if minFinishTimeLeft != sys.maxint:
            self.__loadInvalidateCallback(minFinishTimeLeft)


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

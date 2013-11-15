# 2013.11.15 11:26:05 EST
# Embedded file name: scripts/client/gui/Scaleform/daapi/view/lobby/header/QuestsControl.py
from debug_utils import LOG_DEBUG
from gui import game_control
from gui.shared import g_questsCache, events
from gui.ClientUpdateManager import g_clientUpdateManager
from gui.Scaleform.daapi.view.lobby.quests import quest_helpers
from gui.Scaleform.daapi.view.meta.QuestsControlMeta import QuestsControlMeta
from gui.Scaleform.framework.entities.DAAPIModule import DAAPIModule

class QuestsControl(QuestsControlMeta, DAAPIModule):

    def __init__(self):
        super(QuestsControl, self).__init__()
        self.__isHighlighted = False

    def _populate(self):
        super(QuestsControl, self)._populate()
        g_questsCache.onSyncCompleted += self.__onQuestsUpdated
        game_control.g_instance.igr.onIgrTypeChanged += self.__onQuestsUpdated
        g_clientUpdateManager.addCallbacks({'quests': self.__onQuestsUpdated,
         'cache.eventsData': self.__onQuestsUpdated,
         'inventory.1': self.__onQuestsUpdated})
        self.addListener(events.LobbySimpleEvent.QUESTS_UPDATED, self.__onQuestsUpdated)
        self.__onQuestsUpdated()

    def _dispose(self):
        g_clientUpdateManager.removeObjectCallbacks(self)
        self.removeListener(events.LobbySimpleEvent.QUESTS_UPDATED, self.__onQuestsUpdated)
        game_control.g_instance.igr.onIgrTypeChanged -= self.__onQuestsUpdated
        g_questsCache.onSyncCompleted -= self.__onQuestsUpdated
        super(QuestsControl, self)._dispose()

    def showQuestsWindow(self):
        self.fireEvent(events.ShowWindowEvent(events.ShowWindowEvent.SHOW_QUESTS_WINDOW))

    def __onQuestsUpdated(self, *args):
        quests = g_questsCache.getQuests()
        quest_helpers.updateQuestSettings(quests)
        newQuestsCount = len(quest_helpers.getNewQuests(quests))
        if newQuestsCount:
            if not self.__isHighlighted:
                self.as_highlightControlS()
        else:
            self.as_resetControlS()
        self.__isHighlighted = bool(newQuestsCount)
# okay decompyling res/scripts/client/gui/scaleform/daapi/view/lobby/header/questscontrol.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:26:05 EST

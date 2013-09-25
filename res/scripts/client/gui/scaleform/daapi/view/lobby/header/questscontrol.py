# Embedded file name: scripts/client/gui/Scaleform/daapi/view/lobby/header/QuestsControl.py
from debug_utils import LOG_DEBUG
from gui.shared import g_questsCache, events
from gui.Scaleform.daapi.view.lobby.quests import quest_helpers
from gui.Scaleform.daapi.view.meta.QuestsControlMeta import QuestsControlMeta
from gui.Scaleform.framework.entities.DAAPIModule import DAAPIModule

class QuestsControl(QuestsControlMeta, DAAPIModule):

    def __init__(self):
        super(QuestsControl, self).__init__()
        self.__isHighlighted = False

    def _populate(self):
        super(QuestsControl, self)._populate()
        g_questsCache.onSyncCompleted += self.__checkForNew
        self.addListener(events.LobbySimpleEvent.QUEST_VISITED, self.__checkForNew)
        self.__checkForNew()

    def _dispose(self):
        self.removeListener(events.LobbySimpleEvent.QUEST_VISITED, self.__checkForNew)
        g_questsCache.onSyncCompleted -= self.__checkForNew
        super(QuestsControl, self)._dispose()

    def showQuestsWindow(self):
        self.fireEvent(events.ShowWindowEvent(events.ShowWindowEvent.SHOW_QUESTS_WINDOW))

    def __checkForNew(self, *args):
        newQuestsCount = len(quest_helpers.getNewQuests(g_questsCache.getQuests()))
        if newQuestsCount:
            if not self.__isHighlighted:
                self.as_highlightControlS()
        else:
            self.as_resetControlS()
        self.__isHighlighted = bool(newQuestsCount)
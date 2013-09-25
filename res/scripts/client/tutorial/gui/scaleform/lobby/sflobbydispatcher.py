# Embedded file name: scripts/client/tutorial/gui/Scaleform/lobby/SfLobbyDispatcher.py
import weakref
from gui.Scaleform.Waiting import Waiting
from gui.Scaleform.daapi.settings import VIEW_ALIAS
from gui.Scaleform.framework import AppRef, VIEW_TYPE
from gui.shared import g_eventBus, EVENT_BUS_SCOPE
from gui.shared.events import TutorialEvent, ShowWindowEvent
from tutorial import GlobalStorage, LOG_MEMORY, LOG_ERROR
from tutorial.control.context import GLOBAL_FLAG, GLOBAL_VAR
from tutorial.gui import LobbyDispatcher, GUIDispatcher

class SfLobbyDispatcher(LobbyDispatcher, AppRef):
    _isHistory = GlobalStorage(GLOBAL_FLAG.SHOW_HISTORY, False)
    _isFlagsReset = GlobalStorage(GLOBAL_FLAG.IS_FLAGS_RESET, False)
    _historyNotAvailable = GlobalStorage(GLOBAL_FLAG.HISTORY_NOT_AVAILABLE, False)
    _lastHistoryID = GlobalStorage(GLOBAL_VAR.LAST_HISTORY_ID, 0)

    def __init__(self, config):
        super(LobbyDispatcher, self).__init__()
        self.__uiRef = None
        self.__config = config
        self.__info = None
        self.__level = None
        self.__isStarted = False
        return

    def __del__(self):
        LOG_MEMORY('SfLobbyDispatcher deleted')

    def start(self, ctx):
        if self.__isStarted:
            return
        self.__isStarted = True
        addListener = g_eventBus.addListener
        addListener(TutorialEvent.UI_CONTROL_ADDED, self.__handleUIAdded, scope=EVENT_BUS_SCOPE.GLOBAL)
        addListener(TutorialEvent.UI_CONTROL_REMOVED, self.__handleUIRemoved, scope=EVENT_BUS_SCOPE.GLOBAL)
        addListener(TutorialEvent.REFUSE, self.__handleRefuseTraining, scope=EVENT_BUS_SCOPE.GLOBAL)
        addListener(TutorialEvent.RESTART, self.__handleRestartTraining, scope=EVENT_BUS_SCOPE.GLOBAL)
        addListener(ShowWindowEvent.SHOW_TUTORIAL_BATTLE_HISTORY, self.__handleHistoryShow, scope=EVENT_BUS_SCOPE.DEFAULT)
        self.setDisabled(ctx.isInPrebattle or ctx.isInRandomQueue)
        self._subscribe()

    def stop(self):
        if not self.__isStarted:
            return
        removeListener = g_eventBus.removeListener
        removeListener(TutorialEvent.UI_CONTROL_ADDED, self.__handleUIAdded, scope=EVENT_BUS_SCOPE.GLOBAL)
        removeListener(TutorialEvent.UI_CONTROL_REMOVED, self.__handleUIRemoved, scope=EVENT_BUS_SCOPE.GLOBAL)
        removeListener(TutorialEvent.REFUSE, self.__handleRefuseTraining, scope=EVENT_BUS_SCOPE.GLOBAL)
        removeListener(TutorialEvent.RESTART, self.__handleRestartTraining, scope=EVENT_BUS_SCOPE.GLOBAL)
        removeListener(ShowWindowEvent.SHOW_TUTORIAL_BATTLE_HISTORY, self.__handleHistoryShow, scope=EVENT_BUS_SCOPE.DEFAULT)
        self._unsubscribe()
        self.clearGUI()
        self.__isStarted = False

    def findGUI(self, root = None):
        if self.__uiRef and self.__uiRef():
            return True
        else:
            container = self.app.containerManager.getContainer(VIEW_TYPE.DEFAULT)
            result = False
            if container is not None:
                view = container.getView()
                if view is not None:
                    components = view.components
                    if VIEW_ALIAS.LOBBY_HEADER in components:
                        components = components[VIEW_ALIAS.LOBBY_HEADER].components
                        if VIEW_ALIAS.TUTORIAL_CONTROL in components:
                            self.__uiRef = weakref.ref(components[VIEW_ALIAS.TUTORIAL_CONTROL])
                            self.__uiRef().as_setupS(self.__config.copy())
                            self.__uiRef().as_setDisabledS(self._isDisabled)
                            result = True
            return result

    def clearGUI(self):
        self.__uiRef = None
        self.__info = None
        self.__level = None
        return

    def setChapterInfo(self, title, description):
        self.__info = (title, description)
        if self.__uiRef and self.__uiRef():
            self.__uiRef().as_setChapterInfoS(title, description)

    def clearChapterInfo(self):
        if self.__uiRef and self.__uiRef():
            self.__uiRef().as_clearChapterInfoS()

    def setPlayerXPLevel(self, level):
        self.__level = level
        if self.__uiRef and self.__uiRef():
            self.__uiRef().as_setPlayerXPLevelS(level)

    def setTrainingRestartMode(self):
        super(LobbyDispatcher, self).setTrainingRestartMode()
        Waiting.hide('tutorial-chapter-loading')
        if self.__uiRef and self.__uiRef():
            self.__uiRef().as_setRestartModeS()

    def setTrainingRunMode(self):
        super(LobbyDispatcher, self).setTrainingRunMode()
        if self.__uiRef and self.__uiRef():
            self.__uiRef().as_setRunModeS()

    def setDisabled(self, disabled):
        super(LobbyDispatcher, self).setDisabled(disabled)
        if self.__uiRef and self.__uiRef():
            self.app.varsManager.setTutorialDisabled(disabled)
            self.__uiRef().as_setDisabledS(disabled)

    def __handleUIAdded(self, _):
        if self.findGUI():
            ui = self.__uiRef()
            self.app.varsManager.setTutorialDisabled(self._isDisabled)
            ui.as_setupS(self.__config.copy())
            if self.__level is not None:
                ui.as_setPlayerXPLevelS(self.__level)
            if self.__info is not None:
                ui.as_setChapterInfoS(*self.__info)
                ui.as_setDisabledS(self._isDisabled)
                if self._mode is GUIDispatcher.RUN_MODE:
                    ui.as_setRunModeS()
                elif self._mode is GUIDispatcher.RESTART_MODE:
                    ui.as_setRestartModeS()
        return

    def __handleUIRemoved(self, _):
        self.clearGUI()

    def __handleRefuseTraining(self, _):
        self.refuseTraining()

    def __handleRestartTraining(self, _):
        Waiting.show('tutorial-chapter-loading', isSingle=True)
        if not self.restartTraining():
            Waiting.hide('tutorial-chapter-loading')

    def __handleHistoryShow(self, event):
        ctx = event.ctx
        if ctx is None or 'arenaUniqueID' not in ctx:
            LOG_ERROR('Required parameters is not defined to show history', ctx)
            return
        else:
            self._isHistory = True
            self._isFlagsReset = True
            self._historyNotAvailable = self._lastHistoryID != ctx['arenaUniqueID']
            if self._mode == GUIDispatcher.RESTART_MODE:
                Waiting.show('tutorial-chapter-loading', isSingle=True)
                if not self.restartTraining(afterBattle=True):
                    Waiting.hide('tutorial-chapter-loading')
            else:
                from tutorial.loader import g_loader
                g_loader.tutorial.invalidateFlags()
            return
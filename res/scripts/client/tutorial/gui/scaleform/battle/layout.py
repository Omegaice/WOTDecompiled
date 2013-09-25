# Embedded file name: scripts/client/tutorial/gui/Scaleform/battle/layout.py
import weakref
from gui import DEPTH_OF_Aim
from gui.BattleContext import g_battleContext
from gui.Scaleform.Flash import Flash
from helpers import i18n
from helpers.aop import Aspect
from tutorial.control.battle.functional import IDirectionIndicator
from tutorial.control import g_tutorialWeaver
from tutorial.gui import GUIProxy
from tutorial.gui.Scaleform.battle import ScaleformLayout
from tutorial.logger import LOG_CURRENT_EXCEPTION, LOG_MEMORY

class _DirectionIndicator(Flash, IDirectionIndicator):
    __SWF_FILE_NAME = 'DirectionIndicator.swf'
    __FLASH_CLASS = 'WGDirectionIndicatorFlash'
    __FLASH_MC_NAME = 'directionalIndicatorMc'
    __FLASH_SIZE = (680, 680)

    def __init__(self):
        Flash.__init__(self, self.__SWF_FILE_NAME, self.__FLASH_CLASS, [self.__FLASH_MC_NAME])
        self.component.wg_inputKeyMode = 2
        self.component.position.z = DEPTH_OF_Aim
        self.movie.backgroundAlpha = 0.0
        self.movie.scaleMode = 'NoScale'
        self.component.focus = False
        self.component.moveFocus = False
        self.component.heightMode = 'PIXEL'
        self.component.widthMode = 'PIXEL'
        self.flashSize = self.__FLASH_SIZE
        self.component.relativeRadius = 0.5
        self.__dObject = getattr(self.movie, self.__FLASH_MC_NAME, None)
        return

    def __del__(self):
        LOG_MEMORY('DirectionIndicator deleted')

    def setShape(self, shape):
        if self.__dObject:
            self.__dObject.setShape(shape)

    def setDistance(self, distance):
        if self.__dObject:
            self.__dObject.setDistance(distance)

    def setPosition(self, position):
        self.component.position3D = position

    def track(self, position):
        self.active(True)
        self.component.visible = True
        self.component.position3D = position

    def remove(self):
        self.__dObject = None
        self.close()
        return


class ShowBattleAspect(Aspect):

    def __init__(self):
        super(ShowBattleAspect, self).__init__()
        self.__skipFirstInvoke = True

    def atCall(self, cd):
        if self.__skipFirstInvoke:
            self.__skipFirstInvoke = False
            cd.avoid()


def normalizePlayerName(pName):
    if pName.startswith('#battle_tutorial:'):
        pName = i18n.makeString(pName)
    return pName


class BattleLayout(ScaleformLayout):
    __dispatcher = None

    def _resolveGuiRoot(self):
        proxy = None
        try:
            window = GUIProxy.windowsManager().battleWindow
            self._guiRef = weakref.ref(window)
            proxy = window.proxy
            dispatcher = self.getDispatcher()
            if dispatcher is not None and proxy is not None:
                dispatcher.populateUI(proxy)
        except AttributeError:
            LOG_CURRENT_EXCEPTION()

        return proxy

    def _setMovieView(self, movie):
        dispatcher = self.getDispatcher()
        if dispatcher is not None:
            dispatcher.findGUI(root=movie)
        super(BattleLayout, self)._setMovieView(movie)
        return

    def _getDirectionIndicator(self):
        indicator = None
        try:
            indicator = _DirectionIndicator()
        except AttributeError:
            LOG_CURRENT_EXCEPTION()

        return indicator

    def init(self):
        result = super(BattleLayout, self).init()
        if result:
            g_battleContext.setNormalizePlayerName(normalizePlayerName)
            g_tutorialWeaver.weave('gui.WindowsManager', 'WindowsManager', '^showBattle$', aspects=[ShowBattleAspect])
        return result

    def show(self):
        self.windowsManager().showBattle()

    def clear(self):
        if self._guiRef is not None and self._guiRef() is not None:
            if self._movieView is not None:
                self._movieView.clearStage()
        return

    def fini(self):
        g_battleContext.resetNormalizePlayerName()
        dispatcher = self.getDispatcher()
        if dispatcher is not None:
            dispatcher.dispossessUI()
            dispatcher.clearGUI()
        super(BattleLayout, self).fini()
        return

    def getSceneID(self):
        return 'Battle'

    def showMessage(self, text, lookupType = None):
        self.uiHolder.call('battle.VehicleMessagesPanel.ShowMessage', [lookupType, text, 'green'])

    def getGuiRoot(self):
        try:
            root = GUIProxy.windowsManager().battleWindow
        except AttributeError:
            LOG_CURRENT_EXCEPTION()
            root = None

        return root

    @classmethod
    def setDispatcher(cls, dispatcher):
        cls.__dispatcher = dispatcher

    @classmethod
    def getDispatcher(cls):
        return cls.__dispatcher

    def setTrainingPeriod(self, currentIdx, total):
        if self._movieView is not None:
            self._movieView.populateProgressBar(currentIdx, total)
        return

    def setTrainingProgress(self, mask):
        if self._movieView is not None:
            self._movieView.setTrainingProgressBar(mask)
        return

    def setChapterProgress(self, total, mask):
        if self._movieView is not None:
            self._movieView.setChapterProgressBar(total, mask)
        return
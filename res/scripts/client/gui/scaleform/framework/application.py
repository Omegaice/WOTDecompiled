# 2013.11.15 11:26:27 EST
# Embedded file name: scripts/client/gui/Scaleform/framework/application.py
import weakref
import BigWorld
import GUI
from debug_utils import LOG_ERROR, LOG_CURRENT_EXCEPTION, LOG_DEBUG
from gui import SystemMessages, g_guiResetters, g_repeatKeyHandlers
from gui.Scaleform import SCALEFORM_SWF_PATH_V3
from gui.Scaleform.Flash import Flash
from gui.Scaleform.framework import AppRef, VIEW_TYPE
from gui.Scaleform.framework.entities.abstract.ApplicationMeta import ApplicationMeta
from gui.Scaleform.framework.managers import ContainerManager
from gui.Scaleform.framework.managers import LoaderManager
from gui.Scaleform.framework.ToolTip import ToolTip
from gui.Scaleform.framework.managers.StatsStorage import StatsStorage
from gui.shared.utils.key_mapping import getScaleformKey, voidSymbol
from helpers.i18n import convert, makeString

class AppBase(Flash):

    def __init__(self):
        self.proxy = weakref.proxy(self)
        Flash.__init__(self, 'Application.swf', path=SCALEFORM_SWF_PATH_V3)

    def beforeDelete(self):
        super(AppBase, self).beforeDelete()
        self.proxy = None
        return

    def active(self, state):
        if state is not self.isActive:
            if state:
                self._setup()
            super(AppBase, self).active(state)

    def bindExCallbackToKey(self, key, command, function):
        try:
            gfx_key = getScaleformKey(key)
            if gfx_key != voidSymbol:
                self.movie.invoke(('bindExCallbackToKey', [gfx_key, command]))
                self.addExternalCallback(command, function)
            else:
                LOG_ERROR("Can't convert key:", key)
        except:
            LOG_CURRENT_EXCEPTION()

    def clearExCallbackToKey(self, key, command, function = None):
        try:
            gfx_key = getScaleformKey(key)
            if gfx_key != voidSymbol:
                self.movie.invoke(('clearExCallbackToKey', [gfx_key]))
                self.removeExternalCallback(command, function=function)
            else:
                LOG_ERROR("Can't convert key:", key)
        except:
            LOG_CURRENT_EXCEPTION()

    def quit(self):
        """ Close client """
        BigWorld.quit()

    def logoff(self):
        """ Log current account off """
        self.disconnect()

    def disconnect(self, disconnectNow = False):

        def logOff():
            BigWorld.disconnect()
            BigWorld.clearEntitiesAndSpaces()

        if disconnectNow:
            logOff()
        else:
            BigWorld.callback(0.1, logOff)

    def _setup(self):
        self.movie.setFocussed(SCALEFORM_SWF_PATH_V3)
        BigWorld.wg_setRedefineKeysMode(True)
        BigWorld.wg_setScreenshotNotifyCallback(self.__screenshotNotifyCallback)

    def __screenshotNotifyCallback(self, path):
        SystemMessages.pushMessage(convert(makeString('#menu:screenshot/save')) % {'path': path}, SystemMessages.SM_TYPE.Information)


class App(ApplicationMeta, AppBase):

    def __init__(self, businessHandler):
        super(App, self).__init__()
        if businessHandler is None:
            raise Exception, 'Business handler can not be None'
        self._businessHandler = businessHandler
        self._contextMgr = None
        self._soundMgr = None
        self._loaderMgr = None
        self._containerMgr = None
        self._toolTipMgr = None
        self._colorSchemeMgr = None
        self._varsMgr = None
        self._statsStorage = None
        self.__toolTip = None
        self._guiItemsMgr = None
        self._voiceChatMgr = None
        self._gameInputMgr = None
        self._utilsMgr = None
        AppRef.setReference(self.proxy)
        self.__aliasToLoad = []
        self.addExternalCallback('registerApplication', self.onFlashAppInit)
        return

    @property
    def containerManager(self):
        return self._containerMgr

    @property
    def soundManager(self):
        return self._soundMgr

    @property
    def contextMenuManager(self):
        return self._contextMgr

    @property
    def loaderManager(self):
        return self._loaderMgr

    @property
    def tooltipManager(self):
        return self._toolTipMgr

    @property
    def waitingManager(self):
        return self.__getWaitingFromContainer()

    @property
    def containerManager(self):
        return self._containerMgr

    @property
    def colorManager(self):
        return self._colorSchemeMgr

    @property
    def itemsManager(self):
        return self._guiItemsMgr

    @property
    def voiceChatManager(self):
        return self._voiceChatMgr

    @property
    def gameInputManager(self):
        return self._gameInputMgr

    @property
    def utilsManager(self):
        return self._utilsMgr

    @property
    def varsManager(self):
        return self._varsMgr

    @property
    def cursorMgr(self):
        return self.__getCursorFromContainer()

    def onFlashAppInit(self):
        self.setFlashObject(self.movie.root)
        self.movie.backgroundAlpha = 0.0
        self.afterCreate()

    def afterCreate(self):
        LOG_DEBUG('[App] afterCreate')
        AppBase.afterCreate(self)
        self._createManagers()
        self.__validateManagers()
        self.as_registerManagersS()
        g_guiResetters.add(self.onUpdateStage)
        self.onUpdateStage()
        g_repeatKeyHandlers.add(self.component.handleKeyEvent)
        while len(self.__aliasToLoad):
            alias, name, kargs, kwargs = self.__aliasToLoad.pop(0)
            self.loadView(alias, name, *kargs, **kwargs)

        self._loadCursor()
        self._loadWaiting()

    def beforeDelete(self):
        LOG_DEBUG('[App] beforeDelete')
        if self._containerMgr is not None:
            self._containerMgr.destroy()
            self._containerMgr = None
        if self._loaderMgr is not None:
            self._loaderMgr.destroy()
            self._loaderMgr = None
        if self._contextMgr is not None:
            self._contextMgr.destroy()
            self._contextMgr = None
        if self._soundMgr is not None:
            self._soundMgr.destroy()
            self._soundMgr = None
        if self._varsMgr is not None:
            self._varsMgr.destroy()
            self._varsMgr = None
        if self._toolTipMgr is not None:
            self._toolTipMgr.destroy()
            self._toolTipMgr = None
        if self.__toolTip is not None:
            self.__toolTip.destroy()
            self.__toolTip = None
        if self._colorSchemeMgr is not None:
            self._colorSchemeMgr.destroy()
            self._colorSchemeMgr = None
        if self._statsStorage is not None:
            self._statsStorage.destroy()
            self._statsStorage = None
        if self._guiItemsMgr is not None:
            self._guiItemsMgr.destroy()
            self._guiItemsMgr = None
        if self._voiceChatMgr is not None:
            self._voiceChatMgr.destroy()
            self._voiceChatMgr = None
        if self._gameInputMgr is not None:
            self._gameInputMgr.destroy()
            self._gameInputMgr = None
        if self._utilsMgr is not None:
            self._utilsMgr.destroy()
            self._utilsMgr = None
        if self._businessHandler is not None:
            self._businessHandler.destroy()
            self._businessHandler = None
        g_guiResetters.discard(self.onUpdateStage)
        g_repeatKeyHandlers.discard(self.component.handleKeyEvent)
        self._dispose()
        super(App, self).beforeDelete()
        AppRef.clearReference()
        return

    def loadView(self, newViewAlias, name = None, *args, **kwargs):
        if self._containerMgr:
            self._containerMgr.load(newViewAlias, name, *args, **kwargs)
        else:
            self.__aliasToLoad.append((newViewAlias,
             name,
             args,
             kwargs))

    def setLoaderMgr(self, flashObject):
        self._loaderMgr.setFlashObject(flashObject)

    def setContainerMgr(self, flashObject):
        self._containerMgr.setFlashObject(flashObject)

    def setColorSchemeMgr(self, flashObject):
        self._colorSchemeMgr.setFlashObject(flashObject)

    def setGlobalVarsMgr(self, flashObject):
        self._varsMgr.setFlashObject(flashObject)

    def setContextMenuMgr(self, flashObject):
        self._contextMgr.setFlashObject(flashObject)

    def setSoundMgr(self, flashObject):
        self._soundMgr.setFlashObject(flashObject)

    def setTooltipMgr(self, flashObject):
        self.__toolTip.setFlashObject(flashObject)

    def setGameInputMgr(self, flashObject):
        self._gameInputMgr.setFlashObject(flashObject)

    def setGuiItemsMgr(self, flashObject):
        self._guiItemsMgr.setFlashObject(flashObject)

    def setVoiceChatMgr(self, flashObject):
        self._voiceChatMgr.setFlashObject(flashObject)

    def setUtilsMgr(self, flashObject):
        self._utilsMgr.setFlashObject(flashObject)

    def onUpdateStage(self):
        self.as_updateStageS(*GUI.screenResolution()[:2])

    def _createManagers(self):
        self._loaderMgr = LoaderManager()
        self._containerMgr = ContainerManager(self._loaderMgr)
        self._statsStorage = StatsStorage()
        self.__toolTip = ToolTip()

    def _loadCursor(self):
        raise NotImplementedError, 'App._loadCursor must be overridden'

    def _loadWaiting(self):
        raise NotImplementedError, 'App._loadWaiting must be overridden'

    def __getCursorFromContainer(self):
        if self._containerMgr is not None:
            return self._containerMgr.getView(VIEW_TYPE.CURSOR)
        else:
            return

    def __getWaitingFromContainer(self):
        if self._containerMgr is not None:
            return self._containerMgr.getView(VIEW_TYPE.WAITING)
        else:
            return
            return

    def __validateManagers(self):
        if self._loaderMgr is None:
            raise Exception, 'Loader manager is not defined'
        if self._containerMgr is None:
            raise Exception, 'ContainerMgr manager is not defined'
        if self._soundMgr is None:
            raise Exception, 'Sound manager is not defined'
        if self._colorSchemeMgr is None:
            raise Exception, 'Color scheme manager is not defined'
        if self._statsStorage is None:
            raise Exception, 'Stats storage manager is not defined'
        if self._toolTipMgr is None:
            raise Exception, 'Tooltip manager is not defined'
        if self._varsMgr is None:
            raise Exception, 'Global vars manager is not defined'
        if self._gameInputMgr is None:
            raise Exception, 'Game input manager is not defined'
        return
# okay decompyling res/scripts/client/gui/scaleform/framework/application.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:26:27 EST

import WebBrowser
from adisp import process
import constants
from debug_utils import LOG_DEBUG
from gui.shared import events
from gui.Scaleform.daapi.business_layer import BusinessHandler
from gui.Scaleform.daapi.settings import VIEW_ALIAS
from gui.Scaleform.framework.application import App
from gui.Scaleform.managers.GlobalVarsManager import GlobalVarsManager
from gui.Scaleform.managers.ToolTipManager import ToolTipManager
from gui.Scaleform.managers.SoundManager import SoundManager
from gui.Scaleform.managers.ColorSchemeManager import ColorSchemeManager
from gui.Scaleform.managers.ContextMenuManager import ContextMenuManager
from gui.Scaleform.managers.GuiItemsManager import GuiItemsManager
from gui.Scaleform.managers.VoiceChatManager import VoiceChatManager
from gui.Scaleform.managers.UtilsManager import UtilsManager
from gui.Scaleform.managers.GameInputMgr import GameInputMgr

class AppEntry(App):

    def __init__(self):
        businessHandler = BusinessHandler()
        businessHandler.create()
        super(AppEntry, self).__init__(businessHandler)
        self.browser = None
        return

    def _createManagers(self):
        super(AppEntry, self)._createManagers()
        self._varsMgr = GlobalVarsManager()
        self._soundMgr = SoundManager()
        self._toolTipMgr = ToolTipManager()
        self._colorSchemeMgr = ColorSchemeManager()
        self._contextMgr = ContextMenuManager()
        self._guiItemsMgr = GuiItemsManager()
        self._voiceChatMgr = VoiceChatManager()
        self._utilsMgr = UtilsManager()
        self._gameInputMgr = GameInputMgr()

    def _loadCursor(self):
        self._containerMgr.load(VIEW_ALIAS.CURSOR)

    def _loadWaiting(self):
        self._containerMgr.load(VIEW_ALIAS.WAITING)

    def afterCreate(self):
        super(AppEntry, self).afterCreate()
        if constants.IS_CHINA:
            self.browser = WebBrowser.ChinaWebBrowser(self, 'BrowserBg', (990, 550))
        self.fireEvent(events.GUICommonEvent(events.GUICommonEvent.APP_STARTED))

    def beforeDelete(self):
        if self.browser is not None:
            self.browser.destroy()
        super(AppEntry, self).beforeDelete()
        return

    def logoff(self):
        super(AppEntry, self).logoff()
        self.fireEvent(events.ShowViewEvent(events.ShowViewEvent.SHOW_LOGIN))

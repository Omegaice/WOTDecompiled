# Embedded file name: scripts/client/gui/Scaleform/daapi/view/lobby/LobbyView.py
import BigWorld
import constants
from debug_utils import LOG_DEBUG
from PlayerEvents import g_playerEvents
from gui import GUI_SETTINGS
from gui.BattleContext import g_battleContext
from gui.Scaleform.daapi.view.meta.LobbyPageMeta import LobbyPageMeta
from gui.Scaleform.framework.entities.View import View
from gui.Scaleform.framework.managers.containers import POP_UP_CRITERIA
from gui.prb_control.dispatcher import g_prbLoader
from gui.shared.utils.HangarSpace import g_hangarSpace
from gui.shared import EVENT_BUS_SCOPE, events
from gui.Scaleform.framework import VIEW_TYPE, AppRef
from gui.Scaleform.Waiting import Waiting
from gui.Scaleform.daapi.settings.views import VIEW_ALIAS
from gui.Scaleform.daapi.view.lobby.prb_windows.sf_settings import PRB_WINDOW_VIEW_ALIAS
from messenger.gui.Scaleform.sf_settings import MESSENGER_VIEW_ALIAS

class LobbyView(View, LobbyPageMeta, AppRef):
    VIEW_WAITING_EXCLUDED = (VIEW_ALIAS.SIMPLE_DIALOG,
     VIEW_ALIAS.SYSTEM_MESSAGE_DIALOG,
     VIEW_ALIAS.NOTIFICATIONS_LIST,
     MESSENGER_VIEW_ALIAS.CHANNEL_MANAGEMENT_WINDOW,
     MESSENGER_VIEW_ALIAS.CONNECT_TO_SECURE_CHANNEL_WINDOW,
     MESSENGER_VIEW_ALIAS.CONTACTS_WINDOW,
     MESSENGER_VIEW_ALIAS.LAZY_CHANNEL_WINDOW,
     MESSENGER_VIEW_ALIAS.LOBBY_CHANNEL_WINDOW,
     PRB_WINDOW_VIEW_ALIAS.BATTLE_SESSION_LIST,
     PRB_WINDOW_VIEW_ALIAS.COMPANIES_WINDOW,
     PRB_WINDOW_VIEW_ALIAS.NOTIFICATION_INVITES_WINDOW)

    class COMPONENTS:
        HEADER = 'lobbyHeader'

    def __init__(self, isInQueue):
        View.__init__(self)

    def getSubContainerType(self):
        return VIEW_TYPE.LOBBY_SUB

    def _populate(self):
        View._populate(self)
        g_prbLoader.setEnabled(True)
        self.addListener(events.LobbySimpleEvent.SHOW_HELPLAYOUT, self.__showHelpLayout, EVENT_BUS_SCOPE.LOBBY)
        self.addListener(events.LobbySimpleEvent.CLOSE_HELPLAYOUT, self.__closeHelpLayout, EVENT_BUS_SCOPE.LOBBY)
        g_playerEvents.onVehicleBecomeElite += self.__onVehicleBecomeElite
        self.app.loaderManager.onViewLoadInit += self.__onViewLoadInit
        self.app.loaderManager.onViewLoaded += self.__onViewLoaded
        self.app.loaderManager.onViewLoadError += self.__onViewLoadError
        self.__showBattleResults()
        if self.app.browser is not None and constants.IS_CHINA:
            self.app.browser.checkBattlesCounter()
        return

    def _dispose(self):
        self.app.loaderManager.onViewLoadError -= self.__onViewLoadError
        self.app.loaderManager.onViewLoaded -= self.__onViewLoaded
        self.app.loaderManager.onViewLoadInit -= self.__onViewLoadInit
        self.app.containerManager.removeContainer(VIEW_TYPE.LOBBY_SUB)
        g_playerEvents.onVehicleBecomeElite -= self.__onVehicleBecomeElite
        self.removeListener(events.LobbySimpleEvent.SHOW_HELPLAYOUT, self.__showHelpLayout, EVENT_BUS_SCOPE.LOBBY)
        self.removeListener(events.LobbySimpleEvent.CLOSE_HELPLAYOUT, self.__closeHelpLayout, EVENT_BUS_SCOPE.LOBBY)
        View._dispose(self)

    def __showHelpLayout(self, event):
        self.as_showHelpLayoutS()

    def __closeHelpLayout(self, event):
        self.as_closeHelpLayoutS()

    def __onVehicleBecomeElite(self, vehTypeCompDescr):
        self.fireEvent(events.ShowWindowEvent(events.ShowWindowEvent.SHOW_ELITE_VEHICLE_WINDOW, {'vehTypeCompDescr': vehTypeCompDescr}))

    def moveSpace(self, dx, dy, dz):
        if g_hangarSpace.space:
            g_hangarSpace.space.handleMouseEvent(int(dx), int(dy), int(dz))

    def __onViewLoadInit(self, view):
        if view is not None and view.settings is not None:
            self.__subViewTransferStart(view.settings.alias)
        return

    def __onViewLoaded(self, view):
        if view is not None and view.settings is not None:
            self.__subViewTransferStop(view.settings.alias)
        return

    def __onViewLoadError(self, _, view):
        if view is not None and view.settings is not None:
            self.__subViewTransferStop(view.settings.alias)
        return

    def __subViewTransferStart(self, alias):
        if alias not in self.VIEW_WAITING_EXCLUDED:
            Waiting.show('loadPage')

    def __subViewTransferStop(self, alias):
        if alias not in self.VIEW_WAITING_EXCLUDED:
            Waiting.hide('loadPage')

    def __showBattleResults(self):
        if GUI_SETTINGS.battleStatsInHangar and g_battleContext.lastArenaUniqueID:
            self.fireEvent(events.ShowWindowEvent(events.ShowWindowEvent.SHOW_BATTLE_RESULTS, {'arenaUniqueID': g_battleContext.lastArenaUniqueID}))
            g_battleContext.lastArenaUniqueID = None
        return
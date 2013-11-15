# 2013.11.15 11:26:05 EST
# Embedded file name: scripts/client/gui/Scaleform/daapi/view/lobby/LobbyView.py
import BigWorld
import constants
from debug_utils import LOG_DEBUG
from PlayerEvents import g_playerEvents
from gui import GUI_SETTINGS
from gui.BattleContext import g_battleContext
from gui.Scaleform.daapi.view.meta.LobbyPageMeta import LobbyPageMeta
from gui.Scaleform.framework.entities.View import View
from gui.prb_control.dispatcher import g_prbLoader
from gui.shared.utils.HangarSpace import g_hangarSpace
from gui.shared import EVENT_BUS_SCOPE, events
from gui.Scaleform.framework import VIEW_TYPE, AppRef
from gui.Scaleform.Waiting import Waiting
from gui.Scaleform.daapi.settings.views import VIEW_ALIAS

class LobbyView(View, LobbyPageMeta, AppRef):
    VIEW_WAITING = (VIEW_ALIAS.LOBBY_HANGAR,
     VIEW_ALIAS.LOBBY_INVENTORY,
     VIEW_ALIAS.LOBBY_SHOP,
     VIEW_ALIAS.LOBBY_PROFILE,
     VIEW_ALIAS.LOBBY_BARRACKS,
     VIEW_ALIAS.LOBBY_TRAININGS,
     VIEW_ALIAS.LOBBY_TRAINING_ROOM,
     VIEW_ALIAS.LOBBY_CUSTOMIZATION,
     VIEW_ALIAS.LOBBY_RESEARCH,
     VIEW_ALIAS.LOBBY_TECHTREE,
     VIEW_ALIAS.BATTLE_QUEUE,
     VIEW_ALIAS.BATTLE_LOADING)

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

    def __onViewLoadError(self, token, msg, item):
        if item is not None and item.pyEntity is not None:
            self.__subViewTransferStop(item.pyEntity.settings.alias)
        return

    def __subViewTransferStart(self, alias):
        if alias in self.VIEW_WAITING:
            Waiting.show('loadPage')

    def __subViewTransferStop(self, alias):
        if alias in self.VIEW_WAITING:
            Waiting.hide('loadPage')

    def __showBattleResults(self):
        if GUI_SETTINGS.battleStatsInHangar and g_battleContext.lastArenaUniqueID:
            self.fireEvent(events.ShowWindowEvent(events.ShowWindowEvent.SHOW_BATTLE_RESULTS, {'arenaUniqueID': g_battleContext.lastArenaUniqueID}))
            g_battleContext.lastArenaUniqueID = None
        return
# okay decompyling res/scripts/client/gui/scaleform/daapi/view/lobby/lobbyview.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:26:05 EST

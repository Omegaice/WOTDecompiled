from CurrentVehicle import g_currentVehicle
from PlayerEvents import g_playerEvents
from constants import IGR_TYPE
from gui import game_control
from gui.Scaleform.daapi.settings.views import VIEW_ALIAS
from gui.Scaleform.framework.managers.containers import POP_UP_CRITERIA
from gui.prb_control.prb_helpers import PrbListener
from gui.ClientUpdateManager import g_clientUpdateManager
from gui.Scaleform.framework import VIEW_TYPE
from gui.Scaleform.Waiting import Waiting
from gui.Scaleform.daapi.view.meta.HangarMeta import HangarMeta
from gui.Scaleform.daapi import LobbySubView
from gui.shared import events
from gui.shared.event_bus import EVENT_BUS_SCOPE
from gui.shared.events import LobbySimpleEvent

class Hangar(LobbySubView, HangarMeta, PrbListener):

    class COMPONENTS:
        CAROUSEL = 'tankCarousel'
        PARAMS = 'params'
        CREW = 'crew'
        AMMO_PANEL = 'ammunitionPanel'
        RESEARCH_PANEL = 'researchPanel'
        TMEN_XP_PANEL = 'tmenXpPanel'

    def __init__(self):
        LobbySubView.__init__(self, 0)

    def _populate(self):
        LobbySubView._populate(self)
        g_playerEvents.onVehicleBecomeElite += self.__onVehicleBecomeElite
        g_playerEvents.onBattleResultsReceived += self.onFittingUpdate
        g_currentVehicle.onChanged += self.__onCurrentVehicleChanged
        game_control.g_instance.igr.onIgrTypeChanged += self.__onIgrTypeChanged
        self.startPrbGlobalListening()
        game_control.g_instance.aogas.enableNotifyAccount()
        g_clientUpdateManager.addCallbacks({'inventory.1': self.onVehiclesUpdate,
         'stats.multipliedXPVehs_r': self.onVehiclesUpdate,
         'stats.slots': self.onVehiclesUpdate,
         'stats.vehTypeXP': self.onVehiclesUpdate,
         'stats.unlocks': self.onVehiclesUpdate,
         'stats.eliteVehicles': self.onVehiclesUpdate,
         'stats.credits': self.onFittingUpdate,
         'stats.gold': self.onFittingUpdate,
         'stats.vehicleSellsLeft': self.onFittingUpdate,
         'stats.vehTypeLocks': self.onVehiclesUpdate})
        self.__onIgrTypeChanged()
        self.__updateAll()

    def onEscape(self):
        dialogsContainer = self.app.containerManager.getContainer(VIEW_TYPE.DIALOG)
        if not dialogsContainer.getView(criteria={POP_UP_CRITERIA.VIEW_ALIAS: VIEW_ALIAS.LOBBY_MENU}):
            self.fireEvent(events.ShowViewEvent(events.ShowViewEvent.SHOW_LOBBY_MENU), scope=EVENT_BUS_SCOPE.LOBBY)

    def showHelpLayout(self):
        containerManager = self.app.containerManager
        dialogsContainer = containerManager.getContainer(VIEW_TYPE.DIALOG)
        windowsContainer = containerManager.getContainer(VIEW_TYPE.WINDOW)
        if not dialogsContainer.getViewCount() and not windowsContainer.getViewCount():
            self.fireEvent(LobbySimpleEvent(LobbySimpleEvent.SHOW_HELPLAYOUT), scope=EVENT_BUS_SCOPE.LOBBY)
            self.as_showHelpLayoutS()

    def closeHelpLayout(self):
        self.fireEvent(LobbySimpleEvent(LobbySimpleEvent.CLOSE_HELPLAYOUT), scope=EVENT_BUS_SCOPE.LOBBY)
        self.as_closeHelpLayoutS()

    def _dispose(self):
        g_clientUpdateManager.removeObjectCallbacks(self)
        g_playerEvents.onVehicleBecomeElite -= self.__onVehicleBecomeElite
        g_playerEvents.onBattleResultsReceived -= self.onFittingUpdate
        g_currentVehicle.onChanged -= self.__onCurrentVehicleChanged
        game_control.g_instance.igr.onIgrTypeChanged -= self.__onIgrTypeChanged
        self.closeHelpLayout()
        self.stopPrbGlobalListening()
        LobbySubView._dispose(self)

    def __updateAmmoPanel(self):
        if self.ammoPanel:
            self.ammoPanel.update()

    def __updateParams(self):
        if self.paramsPanel:
            self.paramsPanel.update()

    def __updateCarousel(self):
        if self.tankCarousel is not None:
            self.tankCarousel.updateVehicles()
        return

    def __updateResearchPanel(self):
        panel = self.researchPanel
        if panel is not None:
            panel.onCurrentVehicleChanged()
        return

    def __updateCrew(self):
        if self.crewPanel is not None:
            self.crewPanel.updateTankmen()
        return

    @property
    def tankCarousel(self):
        return self.components.get(self.COMPONENTS.CAROUSEL)

    @property
    def ammoPanel(self):
        return self.components.get(self.COMPONENTS.AMMO_PANEL)

    @property
    def paramsPanel(self):
        return self.components.get(self.COMPONENTS.PARAMS)

    @property
    def crewPanel(self):
        return self.components.get(self.COMPONENTS.CREW)

    @property
    def researchPanel(self):
        return self.components.get(self.COMPONENTS.RESEARCH_PANEL)

    def onVehiclesUpdate(self, *args):
        self.__updateCarousel()
        self.__updateAmmoPanel()

    def onPrbFunctionalFinished(self):
        self.__updateAmmoPanel()
        self.__updateState()

    def onPlayerStateChanged(self, functional, roster, accountInfo):
        if accountInfo.isCurrentPlayer():
            self.__updateAmmoPanel()
            self.__updateState()

    def __onVehicleBecomeElite(self, vehTypeCompDescr):
        self.__updateCarousel()

    def onFittingUpdate(self, *args):
        self.__updateAmmoPanel()

    def __updateAll(self):
        Waiting.show('updateVehicle')
        self.__updateAmmoPanel()
        self.__updateState()
        self.__updateCarousel()
        self.__updateParams()
        self.__updateResearchPanel()
        self.__updateCrew()
        Waiting.hide('updateVehicle')

    def __onCurrentVehicleChanged(self):
        self.__updateAll()

    def __onIgrTypeChanged(self, *args):
        self.as_setIsIGRS(game_control.g_instance.igr.getRoomType() != IGR_TYPE.NONE)

    def __updateState(self):
        isVehicleDisabled = False
        if self.prbFunctional is not None:
            permission = self.prbFunctional.getPermissions()
            if permission is not None:
                isVehicleDisabled = not permission.canChangeVehicle()
        msg, msgLvl = g_currentVehicle.getHangarMessage()
        isPresent = g_currentVehicle.isPresent()
        self.as_readyToFightS(g_currentVehicle.isReadyToFight(), msg, msgLvl, isPresent, isVehicleDisabled, g_currentVehicle.isCrewFull(), g_currentVehicle.isInHangar(), g_currentVehicle.isBroken() if isPresent else False)
        return

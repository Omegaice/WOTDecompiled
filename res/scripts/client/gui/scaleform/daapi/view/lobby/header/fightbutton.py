from CurrentVehicle import g_currentVehicle
from account_helpers import isDemonstrator
from adisp import process
from constants import PREBATTLE_TYPE
from debug_utils import LOG_ERROR
from gui import GUI_SETTINGS
from gui.ClientUpdateManager import g_clientUpdateManager
from gui.Scaleform.daapi.settings import VIEW_ALIAS
from gui.Scaleform.framework import AppRef, VIEW_TYPE
from gui.Scaleform.framework.managers.containers import POP_UP_CRITERIA
from gui.Scaleform.locale.MENU import MENU
from gui.prb_control import areSpecBattlesHidden
from gui.prb_control.dispatcher import g_prbLoader
from gui.prb_control.formatters.tooltips import getActionDisabledTooltip
from gui.prb_control.context import PrebattleAction
from gui.prb_control.settings import PREBATTLE_ACTION_NAME
from gui.shared import EVENT_BUS_SCOPE, events
from gui.Scaleform.locale.TOOLTIPS import TOOLTIPS
from gui.shared.events import ShowWindowEvent
from gui.shared.utils.requesters import StatsRequester
from gui.Scaleform.daapi.view.meta.FightButtonMeta import FightButtonMeta
from gui.Scaleform.framework.entities.DAAPIModule import DAAPIModule
__author__ = 'd_buynitsky'

class FightButton(FightButtonMeta, DAAPIModule, AppRef):

    def __init__(self):
        super(FightButton, self).__init__()
        self.__menuLabels = {PREBATTLE_TYPE.SQUAD: MENU.HEADERBUTTONS_BATTLE_MENU_SQUAD,
         PREBATTLE_TYPE.TRAINING: MENU.HEADERBUTTONS_BATTLE_MENU_TRAINING,
         PREBATTLE_TYPE.COMPANY: MENU.HEADERBUTTONS_BATTLE_MENU_TEAM,
         PREBATTLE_TYPE.CLAN: MENU.HEADERBUTTONS_BATTLE_MENU_BATTLE_SESSION,
         PREBATTLE_TYPE.TOURNAMENT: MENU.HEADERBUTTONS_BATTLE_MENU_BATTLE_SESSION}
        self.__actionsLockedInViews = set([VIEW_ALIAS.BATTLE_QUEUE, VIEW_ALIAS.LOBBY_TRAININGS, VIEW_ALIAS.LOBBY_TRAINING_ROOM])
        self.__isActionsLocked = False

    @process
    def _populate(self):
        super(FightButton, self)._populate()
        g_currentVehicle.onChanged += self.update
        self.app.containerManager.onViewAddedToContainer += self.__onViewAddedToContainer
        self.addListener(events.FightButtonEvent.FIGHT_BUTTON_UPDATE, self.__handleFightButtonUpdate, scope=EVENT_BUS_SCOPE.LOBBY)
        g_clientUpdateManager.addCallbacks({'account.attrs': self.updateDemonstratorButton})
        accountAttrs = yield StatsRequester().getAccountAttrs()
        self.updateDemonstratorButton(accountAttrs)

    def _dispose(self):
        super(FightButton, self)._dispose()
        g_currentVehicle.onChanged -= self.update
        self.app.containerManager.onViewAddedToContainer -= self.__onViewAddedToContainer
        self.removeListener(events.FightButtonEvent.FIGHT_BUTTON_UPDATE, self.__handleFightButtonUpdate, scope=EVENT_BUS_SCOPE.LOBBY)
        g_clientUpdateManager.removeObjectCallbacks(self)

    def update(self):
        prbDispatcher = g_prbLoader.getDispatcher()
        if not prbDispatcher:
            return
        else:
            prbFunctional = prbDispatcher.getPrbFunctional()
            prbType = prbFunctional.getPrbType()
            inPrebattle = prbType is not 0
            isTraining = prbType is PREBATTLE_TYPE.TRAINING
            disableHint = None
            disabled = False
            if self.__isActionsLocked:
                disabled = True
            else:
                canDo, restriction = prbDispatcher.canPlayerDoAction()
                if not canDo:
                    disabled = True
                    disableHint = getActionDisabledTooltip(restriction, functional=prbFunctional)
            self.__disableFightButton(disabled, disableHint)
            label = MENU.HEADERBUTTONS_BATTLE
            isCreator = prbFunctional.isCreator()
            if not isTraining and not isCreator:
                playerInfo = prbFunctional.getPlayerInfo()
                if inPrebattle and playerInfo is not None:
                    if playerInfo.isReady():
                        label = MENU.HEADERBUTTONS_NOTREADY
                    else:
                        label = MENU.HEADERBUTTONS_READY
            menu = self.__menuLabels.get(prbType, MENU.HEADERBUTTONS_BATTLE_MENU_STANDART)
            fightTypes = list()
            fightTypes.append({'label': MENU.HEADERBUTTONS_BATTLE_TYPES_STANDART,
             'data': PREBATTLE_ACTION_NAME.RANDOM_QUEUE,
             'disabled': inPrebattle,
             'tooltip': TOOLTIPS.BATTLETYPES_STANDART})
            if prbType is PREBATTLE_TYPE.SQUAD:
                fightTypes.append({'label': '#menu:headerButtons/battle/types/squadLeave%s' % ('Owner' if isCreator else ''),
                 'data': PREBATTLE_ACTION_NAME.PREBATTLE_LEAVE,
                 'disabled': False,
                 'tooltip': None})
            else:
                fightTypes.append({'label': MENU.HEADERBUTTONS_BATTLE_TYPES_SQUAD,
                 'data': PREBATTLE_ACTION_NAME.SQUAD,
                 'disabled': inPrebattle,
                 'tooltip': TOOLTIPS.BATTLETYPES_SQUAD})
            fightTypes.append({'label': MENU.HEADERBUTTONS_BATTLE_TYPES_TRAINING,
             'data': PREBATTLE_ACTION_NAME.TRAINING_LIST,
             'disabled': inPrebattle and inPrebattle and not isTraining,
             'tooltip': TOOLTIPS.BATTLETYPES_TRAINING})
            fightTypes.append({'label': MENU.HEADERBUTTONS_BATTLE_TYPES_COMPANY,
             'data': PREBATTLE_ACTION_NAME.COMPANY_LIST,
             'disabled': False,
             'tooltip': TOOLTIPS.BATTLETYPES_COMPANY})
            if GUI_SETTINGS.specPrebatlesVisible:
                fightTypes.append({'label': MENU.HEADERBUTTONS_BATTLE_TYPES_SPEC,
                 'data': PREBATTLE_ACTION_NAME.SPEC_BATTLE_LIST,
                 'disabled': areSpecBattlesHidden(),
                 'tooltip': TOOLTIPS.BATTLETYPES_SPEC})
            self.__onFightButtonSet(label, menu, fightTypes)
            self.fireEvent(events.LobbySimpleEvent(events.LobbySimpleEvent.UPDATE_TANK_PARAMS), scope=EVENT_BUS_SCOPE.LOBBY)
            return

    def __onViewAddedToContainer(self, _, pyEntity):
        settings = pyEntity.settings
        if settings.type is VIEW_TYPE.LOBBY_SUB:
            alias = settings.alias
            if alias == VIEW_ALIAS.BATTLE_LOADING:
                return
            if alias in self.__actionsLockedInViews:
                isActionsLocked = True
            else:
                isActionsLocked = False
            self.__isActionsLocked = isActionsLocked
            self.update()

    def __handleFightButtonUpdate(self, event):
        self.update()

    def fightClick(self, mapID = None, actionName = ''):
        dispatcher = g_prbLoader.getDispatcher()
        if dispatcher is not None:
            dispatcher.doAction(PrebattleAction(actionName, mapID=mapID))
        else:
            LOG_ERROR('Prebattle dispatcher is not defined')
        return

    def fightSelectClick(self, actionName):
        dispatcher = g_prbLoader.getDispatcher()
        if dispatcher is not None:
            dispatcher.doAction(PrebattleAction(actionName))
        else:
            LOG_ERROR('Prebattle dispatcher is not defined')
        return

    def __onFightButtonSet(self, label, menu, fightTypes):
        self.as_setFightButtonS(label, menu, fightTypes)

    def __disableFightButton(self, isDisabled, toolTip):
        self.as_disableFightButtonS(isDisabled, toolTip)

    def updateDemonstratorButton(self, accountAttrs):
        self.as_setDemonstratorButtonS(isDemonstrator(accountAttrs))

    def demoClick(self):
        demonstratorWindow = self.app.containerManager.getView(VIEW_TYPE.WINDOW, criteria={POP_UP_CRITERIA.VIEW_ALIAS: VIEW_ALIAS.DEMONSTRATOR_WINDOW})
        if demonstratorWindow is not None:
            demonstratorWindow.onWindowClose()
        else:
            self.fireEvent(ShowWindowEvent(ShowWindowEvent.SHOW_DEMONSTRATOR_WINDOW))
        return

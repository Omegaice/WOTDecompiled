# 2013.11.15 11:26:04 EST
# Embedded file name: scripts/client/gui/Scaleform/daapi/view/lobby/header/FightButton.py
from CurrentVehicle import g_currentVehicle
from account_helpers import isDemonstrator
from account_helpers.AccountSettings import AccountSettings
from adisp import process
from constants import PREBATTLE_TYPE
from debug_utils import LOG_ERROR, LOG_DEBUG
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
from helpers import i18n
__author__ = 'd_buynitsky'

class FightButton(FightButtonMeta, DAAPIModule, AppRef):

    def __init__(self):
        super(FightButton, self).__init__()
        self.__menuLabels = {PREBATTLE_TYPE.SQUAD: MENU.HEADERBUTTONS_BATTLE_MENU_SQUAD,
         PREBATTLE_TYPE.TRAINING: MENU.HEADERBUTTONS_BATTLE_MENU_TRAINING,
         PREBATTLE_TYPE.COMPANY: MENU.HEADERBUTTONS_BATTLE_MENU_TEAM,
         PREBATTLE_TYPE.CLAN: MENU.HEADERBUTTONS_BATTLE_MENU_BATTLE_SESSION,
         PREBATTLE_TYPE.TOURNAMENT: MENU.HEADERBUTTONS_BATTLE_MENU_BATTLE_SESSION,
         PREBATTLE_TYPE.UNIT: MENU.HEADERBUTTONS_BATTLE_MENU_UNIT}
        self.__actionsLockedInViews = set([VIEW_ALIAS.BATTLE_QUEUE, VIEW_ALIAS.LOBBY_TRAININGS, VIEW_ALIAS.LOBBY_TRAINING_ROOM])
        self.__currentLockedView = None
        self.__isActionsLocked = False
        return

    @process
    def _populate(self):
        self.__currentLockedView = None
        super(FightButton, self)._populate()
        g_currentVehicle.onChanged += self.update
        self.app.containerManager.onViewAddedToContainer += self.__onViewAddedToContainer
        self.addListener(events.FightButtonEvent.FIGHT_BUTTON_UPDATE, self.__handleFightButtonUpdate, scope=EVENT_BUS_SCOPE.LOBBY)
        g_clientUpdateManager.addCallbacks({'account.attrs': self.updateDemonstratorButton})
        accountAttrs = yield StatsRequester().getAccountAttrs()
        self.updateDemonstratorButton(accountAttrs)
        return

    def _dispose(self):
        self.__currentLockedView = None
        super(FightButton, self)._dispose()
        g_currentVehicle.onChanged -= self.update
        self.app.containerManager.onViewAddedToContainer -= self.__onViewAddedToContainer
        self.removeListener(events.FightButtonEvent.FIGHT_BUTTON_UPDATE, self.__handleFightButtonUpdate, scope=EVENT_BUS_SCOPE.LOBBY)
        g_clientUpdateManager.removeObjectCallbacks(self)
        return

    def update(self):
        prbDispatcher = g_prbLoader.getDispatcher()
        if not prbDispatcher:
            return
        else:
            prbFunctional = prbDispatcher.getPrbFunctional()
            hasModalEntity, prbType = prbDispatcher.getFunctionalState()
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
            if prbDispatcher.getUnitFunctional().hasEntity():
                menu = MENU.HEADERBUTTONS_BATTLE_MENU_UNIT
            else:
                menu = self.__menuLabels.get(prbType, MENU.HEADERBUTTONS_BATTLE_MENU_STANDART)
            fightTypes = list()
            if self.__currentLockedView == VIEW_ALIAS.BATTLE_QUEUE:
                fightTypes.append({'label': MENU.HEADERBUTTONS_BATTLE_TYPES_STANDART,
                 'data': PREBATTLE_ACTION_NAME.LEAVE_RANDOM_QUEUE,
                 'disabled': True,
                 'tooltip': TOOLTIPS.BATTLETYPES_STANDART,
                 'description': i18n.makeString(MENU.HEADERBUTTONS_BATTLE_TYPES_STANDARTLEAVE_DESCR),
                 'icon': PREBATTLE_ACTION_NAME.LEAVE_RANDOM_QUEUE,
                 'active': True})
            else:
                fightTypes.append({'label': MENU.HEADERBUTTONS_BATTLE_TYPES_STANDART,
                 'data': PREBATTLE_ACTION_NAME.JOIN_RANDOM_QUEUE,
                 'disabled': disabled or hasModalEntity,
                 'tooltip': TOOLTIPS.BATTLETYPES_STANDART,
                 'description': i18n.makeString(MENU.HEADERBUTTONS_BATTLE_TYPES_STANDART_DESCR),
                 'icon': PREBATTLE_ACTION_NAME.JOIN_RANDOM_QUEUE,
                 'active': False})
            if prbType is PREBATTLE_TYPE.SQUAD:
                fightTypes.append({'label': '#menu:headerButtons/battle/types/squadLeave%s' % ('Owner' if isCreator else ''),
                 'data': PREBATTLE_ACTION_NAME.PREBATTLE_LEAVE,
                 'disabled': self.__currentLockedView == VIEW_ALIAS.BATTLE_QUEUE,
                 'tooltip': TOOLTIPS.BATTLETYPES_SQUADLEAVE,
                 'description': i18n.makeString(MENU.HEADERBUTTONS_BATTLE_TYPES_SQUADLEAVE_DESCR),
                 'icon': PREBATTLE_ACTION_NAME.SQUAD,
                 'active': True})
            else:
                fightTypes.append({'label': MENU.HEADERBUTTONS_BATTLE_TYPES_SQUAD,
                 'data': PREBATTLE_ACTION_NAME.SQUAD,
                 'disabled': disabled or hasModalEntity,
                 'tooltip': TOOLTIPS.BATTLETYPES_SQUAD,
                 'description': i18n.makeString(MENU.HEADERBUTTONS_BATTLE_TYPES_SQUAD_DESCR),
                 'icon': PREBATTLE_ACTION_NAME.SQUAD,
                 'active': False})
            units = AccountSettings.getSettings('unitWindow')
            if prbType is PREBATTLE_TYPE.UNIT:
                fightTypes.append({'label': MENU.HEADERBUTTONS_BATTLE_TYPES_UNITLEAVE,
                 'data': PREBATTLE_ACTION_NAME.UNIT_LEAVE,
                 'disabled': False,
                 'tooltip': TOOLTIPS.BATTLETYPES_LEAVEUNIT,
                 'description': i18n.makeString(MENU.HEADERBUTTONS_BATTLE_TYPES_LEAVEUNIT_DESCR),
                 'icon': PREBATTLE_ACTION_NAME.UNIT,
                 'active': True,
                 'isUnitOpened': units['isOpened']})
            else:
                fightTypes.append({'label': MENU.HEADERBUTTONS_BATTLE_TYPES_UNIT,
                 'data': PREBATTLE_ACTION_NAME.UNIT,
                 'disabled': disabled or inPrebattle,
                 'tooltip': TOOLTIPS.BATTLETYPES_UNIT,
                 'description': i18n.makeString(MENU.HEADERBUTTONS_BATTLE_TYPES_UNIT_DESCR),
                 'icon': PREBATTLE_ACTION_NAME.UNIT,
                 'active': False,
                 'isUnitOpened': units['isOpened']})
            if prbType is PREBATTLE_TYPE.COMPANY:
                fightTypes.append({'label': '#menu:headerButtons/battle/types/companyLeave%s' % ('Owner' if isCreator else ''),
                 'data': PREBATTLE_ACTION_NAME.PREBATTLE_LEAVE,
                 'disabled': self.__currentLockedView == VIEW_ALIAS.BATTLE_QUEUE,
                 'tooltip': TOOLTIPS.BATTLETYPES_LEAVECOMPANY,
                 'description': i18n.makeString(MENU.HEADERBUTTONS_BATTLE_TYPES_LEAVECOMPANY_DESCR),
                 'icon': PREBATTLE_ACTION_NAME.COMPANY_LIST,
                 'active': True})
            else:
                fightTypes.append({'label': MENU.HEADERBUTTONS_BATTLE_TYPES_COMPANY,
                 'data': PREBATTLE_ACTION_NAME.COMPANY_LIST,
                 'disabled': disabled or hasModalEntity,
                 'tooltip': TOOLTIPS.BATTLETYPES_COMPANY,
                 'description': i18n.makeString(MENU.HEADERBUTTONS_BATTLE_TYPES_COMPANY_DESCR),
                 'icon': PREBATTLE_ACTION_NAME.COMPANY_LIST,
                 'active': False})
            if GUI_SETTINGS.specPrebatlesVisible:
                if prbType in [PREBATTLE_TYPE.CLAN, PREBATTLE_TYPE.TOURNAMENT]:
                    fightTypes.append({'label': MENU.HEADERBUTTONS_BATTLE_TYPES_SPECLEAVE,
                     'data': PREBATTLE_ACTION_NAME.PREBATTLE_LEAVE,
                     'disabled': False,
                     'tooltip': TOOLTIPS.BATTLETYPES_LEAVESPEC,
                     'description': i18n.makeString(MENU.HEADERBUTTONS_BATTLE_TYPES_LEAVESPEC_DESCR),
                     'icon': PREBATTLE_ACTION_NAME.SPEC_BATTLE_LIST,
                     'active': True})
                else:
                    fightTypes.append({'label': MENU.HEADERBUTTONS_BATTLE_TYPES_SPEC,
                     'data': PREBATTLE_ACTION_NAME.SPEC_BATTLE_LIST,
                     'disabled': disabled or hasModalEntity or areSpecBattlesHidden(),
                     'tooltip': TOOLTIPS.BATTLETYPES_SPEC,
                     'description': i18n.makeString(MENU.HEADERBUTTONS_BATTLE_TYPES_SPEC_DESCR),
                     'icon': PREBATTLE_ACTION_NAME.SPEC_BATTLE_LIST,
                     'active': False})
            if isTraining:
                fightTypes.append({'label': '#menu:headerButtons/battle/types/trainingLeave%s' % ('Owner' if isCreator else ''),
                 'data': PREBATTLE_ACTION_NAME.PREBATTLE_LEAVE,
                 'disabled': False,
                 'tooltip': TOOLTIPS.BATTLETYPES_LEAVETRAINING,
                 'description': i18n.makeString(MENU.HEADERBUTTONS_BATTLE_TYPES_LEAVETRAINING_DESCR),
                 'icon': PREBATTLE_ACTION_NAME.TRAINING_LIST,
                 'active': True})
            elif self.__currentLockedView == VIEW_ALIAS.LOBBY_TRAININGS:
                menu = MENU.HEADERBUTTONS_BATTLE_MENU_TRAINING
                fightTypes.append({'label': '#menu:headerButtons/battle/types/trainingLeave',
                 'data': PREBATTLE_ACTION_NAME.LEAVE_TRAINING_LIST,
                 'disabled': False,
                 'tooltip': TOOLTIPS.BATTLETYPES_LEAVETRAINING,
                 'description': i18n.makeString(MENU.HEADERBUTTONS_BATTLE_TYPES_LEAVETRAINING_DESCR),
                 'icon': PREBATTLE_ACTION_NAME.TRAINING_LIST,
                 'active': True})
            else:
                fightTypes.append({'label': MENU.HEADERBUTTONS_BATTLE_TYPES_TRAINING,
                 'data': PREBATTLE_ACTION_NAME.TRAINING_LIST,
                 'disabled': disabled or hasModalEntity,
                 'tooltip': TOOLTIPS.BATTLETYPES_TRAINING,
                 'description': i18n.makeString(MENU.HEADERBUTTONS_BATTLE_TYPES_TRAINING_DESCR),
                 'icon': PREBATTLE_ACTION_NAME.TRAINING_LIST,
                 'active': False})
            disableDropDown = self.__currentLockedView == VIEW_ALIAS.BATTLE_QUEUE
            self.__onFightButtonSet(label, menu, fightTypes, disableDropDown)
            self.fireEvent(events.LobbySimpleEvent(events.LobbySimpleEvent.UPDATE_TANK_PARAMS), scope=EVENT_BUS_SCOPE.LOBBY)
            return

    def __onViewAddedToContainer(self, _, pyEntity):
        settings = pyEntity.settings
        if settings.type is VIEW_TYPE.LOBBY_SUB:
            alias = settings.alias
            if alias == VIEW_ALIAS.BATTLE_LOADING:
                return
            if alias in self.__actionsLockedInViews:
                self.__isActionsLocked = True
                self.__currentLockedView = alias
            else:
                self.__isActionsLocked = False
                self.__currentLockedView = None
            self.update()
        return

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
        if actionName == PREBATTLE_ACTION_NAME.JOIN_RANDOM_QUEUE:
            LOG_DEBUG('Disabling random battle start on list item click')
            return
        else:
            dispatcher = g_prbLoader.getDispatcher()
            if dispatcher is not None:
                dispatcher.doAction(PrebattleAction(actionName))
            else:
                LOG_ERROR('Prebattle dispatcher is not defined')
            return

    def __onFightButtonSet(self, label, menu, fightTypes, disableDropDown):
        self.as_setFightButtonS(label, menu, fightTypes, disableDropDown)

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
# okay decompyling res/scripts/client/gui/scaleform/daapi/view/lobby/header/fightbutton.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:26:05 EST

# Embedded file name: scripts/client/gui/prb_control/events_dispatcher.py
from constants import PREBATTLE_TYPE
from debug_utils import LOG_ERROR
from gui.Scaleform.framework import VIEW_TYPE, g_entitiesFactories as guiFactory
from gui.Scaleform.framework.managers.containers import POP_UP_CRITERIA
from gui.Scaleform.locale.CHAT import CHAT
from gui.prb_control.settings import DEFAULT_PREBATTLE_COOLDOWN
from gui.shared import g_eventBus, events, EVENT_BUS_SCOPE
from gui.shared.events import ChannelManagementEvent
from messenger.ext import channel_num_gen
from messenger.m_constants import LAZY_CHANNEL

def updateUI():
    g_eventBus.handleEvent(events.FightButtonEvent(events.FightButtonEvent.FIGHT_BUTTON_UPDATE), scope=EVENT_BUS_SCOPE.LOBBY)


def loadHangar():
    g_eventBus.handleEvent(events.LoadEvent(events.LoadEvent.LOAD_HANGAR), scope=EVENT_BUS_SCOPE.LOBBY)


def loadBattleQueue():
    g_eventBus.handleEvent(events.LoadEvent(events.LoadEvent.LOAD_BATTLE_QUEUE), scope=EVENT_BUS_SCOPE.LOBBY)


def loadTrainingList():
    g_eventBus.handleEvent(events.LoadEvent(events.LoadEvent.LOAD_TRAININGS), scope=EVENT_BUS_SCOPE.LOBBY)


def loadTrainingRoom():
    g_eventBus.handleEvent(events.LoadEvent(events.LoadEvent.LOAD_TRAINING_ROOM), scope=EVENT_BUS_SCOPE.LOBBY)


def exitFromTrainingRoom():
    from gui.WindowsManager import g_windowsManager
    from gui.Scaleform.daapi.settings.views import VIEW_ALIAS
    if g_windowsManager.window is not None:
        view = g_windowsManager.window.containerManager.getContainer(VIEW_TYPE.LOBBY_SUB).getView()
        if view is not None and view.settings.alias == VIEW_ALIAS.LOBBY_TRAINING_ROOM:
            return loadTrainingList()
    return


def _showSquadWindow(isInvitesOpen = False):
    g_eventBus.handleEvent(events.ShowWindowEvent(events.ShowWindowEvent.SHOW_SQUAD_WINDOW, {'isInvitesOpen': isInvitesOpen}), scope=EVENT_BUS_SCOPE.LOBBY)


def _closeSquadWindow():
    g_eventBus.handleEvent(events.LoadEvent(events.HideWindowEvent.HIDE_SQUAD_WINDOW), scope=EVENT_BUS_SCOPE.LOBBY)


def addSquadToCarousel():
    clientID = channel_num_gen.getClientID4Prebattle(PREBATTLE_TYPE.SQUAD)
    if not clientID:
        LOG_ERROR('Client ID not found', 'addSquadToCarousel')
        return
    g_eventBus.handleEvent(ChannelManagementEvent(clientID, ChannelManagementEvent.REQUEST_TO_ADD, {'label': CHAT.CHANNELS_SQUAD,
     'canClose': False,
     'isNotified': False,
     'icon': '../maps/icons/messenger/squad_icon.png',
     'order': channel_num_gen.getOrder4Prebattle(),
     'criteria': {POP_UP_CRITERIA.VIEW_ALIAS: guiFactory.getAliasByEvent(events.ShowWindowEvent.SHOW_SQUAD_WINDOW)},
     'openHandler': _showSquadWindow}), scope=EVENT_BUS_SCOPE.LOBBY)


def removeSquadFromCarousel():
    clientID = channel_num_gen.getClientID4Prebattle(PREBATTLE_TYPE.SQUAD)
    if not clientID:
        LOG_ERROR('Client ID not found', '_removeSquadFromCarousel')
        return
    g_eventBus.handleEvent(ChannelManagementEvent(clientID, ChannelManagementEvent.REQUEST_TO_REMOVE), scope=EVENT_BUS_SCOPE.LOBBY)


def loadSquad(isInvitesOpen = False):
    addSquadToCarousel()
    _showSquadWindow(isInvitesOpen=isInvitesOpen)


def unloadSquad():
    _closeSquadWindow()
    removeSquadFromCarousel()
    requestToDestroyPrbChannel(PREBATTLE_TYPE.SQUAD)


def unloadNotificationInviteWindow():
    g_eventBus.handleEvent(events.LoadEvent(events.HideWindowEvent.HIDE_NOTIFICATION_INVITES_WINDOW), scope=EVENT_BUS_SCOPE.LOBBY)


def _showCompanyWindow(isInvitesOpen = False):
    g_eventBus.handleEvent(events.ShowWindowEvent(events.ShowWindowEvent.SHOW_COMPANY_WINDOW, {'isInvitesOpen': isInvitesOpen}), scope=EVENT_BUS_SCOPE.LOBBY)


def _closeCompanyWindow():
    g_eventBus.handleEvent(events.LoadEvent(events.HideWindowEvent.HIDE_COMPANY_WINDOW), scope=EVENT_BUS_SCOPE.LOBBY)


def addCompanyToCarousel():
    clientID = channel_num_gen.getClientID4Prebattle(PREBATTLE_TYPE.COMPANY)
    if not clientID:
        LOG_ERROR('Client ID not found', 'addCompanyToCarousel')
        return
    else:
        g_eventBus.handleEvent(ChannelManagementEvent(clientID, ChannelManagementEvent.REQUEST_TO_ADD, {'label': CHAT.CHANNELS_TEAM,
         'canClose': False,
         'isNotified': False,
         'icon': None,
         'order': channel_num_gen.getOrder4Prebattle(),
         'criteria': {POP_UP_CRITERIA.VIEW_ALIAS: guiFactory.getAliasByEvent(events.ShowWindowEvent.SHOW_COMPANY_WINDOW)},
         'openHandler': _showCompanyWindow}), scope=EVENT_BUS_SCOPE.LOBBY)
        return


def removeCompanyFromCarousel():
    clientID = channel_num_gen.getClientID4Prebattle(PREBATTLE_TYPE.COMPANY)
    if not clientID:
        LOG_ERROR('Client ID not found', '_removeCompanyFromCarousel')
        return
    g_eventBus.handleEvent(ChannelManagementEvent(clientID, ChannelManagementEvent.REQUEST_TO_REMOVE), scope=EVENT_BUS_SCOPE.LOBBY)


def loadCompany(isInvitesOpen = False):
    addCompanyToCarousel()
    _showCompanyWindow(isInvitesOpen=isInvitesOpen)


def unloadCompany():
    _closeCompanyWindow()
    removeCompanyFromCarousel()
    requestToDestroyPrbChannel(PREBATTLE_TYPE.COMPANY)


def _showBattleSessionWindow():
    g_eventBus.handleEvent(events.ShowWindowEvent(events.ShowWindowEvent.SHOW_BATTLE_SESSION_WINDOW), scope=EVENT_BUS_SCOPE.LOBBY)


def _closeBattleSessionWindow():
    g_eventBus.handleEvent(events.ShowWindowEvent(events.HideWindowEvent.HIDE_BATTLE_SESSION_WINDOW), scope=EVENT_BUS_SCOPE.LOBBY)


def addSpecBattleToCarousel(prbType):
    clientID = channel_num_gen.getClientID4Prebattle(prbType)
    if not clientID:
        LOG_ERROR('Client ID not found', 'addSpecBattleToCarousel')
        return
    else:
        if prbType is PREBATTLE_TYPE.CLAN:
            label = CHAT.CHANNELS_CLAN
        elif prbType is PREBATTLE_TYPE.TOURNAMENT:
            label = CHAT.CHANNELS_TOURNAMENT
        else:
            LOG_ERROR('Prebattle type is not valid', prbType)
            return
        g_eventBus.handleEvent(ChannelManagementEvent(clientID, ChannelManagementEvent.REQUEST_TO_ADD, {'label': label,
         'canClose': False,
         'isNotified': False,
         'icon': None,
         'order': channel_num_gen.getOrder4Prebattle(),
         'criteria': {POP_UP_CRITERIA.VIEW_ALIAS: guiFactory.getAliasByEvent(events.ShowWindowEvent.SHOW_BATTLE_SESSION_WINDOW)},
         'openHandler': _showBattleSessionWindow}), scope=EVENT_BUS_SCOPE.LOBBY)
        return


def removeSpecBattleFromCarousel(prbType):
    clientID = channel_num_gen.getClientID4Prebattle(prbType)
    if not clientID:
        LOG_ERROR('Client ID not found', '_removeSpecBattleFromCarousel')
        return
    g_eventBus.handleEvent(ChannelManagementEvent(clientID, ChannelManagementEvent.REQUEST_TO_REMOVE), scope=EVENT_BUS_SCOPE.LOBBY)


def loadBattleSessionWindow(prbType):
    addSpecBattleToCarousel(prbType)
    _showBattleSessionWindow()


def unloadBattleSessionWindow(prbType):
    _closeBattleSessionWindow()
    removeSpecBattleFromCarousel(prbType)
    requestToDestroyPrbChannel(prbType)


def loadBattleSessionList():
    g_eventBus.handleEvent(events.ShowWindowEvent(events.ShowWindowEvent.SHOW_BATTLE_SESSION_LIST), scope=EVENT_BUS_SCOPE.LOBBY)


def addSpecBattlesToCarousel():
    clientID = channel_num_gen.getClientID4LazyChannel(LAZY_CHANNEL.SPECIAL_BATTLES)
    if not clientID:
        LOG_ERROR('Client ID not found', 'addSpecBattlesToCarousel')
        return
    else:
        g_eventBus.handleEvent(ChannelManagementEvent(clientID, ChannelManagementEvent.REQUEST_TO_ADD, {'label': LAZY_CHANNEL.SPECIAL_BATTLES,
         'canClose': False,
         'isNotified': False,
         'icon': None,
         'order': channel_num_gen.getOrder4LazyChannel(LAZY_CHANNEL.SPECIAL_BATTLES),
         'criteria': {POP_UP_CRITERIA.VIEW_ALIAS: guiFactory.getAliasByEvent(events.ShowWindowEvent.SHOW_BATTLE_SESSION_LIST)},
         'openHandler': loadBattleSessionList}), scope=EVENT_BUS_SCOPE.LOBBY)
        return


def removeSpecBattlesFromCarousel():
    clientID = channel_num_gen.getClientID4LazyChannel(LAZY_CHANNEL.SPECIAL_BATTLES)
    if not clientID:
        LOG_ERROR('Client ID not found', 'removeSpecBattlesFromCarousel')
        return
    g_eventBus.handleEvent(ChannelManagementEvent(clientID, ChannelManagementEvent.REQUEST_TO_REMOVE), scope=EVENT_BUS_SCOPE.LOBBY)


def loadCompaniesWindow():
    g_eventBus.handleEvent(events.ShowWindowEvent(events.ShowWindowEvent.SHOW_COMPANIES_WINDOW), scope=EVENT_BUS_SCOPE.LOBBY)


def addCompaniesToCarousel():
    clientID = channel_num_gen.getClientID4LazyChannel(LAZY_CHANNEL.COMPANIES)
    if not clientID:
        LOG_ERROR('Client ID not found', 'addCompaniesToCarousel')
        return
    else:
        g_eventBus.handleEvent(ChannelManagementEvent(clientID, ChannelManagementEvent.REQUEST_TO_ADD, {'label': LAZY_CHANNEL.COMPANIES,
         'canClose': False,
         'isNotified': False,
         'icon': None,
         'order': channel_num_gen.getOrder4LazyChannel(LAZY_CHANNEL.COMPANIES),
         'criteria': {POP_UP_CRITERIA.VIEW_ALIAS: guiFactory.getAliasByEvent(events.ShowWindowEvent.SHOW_COMPANIES_WINDOW)},
         'openHandler': loadCompaniesWindow}), scope=EVENT_BUS_SCOPE.LOBBY)
        return


def requestToDestroyPrbChannel(prbType):
    g_eventBus.handleEvent(events.MessengerEvent(events.MessengerEvent.PRB_CHANNEL_CTRL_REQUEST_DESTROY, {'prbType': prbType}), scope=EVENT_BUS_SCOPE.LOBBY)


def fireCoolDownEvent(requestID, coolDown = DEFAULT_PREBATTLE_COOLDOWN):
    g_eventBus.handleEvent(events.CoolDownEvent(events.CoolDownEvent.PREBATTLE, requestID=requestID, coolDown=coolDown), scope=EVENT_BUS_SCOPE.LOBBY)


def fireAutoInviteReceived(invite):
    g_eventBus.handleEvent(events.AutoInviteEvent(invite, events.AutoInviteEvent.INVITE_RECEIVED), scope=EVENT_BUS_SCOPE.LOBBY)


def showParentControlNotification():
    from gui import game_control, DialogsInterface
    if game_control.g_instance.gameSession.isPlayTimeBlock:
        key = 'koreaPlayTimeNotification'
    else:
        key = 'koreaParentNotification'
    DialogsInterface.showI18nInfoDialog(key, lambda *args: None)
# Embedded file name: scripts/client/gui/shared/personality.py
import SoundGroups
import BigWorld
import MusicController
from account_helpers.SettingsCache import g_settingsCache
from account_helpers.SettingsCore import g_settingsCore
from gui.Scaleform.LogitechMonitor import LogitechMonitor
from helpers import isPlayerAccount
from adisp import process
from debug_utils import LOG_CURRENT_EXCEPTION, LOG_DEBUG
from PlayerEvents import g_playerEvents
from account_helpers import isPremiumAccount
from CurrentVehicle import g_currentVehicle
from gui import SystemMessages, g_guiResetters, game_control
from gui.Scaleform.locale.MENU import MENU
from gui.Scaleform.locale.SYSTEM_MESSAGES import SYSTEM_MESSAGES
from gui.prb_control.dispatcher import g_prbLoader
from gui.shared import g_eventBus, g_itemsCache, g_questsCache
from gui.ClientUpdateManager import g_clientUpdateManager
from gui.WindowsManager import g_windowsManager
from gui.Scaleform.Waiting import Waiting
from gui.shared.utils import ParametersCache
from gui.shared.utils.HangarSpace import g_hangarSpace
from gui.shared.utils.RareAchievementsCache import g_rareAchievesCache
__guiContext = {}

def _updateGuiCtx(data):
    __guiContext.update(data)


def _clearGuiCtx():
    __guiContext.clear()


def _getGuiCtx():
    return __guiContext


@process
def onAccountShowGUI(ctx):
    _updateGuiCtx(ctx)
    yield g_itemsCache.update()
    yield g_questsCache.update()
    yield g_settingsCache.update()
    g_settingsCore.serverSettings.applySettings()
    game_control.g_instance.onAccountShowGUI(_getGuiCtx())
    accDossier = g_itemsCache.items.getAccountDossier()
    g_rareAchievesCache.request(accDossier.getRecord('rareAchievements'))
    MusicController.g_musicController.setAccountAttrs(g_itemsCache.items.stats.attributes)
    MusicController.g_musicController.play(MusicController.MUSIC_EVENT_LOBBY)
    MusicController.g_musicController.play(MusicController.AMBIENT_EVENT_LOBBY)
    premium = isPremiumAccount(g_itemsCache.items.stats.attributes)
    if g_hangarSpace.inited:
        g_hangarSpace.refreshSpace(premium)
    else:
        g_hangarSpace.init(premium)
    g_currentVehicle.init()
    g_windowsManager.onAccountShowGUI(_getGuiCtx())
    yield g_windowsManager.window.tooltipManager.request()
    g_prbLoader.onAccountShowGUI(_getGuiCtx())
    SoundGroups.g_instance.enableLobbySounds(True)
    onCenterIsLongDisconnected(True)
    Waiting.hide('enter')
    _clearGuiCtx()


def onAccountBecomeNonPlayer():
    g_itemsCache.clear()
    g_currentVehicle.destroy()
    g_hangarSpace.destroy()


@process
def onAvatarBecomePlayer():
    yield g_settingsCache.update()
    g_settingsCore.serverSettings.applySettings()
    g_windowsManager.showBattleLoading()
    g_prbLoader.onAvatarBecomePlayer()
    game_control.g_instance.onAvatarBecomePlayer()


@process
def onClientUpdate(diff):
    if isPlayerAccount():
        yield g_itemsCache.update(diff)
        yield g_questsCache.update()
        MusicController.g_musicController.setAccountAttrs(g_itemsCache.items.stats.attributes, True)
        MusicController.g_musicController.play(MusicController.MUSIC_EVENT_LOBBY)
        MusicController.g_musicController.play(MusicController.MUSIC_EVENT_LOBBY)
    else:
        yield lambda callback: callback(None)
    g_clientUpdateManager.update(diff)


def onShopResyncStarted():
    Waiting.show('sinhronize')


@process
def onShopResync():
    yield g_itemsCache.update()
    Waiting.hide('sinhronize')
    import time
    now = time.time()
    SystemMessages.g_instance.pushI18nMessage(SYSTEM_MESSAGES.SHOP_RESYNC, date=BigWorld.wg_getLongDateFormat(now), time=BigWorld.wg_getShortTimeFormat(now), type=SystemMessages.SM_TYPE.Information)


def onCenterIsLongDisconnected(isLongDisconnected):
    isAvailable = not BigWorld.player().isLongDisconnectedFromCenter
    if isAvailable and not isLongDisconnected:
        SystemMessages.g_instance.pushI18nMessage(MENU.CENTERISAVAILABLE, type=SystemMessages.SM_TYPE.Information)
    elif not isAvailable:
        SystemMessages.g_instance.pushI18nMessage(MENU.CENTERISUNAVAILABLE, type=SystemMessages.SM_TYPE.Warning)


def onIGRTypeChanged(roomType, xpFactor):
    _updateGuiCtx({'igrData': {'roomType': roomType,
                 'igrXPFactor': xpFactor}})


def init(loadingScreenGUI = None):
    g_playerEvents.onAccountShowGUI += onAccountShowGUI
    g_playerEvents.onAccountBecomeNonPlayer += onAccountBecomeNonPlayer
    g_playerEvents.onAvatarBecomePlayer += onAvatarBecomePlayer
    g_playerEvents.onClientUpdated += onClientUpdate
    g_playerEvents.onShopResyncStarted += onShopResyncStarted
    g_playerEvents.onShopResync += onShopResync
    g_playerEvents.onCenterIsLongDisconnected += onCenterIsLongDisconnected
    g_playerEvents.onIGRTypeChanged += onIGRTypeChanged
    game_control.g_instance.init()
    from gui.Scaleform import SystemMessagesInterface
    SystemMessages.g_instance = SystemMessagesInterface.SystemMessagesInterface()
    SystemMessages.g_instance.init()
    ParametersCache.g_instance.init()
    if loadingScreenGUI:
        loadingScreenGUI.script.active(False)
    g_prbLoader.init()
    LogitechMonitor.init()
    g_itemsCache.init()
    g_settingsCache.init()
    g_settingsCore.init()
    g_questsCache.init()


def start():
    g_windowsManager.start()


def fini():
    Waiting.close()
    game_control.g_instance.fini()
    g_settingsCore.fini()
    g_settingsCache.fini()
    g_questsCache.fini()
    g_itemsCache.fini()
    LogitechMonitor.destroy()
    g_windowsManager.destroy()
    SystemMessages.g_instance.destroy()
    g_eventBus.clear()
    g_prbLoader.fini()
    g_playerEvents.onIGRTypeChanged -= onIGRTypeChanged
    g_playerEvents.onAccountShowGUI -= onAccountShowGUI
    g_playerEvents.onAccountBecomeNonPlayer -= onAccountBecomeNonPlayer
    g_playerEvents.onAvatarBecomePlayer -= onAvatarBecomePlayer
    g_playerEvents.onClientUpdated -= onClientUpdate
    g_playerEvents.onShopResyncStarted -= onShopResyncStarted
    g_playerEvents.onShopResync -= onShopResync
    g_playerEvents.onCenterIsLongDisconnected -= onCenterIsLongDisconnected


def onConnected():
    pass


def onDisconnected():
    g_prbLoader.onDisconnected()
    game_control.g_instance.onDisconnected()
    g_itemsCache.clear()


def onRecreateDevice():
    for c in g_guiResetters:
        try:
            c()
        except Exception:
            LOG_CURRENT_EXCEPTION()
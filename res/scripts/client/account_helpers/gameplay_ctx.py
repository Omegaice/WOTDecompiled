import ArenaType
import constants
from debug_utils import LOG_DEBUG, LOG_ERROR, LOG_WARNING

def getDefaultMask():
    return 7


def getMask():
    from account_helpers.SettingsCore import g_settingsCore
    mask = g_settingsCore.serverSettings.getGameSetting('gameplayMask', getDefaultMask())
    ctfMask = 1 << constants.ARENA_GAMEPLAY_IDS['ctf']
    if not mask:
        LOG_WARNING('Gameplay is not defined', mask)
    elif mask & ctfMask == 0:
        LOG_WARNING('Gameplay "ctf" is not defined', mask)
    mask |= ctfMask
    return mask


def setMaskByNames(names):
    gameplayNames = set(['ctf'])
    for name in names:
        if name in ArenaType.g_gameplayNames:
            gameplayNames.add(name)
        else:
            LOG_ERROR('Gameplay is not available', name)

    gameplayMask = ArenaType.getGameplaysMask(gameplayNames)
    LOG_DEBUG('Set gameplay (names, mask)', gameplayNames, gameplayMask)
    from account_helpers.SettingsCore import g_settingsCore
    g_settingsCore.serverSettings.setGameSettings({'gameplayMask': gameplayMask})

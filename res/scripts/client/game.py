# 2013.11.15 11:25:30 EST
# Embedded file name: scripts/client/game.py
import cPickle
import zlib
import sys
import asyncore
import AreaDestructibles
import BigWorld
import constants
import CommandMapping
import ResMgr
from post_processing import g_postProcessing
from ConnectionManager import connectionManager
from debug_utils import LOG_CURRENT_EXCEPTION, LOG_DEBUG, LOG_ERROR
import GUI
from gui import CLIENT_ENCODING, onRepeatKeyEvent
from gui.Scaleform.GameLoading import GameLoading
from gui.Scaleform import VoiceChatInterface
from gui.shared import personality as gui_personality
from messenger import MessengerEntry
import MusicController
import TriggersManager
from helpers import RSSDownloader
import Settings
from MemoryCriticalController import g_critMemHandler
import VOIP
from gui import InputHandler
import WebBrowser
try:
    from tutorial.loader import init as tutorialLoaderInit
    from tutorial.loader import fini as tutorialLoaderFini
except ImportError:
    LOG_ERROR('Module tutorial not found')
    tutorialLoaderInit = lambda : None
    tutorialLoaderFini = lambda : None

__import__('__main__').GameLoading = GameLoading
import locale
try:
    locale.setlocale(locale.LC_TIME, '')
except locale.Error:
    LOG_CURRENT_EXCEPTION()

from gui.Scaleform import fonts_config
fonts_config.g_fontConfigMap.load()
g_replayCtrl = None

def autoFlushPythonLog():
    BigWorld.flushPythonLog()
    BigWorld.callback(5.0, autoFlushPythonLog)


def init(scriptConfig, engineConfig, userPreferences, loadingScreenGUI = None):
    global g_replayCtrl
    try:
        if constants.IS_DEVELOPMENT:
            autoFlushPythonLog()
        LOG_DEBUG('init')
        BigWorld.wg_initCustomSettings()
        Settings.g_instance = Settings.Settings(scriptConfig, engineConfig, userPreferences)
        CommandMapping.g_instance = CommandMapping.CommandMapping()
        from helpers import DecalMap
        DecalMap.g_instance = DecalMap.DecalMap(scriptConfig['decal'])
        from helpers import EdgeDetectColorController
        EdgeDetectColorController.g_instance = EdgeDetectColorController.EdgeDetectColorController(scriptConfig['silhouetteColors'])
        import SoundGroups
        SoundGroups.g_instance = SoundGroups.SoundGroups()
        import BattleReplay
        g_replayCtrl = BattleReplay.g_replayCtrl = BattleReplay.BattleReplay()
        g_replayCtrl.registerWotReplayFileExtension()
        try:
            import Vibroeffects
            Vibroeffects.VibroManager.g_instance = Vibroeffects.VibroManager.VibroManager()
            Vibroeffects.VibroManager.g_instance.connect()
        except:
            LOG_CURRENT_EXCEPTION()

        tutorialLoaderInit()
        BigWorld.callback(0.1, asyncore_call)
        MessengerEntry.g_instance.init()
        import items
        items.init(True, None if not constants.IS_DEVELOPMENT else {})
        import ArenaType
        ArenaType.init()
        import dossiers1
        dossiers1.init()
        import dossiers2
        dossiers2.init()
        BigWorld.worldDrawEnabled(False)
        import LcdKeyboard
        LcdKeyboard.enableLcdKeyboardSpecificKeys(True)
        gui_personality.init(loadingScreenGUI=loadingScreenGUI)
        AreaDestructibles.init()
        MusicController.init()
        TriggersManager.init()
        RSSDownloader.init()
        g_postProcessing.init()
        try:
            from LightFx import LightManager
            LightManager.g_instance = LightManager.LightManager()
            import AuxiliaryFx
            AuxiliaryFx.g_instance = AuxiliaryFx.AuxiliaryFxManager()
        except:
            LOG_CURRENT_EXCEPTION()

    except Exception:
        LOG_CURRENT_EXCEPTION()
        BigWorld.quit()

    return


def start():
    LOG_DEBUG('start')
    connectionManager.onConnected += onConnected
    connectionManager.onDisconnected += onDisconnected
    if len(sys.argv) > 2:
        if sys.argv[1] == 'scriptedTest':
            try:
                scriptName = sys.argv[2]
                if scriptName[-3:] == '.py':
                    scriptName = scriptName[:-3]
                try:
                    __import__(scriptName)
                except ImportError:
                    __import__('cat.' + scriptName)

            except:
                LOG_CURRENT_EXCEPTION()
                BigWorld.wg_writeToStdOut('Failed to run scripted test, Python exception was thrown, see python.log')
                BigWorld.quit()

        elif sys.argv[1] == 'offlineTest':
            try:
                from cat.tasks.TestArena2 import TestArena2Object
                LOG_DEBUG(sys.argv)
                LOG_DEBUG('starting offline test: %s', sys.argv[2])
                if len(sys.argv) > 3:
                    TestArena2Object.startOffline(sys.argv[2], sys.argv[3])
                else:
                    TestArena2Object.startOffline(sys.argv[2])
            except:
                LOG_DEBUG('Game start FAILED with:')
                LOG_CURRENT_EXCEPTION()

        elif sys.argv[1] == 'validationTest':
            try:
                gui_personality.start()
                LOG_DEBUG('starting validationTest')
                import Cat
                Cat.Tasks.Validation.ParamsObject.setResultFileName(sys.argv[2])
                BigWorld.callback(10, Cat.Tasks.Validation.startAllValidationTests)
            except:
                LOG_DEBUG('Game start FAILED with:')
                LOG_CURRENT_EXCEPTION()

        elif sys.argv[1] == 'resourcesValidationTest':
            try:
                gui_personality.start()
                LOG_DEBUG('starting resourcesValidationTest')
                import Cat
                Cat.Tasks.Validation.ParamsObject.setResultFileName(sys.argv[2])
                BigWorld.callback(10, Cat.Tasks.Validation.startResourcesValidationTest)
            except:
                LOG_DEBUG('Game start FAILED with:')
                LOG_CURRENT_EXCEPTION()

    else:
        gui_personality.start()
    try:
        import Vibroeffects
        Vibroeffects.VibroManager.g_instance.start()
    except:
        LOG_CURRENT_EXCEPTION()

    try:
        import LightFx
        LightFx.LightManager.g_instance.start()
        import AuxiliaryFx
        AuxiliaryFx.g_instance.start()
    except:
        LOG_CURRENT_EXCEPTION()


def fini():
    global g_replayCtrl
    LOG_DEBUG('fini')
    BigWorld.wg_setScreenshotNotifyCallback(None)
    g_critMemHandler.restore()
    g_critMemHandler.destroy()
    if constants.IS_CAT_LOADED:
        import Cat
        Cat.fini()
    MusicController.g_musicController.destroy()
    TriggersManager.g_manager.destroy()
    RSSDownloader.g_downloader.destroy()
    connectionManager.onConnected -= onConnected
    connectionManager.onDisconnected -= onDisconnected
    MessengerEntry.g_instance.fini()
    g_postProcessing.fini()
    from helpers import EdgeDetectColorController
    if EdgeDetectColorController.g_instance is not None:
        EdgeDetectColorController.g_instance.destroy()
        EdgeDetectColorController.g_instance = None
    BigWorld.resetEntityManager(False, False)
    BigWorld.clearAllSpaces()
    gui_personality.fini()
    tutorialLoaderFini()
    import LcdKeyboard
    LcdKeyboard.finalize()
    import Vibroeffects
    if Vibroeffects.VibroManager.g_instance is not None:
        Vibroeffects.VibroManager.g_instance.destroy()
        Vibroeffects.VibroManager.g_instance = None
    if g_replayCtrl is not None:
        g_replayCtrl.stop()
        g_replayCtrl = None
        import BattleReplay
        BattleReplay.g_replayCtrl = None
    from LightFx import LightManager
    if LightManager.g_instance is not None:
        LightManager.g_instance.destroy()
        LightManager.g_instance = None
    import AuxiliaryFx
    if AuxiliaryFx.g_instance is not None:
        AuxiliaryFx.g_instance.destroy()
        AuxiliaryFx.g_instance = None
    from predefined_hosts import g_preDefinedHosts
    if g_preDefinedHosts is not None:
        g_preDefinedHosts.fini()
    voipRespHandler = VOIP.getVOIPManager()
    if voipRespHandler is not None:
        VOIP.getVOIPManager().destroy()
    Settings.g_instance.save()
    return


def onChangeEnvironments(inside):
    LOG_DEBUG('onChangeEnvironments')


def onRecreateDevice():
    LOG_DEBUG('onRecreateDevice')
    gui_personality.onRecreateDevice()


def onStreamComplete(id, desc, data):
    try:
        origPacketLen, origCrc32 = cPickle.loads(desc)
    except:
        origPacketLen, origCrc32 = (-1, -1)

    packetLen = len(data)
    crc32 = zlib.crc32(data)
    if not origPacketLen != packetLen:
        isCorrupted = origCrc32 != crc32
        desc = (isCorrupted,
         origPacketLen,
         packetLen,
         origCrc32,
         crc32)
        player = BigWorld.player()
        player is None and LOG_ERROR('onStreamComplete: no player entity available for process stream (%d, %s) data' % (id, desc))
    else:
        player.onStreamComplete(id, desc, data)
    return


def onConnected():
    gui_personality.onConnected()
    VOIP.getVOIPManager().onConnected()


def onGeometryMapped(spaceID, path):
    sys.stderr.write('[SPACE] Loading space: ' + path + '\n')


def onDisconnected():
    gui_personality.onDisconnected()
    VOIP.getVOIPManager().logout()
    VOIP.getVOIPManager().unsubscribeChatActions()
    VoiceChatInterface.g_instance.reset()


def handleCharEvent(char, key, mods):
    char = unicode(char.encode('iso8859'), CLIENT_ENCODING)
    if GUI.handleCharEvent(char, key, mods):
        return True
    return False


def handleAxisEvent(event):
    return False


def handleKeyEvent(event):
    isDown, key, mods, isRepeat = convertKeyEvent(event)
    if WebBrowser.g_mgr.handleKeyEvent(event):
        return True
    else:
        if isRepeat:
            if onRepeatKeyEvent(event):
                return True
        if g_replayCtrl.isPlaying:
            if g_replayCtrl.handleKeyEvent(isDown, key, mods, isRepeat, event):
                return True
        if constants.IS_CAT_LOADED:
            import Cat
            if Cat.handleKeyEventBeforeGUI(isDown, key, mods, event):
                return True
        if not isRepeat:
            InputHandler.g_instance.handleKeyEvent(event)
            if GUI.handleKeyEvent(event):
                return True
        if constants.IS_CAT_LOADED:
            import Cat
            if Cat.handleKeyEventAfterGUI(isDown, key, mods, event):
                return True
        if not isRepeat:
            if MessengerEntry.g_instance.gui.isEditing(event):
                return True
        inputHandler = getattr(BigWorld.player(), 'inputHandler', None)
        if inputHandler is not None:
            if inputHandler.handleKeyEvent(event):
                return True
        return False


def handleMouseEvent(event):
    dx, dy, dz, cursorPos = convertMouseEvent(event)
    if constants.IS_CAT_LOADED:
        import Cat
        if Cat.handleMouseEvent(dx, dy, dz):
            return True
    if g_replayCtrl.isPlaying:
        if g_replayCtrl.handleMouseEvent(dx, dy, dz):
            return True
    if GUI.handleMouseEvent(event):
        return True
    else:
        inputHandler = getattr(BigWorld.player(), 'inputHandler', None)
        if inputHandler is None:
            return False
        return inputHandler.handleMouseEvent(dx, dy, dz)


def handleInputLangChangeEvent():
    return False


def addChatMsg(*msg):
    print 'Message:', msg


_PYTHON_MACROS = {'p': 'BigWorld.player()',
 't': 'BigWorld.target()',
 'B': 'BigWorld',
 'v': 'BigWorld.entities[BigWorld.player().playerVehicleID]',
 'b': 'BigWorld.player().addBotToArena',
 'w': 'import Weather; Weather.weather().summon',
 'cam_pos': 'BigWorld.player().inputHandler._AvatarInputHandler__curCtrl.setCameraPosition',
 'gc': 'import gc; gc.set_debug(gc.DEBUG_LEAK | gc.DEBUG_STATS);gc.collect(2)',
 'gcd': 'import gc; gc.set_debug(gc.DEBUG_LEAK | gc.DEBUG_STATS);from debug_utils import dump_garbage; dump_garbage()',
 'gcd2': 'import gc; gc.set_debug(gc.DEBUG_LEAK | gc.DEBUG_STATS);from debug_utils import dump_garbage_2; dump_garbage_2()',
 'connect': 'ls=game.LanServers();ls.searchAndConnect',
 'create': 'BigWorld.player().createArena',
 'list': 'alr = game.ArenaListRequester',
 'start': 'BigWorld.player().startArena',
 'join': 'BigWorld.player().joinArena',
 'leave': 'BigWorld.player().leaveArena',
 'cv': 'import vehicles_check;vehicles_check.check',
 'chat': 'from messenger.MessengerEntry import g_instance;g_instance',
 'battleUI': 'from gui.WindowsManager import g_windowsManager; g_windowsManager.battleWindow',
 'tutorial': 'from tutorial import mock as tutorial_mock; tutorial_mock',
 'sf_player': 'from gui.Scaleform.development import sf_player_test; sf_player_test',
 'wm': 'from gui.WindowsManager import g_windowsManager; wm = g_windowsManager; wm',
 'cm': 'from gui.WindowsManager import g_windowsManager; cm = g_windowsManager.window.containerManager; cm',
 'cls': "print '\\n' * 100",
 'items': 'from gui.shared import g_itemsCache, REQ_CRITERIA; items = g_itemsCache.items',
 'unlockAll': 'BigWorld.player().stats.unlockAll(lambda *args:None)',
 'battleResults': 'from gui import showBattleResults; showBattleResults()',
 'events': 'from gui.WindowsManager import g_windowsManager; wm = g_windowsManager; wm.window.movie.root.utils.events.logState()',
 'killGUI': 'from gui.WindowsManager import g_windowsManager; wm = g_windowsManager; wm.window.close()',
 'prbCtrl': 'from gui.prb_control.dispatcher import g_prbLoader; g_prbLoader',
 'prbFunc': 'from gui.prb_control.dispatcher import g_prbLoader; g_prbLoader.getDispatcher().getPrbFunctional()',
 'unitFunc': 'from gui.prb_control.dispatcher import g_prbLoader; g_prbLoader.getDispatcher().getUnitFunctional()',
 'app': 'from gui.WindowsManager import g_windowsManager; wm = g_windowsManager; wm.window',
 'hangar': 'from gui.ClientHangarSpace import g_clientHangarSpaceOverride; g_clientHangarSpaceOverride',
 'cvi': 'from CurrentVehicle import g_currentVehicle; cvi = g_currentVehicle.item'}

def expandMacros(line):
    import re
    patt = '\\$(' + reduce(lambda x, y: x + '|' + y, _PYTHON_MACROS.iterkeys()) + ')(\\W|\\Z)'

    def repl(match):
        return _PYTHON_MACROS[match.group(1)] + match.group(2)

    return re.sub(patt, repl, line)


def wg_onChunkLoad(spaceID, chunkID, numDestructibles, isOutside):
    if not isOutside:
        return
    if spaceID != AreaDestructibles.g_destructiblesManager.getSpaceID():
        AreaDestructibles.g_destructiblesManager.startSpace(spaceID)
    AreaDestructibles.g_destructiblesManager.onChunkLoad(chunkID, numDestructibles)


def wg_onChunkLoose(spaceID, chunkID, isOutside):
    if not isOutside:
        return
    if spaceID == AreaDestructibles.g_destructiblesManager.getSpaceID():
        AreaDestructibles.g_destructiblesManager.onChunkLoose(chunkID)


def convertKeyEvent(event):
    isDown = event.isKeyDown()
    key = event.key
    isRepeat = event.isRepeatedEvent()
    mods = 1 if event.isShiftDown() else (2 if event.isCtrlDown() else (4 if event.isAltDown() else 0))
    return (isDown,
     key,
     mods,
     isRepeat)


def convertMouseEvent(event):
    return (event.dx,
     event.dy,
     event.dz,
     event.cursorPosition)


def onMemoryCritical():
    g_critMemHandler()


def asyncore_call():
    try:
        asyncore.loop(count=1)
    except:
        LOG_CURRENT_EXCEPTION()

    BigWorld.callback(0.1, asyncore_call)
# okay decompyling res/scripts/client/game.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:25:31 EST

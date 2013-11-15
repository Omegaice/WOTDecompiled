# 2013.11.15 11:26:44 EST
# Embedded file name: scripts/client/gui/Scaleform/SettingsInterface.py
import sys
from functools import partial
import BigWorld
import weakref
import itertools
import SoundGroups
import ResMgr
import ArenaType
from gui.Scaleform.managers.windows_stored_data import g_windowsStoredData
import nations
from account_helpers import gameplay_ctx
from account_helpers.SettingsCore import g_settingsCore
from gui import GUI_SETTINGS, g_guiResetters
from gui.BattleContext import g_battleContext
from gui.GraphicsPresets import GraphicsPresets
from gui.GraphicsResolutions import g_graficsResolutions
from gui.shared.utils.key_mapping import getScaleformKey
from gui.Scaleform import VoiceChatInterface
from windows import UIInterface
from debug_utils import LOG_DEBUG, LOG_NOTE, LOG_ERROR
from account_helpers.AccountSettings import AccountSettings
from post_processing import g_postProcessing
import CommandMapping
import Settings
from adisp import process
from gui.Scaleform.Waiting import Waiting
from Vibroeffects import VibroManager
from LogitechMonitor import LogitechMonitor
from helpers import getClientOverride

class SettingsInterface(UIInterface):
    KEYBOARD_MAPPING_COMMANDS = {'movement': {'forward': 'CMD_MOVE_FORWARD',
                  'backward': 'CMD_MOVE_BACKWARD',
                  'left': 'CMD_ROTATE_LEFT',
                  'right': 'CMD_ROTATE_RIGHT',
                  'auto_rotation': 'CMD_CM_VEHICLE_SWITCH_AUTOROTATION'},
     'cruis_control': {'forward': 'CMD_INCREMENT_CRUISE_MODE',
                       'backward': 'CMD_DECREMENT_CRUISE_MODE',
                       'stop_fire': 'CMD_STOP_UNTIL_FIRE'},
     'firing': {'fire': 'CMD_CM_SHOOT',
                'lock_target': 'CMD_CM_LOCK_TARGET',
                'lock_target_off': 'CMD_CM_LOCK_TARGET_OFF',
                'alternate_mode': 'CMD_CM_ALTERNATE_MODE',
                'reloadPartialClip': 'CMD_RELOAD_PARTIAL_CLIP'},
     'vehicle_other': {'showHUD': 'CMD_TOGGLE_GUI',
                       'showRadialMenu': 'CMD_RADIAL_MENU_SHOW'},
     'equipment': {'item01': 'CMD_AMMO_CHOICE_1',
                   'item02': 'CMD_AMMO_CHOICE_2',
                   'item03': 'CMD_AMMO_CHOICE_3',
                   'item04': 'CMD_AMMO_CHOICE_4',
                   'item05': 'CMD_AMMO_CHOICE_5',
                   'item06': 'CMD_AMMO_CHOICE_6',
                   'item07': 'CMD_AMMO_CHOICE_7',
                   'item08': 'CMD_AMMO_CHOICE_8'},
     'shortcuts': {'attack': 'CMD_CHAT_SHORTCUT_ATTACK',
                   'to_base': 'CMD_CHAT_SHORTCUT_BACKTOBASE',
                   'positive': 'CMD_CHAT_SHORTCUT_POSITIVE',
                   'negative': 'CMD_CHAT_SHORTCUT_NEGATIVE',
                   'help_me': 'CMD_CHAT_SHORTCUT_HELPME',
                   'reload': 'CMD_CHAT_SHORTCUT_RELOAD'},
     'camera': {'camera_up': 'CMD_CM_CAMERA_ROTATE_UP',
                'camera_down': 'CMD_CM_CAMERA_ROTATE_DOWN',
                'camera_left': 'CMD_CM_CAMERA_ROTATE_LEFT',
                'camera_right': 'CMD_CM_CAMERA_ROTATE_RIGHT'},
     'voicechat': {'pushToTalk': 'CMD_VOICECHAT_MUTE'},
     'logitech_keyboard': {'switch_view': 'CMD_LOGITECH_SWITCH_VIEW'},
     'minimap': {'sizeUp': 'CMD_MINIMAP_SIZE_UP',
                 'sizeDown': 'CMD_MINIMAP_SIZE_DOWN',
                 'visible': 'CMD_MINIMAP_VISIBLE'}}
    KEYBOARD_MAPPING_BLOCKS = {'movement': ('forward', 'backward', 'left', 'right', 'auto_rotation'),
     'cruis_control': ('forward', 'backward', 'stop_fire'),
     'firing': ('fire', 'lock_target', 'lock_target_off', 'alternate_mode', 'reloadPartialClip'),
     'vehicle_other': ('showHUD', 'showRadialMenu'),
     'equipment': ('item01', 'item02', 'item03', 'item04', 'item05', 'item06', 'item07', 'item08'),
     'shortcuts': ('attack', 'to_base', 'positive', 'negative', 'help_me', 'reload'),
     'camera': ('camera_up', 'camera_down', 'camera_left', 'camera_right'),
     'voicechat': ('pushToTalk',),
     'logitech_keyboard': ('switch_view',),
     'minimap': ('sizeUp', 'sizeDown', 'visible')}
    KEYBOARD_MAPPING_BLOCKS_ORDER = ('movement', 'cruis_control', 'firing', 'vehicle_other', 'equipment', 'shortcuts', 'camera', 'voicechat', 'minimap', 'logitech_keyboard')
    POPULATE_UI = 'SettingsDialog.PopulateUI'
    APPLY_SETTINGS = 'SettingsDialog.ApplySettings'
    COMMIT_SETTINGS = 'SettingsDialog.CommitSettings'
    DELAY_SETTINGS = 'SettingsDialog.DelaySettings'
    AUTODETECT_QUALITY = 'SettingsDialog.AutodetectQuality'
    CURSOR_VALUES = {'mixing': 3,
     'gunTag': 6,
     'centralTag': 8,
     'net': 3,
     'reloader': 0,
     'condition': 0,
     'cassette': 0,
     'reloaderTimer': 0}
    SNIPER_VALUES = {'snpMixing': 3,
     'snpGunTag': 6,
     'snpCentralTag': 8,
     'snpNet': 3,
     'snpReloader': 0,
     'snpCondition': 0,
     'snpCassette': 0,
     'snpReloaderTimer': 0}
    MARKER_VALUES = {'Hp': 4,
     'Name': 3}
    MARKER_TYPES = ['Base', 'Alt']
    MOUSE_KEYS = {'ingame': {'arcadeSens': ('arcade', 'sensitivity'),
                'sniperSens': ('sniper', 'sensitivity'),
                'artSens': ('strategic', 'sensitivity'),
                'horInvert': ('arcade', 'horzInvert'),
                'vertInvert': ('arcade', 'vertInvert'),
                'backDraftInvert': ('arcade', 'backDraftInvert')},
     'lobby': {'arcadeSens': ('arcadeMode/camera', 'sensitivity', 'float'),
               'sniperSens': ('sniperMode/camera', 'sensitivity', 'float'),
               'artSens': ('strategicMode/camera', 'sensitivity', 'float'),
               'horInvert': ('arcadeMode/camera', 'horzInvert', 'bool'),
               'vertInvert': ('arcadeMode/camera', 'vertInvert', 'bool'),
               'backDraftInvert': ('arcadeMode/camera', 'backDraftInvert', 'bool')},
     'default': {'arcadeSens': 1,
                 'sniperSens': 1,
                 'artSens': 1,
                 'horInvert': False,
                 'vertInvert': False,
                 'backDraftInvert': False}}
    GAMEPLAY_KEY_FORMAT = 'gameplay_{0:>s}'
    GAMEPLAY_PREFIX = 'gameplay_'

    def __init__(self, enableRedefineKeysMode = True):
        UIInterface.__init__(self)
        if not GUI_SETTINGS.minimapSize and self.KEYBOARD_MAPPING_BLOCKS.has_key('minimap'):
            del self.KEYBOARD_MAPPING_BLOCKS['minimap']
        self.__enableRedefineKeysMode = enableRedefineKeysMode
        self.graphicsPresets = GraphicsPresets()
        self.resolutions = g_graficsResolutions
        self.__currentSettings = None
        self.__settingsUI = None
        self.__altVoiceSetting = g_settingsCore.options.getSetting('alternativeVoices')
        if not GUI_SETTINGS.voiceChat and self.KEYBOARD_MAPPING_COMMANDS.has_key('voicechat'):
            if self.KEYBOARD_MAPPING_COMMANDS.has_key('voicechat'):
                del self.KEYBOARD_MAPPING_COMMANDS['voicechat']
            if self.KEYBOARD_MAPPING_BLOCKS.has_key('voicechat'):
                del self.KEYBOARD_MAPPING_BLOCKS['voicechat']
            self.KEYBOARD_MAPPING_BLOCKS_ORDER = list(self.KEYBOARD_MAPPING_BLOCKS_ORDER)
            del self.KEYBOARD_MAPPING_BLOCKS_ORDER[self.KEYBOARD_MAPPING_BLOCKS_ORDER.index('voicechat')]
            self.KEYBOARD_MAPPING_BLOCKS_ORDER = tuple(self.KEYBOARD_MAPPING_BLOCKS_ORDER)
        return

    def populateUI(self, proxy):
        UIInterface.populateUI(self, proxy)
        self.uiHolder.addExternalCallbacks({SettingsInterface.POPULATE_UI: self.onPopulateUI,
         SettingsInterface.APPLY_SETTINGS: self.onApplySettings,
         SettingsInterface.COMMIT_SETTINGS: self.onCommitSettings,
         SettingsInterface.DELAY_SETTINGS: self.onDelaySettings,
         SettingsInterface.AUTODETECT_QUALITY: self.onAutodetectSettings,
         'SettingsDialog.useRedifineKeysMode': self.onUseRedifineKeyMode,
         'SettingsDialog.processVivoxTest': self.onProcessVivoxTest,
         'SettingsDialog.voiceChatEnable': self.onVoiceChatEnable,
         'SettingsDialog.updateCaptureDevices': self.onUpdateCaptureDevices,
         'SettingsDialog.setVivoxMicVolume': self.onSetVivoxMicVolume,
         'SettingsDialog.killDialog': self.onDialogClose})
        VibroManager.g_instance.onConnect += self.__vm_onConnect
        VibroManager.g_instance.onDisconnect += self.__vm_onDisconnect
        g_guiResetters.add(self.onRecreateDevice)
        BigWorld.wg_setAdapterOrdinalNotifyCallback(self.onRecreateDevice)

    def dispossessUI(self):
        if self.__settingsUI:
            self.__settingsUI.script = None
            self.__settingsUI = None
        self.__altVoiceSetting = None
        self.uiHolder.removeExternalCallbacks(SettingsInterface.POPULATE_UI, SettingsInterface.APPLY_SETTINGS, SettingsInterface.COMMIT_SETTINGS, SettingsInterface.DELAY_SETTINGS, SettingsInterface.AUTODETECT_QUALITY, 'SettingsDialog.useRedifineKeysMode', 'SettingsDialog.processVivoxTest', 'SettingsDialog.voiceChatEnable', 'SettingsDialog.updateCaptureDevices', 'SettingsDialog.setVivoxMicVolume', 'SettingsDialog.killDialog')
        VibroManager.g_instance.onConnect -= self.__vm_onConnect
        VibroManager.g_instance.onDisconnect -= self.__vm_onDisconnect
        g_guiResetters.discard(self.onRecreateDevice)
        BigWorld.wg_setAdapterOrdinalNotifyCallback(None)
        UIInterface.dispossessUI(self)
        return

    def altVoicesPreview(self, soundMode):
        if not self.__altVoiceSetting.isOptionEnabled():
            return True
        if not g_battleContext.isInBattle:
            SoundGroups.g_instance.enableVoiceSounds(True)
        self.__altVoiceSetting.preview(soundMode)
        return self.__altVoiceSetting.playPreviewSound(self.uiHolder.soundManager)

    def isSoundModeValid(self, soundMode):
        self.__altVoiceSetting.preview(soundMode)
        valid = self.__altVoiceSetting.isSoundModeValid()
        self.__altVoiceSetting.revert()
        return valid

    def onSetVivoxMicVolume(self, callbackId, value):
        import VOIP
        if round(SoundGroups.g_instance.getVolume('micVivox') * 100) != value:
            SoundGroups.g_instance.setVolume('micVivox', value / 100)
            VOIP.getVOIPManager().setMicrophoneVolume(int(value))

    def onVoiceChatEnable(self, callbackId, isEnable):
        self.__voiceChatEnable(isEnable)

    def __voiceChatEnable(self, isEnable):
        if isEnable is None:
            return
        else:
            preveVoIP = Settings.g_instance.userPrefs.readBool(Settings.KEY_ENABLE_VOIP)
            import VOIP
            if preveVoIP != isEnable:
                VOIP.getVOIPManager().enable(isEnable)
                Settings.g_instance.userPrefs.writeBool(Settings.KEY_ENABLE_VOIP, bool(isEnable))
                from gui.WindowsManager import g_windowsManager
                if g_windowsManager.battleWindow is not None and not isEnable:
                    g_windowsManager.battleWindow.speakingPlayersReset()
                LOG_NOTE('Change state of voip: %s' % str(isEnable))
            return

    def __changeCaptureDevice(self, captureDeviceIdx):
        if captureDeviceIdx is None or captureDeviceIdx == -1:
            return
        else:
            import VOIP
            rh = VOIP.getVOIPManager()
            devices = [ device.decode(sys.getfilesystemencoding()).encode('utf-8') for device in rh.captureDevices ]
            if captureDeviceIdx < len(devices):
                newCaptureDevice = devices[captureDeviceIdx]
                previousDevice = Settings.g_instance.userPrefs.readString(Settings.KEY_VOIP_DEVICE)
                if previousDevice != newCaptureDevice:
                    Settings.g_instance.userPrefs.writeString(Settings.KEY_VOIP_DEVICE, newCaptureDevice)
                    LOG_NOTE('Change device of voip: %s' % str(newCaptureDevice))
            return

    def onUseRedifineKeyMode(self, callbackId, isUse):
        if self.__enableRedefineKeysMode:
            BigWorld.wg_setRedefineKeysMode(isUse)

    def onProcessVivoxTest(self, callbackId, isStart):
        LOG_DEBUG('Vivox test: %s' % str(isStart))
        import VOIP
        rh = VOIP.getVOIPManager()
        rh.enterTestChannel() if isStart else rh.leaveTestChannel()
        self.respond([callbackId, False])

    def __vm_onConnect(self):
        self.call('SettingsDialog.VibroManager.Connect')

    def __vm_onDisconnect(self):
        self.call('SettingsDialog.VibroManager.Disconnect')

    def __getVideoSettings(self):
        settings = {}
        settings['monitor'] = {'current': self.resolutions.monitorIndex,
         'real': self.resolutions.realMonitorIndex,
         'options': self.resolutions.monitorsList}
        settings['fullScreen'] = not self.resolutions.isVideoWindowed
        settings['windowSize'] = {'current': self.resolutions.windowSizeIndex,
         'options': self.resolutions.windowSizesList}
        settings['resolution'] = {'current': self.resolutions.videoModeIndex,
         'options': self.resolutions.videoModesList}
        return settings

    def __getSettings(self):
        settings = [self.graphicsPresets.getGraphicsPresetsData()]
        import VOIP
        rh = VOIP.getVOIPManager()
        g_windowsStoredData.start()
        vManager = VibroManager.g_instance
        vEffGroups = vManager.getGroupsSettings()
        vEffDefGroup = VibroManager.VibroManager.GroupSettings()
        vEffDefGroup.enabled = False
        vEffDefGroup.gain = 0
        markers = {'enemy': g_settingsCore.getSetting('enemy'),
         'dead': g_settingsCore.getSetting('dead'),
         'ally': g_settingsCore.getSetting('ally')}
        config = {'locale': getClientOverride(),
         'aspectRatio': {'current': self.resolutions.aspectRatioIndex,
                         'options': self.resolutions.aspectRatiosList},
         'vertSync': self.resolutions.isVideoVSync,
         'tripleBuffered': self.resolutions.isTripleBuffered,
         'multisampling': {'current': self.resolutions.multisamplingTypeIndex,
                           'options': self.resolutions.multisamplingTypesList},
         'customAA': {'current': self.resolutions.customAAModeIndex,
                      'options': self.resolutions.customAAModesList},
         'gamma': self.resolutions.gamma,
         'masterVolume': round(SoundGroups.g_instance.getMasterVolume() * 100),
         'musicVolume': round(SoundGroups.g_instance.getVolume('music') * 100),
         'voiceVolume': round(SoundGroups.g_instance.getVolume('voice') * 100),
         'vehiclesVolume': round(SoundGroups.g_instance.getVolume('vehicles') * 100),
         'effectsVolume': round(SoundGroups.g_instance.getVolume('effects') * 100),
         'guiVolume': round(SoundGroups.g_instance.getVolume('gui') * 100),
         'ambientVolume': round(SoundGroups.g_instance.getVolume('ambient') * 100),
         'masterVivoxVolume': round(SoundGroups.g_instance.getVolume('masterVivox') * 100),
         'micVivoxVolume': round(SoundGroups.g_instance.getVolume('micVivox') * 100),
         'masterFadeVivoxVolume': round(SoundGroups.g_instance.getVolume('masterFadeVivox') * 100),
         'captureDevice': self.__getCaptureDeviceSettings(),
         'voiceChatNotSupported': rh.vivoxDomain == '' or not VoiceChatInterface.g_instance.ready,
         'datetimeIdx': g_settingsCore.serverSettings.getGameSetting('datetimeIdx', 2),
         'enableOlFilter': g_settingsCore.getSetting('enableOlFilter'),
         'enableSpamFilter': g_settingsCore.getSetting('enableSpamFilter'),
         'enableStoreChatMws': g_settingsCore.getSetting('enableStoreMws'),
         'enableStoreChatCws': g_settingsCore.getSetting('enableStoreCws'),
         'invitesFromFriendsOnly': g_settingsCore.getSetting('invitesFromFriendsOnly'),
         'storeReceiverInBattle': g_settingsCore.getSetting('storeReceiverInBattle'),
         'dynamicCamera': g_settingsCore.getSetting('dynamicCamera'),
         'horStabilizationSnp': g_settingsCore.getSetting('horStabilizationSnp'),
         'enableVoIP': VOIP.getVOIPManager().channelsMgr.enabled,
         'enablePostMortemEffect': g_settingsCore.getSetting('enablePostMortemEffect'),
         'nationalVoices': AccountSettings.getSettings('nationalVoices'),
         'isColorBlind': AccountSettings.getSettings('isColorBlind'),
         'useServerAim': g_settingsCore.getSetting('useServerAim'),
         'showVehiclesCounter': g_settingsCore.getSetting('showVehiclesCounter'),
         'minimapAlpha': g_settingsCore.getSetting('minimapAlpha'),
         'vibroIsConnected': vManager.connect(),
         'vibroGain': vManager.getGain() * 100,
         'vibroEngine': vEffGroups.get('engine', vEffDefGroup).gain * 100,
         'vibroAcceleration': vEffGroups.get('acceleration', vEffDefGroup).gain * 100,
         'vibroShots': vEffGroups.get('shots', vEffDefGroup).gain * 100,
         'vibroHits': vEffGroups.get('hits', vEffDefGroup).gain * 100,
         'vibroCollisions': vEffGroups.get('collisions', vEffDefGroup).gain * 100,
         'vibroDamage': vEffGroups.get('damage', vEffDefGroup).gain * 100,
         'vibroGUI': vEffGroups.get('gui', vEffDefGroup).gain * 100,
         'ppShowLevels': g_settingsCore.getSetting('ppShowLevels'),
         'ppShowTypes': AccountSettings.getSettings('players_panel')['showTypes'],
         'replayEnabled': g_settingsCore.getSetting('replayEnabled'),
         'fpsPerfomancer': g_settingsCore.getSetting('fpsPerfomancer'),
         'arcade': {'values': g_settingsCore.options.getSetting('arcade').toAccountSettings(),
                    'options': SettingsInterface.CURSOR_VALUES},
         'sniper': {'values': g_settingsCore.options.getSetting('sniper').toAccountSettings(),
                    'options': SettingsInterface.SNIPER_VALUES},
         'markers': {'values': markers,
                     'options': SettingsInterface.MARKER_VALUES,
                     'types': SettingsInterface.MARKER_TYPES}}
        if self.__altVoiceSetting.isOptionEnabled():
            altVoices = []
            for idx, desc in enumerate(self.__altVoiceSetting.getOptions()):
                altVoices.append({'data': idx,
                 'label': desc})

            config['alternativeVoices'] = {'current': self.__altVoiceSetting.get(),
             'options': altVoices}
        gameplayMask = gameplay_ctx.getMask()
        for name in ArenaType.g_gameplayNames:
            key = self.GAMEPLAY_KEY_FORMAT.format(name)
            bit = ArenaType.getVisibilityMask(ArenaType.getGameplayIDForName(name))
            config[key] = gameplayMask & bit > 0

        settings.append(config)
        if not LogitechMonitor.isPresentColor():
            if self.KEYBOARD_MAPPING_BLOCKS.has_key('logitech_keyboard'):
                del self.KEYBOARD_MAPPING_BLOCKS['logitech_keyboard']
        else:
            self.KEYBOARD_MAPPING_BLOCKS['logitech_keyboard'] = ('switch_view',)
        cmdMap = CommandMapping.g_instance
        defaults = cmdMap.getDefaults()
        keyboard = []
        for group_name in self.KEYBOARD_MAPPING_BLOCKS_ORDER:
            if group_name in self.KEYBOARD_MAPPING_BLOCKS.keys():
                group = {'id': group_name,
                 'commands': []}
                keyboard.append(group)
                for key_setting in self.KEYBOARD_MAPPING_BLOCKS[group_name]:
                    command = cmdMap.getCommand(self.KEYBOARD_MAPPING_COMMANDS[group_name][key_setting])
                    keyCode = cmdMap.get(self.KEYBOARD_MAPPING_COMMANDS[group_name][key_setting])
                    defaultCode = defaults[command] if defaults.has_key(command) else 0
                    key = {'id': key_setting,
                     'command': command,
                     'key': getScaleformKey(keyCode),
                     'keyDefault': getScaleformKey(defaultCode)}
                    group['commands'].append(key)

        settings.append(keyboard)
        mouse = {}
        player = BigWorld.player()
        if hasattr(player.inputHandler, 'ctrls'):
            for key, path in SettingsInterface.MOUSE_KEYS['ingame'].items():
                if key == 'horInvert':
                    value = g_settingsCore.getSetting('mouseHorzInvert')
                elif key == 'vertInvert':
                    value = g_settingsCore.getSetting('mouseVertInvert')
                elif key == 'backDraftInvert':
                    value = g_settingsCore.getSetting('backDraftInvert')
                else:
                    value = player.inputHandler.ctrls[path[0]].camera.getUserConfigValue(path[1])
                mouse[key] = {'defaultValue': SettingsInterface.MOUSE_KEYS['default'][key],
                 'value': value}

        else:
            ds = Settings.g_instance.userPrefs[Settings.KEY_CONTROL_MODE]
            for key, path in SettingsInterface.MOUSE_KEYS['lobby'].items():
                default = SettingsInterface.MOUSE_KEYS['default'][key]
                value = default
                if key == 'horInvert':
                    value = g_settingsCore.getSetting('mouseHorzInvert')
                elif key == 'vertInvert':
                    value = g_settingsCore.getSetting('mouseVertInvert')
                elif key == 'backDraftInvert':
                    value = g_settingsCore.getSetting('backDraftInvert')
                elif ds is not None:
                    if path[2] == 'float':
                        value = ds[path[0]].readFloat(path[1], default)
                    elif path[2] == 'bool':
                        value = ds[path[0]].readBool(path[1], default)
                    else:
                        LOG_DEBUG('Unknown mouse settings type %s %s' % (key, path))
                mouse[key] = {'defaultValue': default,
                 'value': value}

        settings.append(mouse)
        g_windowsStoredData.stop()
        return settings

    def __getCaptureDeviceSettings(self):
        import VOIP
        rh = VOIP.getVOIPManager()
        devices = [ device.decode(sys.getfilesystemencoding()).encode('utf-8') for device in rh.captureDevices ]
        currentDeviceName = Settings.g_instance.userPrefs.readString(Settings.KEY_VOIP_DEVICE)
        currentCaptureDeviceIdx = -1
        try:
            currentCaptureDeviceIdx = devices.index(currentDeviceName)
        except:
            try:
                currentCaptureDeviceIdx = rh.captureDevices.index(rh.currentCaptureDevice)
            except:
                pass

        settings = {'current': currentCaptureDeviceIdx,
         'options': devices}
        return settings

    def onUpdateCaptureDevices(self, callbackId):
        self.__updateCaptureDevices()

    @process
    def __updateCaptureDevices(self):
        Waiting.show('__updateCaptureDevices')
        devices = yield VoiceChatInterface.g_instance.requestCaptureDevices()
        currentDeviceName = Settings.g_instance.userPrefs.readString(Settings.KEY_VOIP_DEVICE)
        currentCaptureDeviceIdx = -1
        try:
            currentCaptureDeviceIdx = devices.index(currentDeviceName)
        except Exception:
            try:
                import VOIP
                currentCaptureDeviceIdx = devices.index(VOIP.getVOIPManager().currentCaptureDevice)
            except Exception:
                pass

        value = [currentCaptureDeviceIdx]
        value.extend([ d.decode(sys.getfilesystemencoding()).encode('utf-8') for d in devices ])
        Waiting.hide('__updateCaptureDevices')
        self.call('SettingsDialog.updateCaptureDevices', value)

    def onRecreateDevice(self):
        if self.__settingsUI:
            if self.__currentSettings and self.__currentSettings != self.__getVideoSettings():
                self.__currentSettings = self.__getVideoSettings()
                self.__settingsUI.buildGraphicsData(self.__getVideoSettings())

    def onAutodetectSettings(self, callbackID):
        presetIndex = BigWorld.autoDetectGraphicsSettings()
        self.call('SettingsDialog.setPreset', [presetIndex])

    def onPopulateUI(self, *args):
        self.graphicsPresets.checkCurrentPreset(True)
        self.__currentSettings = self.__getVideoSettings()
        VoiceChatInterface.g_instance.processFailedMessage()
        if self.__settingsUI:
            self.__settingsUI.script = None
            self.__settingsUI = None
        settingsDialogName = args[1]
        self.__settingsUI = self.uiHolder.getMember(settingsDialogName)
        if self.__settingsUI:
            settings = self.__getSettings()
            self.__settingsUI.buildData(settings[0], settings[1], settings[2], settings[3])
            self.__settingsUI.buildGraphicsData(self.__getVideoSettings())
            self.__settingsUI.script = self
        else:
            LOG_ERROR('settingsDialog is not found in flash by name {0}'.format(settingsDialogName))
        return

    def onApplySettings(self, callbackId, settings):
        monitorIndex, presetIndex, settingsList, fullscreen = settings
        if (not self.resolutions.isVideoWindowed or fullscreen) and (monitorIndex != self.resolutions.realMonitorIndex or self.resolutions.monitorChanged):
            self.call('SettingsDialog.ApplySettings', ['restartNeeded'])
            return
        applyPresets = self.graphicsPresets.checkApplyGraphicsPreset(int(presetIndex), settingsList)
        self.call('SettingsDialog.ApplySettings', [applyPresets])

    def onDelaySettings(self, *args):
        self.apply(False, *args)

    def onCommitSettings(self, *args):
        self.apply(True, *args)

    def apply(self, restartApproved, callbackId, settings):
        restartClient = False
        import VOIP
        ppSettings = dict(AccountSettings.getSettings('players_panel'))
        ppSettings['showTypes'] = settings['ppShowTypes']
        if (not self.resolutions.isVideoWindowed or settings['fullScreen']) and (settings['monitor'] != self.resolutions.realMonitorIndex or self.resolutions.monitorChanged):
            restartClient = True
        AccountSettings.setSettings('players_panel', ppSettings)
        g_settingsCore.applySetting('ppShowLevels', settings['ppShowLevels'])
        g_settingsCore.applySetting('replayEnabled', settings['replayEnabled'])
        g_settingsCore.applySetting('fpsPerfomancer', settings['fpsPerfomancer'])
        AccountSettings.setSettings('nationalVoices', settings['nationalVoices'])
        AccountSettings.setSettings('isColorBlind', settings['isColorBlind'])
        g_settingsCore.applySetting('useServerAim', settings['useServerAim'])
        g_settingsCore.applySetting('showVehiclesCounter', settings['showVehiclesCounter'])
        g_settingsCore.applySetting('minimapAlpha', settings['minimapAlpha'])
        arcade = g_settingsCore.options.getSetting('arcade').fromAccountSettings(settings['arcade'])
        sniper = g_settingsCore.options.getSetting('sniper').fromAccountSettings(settings['sniper'])
        g_settingsCore.applySetting('arcade', arcade)
        g_settingsCore.applySetting('sniper', sniper)
        g_settingsCore.applySetting('enemy', settings['markers']['enemy'])
        g_settingsCore.applySetting('dead', settings['markers']['dead'])
        g_settingsCore.applySetting('ally', settings['markers']['ally'])
        g_settingsCore.applySetting('dynamicCamera', settings['dynamicCamera'])
        g_settingsCore.applySetting('horStabilizationSnp', settings['horStabilizationSnp'])
        if self.__altVoiceSetting.isOptionEnabled():
            altVoices = settings.get('alternativeVoices')
            if altVoices is not None:
                self.__altVoiceSetting.apply(altVoices)
        vManager = VibroManager.g_instance
        vManager.setGain(settings['vibroGain'] / 100.0)
        vEffGroups = vManager.getGroupsSettings()
        for groupName, newValue in [('engine', settings['vibroEngine']),
         ('acceleration', settings['vibroAcceleration']),
         ('shots', settings['vibroShots']),
         ('hits', settings['vibroHits']),
         ('collisions', settings['vibroCollisions']),
         ('damage', settings['vibroDamage']),
         ('gui', settings['vibroGUI'])]:
            if groupName in vEffGroups:
                vEffGroups[groupName].gain = newValue / 100.0
                vEffGroups[groupName].enabled = newValue > 0

        vManager.setGroupsSettings(vEffGroups)
        self.__voiceChatEnable(settings['enableVoIP'])
        self.__changeCaptureDevice(settings[Settings.KEY_VOIP_DEVICE])
        g_settingsCore.applySetting('enablePostMortemEffect', settings['enablePostMortemEffect'])
        self.uiHolder.clearCommands()
        keyboard = settings['controls']['keyboard']
        keyboardMapping = {}
        keysLayout = dict(g_settingsCore.options.getSetting('keyboard').KEYS_LAYOUT)
        layout = list(itertools.chain(*keysLayout.values()))
        for i in xrange(len(self.KEYBOARD_MAPPING_BLOCKS)):
            group_name = keyboard[i]['id']
            for j in xrange(len(self.KEYBOARD_MAPPING_BLOCKS[group_name])):
                key_name = keyboard[i]['commands'][j]['id']
                value = keyboard[i]['commands'][j]['key']
                cmd = self.KEYBOARD_MAPPING_COMMANDS[group_name][key_name]
                for item in layout:
                    key, command = item[0], item[1]
                    if command == cmd:
                        keyboardMapping[key] = value
                        break

        g_settingsCore.applySetting('keyboard', keyboardMapping)
        self.uiHolder.bindCommands()
        player = BigWorld.player()
        mouse = settings['controls']['mouse']
        if hasattr(player.inputHandler, 'ctrls'):
            player.inputHandler.ctrls['arcade'].camera.setUserConfigValue('sensitivity', mouse['arcadeSens']['value'])
            player.inputHandler.ctrls['sniper'].camera.setUserConfigValue('sensitivity', mouse['sniperSens']['value'])
            player.inputHandler.ctrls['strategic'].camera.setUserConfigValue('sensitivity', mouse['artSens']['value'])
        else:
            ds = Settings.g_instance.userPrefs[Settings.KEY_CONTROL_MODE]
            if ds:
                ds['arcadeMode/camera'].writeFloat('sensitivity', mouse['arcadeSens']['value'])
                ds['sniperMode/camera'].writeFloat('sensitivity', mouse['sniperSens']['value'])
                ds['strategicMode/camera'].writeFloat('sensitivity', mouse['artSens']['value'])
        g_settingsCore.applySetting('mouseHorzInvert', bool(mouse['horInvert']['value']))
        g_settingsCore.applySetting('mouseVertInvert', bool(mouse['vertInvert']['value']))
        g_settingsCore.applySetting('backDraftInvert', bool(mouse['backDraftInvert']['value']))
        self.resolutions.applyChanges(settings['fullScreen'], settings['vertSync'], settings['tripleBuffered'], settings['windowSize'] if not settings['fullScreen'] else settings['resolution'], settings['aspectRatio'], settings['multisampling'], settings['customAA'], settings['gamma'], settings['monitor'])
        if round(SoundGroups.g_instance.getVolume('masterVivox') * 100) != settings['masterVivoxVolume']:
            VOIP.getVOIPManager().setMasterVolume(settings['masterVivoxVolume'])
        if round(SoundGroups.g_instance.getVolume('micVivox') * 100) != settings['micVivoxVolume']:
            VOIP.getVOIPManager().setMicrophoneVolume(settings['micVivoxVolume'])
        SoundGroups.g_instance.setMasterVolume(float(settings['masterVolume']) / 100)
        SoundGroups.g_instance.setVolume('music', float(settings['musicVolume']) / 100)
        SoundGroups.g_instance.setVolume('voice', float(settings['voiceVolume']) / 100)
        SoundGroups.g_instance.setVolume('vehicles', float(settings['vehiclesVolume']) / 100)
        SoundGroups.g_instance.setVolume('effects', float(settings['effectsVolume']) / 100)
        SoundGroups.g_instance.setVolume('gui', float(settings['guiVolume']) / 100)
        SoundGroups.g_instance.setVolume('ambient', float(settings['ambientVolume']) / 100)
        SoundGroups.g_instance.setVolume('masterVivox', float(settings['masterVivoxVolume']) / 100)
        SoundGroups.g_instance.setVolume('micVivox', float(settings['micVivoxVolume']) / 100)
        SoundGroups.g_instance.setVolume('masterFadeVivox', float(settings['masterFadeVivoxVolume']) / 100)
        if len(VOIP.getVOIPManager().captureDevices):
            device = VOIP.getVOIPManager().captureDevices[0]
            if len(VOIP.getVOIPManager().captureDevices) > settings['captureDevice']:
                device = VOIP.getVOIPManager().captureDevices[settings['captureDevice']]
            VOIP.getVOIPManager().setCaptureDevice(device)
        g_settingsCore.applySetting('showDateMessage', settings['datetimeIdx'] & 1)
        g_settingsCore.applySetting('showTimeMessage', settings['datetimeIdx'] & 2)
        g_settingsCore.applySetting('enableOlFilter', settings['enableOlFilter'])
        g_settingsCore.applySetting('enableSpamFilter', settings['enableSpamFilter'])
        g_windowsStoredData.start()
        g_settingsCore.applySetting('enableStoreMws', settings['enableStoreChatMws'])
        g_settingsCore.applySetting('enableStoreCws', settings['enableStoreChatCws'])
        g_windowsStoredData.stop()
        g_settingsCore.applySetting('invitesFromFriendsOnly', settings['invitesFromFriendsOnly'])
        g_settingsCore.applySetting('storeReceiverInBattle', settings['storeReceiverInBattle'])
        gameplayKeys = filter(lambda item: item.startswith(self.GAMEPLAY_PREFIX) and bool(settings[item]), settings.keys())
        prefixLen = len(self.GAMEPLAY_PREFIX)
        gameplay_ctx.setMaskByNames(map(lambda key: str(key[prefixLen:]), gameplayKeys))
        qualitySettings = settings['quality']
        applyPresets = self.graphicsPresets.checkApplyGraphicsPreset(int(settings['graphicsQuality']), qualitySettings)
        if applyPresets:
            self.graphicsPresets.applyGraphicsPresets(int(settings['graphicsQuality']), qualitySettings)
            if applyPresets == 'restartNeeded':
                BigWorld.commitPendingGraphicsSettings()
                restartClient = True
            elif applyPresets == 'hasPendingSettings':
                BigWorld.commitPendingGraphicsSettings()
        g_settingsCore.applyStorages()
        g_postProcessing.refresh()
        if restartClient:
            BigWorld.savePreferences()
            if restartApproved:
                from BattleReplay import g_replayCtrl
                if g_replayCtrl.isPlaying and g_replayCtrl.playbackSpeed == 0:
                    g_replayCtrl.setPlaybackSpeedIdx(5)
                BigWorld.callback(0.3, BigWorld.restartGame)
            else:
                BigWorld.callback(0.0, partial(BigWorld.changeVideoMode, -1, BigWorld.isVideoWindowed()))
        return

    def onDialogClose(self, _):
        if self.__altVoiceSetting.isOptionEnabled():
            self.__altVoiceSetting.revert()
        if not g_battleContext.isInBattle:
            SoundGroups.g_instance.enableVoiceSounds(False)
        elif hasattr(BigWorld.player(), 'vehicle'):
            SoundGroups.g_instance.soundModes.setCurrentNation(nations.NAMES[BigWorld.player().vehicle.typeDescriptor.type.id[0]])
        g_settingsCore.clearStorages()
        if self.__settingsUI:
            self.__settingsUI.script = None
            self.__settingsUI = None
        return
# okay decompyling res/scripts/client/gui/scaleform/settingsinterface.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:26:45 EST

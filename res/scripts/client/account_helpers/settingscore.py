# Embedded file name: scripts/client/account_helpers/SettingsCore.py
import weakref
import Event
from Vibroeffects import VibroManager
from account_helpers.AccountSettings import AccountSettings
from account_helpers.ServerSettingsManager import ServerSettingsManager
from debug_utils import LOG_DEBUG
from gui.Scaleform.daapi.view.lobby.settings import constants, options, settings_storages
from gui.Scaleform.managers.windows_stored_data import TARGET_ID
from gui.shared.utils import graphics
__author__ = 'a_brukish'

class _SettingsCore(object):
    onSettingsChanged = Event.Event()

    def init(self):
        GAME = constants.GAME
        GRAPHICS = constants.GRAPHICS
        SOUND = constants.SOUND
        CONTROLS = constants.CONTROLS
        AIM = constants.AIM
        MARKERS = constants.MARKERS
        self.__serverSettings = ServerSettingsManager(weakref.proxy(self))
        VIDEO_SETTINGS_STORAGE = settings_storages.VideoSettingsStorage()
        GAME_SETTINGS_STORAGE = settings_storages.GameSettingsStorage(weakref.proxy(self.serverSettings))
        GRAPHICS_SETTINGS_STORAGE = settings_storages.GraphicsSettingsStorage(weakref.proxy(self.serverSettings))
        SOUND_SETTINGS_STORAGE = settings_storages.SoundSettingsStorage(weakref.proxy(self.serverSettings))
        KEYBOARD_SETTINGS_STORAGE = settings_storages.KeyboardSettingsStorage(weakref.proxy(self.serverSettings))
        CONTROLS_SETTINGS_STORAGE = settings_storages.ControlsSettingsStorage(weakref.proxy(self.serverSettings))
        AIM_SETTINGS_STORAGE = settings_storages.AimSettingsStorage(weakref.proxy(self.serverSettings))
        MARKERS_SETTINGS_STORAGE = settings_storages.MarkersSettingsStorage(weakref.proxy(self.serverSettings))
        MESSENGER_SETTINGS_STORAGE = settings_storages.MessengerSettingsStorage(weakref.proxy(GAME_SETTINGS_STORAGE))
        self.__storages = {'game': GAME_SETTINGS_STORAGE,
         'sound': SOUND_SETTINGS_STORAGE,
         'keyboard': KEYBOARD_SETTINGS_STORAGE,
         'controls': CONTROLS_SETTINGS_STORAGE,
         'aim': AIM_SETTINGS_STORAGE,
         'markers': MARKERS_SETTINGS_STORAGE,
         'graphics': GRAPHICS_SETTINGS_STORAGE,
         'video': VIDEO_SETTINGS_STORAGE,
         'messenger': MESSENGER_SETTINGS_STORAGE}
        self.__options = options.SettingsContainer(((GAME.REPLAY_ENABLED, options.ReplaySetting(storage=weakref.proxy(GAME_SETTINGS_STORAGE))),
         (GAME.ENABLE_SERVER_AIM, options.StorageAccountSetting(GAME.ENABLE_SERVER_AIM, storage=weakref.proxy(GAME_SETTINGS_STORAGE))),
         (GAME.MINIMAP_ALPHA, options.StorageAccountSetting(GAME.MINIMAP_ALPHA, storage=weakref.proxy(GAME_SETTINGS_STORAGE))),
         (GAME.ENABLE_POSTMORTEM, options.PostProcessingSetting(GAME.ENABLE_POSTMORTEM, 'mortem_post_effect', storage=weakref.proxy(GAME_SETTINGS_STORAGE))),
         (GAME.VIBRO_CONNECTED, options.ReadOnlySetting(lambda : VibroManager.g_instance.connect())),
         (GAME.SHOW_VEHICLES_COUNTER, options.StorageAccountSetting(GAME.SHOW_VEHICLES_COUNTER, storage=weakref.proxy(GAME_SETTINGS_STORAGE))),
         (GAME.DYNAMIC_CAMERA, options.DynamicCamera(GAME.DYNAMIC_CAMERA, storage=weakref.proxy(GAME_SETTINGS_STORAGE))),
         (GAME.VIBRO_GAIN, options.VibroSetting('master')),
         (GAME.VIBRO_ENGINE, options.VibroSetting('engine')),
         (GAME.VIBRO_ACCELERATION, options.VibroSetting('acceleration')),
         (GAME.VIBRO_SHOTS, options.VibroSetting('shots')),
         (GAME.VIBRO_HITS, options.VibroSetting('hits')),
         (GAME.VIBRO_COLLISIONS, options.VibroSetting('collisions')),
         (GAME.VIBRO_DAMAGE, options.VibroSetting('damage')),
         (GAME.VIBRO_GUI, options.VibroSetting('gui')),
         (GAME.ENABLE_OL_FILTER, options.MessengerSetting(GAME.ENABLE_OL_FILTER, storage=weakref.proxy(MESSENGER_SETTINGS_STORAGE))),
         (GAME.ENABLE_SPAM_FILTER, options.MessengerSetting(GAME.ENABLE_SPAM_FILTER, storage=weakref.proxy(MESSENGER_SETTINGS_STORAGE))),
         (GAME.SHOW_DATE_MESSAGE, options.MessengerDateTimeSetting(1, storage=weakref.proxy(MESSENGER_SETTINGS_STORAGE))),
         (GAME.SHOW_TIME_MESSAGE, options.MessengerDateTimeSetting(2, storage=weakref.proxy(MESSENGER_SETTINGS_STORAGE))),
         (GAME.INVITES_FROM_FRIENDS, options.MessengerSetting(GAME.INVITES_FROM_FRIENDS, storage=weakref.proxy(MESSENGER_SETTINGS_STORAGE))),
         (GAME.ENABLE_CHAT_CWS, options.WindowsTarget4StoredData(TARGET_ID.CHANNEL_CAROUSEL)),
         (GAME.ENABLE_CHAT_MWS, options.WindowsTarget4StoredData(TARGET_ID.CHAT_MANAGEMENT)),
         (GAME.STORE_RECEIVER_IN_BATTLE, options.MessengerSetting(GAME.STORE_RECEIVER_IN_BATTLE, storage=weakref.proxy(MESSENGER_SETTINGS_STORAGE))),
         (GAME.PLAYERS_PANELS_SHOW_LEVELS, options.PlayersPanelSetting(GAME.PLAYERS_PANELS_SHOW_LEVELS, 'players_panel', 'showLevels', storage=weakref.proxy(GAME_SETTINGS_STORAGE))),
         (GAME.PLAYERS_PANELS_SHOW_TYPES, options.AccountSetting('players_panel', 'showTypes')),
         (GAME.SNIPER_MODE_SWINGING_ENABLED, options.SniperModeSwingingSetting()),
         (GAME.GAMEPLAY_CTF, options.GameplaySetting(GAME.GAMEPLAY_MASK, 'ctf', storage=weakref.proxy(GAME_SETTINGS_STORAGE))),
         (GAME.GAMEPLAY_DOMINATION, options.GameplaySetting(GAME.GAMEPLAY_MASK, 'domination', storage=weakref.proxy(GAME_SETTINGS_STORAGE))),
         (GAME.GAMEPLAY_ASSAULT, options.GameplaySetting(GAME.GAMEPLAY_MASK, 'assault', storage=weakref.proxy(GAME_SETTINGS_STORAGE))),
         (GRAPHICS.MONITOR, options.MonitorSetting()),
         (GRAPHICS.WINDOW_SIZE, options.WindowSizeSetting()),
         (GRAPHICS.RESOLUTION, options.VideoModeSetting(storage=weakref.proxy(VIDEO_SETTINGS_STORAGE))),
         (GRAPHICS.FULLSCREEN, options.FullscreenSetting(storage=weakref.proxy(VIDEO_SETTINGS_STORAGE))),
         (GRAPHICS.COLOR_BLIND, options.AccountSetting('isColorBlind')),
         (GRAPHICS.GAMMA, options.GammaSetting()),
         (GRAPHICS.TRIPLE_BUFFERED, options.TripleBufferedSetting()),
         (GRAPHICS.VERTICAL_SYNC, options.VerticalSyncSetting()),
         (GRAPHICS.MULTISAMPLING, options.MultisamplingSetting()),
         (GRAPHICS.CUSTOM_AA, options.CustomAASetting()),
         (GRAPHICS.ASPECT_RATIO, options.AspectRatioSetting()),
         (GRAPHICS.FPS_PERFOMANCER, options.FPSPerfomancerSetting(GRAPHICS.FPS_PERFOMANCER, storage=weakref.proxy(GRAPHICS_SETTINGS_STORAGE))),
         (GRAPHICS.PRESETS, options.GraphicsPresetSetting()),
         (GRAPHICS.RENDER_PIPELINE, options.GraphicSetting('RENDER_PIPELINE')),
         (GRAPHICS.TEXTURE_QUALITY, options.TextureQualitySetting()),
         (GRAPHICS.DECALS_QUALITY, options.GraphicSetting('DECALS_QUALITY')),
         (GRAPHICS.OBJECT_LOD, options.GraphicSetting('OBJECT_LOD')),
         (GRAPHICS.FAR_PLANE, options.GraphicSetting('FAR_PLANE')),
         (GRAPHICS.TERRAIN_QUALITY, options.TerrainQualitySetting()),
         (GRAPHICS.SHADOWS_QUALITY, options.GraphicSetting('SHADOWS_QUALITY')),
         (GRAPHICS.LIGHTING_QUALITY, options.GraphicSetting('LIGHTING_QUALITY')),
         (GRAPHICS.SPEEDTREE_QUALITY, options.GraphicSetting('SPEEDTREE_QUALITY')),
         (GRAPHICS.FLORA_QUALITY, options.FloraQualitySetting()),
         (GRAPHICS.WATER_QUALITY, options.GraphicSetting('WATER_QUALITY')),
         (GRAPHICS.EFFECTS_QUALITY, options.GraphicSetting('EFFECTS_QUALITY')),
         (GRAPHICS.POST_PROCESSING_QUALITY, options.GraphicSetting('POST_PROCESSING_QUALITY')),
         (GRAPHICS.SNIPER_MODE_EFFECTS_QUALITY, options.GraphicSetting('SNIPER_MODE_EFFECTS_QUALITY')),
         (GRAPHICS.VEHICLE_DUST_ENABLED, options.GraphicSetting('VEHICLE_DUST_ENABLED')),
         (GRAPHICS.SNIPER_MODE_GRASS_ENABLED, options.GraphicSetting('SNIPER_MODE_GRASS_ENABLED')),
         (GRAPHICS.VEHICLE_TRACES_ENABLED, options.GraphicSetting('VEHICLE_TRACES_ENABLED')),
         (GRAPHICS.GRAPHICS_SETTINGS_LIST, options.ReadOnlySetting(lambda : graphics.GRAPHICS_SETTINGS.ALL())),
         (SOUND.MASTER, options.SoundSetting('master')),
         (SOUND.MUSIC, options.SoundSetting('music')),
         (SOUND.VOICE, options.SoundSetting('voice')),
         (SOUND.VEHICLES, options.SoundSetting('vehicles')),
         (SOUND.EFFECTS, options.SoundSetting('effects')),
         (SOUND.GUI, options.SoundSetting('gui')),
         (SOUND.AMBIENT, options.SoundSetting('ambient')),
         (SOUND.NATIONS_VOICES, options.AccountSetting('nationalVoices')),
         (SOUND.VOIP_MASTER_FADE, options.SoundSetting('masterFadeVivox')),
         (SOUND.VOIP_ENABLE, options.VOIPSetting()),
         (SOUND.VOIP_MASTER, options.VOIPMasterSoundSetting()),
         (SOUND.VOIP_MIC, options.VOIPMicSoundSetting(True)),
         (SOUND.CAPTURE_DEVICES, options.VOIPCaptureDevicesSetting()),
         (SOUND.VOIP_SUPPORTED, options.VOIPSupportSetting()),
         (SOUND.ALT_VOICES, options.AltVoicesSetting(storage=weakref.proxy(SOUND_SETTINGS_STORAGE))),
         (CONTROLS.MOUSE_ARCADE_SENS, options.MouseSensitivitySetting('arcade')),
         (CONTROLS.MOUSE_SNIPER_SENS, options.MouseSensitivitySetting('sniper')),
         (CONTROLS.MOUSE_STRATEGIC_SENS, options.MouseSensitivitySetting('strategic')),
         (CONTROLS.MOUSE_HORZ_INVERSION, options.MouseInversionSetting(CONTROLS.MOUSE_HORZ_INVERSION, 'horzInvert', storage=weakref.proxy(CONTROLS_SETTINGS_STORAGE))),
         (CONTROLS.MOUSE_VERT_INVERSION, options.MouseInversionSetting(CONTROLS.MOUSE_VERT_INVERSION, 'vertInvert', storage=weakref.proxy(CONTROLS_SETTINGS_STORAGE))),
         (CONTROLS.BACK_DRAFT_INVERSION, options.BackDraftInversionSetting(storage=weakref.proxy(CONTROLS_SETTINGS_STORAGE))),
         (CONTROLS.KEYBOARD, options.KeyboardSettings(storage=weakref.proxy(KEYBOARD_SETTINGS_STORAGE))),
         (AIM.ARCADE, options.AimSetting('arcade', storage=weakref.proxy(AIM_SETTINGS_STORAGE))),
         (AIM.SNIPER, options.AimSetting('sniper', storage=weakref.proxy(AIM_SETTINGS_STORAGE))),
         (MARKERS.ENEMY, options.VehicleMarkerSetting(MARKERS.ENEMY, storage=weakref.proxy(MARKERS_SETTINGS_STORAGE))),
         (MARKERS.DEAD, options.VehicleMarkerSetting(MARKERS.DEAD, storage=weakref.proxy(MARKERS_SETTINGS_STORAGE))),
         (MARKERS.ALLY, options.VehicleMarkerSetting(MARKERS.ALLY, storage=weakref.proxy(MARKERS_SETTINGS_STORAGE)))))
        AccountSettings.onSettingsChanging += self.__onAccountSettingsChanging
        LOG_DEBUG('SettingsCore is initialized')

    def fini(self):
        self.__storages = None
        self.__options = None
        self.__serverSettings = None
        AccountSettings.onSettingsChanging -= self.__onAccountSettingsChanging
        LOG_DEBUG('SettingsCore is destroyed')
        return

    @property
    def options(self):
        return self.__options

    @property
    def storages(self):
        return self.__storages

    @property
    def serverSettings(self):
        return self.__serverSettings

    def getSetting(self, name):
        return self.options.getSetting(name).get()

    def applySetting(self, name, value):
        if self.isSettingChanged(name, value):
            return self.options.getSetting(name).apply(value)
        return False

    def isSettingChanged(self, name, value):
        return self.getSetting(name) != value

    def applyStorages(self):
        for storage in self.__storages.values():
            storage.apply()
            storage.clear()

    def clearStorages(self):
        for storage in self.__storages.values():
            storage.clear()

    def __onAccountSettingsChanging(self, key, value):
        LOG_DEBUG('Apply account setting: ', {key: value})
        self.onSettingsChanged({key: value})


g_settingsCore = _SettingsCore()
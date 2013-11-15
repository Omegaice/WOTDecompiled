# 2013.11.15 11:26:13 EST
# Embedded file name: scripts/client/gui/Scaleform/daapi/view/lobby/settings/constants.py
from gui.shared.utils import CONST_CONTAINER

class GRAPHICS(CONST_CONTAINER):
    MONITOR = 'monitor'
    FULLSCREEN = 'fullScreen'
    WINDOW_SIZE = 'windowSize'
    RESOLUTION = 'resolution'
    ASPECT_RATIO = 'aspectRatio'
    CUSTOM_AA = 'customAA'
    MULTISAMPLING = 'multisampling'
    GAMMA = 'gamma'
    VERTICAL_SYNC = 'vertSync'
    TRIPLE_BUFFERED = 'tripleBuffered'
    COLOR_BLIND = 'isColorBlind'
    GRAPHICS_SETTINGS_LIST = 'qualityOrder'
    PRESETS = 'presets'
    QUALITY_PRESET = 'graphicsQuality'
    SMOOTHING = 'smoothing'
    FPS_PERFOMANCER = 'fpsPerfomancer'
    RENDER_PIPELINE = 'RENDER_PIPELINE'
    TEXTURE_QUALITY = 'TEXTURE_QUALITY'
    DECALS_QUALITY = 'DECALS_QUALITY'
    OBJECT_LOD = 'OBJECT_LOD'
    FAR_PLANE = 'FAR_PLANE'
    TERRAIN_QUALITY = 'TERRAIN_QUALITY'
    SHADOWS_QUALITY = 'SHADOWS_QUALITY'
    LIGHTING_QUALITY = 'LIGHTING_QUALITY'
    SPEEDTREE_QUALITY = 'SPEEDTREE_QUALITY'
    FLORA_QUALITY = 'FLORA_QUALITY'
    WATER_QUALITY = 'WATER_QUALITY'
    EFFECTS_QUALITY = 'EFFECTS_QUALITY'
    POST_PROCESSING_QUALITY = 'POST_PROCESSING_QUALITY'
    SNIPER_MODE_EFFECTS_QUALITY = 'SNIPER_MODE_EFFECTS_QUALITY'
    VEHICLE_DUST_ENABLED = 'VEHICLE_DUST_ENABLED'
    SNIPER_MODE_GRASS_ENABLED = 'SNIPER_MODE_GRASS_ENABLED'
    VEHICLE_TRACES_ENABLED = 'VEHICLE_TRACES_ENABLED'


class GAME(CONST_CONTAINER):
    ENABLE_OL_FILTER = 'enableOlFilter'
    ENABLE_SPAM_FILTER = 'enableSpamFilter'
    DATE_TIME_MESSAGE_INDEX = 'datetimeIdx'
    SHOW_DATE_MESSAGE = 'showDateMessage'
    SHOW_TIME_MESSAGE = 'showTimeMessage'
    INVITES_FROM_FRIENDS = 'invitesFromFriendsOnly'
    ENABLE_CHAT_CWS = 'enableStoreCws'
    ENABLE_CHAT_MWS = 'enableStoreMws'
    STORE_RECEIVER_IN_BATTLE = 'storeReceiverInBattle'
    MINIMAP_ALPHA = 'minimapAlpha'
    ENABLE_POSTMORTEM = 'enablePostMortemEffect'
    REPLAY_ENABLED = 'replayEnabled'
    ENABLE_SERVER_AIM = 'useServerAim'
    SHOW_VEHICLES_COUNTER = 'showVehiclesCounter'
    DYNAMIC_CAMERA = 'dynamicCamera'
    SNIPER_MODE_STABILIZATION = 'horStabilizationSnp'
    PLAYERS_PANELS_SHOW_LEVELS = 'ppShowLevels'
    PLAYERS_PANELS_SHOW_TYPES = 'ppShowTypes'
    VIBRO_CONNECTED = 'vibroIsConnected'
    VIBRO_GAIN = 'vibroGain'
    VIBRO_ENGINE = 'vibroEngine'
    VIBRO_ACCELERATION = 'vibroAcceleration'
    VIBRO_SHOTS = 'vibroShots'
    VIBRO_HITS = 'vibroHits'
    VIBRO_COLLISIONS = 'vibroCollisions'
    VIBRO_DAMAGE = 'vibroDamage'
    VIBRO_GUI = 'vibroGUI'
    GAMEPLAY_MASK = 'gameplayMask'
    GAMEPLAY_CTF = 'gameplay_ctf'
    GAMEPLAY_DOMINATION = 'gameplay_domination'
    GAMEPLAY_ASSAULT = 'gameplay_assault'
    SNIPER_MODE_SWINGING_ENABLED = 'SNIPER_MODE_SWINGING_ENABLED'


class SOUND(CONST_CONTAINER):
    MASTER = 'masterVolume'
    MUSIC = 'musicVolume'
    VOICE = 'voiceVolume'
    VEHICLES = 'vehiclesVolume'
    EFFECTS = 'effectsVolume'
    GUI = 'guiVolume'
    AMBIENT = 'ambientVolume'
    NATIONS_VOICES = 'nationalVoices'
    ALT_VOICES = 'alternativeVoices'
    CAPTURE_DEVICES = 'captureDevice'
    VOIP_ENABLE = 'enableVoIP'
    VOIP_MASTER = 'masterVivoxVolume'
    VOIP_MIC = 'micVivoxVolume'
    VOIP_MASTER_FADE = 'masterFadeVivoxVolume'
    VOIP_SUPPORTED = 'voiceChatSupported'


class CONTROLS(CONST_CONTAINER):
    MOUSE_ARCADE_SENS = 'mouseArcadeSens'
    MOUSE_SNIPER_SENS = 'mouseSniperSens'
    MOUSE_STRATEGIC_SENS = 'mouseStrategicSens'
    MOUSE_HORZ_INVERSION = 'mouseHorzInvert'
    MOUSE_VERT_INVERSION = 'mouseVertInvert'
    BACK_DRAFT_INVERSION = 'backDraftInvert'
    KEYBOARD = 'keyboard'


class AIM(CONST_CONTAINER):
    ARCADE = 'arcade'
    SNIPER = 'sniper'


class MARKERS(CONST_CONTAINER):
    ALLY = 'ally'
    ENEMY = 'enemy'
    DEAD = 'dead'
# okay decompyling res/scripts/client/gui/scaleform/daapi/view/lobby/settings/constants.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:26:13 EST

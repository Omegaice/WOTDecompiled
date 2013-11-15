# 2013.11.15 11:25:10 EST
# Embedded file name: scripts/client/account_helpers/ServerSettingsManager.py
import BigWorld
import constants
from collections import namedtuple
from account_helpers.SettingsCache import g_settingsCache
from adisp import process, async
from debug_utils import LOG_ERROR, LOG_DEBUG
from gui.Scaleform.daapi.view.lobby.settings import constants as settings_constants
from gui.shared.utils import CONST_CONTAINER
from helpers import isPlayerAvatar
__author__ = 'a_brukish'

class SETTINGS_SECTIONS(CONST_CONTAINER):
    GAME = 'GAME'
    GRAPHICS = 'GRAPHICS'
    SOUND = 'SOUND'
    CONTROLS = 'CONTROLS'
    AIM_1 = 'AIM_1'
    AIM_2 = 'AIM_2'
    AIM_3 = 'AIM_3'
    MARKERS = 'MARKERS'
    CAROUSEL_FILTER = 'CAROUSEL_FILTER'


class ServerSettingsManager(object):
    __version = 3
    GAME = settings_constants.GAME
    GRAPHICS = settings_constants.GRAPHICS
    SOUND = settings_constants.SOUND
    CONTROLS = settings_constants.CONTROLS
    Section = namedtuple('Section', ['masks', 'offsets'])
    Offset = namedtuple('Offset', ['offset', 'mask'])
    SECTIONS = {SETTINGS_SECTIONS.GAME: Section(masks={GAME.ENABLE_OL_FILTER: 0,
                              GAME.ENABLE_SPAM_FILTER: 1,
                              GAME.INVITES_FROM_FRIENDS: 2,
                              GAME.STORE_RECEIVER_IN_BATTLE: 3,
                              GAME.PLAYERS_PANELS_SHOW_LEVELS: 4,
                              GAME.ENABLE_POSTMORTEM: 5,
                              GAME.DYNAMIC_CAMERA: 6,
                              GAME.REPLAY_ENABLED: 7,
                              GAME.ENABLE_SERVER_AIM: 8,
                              GAME.SHOW_VEHICLES_COUNTER: 9,
                              GAME.SNIPER_MODE_STABILIZATION: 13}, offsets={GAME.GAMEPLAY_MASK: Offset(10, 1024 | 2048 | 4096),
                              GAME.DATE_TIME_MESSAGE_INDEX: Offset(16, 983040),
                              GAME.MINIMAP_ALPHA: Offset(20, 267386880)}),
     SETTINGS_SECTIONS.GRAPHICS: Section(masks={GRAPHICS.FPS_PERFOMANCER: 0}, offsets={}),
     SETTINGS_SECTIONS.SOUND: Section(masks={}, offsets={SOUND.ALT_VOICES: Offset(0, 255)}),
     SETTINGS_SECTIONS.CONTROLS: Section(masks={CONTROLS.MOUSE_HORZ_INVERSION: 0,
                                  CONTROLS.MOUSE_VERT_INVERSION: 1,
                                  CONTROLS.BACK_DRAFT_INVERSION: 2}, offsets={}),
     SETTINGS_SECTIONS.AIM_1: Section(masks={}, offsets={'net': Offset(0, 255),
                               'netType': Offset(8, 65280),
                               'centralTag': Offset(16, 16711680),
                               'centralTagType': Offset(24, 4278190080L)}),
     SETTINGS_SECTIONS.AIM_2: Section(masks={}, offsets={'reloader': Offset(0, 255),
                               'condition': Offset(8, 65280),
                               'mixing': Offset(16, 16711680),
                               'mixingType': Offset(24, 4278190080L)}),
     SETTINGS_SECTIONS.AIM_3: Section(masks={}, offsets={'cassette': Offset(0, 255),
                               'gunTag': Offset(8, 65280),
                               'gunTagType': Offset(16, 16711680),
                               'reloaderTimer': Offset(24, 4278190080L)}),
     SETTINGS_SECTIONS.MARKERS: Section(masks={'markerBaseIcon': 0,
                                 'markerBaseLevel': 1,
                                 'markerBaseHpIndicator': 2,
                                 'markerBaseDamage': 3,
                                 'markerBaseVehicleName': 4,
                                 'markerBasePlayerName': 5,
                                 'markerAltIcon': 16,
                                 'markerAltLevel': 17,
                                 'markerAltHpIndicator': 18,
                                 'markerAltDamage': 19,
                                 'markerAltVehicleName': 20,
                                 'markerAltPlayerName': 21}, offsets={'markerBaseHp': Offset(8, 65280),
                                 'markerAltHp': Offset(24, 4278190080L)}),
     SETTINGS_SECTIONS.CAROUSEL_FILTER: Section(masks={'ready': 1,
                                         'nationIsNegative': 2,
                                         'tankTypeIsNegative': 3}, offsets={'nation': Offset(8, 65280),
                                         'tankType': Offset(16, 16711680)})}
    AIM_MAPPING = {'net': 1,
     'netType': 1,
     'centralTag': 1,
     'centralTagType': 1,
     'reloader': 2,
     'condition': 2,
     'mixing': 2,
     'mixingType': 2,
     'cassette': 3,
     'gunTag': 3,
     'gunTagType': 3,
     'reloaderTimer': 3}

    def __init__(self, core):
        self._core = core

    @property
    def version(self):
        return self.__version

    @process
    def applySettings(self):
        yield self._updateToVersion()
        enableBattleReplay = self._core.options.getSetting(self.GAME.REPLAY_ENABLED)
        enableBattleReplayValue = enableBattleReplay.get()
        from BattleReplay import g_replayCtrl
        g_replayCtrl.enableAutoRecordingBattles(enableBattleReplayValue)
        enablePostMortem = self._core.options.getSetting(self.GAME.ENABLE_POSTMORTEM)
        enablePostMortemValue = enablePostMortem.get()
        from post_processing import g_postProcessing
        g_postProcessing.setSetting('mortem_post_effect', enablePostMortemValue)
        g_postProcessing.refresh()
        enableDynamicCamera = self._core.options.getSetting(self.GAME.DYNAMIC_CAMERA)
        enableDynamicCameraValue = enableDynamicCamera.get()
        enableSniperStabilization = self._core.options.getSetting(self.GAME.SNIPER_MODE_STABILIZATION)
        enableSniperStabilizationValue = enableSniperStabilization.get()
        from AvatarInputHandler import AvatarInputHandler
        AvatarInputHandler.enableDynamicCamera(enableDynamicCameraValue, enableSniperStabilizationValue)
        from messenger.doc_loaders import user_prefs
        from messenger import g_settings as messenger_settings
        user_prefs.loadFromServer(messenger_settings)
        masks = self.SECTIONS[SETTINGS_SECTIONS.GRAPHICS].masks
        offsets = self.SECTIONS[SETTINGS_SECTIONS.GRAPHICS].offsets
        graphicSettingNames = masks.keys() + offsets.keys()
        for setting in graphicSettingNames:
            settingOption = self._core.options.getSetting(setting)
            settingValue = settingOption.get()
            settingOption.setSystemValue(settingValue)

        alternativeVoices = self._core.options.getSetting(self.SOUND.ALT_VOICES)
        alternativeVoicesValue = alternativeVoices.get()
        alternativeVoices.setSystemValue(alternativeVoicesValue)
        self._core.options.getSetting('keyboard').setSystemValue()
        if isPlayerAvatar():
            BigWorld.player().invRotationOnBackMovement = self._core.getSetting('backDraftInvert')

    def getGameSetting(self, key, default = None):
        return self._getSectionSettings(SETTINGS_SECTIONS.GAME, key, default)

    def setGameSettings(self, settings):
        self._setSectionSettings(SETTINGS_SECTIONS.GAME, settings)

    def getGraphicsSetting(self, key, default = None):
        return self._getSectionSettings(SETTINGS_SECTIONS.GRAPHICS, key, default)

    def setGraphicsSettings(self, settings):
        self._setSectionSettings(SETTINGS_SECTIONS.GRAPHICS, settings)

    def getSoundSetting(self, key, default = None):
        return self._getSectionSettings(SETTINGS_SECTIONS.SOUND, key, default)

    def setSoundSettings(self, settings):
        self._setSectionSettings(SETTINGS_SECTIONS.SOUND, settings)

    def getControlsSetting(self, key, default = None):
        return self._getSectionSettings(SETTINGS_SECTIONS.CONTROLS, key, default)

    def setControlsSettings(self, settings):
        self._setSectionSettings(SETTINGS_SECTIONS.CONTROLS, settings)

    def getAimSetting(self, section, key, default = None):
        number = self.AIM_MAPPING[key]
        storageKey = 'AIM_%(section)s_%(number)d' % {'section': section.upper(),
         'number': number}
        settingsKey = 'AIM_%(number)d' % {'number': number}
        storedValue = g_settingsCache.getSectionSettings(storageKey, None)
        masks = self.SECTIONS[settingsKey].masks
        offsets = self.SECTIONS[settingsKey].offsets
        if storedValue is not None:
            return self._extractValue(key, storedValue, default, masks, offsets)
        else:
            return default

    def _buildAimSettings(self, settings):
        settingToServer = {}
        for section, options in settings.iteritems():
            mapping = {}
            for key, value in options.iteritems():
                number = self.AIM_MAPPING[key]
                mapping.setdefault(number, {})[key] = value

            for number, value in mapping.iteritems():
                settingsKey = 'AIM_%(number)d' % {'number': number}
                storageKey = 'AIM_%(section)s_%(number)d' % {'section': section.upper(),
                 'number': number}
                storingValue = storedValue = g_settingsCache.getSetting(storageKey)
                masks = self.SECTIONS[settingsKey].masks
                offsets = self.SECTIONS[settingsKey].offsets
                storingValue = self._mapValues(value, storingValue, masks, offsets)
                if storedValue == storingValue:
                    continue
                settingToServer[storageKey] = storingValue

        return settingToServer

    def setAimSettings(self, settings):
        g_settingsCache.setSettings(self._buildAimSettings(settings))
        self.setVersion()
        self._core.onSettingsChanged(settings)

    def getMarkersSetting(self, section, key, default = None):
        storageKey = 'MARKERS_%(section)s' % {'section': section.upper()}
        storedValue = g_settingsCache.getSectionSettings(storageKey, None)
        masks = self.SECTIONS[SETTINGS_SECTIONS.MARKERS].masks
        offsets = self.SECTIONS[SETTINGS_SECTIONS.MARKERS].offsets
        if storedValue is not None:
            return self._extractValue(key, storedValue, default, masks, offsets)
        else:
            return default

    def _buildMarkersSettings(self, settings):
        settingToServer = {}
        for section, options in settings.iteritems():
            storageKey = 'MARKERS_%(section)s' % {'section': section.upper()}
            storingValue = storedValue = g_settingsCache.getSetting(storageKey)
            masks = self.SECTIONS[SETTINGS_SECTIONS.MARKERS].masks
            offsets = self.SECTIONS[SETTINGS_SECTIONS.MARKERS].offsets
            storingValue = self._mapValues(options, storingValue, masks, offsets)
            if storedValue == storingValue:
                continue
            settingToServer[storageKey] = storingValue

        return settingToServer

    def setMarkersSettings(self, settings):
        g_settingsCache.setSettings(self._buildMarkersSettings(settings))
        self.setVersion()
        self._core.onSettingsChanged(settings)

    def setVersion(self):
        if g_settingsCache.getVersion() != self.__version:
            g_settingsCache.setVersion(self.__version)

    def getVersion(self):
        return g_settingsCache.getVersion()

    def setSettings(self, settings):
        g_settingsCache.setSettings(settings)
        self.setVersion()
        self._core.onSettingsChanged(settings)

    def getSetting(self, key, default = None):
        return g_settingsCache.getSetting(key, default)

    def getSection(self, section, defaults = None):
        result = {}
        defaults = defaults or {}
        masks = self.SECTIONS[section].masks
        offsets = self.SECTIONS[section].offsets
        for m in masks:
            default = defaults.get(m, None)
            result[m] = self._getSectionSettings(section, m, default)

        for o in offsets:
            default = defaults.get(o, None)
            result[o] = self._getSectionSettings(section, o, default)

        return result

    def setSection(self, section, settings):
        if section in self.SECTIONS:
            self._setSectionSettings(section, settings)

    def _getSectionSettings(self, section, key, default = None):
        storedValue = g_settingsCache.getSectionSettings(section, None)
        masks = self.SECTIONS[section].masks
        offsets = self.SECTIONS[section].offsets
        if storedValue is not None:
            return self._extractValue(key, storedValue, default, masks, offsets)
        else:
            return default

    def _buildSectionSettings(self, section, settings):
        storedValue = g_settingsCache.getSectionSettings(section, None)
        storingValue = storedValue if storedValue is not None else 0
        masks = self.SECTIONS[section].masks
        offsets = self.SECTIONS[section].offsets
        return self._mapValues(settings, storingValue, masks, offsets)

    def _setSectionSettings(self, section, settings):
        LOG_DEBUG('Applying %s server settings: ' % section, settings)
        storedValue = g_settingsCache.getSectionSettings(section, None)
        storingValue = self._buildSectionSettings(section, settings)
        if storedValue == storingValue:
            return
        else:
            g_settingsCache.setSectionSettings(section, storingValue)
            self.setVersion()
            self._core.onSettingsChanged(settings)
            return

    def _extractValue(self, key, storedValue, default, masks, offsets):
        if key in masks:
            return storedValue >> masks[key] & 1
        elif key in offsets:
            return (storedValue & offsets[key].mask) >> offsets[key].offset
        else:
            LOG_ERROR('Trying to extract unsupported option: ', key)
            return default

    def _mapValues(self, settings, storingValue, masks, offsets):
        for key, value in settings.iteritems():
            if key in masks:
                storingValue &= ~(1 << masks[key])
                itemValue = int(value) << masks[key]
            elif key in offsets:
                storingValue &= ~offsets[key].mask
                itemValue = int(value) << offsets[key].offset
            else:
                LOG_ERROR('Trying to apply unsupported option: ', key, value)
                continue
            storingValue |= itemValue

        return storingValue

    @async
    @process
    def _updateToVersion(self, callback = None):
        currentVersion = g_settingsCache.getVersion()
        gameData = {}
        controlsData = {}
        aimData = {}
        markersData = {}
        keyboardData = {}
        initialized = False
        processed = False
        if currentVersion < 1:
            gameData, controlsData, aimData, markersData, keyboardData = self._initializeDefaultSettings()
            initialized = True
        if currentVersion < 2 and not initialized:

            @async
            def wrapper(callback = None):
                BigWorld.player().intUserSettings.delIntSettings(range(1, 60), callback)

            yield wrapper()
            gameData, controlsData, aimData, markersData, keyboardData = self._initializeDefaultSettings()
            initialized = True
            processed = True
        if currentVersion < 3:
            if not initialized:
                aimData.update({'arcade': self._core.getSetting('arcade'),
                 'sniper': self._core.getSetting('sniper')})
            aimData['arcade']['reloaderTimer'] = 100
            aimData['sniper']['reloaderTimer'] = 100
            if not initialized:
                gameData['horStabilizationSnp'] = self._core.getSetting('dynamicCamera')
        if not processed:
            yield lambda callback: callback(None)
        self._setSettingsSections(gameData, controlsData, aimData, markersData, keyboardData)
        callback(self)
        return

    def _initializeDefaultSettings(self):
        LOG_DEBUG('Initializing server settings.')
        from AccountSettings import AccountSettings
        gameData = {self.GAME.DATE_TIME_MESSAGE_INDEX: 2,
         self.GAME.ENABLE_OL_FILTER: self._core.getSetting(self.GAME.ENABLE_OL_FILTER),
         self.GAME.ENABLE_SPAM_FILTER: self._core.getSetting(self.GAME.ENABLE_SPAM_FILTER),
         self.GAME.INVITES_FROM_FRIENDS: self._core.getSetting(self.GAME.INVITES_FROM_FRIENDS),
         self.GAME.STORE_RECEIVER_IN_BATTLE: self._core.getSetting(self.GAME.STORE_RECEIVER_IN_BATTLE),
         self.GAME.REPLAY_ENABLED: self._core.getSetting(self.GAME.REPLAY_ENABLED),
         self.GAME.ENABLE_SERVER_AIM: self._core.getSetting(self.GAME.ENABLE_SERVER_AIM),
         self.GAME.SHOW_VEHICLES_COUNTER: self._core.getSetting(self.GAME.SHOW_VEHICLES_COUNTER),
         self.GAME.MINIMAP_ALPHA: self._core.getSetting(self.GAME.MINIMAP_ALPHA),
         self.GAME.PLAYERS_PANELS_SHOW_LEVELS: self._core.getSetting(self.GAME.PLAYERS_PANELS_SHOW_LEVELS),
         self.GAME.GAMEPLAY_MASK: AccountSettings.getSettingsDefault('gameplayMask'),
         self.GAME.ENABLE_POSTMORTEM: self._core.getSetting(self.GAME.ENABLE_POSTMORTEM)}
        aimData = {'arcade': self._core.getSetting('arcade'),
         'sniper': self._core.getSetting('sniper')}
        markersData = {'enemy': self._core.options.getSetting('enemy').getDefaultValue(),
         'dead': self._core.options.getSetting('dead').getDefaultValue(),
         'ally': self._core.options.getSetting('ally').getDefaultValue()}
        controlsData = {self.CONTROLS.MOUSE_HORZ_INVERSION: self._core.getSetting(self.CONTROLS.MOUSE_HORZ_INVERSION),
         self.CONTROLS.MOUSE_VERT_INVERSION: self._core.getSetting(self.CONTROLS.MOUSE_VERT_INVERSION),
         self.CONTROLS.BACK_DRAFT_INVERSION: self._core.getSetting(self.CONTROLS.BACK_DRAFT_INVERSION)}
        keyboardData = self._core.options.getSetting('keyboard').getDefaultMapping()
        from gui import game_control
        if game_control.g_instance.igr.getRoomType() == constants.IGR_TYPE.NONE:
            import Settings
            from messenger import g_settings as messenger_settings
            section = Settings.g_instance.userPrefs
            if section.has_key(Settings.KEY_MESSENGER_PREFERENCES):
                subSec = section[Settings.KEY_MESSENGER_PREFERENCES]
                tags = subSec.keys()
                _userProps = {self.GAME.DATE_TIME_MESSAGE_INDEX: 'readInt',
                 self.GAME.ENABLE_OL_FILTER: 'readBool',
                 self.GAME.ENABLE_SPAM_FILTER: 'readBool',
                 self.GAME.INVITES_FROM_FRIENDS: 'readBool',
                 self.GAME.STORE_RECEIVER_IN_BATTLE: 'readBool'}
                for key, reader in _userProps.iteritems():
                    if key in tags:
                        gameData[key] = getattr(subSec, reader)(key)

            try:
                gameData[self.GAME.REPLAY_ENABLED] = section['replayPrefs'].readBool('enabled', False)
            except:
                LOG_DEBUG('Replay preferences is not available.')

            gameData[self.GAME.ENABLE_SERVER_AIM] = AccountSettings.getSettings('useServerAim')
            gameData[self.GAME.SHOW_VEHICLES_COUNTER] = AccountSettings.getSettings('showVehiclesCounter')
            gameData[self.GAME.MINIMAP_ALPHA] = AccountSettings.getSettings('minimapAlpha')
            gameData[self.GAME.PLAYERS_PANELS_SHOW_LEVELS] = AccountSettings.getSettings('players_panel')['showLevels']
            gameData[self.GAME.GAMEPLAY_MASK] = AccountSettings.getSettings('gameplayMask')
            arcade = AccountSettings.getSettings('arcade')
            sniper = AccountSettings.getSettings('sniper')
            markersData = AccountSettings.getSettings('markers')
            aimData['arcade'] = self._core.options.getSetting('arcade').fromAccountSettings(arcade)
            aimData['sniper'] = self._core.options.getSetting('sniper').fromAccountSettings(sniper)
            from post_processing import g_postProcessing
            gameData[self.GAME.ENABLE_POSTMORTEM] = g_postProcessing.getSetting('mortem_post_effect')
            if section.has_key(Settings.KEY_CONTROL_MODE):
                ds = section[Settings.KEY_CONTROL_MODE]
                try:
                    controlsData[self.CONTROLS.MOUSE_HORZ_INVERSION] = ds['arcadeMode'].readBool('horzInvert', False)
                    controlsData[self.CONTROLS.MOUSE_VERT_INVERSION] = ds['arcadeMode'].readBool('vertInvert', False)
                    controlsData[self.CONTROLS.MOUSE_VERT_INVERSION] = ds['arcadeMode'].readBool('backDraftInvert', False)
                except:
                    LOG_DEBUG('Controls preferences is not available.')

            keyboardData = self._core.options.getSetting('keyboard').getCurrentMapping()
        return (gameData,
         controlsData,
         aimData,
         markersData,
         keyboardData)

    def _setSettingsSections(self, gameData, controlsData, aimData, markersData, keyboardData):
        settings = {}
        if gameData:
            settings[SETTINGS_SECTIONS.GAME] = self._buildSectionSettings(SETTINGS_SECTIONS.GAME, gameData)
        if controlsData:
            settings[SETTINGS_SECTIONS.CONTROLS] = self._buildSectionSettings(SETTINGS_SECTIONS.CONTROLS, controlsData)
        if aimData:
            settings.update(self._buildAimSettings(aimData))
        if markersData:
            settings.update(self._buildMarkersSettings(markersData))
        if keyboardData:
            settings.update(keyboardData)
        if settings:
            self.setSettings(settings)
# okay decompyling res/scripts/client/account_helpers/serversettingsmanager.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:25:11 EST

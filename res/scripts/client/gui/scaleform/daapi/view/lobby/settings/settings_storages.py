import BigWorld
from gui.shared.utils.graphics import g_monitorSettings
from messenger import g_settings as messenger_settings

class ISettingsStorage(object):

    def __init__(self, manager = None):
        self._manager = manager
        self._settings = {}

    def store(self, setting):
        settingOption = setting['option']
        settingValue = setting['value']
        self._settings[settingOption] = settingValue

    def extract(self, settingOption, default = None):
        return self._settings.get(settingOption, default)

    def apply(self):
        raise NotImplementedError

    def clear(self):
        self._settings.clear()


class VideoSettingsStorage(ISettingsStorage):

    @property
    def fullscreen(self):
        return self._settings.get('isFullscreen', g_monitorSettings.isFullscreen)

    @fullscreen.setter
    def fullscreen(self, value):
        self.store({'option': 'isFullscreen',
         'value': value})

    @property
    def videoMode(self):
        return self._settings.get('videoMode', g_monitorSettings.currentVideoMode)

    @videoMode.setter
    def videoMode(self, value):
        self.store({'option': 'videoMode',
         'value': value})

    def apply(self):
        cvm = g_monitorSettings.currentVideoMode
        isFullscreen = self.fullscreen
        videoMode = self.videoMode
        if not g_monitorSettings.isMonitorChanged and cvm is not None and (videoMode.index != cvm.index or isFullscreen != g_monitorSettings.isFullscreen):
            BigWorld.changeVideoMode(videoMode.index, not isFullscreen)
        return


class GameSettingsStorage(ISettingsStorage):

    def apply(self):
        if self._settings:
            self._manager.setGameSettings(self._settings)

    def extract(self, settingOption, default = None):
        default = self._manager.getGameSetting(settingOption, default)
        return self._settings.get(settingOption, default)


class MessengerSettingsStorage(object):

    def __init__(self, proxy = None):
        self._proxy = proxy
        self._settings = {}

    def store(self, setting):
        settingOption = setting['option']
        settingValue = setting['value']
        self._settings[settingOption] = settingValue
        self._proxy.store(setting)

    def extract(self, settingOption, default = None):
        return self._proxy.extract(settingOption, default)

    def apply(self):
        messenger_settings.saveUserPreferences(self._settings)

    def clear(self):
        self._settings.clear()


class GraphicsSettingsStorage(ISettingsStorage):

    def apply(self):
        if self._settings:
            self._manager.setGraphicsSettings(self._settings)

    def extract(self, settingOption, default = None):
        default = self._manager.getGraphicsSetting(settingOption, default)
        return self._settings.get(settingOption, default)


class SoundSettingsStorage(ISettingsStorage):

    def apply(self):
        if self._settings:
            self._manager.setSoundSettings(self._settings)

    def extract(self, settingOption, default = None):
        default = self._manager.getSoundSetting(settingOption, default)
        return self._settings.get(settingOption, default)


class KeyboardSettingsStorage(ISettingsStorage):

    def apply(self):
        if self._settings:
            self._manager.setSettings(self._settings)

    def extract(self, settingOption, default = None):
        default = self._manager.getSetting(settingOption, default)
        return self._settings.get(settingOption, default)


class ControlsSettingsStorage(ISettingsStorage):

    def apply(self):
        if self._settings:
            self._manager.setControlsSettings(self._settings)

    def extract(self, settingOption, default = None):
        default = self._manager.getControlsSetting(settingOption, default)
        return self._settings.get(settingOption, default)


class AimSettingsStorage(ISettingsStorage):

    def apply(self):
        if self._settings:
            self._manager.setAimSettings(self._settings)

    def extract(self, settingOption, key = None, default = None):
        default = self._manager.getAimSetting(settingOption, key, default)
        return self._settings.get(settingOption, {}).get(key, default)


class MarkersSettingsStorage(ISettingsStorage):

    def apply(self):
        if self._settings:
            self._manager.setMarkersSettings(self._settings)

    def extract(self, settingOption, key = None, default = None):
        default = self._manager.getMarkersSetting(settingOption, key, default)
        return self._settings.get(settingOption, {}).get(key, default)

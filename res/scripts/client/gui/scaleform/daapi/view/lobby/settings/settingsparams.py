import BigWorld
from account_helpers.SettingsCore import g_settingsCore
from gui.Scaleform.daapi.view.lobby.settings import constants
from gui.shared.utils import graphics
from gui.shared.utils.graphics import g_monitorSettings
from gui.Scaleform.daapi import AppRef
from gui.Scaleform.daapi.view.lobby.settings import options
_DEFERRED_RENDER_IDX = 0

class SettingsParams(AppRef):

    def __init__(self):
        super(SettingsParams, self).__init__()
        self.SETTINGS = g_settingsCore.options

    def __settingsDiffPreprocessing(self, diff):
        if constants.GRAPHICS.SMOOTHING in diff:
            rppSetting = graphics.GRAPHICS_SETTINGS.RENDER_PIPELINE
            renderOptions = graphics.getGraphicsSetting(rppSetting)
            isAdvancedRender = renderOptions.value == _DEFERRED_RENDER_IDX
            if rppSetting in diff:
                isAdvancedRender = diff[rppSetting] == _DEFERRED_RENDER_IDX
            if isAdvancedRender:
                diff[constants.GRAPHICS.CUSTOM_AA] = diff[constants.GRAPHICS.SMOOTHING]
            else:
                diff[constants.GRAPHICS.MULTISAMPLING] = diff[constants.GRAPHICS.SMOOTHING]
        return diff

    def getGameSettings(self):
        return self.SETTINGS.pack(constants.GAME.ALL())

    def getSoundSettings(self):
        return self.SETTINGS.pack(constants.SOUND.ALL())

    def getGraphicsSettings(self):
        return self.SETTINGS.pack(constants.GRAPHICS.ALL())

    def getMarkersSettings(self):
        return self.SETTINGS.pack(constants.MARKERS.ALL())

    def getAimSettings(self):
        return self.SETTINGS.pack(constants.AIM.ALL())

    def getControlsSettings(self):
        return self.SETTINGS.pack(constants.CONTROLS.ALL())

    def getMonitorSettings(self):
        return self.SETTINGS.pack((constants.GRAPHICS.MONITOR,
         constants.GRAPHICS.FULLSCREEN,
         constants.GRAPHICS.WINDOW_SIZE,
         constants.GRAPHICS.RESOLUTION))

    def preview(self, settingName, value):
        setting = self.SETTINGS.getSetting(settingName)
        if setting is not None:
            setting.preview(value)
        return

    def revert(self):
        self.SETTINGS.revert()
        g_settingsCore.clearStorages()

    def apply(self, diff):
        diff = self.__settingsDiffPreprocessing(diff)
        applyMethod = self.SETTINGS.apply(diff)
        g_settingsCore.applyStorages()
        if len(set(graphics.GRAPHICS_SETTINGS.ALL()) & set(diff.keys())):
            BigWorld.commitPendingGraphicsSettings()
        return options.APPLY_METHOD.RESTART in applyMethod

    def getApplyMethod(self, diff):
        newMonitorIndex = diff.get(constants.GRAPHICS.MONITOR)
        if not g_monitorSettings.isFullscreen:
            isFullscreen = diff.get(constants.GRAPHICS.FULLSCREEN)
            isMonitorChanged = g_monitorSettings.isMonitorChanged or newMonitorIndex is not None and g_monitorSettings.currentMonitor != newMonitorIndex
            return isFullscreen and isMonitorChanged and options.APPLY_METHOD.RESTART
        else:
            return self.SETTINGS.getApplyMethod(diff.keys())

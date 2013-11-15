# 2013.11.15 11:26:15 EST
# Embedded file name: scripts/client/gui/Scaleform/daapi/view/lobby/settings/SettingsWindow.py
import functools
import BigWorld
import VOIP
import SoundGroups
from adisp import process
from debug_utils import *
from Vibroeffects import VibroManager
from gui import DialogsInterface, g_guiResetters
from gui.BattleContext import g_battleContext
from gui.Scaleform.daapi.view.lobby.settings import constants
from gui.shared.utils import flashObject2Dict
from gui.Scaleform.daapi import AppRef
from gui.Scaleform.Waiting import Waiting
from gui.Scaleform.framework.entities.View import View
from gui.Scaleform.daapi.view.meta.WindowViewMeta import WindowViewMeta
from gui.Scaleform.daapi.view.meta.SettingsWindowMeta import SettingsWindowMeta
from gui.Scaleform.daapi.view.lobby.settings.SettingsParams import SettingsParams
from gui.Scaleform.daapi.view.lobby.settings.options import APPLY_METHOD

class SettingsWindow(View, WindowViewMeta, SettingsWindowMeta, AppRef):

    def __init__(self, ctx):
        super(SettingsWindow, self).__init__()
        self.__redefinedKeyModeEnabled = ctx.get('redefinedKeyMode', True)
        self.params = SettingsParams()

    def __getSettings(self):
        return {'GameSettings': self.params.getGameSettings(),
         'GraphicSettings': self.params.getGraphicsSettings(),
         'SoundSettings': self.params.getSoundSettings(),
         'ControlsSettings': self.params.getControlsSettings(),
         'AimSettings': self.params.getAimSettings(),
         'MarkerSettings': self.params.getMarkersSettings()}

    def __commitSettings(self, settings = None, restartApproved = False):
        if settings is None:
            settings = {}
        self.__apply(settings, restartApproved)
        return

    def __apply(self, settings, restartApproved = False):
        LOG_DEBUG('Settings window: apply settings', restartApproved, settings)
        isRestart = self.params.apply(settings)
        if isRestart:
            BigWorld.savePreferences()
            if restartApproved:
                BigWorld.callback(0.3, BigWorld.restartGame)
            else:
                BigWorld.callback(0.0, functools.partial(BigWorld.changeVideoMode, -1, BigWorld.isVideoWindowed()))

    def _populate(self):
        super(SettingsWindow, self)._populate()
        self.__currentSettings = self.params.getMonitorSettings()
        self.app.voiceChatManager.checkForInitialization()
        self.as_setDataS(self.__getSettings())
        self.as_updateVideoSettingsS(self.__currentSettings)
        VibroManager.g_instance.onConnect += self.onVibroManagerConnect
        VibroManager.g_instance.onDisconnect += self.onVibroManagerDisconnect
        g_guiResetters.add(self.onRecreateDevice)
        BigWorld.wg_setAdapterOrdinalNotifyCallback(self.onRecreateDevice)
        SoundGroups.g_instance.enableVoiceSounds(True)

    def _dispose(self):
        if not g_battleContext.isInBattle:
            SoundGroups.g_instance.enableVoiceSounds(False)
        g_guiResetters.discard(self.onRecreateDevice)
        BigWorld.wg_setAdapterOrdinalNotifyCallback(None)
        VibroManager.g_instance.onConnect -= self.onVibroManagerConnect
        VibroManager.g_instance.onDisconnect -= self.onVibroManagerDisconnect
        super(SettingsWindow, self)._dispose()
        return

    def onVibroManagerConnect(self):
        self.as_onVibroManagerConnectS(True)

    def onVibroManagerDisconnect(self):
        self.as_onVibroManagerConnectS(False)

    def onSettingsChange(self, settingName, settingValue):
        settingValue = flashObject2Dict(settingValue)
        self.params.preview(settingName, settingValue)

    def applySettings(self, settings, isCloseWnd):
        settings = flashObject2Dict(settings)
        applyMethod = self.params.getApplyMethod(settings)

        def confirmHandler(isOk):
            self.__commitSettings(settings, isOk)
            if isOk and isCloseWnd:
                self.closeWindow()

        if applyMethod == APPLY_METHOD.RESTART:
            DialogsInterface.showI18nConfirmDialog('graphicsPresetRestartConfirmation', confirmHandler)
        elif applyMethod == APPLY_METHOD.DELAYED:
            DialogsInterface.showI18nConfirmDialog('graphicsPresetDelayedConfirmation', confirmHandler)
        else:
            confirmHandler(True)

    def closeWindow(self):
        self.params.revert()
        self.startVOIPTest(False)
        self.destroy()

    def onRecreateDevice(self):
        if self.__currentSettings and self.__currentSettings != self.params.getMonitorSettings():
            self.__currentSettings = self.params.getMonitorSettings()
            self.as_updateVideoSettingsS(self.__currentSettings)

    def useRedifineKeysMode(self, isUse):
        if self.__redefinedKeyModeEnabled:
            BigWorld.wg_setRedefineKeysMode(isUse)

    def autodetectQuality(self):
        return BigWorld.autoDetectGraphicsSettings()

    def startVOIPTest(self, isStart):
        LOG_DEBUG('Vivox test:', isStart)
        rh = VOIP.getVOIPManager()
        rh.enterTestChannel() if isStart else rh.leaveTestChannel()
        return False

    @process
    def updateCaptureDevices(self):
        Waiting.show('__updateCaptureDevices')
        devices = yield self.app.voiceChatManager.requestCaptureDevices()
        currentCaptureDeviceIdx = -1
        if VOIP.getVOIPManager().currentCaptureDevice in devices:
            currentCaptureDeviceIdx = devices.index(VOIP.getVOIPManager().currentCaptureDevice)
        value = [ d.decode(sys.getfilesystemencoding()).encode('utf-8') for d in devices ]
        Waiting.hide('__updateCaptureDevices')
        self.as_setCaptureDevicesS(currentCaptureDeviceIdx, value)

    def altVoicesPreview(self):
        setting = self.params.SETTINGS.getSetting(constants.SOUND.ALT_VOICES)
        if setting is not None:
            setting.playPreviewSound()
        return

    def isSoundModeValid(self):
        setting = self.params.SETTINGS.getSetting(constants.SOUND.ALT_VOICES)
        if setting is not None:
            return setting.isSoundModeValid()
        else:
            return False

    def showWarningDialog(self, dialogID, settings, isCloseWnd):

        def callback(isOk):
            if isOk:
                self.applySettings(settings, False)
            self.as_confirmWarningDialogS(isOk, dialogID)
            if isCloseWnd and isOk:
                self.closeWindow()

        DialogsInterface.showI18nConfirmDialog(dialogID, callback)
# okay decompyling res/scripts/client/gui/scaleform/daapi/view/lobby/settings/settingswindow.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:26:16 EST

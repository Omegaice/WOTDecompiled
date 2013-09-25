from adisp import process
from gui import DialogsInterface
from gui.shared import events, g_eventBus, EVENT_BUS_SCOPE
from gui.Scaleform.framework import AppRef
from gui.Scaleform.framework.entities.View import View
from gui.Scaleform.daapi.view.meta.LobbyMenuMeta import LobbyMenuMeta
from gui.Scaleform.daapi.view.meta.WindowViewMeta import WindowViewMeta

class LobbyMenu(View, LobbyMenuMeta, WindowViewMeta, AppRef):

    def settingsClick(self):
        self.fireEvent(events.ShowWindowEvent(events.ShowWindowEvent.SHOW_SETTINGS_WINDOW, {'redefinedKeyMode': False}))

    def onWindowClose(self):
        self.destroy()

    def cancelClick(self):
        self.destroy()

    @process
    def refuseTraining(self):
        isOk = yield DialogsInterface.showI18nConfirmDialog('refuseTraining')
        if isOk:
            g_eventBus.handleEvent(events.TutorialEvent(events.TutorialEvent.REFUSE), scope=EVENT_BUS_SCOPE.GLOBAL)
        self.destroy()

    @process
    def logoffClick(self):
        isOk = yield DialogsInterface.showI18nConfirmDialog('disconnect', focusedID=DialogsInterface.DIALOG_BUTTON_ID.CLOSE)
        if isOk:
            self.destroy()
            self.app.logoff()

    @process
    def quitClick(self):
        isOk = yield DialogsInterface.showI18nConfirmDialog('quit', focusedID=DialogsInterface.DIALOG_BUTTON_ID.CLOSE)
        if isOk:
            self.destroy()
            self.app.quit()

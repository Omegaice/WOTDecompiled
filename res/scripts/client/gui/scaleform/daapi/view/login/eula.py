import BigWorld
import ResMgr
from gui import DialogsInterface
from gui.Scaleform.daapi.view.meta.EULAMeta import EULAMeta
from gui.Scaleform.daapi.view.meta.WindowViewMeta import WindowViewMeta
from gui.Scaleform.framework.entities.View import View
from gui.shared.events import CloseWindowEvent

class EULADlg(View, EULAMeta, WindowViewMeta):

    def __init__(self, ctx):
        super(EULADlg, self).__init__()
        self.__applied = False
        self.__eulaString = ctx.get('text', '')

    def _dispose(self):
        super(EULADlg, self)._dispose()
        self.__eulaString = None
        return

    def onWindowClose(self):
        if not self.__applied:
            DialogsInterface.showI18nConfirmDialog('quit', self.__onConfirmClosed, focusedID=DialogsInterface.DIALOG_BUTTON_ID.CLOSE)
        else:
            self.destroy()

    def requestEULAText(self):
        self.as_setEULATextS(self.__eulaString)

    def onApply(self):
        self.__applied = True
        self.__fireEulaClose()
        self.onWindowClose()

    def onLinkClick(self, url):
        BigWorld.wg_openWebBrowser(url)

    def __onQuitOk(self):
        self.__fireEulaClose()
        self.destroy()
        BigWorld.quit()

    def __fireEulaClose(self):
        self.fireEvent(CloseWindowEvent(CloseWindowEvent.EULA_CLOSED, self.__applied))

    def __onConfirmClosed(self, isOk):
        if isOk:
            self.__onQuitOk()

from debug_utils import LOG_DEBUG
from gui.Scaleform.daapi.view.meta.EliteWindowMeta import EliteWindowMeta
from gui.Scaleform.daapi.view.meta.WindowViewMeta import WindowViewMeta
from gui.Scaleform.framework.entities.View import View

class EliteWindow(View, EliteWindowMeta, WindowViewMeta):

    def __init__(self, ctx):
        super(EliteWindow, self).__init__()
        self.vehInvID = ctx['vehTypeCompDescr']

    def _populate(self):
        super(WindowViewMeta, self)._populate()
        self.as_setVehTypeCompDescrS(self.vehInvID)

    def onWindowClose(self):
        self.destroy()

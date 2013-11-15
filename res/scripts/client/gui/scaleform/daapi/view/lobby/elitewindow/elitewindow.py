# 2013.11.15 11:26:01 EST
# Embedded file name: scripts/client/gui/Scaleform/daapi/view/lobby/eliteWindow/EliteWindow.py
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
# okay decompyling res/scripts/client/gui/scaleform/daapi/view/lobby/elitewindow/elitewindow.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:26:01 EST

# 2013.11.15 11:25:45 EST
# Embedded file name: scripts/client/gui/prb_control/prb_helpers.py
from gui.prb_control.dispatcher import g_prbLoader
from gui.prb_control.functional.interfaces import IPrbListener, IUnitListener
from gui.prb_control.functional.interfaces import IGlobalListener

class prbDispatcherProperty(property):

    def __get__(self, obj, objType = None):
        return g_prbLoader.getDispatcher()


class prbInvitesProperty(property):

    def __get__(self, obj, objType = None):
        return g_prbLoader.getInvitesManager()


class prbFunctionalProperty(property):

    def __get__(self, obj, objType = None):
        dispatcher = g_prbLoader.getDispatcher()
        functional = None
        if dispatcher is not None:
            functional = dispatcher.getPrbFunctional()
        return functional


class unitFunctionalProperty(property):

    def __get__(self, obj, objType = None):
        dispatcher = g_prbLoader.getDispatcher()
        functional = None
        if dispatcher is not None:
            functional = dispatcher.getUnitFunctional()
        return functional


class PrbListener(IPrbListener):

    @prbDispatcherProperty
    def prbDispatcher(self):
        return None

    @prbFunctionalProperty
    def prbFunctional(self):
        return None

    def startPrbListening(self):
        dispatcher = self.prbDispatcher
        if dispatcher:
            dispatcher.getPrbFunctional().addListener(self)

    def stopPrbListening(self):
        dispatcher = self.prbDispatcher
        if dispatcher:
            dispatcher.getPrbFunctional().removeListener(self)


class UnitListener(IUnitListener):

    @prbDispatcherProperty
    def prbDispatcher(self):
        return None

    @unitFunctionalProperty
    def unitFunctional(self):
        return None

    def startUnitListening(self):
        dispatcher = self.prbDispatcher
        if dispatcher:
            dispatcher.getUnitFunctional().addListener(self)

    def stopUnitListening(self):
        dispatcher = self.prbDispatcher
        if dispatcher:
            dispatcher.getUnitFunctional().removeListener(self)


class GlobalListener(IGlobalListener):

    @prbDispatcherProperty
    def prbDispatcher(self):
        return None

    @prbFunctionalProperty
    def prbFunctional(self):
        return None

    @unitFunctionalProperty
    def unitFunctional(self):
        return None

    def startGlobalListening(self):
        if self.prbDispatcher:
            self.prbDispatcher.addGlobalListener(self)

    def stopGlobalListening(self):
        if self.prbDispatcher:
            self.prbDispatcher.removeGlobalListener(self)
# okay decompyling res/scripts/client/gui/prb_control/prb_helpers.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:25:45 EST

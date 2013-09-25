# Embedded file name: scripts/client/gui/prb_control/prb_helpers.py
from adisp import process
from gui.shared.utils.functions import checkAmmoLevel
from gui.prb_control.functional.interfaces import IPrbListener

class prbDispatcherProperty(property):
    __prb_dispatcher_property__ = True


class prbFunctionalProperty(property):
    __prb_functional_property__ = True


class prbInvitesProperty(property):
    __prb_invites_property__ = True


class InjectPrebattle(type):

    def __new__(mcls, name, bases, namespace):
        cls = super(InjectPrebattle, mcls).__new__(mcls, name, bases, namespace)

        def getDispatcher(_):
            from gui.prb_control.dispatcher import g_prbLoader
            return g_prbLoader.getDispatcher()

        def getInvitesManager(_):
            from gui.prb_control.dispatcher import g_prbLoader
            return g_prbLoader.getInvitesManager()

        def getFunctional(_):
            from gui.prb_control.dispatcher import g_prbLoader
            dispatcher = g_prbLoader.getDispatcher()
            functional = None
            if dispatcher is not None:
                functional = dispatcher.getPrbFunctional()
            return functional

        for name, value in namespace.items():
            if getattr(value, '__prb_dispatcher_property__', False):
                setattr(cls, name, property(getDispatcher))
            if getattr(value, '__prb_functional_property__', False):
                setattr(cls, name, property(getFunctional))
            if getattr(value, '__prb_invites_property__', False):
                setattr(cls, name, property(getInvitesManager))

        return cls


class PrbListener(IPrbListener):
    __metaclass__ = InjectPrebattle

    @prbDispatcherProperty
    def prbDispatcher(self):
        pass

    @prbFunctionalProperty
    def prbFunctional(self):
        pass

    def startPrbListening(self):
        dispatcher = self.prbDispatcher
        if dispatcher:
            dispatcher.getPrbFunctional().addListener(self)

    def stopPrbListening(self):
        dispatcher = self.prbDispatcher
        if dispatcher:
            dispatcher.getPrbFunctional().removeListener(self)

    def startPrbGlobalListening(self):
        if self.prbDispatcher:
            self.prbDispatcher.addGlobalListener(self)

    def stopPrbGlobalListening(self):
        if self.prbDispatcher:
            self.prbDispatcher.removeGlobalListener(self)


def vehicleAmmoCheck(func):

    @process
    def wrapper(*args, **kwargs):
        res = yield checkAmmoLevel()
        if res:
            func(*args, **kwargs)

    return wrapper
import BigWorld
from constants import PREBATTLE_TYPE_NAMES
from debug_utils import LOG_ERROR
from gui.prb_control.functional.interfaces import IPrbEntry, IPrbFunctional

class NotSupportedEntry(IPrbEntry):

    def doAction(self, action, dispatcher = None):
        LOG_ERROR('NotSupportedEntry.doAction')

    def create(self, ctx, callback = None):
        LOG_ERROR('NotSupportedEntry.create')

    def join(self, ctx, callback = None):
        LOG_ERROR('NotSupportedEntry.join')


class PrbNotSupportedFunctional(IPrbFunctional):

    def __init__(self, settings):
        super(PrbNotSupportedFunctional, self).__init__()
        try:
            self._prbTypeName = PREBATTLE_TYPE_NAMES[settings['type']]
        except KeyError:
            self._prbTypeName = 'N/A'

    def init(self, clientPrb = None, ctx = None):
        LOG_ERROR('PrbNotSupportedFunctional.init. Prebattle is not supported', self._prbTypeName)

    def fini(self, clientPrb = None, woEvents = False):
        pass

    def canPlayerDoAction(self):
        LOG_ERROR('Actions are disabled. Prebattle is not supported', self._prbTypeName)
        return (True, '')

    def doAction(self, action = None, dispatcher = None):
        LOG_ERROR('Leaves prebattle. Prebattle is not supported', self._prbTypeName)
        BigWorld.player().prb_leave(lambda result: result)
        return True

    def hasGUIPage(self):
        LOG_ERROR('PrbNotSupportedFunctional.showGUI. Prebattle is not supported', self._prbTypeName)
        return False

    def isConfirmToChange(self):
        LOG_ERROR('PrbNotSupportedFunctional.isConfirmToChange. Prebattle is not supported', self._prbTypeName)
        return False

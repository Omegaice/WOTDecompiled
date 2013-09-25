from CurrentVehicle import g_currentVehicle
from constants import PREBATTLE_TYPE
from debug_utils import LOG_ERROR
from gui import SystemMessages
from gui.Scaleform.locale.MENU import MENU
from gui.prb_control.functional.interfaces import IPrbFunctional
from gui.prb_control.settings import PREBATTLE_ACTION_NAME

class NoPrbFunctional(IPrbFunctional):
    CREATE_PRB_BY_ACTION = {PREBATTLE_ACTION_NAME.SQUAD: PREBATTLE_TYPE.SQUAD}

    def canPlayerDoAction(self):
        return (True, '')

    def doAction(self, action = None, dispatcher = None):
        result = False
        if not g_currentVehicle.isLocked() and not g_currentVehicle.isBroken():
            if action is not None:
                actionName = action.actionName
                if actionName in self.CREATE_PRB_BY_ACTION:
                    from gui.prb_control.functional import createPrbEntry
                    entry = createPrbEntry(self.CREATE_PRB_BY_ACTION[actionName])
                    result = entry.doAction(action, dispatcher)
        else:
            result = True
            SystemMessages.pushI18nMessage(MENU.HANGAR_VEHICLE_LOCKED, type=SystemMessages.SM_TYPE.Error)
        return result

    def leave(self, ctx, callback = None):
        LOG_ERROR('NoPrbFunctional.leave was invoke', ctx)
        if callback:
            callback(False)

    def request(self, ctx, callback = None):
        LOG_ERROR('NoPrbFunctional.request was invoke', ctx)
        if callback:
            callback(False)

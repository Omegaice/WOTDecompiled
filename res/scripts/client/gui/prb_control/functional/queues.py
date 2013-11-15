# 2013.11.15 11:25:42 EST
# Embedded file name: scripts/client/gui/prb_control/functional/queues.py
import BigWorld
import ArenaType
from CurrentVehicle import g_currentVehicle
from account_helpers import gameplay_ctx
from adisp import process
from debug_utils import LOG_DEBUG, LOG_ERROR
from gui.prb_control import events_dispatcher, isParentControlActivated
from gui.prb_control.functional.interfaces import IQueueFunctional
from gui.prb_control.settings import PREBATTLE_ACTION_NAME
from gui.shared.utils.functions import checkAmmoLevel

class JoinRandomFunctional(IQueueFunctional):

    def canPlayerDoAction(self):
        return True

    def doAction(self, action = None, dispatcher = None):
        result = False
        if action is None or action.actionName == PREBATTLE_ACTION_NAME.JOIN_RANDOM_QUEUE or action.actionName == PREBATTLE_ACTION_NAME.UNDEFINED:
            if isParentControlActivated():
                events_dispatcher.showParentControlNotification()
            else:
                self.__doJoin(action=action)
                result = True
        return result

    def onChanged(self):
        events_dispatcher.loadHangar()

    @process
    def __doJoin(self, action = None):
        if not hasattr(BigWorld.player(), 'enqueueRandom'):
            LOG_ERROR('Player has not method enqueueRandom', BigWorld.player())
            yield lambda callback = None: callback
        mapID = 0
        if action and action.mapID:
            mapID = action.mapID
            LOG_DEBUG('Demonstrator mapID:', ArenaType.g_cache[mapID].geometryName)
        result = yield checkAmmoLevel()
        if result:
            gameplayMask = gameplay_ctx.getMask()
            invID = g_currentVehicle.invID
            BigWorld.player().enqueueRandom(invID, gameplaysMask=gameplayMask, arenaTypeID=mapID)
            LOG_DEBUG('Player joined to enqueue (invID, gameplayMask, mapID) =', invID, gameplayMask, mapID)
        return


class LeaveRandomFunctional(IQueueFunctional):

    def canPlayerDoAction(self):
        return False

    def doAction(self, action = None, dispatcher = None):
        if hasattr(BigWorld.player(), 'dequeueRandom'):
            BigWorld.player().dequeueRandom()
        return True

    def onChanged(self):
        events_dispatcher.loadBattleQueue()
# okay decompyling res/scripts/client/gui/prb_control/functional/queues.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:25:42 EST

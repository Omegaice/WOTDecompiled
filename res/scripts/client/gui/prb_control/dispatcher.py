import weakref
from CurrentVehicle import g_currentVehicle
from adisp import async, process
from constants import PREBATTLE_TYPE
from debug_utils import LOG_ERROR, LOG_DEBUG
from gui import SystemMessages, DialogsInterface, GUI_SETTINGS, game_control
from gui.prb_control import functional, events_dispatcher, getClientPrebattle
from gui.prb_control.functional.battle_session import AutoInvitesNotifier
from gui.prb_control.invites import InvitesManager
from gui.prb_control.formatters import messages
from gui.prb_control.functional.interfaces import IPrbListener
from gui.prb_control import context, areSpecBattlesHidden, isParentControlActivated
from gui.prb_control.settings import PREBATTLE_ACTION_NAME, PREBATTLE_RESTRICTION
from PlayerEvents import g_playerEvents

class _PrebattleDispatcher(object):
    OPEN_PRB_LIST_BY_ACTION = {PREBATTLE_ACTION_NAME.TRAINING_LIST: PREBATTLE_TYPE.TRAINING,
     PREBATTLE_ACTION_NAME.COMPANY_LIST: PREBATTLE_TYPE.COMPANY,
     PREBATTLE_ACTION_NAME.SPEC_BATTLE_LIST: PREBATTLE_TYPE.CLAN}

    def __init__(self):
        super(_PrebattleDispatcher, self).__init__()
        self.__prbCtx = None
        self.__prbFunctional = None
        self.__queueFunctional = None
        self._globalListeners = set()
        return

    def start(self, ctx):
        self.__prbCtx = context._PrbEntryCtx()
        self.__prbFunctional = functional.createPrbFunctional(self)
        self.__prbFunctional.init()
        self.__queueFunctional = functional.createQueueFunctional(isInRandomQueue=ctx.isInRandomQueue)
        self._startListening()
        functional.initDevFunctional()
        if not self.__prbFunctional.hasGUIPage():
            self.__queueFunctional.onChanged()
        events_dispatcher.updateUI()
        events_dispatcher.addCompaniesToCarousel()
        if GUI_SETTINGS.specPrebatlesVisible and not areSpecBattlesHidden():
            events_dispatcher.addSpecBattlesToCarousel()

    def stop(self):
        self._stopListening()
        functional.finiDevFunctional()
        self._clear(woEvents=True)

    def getPrbFunctional(self):
        return self.__prbFunctional

    def getQueueFunctional(self):
        return self.__queueFunctional

    @async
    @process
    def create(self, ctx, callback = None):
        if not self.__prbCtx.isProcessing():
            result = True
            if self.__prbFunctional.isConfirmToChange():
                result = yield DialogsInterface.showDialog(self.__prbFunctional.getConfirmDialogMeta())
                if result:
                    result = yield self.leave(context.LeavePrbCtx(waitingID='prebattle/leave'))
                    ctx.setForced(result)
                elif callback:
                    callback(False)
            if result:
                LOG_DEBUG('Request to create prebattle', ctx)
                self.__prbCtx = ctx
                entry = functional.createPrbEntry(ctx.getPrbType())
                entry.create(ctx, callback=callback)
        else:
            LOG_ERROR('Prebattle request is processing', self.__prbCtx)
            if callback:
                callback(False)
        yield lambda callback = None: callback
        return

    @async
    @process
    def join(self, ctx, callback = None):
        if not self.__prbCtx.isProcessing():
            if self.__prbFunctional.getID() == ctx.getID():
                LOG_DEBUG('Player already joined to prebattle', self.__prbFunctional.getID(), self.__prbFunctional.getPrbTypeName())
                self.__prbFunctional.showGUI()
                if callback:
                    callback(False)
            else:
                result = True
                if self.__prbFunctional.isConfirmToChange():
                    result = yield DialogsInterface.showDialog(self.__prbFunctional.getConfirmDialogMeta())
                    if result:
                        result = yield self.leave(context.LeavePrbCtx(waitingID='prebattle/leave'))
                        ctx.setForced(result)
                    elif callback:
                        callback(False)
                if result:
                    LOG_DEBUG('Request to join prebattle', ctx)
                    if callback:
                        self.__prbCtx = ctx
                    entry = functional.createPrbEntry(ctx.getPrbType())
                    entry.join(ctx, callback=callback)
                else:
                    callback(False)
        else:
            LOG_ERROR('Prebattle request is processing', self.__prbCtx)
            if callback:
                callback(False)
        yield lambda callback = None: callback
        return

    @async
    def leave(self, ctx, callback = None):
        if self.__prbCtx.isProcessing():
            LOG_ERROR('Prebattle request is processing', self.__prbCtx)
            callback(False)
            return
        LOG_DEBUG('Request to leave prebattle', ctx)
        self.__prbCtx = ctx
        self.__prbFunctional.leave(ctx, callback=callback)

    @async
    def sendPrbRequest(self, ctx, callback = None):
        self.__prbFunctional.request(ctx, callback=callback)

    def exitFromRandomQueue(self):
        if not self.__prbFunctional.exitFromRandomQueue():
            self.__queueFunctional.doAction()

    def canPlayerDoAction(self):
        canDo, restriction = True, ''
        if not self.__queueFunctional.canPlayerDoAction():
            canDo = False
        else:
            if not g_currentVehicle.isReadyToFight():
                if not g_currentVehicle.isPresent():
                    canDo = False
                    restriction = PREBATTLE_RESTRICTION.VEHICLE_NOT_PRESENT
                elif g_currentVehicle.isInBattle():
                    canDo = False
                    restriction = PREBATTLE_RESTRICTION.VEHICLE_IN_BATTLE
                elif not g_currentVehicle.isCrewFull():
                    canDo = False
                    restriction = PREBATTLE_RESTRICTION.CREW_NOT_FULL
                elif g_currentVehicle.isBroken():
                    canDo = False
                    restriction = PREBATTLE_RESTRICTION.VEHICLE_BROKEN
            if canDo:
                canDo, restriction = self.__prbFunctional.canPlayerDoAction()
        return (canDo, restriction)

    def doAction(self, action):
        if not g_currentVehicle.isPresent():
            SystemMessages.pushMessage(messages.getInvalidVehicleMessage(PREBATTLE_RESTRICTION.VEHICLE_NOT_PRESENT), type=SystemMessages.SM_TYPE.Error)
            return False
        LOG_DEBUG('Do prebattle action', action)
        actionName = action.actionName
        if actionName == PREBATTLE_ACTION_NAME.PREBATTLE_LEAVE:
            ctx = context.LeavePrbCtx(waitingID='prebattle/leave')
            if self._setPrbCtx(ctx):
                self.__prbFunctional.leave(self.__prbCtx)
                result = True
            else:
                result = False
        elif actionName in self.OPEN_PRB_LIST_BY_ACTION:
            entry = functional.createPrbEntry(self.OPEN_PRB_LIST_BY_ACTION[actionName])
            entry.doAction(action, dispatcher=self)
            result = True
        else:
            result = self.__prbFunctional.doAction(action=action, dispatcher=self)
            if not result:
                result = self.__queueFunctional.doAction(action)
        return result

    def addGlobalListener(self, listener):
        if isinstance(listener, IPrbListener):
            listenerRef = weakref.ref(listener)
            if listenerRef not in self._globalListeners:
                self._globalListeners.add(listenerRef)
                self.__prbFunctional.addListener(listener)
            else:
                LOG_ERROR('Listener already added', listener)
        else:
            LOG_ERROR('Object is not extend IPrbListener', listener)

    def removeGlobalListener(self, listener):
        listenerRef = weakref.ref(listener)
        if listenerRef in self._globalListeners:
            self._globalListeners.remove(listenerRef)
        else:
            LOG_ERROR('Listener not found', listener)
        self.__prbFunctional.removeListener(listener)

    def _startListening(self):
        """
        Subscribes to player events.
        """
        g_playerEvents.onEnqueuedRandom += self.pe_onEnqueuedRandom
        g_playerEvents.onDequeuedRandom += self.pe_onDequeuedRandom
        g_playerEvents.onEnqueueRandomFailure += self.pe_onEnqueueRandomFailure
        g_playerEvents.onKickedFromRandomQueue += self.pe_onKickedFromRandomQueue
        g_playerEvents.onPrebattleJoined += self.pe_onPrebattleJoined
        g_playerEvents.onPrebattleJoinFailure += self.pe_onPrebattleJoinFailure
        g_playerEvents.onPrebattleLeft += self.pe_onPrebattleLeft
        g_playerEvents.onKickedFromPrebattle += self.pe_onKickedFromPrebattle
        g_playerEvents.onArenaJoinFailure += self.pe_onArenaJoinFailure
        g_playerEvents.onKickedFromArena += self.pe_onKickedFromArena
        g_playerEvents.onPrebattleAutoInvitesChanged += self.pe_onPrebattleAutoInvitesChanged
        game_control.g_instance.gameSession.onTimeTillBan += self.gs_onTillBanNotification

    def _stopListening(self):
        """
        Unsubscribe from player events.
        """
        g_playerEvents.onEnqueuedRandom -= self.pe_onEnqueuedRandom
        g_playerEvents.onDequeuedRandom -= self.pe_onDequeuedRandom
        g_playerEvents.onEnqueueRandomFailure -= self.pe_onEnqueueRandomFailure
        g_playerEvents.onKickedFromRandomQueue -= self.pe_onKickedFromRandomQueue
        g_playerEvents.onPrebattleJoined -= self.pe_onPrebattleJoined
        g_playerEvents.onPrebattleJoinFailure -= self.pe_onPrebattleJoinFailure
        g_playerEvents.onPrebattleLeft -= self.pe_onPrebattleLeft
        g_playerEvents.onKickedFromPrebattle -= self.pe_onKickedFromPrebattle
        g_playerEvents.onArenaJoinFailure -= self.pe_onArenaJoinFailure
        g_playerEvents.onKickedFromArena -= self.pe_onKickedFromArena
        g_playerEvents.onPrebattleAutoInvitesChanged -= self.pe_onPrebattleAutoInvitesChanged
        game_control.g_instance.gameSession.onTimeTillBan -= self.gs_onTillBanNotification

    def _setPrbCtx(self, ctx):
        result = True
        if self.__prbCtx.isProcessing():
            LOG_ERROR('Prebattle request is processing', self.__prbCtx)
            result = False
        else:
            self.__prbCtx = ctx
        return result

    def _onPrbInited(self):
        self.__prbFunctional.fini()
        self.__prbCtx.stopProcessing(result=True)
        self.__prbFunctional = functional.createPrbFunctional(self)
        self.__prbFunctional.init(ctx=self.__prbCtx)
        events_dispatcher.updateUI()

    def _clear(self, woEvents = False):
        if self.__prbCtx:
            self.__prbCtx.clear()
            self.__prbCtx = None
        if self.__prbFunctional:
            self.__prbFunctional.fini(woEvents=woEvents)
            self.__prbFunctional = None
        events_dispatcher.removeSpecBattlesFromCarousel()
        self.__queueFunctional = None
        self._globalListeners.clear()
        return

    def pe_onEnqueuedRandom(self):
        self.__queueFunctional = functional.createQueueFunctional(isInRandomQueue=True)
        self.__queueFunctional.onChanged()
        events_dispatcher.updateUI()

    def pe_onDequeuedRandom(self):
        self.__queueFunctional = functional.createQueueFunctional(isInRandomQueue=False)
        self.__queueFunctional.onChanged()
        events_dispatcher.updateUI()

    def pe_onEnqueueRandomFailure(self, errorCode, _):
        SystemMessages.pushMessage(messages.getJoinFailureMessage(errorCode), type=SystemMessages.SM_TYPE.Error)

    def pe_onKickedFromRandomQueue(self):
        self.__queueFunctional = functional.createQueueFunctional(isInRandomQueue=False)
        self.__queueFunctional.onChanged()
        events_dispatcher.updateUI()
        SystemMessages.pushMessage(messages.getKickReasonMessage('timeout'), type=SystemMessages.SM_TYPE.Warning)

    def pe_onArenaJoinFailure(self, errorCode):
        SystemMessages.pushMessage(messages.getJoinFailureMessage(errorCode), type=SystemMessages.SM_TYPE.Error)

    def pe_onKickedFromArena(self, reasonCode):
        SystemMessages.pushMessage(messages.getKickReasonMessage(reasonCode), type=SystemMessages.SM_TYPE.Error)

    def pe_onPrebattleAutoInvitesChanged(self):
        if GUI_SETTINGS.specPrebatlesVisible:
            isHidden = areSpecBattlesHidden()
            if isHidden:
                events_dispatcher.removeSpecBattlesFromCarousel()
            else:
                events_dispatcher.addSpecBattlesToCarousel()
        events_dispatcher.updateUI()

    def pe_onPrebattleJoined(self):
        clientPrb = getClientPrebattle()
        if clientPrb:
            self.__prbFunctional.fini()
            self.__prbFunctional = functional.createPrbFunctional(self)
            self.__prbFunctional.init()
        else:
            LOG_ERROR('ClientPrebattle is not defined')
            self.__prbCtx.stopProcessing(result=False)

    def pe_onPrebattleJoinFailure(self, errorCode):
        SystemMessages.pushMessage(messages.getJoinFailureMessage(errorCode), type=SystemMessages.SM_TYPE.Error)
        self.__prbCtx.stopProcessing(result=False)
        events_dispatcher.updateUI()

    def pe_onPrebattleLeft(self):
        self.__prbFunctional.fini()
        self.__prbFunctional = functional.createPrbFunctional(self)
        self.__prbFunctional.init()
        events_dispatcher.updateUI()

    def pe_onKickedFromPrebattle(self, _):
        self.pe_onPrebattleLeft()

    def gs_onTillBanNotification(self, isPlayTimeBan, timeTillBlock):
        if isParentControlActivated():
            self.__prbFunctional.reset()
            key = '#system_messages:gameSessionControl/korea/{0:>s}'
            if isPlayTimeBan:
                SystemMessages.g_instance.pushI18nMessage(key.format('playTimeNotification'), timeTillBlock)
            else:
                SystemMessages.g_instance.pushI18nMessage(key.format('midnightNotification'))


class _PrbControlLoader(object):
    __slots__ = ('__prbDispatcher', '__invitesManager', '__autoNotifier', '__isEnabled')

    def __init__(self):
        super(_PrbControlLoader, self).__init__()
        self.__prbDispatcher = None
        self.__invitesManager = None
        self.__autoNotifier = None
        self.__isEnabled = False
        return

    def init(self):
        if self.__invitesManager is None:
            self.__invitesManager = InvitesManager()
            self.__invitesManager.init()
        if self.__autoNotifier is None:
            self.__autoNotifier = AutoInvitesNotifier()
        return

    def fini(self):
        self.__removeDispatcher()
        if self.__invitesManager is not None:
            self.__invitesManager.fini()
            self.__invitesManager = None
        if self.__autoNotifier is not None:
            self.__autoNotifier.stop()
            self.__autoNotifier = None
        return

    def getDispatcher(self):
        return self.__prbDispatcher

    def getInvitesManager(self):
        return self.__invitesManager

    def getAutoInvitesNotifier(self):
        return self.__autoNotifier

    def isEnabled(self):
        return self.__isEnabled

    def setEnabled(self, enabled):
        if self.__isEnabled ^ enabled:
            self.__isEnabled = enabled
            if self.__isEnabled and self.__prbDispatcher is not None:
                self.__prbDispatcher.start(context.StartDispatcherCtx.fetch())
                self.__autoNotifier.start()
        return

    def __removeDispatcher(self):
        if self.__prbDispatcher is not None:
            self.__prbDispatcher.stop()
            self.__prbDispatcher = None
        return

    def onAccountShowGUI(self, ctx):
        if self.__prbDispatcher is None:
            self.__prbDispatcher = _PrebattleDispatcher()
        self.__invitesManager.onAccountShowGUI()
        if self.__isEnabled:
            self.__prbDispatcher.start(context.StartDispatcherCtx(**ctx))
            self.__autoNotifier.start()
        return

    def onAvatarBecomePlayer(self):
        self.__isEnabled = False
        self.__removeDispatcher()
        self.__invitesManager.onAvatarBecomePlayer()

    def onDisconnected(self):
        self.__isEnabled = False
        self.__removeDispatcher()
        self.__autoNotifier.stop()
        if self.__invitesManager is not None:
            self.__invitesManager.clear()
        if self.__autoNotifier is not None:
            self.__autoNotifier.stop()
        return


g_prbLoader = _PrbControlLoader()

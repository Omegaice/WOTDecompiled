# 2013.11.15 11:25:37 EST
# Embedded file name: scripts/client/gui/prb_control/dispatcher.py
import weakref
from CurrentVehicle import g_currentVehicle
from adisp import async, process
from constants import PREBATTLE_TYPE
from debug_utils import LOG_ERROR, LOG_DEBUG
from gui import SystemMessages, DialogsInterface, GUI_SETTINGS, game_control
from gui.prb_control import functional, events_dispatcher, getClientPrebattle
from gui.prb_control import getClientUnitMgr
from gui.prb_control.ctrl_events import g_prbCtrlEvents
from gui.prb_control.functional.battle_session import AutoInvitesNotifier
from gui.prb_control.invites import InvitesManager
from gui.prb_control.formatters import messages
from gui.prb_control.functional.interfaces import IGlobalListener
from gui.prb_control import context, areSpecBattlesHidden
from gui.prb_control import isParentControlActivated, getClientUnitBrowser
from gui.prb_control.restrictions.interfaces import IGUIPermissions
from gui.prb_control.settings import PREBATTLE_ACTION_NAME, PREBATTLE_RESTRICTION
from gui.prb_control.settings import CTRL_ENTITY_TYPE, REQUEST_TYPE
from gui.prb_control.settings import IGNORED_UNIT_MGR_ERRORS
from gui.prb_control.settings import IGNORED_UNIT_BROWSER_ERRORS
from gui.prb_control.settings import FUNCTIONAL_EXIT
from gui.prb_control.settings import RETURN_INTRO_UNIT_MGR_ERRORS
from PlayerEvents import g_playerEvents

class _PrebattleDispatcher(object):
    OPEN_PRB_LIST_BY_ACTION = {PREBATTLE_ACTION_NAME.TRAINING_LIST: PREBATTLE_TYPE.TRAINING,
     PREBATTLE_ACTION_NAME.LEAVE_TRAINING_LIST: PREBATTLE_TYPE.TRAINING,
     PREBATTLE_ACTION_NAME.COMPANY_LIST: PREBATTLE_TYPE.COMPANY,
     PREBATTLE_ACTION_NAME.SPEC_BATTLE_LIST: PREBATTLE_TYPE.CLAN}

    def __init__(self):
        super(_PrebattleDispatcher, self).__init__()
        self.__requestCtx = None
        self.__prbFunctional = None
        self.__unitFunctional = None
        self.__queueFunctional = None
        self._globalListeners = set()
        return

    def start(self, ctx):
        self.__requestCtx = context._PrbRequestCtx()
        self.__prbFunctional = functional.createPrbFunctional(self)
        self.__prbFunctional.init()
        self.__unitFunctional = functional.createUnitFunctional(self)
        self.__unitFunctional.init()
        self.__queueFunctional = functional.createQueueFunctional(isInRandomQueue=ctx.isInRandomQueue)
        self._startListening()
        functional.initDevFunctional()
        if not self.__prbFunctional.hasGUIPage() and not self.__prbFunctional.isGUIProcessed():
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

    def getUnitFunctional(self):
        return self.__unitFunctional

    def getQueueFunctional(self):
        return self.__queueFunctional

    def hasModalEntity(self):
        return self.__prbFunctional.hasEntity() or self.__unitFunctional.hasEntity()

    def getFunctionalState(self):
        result = (False, 0)
        if self.__prbFunctional.hasEntity():
            result = (True, self.__prbFunctional.getPrbType())
        elif self.__unitFunctional.hasEntity():
            result = (True, self.__unitFunctional.getPrbType())
        return result

    @async
    @process
    def create(self, ctx, callback = None):
        if ctx.getRequestType() is not REQUEST_TYPE.CREATE:
            LOG_ERROR('Invalid context to create prebattle/unit', ctx)
            if callback:
                callback(False)
        elif not self.__requestCtx.isProcessing():
            result = True
            funcs = ((self.__prbFunctional, context.LeavePrbCtx(waitingID='prebattle/leave')), (self.__unitFunctional, context.LeaveUnitCtx(waitingID='prebattle/leave')))
            for func, leaveCtx in funcs:
                if func.isConfirmToChange(exit=ctx.getFuncExit()):
                    result = yield DialogsInterface.showDialog(func.getConfirmDialogMeta())
                    if result:
                        result = yield self.leave(leaveCtx)
                        ctx.setForced(result)

            if result:
                entry = functional.createEntry(ctx)
                if entry:
                    LOG_DEBUG('Request to create prebattle/unit', ctx)
                    self.__requestCtx = ctx
                    entry.create(ctx, callback=callback)
                else:
                    LOG_ERROR('Entry not found', ctx)
                    if callback:
                        callback(False)
            elif callback:
                callback(False)
        else:
            LOG_ERROR('Request is processing', self.__requestCtx)
            if callback:
                callback(False)
        yield lambda callback = None: callback
        return

    @async
    @process
    def join(self, ctx, callback = None):
        if not self.__requestCtx.isProcessing():
            result = True
            for func in (self.__prbFunctional, self.__unitFunctional):
                if func.isPlayerJoined(ctx):
                    LOG_DEBUG('Player already joined', func.getID())
                    func.showGUI()
                    result = False
                    break
                if func.hasLockedState():
                    SystemMessages.pushI18nMessage('#system_messages:prebattle/hasLockedState', type=SystemMessages.SM_TYPE.Warning)
                    result = False
                    break

            if result:
                funcs = ((self.__prbFunctional, context.LeavePrbCtx(waitingID='prebattle/leave')), (self.__unitFunctional, context.LeaveUnitCtx(waitingID='prebattle/leave')))
                for func, leaveCtx in funcs:
                    if func.isConfirmToChange(exit=ctx.getFuncExit()):
                        result = yield DialogsInterface.showDialog(func.getConfirmDialogMeta())
                        if result:
                            result = yield self.leave(leaveCtx)
                            ctx.setForced(result)

                if result:
                    entry = functional.createEntry(ctx)
                    if entry:
                        LOG_DEBUG('Request to join prebattle/unit', ctx)
                        self.__requestCtx = ctx
                        entry.join(ctx, callback=callback)
                    else:
                        LOG_ERROR('Entry not found', ctx)
                        if callback:
                            callback(False)
                elif callback:
                    callback(False)
            elif callback:
                callback(False)
        else:
            LOG_ERROR('Request is processing', self.__requestCtx)
            if callback:
                callback(False)
        yield lambda callback = None: callback
        return

    @async
    def leave(self, ctx, callback = None):
        if ctx.getRequestType() is not REQUEST_TYPE.LEAVE:
            LOG_ERROR('Invalid context to leave prebattle/unit', ctx)
            if callback:
                callback(False)
            return
        if self.__requestCtx.isProcessing():
            LOG_ERROR('Request is processing', self.__requestCtx)
            if callback:
                callback(False)
            return
        entityType = ctx.getEntityType()
        if entityType is CTRL_ENTITY_TYPE.PREBATTLE:
            if self.__prbFunctional.hasLockedState():
                LOG_ERROR('Player can not leave prebattle', ctx)
                if callback:
                    callback(False)
                return
            LOG_DEBUG('Request to leave prebattle', ctx)
            self.__requestCtx = ctx
            self.__prbFunctional.leave(ctx, callback=callback)
        elif entityType is CTRL_ENTITY_TYPE.UNIT:
            if self.__unitFunctional.hasLockedState():
                LOG_ERROR('Player can not leave unit', ctx)
                if callback:
                    callback(False)
                return
            LOG_DEBUG('Request to leave unit', ctx)
            self.__requestCtx = ctx
            self.__unitFunctional.leave(ctx, callback=callback)
        else:
            LOG_ERROR('Functional not found', ctx)
            if callback:
                callback(False)

    @async
    def sendPrbRequest(self, ctx, callback = None):
        self.__prbFunctional.request(ctx, callback=callback)

    @async
    def sendUnitRequest(self, ctx, callback = None):
        self.__unitFunctional.request(ctx, callback=callback)

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
                elif g_currentVehicle.isDisabledInRoaming():
                    canDo = False
                    restriction = PREBATTLE_RESTRICTION.VEHICLE_ROAMING
            if canDo:
                canDo, restriction = self.__unitFunctional.canPlayerDoAction()
            if canDo:
                canDo, restriction = self.__prbFunctional.canPlayerDoAction()
        return (canDo, restriction)

    def doAction(self, action):
        if not g_currentVehicle.isPresent():
            SystemMessages.pushMessage(messages.getInvalidVehicleMessage(PREBATTLE_RESTRICTION.VEHICLE_NOT_PRESENT), type=SystemMessages.SM_TYPE.Error)
            return False
        LOG_DEBUG('Do prebattle action', action)
        actionName = action.actionName
        if actionName == PREBATTLE_ACTION_NAME.LEAVE_RANDOM_QUEUE:
            self.exitFromRandomQueue()
            result = True
        elif actionName == PREBATTLE_ACTION_NAME.PREBATTLE_LEAVE:
            self.__prbFunctional.doLeaveAction(self)
            result = True
        elif actionName == PREBATTLE_ACTION_NAME.UNIT_LEAVE:
            self.__unitFunctional.doLeaveAction(self)
            result = True
        elif actionName in self.OPEN_PRB_LIST_BY_ACTION:
            entry = functional.createPrbEntry(self.OPEN_PRB_LIST_BY_ACTION[actionName])
            entry.doAction(action, dispatcher=self)
            result = True
        else:
            result = False
            for func in (self.__unitFunctional, self.__prbFunctional, self.__queueFunctional):
                if func.doAction(action=action, dispatcher=self):
                    result = True
                    break

        return result

    def doLeaveAction(self, ctx):
        entityType = ctx.getEntityType()
        if entityType is CTRL_ENTITY_TYPE.PREBATTLE:
            LOG_DEBUG('Request to leave prebattle', ctx)
            self.__prbFunctional.doLeaveAction(self, ctx=ctx)
        elif entityType is CTRL_ENTITY_TYPE.UNIT:
            LOG_DEBUG('Request to leave unit', ctx)
            self.__unitFunctional.doLeaveAction(self, ctx=ctx)

    def addGlobalListener(self, listener):
        if isinstance(listener, IGlobalListener):
            listenerRef = weakref.ref(listener)
            if listenerRef not in self._globalListeners:
                self._globalListeners.add(listenerRef)
                self.__prbFunctional.addListener(listener)
                self.__unitFunctional.addListener(listener)
            else:
                LOG_ERROR('Listener already added', listener)
        else:
            LOG_ERROR('Object is not extend IPrbListener', listener)

    def getGUIPermissions(self):
        if self.__prbFunctional and self.__prbFunctional.hasEntity():
            permissions = self.__prbFunctional.getPermissions()
        elif self.__unitFunctional and self.__unitFunctional.hasEntity():
            permissions = self.__unitFunctional.getPermissions()
        else:
            permissions = IGUIPermissions()
        return permissions

    def removeGlobalListener(self, listener):
        listenerRef = weakref.ref(listener)
        if listenerRef in self._globalListeners:
            self._globalListeners.remove(listenerRef)
        else:
            LOG_ERROR('Listener not found', listener)
        if self.__prbFunctional:
            self.__prbFunctional.removeListener(listener)
        if self.__unitFunctional:
            self.__unitFunctional.removeListener(listener)

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
        gameSession = game_control.g_instance.gameSession
        if gameSession.lastBanMsg is not None:
            self.gs_onTillBanNotification(*gameSession.lastBanMsg)
        gameSession.onTimeTillBan += self.gs_onTillBanNotification
        unitMgr = getClientUnitMgr()
        if unitMgr:
            unitMgr.onUnitJoined += self.unitMgr_onUnitJoined
            unitMgr.onUnitLeft += self.unitMgr_onUnitLeft
            unitMgr.onUnitErrorReceived += self.unitMgr_onUnitErrorReceived
        else:
            LOG_ERROR('Unit manager is not defined')
        unitBrowser = getClientUnitBrowser()
        if unitBrowser:
            unitBrowser.onErrorReceived += self.unitBrowser_onErrorReceived
        else:
            LOG_ERROR('Unit browser is not defined')
        g_prbCtrlEvents.onPrebattleInited += self.ctrl_onPrebattleInited
        g_prbCtrlEvents.onUnitIntroModeJoined += self.ctrl_onUnitIntroModeJoined
        g_prbCtrlEvents.onUnitIntroModeLeft += self.ctrl_onUnitIntroModeLeft
        return

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
        unitMgr = getClientUnitMgr()
        if unitMgr:
            unitMgr.onUnitJoined -= self.unitMgr_onUnitJoined
            unitMgr.onUnitLeft -= self.unitMgr_onUnitLeft
            unitMgr.onUnitErrorReceived -= self.unitMgr_onUnitErrorReceived
        unitBrowser = getClientUnitBrowser()
        if unitBrowser:
            unitBrowser.onErrorReceived -= self.unitBrowser_onErrorReceived
        g_prbCtrlEvents.clear()

    def _setRequestCtx(self, ctx):
        result = True
        if self.__requestCtx.isProcessing():
            LOG_ERROR('Request is processing', self.__requestCtx)
            result = False
        else:
            self.__requestCtx = ctx
        return result

    def _clear(self, woEvents = False):
        if self.__requestCtx:
            self.__requestCtx.clear()
            self.__requestCtx = None
        if self.__prbFunctional:
            self.__prbFunctional.fini(woEvents=woEvents)
            self.__prbFunctional = None
        if self.__unitFunctional:
            self.__unitFunctional.fini(woEvents=woEvents)
            self.__unitFunctional = None
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
            self.__requestCtx.stopProcessing(result=False)

    def pe_onPrebattleJoinFailure(self, errorCode):
        SystemMessages.pushMessage(messages.getJoinFailureMessage(errorCode), type=SystemMessages.SM_TYPE.Error)
        self.__requestCtx.stopProcessing(result=False)
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
            self.__unitFunctional.reset()
            key = '#system_messages:gameSessionControl/korea/{0:>s}'
            if isPlayTimeBan:
                SystemMessages.g_instance.pushI18nMessage(key.format('playTimeNotification'), timeTillBlock)
            else:
                SystemMessages.g_instance.pushI18nMessage(key.format('midnightNotification'))

    def ctrl_onPrebattleInited(self):
        self.__prbFunctional.fini()
        self.__requestCtx.stopProcessing(result=True)
        self.__prbFunctional = functional.createPrbFunctional(self)
        self.__prbFunctional.init(ctx=self.__requestCtx)
        events_dispatcher.updateUI()

    def _changeUnitFunctional(self, exit = None):
        if exit is not None:
            self.__unitFunctional.setExit(exit)
        self.__unitFunctional.fini()
        self.__requestCtx.stopProcessing(result=True)
        self.__unitFunctional = functional.createUnitFunctional(self)
        self.__unitFunctional.init()
        events_dispatcher.updateUI()
        return

    def ctrl_onUnitIntroModeJoined(self):
        self._changeUnitFunctional(exit=FUNCTIONAL_EXIT.INTRO_UNIT)

    def ctrl_onUnitIntroModeLeft(self):
        self._changeUnitFunctional()

    def unitMgr_onUnitJoined(self, unitMgrID, unitIdx):
        if self.__unitFunctional.getID() == unitMgrID and self.__unitFunctional.getUnitIdx() == unitIdx:
            self.__unitFunctional.rejoin()
        else:
            self._changeUnitFunctional(exit=FUNCTIONAL_EXIT.UNIT)

    def unitMgr_onUnitLeft(self, unitMgrID, unitIdx):
        self._changeUnitFunctional()

    def unitMgr_onUnitErrorReceived(self, requestID, unitMgrID, unitIdx, errorCode, errorString):
        if errorCode not in IGNORED_UNIT_MGR_ERRORS:
            msgType, msgBody = messages.getUnitMessage(errorCode, errorString)
            SystemMessages.pushMessage(msgBody, type=msgType)
            if errorCode in RETURN_INTRO_UNIT_MGR_ERRORS:
                self.__unitFunctional.setExit(FUNCTIONAL_EXIT.INTRO_UNIT)
            self.__requestCtx.stopProcessing(result=False)
            events_dispatcher.updateUI()

    def unitBrowser_onErrorReceived(self, errorCode, errorString):
        if errorCode not in IGNORED_UNIT_BROWSER_ERRORS:
            msgType, msgBody = messages.getUnitBrowserMessage(errorCode, errorString)
            SystemMessages.pushMessage(msgBody, type=msgType)


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
# okay decompyling res/scripts/client/gui/prb_control/dispatcher.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:25:38 EST

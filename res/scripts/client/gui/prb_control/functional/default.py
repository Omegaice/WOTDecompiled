import weakref
import BigWorld
from PlayerEvents import g_playerEvents
import account_helpers
from constants import PREBATTLE_TYPE_NAMES, PREBATTLE_ACCOUNT_STATE, REQUEST_COOLDOWN
from debug_utils import LOG_ERROR, LOG_DEBUG
from gui import prb_control, SystemMessages
from gui.Scaleform.daapi.view.dialogs import I18nConfirmDialogMeta, SimpleDialogMeta
from gui.Scaleform.locale.DIALOGS import DIALOGS
from gui.prb_control import restrictions, events_dispatcher
from gui.prb_control.formatters import messages
from gui.prb_control.functional.interfaces import IPrbEntry, IPrbFunctional
from gui.prb_control.functional.interfaces import IPrbListener, IPrbListRequester
from gui.prb_control import info, isParentControlActivated
from gui.prb_control.info import PlayerPrbInfo
from gui.prb_control.sequences import RosterIterator
from gui.prb_control.restrictions.limits import DefaultLimits
from gui.prb_control.restrictions.permissions import DefaultPermissions
from gui.prb_control.settings import PREBATTLE_ROSTER, PREBATTLE_INIT_STEP
from gui.prb_control.settings import PREBATTLE_REQUEST
from prebattle_shared import decodeRoster

class PrbEntry(IPrbEntry):

    def doAction(self, action, dispatcher = None):
        return True

    def create(self, ctx, callback = None):
        LOG_ERROR('Routine "create" must be implemented in subclass')

    def join(self, ctx, callback = None):
        if prb_control.getClientPrebattle() is None or ctx.isForced():
            ctx.startProcessing(callback=callback)
            BigWorld.player().prb_join(ctx.getID())
        else:
            LOG_ERROR('First, player has to confirm exit from the current prebattle', prb_control.getPrebattleType())
            if callback:
                callback(False)
        return


class PrbInitFunctional(IPrbFunctional):

    def __init__(self, dispatcher):
        super(PrbInitFunctional, self).__init__()
        self.__prbInitSteps = 0
        self.__dispatcher = weakref.proxy(dispatcher)

    def init(self, clientPrb = None, ctx = None):
        if clientPrb is None:
            clientPrb = prb_control.getClientPrebattle()
        if clientPrb is not None:
            clientPrb.onSettingsReceived += self.prb_onSettingsReceived
            clientPrb.onRosterReceived += self.prb_onRosterReceived
            if prb_control.isPrebattleSettingsReceived(prebattle=clientPrb):
                self.prb_onSettingsReceived()
            if len(prb_control.getPrebattleRosters(prebattle=clientPrb)):
                self.prb_onRosterReceived()
        return

    def fini(self, clientPrb = None, woEvents = False):
        self.__dispatcher = None
        if clientPrb is None:
            clientPrb = prb_control.getClientPrebattle()
        if clientPrb is not None:
            clientPrb.onSettingsReceived -= self.prb_onSettingsReceived
            clientPrb.onRosterReceived -= self.prb_onRosterReceived
        return

    def prb_onSettingsReceived(self):
        LOG_DEBUG('prb_onSettingsReceived')
        self.__prbInitSteps |= PREBATTLE_INIT_STEP.SETTING_RECEIVED
        self.__isPrebattleInited()

    def prb_onRosterReceived(self):
        LOG_DEBUG('prb_onRosterReceived')
        self.__prbInitSteps |= PREBATTLE_INIT_STEP.ROSTERS_RECEIVED
        self.__isPrebattleInited()

    def __isPrebattleInited(self):
        result = False
        if self.__prbInitSteps is PREBATTLE_INIT_STEP.INITED:
            if self.__dispatcher is not None:
                self.__dispatcher._onPrbInited()
            result = True
            self.__prbInitSteps = 0
        return result


class PrbRosterRequester(IPrbListRequester):

    def __init__(self):
        super(PrbRosterRequester, self).__init__()
        self.__callback = None
        self.__prebattleID = 0
        return

    def start(self, callback):
        if callback is not None and callable(callback):
            self.__callback = callback
        else:
            LOG_ERROR('Callback is None or is not callable')
            return
        g_playerEvents.onPrebattleRosterReceived += self.__pe_onPrebattleRosterReceived
        return

    def stop(self):
        g_playerEvents.onPrebattleRosterReceived -= self.__pe_onPrebattleRosterReceived
        self.__callback = None
        return

    def request(self, prebattleID = None):
        LOG_DEBUG('Request prebattle rosters', prebattleID)
        BigWorld.player().requestPrebattleRoster(prebattleID)

    def __pe_onPrebattleRosterReceived(self, prebattleID, roster):
        self.__callback(prebattleID, RosterIterator(roster))


class PrbDispatcher(IPrbFunctional):

    def __init__(self, settings, permClass = None, limits = None, requestHandlers = None):
        super(PrbDispatcher, self).__init__()
        self._settings = settings
        self._listeners = []
        if permClass is not None:
            self._permClass = permClass
        else:
            self._permClass = DefaultPermissions
        if limits is not None:
            self._limits = limits
        else:
            self._limits = DefaultLimits(self)
        if requestHandlers is not None:
            self._requestHandlers = requestHandlers
        else:
            self._requestHandlers = {}
        return

    def init(self, clientPrb = None, ctx = None):
        if clientPrb is None:
            clientPrb = prb_control.getClientPrebattle()
        if clientPrb is not None:
            clientPrb.onSettingUpdated += self.prb_onSettingUpdated
            clientPrb.onRosterReceived += self.prb_onRosterReceived
            clientPrb.onTeamStatesReceived += self.prb_onTeamStatesReceived
            clientPrb.onPlayerStateChanged += self.prb_onPlayerStateChanged
            clientPrb.onPlayerRosterChanged += self.prb_onPlayerRosterChanged
            clientPrb.onPlayerAdded += self.prb_onPlayerAdded
            clientPrb.onPlayerRemoved += self.prb_onPlayerRemoved
            clientPrb.onKickedFromQueue += self.prb_onKickedFromQueue
            for listener in self._listeners:
                listener.onPrbFunctionalInited()

        else:
            LOG_ERROR('ClientPrebattle is not defined')
        return

    def fini(self, clientPrb = None, woEvents = False):
        self._settings = None
        self._requestHandlers.clear()
        if self._limits is not None:
            self._limits.clear()
            self._limits = None
        for listener in self._listeners:
            listener.onPrbFunctionalFinished()

        if clientPrb is None:
            clientPrb = prb_control.getClientPrebattle()
        if clientPrb is not None:
            clientPrb.onSettingUpdated -= self.prb_onSettingUpdated
            clientPrb.onTeamStatesReceived -= self.prb_onTeamStatesReceived
            clientPrb.onPlayerStateChanged -= self.prb_onPlayerStateChanged
            clientPrb.onPlayerRosterChanged -= self.prb_onPlayerRosterChanged
            clientPrb.onPlayerAdded -= self.prb_onPlayerAdded
            clientPrb.onPlayerRemoved -= self.prb_onPlayerRemoved
            clientPrb.onKickedFromQueue -= self.prb_onKickedFromQueue
        return

    def addListener(self, listener):
        if isinstance(listener, IPrbListener):
            if listener not in self._listeners:
                self._listeners.append(listener)
            else:
                LOG_ERROR('Listener already added', listener)
        else:
            LOG_ERROR('Object is not extend IPrbListener', listener)

    def removeListener(self, listener):
        if listener in self._listeners:
            self._listeners.remove(listener)
        else:
            LOG_ERROR('Listener not found', listener)

    def getID(self):
        return prb_control.getPrebattleID()

    def getPrbType(self):
        if self._settings:
            return self._settings['type']
        return 0

    def getPrbTypeName(self):
        return prb_control.getPrebattleTypeName(self.getPrbType())

    def getSettings(self):
        return self._settings

    def getLimits(self):
        return self._limits

    def getPermissions(self, pID = None):
        return restrictions.createPermissions(self, pID=pID)

    def isCreator(self, pDatabaseID = None):
        return self._permClass.isCreator(self.getRoles(pDatabaseID=pDatabaseID))

    def hasEntity(self):
        return True

    def isConfirmToChange(self):
        return self._settings is not None

    def getConfirmDialogMeta(self):
        message = DIALOGS.exitcurrentprebattle_custommessage(PREBATTLE_TYPE_NAMES[self.getPrbType()])
        return I18nConfirmDialogMeta('exitCurrentPrebattle', meta=SimpleDialogMeta(message=message))

    def prb_onSettingUpdated(self, settingName):
        settingValue = self._settings[settingName]
        LOG_DEBUG('prb_onSettingUpdated', settingName, settingValue)
        for listener in self._listeners:
            listener.onSettingUpdated(self, settingName, settingValue)

    def prb_onTeamStatesReceived(self):
        team1State = self.getTeamState(team=1)
        team2State = self.getTeamState(team=2)
        LOG_DEBUG('prb_onTeamStatesReceived', team1State, team2State)
        for listener in self._listeners:
            listener.onTeamStatesReceived(self, team1State, team2State)

    def prb_onPlayerStateChanged(self, pID, roster):
        accountInfo = self.getPlayerInfo(pID=pID)
        LOG_DEBUG('prb_onPlayerStateChanged', accountInfo)
        for listener in self._listeners:
            listener.onPlayerStateChanged(self, roster, accountInfo)

    def prb_onRosterReceived(self):
        LOG_DEBUG('prb_onRosterReceived')
        rosters = self.getRosters()
        for listener in self._listeners:
            listener.onRostersChanged(self, rosters, True)

        team = self.getPlayerTeam()
        for listener in self._listeners:
            listener.onPlayerTeamNumberChanged(self, team)

    def prb_onPlayerRosterChanged(self, pID, prevRoster, roster, actorID):
        LOG_DEBUG('prb_onPlayerRosterChanged', pID, prevRoster, roster, actorID)
        rosters = self.getRosters(keys=[prevRoster, roster])
        actorInfo = self.getPlayerInfo(pID=actorID)
        playerInfo = self.getPlayerInfo(pID=pID)
        for listener in self._listeners:
            if actorInfo and playerInfo:
                listener.onPlayerRosterChanged(self, actorInfo, playerInfo)
            listener.onRostersChanged(self, rosters, False)

        if pID == account_helpers.getPlayerID():
            prevTeam, _ = decodeRoster(prevRoster)
            currentTeam, _ = decodeRoster(roster)
            if currentTeam is not prevTeam:
                for listener in self._listeners:
                    listener.onPlayerTeamNumberChanged(self, currentTeam)

    def prb_onPlayerAdded(self, pID, roster):
        LOG_DEBUG('prb_onPlayerAdded', pID, roster)
        rosters = self.getRosters(keys=[roster])
        playerInfo = self.getPlayerInfo(pID=pID, rosterKey=roster)
        for listener in self._listeners:
            listener.onPlayerAdded(self, playerInfo)
            listener.onRostersChanged(self, rosters, False)

    def prb_onPlayerRemoved(self, pID, roster, name):
        LOG_DEBUG('prb_onPlayerRemoved', pID, roster, name)
        rosters = self.getRosters(keys=[roster])
        playerInfo = PlayerPrbInfo(pID, name=name)
        for listener in self._listeners:
            listener.onPlayerRemoved(self, playerInfo)
            listener.onRostersChanged(self, rosters, False)

    def prb_onKickedFromQueue(self, *args):
        LOG_DEBUG('prb_onKickedFromQueue', args)
        message = messages.getPrbKickedFromQueueMessage(self.getPrbTypeName())
        if len(message):
            SystemMessages.pushMessage(message, type=SystemMessages.SM_TYPE.Warning)


class PrbFunctional(PrbDispatcher):

    def getRosterKey(self, pID = None):
        rosters = prb_control.getPrebattleRosters()
        rosterRange = PREBATTLE_ROSTER.getRange(self.getPrbType())
        if pID is None:
            pID = account_helpers.getPlayerID()
        for roster in rosterRange:
            if roster in rosters and pID in rosters[roster].keys():
                return roster

        return PREBATTLE_ROSTER.UNKNOWN

    def getPlayerInfo(self, pID = None, rosterKey = None):
        rosters = prb_control.getPrebattleRosters()
        if pID is None:
            pID = account_helpers.getPlayerID()
        if rosterKey is not None:
            if rosterKey in rosters and pID in rosters[rosterKey].keys():
                return info.PlayerPrbInfo(pID, functional=self, roster=rosterKey, **rosters[rosterKey][pID])
        else:
            rosterRange = PREBATTLE_ROSTER.getRange(self.getPrbType())
            for roster in rosterRange:
                if roster in rosters and pID in rosters[roster].keys():
                    return info.PlayerPrbInfo(pID, functional=self, roster=roster, **rosters[roster][pID])

        return info.PlayerPrbInfo(-1L)

    def getPlayerInfoByDbID(self, dbID):
        rosters = prb_control.getPrebattleRosters()
        rosterRange = PREBATTLE_ROSTER.getRange(self.getPrbType())
        for roster in rosterRange:
            if roster in rosters:
                for pID, data in rosters[roster].iteritems():
                    if data['dbID'] == dbID:
                        return info.PlayerPrbInfo(pID, functional=self, roster=roster, **rosters[roster][pID])

        return info.PlayerPrbInfo(-1L)

    def getPlayerTeam(self, pID = None):
        team = 0
        roster = self.getRosterKey(pID=pID)
        if roster is not PREBATTLE_ROSTER.UNKNOWN:
            team, _ = decodeRoster(roster)
        return team

    def getTeamState(self, team = None):
        result = info.TeamStateInfo(0)
        if team is None:
            roster = self.getRosterKey()
            if roster is not PREBATTLE_ROSTER.UNKNOWN:
                team, _ = decodeRoster(self.getRosterKey())
        teamStates = prb_control.getPrebattleTeamStates()
        if team is not None and team < len(teamStates):
            result = info.TeamStateInfo(teamStates[team])
        return result

    def getRoles(self, pDatabaseID = None):
        result = 0
        if self._settings is None:
            return result
        else:
            if pDatabaseID is None:
                pDatabaseID = account_helpers.getPlayerDatabaseID()
            roles = self._settings['roles']
            if pDatabaseID in roles:
                result = roles[pDatabaseID]
            return result

    def getProps(self):
        return info.PrbPropsInfo(**prb_control.getPrebattleProps())

    def leave(self, ctx, callback = None):
        ctx.startProcessing(callback)
        BigWorld.player().prb_leave(ctx.onResponseReceived)

    def request(self, ctx, callback = None):
        requestType = ctx.getRequestType()
        if requestType in self._requestHandlers:
            LOG_DEBUG('Prebattle request', ctx)
            self._requestHandlers[requestType](ctx, callback=callback)
        else:
            LOG_ERROR('Handler not found', ctx)
            callback(False)

    def reset(self):

        def setNotReady(code):
            if code >= 0:
                BigWorld.player().prb_notReady(PREBATTLE_ACCOUNT_STATE.NOT_READY, lambda *args: None)

        if self.isCreator() and self.getTeamState().isInQueue():
            BigWorld.player().prb_teamNotReady(self.getPlayerTeam(), setNotReady)
        elif self.getPlayerInfo().isReady():
            setNotReady(0)

    def assign(self, ctx, callback = None):
        prevTeam, _ = decodeRoster(self.getRosterKey(pID=ctx.getPlayerID()))
        nextTeam, assigned = decodeRoster(ctx.getRoster())
        pPermissions = self.getPermissions()
        if prevTeam is nextTeam:
            if not pPermissions.canAssignToTeam(team=nextTeam):
                LOG_ERROR('Player can not change roster', nextTeam, assigned)
                if callback:
                    callback(False)
                return
        elif not pPermissions.canChangePlayerTeam():
            LOG_ERROR('Player can not change team', prevTeam, nextTeam)
            if callback:
                callback(False)
            return
        result, restriction = self.getLimits().isMaxCountValid(nextTeam, assigned)
        if not result:
            LOG_ERROR('Max count limit', nextTeam, assigned)
            if callback:
                callback(False)
            return
        ctx.startProcessing(callback)
        BigWorld.player().prb_assign(ctx.getPlayerID(), ctx.getRoster(), ctx.onResponseReceived)

    def setTeamState(self, ctx, callback = None):
        team = ctx.getTeam()
        if not self.getPermissions().canSetTeamState(team=team):
            LOG_ERROR('Player can not change state of team', team)
            if callback:
                callback(False)
            return
        teamState = self.getTeamState()
        setReady = ctx.isReadyState()
        if setReady and teamState.isNotReady():
            if teamState.isLocked():
                LOG_ERROR('Team is locked')
                if callback:
                    callback(False)
            else:
                self._setTeamReady(ctx, callback=callback)
        elif not setReady and teamState.isInQueue():
            self._setTeamNotReady(ctx, callback=callback)
        elif callback:
            callback(True)

    def setPlayerState(self, ctx, callback = None):
        playerInfo = self.getPlayerInfo()
        if playerInfo is not None:
            playerIsReady = playerInfo.isReady()
            setReady = ctx.isReadyState()
            if setReady and not playerIsReady:
                self._setPlayerReady(ctx, callback=callback)
            elif not setReady and playerIsReady:
                self._setPlayerNotReady(ctx, callback=callback)
            elif callback:
                callback(True)
        else:
            LOG_ERROR('Account info not found in prebattle.rosters', ctx)
            if callback:
                callback(False)
        return

    def kickPlayer(self, ctx, callback = None):
        pID = ctx.getPlayerID()
        rosterKey = self.getRosterKey(pID=pID)
        team, assigned = decodeRoster(rosterKey)
        pPermissions = self.getPermissions()
        if not pPermissions.canKick(team=team):
            LOG_ERROR('Player can not kick from team', team, pPermissions)
            if callback:
                callback(False)
            return
        if assigned:
            if self.getPlayerInfo(pID=pID, rosterKey=rosterKey).isReady() and self.getTeamState(team=team).isInQueue():
                LOG_ERROR('Player is ready, assigned and team is ready or locked', ctx)
                if callback:
                    callback(False)
                return
        ctx.startProcessing(callback)
        BigWorld.player().prb_kick(ctx.getPlayerID(), ctx.onResponseReceived)

    def swapTeams(self, ctx, callback = None):
        if info.isRequestInCoolDown(PREBATTLE_REQUEST.SWAP_TEAMS):
            SystemMessages.pushMessage(messages.getRequestInCoolDownMessage(PREBATTLE_REQUEST.SWAP_TEAMS), type=SystemMessages.SM_TYPE.Error)
            if callback:
                callback(False)
            return
        pPermissions = self.getPermissions()
        if self.getPermissions().canChangePlayerTeam():
            ctx.startProcessing(callback)
            BigWorld.player().prb_swapTeams(ctx.onResponseReceived)
            info.setRequestCoolDown(PREBATTLE_REQUEST.SWAP_TEAMS)
        else:
            LOG_ERROR('Player can not swap teams', pPermissions)
            if callback:
                callback(False)

    def sendInvites(self, ctx, callback = None):
        if info.isRequestInCoolDown(PREBATTLE_REQUEST.SEND_INVITE):
            SystemMessages.pushMessage(messages.getRequestInCoolDownMessage(PREBATTLE_REQUEST.SEND_INVITE), type=SystemMessages.SM_TYPE.Error)
            if callback:
                callback(False)
            return
        pPermissions = self.getPermissions()
        if self.getPermissions().canSendInvite():
            BigWorld.player().prb_sendInvites(ctx.getDatabaseIDs(), ctx.getComment())
            info.setRequestCoolDown(PREBATTLE_REQUEST.SEND_INVITE, coolDown=REQUEST_COOLDOWN.PREBATTLE_INVITES)
            if callback:
                callback(True)
        else:
            LOG_ERROR('Player can not send invite', pPermissions)
            if callback:
                callback(False)

    def _setTeamNotReady(self, ctx, callback = None):
        if info.isRequestInCoolDown(PREBATTLE_REQUEST.SET_TEAM_STATE):
            SystemMessages.pushMessage(messages.getRequestInCoolDownMessage(PREBATTLE_REQUEST.SET_TEAM_STATE, REQUEST_COOLDOWN.PREBATTLE_TEAM_NOT_READY), type=SystemMessages.SM_TYPE.Error)
            if callback:
                callback(False)
            return
        ctx.startProcessing(callback)
        BigWorld.player().prb_teamNotReady(ctx.getTeam(), ctx.onResponseReceived)
        info.setRequestCoolDown(PREBATTLE_REQUEST.SET_TEAM_STATE, coolDown=REQUEST_COOLDOWN.PREBATTLE_TEAM_NOT_READY)

    def _setTeamReady(self, ctx, callback = None):
        if isParentControlActivated():
            events_dispatcher.showParentControlNotification()
            if callback:
                callback(False)
            return
        isValid, notValidReason = self._limits.isTeamValid()
        if isValid:
            ctx.startProcessing(callback)
            BigWorld.player().prb_teamReady(ctx.getTeam(), ctx.isForced(), ctx.getGamePlayMask(), ctx.onResponseReceived)
        else:
            LOG_ERROR('Team is invalid', notValidReason)
            if callback:
                callback(False)
            SystemMessages.pushMessage(messages.getInvalidTeamMessage(notValidReason, functional=self), type=SystemMessages.SM_TYPE.Error)

    def _setPlayerNotReady(self, ctx, callback = None):
        if info.isRequestInCoolDown(PREBATTLE_REQUEST.SET_PLAYER_STATE):
            SystemMessages.pushMessage(messages.getRequestInCoolDownMessage(PREBATTLE_REQUEST.SET_PLAYER_STATE, REQUEST_COOLDOWN.PREBATTLE_NOT_READY), type=SystemMessages.SM_TYPE.Error)
            if callback:
                callback(False)
            return
        rosterKey = self.getRosterKey()
        team, assigned = decodeRoster(rosterKey)
        if assigned and self.getTeamState(team=team).isInQueue():
            LOG_ERROR('Account assigned and team is ready or locked')
            if callback:
                callback(False)
            return
        ctx.startProcessing(callback)
        BigWorld.player().prb_notReady(PREBATTLE_ACCOUNT_STATE.NOT_READY, ctx.onResponseReceived)
        info.setRequestCoolDown(PREBATTLE_REQUEST.SET_PLAYER_STATE, coolDown=REQUEST_COOLDOWN.PREBATTLE_NOT_READY)

    def _setPlayerReady(self, ctx, callback = None):
        if isParentControlActivated():
            events_dispatcher.showParentControlNotification()
            if callback:
                callback(False)
            return
        isValid, notValidReason = self._limits.isVehicleValid()
        if not isValid:
            SystemMessages.pushMessage(messages.getInvalidVehicleMessage(notValidReason, self), type=SystemMessages.SM_TYPE.Error)
            if callback:
                callback(False)
            return
        rosterKey = self.getRosterKey()
        team, assigned = decodeRoster(rosterKey)
        if assigned and self.getTeamState(team=team).isInQueue():
            LOG_ERROR('Account assigned and team is ready or locked')
            if callback:
                callback(False)
            return
        ctx.startProcessing(callback)
        BigWorld.player().prb_ready(ctx.getVehicleInventoryID(), ctx.onResponseReceived)

    def _getPlayersStateStats(self, rosterKey):
        clientPrb = prb_control.getClientPrebattle()
        notReadyCount = 0
        playersCount = 0
        limitMaxCount = 0
        haveInBattle = False
        if clientPrb:
            players = clientPrb.rosters.get(rosterKey, {})
            playersCount = len(players)
            team, assigned = decodeRoster(rosterKey)
            teamLimits = self._settings.getTeamLimits(team)
            limitMaxCount = teamLimits['maxCount'][not assigned]
            for _, accInfo in players.iteritems():
                state = accInfo.get('state', PREBATTLE_ACCOUNT_STATE.UNKNOWN)
                if not state & PREBATTLE_ACCOUNT_STATE.READY or state & PREBATTLE_ACCOUNT_STATE.OFFLINE:
                    notReadyCount += 1
                    if not haveInBattle and state & PREBATTLE_ACCOUNT_STATE.IN_BATTLE:
                        haveInBattle = True

        return info.PlayersStateStats(notReadyCount, haveInBattle, playersCount, limitMaxCount)

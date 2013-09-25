import BigWorld
from ConnectionManager import connectionManager
from PlayerEvents import g_playerEvents
from debug_utils import LOG_ERROR
from gui import SystemMessages
from gui.Scaleform.locale.SYSTEM_MESSAGES import SYSTEM_MESSAGES
from gui.shared import g_eventBus, EVENT_BUS_SCOPE
from gui.shared.events import ChannelCarouselEvent
from helpers import i18n
from gui.prb_control import events_dispatcher, getPrebattleRosters, info, context, getPrebattleSettings, isBattleSession, getPrebattleType
from gui.prb_control.functional.default import PrbEntry, PrbFunctional
from gui.prb_control.functional.interfaces import IPrbListRequester
from gui.prb_control.sequences import AutoInvitesIterator
from gui.prb_control.settings import PREBATTLE_REQUEST, PREBATTLE_ROSTER, PREBATTLE_SETTING_NAME
from gui.prb_control.restrictions.limits import BattleSessionLimits
from gui.prb_control.restrictions.permissions import BattleSessionPermissions
from predefined_hosts import g_preDefinedHosts
from gui.prb_control.prb_helpers import vehicleAmmoCheck

class BattleSessionEntry(PrbEntry):

    def create(self, ctx, callback = None):
        raise Exception, 'BattleSession can be created through the web only'

    def join(self, ctx, callback = None):
        player = BigWorld.player()
        if hasattr(player, 'prebattleAutoInvites'):
            peripheryID = player.prebattleAutoInvites.get(ctx.getID(), {}).get('peripheryID', 0)
            if peripheryID and peripheryID != connectionManager.peripheryID:
                pInfo = g_preDefinedHosts.periphery(peripheryID)
                if pInfo is None:
                    message = i18n.makeString(SYSTEM_MESSAGES.ARENA_START_ERRORS_JOIN_WRONG_PERIPHERY_UNKNOWN)
                else:
                    message = i18n.makeString(SYSTEM_MESSAGES.ARENA_START_ERRORS_JOIN_WRONG_PERIPHERY_KNOWN, pInfo.name)
                SystemMessages.pushMessage(message, type=SystemMessages.SM_TYPE.Warning)
                if callback:
                    callback(False)
                return
        super(BattleSessionEntry, self).join(ctx, callback)
        return

    def doAction(self, action, dispatcher = None):
        if isBattleSession():
            events_dispatcher.loadBattleSessionWindow(getPrebattleType())
        else:
            events_dispatcher.loadBattleSessionList()
        return True


class AutoInvitesRequester(IPrbListRequester):

    def __init__(self):
        super(AutoInvitesRequester, self).__init__()
        self.__callback = None
        return

    def start(self, callback):
        if callback is not None and callable(callback):
            self.__callback = callback
        else:
            LOG_ERROR('Callback is None or is not callable')
            return
        g_playerEvents.onPrebattleAutoInvitesChanged += self.__pe_onPrbAutoInvitesChanged
        return

    def stop(self):
        g_playerEvents.onPrebattleAutoInvitesChanged -= self.__pe_onPrbAutoInvitesChanged
        self.__callback = None
        return

    def request(self, ctx = None):
        self.__fetchList()

    def __pe_onPrbAutoInvitesChanged(self):
        self.__fetchList()

    def __fetchList(self):
        if self.__callback is not None:
            self.__callback(AutoInvitesIterator())
        return


class AutoInvitesNotifier(object):

    def __init__(self):
        super(AutoInvitesNotifier, self).__init__()
        self.__notified = set()
        self.__isStarted = False

    def start(self):
        if self.__isStarted:
            self.__doNotify()
            return
        self.__isStarted = True
        g_playerEvents.onPrebattleAutoInvitesChanged += self.__pe_onPrbAutoInvitesChanged
        self.__doNotify()

    def stop(self):
        if not self.__isStarted:
            return
        self.__isStarted = False
        g_playerEvents.onPrebattleAutoInvitesChanged -= self.__pe_onPrbAutoInvitesChanged
        self.__notified.clear()

    def getNotified(self):
        result = []
        for invite in AutoInvitesIterator():
            if invite.prbID in self.__notified:
                result.append(invite)

        return result

    def __doNotify(self):
        haveInvites = False
        for invite in AutoInvitesIterator():
            prbID = invite.prbID
            haveInvites = True
            if prbID in self.__notified:
                continue
            if not len(invite.description):
                continue
            events_dispatcher.fireAutoInviteReceived(invite)
            self.__notified.add(prbID)

        if not haveInvites:
            self.__notified.clear()

    def __pe_onPrbAutoInvitesChanged(self):
        self.__doNotify()


class BattleSessionFunctional(PrbFunctional):

    def __init__(self, settings):
        requests = {PREBATTLE_REQUEST.ASSIGN: self.assign,
         PREBATTLE_REQUEST.SET_TEAM_STATE: self.setTeamState,
         PREBATTLE_REQUEST.SET_PLAYER_STATE: self.setPlayerState,
         PREBATTLE_REQUEST.KICK: self.kickPlayer}
        super(BattleSessionFunctional, self).__init__(settings, permClass=BattleSessionPermissions, limits=BattleSessionLimits(self), requestHandlers=requests)

    def init(self, clientPrb = None, ctx = None):
        super(BattleSessionFunctional, self).init(clientPrb=clientPrb)
        events_dispatcher.loadBattleSessionWindow(self.getPrbType())
        g_eventBus.addListener(ChannelCarouselEvent.CAROUSEL_INITED, self.__handleCarouselInited, scope=EVENT_BUS_SCOPE.LOBBY)

    def fini(self, clientPrb = None, woEvents = False):
        prbType = self.getPrbType()
        super(BattleSessionFunctional, self).fini(clientPrb=clientPrb)
        if not woEvents:
            events_dispatcher.unloadBattleSessionWindow(prbType)
        else:
            events_dispatcher.removeSpecBattleFromCarousel(prbType)
        g_eventBus.removeListener(ChannelCarouselEvent.CAROUSEL_INITED, self.__handleCarouselInited, scope=EVENT_BUS_SCOPE.LOBBY)

    @vehicleAmmoCheck
    def setPlayerState(self, ctx, callback = None):
        super(BattleSessionFunctional, self).setPlayerState(ctx, callback)

    def showGUI(self):
        events_dispatcher.loadBattleSessionWindow(self.getPrbType())

    def getRosters(self, keys = None):
        rosters = getPrebattleRosters()
        prbRosters = PREBATTLE_ROSTER.getRange(self.getPrbType(), self.getPlayerTeam())
        result = dict(((r, []) for r in prbRosters))
        for roster in prbRosters:
            if roster in rosters:
                result[roster] = map(lambda accInfo: info.PlayerPrbInfo(accInfo[0], functional=self, roster=roster, **accInfo[1]), rosters[roster].iteritems())

        return result

    def getTeamLimits(self):
        return getPrebattleSettings().getTeamLimits(self.getPlayerTeam())

    def doAction(self, action = None, dispatcher = None):
        if self.getPlayerInfo().isReady():
            self.setPlayerState(context.SetPlayerStateCtx(False, waitingID='prebattle/player_not_ready'))
        else:
            self.setPlayerState(context.SetPlayerStateCtx(True, waitingID='prebattle/player_ready'))
        return True

    def prb_onSettingUpdated(self, settingName):
        super(BattleSessionFunctional, self).prb_onSettingUpdated(settingName)
        if settingName == PREBATTLE_SETTING_NAME.LIMITS:
            events_dispatcher.updateUI()

    def prb_onPlayerStateChanged(self, pID, roster):
        super(BattleSessionFunctional, self).prb_onPlayerStateChanged(pID, roster)
        events_dispatcher.updateUI()

    def prb_onRosterReceived(self):
        super(BattleSessionFunctional, self).prb_onRosterReceived()
        events_dispatcher.updateUI()

    def prb_onPlayerRosterChanged(self, pID, prevRoster, roster, actorID):
        super(BattleSessionFunctional, self).prb_onPlayerRosterChanged(pID, prevRoster, roster, actorID)
        events_dispatcher.updateUI()

    def __handleCarouselInited(self, _):
        events_dispatcher.addSpecBattleToCarousel(self.getPrbType())

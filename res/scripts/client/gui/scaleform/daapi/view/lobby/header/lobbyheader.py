# 2013.11.15 11:26:05 EST
# Embedded file name: scripts/client/gui/Scaleform/daapi/view/lobby/header/LobbyHeader.py
import datetime
import BigWorld
import constants
import account_helpers
from ConnectionManager import connectionManager
from CurrentVehicle import g_currentVehicle
from predefined_hosts import g_preDefinedHosts
from adisp import process, async
from PlayerEvents import g_playerEvents
from helpers.i18n import makeString
from helpers.links import openPaymentWebsite
from helpers.time_utils import makeLocalServerTime
from debug_utils import LOG_DEBUG, LOG_ERROR
from gui import makeHtmlString, GUI_SETTINGS, game_control, DialogsInterface
from gui.LobbyContext import g_lobbyContext
from gui.shared import events
from gui.Scaleform.daapi.view.meta.LobbyHeaderMeta import LobbyHeaderMeta
from gui.shared import g_itemsCache
from gui.shared.event_bus import EVENT_BUS_SCOPE
from gui.shared.events import StatsStorageEvent, ShowWindowEvent
from gui.shared.utils.HangarSpace import g_hangarSpace
from gui.shared.utils.requesters import StatsRequester
from gui.shared.utils.functions import makeTooltip
from gui.ClientUpdateManager import g_clientUpdateManager
from gui.Scaleform.Waiting import Waiting
from gui.Scaleform.daapi.settings.views import VIEW_ALIAS
from gui.Scaleform.framework import g_entitiesFactories, VIEW_TYPE, AppRef
from gui.Scaleform.framework.entities.DAAPIModule import DAAPIModule
from gui.Scaleform.managers.SoundEventManager import SoundEventManager

class LobbyHeader(LobbyHeaderMeta, DAAPIModule, AppRef):

    def __init__(self):
        super(LobbyHeader, self).__init__()
        self.eventSoundChecker = None
        self.currentInterface = VIEW_ALIAS.LOBBY_HANGAR
        self.__isSubscribe = False
        self.__statsCallbackID = None
        return

    def _populate(self):
        super(LobbyHeader, self)._populate()
        self.addListener(events.LobbySimpleEvent.UPDATE_TANK_PARAMS, self.__onUpdateTankParamsHandler, scope=EVENT_BUS_SCOPE.LOBBY)
        self.app.containerManager.onViewAddedToContainer += self.__onViewAddedToContainer
        self.as_setWalletStatusS(game_control.g_instance.wallet.componentsStatuses)
        self.addListener(events.FightButtonEvent.FIGHT_BUTTON_UPDATE, self.__updateRoamingCtrl, scope=EVENT_BUS_SCOPE.LOBBY)
        self.processLobby()

    def _dispose(self):
        super(LobbyHeader, self)._dispose()
        self._unsubscribe()
        self.removeListener(events.FightButtonEvent.FIGHT_BUTTON_UPDATE, self.__updateRoamingCtrl, scope=EVENT_BUS_SCOPE.LOBBY)
        if self.eventSoundChecker is not None:
            self.eventSoundChecker.cleanUp()
            self.eventSoundChecker = None
        if self.__statsCallbackID is not None:
            BigWorld.cancelCallback(self.__statsCallbackID)
            self.__statsCallbackID = None
        self.removeListener(events.LobbySimpleEvent.UPDATE_TANK_PARAMS, self.__onUpdateTankParamsHandler, scope=EVENT_BUS_SCOPE.LOBBY)
        self.app.containerManager.onViewAddedToContainer -= self.__onViewAddedToContainer
        return

    @process
    def processLobby(self):
        yield self.__populateData()
        self._subscribe()
        if constants.IS_SHOW_SERVER_STATS:
            self.__requestServerStats()
        self.updateAccountInfo()
        Waiting.hide('enter')

    @async
    def __populateData(self, callback):
        credits, gold = g_itemsCache.items.stats.actualMoney
        self.eventSoundChecker = SoundEventManager(credits, gold)
        callback(True)

    def _subscribe(self):
        if self.__isSubscribe:
            return
        self.__isSubscribe = True
        g_clientUpdateManager.addCallbacks({'stats.credits': self.setCredits,
         'stats.gold': self.setGold,
         'stats.freeXP': self.setFreeXP,
         'stats.clanInfo': self.setClanInfo,
         'stats.denunciationsLeft': self.setDenunciationsCount,
         'account': self.onAccountChanged,
         'stats.eliteVehicles': self.onVehicleBecomeElite})
        g_playerEvents.onServerStatsReceived += self.onStatsReceived
        game_control.g_instance.wallet.onWalletStatusChanged += self.onWalletChanged

    def _unsubscribe(self):
        if not self.__isSubscribe:
            return
        self.__isSubscribe = False
        game_control.g_instance.wallet.onWalletStatusChanged -= self.onWalletChanged
        g_playerEvents.onServerStatsReceived -= self.onStatsReceived
        g_clientUpdateManager.removeObjectCallbacks(self)

    def __requestServerStats(self):
        self.__statsCallbackID = None
        if hasattr(BigWorld.player(), 'requestServerStats'):
            BigWorld.player().requestServerStats()
        return

    @process
    def relogin(self, peripheryID):
        if g_preDefinedHosts.isRoamingPeriphery(peripheryID):
            success = yield DialogsInterface.showI18nConfirmDialog('changeRoamingPeriphery')
        else:
            success = yield DialogsInterface.showI18nConfirmDialog('changePeriphery')
        if success:
            game_control.g_instance.roaming.relogin(peripheryID)
        self.as_setPeripheryChangingS(success)

    def getServers(self):
        result = []
        predefined = tuple((host.url for host in g_preDefinedHosts.peripheries()))
        hosts = g_preDefinedHosts.peripheries()
        for h in g_preDefinedHosts.roamingHosts():
            if h.url not in predefined:
                hosts.append(h)

        for host in hosts:
            result.append({'label': host.name,
             'id': host.peripheryID,
             'selected': connectionManager.peripheryID == host.peripheryID})

        if connectionManager.peripheryID == 0:
            result.insert(0, {'label': connectionManager.serverUserName,
             'id': 0,
             'selected': True})
        return result

    def onStatsReceived(self, stats):
        if constants.IS_SHOW_SERVER_STATS:
            self.as_setServerStatsS(dict(stats))
            self.__statsCallbackID = BigWorld.callback(5, self.__requestServerStats)

    def updateAccountInfo(self):
        self.updateMoneyStats()
        self.updateXPInfo()
        self.updateClanInfo()
        self.updateAccountAttrs()
        self.setServerInfo()

    def updateMoneyStats(self):
        credits, gold = g_itemsCache.items.stats.actualMoney
        self.setCredits(credits)
        self.setGold(gold)

    @process
    def updateXPInfo(self):
        freeXP = yield StatsRequester().getFreeExperience()
        self.setFreeXP(freeXP)

    @process
    def updateClanInfo(self):
        clanInfo = yield StatsRequester().getClanInfo()
        self.setClanInfo(clanInfo)

    @process
    def updateAccountAttrs(self):
        accAttrs = yield StatsRequester().getAccountAttrs()
        denunciations = yield StatsRequester().getDenunciations()
        isPremium = account_helpers.isPremiumAccount(accAttrs)
        premiumExpiryTime = 0
        if isPremium:
            premiumExpiryTime = yield StatsRequester().getPremiumExpiryTime()
        self.setAccountsAttrs(accAttrs, premiumExpiryTime=premiumExpiryTime)
        self.setDenunciationsCount(denunciations)

    def setServerInfo(self):
        from ConnectionManager import connectionManager
        if connectionManager.serverUserName:
            tooltipBody = makeString('#tooltips:header/info/players_online_full/body')
            tooltipFullData = makeTooltip('#tooltips:header/info/players_online_full/header', tooltipBody % {'servername': connectionManager.serverUserName})
            serverName = makeHtmlString('html_templates:lobby/header', 'server-name', {'value': connectionManager.serverUserName})
            self.as_setServerInfoS(serverName, tooltipFullData)

    def setCredits(self, accCredits):
        self.as_creditsResponseS(BigWorld.wg_getIntegralFormat(accCredits))

    def setGold(self, gold):
        self.gold = gold
        self.as_goldResponseS(BigWorld.wg_getGoldFormat(gold))
        self.fireEvent(StatsStorageEvent(StatsStorageEvent.GOLD_RESPONSE, gold), EVENT_BUS_SCOPE.STATS)

    def setFreeXP(self, freeXP):
        self.freeXP = freeXP
        self.as_setFreeXPS(BigWorld.wg_getIntegralFormat(freeXP))

    @process
    def setClanInfo(self, clanInfo):
        name = BigWorld.player().name
        isTeamKiller = yield StatsRequester().isTeamKiller()
        clanDBID = yield StatsRequester().getClanDBID()
        self.as_nameResponseS(g_lobbyContext.getPlayerFullName(name, clanInfo=clanInfo), isTeamKiller, clanInfo is not None)
        if clanDBID is not None and clanDBID != 0:
            tID = 'clanInfo' + name
            success = yield StatsRequester().getClanEmblemTextureID(clanDBID, False, tID)
            if success:
                self.as_setClanEmblemS(tID)
        return

    def setDenunciationsCount(self, count):
        pass

    def setAccountsAttrs(self, attrs, premiumExpiryTime = 0):
        if not GUI_SETTINGS.goldTransfer and attrs & constants.ACCOUNT_ATTR.TRADING:
            attrs ^= constants.ACCOUNT_ATTR.TRADING
        isPremiumAccount = account_helpers.isPremiumAccount(attrs)
        if g_hangarSpace.inited:
            g_hangarSpace.refreshSpace(isPremiumAccount)
        self.as_setProfileTypeS(makeHtmlString('html_templates:lobby/header', 'premium-account-label' if isPremiumAccount else 'base-account-label'))
        if not (isPremiumAccount and premiumExpiryTime > 0):
            raise AssertionError
            lExpiryTime = makeLocalServerTime(premiumExpiryTime)
            delta = datetime.datetime.utcfromtimestamp(lExpiryTime) - datetime.datetime.utcnow()
            if delta.days > 0:
                timeLeft = delta.days + 1 if delta.seconds > 0 else delta.days
                timeMetric = makeString('#menu:header/account/premium/days')
            elif not delta.days:
                import math
                timeLeft = math.ceil(delta.seconds / 3600.0)
                timeMetric = makeString('#menu:header/account/premium/hours')
            else:
                LOG_ERROR('timedelta with negative days', premiumExpiryTime, delta)
                return
            self.as_setPremiumParamsS(makeHtmlString('html_templates:lobby/header', 'premium-time-label', {'timeMetric': timeMetric,
             'timeLeft': timeLeft}), makeString('#menu:common/premiumContinue'), delta.days > 360)
        self.as_premiumResponseS(isPremiumAccount)

    def onPayment(self):
        if constants.IS_VIETNAM:
            self.fireEvent(events.ShowWindowEvent(events.ShowWindowEvent.SHOW_EXCHANGE_VCOIN_WINDOW, {}), EVENT_BUS_SCOPE.LOBBY)
            return
        openPaymentWebsite()

    def showLobbyMenu(self):
        LOG_DEBUG('onEscape - firing "showLobbyMenu" event')
        self.fireEvent(events.ShowViewEvent(events.ShowViewEvent.SHOW_LOBBY_MENU), scope=EVENT_BUS_SCOPE.LOBBY)

    def menuItemClick(self, alias):
        self.currentInterface = alias
        self.__triggerViewLoad(self.currentInterface)

    def showExchangeWindow(self, initData):
        self.fireEvent(events.ShowWindowEvent(events.ShowWindowEvent.SHOW_EXCHANGE_WINDOW, {}), EVENT_BUS_SCOPE.LOBBY)

    def showExchangeXPWindow(self, initData):
        LOG_DEBUG('showExchangeXPWindow method called')
        self.fireEvent(events.ShowWindowEvent(events.ShowWindowEvent.SHOW_EXCHANGE_XP_WINDOW, {}), EVENT_BUS_SCOPE.LOBBY)

    def showPremiumDialog(self, event):
        self.fireEvent(events.ShowWindowEvent(events.ShowWindowEvent.SHOW_PREMIUM_DIALOG))

    def __onUpdateTankParamsHandler(self, event):
        self.__updateTankParams()

    def __setBattleQueue(self, event):
        self.as_doDisableNavigationS()

    def __updateTankParams(self):
        if g_currentVehicle.isPresent():
            self.as_setTankNameS(g_currentVehicle.item.userName)
            self.as_setTankTypeS(g_currentVehicle.item.type)
            self.as_setTankEliteS(g_currentVehicle.item.isElite)
        else:
            self.as_setTankNameS('')
            self.as_setTankTypeS('')
            self.as_setTankEliteS(False)

    def __triggerViewLoad(self, alias):
        if alias == 'browser':
            event = ShowWindowEvent(ShowWindowEvent.SHOW_BROWSER_WINDOW)
        else:
            event = g_entitiesFactories.makeLoadEvent(alias)
        if event is not None:
            self.fireEvent(event, scope=EVENT_BUS_SCOPE.LOBBY)
            self.as_setScreenS(alias)
        else:
            LOG_ERROR("Passed alias '{1}' is not listed in alias to event dictionary!".format(alias))
        return

    def onVehicleBecomeElite(self, eliteVehicles):
        if g_currentVehicle.isPresent():
            if g_currentVehicle.item.intCD in eliteVehicles:
                self.__updateTankParams()

    def onAccountChanged(self, args):
        if 'attrs' in args or 'premiumExpiryTime' in args:
            attrs = args.get('attrs', 0)
            expiryTime = args.get('premiumExpiryTime', 0)
            if expiryTime > 0:
                attrs |= constants.ACCOUNT_ATTR.PREMIUM
            self.setAccountsAttrs(attrs, premiumExpiryTime=expiryTime)

    def onWalletChanged(self, status):
        self.as_goldResponseS(BigWorld.wg_getGoldFormat(g_itemsCache.items.stats.actualGold))
        self.as_setFreeXPS(BigWorld.wg_getIntegralFormat(g_itemsCache.items.stats.actualFreeXP))
        self.as_setWalletStatusS(status)

    def __onViewAddedToContainer(self, _, pyEntity):
        settings = pyEntity.settings
        if settings.type is VIEW_TYPE.LOBBY_SUB:
            if settings.alias == VIEW_ALIAS.BATTLE_QUEUE:
                self.as_doDisableNavigationS()
            else:
                self.as_setScreenS(settings.alias)

    def __updateRoamingCtrl(self, event):
        from gui.prb_control.dispatcher import g_prbLoader
        dispatcher = g_prbLoader.getDispatcher()
        isRoamingCtrlDisabled = False
        if dispatcher:
            prbFunctional = dispatcher.getPrbFunctional()
            unitFunctional = dispatcher.getUnitFunctional()
            isRoamingCtrlDisabled = prbFunctional and prbFunctional.hasLockedState() or unitFunctional and unitFunctional.hasLockedState()
        self.as_disableRoamingDDS(isRoamingCtrlDisabled)
# okay decompyling res/scripts/client/gui/scaleform/daapi/view/lobby/header/lobbyheader.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:26:05 EST

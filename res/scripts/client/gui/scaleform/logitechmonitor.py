# Embedded file name: scripts/client/gui/Scaleform/LogitechMonitor.py
import BigWorld
import constants
import CommandMapping
from debug_utils import LOG_DEBUG
from gui.Scaleform.Flash import Flash
from adisp import process
from gui.BattleContext import g_battleContext
from gui.Scaleform.framework.entities.EventSystemEntity import EventSystemEntity
from gui.shared import EVENT_BUS_SCOPE, events
from gui.shared.utils.requesters import StatsRequester
from gui.shared.utils import dossiers_utils
from CurrentVehicle import g_currentVehicle
from helpers import i18n, isPlayerAccount
from gui.shared.utils.functions import getArenaSubTypeName
from messenger.m_constants import MESSENGER_SCOPE

class _LogitechFlash(Flash, EventSystemEntity):

    def __init__(self, isColored, width, height):
        swf = 'keyboard.swf' if isColored else 'keyboardMono.swf'
        Flash.__init__(self, swf)
        EventSystemEntity.__init__(self)
        self.movie.wg_outputToLogitechLcd = True
        self.addListener(events.ShowViewEvent.SHOW_LOGIN, self.__showLogoScreen, EVENT_BUS_SCOPE.GLOBAL)
        self.addListener(events.ShowViewEvent.SHOW_LOBBY, self.__showStatsScreen, EVENT_BUS_SCOPE.GLOBAL)
        self.addListener(events.LoadEvent.LOAD_BATTLE_LOADING, self.__showBattleLoadingScreen, EVENT_BUS_SCOPE.LOBBY)
        self.addListener(events.LoadEvent.LOAD_TUTORIAL_LOADING, self.__showBattleLoadingScreen, EVENT_BUS_SCOPE.LOBBY)

    def beforeDelete(self):
        if self.movie:
            self.movie.wg_outputToLogitechLcd = False
        self.removeListener(events.ShowViewEvent.SHOW_LOGIN, self.__showLogoScreen, EVENT_BUS_SCOPE.GLOBAL)
        self.removeListener(events.ShowViewEvent.SHOW_LOBBY, self.__showStatsScreen, EVENT_BUS_SCOPE.GLOBAL)
        self.removeListener(events.LoadEvent.LOAD_BATTLE_LOADING, self.__showBattleLoadingScreen, EVENT_BUS_SCOPE.LOBBY)
        self.removeListener(events.LoadEvent.LOAD_TUTORIAL_LOADING, self.__showBattleLoadingScreen, EVENT_BUS_SCOPE.LOBBY)
        super(_LogitechFlash, self).beforeDelete()

    def __showStatsScreen(self, event):
        LogitechMonitor.onScreenChange('hangar')

    def __showLogoScreen(self, event):
        LogitechMonitor.onScreenChange('login')

    def __showBattleLoadingScreen(self, event):
        LogitechMonitor.onScreenChange('battleloading')


class _LogitechScreen(object):

    def __init__(self, component, frame):
        self.uiHolder = component
        self.__frameLabel = frame

    def __del__(self):
        LOG_DEBUG('_LogitechScreen::destroy', self)

    def load(self, isColored):
        LOG_DEBUG('Logitech changeScreen: ', self.__frameLabel)
        self.uiHolder.call('logitech.gotoFrame', [self.__frameLabel])
        if not isColored:
            self.onLoadedMono()

    def onLoaded(self):
        pass

    def onLoadedMono(self):
        pass

    def destroy(self, isColored):
        if not isColored:
            self.onUnloadMono()
        self.uiHolder = None
        self.onUnload()
        return

    def onUnload(self):
        pass

    def onUnloadMono(self):
        pass

    def onChangeView(self):
        self.call('logitech.changeView', [])

    def call(self, methodName, args = None):
        self.uiHolder.call(methodName, args)


class _LogoScreen(_LogitechScreen):

    def __init__(self, component):
        _LogitechScreen.__init__(self, component, 'logo')

    def onLoadedMono(self):
        self.uiHolder.call('logitech.setMonoText', [i18n.makeString('#menu:login/version')])


class _StatsScreen(_LogitechScreen):

    def __init__(self, component):
        _LogitechScreen.__init__(self, component, 'stats')

    def onLoadedMono(self):
        self.onVehicleChange()
        g_currentVehicle.onChanged += self.onVehicleChange

    def onUnloadMono(self):
        g_currentVehicle.onChanged -= self.onVehicleChange

    def onVehicleChange(self):
        self.uiHolder.call('logitech.setMonoText', [g_currentVehicle.item.userName + '\r\n' + i18n.makeString(g_currentVehicle.getHangarMessage()[0])])

    @process
    def onLoaded(self):
        dossier = yield StatsRequester().getAccountDossier()
        self.call('logitech.setStatsData', dossiers_utils.getDossierTotalBlocksSummary(dossier, isCompact=True))


class _BattleLoadingScreen(_LogitechScreen):
    _MAP_SOURCE = '../maps/icons/map/screen/%s.png'

    def __init__(self, component):
        _LogitechScreen.__init__(self, component, 'mapLoading')

    def onLoaded(self):
        arena = getattr(BigWorld.player(), 'arena', None)
        if arena:
            self.call('logitech.setMap', [arena.arenaType.name, '#menu:loading/battleTypes/%d' % arena.guiType, self._MAP_SOURCE % arena.arenaType.geometryName])
        return


class _BattleScreen(_LogitechScreen):
    __viewCmds = ('CMD_CHAT_SHORTCUT_ATTACK', 'CMD_CHAT_SHORTCUT_BACKTOBASE', 'CMD_CHAT_SHORTCUT_FOLLOWME', 'CMD_CHAT_SHORTCUT_POSITIVE', 'CMD_CHAT_SHORTCUT_NEGATIVE', 'CMD_CHAT_SHORTCUT_HELPME', 'CMD_CHAT_SHORTCUT_ATTACK_MY_TARGET')
    __timerCallBackId = None
    __debugCallBackId = None

    def __init__(self, component):
        _LogitechScreen.__init__(self, component, 'battle')

    def onLoadedMono(self):
        self.onUpdateMono()

    def onUnloadMono(self):
        if self.__timerCallBackId:
            BigWorld.cancelCallback(self.__timerCallBackId)
            self.__timerCallBackId = None
        return

    def onUpdateMono(self):
        self.__timerCallBackId = None
        arena = BigWorld.player().arena
        if not g_battleContext.isInBattle or arena is None:
            return
        else:
            arenaLength = int(arena.periodEndTime - BigWorld.serverTime())
            arenaLength = arenaLength if arenaLength > 0 else 0
            allayFrags, enemyFrags, _, _ = self.getFrags()
            msg = '%s :%s\n%d :%d\n' % (i18n.makeString('#ingame_gui:player_messages/allied_team_name'),
             i18n.makeString('#ingame_gui:player_messages/enemy_team_name'),
             allayFrags,
             enemyFrags)
            if arena.period == constants.ARENA_PERIOD.BATTLE:
                m, s = divmod(arenaLength, 60)
                msg += '\n%s: %d :%02d' % (i18n.makeString('#ingame_gui:timer/battlePeriod'), m, s)
            self.uiHolder.call('logitech.setMonoText', [msg])
            self.__timerCallBackId = BigWorld.callback(1, self.onUpdateMono)
            return

    def onLoaded(self):
        _alliedTeamName = '#ingame_gui:player_messages/allied_team_name'
        _enemyTeamName = '#ingame_gui:player_messages/enemy_team_name'
        self.call('battle.fragCorrelationBar.setTeamNames', [_alliedTeamName, _enemyTeamName])
        arena = getattr(BigWorld.player(), 'arena', None)
        if not g_battleContext.isInBattle or arena is None:
            return
        else:
            self.__updateDebug()
            self.__onSetArenaTime()
            self.__updatePlayers()
            self.setCommands()
            arena.onPeriodChange += self.__onSetArenaTime
            arena.onNewVehicleListReceived += self.__updatePlayers
            arena.onNewStatisticsReceived += self.__updatePlayers
            arena.onVehicleAdded += self.__updatePlayers
            arena.onVehicleStatisticsUpdate += self.__updatePlayers
            arena.onVehicleKilled += self.__updatePlayers
            arena.onAvatarReady += self.__updatePlayers
            return

    def onUnload(self):
        arena = getattr(BigWorld.player(), 'arena', None)
        if not g_battleContext.isInBattle or arena is None:
            return
        else:
            arena.onPeriodChange -= self.__onSetArenaTime
            arena.onNewVehicleListReceived -= self.__updatePlayers
            arena.onNewStatisticsReceived -= self.__updatePlayers
            arena.onVehicleAdded -= self.__updatePlayers
            arena.onVehicleStatisticsUpdate -= self.__updatePlayers
            arena.onVehicleKilled -= self.__updatePlayers
            arena.onAvatarReady -= self.__updatePlayers
            if self.__timerCallBackId:
                BigWorld.cancelCallback(self.__timerCallBackId)
                self.__timerCallBackId = None
            if self.__debugCallBackId:
                BigWorld.cancelCallback(self.__debugCallBackId)
                self.__debugCallBackId = None
            _LogitechScreen.onUnload(self)
            return

    def __updatePlayers(self, *args):
        self.call('battle.fragCorrelationBar.updateFrags', list(self.getFrags()))

    def getFrags(self):
        arena = BigWorld.player().arena
        if not g_battleContext.isInBattle or arena is None:
            return
        else:
            vehicles = arena.vehicles
            frags = {1: 0,
             2: 0}
            total = {1: 0,
             2: 0}
            for vId, vData in vehicles.items():
                vStats = arena.statistics.get(vId, None)
                frags[vData['team']] += 0 if vStats is None else vStats['frags']
                total[vData['team']] += 1

            playerTeam = BigWorld.player().team
            enemyTeam = 3 - playerTeam
            return (frags[playerTeam],
             frags[enemyTeam],
             total[playerTeam],
             total[enemyTeam])

    def __onSetArenaTime(self, *args):
        self.__timerCallBackId = None
        arena = getattr(BigWorld.player(), 'arena', None)
        if not g_battleContext.isInBattle or arena is None:
            return
        else:
            arenaLength = int(arena.periodEndTime - BigWorld.serverTime())
            arenaLength = arenaLength if arenaLength > 0 else 0
            self.call('battle.timerBar.setTotalTime', [arenaLength])
            if arenaLength > 1:
                self.__timerCallBackId = BigWorld.callback(1, self.__onSetArenaTime)
            return

    def __updateDebug(self):
        self.__debugCallBackId = None
        player = BigWorld.player()
        if player is None or not hasattr(player, 'playerVehicleID'):
            return
        else:
            isLaggingNow = False
            ping = min(BigWorld.LatencyInfo().value[3] * 1000, 999)
            if ping < 999:
                ping = max(1, ping - 500.0 * constants.SERVER_TICK_LENGTH)
            fps = BigWorld.getFPS()[0]
            self.call('battle.debugBar.updateInfo', [int(fps), int(ping), isLaggingNow])
            self.__debugCallBackId = BigWorld.callback(0.01, self.__updateDebug)
            return

    def setCommands(self):
        cmdMap = CommandMapping.g_instance
        viewCmdMapping = []
        for command in self.__viewCmds:
            key = cmdMap.get(command)
            viewCmdMapping.append(command)
            viewCmdMapping.append(BigWorld.keyToString(key) if key is not None else 'NONE')

        self.call('battle.ingameHelp.setCommandMapping', viewCmdMapping)
        return


class _PostmortemScreen(_BattleScreen):

    def __init__(self, component):
        _LogitechScreen.__init__(self, component, 'postmortem')

    def load(self, isColored):
        _BattleScreen.load(self, isColored)
        if isColored:
            self.onLoaded()

    def setCommands(self):
        self.call('battle.ingameHelp.setCommandMapping', [])


class LogitechBattleMessenger(object):

    def __init__(self):
        self.messenger = None
        return

    def __del__(self):
        LOG_DEBUG('Deleted:', self)

    def create(self, uiHolder):
        from messenger.gui.Scaleform.BattleEntry import BattleEntry
        self.messenger = BattleEntry()
        self.messenger.show()
        self.messenger.invoke('populateUI', uiHolder)

    def destroy(self):
        self.messenger.close(MESSENGER_SCOPE.UNKNOWN)
        self.messenger.invoke('dispossessUI')
        self.messenger = None
        return


class LogitechMonitor(object):
    __component = None
    __screen = None
    __currentScreen = None
    __messenger = None
    __isColored = False
    SCREEN_TO_FRAME = {'login': _LogoScreen,
     'hangar': _StatsScreen,
     'battleloading': _BattleLoadingScreen,
     'battle': _BattleScreen,
     'postmortem': _PostmortemScreen}
    MESSENGER_IN_SCREEN = ['battle', 'postmortem']

    @staticmethod
    def init():
        LogitechMonitor.onScreenChange('login')
        import LcdKeyboard
        if LcdKeyboard._g_instance:
            LcdKeyboard._g_instance.changeNotifyCallback = LogitechMonitor.onChange
        LOG_DEBUG('LogitechMonitor is initialized')

    @staticmethod
    def onChange(isEnabled, isColored, width, height):
        if isEnabled:
            LogitechMonitor.destroy()
            LogitechMonitor.__isColored = isColored
            LogitechMonitor.__component = _LogitechFlash(isColored, width, height)
            LogitechMonitor.__component.addExternalCallback('logitech.frameLoaded', LogitechMonitor.onScreenLoaded)
            LOG_DEBUG('Logitech keyboard display found: colored = %s,  size = %sx%s' % (isColored, width, height))
            LogitechMonitor.onScreenChange()
        else:
            LogitechMonitor.destroy()
            LOG_DEBUG('No logitech keyboard color display found')

    @staticmethod
    def isPresent():
        return LogitechMonitor.__component is not None

    @staticmethod
    def isPresentColor():
        return LogitechMonitor.__isColored

    @staticmethod
    def destroy():
        LogitechMonitor.__isColored = False
        if LogitechMonitor.__screen:
            LogitechMonitor.__screen.destroy(LogitechMonitor.__isColored)
            LogitechMonitor.__screen = None
        if LogitechMonitor.__component:
            LogitechMonitor.__component.close()
            LogitechMonitor.__component = None
        if LogitechMonitor.__messenger:
            LogitechMonitor.__messenger.destroy()
            LogitechMonitor.__messenger = None
        LOG_DEBUG('LogitechMonitor is finalized')
        return

    @staticmethod
    def onScreenChange(currentScreen = None):
        if not currentScreen and isPlayerAccount():
            currentScreen = 'hangar'
        if currentScreen in LogitechMonitor.SCREEN_TO_FRAME.keys():
            LogitechMonitor.__currentScreen = currentScreen
        if LogitechMonitor.__component:
            screenClass = LogitechMonitor.SCREEN_TO_FRAME[LogitechMonitor.__currentScreen]
            if not isinstance(LogitechMonitor.__screen, screenClass):
                if LogitechMonitor.__screen:
                    LogitechMonitor.__screen.destroy(LogitechMonitor.__isColored)
                LogitechMonitor.__screen = screenClass(LogitechMonitor.__component)
            LogitechMonitor.__screen.load(LogitechMonitor.__isColored)
            LogitechMonitor.onSwitchMessenger(currentScreen)

    @staticmethod
    def onScreenLoaded(callBackID, screenLabel):
        if LogitechMonitor.__screen:
            LOG_DEBUG('LogitechMonitor::screen loaded:', screenLabel)
            LogitechMonitor.__screen.onLoaded()

    @staticmethod
    def onChangeView():
        if LogitechMonitor.__screen:
            LOG_DEBUG('LogitechMonitor::screen change view:')
            LogitechMonitor.__screen.onChangeView()

    @staticmethod
    def onSwitchMessenger(currentScreen):
        delegator = LogitechMonitor.__messenger
        if currentScreen in LogitechMonitor.MESSENGER_IN_SCREEN:
            if delegator is None:
                delegator = LogitechBattleMessenger()
                delegator.create(LogitechMonitor.__screen.uiHolder)
                LogitechMonitor.__messenger = delegator
        elif delegator is not None:
            delegator.destroy()
            LogitechMonitor.__messenger = None
        return
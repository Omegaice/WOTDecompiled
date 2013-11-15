# 2013.11.15 11:25:47 EST
# Embedded file name: scripts/client/gui/Scaleform/Battle.py
import math
import weakref
import BigWorld
import ResMgr
import FMOD
import GUI
import Math
import SoundGroups
import Vehicle
from chat_shared import USERS_ROSTER_VOICE_MUTED
import constants
import BattleReplay
import CommandMapping
from account_helpers.AccountSettings import AccountSettings
from account_helpers.SettingsCore import g_settingsCore
from dossiers2.custom.records import DB_ID_TO_RECORD
from dossiers2.ui.achievements import BATTLE_HERO_TEXTS as heroesTexts
from gui.prb_control.formatters import getPrebattleFullDescription
from messenger import MessengerEntry, g_settings
from messenger.proto.events import g_messengerEvents
from messenger.storage import storage_getter
import nations
from windows import BattleWindow
from SettingsInterface import SettingsInterface
from debug_utils import LOG_CURRENT_EXCEPTION, LOG_DEBUG, LOG_ERROR, LOG_CODEPOINT_WARNING
from helpers import i18n, html, isPlayerAvatar
from helpers.i18n import makeString
from PlayerEvents import g_playerEvents
from MemoryCriticalController import g_critMemHandler
from items.vehicles import NUM_EQUIPMENT_SLOTS, VEHICLE_CLASS_TAGS
from gui import DEPTH_OF_Battle, DEPTH_OF_VehicleMarker, TANKMEN_ROLES_ORDER_DICT, GUI_SETTINGS, g_tankActiveCamouflage, g_guiResetters, g_repeatKeyHandlers, makeHtmlString, game_control
from gui.BattleContext import g_battleContext, PLAYER_ENTITY_NAME
from gui.Scaleform import VehicleActions, VoiceChatInterface, ColorSchemeManager
from gui.Scaleform.SoundManager import SoundManager
from gui.shared.utils.sound import Sound
from gui.shared.utils.functions import getBattleSubTypeBaseNumder, isControlPointExists
from gui.Scaleform.Flash import Flash
from gui.Scaleform.windows import UIInterface
from gui.Scaleform.MovingText import MovingText
from gui.Scaleform.Minimap import Minimap
from gui.Scaleform.RadialMenu import RadialMenu
from gui.Scaleform.CursorDelegator import g_cursorDelegator
from gui.Scaleform.ingame_help import IngameHelp
from gui.shared.gui_items.Vehicle import VEHICLE_BATTLE_TYPES_ORDER_INDICES
from gui.Scaleform import SCALEFORM_SWF_PATH
_CONTOUR_ICONS_MASK = '../maps/icons/vehicle/contour/%(unicName)s.png'
_BASE_CAPTURE_SOUND_NAME_ENEMY = '/GUI/notifications_FX/base_capture_2'
_BASE_CAPTURE_SOUND_NAME_ALLY = '/GUI/notifications_FX/base_capture_1'
_BATTLE_START_NOTIFICATION_TIME = 5.0

class Battle(BattleWindow):
    PLAYERS_PANEL_LENGTH = 15
    teamBasesPanel = property(lambda self: self.__teamBasesPanel)
    consumablesPanel = property(lambda self: self.__consumablesPanel)
    damagePanel = property(lambda self: self.__damagePanel)
    vMarkersManager = property(lambda self: self.__vMarkersManager)
    vErrorsPanel = property(lambda self: self.__vErrorsPanel)
    vMsgsPanel = property(lambda self: self.__vMsgsPanel)
    pMsgsPanel = property(lambda self: self.__pMsgsPanel)
    minimap = property(lambda self: self.__minimap)
    radialMenu = property(lambda self: self.__radialMenu)
    damageInfoPanel = property(lambda self: self.__damageInfoPanel)
    VEHICLE_DESTROY_TIMER = {'ALL': 'all',
     constants.VEHICLE_MISC_STATUS.VEHICLE_DROWN_WARNING: 'drown',
     constants.VEHICLE_MISC_STATUS.VEHICLE_IS_OVERTURNED: 'overturn',
     constants.VEHICLE_MISC_STATUS.IN_DEATH_ZONE: 'death_zone'}
    DENUNCIATIONS = {'bot': constants.DENUNCIATION.BOT,
     'flood': constants.DENUNCIATION.FLOOD,
     'offend': constants.DENUNCIATION.OFFEND,
     'notFairPlay': constants.DENUNCIATION.NOT_FAIR_PLAY,
     'teamKill': constants.DENUNCIATION.TEAMKILL,
     'allyEjection': constants.DENUNCIATION.ALLY_EJECTION,
     'openingOfAllyPos': constants.DENUNCIATION.OPENING_OF_ALLY_POS}
    _speakPlayers = {}
    __cameraVehicleID = -1

    def __init__(self):
        self.__soundManager = None
        self.__timerCallBackId = None
        self.__vehicles = {}
        self.__arena = BigWorld.player().arena
        self.__playersPanelStateChanged = False
        self.__battleNotificationExecuted = False
        BattleWindow.__init__(self, 'battle.swf')
        self.__timerSound = Sound('/GUI/notifications_FX/timer')
        self.__isTimerVisible = False
        self.component.wg_inputKeyMode = 1
        self.component.position.z = DEPTH_OF_Battle
        self.movie.backgroundAlpha = 0
        self.addFsCallbacks({'battle.leave': self.onExitBattle})
        self.addExternalCallbacks({'battle.showCursor': self.cursorVisibility,
         'Battle.UsersRoster.Appeal': self.onDenunciationReceived,
         'Battle.playersPanelStateChange': self.onPlayersPanelStateChange,
         'Battle.selectPlayer': self.selectPlayer})
        BigWorld.wg_setRedefineKeysMode(False)
        self.onPostmortemVehicleChanged(BigWorld.player().playerVehicleID)
        return

    @storage_getter('users')
    def usersStorage(self):
        return None

    def showAll(self, isShow):
        self.call('battle.showAll', [isShow])
        self.__vMarkersManager.active(isShow)

    def showCursor(self, isShow):
        self.cursorVisibility(-1, isShow)

    def onPlayersPanelStateChange(self, cid, state):
        ppSettings = dict(AccountSettings.getSettings('players_panel'))
        ppSettings['state'] = state
        AccountSettings.setSettings('players_panel', ppSettings)
        self.__playersPanelStateChanged = True

    @property
    def soundManager(self):
        return self.__soundManager

    def selectPlayer(self, cid, vehId):
        player = BigWorld.player()
        if isPlayerAvatar():
            player.selectPlayer(int(vehId))

    def onDenunciationReceived(self, cid, uid, userName, topic):
        topicID = self.DENUNCIATIONS.get(topic)
        if topicID is not None:
            self.__makeDenunciation(uid, userName, topicID)
        return

    def __makeDenunciation(self, uid, userName, topicID):
        player = BigWorld.player()
        violatorKind = constants.VIOLATOR_KIND.UNKNOWN
        for id, p in player.arena.vehicles.iteritems():
            if p['accountDBID'] == uid:
                violatorKind = constants.VIOLATOR_KIND.ALLY if player.team == p['team'] else constants.VIOLATOR_KIND.ENEMY

        player.makeDenunciation(uid, topicID, violatorKind)
        self.__updatePlayers()
        topicStr = makeString('#menu:denunciation/%d' % topicID)
        message = makeString('#system_messages:denunciation/success') % {'name': userName,
         'topic': topicStr}
        MessengerEntry.g_instance.gui.addClientMessage(g_settings.htmlTemplates.format('battleErrorMessage', ctx={'error': message}))

    def onPostmortemVehicleChanged(self, id):
        if self.__cameraVehicleID == id:
            return
        else:
            self.__cameraVehicleID = id
            self.__setPlayerInfo(id)
            self.__updatePlayers()
            self.__damagePanel.switchToVehicle(id)
            self.hideVehicleTimer('ALL')
            self.vErrorsPanel.clear()
            self.vMsgsPanel.clear()
            aim = BigWorld.player().inputHandler.aim
            if aim is not None:
                aim.updateAmmoState(True)
            BigWorld.player().soundNotifications.clear()
            vehicle = BigWorld.entities[id]
            if isinstance(vehicle, Vehicle.Vehicle):
                nationId = vehicle.typeDescriptor.type.id[0]
                SoundGroups.g_instance.soundModes.setCurrentNation(nations.NAMES[nationId])
            return

    def onCameraChanged(self, cameraMode, curVehID = None):
        LOG_DEBUG('onCameraChanged', cameraMode, curVehID)
        self.damagePanel.showAll(cameraMode != 'video')

        def setVisible(cname):
            m = self.getMember(cname)
            if m is not None:
                m.visible = cameraMode != 'video'
            return

        setVisible('vehicleMessagesPanel')
        setVisible('vehicleErrorsPanel')
        if cameraMode == 'video':
            self.__cameraVehicleID = -1
            self.damagePanel._reset()
            self.vErrorsPanel.clear()
            self.vMsgsPanel.clear()
            self.hideVehicleTimer('ALL')
            aim = BigWorld.player().inputHandler.aim
            if aim is not None:
                aim.updateAmmoState(True)
        aim = BigWorld.player().inputHandler.aim
        if aim is not None:
            aim.onCameraChange()
        return

    def showVehicleTimer(self, code, time, warnLvl = 'critical'):
        LOG_DEBUG('show vehicles destroy timer', code, time, warnLvl)
        self.call('destroyTimer.show', [self.VEHICLE_DESTROY_TIMER[code], time, warnLvl])

    def hideVehicleTimer(self, code):
        LOG_DEBUG('hide vehicles destroy timer', code)
        self.call('destroyTimer.hide', [self.VEHICLE_DESTROY_TIMER[code]])

    def showSixthSenseIndicator(self, isShow):
        self.call('sixthSenseIndicator.show', [isShow])

    def speakingPlayersReset(self):
        for id in self._speakPlayers.keys():
            self.setPlayerSpeaking(id, False)

        self._speakPlayers.clear()

    def setVisible(self, bool):
        LOG_DEBUG('[Battle] visible', bool)
        self.component.visible = bool

    def afterCreate(self):
        player = BigWorld.player()
        LOG_DEBUG('[Battle] afterCreate')
        setattr(self.movie, '_global.wg_isShowLanguageBar', GUI_SETTINGS.isShowLanguageBar)
        setattr(self.movie, '_global.wg_isShowVoiceChat', GUI_SETTINGS.voiceChat)
        setattr(self.movie, '_global.wg_voiceChatProvider', VoiceChatInterface.g_instance.voiceChatProvider)
        setattr(self.movie, '_global.wg_isChina', constants.IS_CHINA)
        setattr(self.movie, '_global.wg_isKorea', constants.IS_KOREA)
        BattleWindow.afterCreate(self)
        g_playerEvents.onBattleResultsReceived += self.__showFinalStatsResults
        g_messengerEvents.users.onUsersRosterReceived += self.__updatePlayers
        g_messengerEvents.users.onUserRosterChanged += self.__updatePlayers
        BigWorld.wg_setScreenshotNotifyCallback(self.__screenshotNotifyCallback)
        player.inputHandler.onPostmortemVehicleChanged += self.onPostmortemVehicleChanged
        player.inputHandler.onCameraChanged += self.onCameraChanged
        g_settingsCore.onSettingsChanged += self.__accs_onSettingsChanged
        if self.__arena:
            self.__arena.onPeriodChange += self.__onSetArenaTime
            self.__arena.onNewVehicleListReceived += self.__updatePlayers
            self.__arena.onNewStatisticsReceived += self.__updatePlayers
            self.__arena.onVehicleAdded += self.__updatePlayers
            self.__arena.onVehicleStatisticsUpdate += self.__updatePlayers
            self.__arena.onVehicleKilled += self.__updatePlayers
            self.__arena.onAvatarReady += self.__updatePlayers
            self.__arena.onTeamKiller += self.__onTeamKiller
            self.__arena.onVehicleUpdated += self.__updatePlayers
        self.proxy = weakref.proxy(self)
        self._speakPlayers.clear()
        VoiceChatInterface.g_instance.populateUI(self.proxy)
        self.colorManager = ColorSchemeManager._ColorSchemeManager()
        self.colorManager.populateUI(self.proxy)
        self.movingText = MovingText()
        self.movingText.populateUI(self.proxy)
        self.__settingsInterface = SettingsInterface()
        self.__settingsInterface.populateUI(self.proxy)
        self.__soundManager = SoundManager()
        self.__soundManager.populateUI(self.proxy)
        self.__teamBasesPanel = TeamBasesPanel(self.proxy)
        self.__fragCorrelation = FragCorrelationPanel(self.proxy)
        self.__debugPanel = DebugPanel(self.proxy)
        self.__consumablesPanel = ConsumablesPanel(self.proxy)
        self.__damagePanel = DamagePanel(self.proxy)
        self.__vMarkersManager = VehicleMarkersManager(self.proxy)
        self.__ingameHelp = IngameHelp(self.proxy)
        self.__minimap = Minimap(self.proxy)
        self.__radialMenu = RadialMenu(self.proxy)
        self.isVehicleCountersVisible = g_settingsCore.getSetting('showVehiclesCounter')
        self.__fragCorrelation.showVehiclesCounter(self.isVehicleCountersVisible)
        self.__damageInfoPanel = VehicleDamageInfoPanel(self.proxy)
        isColorBlind = AccountSettings.getSettings('isColorBlind')
        self.__vErrorsPanel = FadingMessagesPanel(self.proxy, 'VehicleErrorsPanel', 'gui/vehicle_errors_panel.xml', isColorBlind=isColorBlind)
        self.__vMsgsPanel = FadingMessagesPanel(self.proxy, 'VehicleMessagesPanel', 'gui/vehicle_messages_panel.xml', isColorBlind=isColorBlind)
        self.__pMsgsPanel = FadingMessagesPanel(self.proxy, 'PlayerMessagesPanel', 'gui/player_messages_panel.xml', isColorBlind=isColorBlind)
        self.__teamBasesPanel.start()
        self.__debugPanel.start()
        self.__consumablesPanel.start()
        self.__damagePanel.start()
        self.__ingameHelp.start()
        self.__vErrorsPanel.start()
        self.__vMsgsPanel.start()
        self.__pMsgsPanel.start()
        self.__vMarkersManager.start()
        self.__vMarkersManager.setMarkerDuration(GUI_SETTINGS.markerHitSplashDuration)
        markers = {'enemy': g_settingsCore.getSetting('enemy'),
         'dead': g_settingsCore.getSetting('dead'),
         'ally': g_settingsCore.getSetting('ally')}
        self.__vMarkersManager.setMarkerSettings(markers)
        self.__initMemoryCriticalHandlers()
        MessengerEntry.g_instance.gui.invoke('populateUI', self.proxy)
        g_guiResetters.add(self.__onRecreateDevice)
        g_repeatKeyHandlers.add(self.component.handleKeyEvent)
        self.__onRecreateDevice()
        self.__setPlayerInfo(player.playerVehicleID)
        self.__updatePlayers()
        self.__populateData()
        self.__minimap.start()
        self.__radialMenu.setSettings(self.__settingsInterface)
        self.__radialMenu.populateUI(self.proxy)
        BigWorld.callback(1, self.__setArenaTime)
        self.updateFlagsColor()
        VoiceChatInterface.g_instance.onVoiceChatInitFailed += self.onVoiceChatInitFailed
        self.movie.setFocussed(SCALEFORM_SWF_PATH)
        if self.__arena.period == constants.ARENA_PERIOD.BATTLE:
            self.call('players_panel.setState', [AccountSettings.getSettings('players_panel')['state']])
        else:
            self.call('players_panel.setState', ['large'])
        self.call('sixthSenseIndicator.setDuration', [GUI_SETTINGS.sixthSenseDuration])
        g_tankActiveCamouflage[player.vehicleTypeDescriptor.type.compactDescr] = self.__arena.arenaType.vehicleCamouflageKind
        if BattleReplay.g_replayCtrl.isPlaying:
            BattleReplay.g_replayCtrl.onBattleSwfLoaded()
        player.battleMessages.onShowPlayerMessage += self.onShowPlayerMessage
        player.battleMessages.onShowVehicleMessage += self.onShowVehicleMessage

    def beforeDelete(self):
        LOG_DEBUG('[Battle] beforeDelete')
        if self.colorManager:
            self.colorManager.dispossessUI()
        if VoiceChatInterface.g_instance:
            VoiceChatInterface.g_instance.dispossessUI(self.proxy)
        self.__destroyMemoryCriticalHandlers()
        if self.movingText is not None:
            self.movingText.dispossessUI()
            self.movingText = None
        if self.__soundManager is not None:
            self.__soundManager.dispossessUI()
            self.__soundManager = None
        if self.colorManager is not None:
            self.colorManager.dispossessUI()
            self.colorManager = None
        if self.component:
            g_repeatKeyHandlers.discard(self.component.handleKeyEvent)
        g_settingsCore.onSettingsChanged -= self.__accs_onSettingsChanged
        self.__teamBasesPanel.destroy()
        self.__debugPanel.destroy()
        self.__consumablesPanel.destroy()
        self.__damagePanel.destroy()
        self.__vMarkersManager.destroy()
        self.__ingameHelp.destroy()
        self.__vErrorsPanel.destroy()
        self.__vMsgsPanel.destroy()
        self.__pMsgsPanel.destroy()
        self.__radialMenu.destroy()
        self.__minimap.destroy()
        self.__timerSound.stop()
        MessengerEntry.g_instance.gui.invoke('dispossessUI')
        g_playerEvents.onBattleResultsReceived -= self.__showFinalStatsResults
        g_messengerEvents.users.onUsersRosterReceived -= self.__updatePlayers
        g_messengerEvents.users.onUserRosterChanged -= self.__updatePlayers
        if self.__arena:
            self.__arena.onPeriodChange -= self.__onSetArenaTime
            self.__arena.onNewVehicleListReceived -= self.__updatePlayers
            self.__arena.onNewStatisticsReceived -= self.__updatePlayers
            self.__arena.onVehicleAdded -= self.__updatePlayers
            self.__arena.onVehicleStatisticsUpdate -= self.__updatePlayers
            self.__arena.onVehicleKilled -= self.__updatePlayers
            self.__arena.onAvatarReady -= self.__updatePlayers
            self.__arena.onTeamKiller -= self.__onTeamKiller
            self.__arena.onVehicleUpdated -= self.__updatePlayers
        self.__arena = None
        g_guiResetters.discard(self.__onRecreateDevice)
        self.__settingsInterface.dispossessUI()
        self.__settingsInterface = None
        VoiceChatInterface.g_instance.onVoiceChatInitFailed -= self.onVoiceChatInitFailed
        BattleWindow.beforeDelete(self)
        return

    def __screenshotNotifyCallback(self, path):
        self.vMsgsPanel.showMessage('SCREENSHOT_CREATED', {'path': path.encode('utf-8')})

    def onVoiceChatInitFailed(self):
        if GUI_SETTINGS.voiceChat:
            self.call('VoiceChat.initFailed', [])

    def onShowPlayerMessage(self, code, postfix, targetID, attackerID):
        targetInfo = self.__arena.vehicles.get(targetID)
        attackerInfo = self.__arena.vehicles.get(attackerID)
        LOG_DEBUG('onShowPlayerMessage', code, postfix, targetID, attackerID)
        self.pMsgsPanel.showMessage(code, {'target': g_battleContext.getFullPlayerName(targetInfo, showClan=False),
         'attacker': g_battleContext.getFullPlayerName(attackerInfo, showClan=False)}, extra=(('target', targetID), ('attacker', attackerID)), postfix=postfix)

    def onShowVehicleMessage(self, code, postfix, entityID, extra):
        LOG_DEBUG('onShowVehicleMessage', code, postfix, entityID, extra)
        names = {'device': '',
         'entity': '',
         'target': ''}
        if extra is not None:
            names['device'] = extra.deviceUserString
        if entityID:
            targetInfo = self.__arena.vehicles.get(entityID)
            if targetInfo is None:
                LOG_CODEPOINT_WARNING()
                return
            names['entity'] = g_battleContext.getFullPlayerName(targetInfo)
        self.vMsgsPanel.showMessage(code, names, postfix=postfix)
        return

    def clearCommands(self):
        pass

    def bindCommands(self):
        self.__consumablesPanel.bindCommands()
        self.__ingameHelp.buildCmdMapping()

    def updateFlagsColor(self):
        isColorBlind = AccountSettings.getSettings('isColorBlind')
        colorGreen = self.colorManager.getSubScheme('flag_team_green', isColorBlind=isColorBlind)['rgba']
        colorRed = self.colorManager.getSubScheme('flag_team_red', isColorBlind=isColorBlind)['rgba']
        if 1 == BigWorld.player().team:
            BigWorld.wg_setFlagColor(1, colorGreen / 255)
            BigWorld.wg_setFlagColor(2, colorRed / 255)
        else:
            BigWorld.wg_setFlagColor(2, colorGreen / 255)
            BigWorld.wg_setFlagColor(1, colorRed / 255)
        BigWorld.wg_setFlagEmblem(0, 'system/maps/wg_emblem.dds', Math.Vector4(0.0, 0.1, 0.5, 0.9))
        BigWorld.wg_setFlagEmblem(1, 'system/maps/wg_emblem.dds', Math.Vector4(0.0, 0.1, 0.5, 0.9))
        BigWorld.wg_setFlagEmblem(2, 'system/maps/wg_emblem.dds', Math.Vector4(0.0, 0.1, 0.5, 0.9))

    def setPlayerSpeaking(self, accountDBID, flag):
        if not GUI_SETTINGS.voiceChat:
            return
        self._speakPlayers[accountDBID] = flag
        self.__callEx('setPlayerSpeaking', [accountDBID, flag])
        vID = g_battleContext.getVehIDByAccDBID(accountDBID)
        if vID > 0:
            self.__vMarkersManager.showDynamic(vID, flag)

    def isPlayerSpeaking(self, accountDBID):
        if GUI_SETTINGS.voiceChat:
            return self._speakPlayers.get(accountDBID, False)
        else:
            return False

    def showPostmortemTips(self):
        if self.radialMenu is not None:
            self.radialMenu.forcedHide()
        if not g_battleContext.isPlayerObserver():
            self.__callEx('showPostmortemTips', [1.0, 5.0, 1.0])
        return

    def cursorVisibility(self, callbackId, visible, x = None, y = None, customCall = False, enableAiming = True):
        if visible:
            g_cursorDelegator.syncMousePosition(self, x, y, customCall)
        else:
            g_cursorDelegator.restoreMousePosition()
        if BigWorld.player() is not None and isPlayerAvatar():
            BigWorld.player().setForcedGuiControlMode(visible, False, enableAiming)
        return

    def onExitBattle(self, arg):
        arena = getattr(BigWorld.player(), 'arena', None)
        LOG_DEBUG('onExitBattle', arena)
        if arena:
            BigWorld.player().leaveArena()
        return

    def __setPlayerInfo(self, vID):
        playerName, vTypeName = ('', '')
        vInfo = self.__arena.vehicles.get(vID)
        if vInfo is not None:
            playerName = g_battleContext.getFullPlayerName(vInfo, showVehShortName=False, showClan=False)
            vTypeName = vInfo['vehicleType'].type.userString
        self.__callEx('setPlayerInfo', [playerName, vTypeName])
        return

    def __populateData(self):
        from gui.shared.utils.functions import getBattleSubTypeWinText, getArenaSubTypeName, isBaseExists
        arena = getattr(BigWorld.player(), 'arena', None)
        arenaData = ['',
         0,
         '',
         '',
         '']
        if arena:
            arenaData = [arena.arenaType.name]
            descExtra = getPrebattleFullDescription(arena.extraData or {})
            arenaSubType = getArenaSubTypeName(BigWorld.player().arenaTypeID)
            if descExtra:
                arenaData.extend([arena.guiType + 1, descExtra])
            elif arena.guiType == constants.ARENA_GUI_TYPE.RANDOM:
                arenaTypeName = '#arenas:type/%s/name' % arenaSubType
                if arenaSubType == 'assault':
                    arenaSubType += '1' if isBaseExists(BigWorld.player().arenaTypeID, BigWorld.player().team) else '2'
                arenaData.extend([arenaSubType, arenaTypeName])
            else:
                arenaData.extend([arena.guiType + 1, '#menu:loading/battleTypes/%d' % arena.guiType])
            extraData = arena.extraData or {}
            myTeam = BigWorld.player().team
            team1 = extraData.get('opponents', {}).get('%s' % myTeam, {}).get('name', '#menu:loading/team1')
            team2 = extraData.get('opponents', {}).get('2' if myTeam == 1 else '1', {}).get('name', '#menu:loading/team2')
            arenaData.extend([team1, team2])
            teamHasBase = 1 if isBaseExists(BigWorld.player().arenaTypeID, myTeam) else 2
            winText = getBattleSubTypeWinText(BigWorld.player().arenaTypeID, teamHasBase)
            arenaData.append(winText)
        self.__callEx('arenaData', arenaData)
        return

    def __updatePlayers(self, *args):
        stat = {1: [],
         2: []}
        teams = {1: [],
         2: []}
        squads = {1: {},
         2: {}}
        player = BigWorld.player()
        if player is None or not isPlayerAvatar():
            return
        elif self.__arena is None:
            return
        else:
            vehicles = self.__arena.vehicles
            userGetter = self.usersStorage.getUser
            for vId, vData in vehicles.items():
                if g_battleContext.isObserver(vId) and g_battleContext.isPlayerObserver():
                    continue
                team = vData['team']
                dbID = vData['accountDBID']
                user = userGetter(dbID)
                if user:
                    roster = user.getRoster()
                    isMuted = roster & USERS_ROSTER_VOICE_MUTED != 0
                else:
                    roster = 0
                    isMuted = False
                if vData['name'] is not None:
                    name = g_battleContext.getFullPlayerName(vData, showVehShortName=False)
                else:
                    name = makeString('#ingame_gui:players_panel/unknown_name')
                if vData['vehicleType'] is not None:
                    vName = vData['vehicleType'].type.userString
                    vShortName = vData['vehicleType'].type.shortUserString
                    vIcon = _CONTOUR_ICONS_MASK % {'unicName': vData['vehicleType'].type.name.replace(':', '-')}
                    vType = set(VEHICLE_CLASS_TAGS.intersection(vData['vehicleType'].type.tags)).pop()
                    vLevel = vData['vehicleType'].level
                    classSet = VEHICLE_CLASS_TAGS & vData['vehicleType'].type.tags
                    classTag = list(classSet)[0]
                else:
                    vName = vShortName = makeString('#ingame_gui:players_panel/unknown_vehicle')
                    vIcon = _CONTOUR_ICONS_MASK % {'unicName': 'unknown'}
                    classTag = 'unknown'
                    vType = 100
                    vLevel = -1
                isAlive = vData['isAlive']
                isAvatarReady = vData['isAvatarReady']
                vState = 0
                if isAlive:
                    vState |= 1
                if isAvatarReady:
                    vState |= 2
                if isAlive is None or isAvatarReady is None:
                    vState = 4
                if vData['prebattleID'] > 0:
                    if vData['prebattleID'] not in squads[team].keys():
                        squads[team][vData['prebattleID']] = 1
                    else:
                        squads[team][vData['prebattleID']] += 1
                vStats = self.__arena.statistics.get(vId, None)
                frags = 0 if vStats is None else vStats['frags']
                if vData['clanAbbrev']:
                    userDisplayName = name + '[%s]' % vData['clanAbbrev']
                else:
                    userDisplayName = name
                self.__vehicles.update({vId: (userDisplayName, vName)})
                vehActions = VehicleActions.getBitMask(vData.get('events', {}))
                if not g_battleContext.isObserver(vId):
                    teams[team].append([vId, classTag, vData['isAlive']])
                if vData['igrType'] != constants.IGR_TYPE.NONE:
                    igrLabel = makeHtmlString('html_templates:battle/players_list', 'igr_name_label')
                else:
                    igrLabel = ''
                roamingCtrl = game_control.g_instance.roaming
                disableCtxMenu = not roamingCtrl.isInRoaming() and not roamingCtrl.isPlayerInRoaming(dbID)
                stat[team].append([name,
                 vIcon,
                 vShortName,
                 vState,
                 frags,
                 vId,
                 vData['prebattleID'],
                 vData['clanAbbrev'],
                 VoiceChatInterface.g_instance.isPlayerSpeaking(vData['accountDBID']),
                 dbID,
                 roster,
                 isMuted,
                 0,
                 False,
                 vData['isTeamKiller'],
                 vLevel,
                 vehActions,
                 not isAlive,
                 vType,
                 vData['igrType'],
                 igrLabel,
                 disableCtxMenu])

            squadsSorted = {1: sorted(squads[1].iteritems(), cmp=lambda x, y: cmp(x[0], y[0])),
             2: sorted(squads[2].iteritems(), cmp=lambda x, y: cmp(x[0], y[0]))}
            squadsFiltered = {1: [ id for id, num in squadsSorted[1] if 1 < num < 4 and self.__arena.guiType == constants.ARENA_GUI_TYPE.RANDOM ],
             2: [ id for id, num in squadsSorted[2] if 1 < num < 4 and self.__arena.guiType == constants.ARENA_GUI_TYPE.RANDOM ]}
            teamFrags = [0, 0]
            for team in (1, 2):
                value = ['team%d' % team,
                 -1,
                 -1,
                 BigWorld.player().denunciationsLeft,
                 AccountSettings.getSettings('isColorBlind'),
                 None]
                data = sorted(stat[team], cmp=_playerComparator)
                for item in data:
                    teamFrags[team - 1] += item[4]
                    sNumber = squadsFiltered[team].index(item[6]) + 1 if item[6] in squadsFiltered[team] else 0
                    item[6] = sNumber
                    if item[5] == player.playerVehicleID and item[6] > 0:
                        value[2] = item[6]
                    value.extend(item[:-7])
                    if team != player.team:
                        value[-1] = False
                    value.append(self.__cameraVehicleID == item[5])
                    value.append(item[15] if g_settingsCore.getSetting('ppShowLevels') else 0)
                    value.append(item[16])
                    value.append(item[5])
                    value.append(item[19] != constants.IGR_TYPE.NONE)
                    value.append(item[20])
                    value.append(item[21])

                if team == player.team:
                    value[1] = player.playerVehicleID
                self.__callEx('setTeam', value)

            playerTeam = player.team - 1
            enemyTeam = 1 - playerTeam
            self.__fragCorrelation.updateFrags(teamFrags[playerTeam], teamFrags[enemyTeam])
            if self.isVehicleCountersVisible:
                sortedList = sorted(teams[playerTeam + 1], cmp=_markerComparator)
                self.__fragCorrelation.updatePlayerTeam([ pos for item in sortedList for pos in item ])
                sortedList = sorted(teams[enemyTeam + 1], cmp=_markerComparator)
                self.__fragCorrelation.updateEnemyTeam([ pos for item in sortedList for pos in item ])
            return

    def __showFinalStatsResults(self, isActiveVehicle, results):
        if isActiveVehicle:
            if GUI_SETTINGS.battleStatsInHangar:
                if self.__arena:
                    g_battleContext.lastArenaUniqueID = self.__arena.arenaUniqueID
                self.onExitBattle(None)
            else:
                if not self.__vehicles:
                    self.__updatePlayers()
                if results['killerID']:
                    killer = makeString('#ingame_gui:statistics/final/lifeInfo/dead', '%s (%s)' % self.__vehicles.get(results['killerID'], ('n/a', 'n/a')))
                else:
                    killer = makeString('#ingame_gui:statistics/final/lifeInfo/alive')
                isMultipliedXP = int(results['factors']['dailyXPFactor10'] / 10.0) > 1 and results['xp'] > 0
                stats = [results['xp'],
                 results['credits'],
                 results['repair'],
                 isMultipliedXP,
                 i18n.makeString('#ingame_gui:statistics/final/stats/multipliedExp') % int(results['factors']['dailyXPFactor10'] / 10.0) if isMultipliedXP else i18n.makeString('#ingame_gui:statistics/final/stats/experience'),
                 self.__vehicles.get(BigWorld.player().playerVehicleID, ('n/a', 'n/a'))[0],
                 killer]
                results['damaged'] = list(set(results['damaged']).difference(set(results['killed'])))
                for key in ('killed', 'damaged', 'spotted'):
                    lt = set()
                    for id in results[key]:
                        lt.add('%s (%s)' % self.__vehicles.get(id, ('n/a', 'n/a')))

                    stats.append(len(lt))
                    stats.extend(lt)

                hl = set()
                if results.has_key('achieveIndices'):
                    for i, heroId in enumerate(results['achieveIndices']):
                        herolist = [makeString(heroesTexts[DB_ID_TO_RECORD[heroId][1]])]
                        if results.has_key('heroVehicleIDs') and len(results['heroVehicleIDs']) > i:
                            if self.__arena.vehicles.get(results['heroVehicleIDs'][i], False):
                                if not self.__arena.vehicles[results['heroVehicleIDs'][i]]['isAlive']:
                                    herolist[0] += ' ' + makeString('#ingame_gui:statistics/final/personal/postmortem')
                            herolist.extend(self.__vehicles.get(results['heroVehicleIDs'][i], ('n/a', 'n/a')))
                            hl.add('%s - %s (%s)' % tuple(herolist))

                stats.append(len(hl))
                stats.extend(hl)
                for key in ('shots', 'hits', 'shotsReceived'):
                    stats.append(makeString('#ingame_gui:statistics/final/personal/' + key, results[key]))

                for key in ('capturePoints', 'droppedCapturePoints'):
                    stats.append(makeString('#ingame_gui:statistics/final/personal/' + key, min(results[key], 100)))

                self.__callEx('showFinalStatistic', stats)
        return

    def __showFinalStats(self, winnerTeam, reason):
        if hasattr(BigWorld.player(), 'team'):
            status = 'tie' if winnerTeam == 0 else ('win' if winnerTeam == BigWorld.player().team else 'lose')
            status = makeString('#menu:finalStatistic/commonStats/resultlabel/%s' % status)
            self.__callEx('showStatus', [status])

    def __hideTimer(self):
        self.__callEx('showBattleTimer', [False])

    def __onSetArenaTime(self, *args):
        if self.__timerCallBackId is not None:
            BigWorld.cancelCallback(self.__timerCallBackId)
        self.__setArenaTime()
        return

    def __setArenaTime(self):
        self.__timerCallBackId = None
        if self.__arena is None:
            return
        else:
            replayCtrl = BattleReplay.g_replayCtrl
            if replayCtrl.isPlaying:
                period = replayCtrl.getArenaPeriod()
                arenaLength = int(replayCtrl.getArenaLength())
                if period == 0:
                    self.__timerCallBackId = BigWorld.callback(1, self.__setArenaTime)
                    return
            else:
                period = self.__arena.period
                arenaLength = int(self.__arena.periodEndTime - BigWorld.serverTime())
                if period == constants.ARENA_PERIOD.PREBATTLE:
                    if arenaLength <= _BATTLE_START_NOTIFICATION_TIME and not self.__battleNotificationExecuted:
                        BigWorld.WGWindowsNotifier.onBattleBeginning()
                        self.__battleNotificationExecuted = True
                else:
                    self.__battleNotificationExecuted = False
                arenaLength = arenaLength if arenaLength > 0 else 0
                if replayCtrl.isRecording:
                    replayCtrl.setArenaPeriod(period)
                    replayCtrl.setArenaLength(arenaLength)
            if period != constants.ARENA_PERIOD.AFTERBATTLE:
                self.__callEx('timerBar.setTotalTime', [arenaLength])
            if period == constants.ARENA_PERIOD.WAITING:
                self.__callEx('timerBig.setTimer', [makeString('#ingame_gui:timer/waiting')])
                self.__isTimerVisible = True
            elif period == constants.ARENA_PERIOD.PREBATTLE:
                self.__callEx('timerBig.setTimer', [makeString('#ingame_gui:timer/starting'), arenaLength])
                self.__isTimerVisible = True
                if not self.__timerSound.isPlaying and not replayCtrl.isPlaying:
                    self.__timerSound.play()
            elif period == constants.ARENA_PERIOD.BATTLE and self.__isTimerVisible:
                self.__isTimerVisible = False
                self.__timerSound.stop()
                self.__callEx('timerBig.setTimer', [makeString('#ingame_gui:timer/started')])
                self.__callEx('timerBig.hide')
                if not self.__playersPanelStateChanged:
                    self.call('players_panel.setState', [AccountSettings.getSettings('players_panel')['state']])
            elif period == constants.ARENA_PERIOD.AFTERBATTLE:
                self.__hideTimer()
                self.consumablesPanel._isOptDeviceEnabled = False
            if arenaLength > 1 or replayCtrl.isPlaying:
                self.__timerCallBackId = BigWorld.callback(1.0 if not replayCtrl.isPlaying else 0.0, self.__setArenaTime)
            return

    def __onTeamKiller(self, vID):
        self.__updatePlayers(vID)
        self.__vMarkersManager.setTeamKiller(vID)

    def __onRecreateDevice(self):
        self.call('Stage.Update', list(GUI.screenResolution()))

    def __callEx(self, funcName, args = None):
        self.call('battle.' + funcName, args)

    def __initMemoryCriticalHandlers(self):
        for message in g_critMemHandler.messages:
            self.__onMemoryCritical(message)

        g_critMemHandler.onMemCrit += self.__onMemoryCritical

    def __destroyMemoryCriticalHandlers(self):
        g_critMemHandler.onMemCrit -= self.__onMemoryCritical

    def __onMemoryCritical(self, message):
        self.__vMsgsPanel.showMessage(message[1])

    def __accs_onSettingsChanged(self, diff):
        self.colorManager.update()
        if 'isColorBlind' in diff:
            isColorBlind = diff['isColorBlind']
            self.__vErrorsPanel.defineColorFlags(isColorBlind=isColorBlind)
            self.__vMsgsPanel.defineColorFlags(isColorBlind=isColorBlind)
            self.__pMsgsPanel.defineColorFlags(isColorBlind=isColorBlind)
            self.updateFlagsColor()
            self.__vMarkersManager.updateMarkers()
            self.__minimap.updateEntries()
        if 'enemy' in diff or 'dead' in diff or 'ally' in diff:
            markers = {'enemy': g_settingsCore.getSetting('enemy'),
             'dead': g_settingsCore.getSetting('dead'),
             'ally': g_settingsCore.getSetting('ally')}
            self.vMarkersManager.setMarkerSettings(markers)
            self.__vMarkersManager.updateMarkerSettings()
        if 'showVehiclesCounter' in diff:
            self.isVehicleCountersVisible = diff['showVehiclesCounter']
            self.__fragCorrelation.showVehiclesCounter(self.isVehicleCountersVisible)
        self.__updatePlayers()

    def __getEntityUserString(self, entityName):
        player = BigWorld.player()
        if player and player.isVehicleAlive:
            extra = player.vehicleTypeDescriptor.extrasDict.get(entityName + 'Health')
            if extra is None:
                return entityName
            return extra.deviceUserString
        else:
            return

    def _showTankmanIsSafeMessage(self, entityName):
        if not self.__consumablesPanel.hasMedkit():
            return
        tankman = self.__getEntityUserString(entityName)
        if tankman:
            self.__vErrorsPanel.showMessage('medkitTankmanIsSafe', {'entity': tankman})

    def _showDeviceIsNotDamagedMessage(self, entityName):
        if not self.__consumablesPanel.hasRepairkit():
            return
        if entityName == 'chassis':
            device = i18n.makeString('#ingame_gui:devices/chassis')
        else:
            device = self.__getEntityUserString(entityName)
        if device:
            self.__vErrorsPanel.showMessage('repairkitDeviceIsNotDamaged', {'entity': device})


class TeamBasesPanel(object):
    __settings = {0: {'weight': 2,
         'color': 'red',
         'capturing': i18n.makeString('#ingame_gui:player_messages/ally_base_captured_by_notification'),
         'captured': i18n.makeString('#ingame_gui:player_messages/ally_base_captured_notification')},
     3: {'weight': 1,
         'color': 'green',
         'capturing': i18n.makeString('#ingame_gui:player_messages/enemy_base_captured_by_notification'),
         'captured': i18n.makeString('#ingame_gui:player_messages/enemy_base_captured_notification')},
     'controlPoint': {'weight': {0: 4,
                                 3: 3},
                      'color': {0: 'red',
                                3: 'green'},
                      'capturing': i18n.makeString('#ingame_gui:player_messages/base_captured_by_notification'),
                      'captured': i18n.makeString('#ingame_gui:player_messages/base_captured_notification')}}

    def __init__(self, parentUI):
        self.__ui = parentUI
        self.__captureSounds = {}
        self.__baseIds = set()

    def start(self):
        LOG_DEBUG('TeamBasesPanel.start')
        arena = BigWorld.player().arena
        arena.onTeamBasePointsUpdate += self.__onTeamBasePointsUpdate
        arena.onTeamBaseCaptured += self.__onTeamBaseCaptured
        arena.onPeriodChange += self.__onPeriodChange

    def destroy(self):
        LOG_DEBUG('TeamBasesPanel.destroy')
        arena = getattr(BigWorld.player(), 'arena', None)
        if arena is not None:
            arena.onTeamBasePointsUpdate -= self.__onTeamBasePointsUpdate
            arena.onTeamBaseCaptured -= self.__onTeamBaseCaptured
            arena.onPeriodChange -= self.__onPeriodChange
        self.__stopCaptureSound()
        return

    def _getID(self, team, baseID):
        if baseID is None:
            baseID = 0
        return (int(baseID) << 2) + team

    def _hasBaseId(self, team, exclude = -1):
        return len(filter(lambda i: i & team != 0 and i != exclude, self.__baseIds)) > 0

    def __onTeamBasePointsUpdate(self, team, baseID, points, capturingStopped):
        if team not in (1, 2):
            return
        id = self._getID(team, baseID)
        if not points:
            if id in self.__baseIds:
                self.__baseIds.remove(id)
                self.__callFlash('remove', [id])
                if not self._hasBaseId(team) or team ^ BigWorld.player().team:
                    self.__stopCaptureSound(team)
        else:
            if id in self.__baseIds:
                self.__callFlash('stop' if capturingStopped else 'updatePoints', [id, points])
            else:
                self.__baseIds.add(id)
                key = team ^ BigWorld.player().team
                if isControlPointExists(BigWorld.player().arenaTypeID):
                    settings = self.__settings.get('controlPoint', {})
                    color = settings.get('color', {}).get(key, 'green')
                    weight = settings.get('weight', {}).get(key, 0)
                else:
                    settings = self.__settings.get(key, {})
                    color = settings.get('color', 'green')
                    weight = settings.get('weight', 0)
                capturingString = settings.get('capturing', '') % getBattleSubTypeBaseNumder(BigWorld.player().arenaTypeID, team, baseID)
                self.__callFlash('add', [id,
                 weight,
                 color,
                 capturingString,
                 points])
                if capturingStopped:
                    self.__callFlash('stop', [id, points])
            if not capturingStopped:
                self.__playCaptureSound(team)
            elif not self._hasBaseId(team, exclude=id) or team ^ BigWorld.player().team:
                self.__stopCaptureSound(team)

    def __onTeamBaseCaptured(self, team, baseID):
        if team not in (1, 2):
            return
        id = self._getID(team, baseID)
        if isControlPointExists(BigWorld.player().arenaTypeID):
            settings = self.__settings.get('controlPoint', {})
            color = settings.get('color', {}).get(team ^ BigWorld.player().team, 'green')
        else:
            settings = self.__settings.get(team ^ BigWorld.player().team, {})
            color = settings.get('color', 'green')
        if id in self.__baseIds:
            self.__callFlash('setCaptured', [id, settings.get('captured', '') % getBattleSubTypeBaseNumder(BigWorld.player().arenaTypeID, team, baseID)])
        else:
            self.__baseIds.add(id)
            self.__callFlash('add', [id,
             color,
             settings.get('weight', 0),
             settings.get('captured', '') % getBattleSubTypeBaseNumder(BigWorld.player().arenaTypeID, team, baseID),
             100])
        self.__stopCaptureSound(team)

    def __onPeriodChange(self, period, *args):
        if period != constants.ARENA_PERIOD.AFTERBATTLE:
            return
        self.__callFlash('clear', [])
        self.__stopCaptureSound()

    def __callFlash(self, funcName, args):
        self.__ui.call('battle.teamBasesPanel.{0:>s}'.format(funcName), args)

    def __playCaptureSound(self, team):
        arena = getattr(BigWorld.player(), 'arena', None)
        if arena is not None and arena.period == constants.ARENA_PERIOD.AFTERBATTLE:
            return
        else:
            snd = self.__captureSounds.get(team)
            if snd is None:
                try:
                    isAllyTeam = True if team == BigWorld.player().team else False
                    if isAllyTeam:
                        snd = FMOD.playSound(_BASE_CAPTURE_SOUND_NAME_ALLY)
                        self.__captureSounds[team] = snd
                except Exception:
                    LOG_CURRENT_EXCEPTION()

            return

    def __stopCaptureSound(self, team = None):
        if team is None:
            for t in self.__captureSounds.keys():
                self.__stopCaptureSound(t)

        else:
            snd = self.__captureSounds.get(team)
            if snd is not None:
                try:
                    snd.stop()
                except Exception:
                    LOG_CURRENT_EXCEPTION()

                del self.__captureSounds[team]
        return


class VehicleDamageInfoPanel(object):

    def __init__(self, parent):
        self.parent = parent
        self.isShown = False

    def show(self, vehicleID, damagedExtras = [], destroyedExtras = []):
        if vehicleID not in BigWorld.player().arena.vehicles or not BigWorld.player().arena.vehicles[vehicleID].has_key('vehicleType'):
            return
        extras = BigWorld.player().arena.vehicles[vehicleID]['vehicleType'].extras
        isFire = False
        itemsList = []
        for i, id in enumerate(damagedExtras):
            if extras[id].name == 'fire':
                isFire = True
                continue
            itemsList.append({'name': extras[id].name,
             'userName': extras[id].deviceUserString,
             'state': 'damaged'})

        for i, id in enumerate(destroyedExtras):
            itemsList.append({'name': extras[id].name,
             'userName': extras[id].deviceUserString,
             'state': 'destroyed'})

        self.parent.movie.showDamageInfoPanel(vehicleID, itemsList, isFire)
        self.isShown = True

    def hide(self):
        if not self.isShown:
            return
        self.parent.movie.hideDamageInfoPanel()
        self.isShown = False


class FragCorrelationPanel(object):

    def __init__(self, parentUI):
        self.__ui = parentUI
        playerTeamIdx = BigWorld.player().team
        _alliedTeamName = g_battleContext.getTeamName(playerTeamIdx, True)
        _enemyTeamName = g_battleContext.getTeamName(playerTeamIdx, False)
        self.__callFlash('setTeamNames', [_alliedTeamName, _enemyTeamName])
        self.showVehiclesCounter(AccountSettings.getSettings('showVehiclesCounter'))

    def updateFrags(self, alliedFrags, enemyFrags):
        self.__callFlash('updateFrags', [alliedFrags, enemyFrags])

    def updatePlayerTeam(self, team):
        self.__callFlash('updatePlayerTeam', team)

    def updateEnemyTeam(self, team):
        self.__callFlash('updateEnemyTeam', team)

    def showVehiclesCounter(self, isShown):
        self.__callFlash('showVehiclesCounter', [isShown])

    def __callFlash(self, funcName, args):
        self.__ui.call('battle.fragCorrelationBar.' + funcName, args)


class DebugPanel(UIInterface):
    __UPDATE_INTERVAL = 0.01

    def __init__(self, parentUI):
        UIInterface.__init__(self)
        self.__ui = parentUI
        self.__timeInterval = None
        self.__performanceStats = _PerformanceStats()
        self.__performanceStats.populateUI(parentUI)
        return

    def start(self):
        self.__timeInterval = _TimeInterval(self.__UPDATE_INTERVAL, '_DebugPanel__update', weakref.proxy(self))
        self.__timeInterval.start()
        self.__update()

    def destroy(self):
        self.__performanceStats.disposeUI()
        self.__performanceStats = None
        self.__timeInterval.stop()
        return

    def __update(self):
        player = BigWorld.player()
        if player is None or not hasattr(player, 'playerVehicleID'):
            return
        else:
            fps = 0
            recordedFps = -1
            ping = 0
            isLaggingNow = False
            replayCtrl = BattleReplay.g_replayCtrl
            if replayCtrl.isPlaying and replayCtrl.fps > 0:
                fps = BigWorld.getFPS()[1]
                recordedFps = replayCtrl.fps
                ping = replayCtrl.ping
                isLaggingNow = replayCtrl.isLaggingNow
            else:
                isLaggingNow = player.filter.isLaggingNow
                if not isLaggingNow:
                    for v in BigWorld.entities.values():
                        if isinstance(v, Vehicle.Vehicle):
                            if v.isAlive() and isinstance(v.filter, BigWorld.WGVehicleFilter) and v.filter.isLaggingNow:
                                isLaggingNow = True
                                break

                ping = min(BigWorld.LatencyInfo().value[3] * 1000, 999)
                if ping < 999:
                    ping = max(1, ping - 500.0 * constants.SERVER_TICK_LENGTH)
                fps = BigWorld.getFPS()[1]
                if replayCtrl.isRecording:
                    replayCtrl.setFpsPingLag(fps, ping, isLaggingNow)
            self.__performanceStats.updateDebugInfo(int(fps), int(ping), isLaggingNow, int(recordedFps))
            return


class _PerformanceStats(UIInterface):

    def __init__(self):
        UIInterface.__init__(self)
        self.flashObject = None
        return

    def populateUI(self, proxy):
        UIInterface.populateUI(self, proxy)
        self.flashObject = self.uiHolder.getMember('_level0.debugPanel')
        self.flashObject.script = self

    def updateDebugInfo(self, fps, ping, lag, fpsReplay):
        if fpsReplay != 0 and fpsReplay != -1:
            fps = '{0}({1})'.format(fpsReplay, fps)
        else:
            fps = str(fps)
        ping = str(ping)
        self.flashObject.as_updateDebugInfo(fps, ping, lag)

    def disposeUI(self):
        self.flashObject.script = None
        self.flashObject = None
        return


class ConsumablesPanel(object):
    __supportedTags = set(('medkit', 'repairkit', 'stimulator', 'trigger', 'fuel', 'extinguisher'))
    __orderSets = {'medkit': TANKMEN_ROLES_ORDER_DICT['enum'],
     'repairkit': ('engine', 'ammoBay', 'gun', 'turretRotator', 'chassis', 'surveyingDevice', 'radio', 'fuelTank')}
    __mergedEntities = {'chassis': ('leftTrack', 'rightTrack')}
    _SHELL_ICON_PATH = '../maps/icons/ammopanel/ammo/%s'
    _NO_SHELL_ICON_PATH = '../maps/icons/ammopanel/ammo/NO_%s'
    _COMMAND_MAPPING_KEY_MASK = 'CMD_AMMO_CHOICE_%d'
    _START_EQUIPMENT_SLOT_IDX = 3

    def __init__(self, parentUI):
        self.__ui = parentUI
        self.__ui.addExternalCallbacks({'battle.consumablesPanel.onClickToSlot': self.onClickToSlot,
         'battle.consumablesPanel.onCollapseEquipment': self.onCollapseEquipment})
        self.__shellKCMap = {}
        self.__equipmentKCMap = {}
        self.__equipmentTagsByIdx = {}
        self.__entitiesKCMap = {}
        self.__expandEquipmentIdx = None
        self.__processedInfo = None
        self.__emptyEquipmentSlotCount = 0
        self._isOptDeviceEnabled = False
        self.__disableTurretRotator = not vehicleHasTurretRotator(BigWorld.player().vehicleTypeDescriptor)
        return

    def start(self):
        self._isOptDeviceEnabled = True
        replayCtrl = BattleReplay.g_replayCtrl
        if replayCtrl.isPlaying and replayCtrl.replayContainsGunReloads:
            self.__cbIdSetCooldown = BigWorld.callback(0.0, self.setCooldownFromReplay)
        else:
            self.__cbIdSetCooldown = None
        return

    def destroy(self):
        self._isOptDeviceEnabled = False
        if self.__cbIdSetCooldown is not None:
            BigWorld.cancelCallback(self.__cbIdSetCooldown)
            self.__cbIdSetCooldown = None
        self.__ui = None
        return

    def setItemQuantityInSlot(self, idx, quantity):
        if self.__equipmentTagsByIdx.has_key(idx):
            self.__equipmentTagsByIdx[idx][1] = quantity
        self.__callFlash('setItemQuantityInSlot', [idx, quantity])

    def setCoolDownTime(self, idx, timeRemaining):
        replayCtrl = BattleReplay.g_replayCtrl
        if replayCtrl.isPlaying and idx <= 2 and replayCtrl.replayContainsGunReloads:
            return
        else:
            if replayCtrl.isRecording and idx is not None:
                replayCtrl.setConsumableSlotCooldown(idx, timeRemaining, True)
            self.__callFlash('setCoolDownTime', [idx, timeRemaining])
            return

    def setCoolDownPosAsPercent(self, idx, percent):
        self.__callFlash('setCoolDownPosAsPercent', [idx, percent])

    def setCooldownFromReplay(self):
        player = BigWorld.player()
        if isPlayerAvatar():
            for idx in xrange(0, 3):
                self.setCoolDownPosAsPercent(idx, 100.0 * BattleReplay.g_replayCtrl.getConsumableSlotCooldownAmount(idx))

        self.__cbIdSetCooldown = BigWorld.callback(0.0, self.setCooldownFromReplay)

    def setDisabled(self, currentShellIdx):
        self.setCoolDownTime(currentShellIdx, 0)
        self.setCurrentShell(-1)
        self.setNextShell(-1)
        if self.__expandEquipmentIdx is not None:
            self.collapseEquipmentSlot(self.__expandEquipmentIdx)
        return

    def __getKey(self, idx):
        if not -1 < idx < 10:
            raise AssertionError
            cmdMappingKey = self._COMMAND_MAPPING_KEY_MASK % (idx + 1) if idx < 9 else 0
            keyCode = CommandMapping.g_instance.get(cmdMappingKey)
            keyChr = ''
            keyChr = keyCode is not None and keyCode != 0 and BigWorld.keyToString(keyCode)
        return (keyCode, keyChr)

    def bindCommands(self):
        shellKCMap = {}
        for idx in self.__shellKCMap.values():
            keyCode, keyChr = self.__getKey(idx)
            shellKCMap[keyCode] = idx
            self.__callFlash('setKeyToSlot', [idx, keyCode, keyChr])

        self.__shellKCMap = shellKCMap
        equipmentKCMap = {}
        for idx in self.__equipmentKCMap.values():
            keyCode, keyChr = self.__getKey(idx)
            equipmentKCMap[keyCode] = idx
            self.__callFlash('setKeyToSlot', [idx, keyCode, keyChr])

        self.__equipmentKCMap = equipmentKCMap

    def setShellQuantityInSlot(self, idx, quantity, quantityInClip):
        if self.__equipmentTagsByIdx.has_key(idx):
            self.__equipmentTagsByIdx[idx][1] = quantity
        self.__callFlash('setShellQuantityInSlot', [idx, quantity, quantityInClip])

    def addShellSlot(self, idx, quantity, quantityInClip, clipCapacity, shellDescr, piercingPower):
        kind = shellDescr['kind']
        icon = shellDescr['icon'][0]
        toolTip = i18n.convert(i18n.makeString('#ingame_gui:shells_kinds/{0:>s}'.format(kind), caliber=shellDescr['caliber'], userString=shellDescr['userString'], damage=str(int(shellDescr['damage'][0])), piercingPower=str(int(piercingPower[0]))))
        shellIconPath = self._SHELL_ICON_PATH % icon
        noShellIconPath = self._NO_SHELL_ICON_PATH % icon
        keyCode, keyChr = self.__getKey(idx)
        self.__shellKCMap[keyCode] = idx
        self.__callFlash('addShellSlot', [idx,
         keyCode,
         keyChr,
         quantity,
         quantityInClip,
         clipCapacity,
         shellIconPath,
         noShellIconPath,
         toolTip])

    def setCurrentShell(self, idx):
        self.__callFlash('setCurrentShell', [idx])

    def setNextShell(self, idx):
        self.__callFlash('setNextShell', [idx])

    def hasMedkit(self):
        for tagName, quantity in self.__equipmentTagsByIdx.values():
            if tagName == 'medkit':
                return quantity > 0

        return False

    def hasRepairkit(self):
        for tagName, quantity in self.__equipmentTagsByIdx.values():
            if tagName == 'repairkit':
                return quantity > 0

        return False

    def checkEquipmentSlotIdx(self, idx):
        return max(self._START_EQUIPMENT_SLOT_IDX, idx)

    def addEquipmentSlot(self, idx, quantity, equipmentDescr):
        tags = self.__supportedTags & equipmentDescr.tags
        tagName = None
        if len(tags) == 1:
            tagName = tags.pop()
        iconPath = equipmentDescr.icon[0]
        toolTip = '{0:>s}\n{1:>s}'.format(equipmentDescr.userString, equipmentDescr.description)
        keyCode, keyChr = (None, None)
        if tagName:
            keyCode, keyChr = self.__getKey(idx)
            self.__equipmentKCMap[keyCode] = idx
            self.__equipmentTagsByIdx[idx] = [tagName, quantity]
        self.__callFlash('addEquipmentSlot', [idx,
         keyCode,
         keyChr,
         tagName,
         quantity,
         iconPath,
         toolTip])
        return

    def addEmptyEquipmentSlot(self, idx):
        self.__emptyEquipmentSlotCount += 1
        toolTip = i18n.makeString('#ingame_gui:consumables_panel/equipment/tooltip/empty')
        self.__callFlash('addEquipmentSlot', [idx,
         None,
         None,
         None,
         0,
         None,
         toolTip])
        if self.__emptyEquipmentSlotCount == NUM_EQUIPMENT_SLOTS:
            self.__callFlash('showEquipmentSlots', [False])
        return

    def expandEquipmentSlot(self, idx, tagName, entityStates):
        orderSet = self.__orderSets.get(tagName)
        if orderSet is None:
            if constants.IS_DEVELOPMENT:
                LOG_ERROR('Order set not determine for tag %s' % tagName)
            return
        else:
            self.__expandEquipmentIdx = idx
            self.__processedInfo = (tagName, entityStates)
            args = self.__buildEntitiesInfoList(idx, tagName, entityStates, orderSet)
            self.__callFlash('expandEquipmentSlot', args)
            return

    def updateExpandedEquipmentSlot(self, entityName, entityState):
        if self.__expandEquipmentIdx and self.__processedInfo:
            tagName, entityStates = self.__processedInfo
            if entityStates.has_key(entityName):
                entityStates[entityName] = entityState if entityState != 'repaired' else 'critical'
                self.__processedInfo = (tagName, entityStates)
                idx = self.__expandEquipmentIdx
                orderSet = self.__orderSets[tagName]
                args = self.__buildEntitiesInfoList(idx, tagName, entityStates, orderSet)
                self.__callFlash('updateExpandedEquipmentSlot', args)

    def collapseEquipmentSlot(self, idx):
        self.__callFlash('collapseEquipmentSlot', [idx])

    def __buildEntitiesInfoList(self, idx, tagName, entityStates, orderSet):
        args = [idx, tagName]
        for entityIdx, entityName in enumerate(orderSet):
            entityState, disabled = None, True
            keyCode, keyChr = self.__getKey(entityIdx)
            if self.__mergedEntities.has_key(entityName):
                realName = None
                for name in self.__mergedEntities[entityName]:
                    state = entityStates.get(name, None)
                    disabled &= not entityStates.has_key(name)
                    if realName is None and state == 'critical':
                        realName = name
                        entityState = 'critical'
                    elif state == 'destroyed':
                        realName = name
                        entityState = 'destroyed'
                        break

                if realName is not None:
                    self.__entitiesKCMap[keyCode] = (realName, False)
                else:
                    self.__entitiesKCMap[keyCode] = (entityName, True)
            elif entityStates.has_key(entityName):
                entityState = entityStates[entityName]
                if entityName == 'turretRotator':
                    disabled = self.__disableTurretRotator
                    self.__entitiesKCMap[keyCode] = disabled or (entityName, entityState not in ('destroyed', 'critical'))
            args.extend([keyCode,
             keyChr,
             entityName,
             entityState,
             disabled])

        return args

    def __removeExpandEquipment(self, idx):
        if idx == self.__expandEquipmentIdx:
            self.__expandEquipmentIdx = None
            self.__processedInfo = None
            self.__entitiesKCMap.clear()
        return

    def addOptionalDevice(self, idx, deviceDescr):
        iconPath = deviceDescr.icon[0]
        toolTip = '{0:>s}\n{1:>s}'.format(deviceDescr.userString, deviceDescr.description)
        self.__callFlash('addOptionalDeviceSlot', [idx, iconPath, toolTip])

    def setOptionalDeviceState(self, idx, isOn):
        if self._isOptDeviceEnabled:
            self.setCoolDownTime(idx, -1 if isOn else 0)

    def handleKey(self, key):
        replayCtrl = BattleReplay.g_replayCtrl
        if replayCtrl.isPlaying:
            return
        elif self.__expandEquipmentIdx is not None:
            if key in self.__entitiesKCMap.keys():
                slotIdx = self.__expandEquipmentIdx
                devName, isNormal = self.__entitiesKCMap[key]
                if not isNormal:
                    self.collapseEquipmentSlot(slotIdx)
                    BigWorld.player().onEquipmentButtonPressed(slotIdx, deviceName=devName)
                else:
                    if self.__processedInfo is None:
                        LOG_ERROR("Can't determine equipment tag", slotIdx, devName)
                        return
                    tagName, _ = self.__processedInfo
                    if tagName == 'medkit':
                        self.__ui._showTankmanIsSafeMessage(devName)
                    elif tagName == 'repairkit':
                        self.__ui._showDeviceIsNotDamagedMessage(devName)
                    else:
                        LOG_ERROR("Can't determine message for tag", tagName)
            return
        else:
            if key in self.__shellKCMap.keys():
                BigWorld.player().onAmmoButtonPressed(self.__shellKCMap[key])
            elif key in self.__equipmentKCMap.keys():
                BigWorld.player().onEquipmentButtonPressed(self.__equipmentKCMap[key])
            return

    def onClickToSlot(self, _, keyCode):
        self.handleKey(int(keyCode))

    def onCollapseEquipment(self, _, idx):
        self.__removeExpandEquipment(int(idx))

    def __callFlash(self, funcName, args = None):
        self.__ui.call('battle.consumablesPanel.%s' % funcName, args)


class DamagePanel():
    _WAITING_INTERVAL = 0.05
    _UPDATING_INTERVAL = 0.03

    def __init__(self, parentUI):
        self.__ui = parentUI
        self.__hasYawLimits = False
        self.__vID = 0
        self.__speed = 0.0
        self.__health = 0
        self.__waitingTI = _TimeInterval(self._WAITING_INTERVAL, '_waiting', weakref.proxy(self))
        self.__updateTI = _TimeInterval(self._UPDATING_INTERVAL, '_updateSelf', weakref.proxy(self))
        self.__tankIndicator = _TankIndicatorCtrl(self.__ui)
        self.__otherVehiclesModules = {'critical': {},
         'destroyed': {}}
        self.__ui.addExternalCallbacks({'battle.damagePanel.onClickToDeviceIcon': self.__onClickToDeviceIcon,
         'battle.damagePanel.onClickToTankmenIcon': self.__onClickToTankmenIcon})

    def start(self):
        self.__tankIndicator.start()
        self.__vID = BigWorld.player().playerVehicleID
        self.__waitingTI.start()

    def destroy(self):
        self.__waitingTI.stop()
        self.__waitingTI = None
        self.__updateTI.stop()
        self.__updateTI = None
        self.__tankIndicator.destroy()
        self.__tankIndicator = None
        self.__hasYawLimits = False
        self.__ui = None
        self.__otherVehiclesModules = None
        return

    def updateHealth(self, health):
        if self.__health is not health:
            self.__health = health
            self.__callFlash('updateHealth', [health])

    def updateModuleRepair(self, module, percents, seconds):
        self.__callFlash('updateModuleRepair', [module, percents, seconds])

    def updateSpeed(self, speed):
        if self.__speed is not speed:
            self.__speed = speed
            self.__callFlash('updateSpeed', [speed])

    def setCruiseMode(self, mode):
        self.__callFlash('setCruiseMode', [mode])

    def switchToVehicle(self, vID):
        if self.__vID is vID or vID is None:
            return
        else:
            self._reset()
            self.__waitingTI.stop()
            self.__updateTI.stop()
            self.__vID = vID
            self.__waitingTI.start()
            return

    def _reset(self):
        self.__vID = 0
        self.__speed = 0.0
        self.__health = 0
        self.__hasYawLimits = False
        self.__callFlash('reset')

    def _waiting(self):
        vehicle = BigWorld.entity(self.__vID)
        if vehicle is not None:
            self.__waitingTI.stop()
            self._setup(vehicle)
        return

    def _setup(self, vehicle):
        vTypeDesc = vehicle.typeDescriptor
        vType = vTypeDesc.type
        yawLimits = vTypeDesc.gun['turretYawLimits']
        self.__tankIndicator._setup(vehicle)
        self.__hasYawLimits = yawLimits is not None
        modulesLayout = vehicleHasTurretRotator(vTypeDesc)
        crewLayout = [ elem[0] for elem in vType.crewRoles ]
        order = TANKMEN_ROLES_ORDER_DICT['plain']
        lastIdx = len(order)

        def comparator(item, other):
            itemIdx = order.index(item) if item in order else lastIdx
            otherIdx = order.index(other) if other in order else lastIdx
            return cmp(itemIdx, otherIdx)

        crewLayout = sorted(crewLayout, cmp=comparator)
        self.__callFlash('setIconsLayout', crewLayout + [modulesLayout])
        self.__callFlash('setMaxHealth', [vTypeDesc.maxHealth])
        self.__callFlash('updateHealth', [vehicle.health])
        if vehicle.isPlayer and self.__hasYawLimits:
            aih = BigWorld.player().inputHandler
            auto = False
            if aih is not None:
                auto = aih.getAutorotation()
            self.onVehicleAutorotationEnabled(auto)
        if not vehicle.isAlive():
            self.onVehicleDestroyed()
            return
        else:
            self.__updateTI = None
            self.__updateTI = _TimeInterval(0.03, '_updateSelf' if vehicle.isPlayer else '_updateOther', weakref.proxy(self))
            self.__updateTI.start()
            return

    def _updateSelf(self):
        player = BigWorld.player()
        if player is None:
            return
        else:
            vehicle = BigWorld.entity(self.__vID)
            if vehicle is not None and vehicle.isStarted:
                speed, _ = player.getOwnVehicleSpeeds()
                self.updateSpeed(int(speed * 3.6))
            return

    def _updateOther(self):
        vehicle = BigWorld.entity(self.__vID)
        if vehicle is not None:
            self.updateHealth(vehicle.health)
            if vehicle.isStarted:
                try:
                    speed = vehicle.filter.speedInfo.value[0]
                    fwdSpeedLimit, bckwdSpeedLimit = vehicle.typeDescriptor.physics['speedLimits']
                    speed = max(min(speed, fwdSpeedLimit), -bckwdSpeedLimit)
                    self.updateSpeed(int(speed * 3.6))
                except (AttributeError, IndexError, ValueError):
                    LOG_CURRENT_EXCEPTION()
                    LOG_ERROR('Can not update speed. Stop')
                    self.__updateTI.stop()

            if not vehicle.isAlive():
                self.onVehicleDestroyed()
                self.__updateTI.stop()
        return

    def showAll(self, isShow):
        self.__callFlash('showAll', [isShow])

    def __getExtraName(self, extra):
        if extra.name == 'fire':
            return extra.name
        return extra.name[:-len('Health')]

    def updateExtras(self, vehicleID, damagedExtras, destroyedExtras):
        prevDamagedExtras = self.__otherVehiclesModules['critical'].setdefault(vehicleID, [])
        prevDestroyedExtras = self.__otherVehiclesModules['destroyed'].setdefault(vehicleID, [])
        vData = BigWorld.player().arena.vehicles.get(vehicleID)
        if vData is not None:
            for extraIdx in prevDestroyedExtras:
                if extraIdx not in destroyedExtras:
                    extraName = self.__getExtraName(vData['vehicleType'].extras[extraIdx])
                    self.updateState(extraName, 'repaired' if extraIdx in damagedExtras else 'normal')

            for extraIdx in prevDamagedExtras:
                if extraIdx not in damagedExtras:
                    extraName = self.__getExtraName(vData['vehicleType'].extras[extraIdx])
                    if extraName == 'fire':
                        self.onFireInVehicle(False)
                    else:
                        self.updateState(extraName, 'normal')

            for extraIdx in destroyedExtras:
                extraName = self.__getExtraName(vData['vehicleType'].extras[extraIdx])
                self.updateState(extraName, 'destroyed')

            for extraIdx in damagedExtras:
                extraName = self.__getExtraName(vData['vehicleType'].extras[extraIdx])
                if extraName == 'fire':
                    self.onFireInVehicle(True)
                else:
                    self.updateState(extraName, 'critical')

        self.__otherVehiclesModules['critical'][vehicleID] = damagedExtras
        self.__otherVehiclesModules['destroyed'][vehicleID] = destroyedExtras
        return

    def updateState(self, type, state):
        LOG_DEBUG('[DamagePanel.updateState] type = %s state = %s' % (type, state))
        self.__callFlash('updateState', [type, state])

    def onVehicleDestroyed(self):
        self.__updateTI.stop()
        self.__callFlash('onVehicleDestroyed')
        self.__callFlash('onCrewDeactivated')

    def onCrewDeactivated(self):
        self.__callFlash('onCrewDeactivated')

    def onFireInVehicle(self, bool):
        self.__callFlash('onFireInVehicle', [bool])

    def onVehicleAutorotationEnabled(self, value):
        if self.__hasYawLimits:
            self.__callFlash('onVehicleAutorotationEnabled', [value])

    def __onClickToTankmenIcon(self, _, entityName, entityState):
        if BattleReplay.g_replayCtrl.isPlaying:
            return
        if entityState == 'normal':
            self.__ui._showTankmanIsSafeMessage(entityName)
            return
        BigWorld.player().onDamageIconButtonPressed('medkit', entityName)

    def __onClickToDeviceIcon(self, _, entityName, entityState):
        if BattleReplay.g_replayCtrl.isPlaying:
            return
        if entityState == 'normal':
            self.__ui._showDeviceIsNotDamagedMessage(entityName)
            return
        BigWorld.player().onDamageIconButtonPressed('repairkit', entityName)

    def __callFlash(self, funcName, args = None):
        self.__ui.call('battle.damagePanel.' + funcName, args)


class _TankIndicatorCtrl():

    def __init__(self, parentUI):
        self.__ui = parentUI

    def __del__(self):
        LOG_DEBUG('_TankIndicatorCtrl deleted')

    def start(self):
        self._define()

    def destroy(self):
        setattr(self.__ui.component, 'tankIndicator', None)
        self.__ui = None
        return

    def _define(self):
        mc = GUI.WGTankIndicatorFlash(self.__ui.movie, '_root.damagePanel.componentsContainer.tankIndicator')
        mc.wg_inputKeyMode = 2
        self.__ui.component.addChild(mc, 'tankIndicator')

    def _setup(self, vehicle):
        vTypeDesc = vehicle.typeDescriptor
        vTags = vTypeDesc.type.tags
        yawLimits = vTypeDesc.gun['turretYawLimits']
        if 'SPG' in vTags:
            type = 'SPG'
        elif 'AT-SPG' in vTags:
            type = 'AT-SPG'
        else:
            type = 'Tank'
        hasYawLimits = yawLimits is not None
        if type in ('SPG', 'AT-SPG') and (not hasYawLimits or vehicleHasTurretRotator(vTypeDesc)):
            type = 'Tank'
        self.__flashCall('setType', [type])
        if hasYawLimits:
            args = [math.degrees(-yawLimits[0]), math.degrees(yawLimits[1]), True]
        else:
            args = [0, 0, False]
        self.__flashCall('setGunConstraints', args)
        if vehicle.isPlayer:
            hullMat = BigWorld.player().getOwnVehicleMatrix()
        else:
            hullMat = vehicle.matrix
        turretMat = vehicle.appearance.turretMatrix
        tankIndicator = self.__ui.component.tankIndicator
        tankIndicator.wg_turretYawConstraints = yawLimits if hasYawLimits else Math.Vector2(0.0, 0.0)
        tankIndicator.wg_hullMatProv = hullMat
        tankIndicator.wg_turretMatProv = turretMat
        return

    def __flashCall(self, funcName, args = None):
        if self.__ui:
            self.__ui.call('battle.tankIndicator.{0:>s}'.format(funcName), args)


class VehicleMarkersManager(Flash):
    __SWF_FILE_NAME = 'VehicleMarkersManager.swf'
    ATTACK_REASONS = ['attack',
     'fire',
     'ramming',
     'world_collision',
     'death_zone',
     'drowning']

    class DAMAGE_TYPE:
        FROM_UNKNOWN = 0
        FROM_ALLY = 1
        FROM_ENEMY = 2
        FROM_SQUAD = 3
        FROM_PLAYER = 4

    def __init__(self, parentUI):
        Flash.__init__(self, self.__SWF_FILE_NAME)
        self.component.wg_inputKeyMode = 2
        self.component.position.z = DEPTH_OF_VehicleMarker
        self.component.drawWithRestrictedViewPort = False
        self.movie.backgroundAlpha = 0
        self.colorManager = ColorSchemeManager._ColorSchemeManager()
        self.colorManager.populateUI(weakref.proxy(self))
        self.__ownUI = None
        self.__parentUI = parentUI
        self.__markers = dict()
        return

    def showExtendedInfo(self, value):
        self.__invokeCanvas('setShowExInfoFlag', [value])
        for handle in self.__markers.iterkeys():
            self.invokeMarker(handle, 'showExInfo', [value])

    def setScaleProps(self, minScale = 40, maxScale = 100, defScale = 100, speed = 3.0):
        if constants.IS_DEVELOPMENT:
            self.__ownUI.scaleProperties = (minScale,
             maxScale,
             defScale,
             speed)

    def setAlphaProps(self, minAlpha = 40, maxAlpha = 100, defAlpha = 100, speed = 3.0):
        if constants.IS_DEVELOPMENT:
            self.__ownUI.alphaProperties = (minAlpha,
             maxAlpha,
             defAlpha,
             speed)

    def start(self):
        self.active(True)
        self.__ownUI = GUI.WGVehicleMarkersCanvasFlash(self.movie)
        self.__ownUI.wg_inputKeyMode = 2
        self.__ownUI.scaleProperties = GUI_SETTINGS.markerScaleSettings
        self.__ownUI.alphaProperties = GUI_SETTINGS.markerBgSettings
        self.__ownUIProxy = weakref.proxy(self.__ownUI)
        self.__parentUI.component.addChild(self.__ownUI, 'vehicleMarkersManager')
        self.__markersCanvasUI = self.getMember('vehicleMarkersCanvas')

    def destroy(self):
        if self.__parentUI is not None:
            setattr(self.__parentUI.component, 'vehicleMarkersManager', None)
        self.__parentUI = None
        self.__ownUI = None
        self.__markersCanvasUI = None
        self.colorManager.dispossessUI()
        self.close()
        return

    def createMarker(self, vProxy):
        vInfo = dict(vProxy.publicInfo)
        if g_battleContext.isObserver(vProxy.id):
            return -1
        isFriend = vInfo['team'] == BigWorld.player().team
        vehicles = BigWorld.player().arena.vehicles
        vInfoEx = vehicles.get(vProxy.id, {})
        vTypeDescr = vProxy.typeDescriptor
        maxHealth = vTypeDescr.maxHealth
        mProv = vProxy.model.node('HP_gui')
        tags = set(vTypeDescr.type.tags & VEHICLE_CLASS_TAGS)
        vClass = tags.pop() if len(tags) > 0 else ''
        vType = vTypeDescr.type
        vIconSource = _CONTOUR_ICONS_MASK % {'unicName': vType.name.replace(':', '-')}
        entityName = g_battleContext.getPlayerEntityName(vProxy.id, vInfoEx)
        entityType = 'ally' if BigWorld.player().team == vInfoEx.get('team') else 'enemy'
        speaking = False
        if GUI_SETTINGS.voiceChat:
            speaking = VoiceChatInterface.g_instance.isPlayerSpeaking(vInfoEx.get('accountDBID', 0))
        hunting = VehicleActions.isHunting(vInfoEx.get('events', {}))
        handle = self.__ownUI.addMarker(mProv, 'VehicleMarkerAlly' if isFriend else 'VehicleMarkerEnemy')
        self.__markers[handle] = _VehicleMarker(vProxy, self.__ownUIProxy, handle)
        self.invokeMarker(handle, 'init', [vClass,
         vIconSource,
         vType.shortUserString,
         vType.level,
         g_battleContext.getFullPlayerName(vInfoEx, showVehShortName=False),
         vProxy.health,
         maxHealth,
         entityName.name(),
         speaking,
         hunting,
         entityType])
        self.__parentUI.call('minimap.entryInited', [])
        return handle

    def destroyMarker(self, handle):
        if self.__markers.has_key(handle):
            del self.__markers[handle]
            self.__ownUI.delMarker(handle)

    def createStaticMarker(self, pos, symbol):
        mProv = Math.Matrix()
        mProv.translation = pos
        handle = self.__ownUI.addMarker(mProv, symbol)
        return (mProv, handle)

    def destroyStaticMarker(self, handle):
        if self.__ownUI:
            self.__ownUI.delMarker(handle)

    def updateMarkerState(self, handle, newState, isImmediate = False):
        self.invokeMarker(handle, 'updateState', [newState, isImmediate])

    def showActionMarker(self, handle, newState):
        self.invokeMarker(handle, 'showActionMarker', [newState])

    def __getVehicleDamageType(self, attackerID):
        if not attackerID:
            return VehicleMarkersManager.DAMAGE_TYPE.FROM_UNKNOWN
        if attackerID == BigWorld.player().playerVehicleID:
            return VehicleMarkersManager.DAMAGE_TYPE.FROM_PLAYER
        entityName = g_battleContext.getPlayerEntityName(attackerID, BigWorld.player().arena.vehicles.get(attackerID, dict()))
        if entityName == PLAYER_ENTITY_NAME.squadman:
            return VehicleMarkersManager.DAMAGE_TYPE.FROM_SQUAD
        if entityName == PLAYER_ENTITY_NAME.ally:
            return VehicleMarkersManager.DAMAGE_TYPE.FROM_ALLY
        if entityName == PLAYER_ENTITY_NAME.enemy:
            return VehicleMarkersManager.DAMAGE_TYPE.FROM_ENEMY
        return VehicleMarkersManager.DAMAGE_TYPE.FROM_UNKNOWN

    def onVehicleHealthChanged(self, handle, curHealth, attackerID = -1, attackReasonID = 0):
        self.invokeMarker(handle, 'updateHealth', [curHealth, self.__getVehicleDamageType(attackerID), VehicleMarkersManager.ATTACK_REASONS[attackReasonID]])

    def showDynamic(self, vID, flag):
        handle = getattr(BigWorld.entity(vID), 'marker', None)
        if handle is not None and GUI_SETTINGS.voiceChat:
            self.invokeMarker(handle, 'setSpeaking', [flag])
        return

    def setTeamKiller(self, vID):
        if not g_battleContext.isTeamKiller(vID=vID):
            return
        else:
            handle = getattr(BigWorld.entity(vID), 'marker', None)
            if handle is not None:
                self.invokeMarker(handle, 'setEntityName', [PLAYER_ENTITY_NAME.teamKiller.name()])
            return

    def invokeMarker(self, handle, function, args = None):
        if handle == -1:
            return
        else:
            if args is None:
                args = []
            self.__ownUI.markerInvoke(handle, (function, args))
            return

    def __invokeCanvas(self, function, args = None):
        if args is None:
            args = []
        self.call('battle.vehicleMarkersCanvas.' + function, args)
        return

    def setMarkerSettings(self, settings):
        if self.__markersCanvasUI:
            self.__markersCanvasUI.setMarkerSettings(settings)

    def setMarkerDuration(self, value):
        self.__invokeCanvas('setMarkerDuration', [value])

    def updateMarkers(self):
        self.colorManager.update()
        for handle in self.__markers.iterkeys():
            self.invokeMarker(handle, 'update', [])

    def updateMarkerSettings(self):
        for handle in self.__markers.iterkeys():
            self.invokeMarker(handle, 'updateMarkerSettings', [])


class _VehicleMarker():

    def __init__(self, vProxy, uiProxy, handle):
        self.vProxy = vProxy
        self.uiProxy = uiProxy
        self.handle = handle
        self.vProxy.appearance.onModelChanged += self.__onModelChanged

    def destroy(self):
        self.vProxy.appearance.onModelChanged -= self.__onModelChanged
        self.vProxy = None
        self.uiProxy = None
        self.handle = -1
        return

    def __onModelChanged(self):
        self.uiProxy.markerSetMatrix(self.handle, self.vProxy.model.node('HP_gui'))


class FadingMessagesPanel(object):
    __settings = []
    __messageDict = {}
    _EXTRA_COLOR_FORMAT = '<font color="#{0:02X}{1:02X}{2:02X}">{3:>s}</font>'

    def __init__(self, parentUI, name, cfgFileName, isColorBlind = False):
        self.__ui = parentUI
        self.__name = name
        self.__pathPrefix = 'battle.' + name + '.' + '%s'
        self.__readConfig(cfgFileName)
        self.__ui.addExternalCallbacks({'battle.%s.PopulateUI' % name: self.__onPopulateUI})
        self.defineColorFlags(isColorBlind=isColorBlind)
        self.__isPopulated = False
        self.__pendingMessages = []

    def start(self):
        self.__callFlash('RefreshUI')

    def destroy(self):
        self.__ui = None
        self.__isPopulated = False
        self.__pendingMessages = []
        return

    def clear(self):
        self.__callFlash('Clear')

    def defineColorFlags(self, isColorBlind = False):
        self.__colorGroup = 'color_blind' if isColorBlind else 'default'

    def showMessage(self, key, args = None, extra = None, postfix = ''):
        replayCtrl = BattleReplay.g_replayCtrl
        if replayCtrl.isPlaying and replayCtrl.isTimeWarpInProgress:
            return
        else:
            extKey = '%s_%s' % (key, postfix)
            if extKey in self.__messageDict:
                key = extKey
            msgText, colors = self.__messageDict.get(key, (None, ''))
            if msgText is None:
                return
            if args is not None:
                self.__formatEntitiesEx(args, extra=extra)
                try:
                    msgText = msgText % args
                except TypeError:
                    LOG_CURRENT_EXCEPTION()

            color = colors.get(self.__colorGroup if self.__colorGroup in colors else 'default')
            if self.__isPopulated:
                self.__showMessage(key, msgText, color)
            else:
                self.__pendingMessages.append([key, msgText, color])
            return

    def __showMessage(self, key, msgText, color):
        LOG_DEBUG('%s: show message with key = %s' % (self.__name, key))
        self.__callFlash('ShowMessage', [key, msgText, color])

    def __formatEntitiesEx(self, args, extra = None):
        if extra is None:
            extra = ()
        csManager = self.__ui.colorManager
        for argName, vID in extra:
            arg = args.get(argName)
            rgba = None
            if g_battleContext.isTeamKiller(vID=vID):
                rgba = csManager.getScheme('teamkiller').get(self.__colorGroup, {}).get('rgba')
            elif g_battleContext.isSquadMan(vID=vID):
                rgba = csManager.getScheme('squad').get(self.__colorGroup, {}).get('rgba')
            if arg and rgba:
                args[argName] = self._EXTRA_COLOR_FORMAT.format(int(rgba[0]), int(rgba[1]), int(rgba[2]), arg)

        return

    def __readConfig(self, cfgFileName):
        self.__settings = []
        import ResMgr
        sec = ResMgr.openSection(cfgFileName)
        if sec is None:
            raise Exception, "can not open '%s'" % cfgFileName
        self.__settings.append(sec.readInt('maxLinesCount', -1))
        direction = sec.readString('direction')
        if direction not in ('up', 'down'):
            raise Exception, 'Wrong direction value in %s' % cfgFileName
        self.__settings.append(direction)
        self.__settings.append(sec.readFloat('lifeTime'))
        self.__settings.append(sec.readFloat('alphaSpeed'))
        self.__settings.append(sec.readBool('showUniqueOnly', False))
        self.__messageDict = dict()
        for mTag, mSec in sec['messages'].items():
            text = mSec.readString('text')
            text = html.translation(text)
            aliasesSec = mSec['colorAlias']
            aliases = aliasesSec.items()
            if len(aliases):
                groups = dict(((key, section.asString) for key, section in aliases))
            else:
                groups = {'default': aliasesSec.asString}
            self.__messageDict[mTag] = (text, groups)

        return

    def __callFlash(self, funcName, args = None):
        self.__ui.call(self.__pathPrefix % funcName, args)

    def __onPopulateUI(self, requestId):
        args = [requestId]
        args.extend(self.__settings)
        self.__ui.respond(args)
        self.__isPopulated = True
        while len(self.__pendingMessages):
            self.__showMessage(*self.__pendingMessages.pop())


def _playerComparator(x1, x2):
    INDEX_IS_ALIVE = 17
    INDEX_VEHICLE_LEVEL = 15
    INDEX_VEHICLE_TYPE = 18
    INDEX_VEHICLE_NAME = 2
    INDEX_PLAYER_NAME = 0
    if x1[INDEX_IS_ALIVE] < x2[INDEX_IS_ALIVE]:
        return -1
    if x1[INDEX_IS_ALIVE] > x2[INDEX_IS_ALIVE]:
        return 1
    if x1[INDEX_VEHICLE_LEVEL] < x2[INDEX_VEHICLE_LEVEL]:
        return 1
    if x1[INDEX_VEHICLE_LEVEL] > x2[INDEX_VEHICLE_LEVEL]:
        return -1
    vehTypeIdx1 = VEHICLE_BATTLE_TYPES_ORDER_INDICES.get(x1[INDEX_VEHICLE_TYPE], 10)
    vehTypeIdx2 = VEHICLE_BATTLE_TYPES_ORDER_INDICES.get(x2[INDEX_VEHICLE_TYPE], 10)
    if vehTypeIdx1 < vehTypeIdx2:
        return -1
    if vehTypeIdx1 > vehTypeIdx2:
        return 1
    if x1[INDEX_VEHICLE_NAME] < x2[INDEX_VEHICLE_NAME]:
        return -1
    if x1[INDEX_VEHICLE_NAME] > x2[INDEX_VEHICLE_NAME]:
        return 1
    if x1[INDEX_PLAYER_NAME] < x2[INDEX_PLAYER_NAME]:
        return -1
    if x1[INDEX_PLAYER_NAME] > x2[INDEX_PLAYER_NAME]:
        return 1
    return 0


def _markerComparator(x1, x2):
    INDEX_IS_ALIVE = 2
    INDEX_VEHICLE_CLASS = 1
    if x1[INDEX_IS_ALIVE] < x2[INDEX_IS_ALIVE]:
        return 1
    if x1[INDEX_IS_ALIVE] > x2[INDEX_IS_ALIVE]:
        return -1
    x1Index = VEHICLE_BATTLE_TYPES_ORDER_INDICES.get(x1[INDEX_VEHICLE_CLASS], 100)
    x2Index = VEHICLE_BATTLE_TYPES_ORDER_INDICES.get(x2[INDEX_VEHICLE_CLASS], 100)
    if x1Index < x2Index:
        return -1
    if x1Index > x2Index:
        return 1
    return 0


class _TimeInterval():

    def __init__(self, interval, funcName, scopeProxy = None):
        self.__cbId = None
        self.__interval = interval
        self.__funcName = funcName
        self.__scopeProxy = scopeProxy
        return

    def start(self):
        if self.__cbId is not None:
            LOG_ERROR('To start a new time interval You should before stop already the running time interval.')
            return
        else:
            self.__cbId = BigWorld.callback(self.__interval, self.__update)
            return

    def stop(self):
        if self.__cbId is not None:
            BigWorld.cancelCallback(self.__cbId)
            self.__cbId = None
        return

    def __update(self):
        self.__cbId = None
        self.__cbId = BigWorld.callback(self.__interval, self.__update)
        if self.__scopeProxy is not None:
            funcObj = getattr(self.__scopeProxy, self.__funcName, None)
            if funcObj is not None:
                funcObj()
        return


def vehicleHasTurretRotator(vTypeDesc):
    result = True
    if vTypeDesc.type.tags & set(['SPG', 'AT-SPG']) and len(vTypeDesc.hull.get('fakeTurrets', {}).get('battle', ())) > 0:
        result = False
    return result
# okay decompyling res/scripts/client/gui/scaleform/battle.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:25:50 EST

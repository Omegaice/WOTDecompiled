# Embedded file name: scripts/client/gui/Scaleform/daapi/view/BattleLoading.py
import BigWorld
from chat_shared import USERS_ROSTER_VOICE_MUTED
import constants
from debug_utils import LOG_DEBUG
from gui import makeHtmlString
from gui.prb_control.formatters import getPrebattleFullDescription
from helpers import tips, i18n
from gui.shared.utils.functions import getBattleSubTypeWinText, getArenaSubTypeName, isBaseExists
from gui.Scaleform import VehicleActions
from gui.Scaleform.Waiting import Waiting
from gui.Scaleform.daapi import LobbySubView
from gui.Scaleform.daapi.view.meta.BattleLoadingMeta import BattleLoadingMeta
from messenger.proto.events import g_messengerEvents
from messenger.storage import storage_getter
from gui.shared.gui_items.Vehicle import VEHICLE_BATTLE_TYPES_ORDER_INDICES
from items.vehicles import VEHICLE_CLASS_TAGS

class BattleLoading(LobbySubView, BattleLoadingMeta):
    MAP_BG_SOURCE = '../maps/icons/map/screen/%s.png'
    CONTOUR_ICONS_MASK = '../maps/icons/vehicle/contour/%(unicName)s.png'

    def __init__(self, ctx):
        super(BattleLoading, self).__init__(backAlpha=1.0)
        self.loadCompleteHandler = ctx.get('loadComplete')
        self.callbackId = None
        self.__arena = getattr(BigWorld.player(), 'arena', None)
        self.__progress = 0
        self.__winTextInit = False
        return

    @storage_getter('users')
    def usersStorage(self):
        return None

    def _populate(self):
        super(BattleLoading, self)._populate()
        if self.__arena:
            self.__arena.onNewVehicleListReceived += self.__updatePlayers
            self.__arena.onNewStatisticsReceived += self.__updatePlayers
            self.__arena.onVehicleAdded += self.__updatePlayers
            self.__arena.onVehicleStatisticsUpdate += self.__updatePlayers
            self.__arena.onVehicleKilled += self.__updatePlayers
            self.__arena.onAvatarReady += self.__updatePlayers
            self.__arena.onVehicleUpdated += self.__updatePlayers
            g_messengerEvents.users.onUsersRosterReceived += self.__updatePlayers
        self.getData()
        self.isSpaceLoaded()
        BigWorld.wg_setReducedFpsMode(True)
        Waiting.close()

    def _dispose(self):
        if self.callbackId is not None:
            BigWorld.cancelCallback(self.callbackId)
            self.callbackId = None
        if self.__arena:
            self.__arena.onNewVehicleListReceived -= self.__updatePlayers
            self.__arena.onNewStatisticsReceived -= self.__updatePlayers
            self.__arena.onVehicleAdded -= self.__updatePlayers
            self.__arena.onVehicleStatisticsUpdate -= self.__updatePlayers
            self.__arena.onVehicleKilled -= self.__updatePlayers
            self.__arena.onAvatarReady -= self.__updatePlayers
            self.__arena.onVehicleUpdated -= self.__updatePlayers
            g_messengerEvents.users.onUsersRosterReceived -= self.__updatePlayers
        self.__arena = None
        self.loadCompleteHandler = None
        super(BattleLoading, self)._dispose()
        BigWorld.wg_setReducedFpsMode(False)
        return

    def isSpaceLoaded(self):
        self.callbackId = None
        import BattleReplay
        status = 1.0 if BattleReplay.g_replayCtrl.isTimeWarpInProgress else BigWorld.spaceLoadStatus()
        if status > self.__progress:
            self.__progress = status
            self.__setProgress(status)
        if status < 1.0:
            self.callbackId = BigWorld.callback(0.5, self.isSpaceLoaded)
            BigWorld.SetDrawInflux(False)
            return
        else:
            BigWorld.SetDrawInflux(True)
            BigWorld.player().onSpaceLoaded()
            self.isLoaded()
            return

    def isLoaded(self):
        self.callbackId = None
        if not BigWorld.worldDrawEnabled():
            self.callbackId = BigWorld.callback(0.5, self.isLoaded)
            return
        else:
            if self.loadCompleteHandler is not None:
                self.loadCompleteHandler()
            self.destroy()
            return

    def __setProgress(self, value):
        self.as_setProgressS(value)

    def getData(self):
        arena = getattr(BigWorld.player(), 'arena', None)
        if arena:
            self.as_setMapNameS(arena.arenaType.name)
            self.as_setMapBGS(BattleLoading.MAP_BG_SOURCE % arena.arenaType.geometryName)
            descExtra = getPrebattleFullDescription(arena.extraData or {})
            arenaSubType = getArenaSubTypeName(BigWorld.player().arenaTypeID)
            if descExtra:
                self.as_setBattleTypeNameS(descExtra)
                self.as_setBattleTypeFrameNumS(arena.guiType + 1)
            elif arena.guiType == constants.ARENA_GUI_TYPE.RANDOM:
                self.as_setBattleTypeNameS('#arenas:type/%s/name' % arenaSubType)
                self.as_setBattleTypeFrameNameS(arenaSubType)
            else:
                self.as_setBattleTypeNameS('#menu:loading/battleTypes/%d' % arena.guiType)
                self.as_setBattleTypeFrameNumS(arena.guiType + 1)
        self.as_setTipS(tips.getTip())
        self.__updatePlayers()
        return

    def __updatePlayers(self, *args):
        stat = {1: [],
         2: []}
        squads = {1: {},
         2: {}}
        player = BigWorld.player()
        if player is None:
            return
        elif self.__arena is None:
            return
        else:
            vehicles = self.__arena.vehicles
            userGetter = self.usersStorage.getUser
            for vId, vData in vehicles.items():
                team = vData['team']
                name = vData['name'] if vData['name'] is not None else i18n.makeString('#ingame_gui:players_panel/unknown_name')
                if vData['vehicleType'] is not None:
                    vShortName = vData['vehicleType'].type.shortUserString
                    vName = vData['vehicleType'].type.userString
                    vIcon = self.CONTOUR_ICONS_MASK % {'unicName': vData['vehicleType'].type.name.replace(':', '-')}
                    vType = set(VEHICLE_CLASS_TAGS.intersection(vData['vehicleType'].type.tags)).pop()
                else:
                    vName = vShortName = i18n.makeString('#ingame_gui:players_panel/unknown_vehicle')
                    vIcon = self.CONTOUR_ICONS_MASK % {'unicName': 'unknown'}
                    vType = 100
                if vData['isAlive']:
                    isAlive = vData['isAvatarReady']
                    vehActions = VehicleActions.getBitMask(vData.get('events', {}))
                    if vData['prebattleID']:
                        if vData['prebattleID'] not in squads[team].keys():
                            squads[team][vData['prebattleID']] = 1
                        else:
                            squads[team][vData['prebattleID']] += 1
                    user = userGetter(vData['accountDBID'])
                    isMuted = user and user.getRoster() & USERS_ROSTER_VOICE_MUTED != 0
                else:
                    isMuted = False
                stat[team].append([name,
                 vIcon,
                 vShortName,
                 not isAlive,
                 vId,
                 vData['prebattleID'],
                 vType,
                 vName,
                 not vData['isAlive'],
                 vData['name'],
                 vData['accountDBID'],
                 isMuted,
                 vehActions,
                 self.app.voiceChatManager.isPlayerSpeaking(vData['accountDBID']),
                 vData['isTeamKiller'],
                 vData['vehicleType'].level,
                 vData['igrType'],
                 vData['clanAbbrev']])

            squadsSorted = dict()
            squadsSorted[1] = sorted(squads[1].iteritems(), cmp=lambda x, y: cmp(x[0], y[0]))
            squadsSorted[2] = sorted(squads[2].iteritems(), cmp=lambda x, y: cmp(x[0], y[0]))
            squadsFiltered = dict()
            squadsFiltered[1] = [ id for id, num in squadsSorted[1] if 1 < num < 4 and self.__arena.guiType == constants.ARENA_GUI_TYPE.RANDOM ]
            squadsFiltered[2] = [ id for id, num in squadsSorted[2] if 1 < num < 4 and self.__arena.guiType == constants.ARENA_GUI_TYPE.RANDOM ]
            playerVehicleID = -1
            if hasattr(player, 'playerVehicleID'):
                playerVehicleID = player.playerVehicleID
            playerSquadID = -1
            for team in (1, 2):
                data = sorted(stat[team], cmp=_playerComparator)
                for item in data:
                    if playerVehicleID == item[4]:
                        playerSquadID = squadsFiltered[team].index(item[5]) + 1 if item[5] in squadsFiltered[team] else 0
                        break

            result = {'playerID': playerVehicleID,
             'squadID': playerSquadID,
             'team1': list(),
             'team2': list()}
            for team in (1, 2):
                thisTeam = 'team2'
                thisTeamMembers = list()
                data = sorted(stat[team], cmp=_playerComparator)
                for item in data:
                    item[5] = squadsFiltered[team].index(item[5]) + 1 if item[5] in squadsFiltered[team] else 0
                    if item[9] == player.name and result['playerID'] == -1 or item[4] == playerVehicleID:
                        result['playerID'] = item[4]
                        thisTeam = 'team1'
                        self.setTeams(team)
                        if not self.__winTextInit:
                            self.__winTextInit = True
                            teamHasBase = 1 if isBaseExists(BigWorld.player().arenaTypeID, team) else 2
                            winText = getBattleSubTypeWinText(BigWorld.player().arenaTypeID, teamHasBase)
                            self.as_setWinTextS(winText)
                    thisTeamMembers.append({'id': item[10],
                     'muted': item[11],
                     'playerID': item[4],
                     'label': item[0],
                     'icon': item[1],
                     'vehicle': item[2],
                     'enabled': not item[3],
                     'squad': item[5],
                     'vehAction': item[12],
                     'speak': item[13],
                     'isTeamKiller': item[14],
                     'isIGR': item[16] != constants.IGR_TYPE.NONE,
                     'clanAbbrev': item[17]})

                result[thisTeam] = thisTeamMembers

            self.as_setTeamValuesS(result)
            return

    def setTeams(self, myTeam):
        arena = getattr(BigWorld.player(), 'arena', None)
        if arena:
            extraData = arena.extraData or {}
            team1 = extraData.get('opponents', {}).get('%s' % myTeam, {}).get('name', '#menu:loading/team1')
            team2 = extraData.get('opponents', {}).get('2' if myTeam == 1 else '1', {}).get('name', '#menu:loading/team2')
            self.as_setTeamsS(team1, team2)
        return


def _playerComparator(x1, x2):
    if x1[8] < x2[8]:
        return -1
    if x1[8] > x2[8]:
        return 1
    if x1[15] < x2[15]:
        return 1
    if x1[15] > x2[15]:
        return -1
    vehTypeIdx1 = VEHICLE_BATTLE_TYPES_ORDER_INDICES.get(x1[6], 100)
    vehTypeIdx2 = VEHICLE_BATTLE_TYPES_ORDER_INDICES.get(x2[6], 100)
    if vehTypeIdx1 < vehTypeIdx2:
        return -1
    if vehTypeIdx1 > vehTypeIdx2:
        return 1
    if x1[2] < x2[2]:
        return -1
    if x1[2] > x2[2]:
        return 1
    if x1[9] < x2[9]:
        return -1
    if x1[9] > x2[9]:
        return 1
    return 0
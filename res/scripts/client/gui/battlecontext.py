import BigWorld
import Settings
import constants
from enumerations import AttributeEnumItem, Enumeration
from gui.shared.utils.gui_items import isVehicleObserver
PLAYER_ENTITY_NAME = Enumeration('Player entity name in battle', [('ally', {'isFriend': True,
   'base': 'ally'}),
 ('teamKiller', {'isFriend': True,
   'base': 'ally'}),
 ('squadman', {'isFriend': True,
   'base': 'ally'}),
 ('enemy', {'isFriend': False,
   'base': 'enemy'})], instance=AttributeEnumItem)
defNormalizePNameFunction = lambda pName: pName

class _BattleContext(object):
    __playerFullNameFormats = {1: '{0:>s} ({2:>s})',
     16: '{0:>s}[{1:>s}]',
     17: '{0:>s}[{1:>s}] ({2:>s})'}
    __normalizePName = staticmethod(defNormalizePNameFunction)

    def setNormalizePlayerName(self, function):
        _BattleContext.__normalizePName = staticmethod(function)

    def resetNormalizePlayerName(self):
        _BattleContext.__normalizePName = staticmethod(defNormalizePNameFunction)

    def __init__(self):
        super(_BattleContext, self).__init__()
        self.__playersVIDs = {}
        self.__squadID = None
        self.__squadManVIDs = set()
        self.__teamKillerVIDs = set()
        self.__isShowVehShortName = True
        self.lastArenaUniqueID = None
        self.isInBattle = False
        return

    def init(self):
        prefs = Settings.g_instance.userPrefs
        if prefs is not None:
            self.__isShowVehShortName = prefs.readBool('showVehShortName', True)
        player = BigWorld.player()
        if not player:
            return
        else:
            arena = getattr(player, 'arena', None)
            if arena is None:
                return
            playerVehID = getattr(player, 'playerVehicleID', None)
            prebattleID = arena.vehicles.get(playerVehID, {}).get('prebattleID')
            if arena.guiType == constants.ARENA_GUI_TYPE.RANDOM and prebattleID > 0:
                self.__squadID = prebattleID
            self.__findRequiredData()
            arena.onNewVehicleListReceived += self.__arena_onNewVehicleListReceived
            arena.onVehicleAdded += self.__arena_onVehicleAdded
            arena.onTeamKiller += self.__arena_onTeamKiller
            self.isInBattle = True
            return

    def fini(self):
        self.isInBattle = False
        self.__playersVIDs.clear()
        self.__squadManVIDs.clear()
        self.__teamKillerVIDs.clear()
        self.__squadID = None
        arena = getattr(BigWorld.player(), 'arena', None)
        if arena is None:
            arena.onNewVehicleListReceived -= self.__arena_onNewVehicleListReceived
            arena.onVehicleAdded -= self.__arena_onVehicleAdded
            arena.onTeamKiller -= self.__arena_onTeamKiller
        return

    def getVehIDByAccDBID(self, accDBID):
        return self.__playersVIDs.get(accDBID, 0)

    def getFullPlayerName(self, vData = None, vID = None, accID = None, pName = None, showVehShortName = True, showClan = True):
        key = 0
        vehShortName = ''
        if vData is None:
            arena = getattr(BigWorld.player(), 'arena', None)
            if vID is None:
                vID = self.__playersVIDs.get(accID, 0)
            vData = arena.vehicles.get(vID, {}) if arena else {}
        if showVehShortName and self.__isShowVehShortName:
            vehType = vData.get('vehicleType')
            if vehType is not None:
                vehShortName = vehType.type.shortUserString
                key |= 1
        if pName is None:
            pName = vData.get('name', '')
        pName = self.__normalizePName(pName)
        clanAbbrev = ''
        if showClan:
            clanAbbrev = vData.get('clanAbbrev', '')
            if clanAbbrev is not None and len(clanAbbrev) > 0:
                key |= 16
        if key == 0:
            return pName
        else:
            return self.__playerFullNameFormats.get(key, '{0:>s}').format(pName, clanAbbrev, vehShortName)

    def isSquadMan(self, vID = None, accID = None):
        if vID is None:
            vID = self.__playersVIDs.get(accID)
        return self.__squadID and vID in self.__squadManVIDs

    def isTeamKiller(self, vID = None, accID = None):
        if vID is None:
            vID = self.__playersVIDs.get(accID)
        return vID in self.__teamKillerVIDs

    def isObserver(self, vID):
        resultVal = False
        vData = BigWorld.player().arena.vehicles.get(vID)
        if vData is not None:
            vDescr = vData.get('vehicleType')
            if vDescr is not None:
                resultVal = isVehicleObserver(vDescr.type.compactDescr)
        return resultVal

    def isPlayerObserver(self):
        return self.isObserver(getattr(BigWorld.player(), 'playerVehicleID', -1))

    def getPlayerEntityName(self, vID, vData):
        entityName = PLAYER_ENTITY_NAME.enemy
        if BigWorld.player().team == vData.get('team'):
            if self.isTeamKiller(vID=vID):
                entityName = PLAYER_ENTITY_NAME.teamKiller
            elif self.isSquadMan(vID=vID):
                entityName = PLAYER_ENTITY_NAME.squadman
            else:
                entityName = PLAYER_ENTITY_NAME.ally
        return entityName

    def getTeamName(self, myTeam, isAlliedTeam):
        teamName = '#menu:loading/team%s' % ('1' if isAlliedTeam else '2')
        arena = getattr(BigWorld.player(), 'arena', None)
        if arena:
            if not arena.extraData:
                extraData = {}
                teamName = isAlliedTeam and extraData.get('opponents', {}).get('%s' % myTeam, {}).get('name', teamName)
            else:
                teamName = extraData.get('opponents', {}).get('2' if myTeam == 1 else '1', {}).get('name', teamName)
        return teamName

    def __findRequiredData(self):
        self.__playersVIDs.clear()
        self.__squadManVIDs.clear()
        self.__teamKillerVIDs.clear()
        arena = BigWorld.player().arena
        for vID, vData in arena.vehicles.iteritems():
            self.__addVehicleData(vID, vData)

    def __addVehicleData(self, vID, vData):
        accDBID = vData.get('accountDBID', 0)
        if accDBID > 0:
            self.__playersVIDs[accDBID] = vID
        if self.__squadID and self.__squadID == vData.get('prebattleID'):
            self.__squadManVIDs.add(vID)
        if vData.get('isTeamKiller', False) and BigWorld.player().team == vData.get('team'):
            self.__teamKillerVIDs.add(vID)

    def __arena_onNewVehicleListReceived(self):
        self.__findRequiredData()

    def __arena_onVehicleAdded(self, vID):
        self.__addVehicleData(vID, BigWorld.player().arena.vehicles.get(vID, {}))

    def __arena_onTeamKiller(self, vID):
        vData = BigWorld.player().arena.vehicles.get(vID, {})
        if vData.get('isTeamKiller', False) and BigWorld.player().team == vData.get('team'):
            self.__teamKillerVIDs.add(vID)


g_battleContext = _BattleContext()

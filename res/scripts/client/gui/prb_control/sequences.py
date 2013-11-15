# 2013.11.15 11:25:46 EST
# Embedded file name: scripts/client/gui/prb_control/sequences.py
import time
import itertools
import BigWorld
from UnitBase import UNIT_ROLE
from constants import PREBATTLE_CACHE_KEY, PREBATTLE_COMPANY_DIVISION_NAMES
from constants import PREBATTLE_TYPE
from gui.LobbyContext import g_lobbyContext
from gui.prb_control.info import PlayerPrbInfo, UnitState
from gui.prb_control.settings import CREATOR_ROSTER_SLOT_INDEXES
from gui.shared import g_itemsCache, REQ_CRITERIA
from helpers.time_utils import makeLocalServerTime
from messenger.ext import passCensor

def PrbListIterator(prebattles):
    for time, prbID, info in prebattles:
        yield PrbListItem(time, prbID, info)


def RosterIterator(roster):
    for pID, name, dbID, roster, state, time, vehCompDescr, clanDBID, clanAbbrev in roster:
        yield PlayerPrbInfo(pID, name=name, dbID=dbID, state=state, time=time, vehCompDescr=vehCompDescr, clanDBID=clanDBID, clanAbbrev=clanAbbrev, roster=roster)


def AutoInvitesIterator():
    autoInvites = []
    player = BigWorld.player()
    if hasattr(player, 'prebattleAutoInvites'):
        autoInvites = player.prebattleAutoInvites.items()

    def comparator(obj, other):
        return cmp(obj[1].get('startTime', time.time()), other[1].get('startTime', time.time()))

    autoInvites.sort(comparator)
    for prbID, info in autoInvites:
        yield AutoInviteItem(prbID, **info)


def UnitsListIterator(data):
    units = sorted(data.iteritems(), key=lambda item: item[1]['cmdrRating'], reverse=True)
    for cfdUnitID, unitInfo in units:
        yield UnitsListItem(cfdUnitID, **unitInfo)


def UnitsUpdateIterator(data):
    for cfdUnitID, unitInfo in data.iteritems():
        yield (cfdUnitID, unitInfo)


class PrbListItem(object):
    __slots__ = ('prbID', 'time', 'arenaTypeID', 'creator', 'clanAbbrev', 'playersCount', 'isOpened', 'comment', 'division')

    def __init__(self, time, prbID, info):
        super(PrbListItem, self).__init__()
        self.prbID = prbID
        self.time = time
        self.arenaTypeID = 0
        if PREBATTLE_CACHE_KEY.ARENA_TYPE_ID in info:
            self.arenaTypeID = info[PREBATTLE_CACHE_KEY.ARENA_TYPE_ID]
        self.creator = ''
        if PREBATTLE_CACHE_KEY.CREATOR in info:
            self.creator = info[PREBATTLE_CACHE_KEY.CREATOR]
        self.clanAbbrev = ''
        if PREBATTLE_CACHE_KEY.CREATOR_CLAN_ABBREV in info:
            self.clanAbbrev = info[PREBATTLE_CACHE_KEY.CREATOR_CLAN_ABBREV]
        self.playersCount = 0
        if PREBATTLE_CACHE_KEY.PLAYER_COUNT in info:
            self.playersCount = info[PREBATTLE_CACHE_KEY.PLAYER_COUNT]
        self.isOpened = True
        if PREBATTLE_CACHE_KEY.IS_OPENED in info:
            self.isOpened = info[PREBATTLE_CACHE_KEY.IS_OPENED]
        self.comment = ''
        if PREBATTLE_CACHE_KEY.COMMENT in info:
            self.comment = info[PREBATTLE_CACHE_KEY.COMMENT]
        self.division = 0
        if PREBATTLE_CACHE_KEY.DIVISION in info:
            self.division = info[PREBATTLE_CACHE_KEY.DIVISION]

    def __repr__(self):
        return 'PrbListItem(prbID = {0:n}, arenaTypeID = {1:n}, creator = {2:>s}, playersCount = {3:n}, isOpened = {4!r:s}, division = {5:>s}, time = {6:n})'.format(self.prbID, self.arenaTypeID, self.getCreatorFullName(), self.playersCount, self.isOpened, self.getDivisionName(), self.time)

    def getCreatorFullName(self):
        if self.clanAbbrev and len(self.clanAbbrev):
            fullName = '{0:>s}[{1:>s}]'.format(self.creator, self.clanAbbrev)
        else:
            fullName = self.creator
        return fullName

    def getCensoredComment(self):
        if self.comment:
            return passCensor(self.comment)
        return ''

    def getDivisionName(self):
        name = None
        if self.division in PREBATTLE_COMPANY_DIVISION_NAMES:
            name = PREBATTLE_COMPANY_DIVISION_NAMES[self.division]
        return name


class AutoInviteItem(object):
    __slots__ = ('prbID', 'peripheryID', 'description', 'startTime', 'isValid', 'prbType')

    def __init__(self, prbID, type = PREBATTLE_TYPE.CLAN, peripheryID = 0, description = None, startTime = 0, isValid = True):
        super(AutoInviteItem, self).__init__()
        self.prbID = prbID
        self.peripheryID = peripheryID
        self.prbType = type
        if description:
            self.description = description
        else:
            self.description = {}
        if startTime > 0:
            self.startTime = makeLocalServerTime(startTime)
        else:
            self.startTime = time.time()
        self.isValid = isValid

    def __repr__(self):
        return 'AutoInviteItem(prbID = {0:n}, peripheryID = {1:n}, type = {2:n} description = {3!r:s}, startTime = {4:n}, isValid = {5!r:s})'.format(self.prbID, self.prbType, self.peripheryID, self.description, self.startTime, self.isValid)


class UnitsListItem(object):
    __slots__ = ('cfdUnitID', 'unitMgrID', 'creator', 'rating', 'playersCount', 'commandSize', 'vehicles', 'state', 'isRosterSet', 'peripheryID')

    def __init__(self, cfdUnitID, unitMgrID = 0, cmdrRating = 0, peripheryID = 0, unit = None, **kwargs):
        super(UnitsListItem, self).__init__()
        creatorFullName = ''
        vehiclesNames = tuple()
        playersCount = 0
        commandSize = 0
        state = 0
        isRosterSet = False
        if unit:
            creatorDBID, creator = next(itertools.ifilter(lambda (dbID, p): p['role'] & UNIT_ROLE.COMMANDER_UPDATES > 0, unit._players.iteritems()), (None, None))
            if creator is not None:
                creatorFullName = g_lobbyContext.getPlayerFullName(creator['nickName'], clanAbbrev=creator.get('clanAbbrev'), pDBID=creatorDBID)
            freeSlots = unit.getFreeSlots()
            playersSlots = unit.getPlayerSlots()
            state = unit.getState()
            vehicles = g_itemsCache.items.getVehicles(REQ_CRITERIA.INVENTORY)
            matches = unit.getRoster().matchVehicleListToSlotList(vehicles.keys(), freeSlots)
            vehiclesNames = tuple(itertools.imap(lambda x: vehicles[x].shortUserName, set(matches.keys())))
            playersCount = len(playersSlots)
            commandSize = len(playersSlots) + len(freeSlots)
            isRosterSet = unit.isRosterSet(ignored=CREATOR_ROSTER_SLOT_INDEXES)
        self.cfdUnitID = cfdUnitID
        self.unitMgrID = unitMgrID
        self.creator = creatorFullName
        self.rating = cmdrRating
        self.peripheryID = peripheryID
        self.playersCount = playersCount
        self.commandSize = commandSize
        self.vehicles = vehiclesNames
        self.state = UnitState(state)
        self.isRosterSet = isRosterSet
        return

    def __repr__(self):
        return 'UnitsListItem(cfdUnitID={0:n}, unitMgrID = {1:n}, creator = {2:>s}, rating = {3:n}, peripheryID = {4:n}, size = {5:n}/{6:n}, vehicles = {7!r:s}, state = {8!r:s})'.format(self.cfdUnitID, self.unitMgrID, self.creator, self.rating, self.peripheryID, self.playersCount, self.commandSize, self.vehicles, self.state)
# okay decompyling res/scripts/client/gui/prb_control/sequences.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:25:46 EST

# Embedded file name: scripts/client/gui/prb_control/sequences.py
import time
import BigWorld
from constants import PREBATTLE_CACHE_KEY, PREBATTLE_COMPANY_DIVISION_NAMES
from constants import PREBATTLE_TYPE
from gui.prb_control.info import PlayerPrbInfo
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
        return 'AutoInviteItem(prbID = {0:n}, peripheryID = {1:n}, type = {2:n} description = {3!r:s}, startTime = {4:n}, isValid = {5!r:s},)'.format(self.prbID, self.prbType, self.peripheryID, self.description, self.startTime, self.isValid)
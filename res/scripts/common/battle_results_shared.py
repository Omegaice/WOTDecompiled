# 2013.11.15 11:27:31 EST
# Embedded file name: scripts/common/battle_results_shared.py
import struct
from itertools import izip
from debug_utils import *
VEH_INTERACTION_DETAILS = (('spotted', 'B', 1, 0),
 ('deathReason', 'b', 10, -1),
 ('hits', 'H', 65535, 0),
 ('he_hits', 'H', 65535, 0),
 ('pierced', 'H', 65535, 0),
 ('damageDealt', 'H', 65535, 0),
 ('damageAssistedTrack', 'H', 65535, 0),
 ('damageAssistedRadio', 'H', 65535, 0),
 ('crits', 'I', 4294967295L, 0),
 ('fire', 'H', 65535, 0))
VEH_INTERACTION_DETAILS_NAMES = [ x[0] for x in VEH_INTERACTION_DETAILS ]
VEH_INTERACTION_DETAILS_MAX_VALUES = dict(((x[0], x[2]) for x in VEH_INTERACTION_DETAILS))
VEH_INTERACTION_DETAILS_INIT_VALUES = [ x[3] for x in VEH_INTERACTION_DETAILS ]
VEH_INTERACTION_DETAILS_LAYOUT = ''.join([ x[1] for x in VEH_INTERACTION_DETAILS ])
VEH_INTERACTION_DETAILS_INDICES = dict(((x[1][0], x[0]) for x in enumerate(VEH_INTERACTION_DETAILS)))
_VEH_CELL_RESULTS_PUBLIC = ('health', 'credits', 'xp', 'shots', 'hits', 'thits', 'he_hits', 'pierced', 'damageDealt', 'damageAssistedRadio', 'damageAssistedTrack', 'damageReceived', 'shotsReceived', 'noDamageShotsReceived', 'heHitsReceived', 'piercedReceived', 'spotted', 'damaged', 'kills', 'tdamageDealt', 'tkills', 'isTeamKiller', 'capturePoints', 'droppedCapturePoints', 'mileage', 'lifeTime', 'killerID', 'achievements', 'potentialDamageReceived')
_VEH_CELL_RESULTS_PRIVATE = ('repair', 'freeXP', 'details')
_VEH_CELL_RESULTS_SERVER = ('potentialDamageDealt', 'soloHitsAssisted', 'isEnemyBaseCaptured', 'stucks', 'autoAimedShots', 'presenceTime', 'spot_list', 'damage_list', 'kill_list', 'ammo', 'crewActivityFlags', 'series', 'tkillRating', 'tkillLog', 'destroyedObjects', 'achievementCredits', 'achievementXP', 'achievementFreeXP')
VEH_CELL_RESULTS = _VEH_CELL_RESULTS_PUBLIC + _VEH_CELL_RESULTS_PRIVATE + _VEH_CELL_RESULTS_SERVER
VEH_CELL_RESULTS_INDICES = dict(((x[1], x[0]) for x in enumerate(VEH_CELL_RESULTS)))
_VEH_BASE_RESULTS_PUBLIC = ('accountDBID', 'team', 'typeCompDescr', 'gold', 'deathReason')
_VEH_BASE_RESULTS_PRIVATE = ('xpPenalty', 'creditsPenalty', 'creditsContributionIn', 'creditsContributionOut')
_VEH_BASE_RESULTS_SERVER = ('eventIndices', 'vehLockTimeFactor', 'misc', 'cybersportRatingDeltas')
VEH_BASE_RESULTS = _VEH_CELL_RESULTS_PUBLIC + _VEH_BASE_RESULTS_PUBLIC + _VEH_CELL_RESULTS_PRIVATE + _VEH_BASE_RESULTS_PRIVATE + _VEH_CELL_RESULTS_SERVER + _VEH_BASE_RESULTS_SERVER
VEH_BASE_RESULTS_INDICES = dict(((x[1], x[0]) for x in enumerate(VEH_BASE_RESULTS)))
VEH_PUBLIC_RESULTS = _VEH_CELL_RESULTS_PUBLIC + _VEH_BASE_RESULTS_PUBLIC
VEH_PUBLIC_RESULTS_INDICES = dict(((x[1], x[0]) for x in enumerate(VEH_PUBLIC_RESULTS)))
VEH_FULL_RESULTS_UPDATE = ('tmenXP', 'isPremium', 'eventCredits', 'eventGold', 'eventXP', 'eventFreeXP', 'eventTMenXP', 'autoRepairCost', 'autoLoadCost', 'autoEquipCost', 'premiumXPFactor10', 'premiumCreditsFactor10', 'dailyXPFactor10', 'igrXPFactor10', 'aogasFactor10', 'markOfMastery', 'dossierPopUps')
VEH_FULL_RESULTS_UPDATE_INDICES = dict(((x[1], x[0]) for x in enumerate(VEH_FULL_RESULTS_UPDATE)))
_VEH_FULL_RESULTS_PRIVATE = ('originalCredits', 'originalXP', 'originalFreeXP', 'questsProgress')
VEH_FULL_RESULTS = _VEH_CELL_RESULTS_PUBLIC + _VEH_BASE_RESULTS_PUBLIC + _VEH_CELL_RESULTS_PRIVATE + _VEH_BASE_RESULTS_PRIVATE + VEH_FULL_RESULTS_UPDATE + _VEH_FULL_RESULTS_PRIVATE
VEH_FULL_RESULTS_INDICES = dict(((x[1], x[0]) for x in enumerate(VEH_FULL_RESULTS)))
PLAYER_INFO = ('name', 'clanDBID', 'clanAbbrev', 'prebattleID', 'team', 'igrType')
PLAYER_INFO_INDICES = dict(((x[1], x[0]) for x in enumerate(PLAYER_INFO)))
COMMON_RESULTS = ('arenaTypeID', 'arenaCreateTime', 'winnerTeam', 'finishReason', 'duration', 'bonusType', 'guiType', 'vehLockMode')
COMMON_RESULTS_INDICES = dict(((x[1], x[0]) for x in enumerate(COMMON_RESULTS)))
raise not set(VEH_FULL_RESULTS) & set(COMMON_RESULTS) or AssertionError

def dictToList(indices, d):
    l = [None] * len(indices)
    for name, index in indices.iteritems():
        l[index] = d[name]

    return l


def listToDict(names, l):
    d = {}
    for x in enumerate(names):
        d[x[1]] = l[x[0]]

    return d


class _VehicleInteractionDetailsItem(object):

    def __init__(self, values, offset):
        self.__values = values
        self.__offset = offset

    def __getitem__(self, key):
        return self.__values[self.__offset + VEH_INTERACTION_DETAILS_INDICES[key]]

    def __setitem__(self, key, value):
        self.__values[self.__offset + VEH_INTERACTION_DETAILS_INDICES[key]] = min(int(value), VEH_INTERACTION_DETAILS_MAX_VALUES[key])

    def __str__(self):
        return str(dict(self))

    def __iter__(self):
        return izip(VEH_INTERACTION_DETAILS_NAMES, self.__values[self.__offset:])


class VehicleInteractionDetails(object):

    def __init__(self, vehicleIDs, values):
        self.__vehicleIDs = vehicleIDs
        self.__values = values
        size = len(VEH_INTERACTION_DETAILS)
        self.__offsets = dict(((x[1], x[0] * size) for x in enumerate(self.__vehicleIDs)))

    @staticmethod
    def fromPacked(packed):
        count = len(packed) / struct.calcsize(''.join(['<I', VEH_INTERACTION_DETAILS_LAYOUT]))
        packedVehIDsLayout = '<%dI' % (count,)
        packedVehIDsLen = struct.calcsize(packedVehIDsLayout)
        vehicleIDs = struct.unpack(packedVehIDsLayout, packed[:packedVehIDsLen])
        values = struct.unpack('<' + VEH_INTERACTION_DETAILS_LAYOUT * count, packed[packedVehIDsLen:])
        return VehicleInteractionDetails(vehicleIDs, values)

    def __getitem__(self, vehicleID):
        offset = self.__offsets.get(vehicleID, None)
        if offset is None:
            self.__vehicleIDs.append(vehicleID)
            offset = len(self.__values)
            self.__values += VEH_INTERACTION_DETAILS_INIT_VALUES
            self.__offsets[vehicleID] = offset
        return _VehicleInteractionDetailsItem(self.__values, offset)

    def __contains__(self, vehicleID):
        return vehicleID in self.__offsets

    def __str__(self):
        return str(self.toDict())

    def pack(self):
        count = len(self.__vehicleIDs)
        packed = struct.pack(('<%dI' % count), *self.__vehicleIDs) + struct.pack(('<' + VEH_INTERACTION_DETAILS_LAYOUT * count), *self.__values)
        return packed

    def toDict(self):
        return dict([ (vehID, dict(_VehicleInteractionDetailsItem(self.__values, offset))) for vehID, offset in self.__offsets.iteritems() ])
# okay decompyling res/scripts/common/battle_results_shared.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:27:31 EST

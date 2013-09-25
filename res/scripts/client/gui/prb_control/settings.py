# Embedded file name: scripts/client/gui/prb_control/settings.py
from constants import PREBATTLE_TYPE
from prebattle_shared import SETTING_DEFAULTS, PrebattleSettings
VEHICLE_MIN_LEVEL = 1
VEHICLE_MAX_LEVEL = 10
VEHICLE_DEF_LEVEL_RANGE = (VEHICLE_MIN_LEVEL, VEHICLE_MAX_LEVEL)
TEAM_MAX_LIMIT = 150
DEFAULT_PREBATTLE_COOLDOWN = 5.0
INVITE_COMMENT_MAX_LENGTH = 400

class PREBATTLE_ACTION_NAME(object):
    UNDEFINED = ''
    RANDOM_QUEUE = 'randomQueue'
    TRAINING_LIST = 'trainingList'
    COMPANY_LIST = 'companyList'
    SPEC_BATTLE_LIST = 'specBattleList'
    PREBATTLE_LEAVE = 'prebattleLeave'
    SQUAD = 'squad'
    TOURNAMENT = 'tournament'
    CLAN = 'clan'


class PREBATTLE_INIT_STEP:
    SETTING_RECEIVED = 1
    ROSTERS_RECEIVED = 2
    INITED = SETTING_RECEIVED | ROSTERS_RECEIVED


class PREBATTLE_REQUEST(object):
    CREATE, ASSIGN, LEAVE, SET_TEAM_STATE, SET_PLAYER_STATE, SWAP_TEAMS, CHANGE_SETTINGS, CHANGE_OPENED, CHANGE_COMMENT, CHANGE_DIVISION, CHANGE_ARENA_VOIP, KICK, SEND_INVITE, PREBATTLES_LIST = range(1, 15)


PREBATTLE_REQUEST_NAME = dict([ (v, k) for k, v in PREBATTLE_REQUEST.__dict__.iteritems() ])

class PREBATTLE_SETTING_NAME(object):
    CREATOR = 'creator'
    IS_OPENED = 'isOpened'
    COMMENT = 'comment'
    ARENA_TYPE_ID = 'arenaTypeID'
    ROUND_LENGTH = 'roundLength'
    ARENA_VOIP_CHANNELS = 'arenaVoipChannels'
    DEFAULT_ROSTER = 'defaultRoster'
    VEHICLE_LOCK_MODE = 'vehicleLockMode'
    DIVISION = 'division'
    START_TIME = 'startTime'
    BATTLES_LIMIT = 'battlesLimit'
    WINS_LIMIT = 'winsLimit'
    EXTRA_DATA = 'extraData'
    LIMITS = 'limits'


class PREBATTLE_RESTRICTION:
    LIMIT_MIN_COUNT = 'limit/minCount'
    LIMIT_MAX_COUNT = 'limit/maxCount'
    LIMIT_LEVEL = 'limits/level'
    LIMIT_TOTAL_LEVEL = 'limit/totalLevel'
    LIMIT_CLASSES = 'limits/classes'
    LIMIT_CLASS_LEVEL = 'limits/classLevel'
    LIMIT_VEHICLES = 'limits/vehicles'
    LIMIT_NATIONS = 'limits/nations'
    LIMIT_COMPONENTS = 'limits/components'
    LIMIT_AMMO = 'limits/ammo'
    LIMIT_SHELLS = 'limits/shells'
    LIMIT_LIGHT_TANK = 'limits/classes/lightTank'
    LIMIT_MEDIUM_TANK = 'limits/classes/mediumTank'
    LIMIT_HEAVY_TANK = 'limits/classes/heavyTank'
    LIMIT_SPG = 'limits/classes/SPG'
    LIMIT_AT_SPG = 'limits/classes/AT-SPG'
    HAS_PLAYER_IN_BATTLE = 'player/inBattle'
    VEHICLE_NOT_READY = 'vehicle/notReady'
    VEHICLE_NOT_PRESENT = 'vehicle/notPresent'
    VEHICLE_IN_BATTLE = 'vehicle/inBattle'
    VEHICLE_BROKEN = 'vehicle/broken'
    CREW_NOT_FULL = 'crew/notFull'
    SERVER_LIMITS = (LIMIT_MIN_COUNT,
     LIMIT_MAX_COUNT,
     LIMIT_LEVEL,
     LIMIT_TOTAL_LEVEL,
     LIMIT_CLASSES,
     LIMIT_CLASS_LEVEL,
     LIMIT_VEHICLES,
     LIMIT_NATIONS,
     LIMIT_COMPONENTS,
     LIMIT_AMMO,
     LIMIT_SHELLS)
    VEHICLE_CLASS_LIMITS = (('lightTank', LIMIT_LIGHT_TANK),
     ('mediumTank', LIMIT_MEDIUM_TANK),
     ('heavyTank', LIMIT_HEAVY_TANK),
     ('SPG', LIMIT_SPG),
     ('AT-SPG', LIMIT_AT_SPG))
    VEHICLE_INVALID_STATES = (VEHICLE_NOT_READY,
     VEHICLE_NOT_PRESENT,
     VEHICLE_IN_BATTLE,
     VEHICLE_BROKEN)

    @classmethod
    def getVehClassRestrictions(cls):
        return dict(((restriction, tag) for tag, restriction in cls.VEHICLE_CLASS_LIMITS))

    @classmethod
    def getVehClassTags(cls):
        return dict(((tag, restriction) for tag, restriction in cls.VEHICLE_CLASS_LIMITS))

    @classmethod
    def inVehClassLimit(cls, search):
        for tag, restriction in cls.VEHICLE_CLASS_LIMITS:
            if restriction == search:
                return True

        return False


class PREBATTLE_ROSTER(object):
    UNKNOWN = -1
    ASSIGNED = 0
    UNASSIGNED = 16
    ASSIGNED_IN_TEAM1 = ASSIGNED | 1
    UNASSIGNED_IN_TEAM1 = UNASSIGNED | 1
    ASSIGNED_IN_TEAM2 = ASSIGNED | 2
    UNASSIGNED_IN_TEAM2 = UNASSIGNED | 2
    ALL = (ASSIGNED_IN_TEAM1,
     UNASSIGNED_IN_TEAM1,
     ASSIGNED_IN_TEAM2,
     UNASSIGNED_IN_TEAM2)
    PREBATTLE_RANGES = {PREBATTLE_TYPE.TRAINING: ALL,
     PREBATTLE_TYPE.SQUAD: (ASSIGNED_IN_TEAM1,),
     PREBATTLE_TYPE.COMPANY: (ASSIGNED_IN_TEAM1, UNASSIGNED_IN_TEAM1),
     PREBATTLE_TYPE.TOURNAMENT: ALL,
     PREBATTLE_TYPE.CLAN: ALL}

    @classmethod
    def getRange(cls, pbType, team = None):
        result = ()
        if pbType in cls.PREBATTLE_RANGES:
            result = cls.PREBATTLE_RANGES[pbType]
            if team is not None:
                result = filter(lambda r: r & team, result)
        return result


_PREBATTLE_DEFAULT_SETTINGS = SETTING_DEFAULTS
_PREBATTLE_DEFAULT_SETTINGS.update({'limits': {0: {},
            1: {},
            2: {}}})

def makePrebattleSettings(settings = None):
    if not settings:
        settings = _PREBATTLE_DEFAULT_SETTINGS
    return PrebattleSettings(settings)
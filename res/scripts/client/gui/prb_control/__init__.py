# Embedded file name: scripts/client/gui/prb_control/__init__.py
import BigWorld
from constants import PREBATTLE_TYPE, ARENA_GUI_TYPE, DEFAULT_LANGUAGE
from constants import PREBATTLE_TYPE_NAMES
from gui.prb_control.settings import makePrebattleSettings, VEHICLE_MAX_LEVEL

def getClientPrebattle():
    return getattr(BigWorld.player(), 'prebattle', None)


def getPrebattleID():
    clientPrb = getClientPrebattle()
    prbID = 0
    if clientPrb:
        prbID = clientPrb.id
    return prbID


def isPrebattleSettingsReceived(prebattle = None):
    if not prebattle:
        prb = getClientPrebattle()
        return prb is not None and prb.settings is not None
    else:
        return False


def getPrebattleSettings(prebattle = None):
    if not prebattle:
        prb = getClientPrebattle()
        return prb and prb.settings and makePrebattleSettings(prb.settings)
    return makePrebattleSettings()


def getPrebattleProps(prebattle = None):
    if not prebattle:
        prb = getClientPrebattle()
        result = {}
        result = prb and prb.properties and prb.properties
    return result


def getPrebattleRosters(prebattle = None):
    if not prebattle:
        prb = getClientPrebattle()
        result = {}
        result = prb and prb.rosters
    return result


def getPrebattleTeamStates(prebattle = None):
    if not prebattle:
        prb = getClientPrebattle()
        result = [None, 0, 0]
        result = prb and prb.teamStates
    return result


def getPrebattleType(prebattle = None, settings = None):
    try:
        if settings is None:
            settings = getPrebattleSettings(prebattle=prebattle)
        return settings['type']
    except KeyError:
        return

    return


def getPrebattleTypeName(prbType = None):
    if prbType is None:
        prbType = getPrebattleType()
    if prbType in PREBATTLE_TYPE_NAMES:
        prbTypeName = PREBATTLE_TYPE_NAMES[prbType]
    else:
        prbTypeName = 'PREBATTLE'
    return prbTypeName


ARENA_GUI_TYPE_BY_PRB_TYPE = {PREBATTLE_TYPE.SQUAD: ARENA_GUI_TYPE.RANDOM,
 PREBATTLE_TYPE.TRAINING: ARENA_GUI_TYPE.TRAINING,
 PREBATTLE_TYPE.COMPANY: ARENA_GUI_TYPE.COMPANY}

def getArenaGUIType(prbType = None):
    if prbType is None:
        prbType = getPrebattleType()
    arenaGuiType = ARENA_GUI_TYPE.RANDOM
    if prbType is not None:
        arenaGuiType = ARENA_GUI_TYPE.UNKNOWN
        if prbType in ARENA_GUI_TYPE_BY_PRB_TYPE:
            arenaGuiType = ARENA_GUI_TYPE_BY_PRB_TYPE[prbType]
    return arenaGuiType


def getTotalLevelLimits(teamLimits):
    return teamLimits['totalLevel']


def getLevelLimits(teamLimits):
    limit = teamLimits['level']
    return (limit[0], min(limit[1], VEHICLE_MAX_LEVEL))


def getNationsLimits(teamLimits):
    return teamLimits['nations']


def getMaxSizeLimits(teamLimits):
    return teamLimits['maxCount']


def getClassLevelLimits(teamLimits, classType):
    classesLimits = teamLimits['classes']
    if classesLimits is not None and classType not in classesLimits:
        return (0, 0)
    else:
        classLevel = teamLimits['classLevel']
        if classType in classLevel:
            limit = teamLimits['classLevel'][classType]
        else:
            limit = getLevelLimits(teamLimits)
        return (limit[0], min(limit[1], VEHICLE_MAX_LEVEL))


def getPrebattleLocalizedData(extraData = None):
    led = {}
    if extraData is None:
        extraData = getPrebattleSettings()['extraData']
    if extraData:
        from helpers import getClientLanguage
        lng = getClientLanguage()
        ld = extraData.get('localized_data', {})
        if ld:
            if lng in ld:
                led = ld[lng]
            elif DEFAULT_LANGUAGE in ld:
                led = ld[DEFAULT_LANGUAGE]
            else:
                sortedItems = ld.items()
                sortedItems.sort()
                led = sortedItems[0][1]
    return led


def getCreatorFullName():
    settings = getPrebattleSettings()
    creatorName = settings['creator']
    clanAbbrev = settings['creatorClanAbbrev']
    if clanAbbrev:
        fullName = '{0:>s}[{1:>s}]'.format(creatorName, clanAbbrev)
    else:
        fullName = creatorName
    return fullName


def areSpecBattlesHidden():
    return not getattr(BigWorld.player(), 'prebattleAutoInvites', None)


def isSquad(settings = None):
    return getPrebattleType(settings=settings) == PREBATTLE_TYPE.SQUAD


def isCompany(settings = None):
    return getPrebattleType(settings=settings) == PREBATTLE_TYPE.COMPANY


def isTraining(settings = None):
    return getPrebattleType(settings=settings) == PREBATTLE_TYPE.TRAINING


def isBattleSession(settings = None):
    return getPrebattleType(settings=settings) in (PREBATTLE_TYPE.TOURNAMENT, PREBATTLE_TYPE.CLAN)


def isParentControlActivated():
    from gui import game_control
    return game_control.g_instance.gameSession.isParentControlActive and not isTraining()
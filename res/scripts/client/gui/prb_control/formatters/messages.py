# 2013.11.15 11:25:39 EST
# Embedded file name: scripts/client/gui/prb_control/formatters/messages.py
from CurrentVehicle import g_currentVehicle
from UnitBase import UNIT_ERROR
from constants import JOIN_FAILURE_NAMES, KICK_REASON_NAMES
from debug_utils import LOG_ERROR
from gui import SystemMessages
from gui.Scaleform.locale.SYSTEM_MESSAGES import SYSTEM_MESSAGES
from gui.prb_control import getLevelLimits, getClassLevelLimits, getTotalLevelLimits
from gui.prb_control.settings import REQUEST_TYPE_NAMES, PREBATTLE_RESTRICTION
from gui.prb_control.settings import UNIT_ERROR_NAMES, UNIT_BROWSER_ERROR_NAMES
from gui.prb_control.settings import UNIT_ERRORS_TRANSLATE_AS_WARNINGS
from helpers import i18n
from prebattle_shared import LIMIT_DEFAULTS, decodeRoster

def getJoinFailureMessage(errorCode):
    if errorCode in JOIN_FAILURE_NAMES:
        error = JOIN_FAILURE_NAMES[errorCode]
    else:
        error = errorCode
    return i18n.makeString('#system_messages:arena_start_errors/join/%s' % error)


def getKickReasonMessage(reasonCode):
    if reasonCode in KICK_REASON_NAMES:
        reason = KICK_REASON_NAMES[reasonCode]
    else:
        reason = reasonCode
    return i18n.makeString('#system_messages:arena_start_errors/kick/%s' % reason)


def getPrbKickedFromQueueMessage(prbTypeName):
    guiName = prbTypeName.lower()
    if guiName != 'squad' and guiName != 'company':
        guiName = 'default'
    return i18n.makeString('#system_messages:prebattle_start_failed/kickedFromQueue/{0:>s}'.format(guiName))


def getVehicleNotPresentMessage():
    return i18n.makeString('#menu:hangar/no_current_vehicle_selected')


def getVehicleNotReadyMessage():
    return i18n.makeString('#system_messages:prebattle/vehicleInvalid/no_readyVehicle')


def getClassLimitMessage4Vehicle(teamLimits):
    classesList = map(lambda clazz: i18n.makeString('#menu:classes/%s' % clazz), teamLimits['classes'])
    return i18n.makeString('#system_messages:prebattle/vehicleInvalid/limits/classes') % ', '.join(classesList)


def getNationLimitMessage4Vehicle(teamLimits):
    nationsList = map(lambda nation: i18n.makeString('#menu:nations/%s' % nation), teamLimits['nations'])
    return i18n.makeString('#system_messages:prebattle/vehicleInvalid/limits/nations') % ', '.join(nationsList)


def getLevelLimitMessage4Vehicle(teamLimits):
    minLevel, maxLevel = getLevelLimits(teamLimits)
    return i18n.makeString('#system_messages:prebattle/vehicleInvalid/limits/level', minLevel, maxLevel)


def getClassLevelLimitMessage4Vehicle(teamLimits):
    minLevel, maxLevel = getClassLevelLimits(teamLimits, g_currentVehicle.item.type)
    return i18n.makeString('#system_messages:prebattle/vehicleInvalid/limits/level', minLevel, maxLevel)


def getMinCountLimitMessage4Team(teamLimits):
    return i18n.makeString('#system_messages:prebattle/teamInvalid/limit/minCount', minCount=teamLimits['minCount'])


def getTotalLevelLimitMessage4Team(teamLimits):
    minTotalLevel, maxTotalLevel = getTotalLevelLimits(teamLimits)
    return i18n.makeString('#system_messages:prebattle/teamInvalid/limit/totalLevel', minTotalLevel=minTotalLevel, maxTotalLevel=maxTotalLevel)


def getLevelLimitMessage4Team(teamLimits):
    minLevel, maxLevel = getLevelLimits(teamLimits)
    return i18n.makeString('#system_messages:prebattle/teamInvalid/limits/level', minLevel=minLevel, maxLevel=maxLevel)


_INVALID_VEHICLE_STATE = {PREBATTLE_RESTRICTION.VEHICLE_NOT_PRESENT: getVehicleNotPresentMessage,
 PREBATTLE_RESTRICTION.VEHICLE_NOT_READY: getVehicleNotReadyMessage}
_INVALID_VEHICLE_IN_TEAM = {PREBATTLE_RESTRICTION.LIMIT_CLASSES: getClassLimitMessage4Vehicle,
 PREBATTLE_RESTRICTION.LIMIT_NATIONS: getNationLimitMessage4Vehicle,
 PREBATTLE_RESTRICTION.LIMIT_LEVEL: getLevelLimitMessage4Vehicle,
 PREBATTLE_RESTRICTION.LIMIT_CLASS_LEVEL: getClassLevelLimitMessage4Vehicle}
_INVALID_TEAM = {PREBATTLE_RESTRICTION.LIMIT_MIN_COUNT: getMinCountLimitMessage4Team,
 PREBATTLE_RESTRICTION.LIMIT_TOTAL_LEVEL: getTotalLevelLimitMessage4Team,
 PREBATTLE_RESTRICTION.LIMIT_LEVEL: getLevelLimitMessage4Team}

def getInvalidTeamMessage(reason, functional = None):
    if reason in PREBATTLE_RESTRICTION.SERVER_LIMITS:
        if reason in _INVALID_TEAM:
            if functional:
                teamLimits = functional.getSettings().getTeamLimits(functional.getPlayerTeam())
            else:
                LOG_ERROR('Functional is not defined')
                teamLimits = LIMIT_DEFAULTS
            message = _INVALID_TEAM[reason](teamLimits)
        else:
            message = i18n.makeString('#system_messages:prebattle/teamInvalid/{0;>s}'.format(reason))
    else:
        LOG_ERROR('Reason can not be converted', reason)
        message = reason
    return message


def getInvalidVehicleMessage(reason, functional = None):
    if reason in _INVALID_VEHICLE_STATE:
        message = _INVALID_VEHICLE_STATE[reason]()
    elif reason in PREBATTLE_RESTRICTION.SERVER_LIMITS:
        if reason in _INVALID_VEHICLE_IN_TEAM:
            if functional:
                teamLimits = functional.getSettings().getTeamLimits(functional.getPlayerTeam())
            else:
                LOG_ERROR('Functional is not defined')
                teamLimits = LIMIT_DEFAULTS
            message = _INVALID_VEHICLE_IN_TEAM[reason](teamLimits)
        else:
            message = i18n.makeString('#system_messages:prebattle/vehicleInvalid/%s' % reason)
    else:
        LOG_ERROR('Reason can not be converted', reason)
        message = reason
    return message


def getRequestInCoolDownMessage(requestType, coolDown = 5.0):
    requestName = requestType
    if requestType in REQUEST_TYPE_NAMES:
        requestName = REQUEST_TYPE_NAMES[requestType]
        requestName = i18n.makeString('#system_messages:prebattle/request/name/{0:>s}'.format(requestName))
    return i18n.makeString('#system_messages:prebattle/request/isInCoolDown', request=requestName, coolDown=coolDown)


def getPlayerStateChangedMessage(prbName, playerInfo):
    if playerInfo.isOffline():
        key = '#system_messages:{0:>s}/memberOffline'.format(prbName)
    elif playerInfo.isReady():
        key = '#system_messages:{0:>s}/memberReady'.format(prbName)
    else:
        key = '#system_messages:{0:>s}/memberNotReady'.format(prbName)
    return i18n.makeString(key, playerInfo.getFullName())


def getPlayerAddedMessage(prbName, playerInfo):
    return i18n.makeString('#system_messages:{0:>s}/memberJoined'.format(prbName), playerInfo.getFullName())


def getPlayerRemovedMessage(prbName, playerInfo):
    return i18n.makeString('#system_messages:{0:>s}/memberLeave'.format(prbName), playerInfo.getFullName())


def getPlayerAssignFlagChanged(actorInfo, playerInfo):
    _, assigned = decodeRoster(playerInfo.roster)
    if assigned:
        key = '#system_messages:memberRosterChangedMain'
    else:
        key = '#system_messages:memberRosterChangedSecond'
    return i18n.makeString(key, actorInfo.getFullName(), playerInfo.getFullName())


def getUnitMessage(errorCode, errorString):
    errorName = UNIT_ERROR_NAMES[errorCode]
    if errorCode in UNIT_ERRORS_TRANSLATE_AS_WARNINGS:
        msgType = SystemMessages.SM_TYPE.Warning
        errorKey = SYSTEM_MESSAGES.unit_warnings(errorName)
    else:
        msgType = SystemMessages.SM_TYPE.Error
        errorKey = SYSTEM_MESSAGES.unit_errors(errorName)
    if errorKey is not None:
        msgBody = i18n.makeString(errorKey)
    else:
        msgBody = errorName + '\n' + errorString
    return (msgType, msgBody)


def getUnitKickedReasonMessage(reasonStr):
    return i18n.makeString(SYSTEM_MESSAGES.unit_warnings(reasonStr))


def getUnitBrowserMessage(errorCode, errorString):
    errorName = UNIT_BROWSER_ERROR_NAMES[errorCode]
    errorKey = SYSTEM_MESSAGES.unitbrowser_errors(errorName)
    if errorKey is not None:
        msgBody = i18n.makeString(errorKey)
    else:
        msgBody = errorName + '\n' + errorString
    return (SystemMessages.SM_TYPE.Error, msgBody)


def getUnitOnlineStatusChangedMessage(pInfo):
    if pInfo.isOffline():
        key = '#system_messages:unit/info/offlineStatus'
    else:
        key = '#system_messages:unit/info/onlineStatus'
    return i18n.makeString(key, userName=pInfo.getFullName())
# okay decompyling res/scripts/client/gui/prb_control/formatters/messages.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:25:39 EST

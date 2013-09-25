# Embedded file name: scripts/client/gui/prb_control/formatters/__init__.py
import types
import time
import BigWorld
from datetime import datetime
from gui.Scaleform.locale.CHAT import CHAT
from gui.Scaleform.locale.PREBATTLE import PREBATTLE
from gui.prb_control import getPrebattleLocalizedData, getPrebattleTypeName
from gui.prb_control import getCreatorFullName
from helpers import html, i18n
from helpers.time_utils import makeLocalServerTime

def makePrebattleWaitingID(requestName):
    return '{0:>s}/{1:>s}'.format(getPrebattleTypeName().lower(), requestName)


def getPrebattleLocalizedString(string, led = None, escapeHtml = False):
    result = ''
    if led:
        result = led.get(string, '')
        if type(result) is types.UnicodeType:
            result = result.encode('utf-8', 'ignore')
        if escapeHtml:
            html.escape(result)
    return result


def getPrebattleEventName(extraData = None, escapeHtml = False):
    led = getPrebattleLocalizedData(extraData)
    if led:
        return getPrebattleLocalizedString('event_name', led, escapeHtml)
    return ''


def getPrebattleSessionName(extraData = None, escapeHtml = False):
    led = getPrebattleLocalizedData(extraData)
    if led:
        return getPrebattleLocalizedString('session_name', led, escapeHtml)
    return ''


def getPrebattleDescription(extraData = None, escapeHtml = False):
    led = getPrebattleLocalizedData(extraData)
    if led:
        return getPrebattleLocalizedString('desc', led, escapeHtml)
    return ''


def getPrebattleFullDescription(extraData = None, escapeHtml = False):
    led = getPrebattleLocalizedData(extraData)
    description = ''
    if led:
        eventName = getPrebattleLocalizedString('event_name', led, escapeHtml)
        sessionName = getPrebattleLocalizedString('session_name', led, escapeHtml)
        description = '{0:>s}: {1:>s}'.format(eventName, sessionName)
    return description


def getPrebattleOpponents(extraData, escapeHtml = False):
    first = ''
    second = ''
    if 'opponents' in extraData:
        opponents = extraData['opponents']
        first = opponents.get('1', {}).get('name', '').encode('utf-8', 'ignore')
        second = opponents.get('2', {}).get('name', '').encode('utf-8', 'ignore')
        if escapeHtml:
            first = html.escape(first)
            second = html.escape(second)
    return (first, second)


def getPrebattleOpponentsString(extraData, escapeHtml = False):
    first, second = getPrebattleOpponents(extraData, escapeHtml=escapeHtml)
    result = ''
    if len(first) and len(second):
        result = i18n.makeString('#menu:opponents', firstOpponent=first, secondOpponent=second)
    return result


def getPrebattleStartTimeString(startTime):
    startTimeString = BigWorld.wg_getLongTimeFormat(startTime)
    if startTime - time.time() > 8640:
        startTimeString = '{0:>s} {1:>s}'.format(BigWorld.wg_getLongDateFormat(startTime), startTimeString)
    return startTimeString


def getBattleSessionStartTimeString(startTime):
    startTimeString = getPrebattleStartTimeString(startTime)
    return '%s %s' % (i18n.makeString(PREBATTLE.TITLE_BATTLESESSION_STARTTIME), startTimeString)


def getCompanyDivisionString(divisionName):
    if divisionName is None:
        divisionName = 'NA'
    return i18n.makeString('#prebattle:labels/company/division/{0:>s}'.format(divisionName))


def getCompanyName():
    return '{0:>s} {1:>s}'.format(i18n.makeString(CHAT.CHANNELS_TEAM), getCreatorFullName())


def getStartTimeLeft(startTime):
    if startTime:
        startTime = makeLocalServerTime(startTime)
        if datetime.utcfromtimestamp(startTime) > datetime.utcnow():
            return (datetime.utcfromtimestamp(startTime) - datetime.utcnow()).seconds
    return 0
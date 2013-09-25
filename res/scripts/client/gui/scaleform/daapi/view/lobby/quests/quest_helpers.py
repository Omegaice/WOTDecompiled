# Embedded file name: scripts/client/gui/Scaleform/daapi/view/lobby/quests/quest_helpers.py
import time
import BigWorld
from account_helpers.AccountSettings import AccountSettings
from helpers import i18n, int2roman
from debug_utils import LOG_DEBUG
from gui import makeHtmlString
from gui.shared import events, g_eventBus, g_itemsCache
from gui.shared.utils import CONST_CONTAINER
from gui.Scaleform.locale.QUESTS import QUESTS
_ONE_HOUR = 3600
_ONE_DAY = 24 * _ONE_HOUR
FINISH_TIME_LEFT_TO_SHOW = _ONE_DAY
START_TIME_LIMIT = 5 * _ONE_DAY
_PROGRESS_TOOLTIP_MAX_ITEMS = 4

class QUEST_STATUS(CONST_CONTAINER):
    COMPLETED = 'done'
    NOT_AVAILABLE = 'notAvailable'
    NONE = ''


class PROGRESS_BAR_TYPE(CONST_CONTAINER):
    STRATEGIC = 'strategic'
    SIMPLE = 'current'
    NONE = ''


def _getDateTimeString(timeValue):
    return '{0:>s} {1:>s}'.format(BigWorld.wg_getLongDateFormat(timeValue), BigWorld.wg_getShortTimeFormat(timeValue))


def getTimerMsg(q):
    startTimeLeft = q.getStartTimeLeft()
    if startTimeLeft > 0:
        gmtime = time.gmtime(startTimeLeft)
        if startTimeLeft > START_TIME_LIMIT:
            fmt = _getDateTimeString(q.getStartTime())
        elif START_TIME_LIMIT >= startTimeLeft > _ONE_DAY:
            gmtime = time.gmtime(q.getStartTimeLeft() - _ONE_DAY)
            fmt = time.strftime(i18n.makeString('#quests:item/timer/tillStart/days'), gmtime)
        elif _ONE_DAY >= startTimeLeft > _ONE_HOUR:
            fmt = time.strftime(i18n.makeString('#quests:item/timer/tillStart/hours'), gmtime)
        else:
            fmt = time.strftime(i18n.makeString('#quests:item/timer/tillStart/min'), gmtime)
        return makeHtmlString('html_templates:lobby/quests', 'timerTillStart', {'time': fmt})
    if FINISH_TIME_LEFT_TO_SHOW > q.getFinishTimeLeft() > 0:
        gmtime = time.gmtime(q.getFinishTimeLeft())
        if gmtime.tm_hour > 0:
            fmt = i18n.makeString('#quests:item/timer/tillFinish/longFormat')
        else:
            fmt = i18n.makeString('#quests:item/timer/tillFinish/shortFormat')
        return makeHtmlString('html_templates:lobby/quests', 'timerTillFinish', {'time': time.strftime(fmt, gmtime)})
    return ''


def getQuestStatus(q):
    if not q.isAvailable():
        return QUEST_STATUS.NOT_AVAILABLE
    if q.isCompleted():
        return QUEST_STATUS.COMPLETED
    return QUEST_STATUS.NONE


def getBonusCount(q):
    if not q.isCompleted() and q.isAvailable() and (q.getBonusLimit() is None or q.getBonusLimit() > 1):
        return q.getBonusCount()
    else:
        return -1


def getQuestCompletionDetails(q):
    bonusLimit = q.getBonusLimit()
    if bonusLimit is None:
        return i18n.makeString(QUESTS.DETAILS_HEADER_COMPLETION_UNLIMITED)
    else:
        groupBy = q.getCumulativeGroup()
        if q.isDaily():
            key = QUESTS.DETAILS_HEADER_COMPLETION_DAILY
            if groupBy is not None:
                key = '#quests:details/header/completion/daily/groupBy%s' % groupBy.capitalize()
        else:
            key = QUESTS.DETAILS_HEADER_COMPLETION_SINGLE
            if groupBy is not None:
                key = '#quests:details/header/completion/single/groupBy%s' % groupBy.capitalize()
        return i18n.makeString(key, count=bonusLimit)
        return


def getBonusesString(q):
    return '\n'.join([ b.format() for b in q.getBonuses().itervalues() ])


def getConditions(q):
    result = []
    if q.getDescription():
        result.append({'descr': q.getDescription()})
    for condName, cond in q.getConditions().iteritems():
        cData = {}
        if cond.isShowInGUI():
            if cond.getName() == 'meta':
                cData['descr'] = cond.parse()
            else:
                cData['descr'] = i18n.makeString('#quests:details/conditions/%s' % cond.getName())
                vehs = []
                for v in cond.parse():
                    vehs.append({'nationID': v.nationID,
                     'vIconSmall': v.iconSmall,
                     'vType': v.type,
                     'vLevel': v.level,
                     'vName': v.userName})

                cData['vehicles'] = vehs
            result.append(cData)

    if not len(result):
        return
    else:
        title = i18n.makeString(QUESTS.DETAILS_CONDITIONS_TITLE)
        if q.isStrategic():
            title = None
        return [{'title': title,
          'elements': result}]


def getQuestProgress(q, quests = None):
    result = (0,
     0,
     '',
     PROGRESS_BAR_TYPE.NONE,
     None)
    if not q.isAvailable() or q.isCompleted():
        return result
    elif q.isStrategic():
        subtasks = tuple((st for st in makeQuestGroup(q, quests) if st.getID() != q.getID()))
        if len(subtasks):
            return (len(filter(lambda t: t.isCompleted(), subtasks)),
             len(subtasks) + 1,
             '',
             PROGRESS_BAR_TYPE.STRATEGIC,
             None)
        return result
    p = q.getProgress()
    if p is not None:
        groupBy = q.getCumulativeGroup()
        groupByKey, current, total, label, nearestProgs = p
        tooltip = None
        if groupBy is not None and groupByKey is not None:
            name, names = ('', '')
            if groupBy == 'vehicle':
                name = g_itemsCache.items.getItemByCD(groupByKey).shortUserName
                names = [ g_itemsCache.items.getItemByCD(intCD).shortUserName for intCD in nearestProgs ]
            elif groupBy == 'nation':
                name = i18n.makeString('#menu:nations/%s' % groupByKey)
                names = [ i18n.makeString('#menu:nations/%s' % n) for n in nearestProgs ]
            elif groupBy == 'class':
                name = i18n.makeString('#menu:classes/%s' % groupByKey)
                names = [ i18n.makeString('#menu:classes/%s' % n) for n in nearestProgs ]
            elif groupBy == 'level':

                def makeLvlStr(lvl):
                    return i18n.makeString('#quests:tooltip/progress/groupBy/note/level', int2roman(lvl))

                name = makeLvlStr(int(groupByKey.replace('level ', '')))
                names = [ makeLvlStr(int(l.replace('level ', ''))) for l in nearestProgs ]
            note = None
            if len(names):
                note = makeHtmlString('html_templates:lobby/quests/tooltips/progress', 'note', {'names': ', '.join(names[:_PROGRESS_TOOLTIP_MAX_ITEMS])})
            tooltip = {'header': i18n.makeString('#quests:tooltip/progress/groupBy/header'),
             'body': makeHtmlString('html_templates:lobby/quests/tooltips/progress', 'body', {'name': name}),
             'note': note}
        return (current,
         total,
         label,
         PROGRESS_BAR_TYPE.SIMPLE,
         tooltip)
    else:
        return result


def makeQuestGroup(q, quests = None):
    if q.isStrategic() or q.isSubtask():
        quests = quests or {}
        group = list((quests[qID] for qID in q.getGroup() if qID in quests))
        return group
    return []


def packSubQuest(q, quests = None):
    subTasks = []
    nextSubTask = []

    def pack(qList, title = '', noProgressInfo = False):
        result = []
        for q in qList:
            result.append({'title': title,
             'questInfo': packQuest(q, quests, noProgressInfo=noProgressInfo)})

        return result

    group = makeQuestGroup(q, quests)
    if q.isStrategic():
        subTasks = pack(list((st for st in group if st.getID() != q.getID())), i18n.makeString(QUESTS.DETAILS_TASKS_SUBTASK))
    elif q.isSubtask():
        if q.getSeqID() != -1:
            for idx, st in enumerate(group):
                if st.getID() == q.getID() and idx != len(group) - 1:
                    nextSubTask = pack([group[idx + 1]], i18n.makeString(QUESTS.DETAILS_TASKS_NEXTTASK), True)
                    break

        if len(group) > 0 and group[0].isStrategic():
            subTasks = pack([group[0]], i18n.makeString(QUESTS.DETAILS_TASKS_STRATEGIC), True)
    return (subTasks, nextSubTask)


def packQuest(q, quests = None, linkUp = False, linkDown = False, noProgressInfo = False, noProgressTooltip = False):
    visited = AccountSettings.getSettings('quests').get('visited', [])
    status = getQuestStatus(q)
    bonusCount = getBonusCount(q)
    qProgCur, qProgTot, qProgLabl, qProgbarType, tooltip = getQuestProgress(q, quests)
    if noProgressInfo:
        bonusCount = -1
        status = QUEST_STATUS.NONE
        qProgCur, qProgTot, qProgLabl, qProgbarType, tooltip = (0,
         0,
         '',
         PROGRESS_BAR_TYPE.NONE,
         None)
    if noProgressTooltip:
        tooltip = None
    return {'questID': q.getID(),
     'isNew': q.getID() not in visited and not q.isCompleted() and q.isAvailable(),
     'status': status,
     'IGR': q.isIGR(),
     'taskType': q.getUserType(),
     'description': q.getUserName(),
     'timerDescr': getTimerMsg(q),
     'tasksCount': bonusCount,
     'progrBarType': qProgbarType,
     'progrTooltip': tooltip,
     'maxProgrVal': qProgTot,
     'currentProgrVal': qProgCur,
     'isLock': linkDown,
     'isLocked': linkUp}


def packQuestDetails(q, quests = None):
    dateString = i18n.makeString(QUESTS.DETAILS_HEADER_TILLDATE, finishTime=_getDateTimeString(q.getFinishTime()))
    if q.getStartTimeLeft() > 0:
        dateString = i18n.makeString('#quests:details/header/activeDuration', startTime=_getDateTimeString(q.getStartTime()), finishTime=_getDateTimeString(q.getFinishTime()))
    errorMsg = ''
    if not q._checkForInvVehicles():
        errorMsg = i18n.makeString(QUESTS.DETAILS_HEADER_HASNOVEHICLES)
    qProgCur, qProgTot, qProgLabl, qProgbarType, tooltip = getQuestProgress(q, quests)
    subTasks, nextTasks = packSubQuest(q, quests)
    qInfo = None
    if q.isStrategic():
        qInfo = {'title': i18n.makeString('#quests:details/header/info/title'),
         'descr': i18n.makeString('#quests:details/header/info/descr_parallel')}
        if q.isSerialGroup():
            qInfo['descr'] = i18n.makeString('#quests:details/header/info/descr_serial')
    return {'header': {'title': q.getUserName(),
                'date': dateString,
                'type': getQuestCompletionDetails(q),
                'impDescr': errorMsg,
                'status': getQuestStatus(q),
                'progrBarType': qProgbarType,
                'progrTooltip': tooltip,
                'maxProgrVal': qProgTot,
                'currentProgrVal': qProgCur,
                'tasksCount': getBonusCount(q)},
     'info': {'descr': qInfo,
              'subtasks': subTasks,
              'conditions': getConditions(q)},
     'award': getBonusesString(q),
     'nextTasks': nextTasks}


def getNewQuests(quests):
    visited = AccountSettings.getSettings('quests').get('visited', [])
    return filter(lambda q: q.getID() not in visited and not q.isCompleted() and q.isAvailable(), quests.itervalues())


def visitQuestsGUI(quest):
    if quest is None:
        return
    else:
        quests = {quest.getID: quest}
        s = dict(AccountSettings.getSettings('quests'))
        active = set((q.getID() for q in quests.itervalues() if not q.isCompleted() and q.isAvailable()))
        completed = set((q.getID() for q in quests.itervalues() if q.isCompleted()))
        s['visited'] = tuple(set(s['visited']).difference(completed) | active)
        s['lastVisitTime'] = time.time()
        AccountSettings.setSettings('quests', s)
        g_eventBus.handleEvent(events.LobbySimpleEvent(events.LobbySimpleEvent.QUEST_VISITED, {'questID': quest.getID()}))
        return
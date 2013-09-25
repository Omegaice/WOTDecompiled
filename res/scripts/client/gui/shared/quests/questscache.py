import zlib
import pickle
from collections import defaultdict
import BigWorld
from Event import Event
from adisp import async
from helpers import isPlayerAccount
from debug_utils import LOG_ERROR, LOG_CURRENT_EXCEPTION
from gui.shared.utils.requesters.QuestsProgress import QuestsProgress
from gui.shared.quests.event_items import Quest

class _QuestsCache(object):

    def __init__(self):
        self.__progress = QuestsProgress()
        self.__waitForSync = False
        self.onSyncStarted = Event()
        self.onSyncCompleted = Event()

    def init(self):
        pass

    def fini(self):
        self.onSyncStarted.clear()
        self.onSyncCompleted.clear()

    @property
    def waitForSync(self):
        return self.__waitForSync

    @property
    def progress(self):
        return self.__progress

    @async
    def update(self, callback = None):
        self.__invalidateData(callback)

    @classmethod
    def makeQuestsGroups(cls, quests):
        tasks = []
        groups = defaultdict(lambda : [])
        for qID, q in quests.iteritems():
            if q.getGroupID() is None:
                tasks.append(q)
            elif q.isStrategic():
                tasks.append(q)
                groups[q.getGroupID()].insert(0, q)
            else:
                groups[q.getGroupID()].append(q)

        return (tasks, groups)

    def getQuests(self, filterFunc = None):
        quests = self.__getQuestsData()
        filterFunc = filterFunc or (lambda a: True)
        result = {}
        for qID, qData in quests.iteritems():
            q = Quest(qID, qData, self.__progress.getQuestProgress(qID))
            if q.getDestroyingTimeLeft() <= 0:
                continue
            if not filterFunc(q):
                continue
            result[qID] = q

        _, groups = self.makeQuestsGroups(result)
        for q in result.itervalues():
            if q.isSubtask() or q.isStrategic():
                q.setGroup(groups[q.getGroupID()])

        return result

    def getCurrentQuests(self):
        return self.getQuests(lambda q: q.getStartTimeLeft() <= 0 and q.getFinishTimeLeft() > 0)

    def getFutureQuests(self):
        return self.getQuests(lambda q: q.getStartTimeLeft() > 0)

    def _onResync(self, *args):
        self.__invalidateData()

    @classmethod
    def __getQuestGroupID(cls, qData):
        return qData.get('groupID') or None

    @classmethod
    def __getQuestSeqID(cls, qData):
        return qData.get('seqID', -1)

    def __invalidateData(self, callback = lambda *args: None):

        def cbWrapper(*args):
            self.__waitForSync = False
            self.onSyncCompleted()
            callback(*args)

        self.__waitForSync = True
        self.onSyncStarted()
        self.__progress.request()(cbWrapper)

    def __getQuestsData(self):
        try:
            if isPlayerAccount():
                if 'questsClientData' in BigWorld.player().eventsData:
                    return pickle.loads(zlib.decompress(BigWorld.player().eventsData['questsClientData']))
                return {}
            LOG_ERROR('Trying to get quests data from not account player', BigWorld.player())
        except Exception:
            LOG_CURRENT_EXCEPTION()

        return {}


g_questsCache = _QuestsCache()

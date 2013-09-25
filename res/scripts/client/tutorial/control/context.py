# Embedded file name: scripts/client/tutorial/control/context.py
from abc import ABCMeta, abstractmethod
from tutorial.control import TutorialProxyHolder
from tutorial.logger import LOG_MEMORY
__all__ = ['StartReqs',
 'BonusesRequester',
 'SoundPlayer',
 'GlobalStorage']

class StartReqs(object):
    __meta__ = ABCMeta

    def __init__(self, loader, ctx):
        super(StartReqs, self).__init__()
        self._loader = loader
        self._ctx = ctx

    def __del__(self):
        LOG_MEMORY('StartReqs deleted: {0:>s}'.format(self))

    def _clear(self):
        self._loader = None
        self._ctx = None
        return

    def _flush(self):
        args = (self._loader, self._ctx)
        self._clear()
        return args

    @abstractmethod
    def isEnabled(self):
        pass

    @abstractmethod
    def process(self):
        pass


class BonusesRequester(TutorialProxyHolder):
    __meta__ = ABCMeta

    def __init__(self, completed):
        super(BonusesRequester, self).__init__()
        self._completed = completed

    def getCompleted(self):
        return self._completed

    def setCompleted(self, completed):
        self._completed = completed

    def isStillRunning(self):
        return False

    def getChapter(self, chapterID = None):
        chapter = self._data
        if chapterID is not None and len(chapterID):
            chapter = self._tutorial._descriptor.getChapter(chapterID)
        return chapter

    @abstractmethod
    def request(self, chapterID = None):
        pass


class SOUND_EVENT:
    TASK_FAILED = 0
    TASK_COMPLETED = 1
    NEXT_CHAPTER = 2
    SPEAKING = 3


class SoundPlayer(object):
    __meta__ = ABCMeta

    def __init__(self):
        super(SoundPlayer, self).__init__()
        self._muted = False
        self._enabled = False

    def setMuted(self, value):
        self._muted = value

    def isMuted(self):
        return self._muted

    def setEnabled(self, value):
        self._enabled = value

    def isEnabled(self):
        return self._enabled

    @abstractmethod
    def play(self, event, sndID = None):
        pass

    @abstractmethod
    def stop(self):
        pass

    def isPlaying(self, event, sndID = None):
        return False

    def goToNextChapter(self):
        pass


class NoSound(SoundPlayer):

    def play(self, event, sndID = None):
        pass

    def stop(self):
        pass


class GLOBAL_VAR(object):
    LAST_HISTORY_ID = '_TutorialLastHistoryID'
    ALL = [LAST_HISTORY_ID]


class GLOBAL_FLAG(object):
    IS_FLAGS_RESET = '_TutorialIsFlagsReset'
    SHOW_HISTORY = '_TutorialShowHistory'
    HISTORY_NOT_AVAILABLE = '_TutorialHistoryNotAvailable'
    IN_QUEUE = '_InTutorialQueue'
    ALL = [IS_FLAGS_RESET,
     SHOW_HISTORY,
     HISTORY_NOT_AVAILABLE,
     IN_QUEUE]


class GlobalStorage(object):
    __slots__ = ('attribute',)
    __storage = {}
    __default = {}

    def __init__(self, attribute, defaultValue):
        self.attribute = attribute
        if attribute not in self.__storage:
            self.__storage[attribute] = defaultValue
            if attribute in GLOBAL_VAR.ALL:
                self.__default[attribute] = defaultValue

    def __repr__(self):
        return 'GlobalStorage {0:s}: {1!r:s}'.format(self.attribute, self.__storage.get(self.attribute))

    def __set__(self, _, value):
        self.__storage[self.attribute] = value

    def __get__(self, instance, owner = None):
        if instance is None:
            return self
        else:
            return self.__storage[self.attribute]

    def value(self):
        return self.__storage[self.attribute]

    @classmethod
    def clearFlags(cls):
        for flag in GLOBAL_FLAG.ALL:
            if flag in cls.__storage:
                cls.__storage[flag] = False

    @classmethod
    def clearVars(cls):
        for var in GLOBAL_VAR.ALL:
            if var in cls.__storage:
                cls.__storage[var] = cls.__default[var]

    @classmethod
    def all(cls):
        return cls.__storage.copy()

    @classmethod
    def getValue(cls, attribute):
        result = None
        if attribute in cls.__storage:
            result = cls.__storage[attribute]
        return result

    @classmethod
    def setValue(cls, attribute, value):
        cls.__storage[attribute] = value


class ClientCtx(object):

    @classmethod
    def fetch(cls, *args):
        pass

    @classmethod
    def makeCtx(cls, record):
        pass

    def makeRecord(self):
        pass
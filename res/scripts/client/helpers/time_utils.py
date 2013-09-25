# Embedded file name: scripts/client/helpers/time_utils.py
import time, BigWorld, datetime, calendar
from debug_utils import *

class _TimeCorrector(object):

    def __init__(self):
        self._evalTimeCorrection(time.time())

    def _evalTimeCorrection(self, serverUTCTime):
        self.__clientLoginTime = BigWorld.time()
        self.__serverLoginUTCTime = serverUTCTime

    def __loginDelta(self):
        return BigWorld.time() - self.__clientLoginTime

    timeCorrection = property(lambda self: self.serverUTCTime - time.time())
    serverUTCTime = property(lambda self: self.__serverLoginUTCTime + self.__loginDelta())

    @property
    def serverRegionalTime(self):
        regionalSecondsOffset = 0
        try:
            serverRegionalSettings = BigWorld.player().serverSettings['regional_settings']
            regionalSecondsOffset = serverRegionalSettings['starting_time_of_a_new_day']
        except Exception:
            LOG_CURRENT_EXCEPTION()

        return _g_instance.serverUTCTime + regionalSecondsOffset


_g_instance = _TimeCorrector()

def setTimeCorrection(serverUTCTime):
    _g_instance._evalTimeCorrection(serverUTCTime)


def makeLocalServerTime(serverTime):
    if serverTime:
        return serverTime - _g_instance.timeCorrection
    else:
        return None


def makeLocalServerDatetime(serverDatetime):
    if isinstance(serverDatetime, datetime.datetime):
        return serverDatetime - datetime.timedelta(seconds=_g_instance.timeCorrection)
    else:
        return None


def utcToLocalDatetime(utcDatetime):
    return datetime.datetime.fromtimestamp(calendar.timegm(utcDatetime.timetuple()))
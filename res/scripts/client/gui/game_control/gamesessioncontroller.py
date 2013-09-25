# Embedded file name: scripts/client/gui/game_control/GameSessionController.py
import BigWorld, Event, account_shared, time, constants
from adisp import process
from helpers import time_utils
from debug_utils import *

class GameSessionController(object):
    """ Game playing time and parent controlling class. """
    DAY_DURATION = 86400
    NOTIFY_PERIOD = 3600
    PLAY_TIME_LEFT_NOTIFY = 900
    MIDNIGHT_BLOCK_TIME = DAY_DURATION - PLAY_TIME_LEFT_NOTIFY
    onClientNotify = Event.Event()
    onTimeTillBan = Event.Event()

    def init(self):
        """ Singleton initialization method """
        self.__sessionStartedAt = -1
        self.__stats = None
        self.__notifyCallback = None
        self.__banCallback = None
        self.isAdult = True
        self.isPlayTimeBlock = False
        self.__midnightBlockTime = None
        self.__playTimeBlockTime = None
        self.__doNotifyInStart = False
        LOG_DEBUG('GameSessionController::init')
        return

    def fini(self):
        """        Singleton finalization method """
        self.stop()
        self.onClientNotify.clear()
        self.onTimeTillBan.clear()
        LOG_DEBUG('GameSessionController::fini')

    @process
    def start(self, sessionStartTime):
        """
        Starting new game session.
        @param sessionStartTime: session start time (server time)
        """
        LOG_DEBUG('GameSessionController::start', sessionStartTime)
        from gui.shared.utils.requesters import StatsRequesterr
        self.__stats = yield StatsRequesterr().request()
        self.__sessionStartedAt = sessionStartTime
        if constants.RESTRICTION_TYPE.BAN in self.__stats.restrictions:
            for ban in self.__stats.restrictions[constants.RESTRICTION_TYPE.BAN].itervalues():
                if ban.get('reason') == '#ban_reason:curfew_ban':
                    self.isAdult = False

        if self.__doNotifyInStart:
            self.__notifyClient()
        else:
            self.__startNotifyCallback()
        if self.__banCallback is None:
            self.__midnightBlockTime = self.MIDNIGHT_BLOCK_TIME - self.serverRegionalTime
            playTimeLeft = min([self.getDailyPlayTimeLeft(), self.getWeeklyPlayTimeLeft()])
            self.__playTimeBlockTime = playTimeLeft - self.PLAY_TIME_LEFT_NOTIFY
            self.isPlayTimeBlock = self.__playTimeBlockTime < self.__midnightBlockTime
            self.__banCallback = BigWorld.callback(self.__getBlockTime(), self.__onBanNotifyHandler)
        return

    def stop(self, doNotifyInStart = False):
        """ Stopping current game session """
        LOG_DEBUG('GameSessionController::stop')
        self.__sessionStartedAt = -1
        self.__stats = None
        self.__doNotifyInStart = doNotifyInStart
        self.__clearBanCallback()
        self.__clearNotifyCallback()
        return

    def isSessionStartedThisDay(self):
        """
        Is game session has been started at this day or not
        @return: <bool> flag
        """
        serverRegionalSettings = BigWorld.player().serverSettings['regional_settings']
        return int(time_utils._g_instance.serverRegionalTime) / 86400 == int(self.__sessionStartedAt + serverRegionalSettings['starting_time_of_a_new_day']) / 86400

    def getDailyPlayTimeLeft(self):
        """
        Returns value of this day playing time left in seconds
        @return: playting time left
        """
        d, _ = self.__stats.playLimits
        return d[0] - self._getDailyPlayHours()

    def getWeeklyPlayTimeLeft(self):
        """
        Returns value of this week playing time left in seconds
        @return: playting time left
        """
        _, w = self.__stats.playLimits
        return w[0] - self._getWeeklyPlayHours()

    @property
    def isParentControlEnabled(self):
        """
        Is parent control enabled. Algo has been taken
        from a_mikhailik.
        """
        d, w = self.__stats.playLimits
        return d[0] < self.DAY_DURATION or w[0] < 7 * self.DAY_DURATION

    @property
    def isParentControlActive(self):
        """
        Is parent control active now: current time between
        MIDNIGHT_BLOCK_TIME and midnight or playing time is less
        than PLAY_TIME_LEFT_NOTIFY.
        
        @return: <bool> is parent control active now
        """
        parentControl = self.isParentControlEnabled and min([self.getDailyPlayTimeLeft(), self.getWeeklyPlayTimeLeft()]) <= self.PLAY_TIME_LEFT_NOTIFY
        curfewControl = not self.isAdult and self.serverRegionalTime >= self.MIDNIGHT_BLOCK_TIME
        return parentControl or curfewControl

    @property
    def sessionDuration(self):
        """
        @return: <int> current session duration
        """
        return time_utils._g_instance.serverUTCTime - self.__sessionStartedAt

    @property
    def serverRegionalTime(self):
        """
        @return: current server time according to the server's regional settings
        """
        serverTimeStruct = time.gmtime(time_utils._g_instance.serverRegionalTime)
        return serverTimeStruct.tm_hour * 60 * 60 + serverTimeStruct.tm_min * 60 + serverTimeStruct.tm_sec

    def _getDailyPlayHours(self):
        """
        Returns value of this day playing time in seconds.
        @return: <int> playing time
        """
        if self.isSessionStartedThisDay():
            return self.__stats.dailyPlayHours[0] + (time_utils._g_instance.serverUTCTime - self.__sessionStartedAt)
        else:
            return self.__stats.dailyPlayHours[0] + time_utils._g_instance.serverRegionalTime % 86400

    def _getWeeklyPlayHours(self):
        """
        Returns value of this week playing time in seconds.
        @return: <int> playing time
        """
        serverRegionalSettings = BigWorld.player().serverSettings['regional_settings']
        weekDaysCount = account_shared.currentWeekPlayDaysCount(time_utils._g_instance.serverUTCTime, serverRegionalSettings['starting_time_of_a_new_day'], serverRegionalSettings['starting_day_of_a_new_week'])
        return self._getDailyPlayHours() + sum(self.__stats.dailyPlayHours[1:weekDaysCount])

    def __getBlockTime(self):
        return (self.__playTimeBlockTime if self.isPlayTimeBlock else self.__midnightBlockTime) + 5

    def __startNotifyCallback(self):
        self.__clearNotifyCallback()
        self.__notifyCallback = BigWorld.callback(self.NOTIFY_PERIOD, self.__notifyClient)

    def __clearNotifyCallback(self):
        if self.__notifyCallback is not None:
            BigWorld.cancelCallback(self.__notifyCallback)
            self.__notifyCallback = None
        return

    def __clearBanCallback(self):
        if self.__banCallback is not None:
            BigWorld.cancelCallback(self.__banCallback)
            self.__banCallback = None
        return

    def __notifyClient(self):
        playTimeLeft = None
        if self.isParentControlEnabled:
            playTimeLeft = min([self.getDailyPlayTimeLeft(), self.getWeeklyPlayTimeLeft()])
            playTimeLeft = max(playTimeLeft, 0)
        self.onClientNotify(self.sessionDuration, self.DAY_DURATION - self.serverRegionalTime, playTimeLeft)
        self.__startNotifyCallback()
        return

    def __onBanNotifyHandler(self):
        """ Ban notification event handler """
        LOG_DEBUG('GameSessionController:__onBanNotifyHandler')
        self.onTimeTillBan(self.isPlayTimeBlock, time.strftime('%H:%M', time.gmtime(time.time() + self.PLAY_TIME_LEFT_NOTIFY)))
        self.__banCallback = BigWorld.callback(self.DAY_DURATION, self.__onBanNotifyHandler)
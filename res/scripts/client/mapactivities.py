# 2013.11.15 11:27:09 EST
# Embedded file name: scripts/client/MapActivities.py
import BigWorld
import Math
import ResMgr
import Pixie
import PlayerEvents
import random
import copy
import SoundGroups
from constants import ARENA_PERIOD
from debug_utils import *

class IMapActivity:

    def create(self, settings, startTime):
        pass

    def destroy(self):
        self.stop()

    def start(self):
        pass

    def stop(self):
        pass

    def canStart(self):
        return False

    def isActive(self):
        return False


class MapActivities(object):

    def __init__(self):
        self.__cbID = BigWorld.callback(0.1, self.__onPeriodicTimer)
        self.__isOnArena = False
        self.__pendingActivities = []
        self.__currActivities = []
        PlayerEvents.g_playerEvents.onArenaPeriodChange += self.__onArenaPeriodChange

    def destroy(self):
        BigWorld.cancelCallback(self.__cbID)
        self.__cbID = None
        self.stop()
        PlayerEvents.g_playerEvents.onArenaPeriodChange -= self.__onArenaPeriodChange
        return

    def stop(self):
        for activity in self.__currActivities:
            activity.stop()

        self.__currActivities = []
        self.__pendingActivities = []

    def generateHangarActivities(self, spacePath):
        xmlName = spacePath.split('/')[-1]
        settings = ResMgr.openSection('scripts/arena_defs/' + xmlName + '.xml/mapActivities')
        if settings is not None:
            SoundGroups.g_instance.enableArenaSounds(True)
        else:
            return
        startTimes = []
        for activityXML in settings.values():
            timeframe = activityXML.readVector2('startTime')
            possibility = activityXML.readFloat('possibility', 1.0)
            if possibility < random.uniform(0, 1):
                startTimes.append(-1)
            else:
                startTimes.append(BigWorld.serverTime() + random.uniform(timeframe[0], timeframe[1]))

        self.__generateActivities(settings, startTimes)
        return

    def generateArenaActivities(self, startTimes):
        arenaType = BigWorld.player().arena.arenaType
        self.__generateActivities(arenaType.mapActivitiesSection, startTimes)

    def __generateActivities(self, settings, startTimes):
        self.__pendingActivities = []
        if settings is None or len(startTimes) != len(settings.items()):
            return
        else:
            i = -1
            for activityType, activityXML in settings.items():
                i += 1
                startTime = startTimes[i]
                if startTime == -1:
                    continue
                activity = _createActivity(activityType)
                if activity is not None:
                    activity.create(activityXML, startTime)
                    self.__pendingActivities.append(activity)

            return

    def __onPeriodicTimer(self):
        for activity in self.__pendingActivities:
            if activity.canStart():
                activity.start()
                self.__currActivities.append(activity)
                self.__pendingActivities.remove(activity)

        self.__cbID = BigWorld.callback(0.1, self.__onPeriodicTimer)

    def __onArenaPeriodChange(self, period, periodEndTime, periodLength, periodAdditionalInfo):
        isOnArena = period == ARENA_PERIOD.BATTLE
        if isOnArena and not self.__isOnArena:
            self.generateArenaActivities(periodAdditionalInfo)
        elif not isOnArena and self.__isOnArena:
            self.stop()
        self.__isOnArena = isOnArena


class WarplaneActivity(IMapActivity):

    def create(self, settings, startTime):
        self.__settings = settings
        self.__curve = None
        self.__model = None
        self.__motor = None
        self.__sound = None
        self.__particles = None
        self.__particlesNode = None
        self.__cbID = None
        self.__startTime = startTime
        self.__canStart = True
        self.__fadedIn = False
        if BigWorld.serverTime() > self.__startTime + 5.0:
            self.__canStart = False
            return
        else:
            self.__curve = BigWorld.WGActionCurve(self.__settings)
            self.__modelName = self.__curve.getChannelProperty(0, 'modelName').asString
            BigWorld.loadResourceListBG((self.__modelName,), self.__onModelLoaded)
            return

    def isActive(self):
        return self.__model is not None

    def canStart(self):
        return self.__canStart and BigWorld.serverTime() >= self.__startTime and self.__model is not None

    def start(self):
        self.__model = BigWorld.Model(self.__curve.getChannelProperty(0, 'modelName').asString)
        BigWorld.addModel(self.__model)
        self.__motor = BigWorld.WGWarplaneMotor(self.__curve, 0)
        self.__model.addMotor(self.__motor)
        ds = self.__curve.getChannelProperty(0, 'soundName')
        soundName = ds.asString if ds is not None else ''
        if soundName != '':
            try:
                self.__sound = self.__model.playSound(soundName)
                self.__sound.volume = 0.0
            except:
                self.__sound = None
                LOG_CURRENT_EXCEPTION()

        self.__update()
        return

    def stop(self):
        if self.__cbID is not None:
            BigWorld.cancelCallback(self.__cbID)
            self.__cbID = None
        if self.__model is not None:
            self.__model.delMotor(self.__motor)
            if self.__model in BigWorld.models():
                BigWorld.delModel(self.__model)
            self.__model = None
            self.__motor = None
            self.__curve = None
        if self.__sound is not None:
            self.__sound.stop()
            self.__sound = None
        if self.__particles is not None:
            self.__particlesNode.detach(self.__particles)
            self.__particlesNode = None
            self.__particles = None
        return

    def __update(self):
        self.__cbID = None
        visibility = self.__motor.warplaneAlpha
        if self.__sound is not None and self.__sound.isPlaying:
            self.__sound.volume = visibility
        if visibility == 1.0 and not self.__fadedIn:
            self.__fadedIn = True
            ds = self.__curve.getChannelProperty(0, 'effectName')
            effectName = ds.asString if ds is not None else ''
            if effectName != '':
                Pixie.createBG(effectName, self.__onParticlesLoaded)
        elif visibility <= 0.1 and self.__fadedIn:
            self.stop()
            return
        self.__cbID = BigWorld.callback(0, self.__update)
        return

    def __onModelLoaded(self, resourceRefs):
        if self.__modelName not in resourceRefs.failedIDs:
            self.__model = resourceRefs[self.__modelName]
        else:
            LOG_ERROR('Could not load model %s' % self.__modelName)

    def __onParticlesLoaded(self, particles):
        if self.__curve is None:
            return
        else:
            propValue = self.__curve.getChannelProperty(0, 'effectHardpoint')
            if propValue is None:
                return
            hardPointName = propValue.asString
            if hardPointName != '':
                self.__particles = particles
                self.__particlesNode = self.__model.node(hardPointName)
                self.__particlesNode.attach(self.__particles)
            return


def _createActivity(typeName):
    if typeName == 'warplane':
        return WarplaneActivity()
    else:
        return None


g_mapActivities = MapActivities()
# okay decompyling res/scripts/client/mapactivities.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:27:09 EST

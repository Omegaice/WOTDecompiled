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

    def create(self, settings, startTimes):
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
        self.__generateActivities(settings, {})
        return

    def generateArenaActivities(self, startTimes):
        arenaType = BigWorld.player().arena.arenaType
        self.__generateActivities(arenaType.mapActivitiesSection, startTimes)

    def __generateActivities(self, settings, startTimes):
        self.__pendingActivities = []
        if settings is None:
            return
        else:
            for activityType, activityXML in settings.items():
                activity = _createActivity(activityType)
                if activity is not None:
                    activity.create(activityXML, startTimes)
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

    def create(self, settings, startTimes):
        self.__settings = settings
        self.__curve = None
        self.__model = None
        self.__motor = None
        self.__sound = None
        self.__particles = None
        self.__particlesAdded = False
        self.__particlesNode = None
        self.__cbID = None
        preset = settings.readString('preset', '')
        self.__startTime = startTimes.get(preset, BigWorld.serverTime())
        self.__startTime += BigWorld.time() - BigWorld.serverTime()
        if BigWorld.time() >= self.__startTime or settings.readFloat('possibility', 1.0) < random.uniform(0, 1):
            self.__startTime += 1000000.0
        self.__curve = BigWorld.WGActionCurve(self.__settings)
        self.__modelName = self.__curve.getChannelProperty(0, 'modelName').asString
        BigWorld.loadResourceListBG((self.__modelName,), self.__onModelLoaded)
        return

    def isActive(self):
        return self.__model is not None

    def canStart(self):
        return BigWorld.time() >= self.__startTime and self.__model is not None

    def start(self):
        self.__model = BigWorld.Model(self.__curve.getChannelProperty(0, 'modelName').asString)
        BigWorld.addModel(self.__model)
        self.__model.wg_fashion = BigWorld.WGBaseFashion()
        self.__model.wg_fashion.initAlphaMaterials()
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

        self.__updateAlpha()
        return

    def stop(self):
        if self.__cbID is not None:
            BigWorld.cancelCallback(self.__cbID)
            self.__cbID = None
        if self.__model is not None:
            delattr(self.__model, 'wg_fashion')
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

    def __updateAlpha(self):
        alpha = self.__motor.warplaneAlpha
        self.__cbID = None
        self.__model.wg_fashion.setAlpha(alpha)
        if self.__sound is not None and self.__sound.isPlaying:
            self.__sound.volume = alpha
        if alpha == 1.0 and self.__particles is None and not self.__particlesAdded:
            self.__particlesAdded = True
            ds = self.__curve.getChannelProperty(0, 'effectName')
            effectName = ds.asString if ds is not None else ''
            if effectName != '':
                Pixie.createBG(effectName, self.__onParticlesLoaded)
        elif alpha == 0.0 and self.__particles is not None and self.__particlesAdded:
            self.stop()
            return
        self.__cbID = BigWorld.callback(0, self.__updateAlpha)
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
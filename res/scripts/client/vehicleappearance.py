import BigWorld
import ResMgr
import Math
import Pixie
import weakref
from AvatarInputHandler.control_modes import SniperControlMode
from VehicleEffects import VehicleTrailEffects, VehicleExhaustEffects
from constants import IS_DEVELOPMENT
from debug_utils import *
import helpers
import vehicle_extras
from helpers import bound_effects, DecalMap, isPlayerAvatar
from helpers.EffectsList import EffectsListPlayer
import items.vehicles
import random
import math
import time
from Event import Event
from functools import partial
import material_kinds
import VehicleStickers
import AuxiliaryFx
import TriggersManager
from TriggersManager import TRIGGER_TYPE
from Vibroeffects.ControllersManager import ControllersManager as VibrationControllersManager
from LightFx.LightControllersManager import LightControllersManager as LightFxControllersManager
import LightFx.LightManager
_ENABLE_VEHICLE_VALIDATION = False
_VEHICLE_DISAPPEAR_TIME = 0.2
_VEHICLE_APPEAR_TIME = 0.2
_ROOT_NODE_NAME = 'V'
_GUN_RECOIL_NODE_NAME = 'G'
_PERIODIC_TIME = 0.25
_LOD_DISTANCE_SOUNDS = 150
_LOD_DISTANCE_EXHAUST = 200
_LOD_DISTANCE_TRAIL_PARTICLES = 100
_MOVE_THROUGH_WATER_SOUND = '/vehicles/tanks/water'
_CAMOUFLAGE_MIN_INTENSITY = 1.0
_PITCH_SWINGING_MODIFIERS = (0.9,
 1.88,
 0.3,
 4.0,
 1.0,
 1.0)
_ROUGHNESS_DECREASE_SPEEDS = (5.0, 6.0)
_ROUGHNESS_DECREASE_FACTOR = 0.5
_ROUGHNESS_DECREASE_FACTOR2 = 0.1
_FRICTION_ANG_FACTOR = 0.8
_FRICTION_ANG_BOUND = 0.5
_FRICTION_STRAFE_FACTOR = 0.4
_FRICTION_STRAFE_BOUND = 1.0
_MIN_DEPTH_FOR_HEAVY_SPLASH = 0.5
_EFFECT_MATERIALS_HARDNESS = {'ground': 0.1,
 'stone': 1,
 'wood': 0.5,
 'snow': 0.3,
 'sand': 0,
 'water': 0.2}

class SoundMaxPlaybacksChecker():

    def __init__(self, maxPaybacks, period = 0.25):
        self.__maxPlaybacks = maxPaybacks
        self.__period = period
        self.__queue = []
        self.__distRecalcId = None
        return

    @staticmethod
    def __isSoundPlaying(sound):
        return sound.isPlaying

    def __distRecalc(self):
        if not isPlayerAvatar():
            self.__distRecalcId = None
            self.cleanup()
            return
        else:
            self.__distRecalcId = BigWorld.callback(self.__period, self.__distRecalc)
            cameraPos = BigWorld.camera().position
            for soundDistSq in self.__queue:
                if not self.__isSoundPlaying(soundDistSq[0]):
                    soundDistSq[0] = None
                    soundDistSq[1] = 0
                else:
                    soundDistSq[1] = (cameraPos - soundDistSq[0].position).lengthSquared

            self.__queue = filter(lambda x: x[0] is not None, self.__queue)
            self.__queue.sort(key=lambda soundDistSq: soundDistSq[1])
            return

    def cleanup(self):
        self.__queue = []
        if self.__distRecalcId is not None:
            BigWorld.cancelCallback(self.__distRecalcId)
            self.__distRecalcId = None
        return

    def checkAndPlay(self, newSound):
        if self.__distRecalcId is None:
            self.__distRecalc()
        cameraPos = BigWorld.camera().position
        newSoundDistSq = (cameraPos - newSound.position).lengthSquared
        for sound, distSq in self.__queue:
            if sound is newSound:
                return

        fullQueue = len(self.__queue) == self.__maxPlaybacks
        insertBeforeIdx = len(self.__queue)
        while insertBeforeIdx >= 1:
            sound, distSq = self.__queue[insertBeforeIdx - 1]
            if distSq < newSoundDistSq:
                break
            insertBeforeIdx -= 1

        if insertBeforeIdx < len(self.__queue) or not fullQueue:
            toInsert = [newSound, newSoundDistSq]
            self.__queue.insert(insertBeforeIdx, toInsert)
            if fullQueue:
                excessSound = self.__queue.pop()[0]
                if excessSound is not None:
                    excessSound.stop(True)
            if not self.__isSoundPlaying(newSound):
                newSound.play()
        return

    def removeSound(self, sound):
        if sound is None:
            return
        else:
            for idx, (snd, _) in enumerate(self.__queue):
                if snd == sound:
                    del self.__queue[idx]
                    return

            return


class VehicleAppearance(object):
    VehicleSoundsChecker = SoundMaxPlaybacksChecker(6)
    gunRecoil = property(lambda self: self.__gunRecoil)
    fashion = property(lambda self: self.__fashion)
    terrainMatKind = property(lambda self: self.__currTerrainMatKind)
    isInWater = property(lambda self: self.__isInWater)
    isUnderwater = property(lambda self: self.__isUnderWater)
    waterHeight = property(lambda self: self.__waterHeight)

    def __init__(self):
        self.modelsDesc = {'chassis': {'model': None,
                     'boundEffects': None,
                     '_visibility': (True, True),
                     '_fetchedModel': None,
                     '_stateFunc': lambda vehicle, state: vehicle.typeDescriptor.chassis['models'][state],
                     '_callbackFunc': '_VehicleAppearance__onChassisModelLoaded'},
         'hull': {'model': None,
                  'boundEffects': None,
                  '_visibility': (True, True),
                  '_node': None,
                  '_fetchedModel': None,
                  '_stateFunc': lambda vehicle, state: vehicle.typeDescriptor.hull['models'][state],
                  '_callbackFunc': '_VehicleAppearance__onHullModelLoaded'},
         'turret': {'model': None,
                    'boundEffects': None,
                    '_visibility': (True, True),
                    '_node': None,
                    '_fetchedModel': None,
                    '_stateFunc': lambda vehicle, state: vehicle.typeDescriptor.turret['models'][state],
                    '_callbackFunc': '_VehicleAppearance__onTurretModelLoaded'},
         'gun': {'model': None,
                 'boundEffects': None,
                 '_visibility': (True, True),
                 '_fetchedModel': None,
                 '_node': None,
                 '_stateFunc': lambda vehicle, state: vehicle.typeDescriptor.gun['models'][state],
                 '_callbackFunc': '_VehicleAppearance__onGunModelLoaded'}}
        self.turretMatrix = Math.WGAdaptiveMatrixProvider()
        self.gunMatrix = Math.WGAdaptiveMatrixProvider()
        self.__vehicle = None
        self.__skeletonCollider = None
        self.__engineSound = None
        self.__movementSound = None
        self.__waterHeight = -1.0
        self.__isInWater = False
        self.__isUnderWater = False
        self.__splashedWater = False
        self.__vibrationsCtrl = None
        self.__lightFxCtrl = None
        self.__auxiliaryFxCtrl = None
        self.__fashion = None
        self.__crashedTracksCtrl = None
        self.__gunRecoil = None
        self.__firstInit = True
        self.__curDamageState = None
        self.__loadingProgress = len(self.modelsDesc)
        self.__actualDamageState = None
        self.__invalidateLoading = False
        self.__showStickers = True
        self.__effectsPlayer = None
        self.__engineMode = (0, 0)
        self.__swingMoveFlags = 0
        self.__engineSndVariation = [0, 0]
        self.__trackSounds = [None, None]
        self.__currTerrainMatKind = [-1, -1, -1]
        self.__periodicTimerID = None
        self.__trailEffects = None
        self.__exhaustEffects = None
        self.__stickers = {}
        self.onModelChanged = Event()
        return

    def prerequisites(self, vehicle):
        self.__curDamageState = self.__getDamageModelsState(vehicle.health)
        out = []
        for desc in self.modelsDesc.itervalues():
            out.append(desc['_stateFunc'](vehicle, self.__curDamageState))

        vDesc = vehicle.typeDescriptor
        out.append(vDesc.type.camouflageExclusionMask)
        customization = items.vehicles.g_cache.customization(vDesc.type.id[0])
        camouflageParams = self.__getCamouflageParams(vehicle)
        if camouflageParams is not None and customization is not None:
            camouflageId = camouflageParams[0]
            camouflageDesc = customization['camouflages'].get(camouflageId)
            if camouflageDesc is not None and camouflageDesc['texture'] != '':
                out.append(camouflageDesc['texture'])
                for tgDesc in (vDesc.turret, vDesc.gun):
                    exclMask = tgDesc.get('camouflageExclusionMask')
                    if exclMask is not None and exclMask != '':
                        out.append(exclMask)

        return out

    def destroy(self):
        vehicle = self.__vehicle
        self.__vehicle = None
        if IS_DEVELOPMENT and _ENABLE_VEHICLE_VALIDATION and self.__validateCallbackId is not None:
            BigWorld.cancelCallback(self.__validateCallbackId)
            self.__validateCallbackId = None
        self.__skeletonCollider.destroy()
        if self.__engineSound is not None:
            VehicleAppearance.VehicleSoundsChecker.removeSound(self.__engineSound)
            self.__engineSound.stop()
            self.__engineSound = None
        if self.__movementSound is not None:
            VehicleAppearance.VehicleSoundsChecker.removeSound(self.__movementSound)
            self.__movementSound.stop()
            self.__movementSound = None
        if self.__vibrationsCtrl is not None:
            self.__vibrationsCtrl.destroy()
            self.__vibrationsCtrl = None
        if self.__lightFxCtrl is not None:
            self.__lightFxCtrl.destroy()
            self.__lightFxCtrl = None
        if self.__auxiliaryFxCtrl is not None:
            self.__auxiliaryFxCtrl.destroy()
            self.__auxiliaryFxCtrl = None
        self.__stopEffects()
        self.__destroyTrackDamageSounds()
        if self.__trailEffects is not None:
            self.__trailEffects.destroy()
            self.__trailEffects = None
        if self.__exhaustEffects is not None:
            self.__exhaustEffects.destroy()
            self.__exhaustEffects = None
        vehicle.stopHornSound(True)
        for desc in self.modelsDesc.iteritems():
            boundEffects = desc[1].get('boundEffects', None)
            if boundEffects is not None:
                boundEffects.destroy()

        if vehicle.isPlayer:
            player = BigWorld.player()
            if player.inputHandler is not None:
                arcadeCamera = player.inputHandler.ctrls['arcade'].camera
                if arcadeCamera is not None:
                    hull = self.modelsDesc['hull']['model']
                    turret = self.modelsDesc['turret']['model']
                    arcadeCamera.removeModelsToCollideWith((hull, turret))
        vehicle.model.delMotor(vehicle.model.motors[0])
        vehicle.filter.vehicleCollisionCallback = None
        self.__stickers = None
        self.modelsDesc = None
        self.onModelChanged = None
        id = getattr(self, '_VehicleAppearance__stippleCallbackID', None)
        if id is not None:
            BigWorld.cancelCallback(id)
            self.__stippleCallbackID = None
        if self.__periodicTimerID is not None:
            BigWorld.cancelCallback(self.__periodicTimerID)
            self.__periodicTimerID = None
        self.__crashedTracksCtrl.destroy()
        self.__crashedTracksCtrl = None
        return

    def start(self, vehicle, prereqs = None):
        self.__vehicle = vehicle
        descr = vehicle.typeDescriptor
        player = BigWorld.player()
        if prereqs is None:
            descr.chassis['hitTester'].loadBspModel()
            descr.hull['hitTester'].loadBspModel()
            descr.turret['hitTester'].loadBspModel()
        filter = BigWorld.WGVehicleFilter()
        vehicle.filter = filter
        filter.vehicleWidth = descr.chassis['topRightCarryingPoint'][0] * 2
        filter.vehicleCollisionCallback = player.handleVehicleCollidedVehicle
        filter.vehicleMaxMove = descr.physics['speedLimits'][0] * 2.0
        filter.vehicleMinNormalY = descr.physics['minPlaneNormalY']
        filter.isStrafing = vehicle.isStrafing
        for p1, p2, p3 in descr.physics['carryingTriangles']:
            filter.addTriangle((p1[0], 0, p1[1]), (p2[0], 0, p2[1]), (p3[0], 0, p3[1]))

        self.turretMatrix.target = filter.turretMatrix
        self.gunMatrix.target = filter.gunMatrix
        self.__createGunRecoil()
        self.__createStickers(prereqs)
        self.__createExhaust()
        self.__skeletonCollider = _SkeletonCollider(vehicle, self)
        self.__crashedTracksCtrl = _CrashedTrackController(vehicle, self)
        self.__fashion = BigWorld.WGVehicleFashion()
        _setupVehicleFashion(self.__fashion, self.__vehicle)
        for desc in self.modelsDesc.itervalues():
            modelName = desc['_stateFunc'](vehicle, self.__curDamageState)
            if prereqs is not None:
                try:
                    desc['model'] = prereqs[modelName]
                except Exception:
                    LOG_ERROR("can't load model <%s> from prerequisites." % modelName)

                if desc['model'] is None:
                    desc['model'] = BigWorld.Model(desc['_stateFunc'](vehicle, 'undamaged'))
            else:
                desc['model'] = BigWorld.Model(modelName)
            desc['model'].outsideOnly = 1
            if desc.has_key('boundEffects'):
                desc['boundEffects'] = bound_effects.ModelBoundEffects(desc['model'])

        self.__setupModels()
        state = self.__curDamageState
        if state == 'destroyed':
            self.__playEffect('destruction', 'static')
        elif state == 'exploded':
            self.__playEffect('explosion', 'static')
        self.__firstInit = False
        if self.__invalidateLoading:
            self.__invalidateLoading = True
            self.__fetchModels(self.__actualDamageState)
        if vehicle.isAlive():
            turretModel = self.modelsDesc['turret']['model']
            self.__engineSound = _getSound(turretModel, descr.engine['sound'])
            self.__movementSound = _getSound(turretModel, descr.chassis['sound'])
            self.__isEngineSoundMutedByLOD = False
        if vehicle.isAlive() and self.__vehicle.isPlayer:
            self.__vibrationsCtrl = VibrationControllersManager()
            if LightFx.LightManager.g_instance is not None and LightFx.LightManager.g_instance.isEnabled():
                self.__lightFxCtrl = LightFxControllersManager(self.__vehicle)
            if AuxiliaryFx.g_instance is not None:
                self.__auxiliaryFxCtrl = AuxiliaryFx.g_instance.createFxController(self.__vehicle)
        vehicle.model.stipple = True
        self.__stippleCallbackID = BigWorld.callback(_VEHICLE_APPEAR_TIME, self.__disableStipple)
        self.__setupTrailParticles()
        self.__setupTrackDamageSounds()
        self.__periodicTimerID = BigWorld.callback(_PERIODIC_TIME * random.uniform(0.01, 1.0), self.__onPeriodicTimer)
        return

    def showStickers(self, bool):
        self.__showStickers = bool
        for compName, stickerDesc in self.__stickers.iteritems():
            alpha = stickerDesc['alpha'] if bool else 0.0
            stickerDesc['stickers'].setAlphas(alpha, alpha)

    def changeVisibility(self, modelName, modelVisible, attachmentsVisible):
        desc = self.modelsDesc.get(modelName, None)
        if desc is None:
            LOG_ERROR("invalid model's description name <%s>." % modelName)
        desc['model'].visible = modelVisible
        desc['model'].visibleAttachments = attachmentsVisible
        desc['_visibility'] = (modelVisible, attachmentsVisible)
        if modelName == 'chassis':
            self.__crashedTracksCtrl.setVisible(modelVisible)
        return

    def onVehicleHealthChanged(self):
        vehicle = self.__vehicle
        if not vehicle.isAlive():
            BigWorld.wgDelEdgeDetectEntity(vehicle)
            if vehicle.health > 0:
                self.changeEngineMode((0, 0))
            elif self.__engineSound is not None:
                VehicleAppearance.VehicleSoundsChecker.removeSound(self.__engineSound)
                self.__engineSound.stop()
                self.__engineSound = None
            if self.__movementSound is not None:
                VehicleAppearance.VehicleSoundsChecker.removeSound(self.__movementSound)
                self.__movementSound.stop()
                self.__movementSound = None
        state = self.__getDamageModelsState(vehicle.health)
        if state != self.__curDamageState:
            if self.__loadingProgress == len(self.modelsDesc) and not self.__firstInit:
                if state == 'undamaged':
                    self.__stopEffects()
                elif state == 'destroyed':
                    self.__playEffect('destruction')
                elif state == 'exploded':
                    self.__playEffect('explosion')
                if vehicle.health <= 0:
                    BigWorld.player().inputHandler.onVehicleDeath(vehicle, state == 'exploded')
                self.__fetchModels(state)
            else:
                self.__actualDamageState = state
                self.__invalidateLoading = True
        return

    def changeEngineMode(self, mode, forceSwinging = False):
        self.__engineMode = mode
        powerMode = mode[0]
        dirFlags = mode[1]
        self.__changeExhaust(powerMode)
        self.__updateBlockedMovement()
        sound = self.__engineSound
        if sound is not None:
            param = sound.param('load')
            if param is not None:
                param.value = powerMode + (0.0 if param.value != powerMode else 0.001)
                self.__engineSndVariation = [BigWorld.time() + 1.0, False]
        if forceSwinging:
            flags = mode[1]
            prevFlags = self.__swingMoveFlags
            fashion = self.fashion
            moveMask = 3
            rotMask = 12
            if flags & moveMask ^ prevFlags & moveMask:
                swingPeriod = 2.0
                if flags & 1:
                    fashion.accelSwingingDirection = -1
                elif flags & 2:
                    fashion.accelSwingingDirection = 1
                else:
                    fashion.accelSwingingDirection = 0
            elif not flags & moveMask and flags & rotMask ^ prevFlags & rotMask:
                swingPeriod = 1.0
                fashion.accelSwingingDirection = 0
            else:
                swingPeriod = 0.0
            if swingPeriod > fashion.accelSwingingPeriod:
                fashion.accelSwingingPeriod = swingPeriod
            self.__swingMoveFlags = flags
        return

    def stopSwinging(self):
        self.fashion.accelSwingingPeriod = 0.0

    def removeDamageSticker(self, code):
        for stickerDesc in self.__stickers.itervalues():
            dmgSticker = stickerDesc['damageStickers'].get(code)
            if dmgSticker is not None:
                if dmgSticker['handle'] is not None:
                    stickerDesc['stickers'].delDamageSticker(dmgSticker['handle'])
                del stickerDesc['damageStickers'][code]

        return

    def addDamageSticker(self, code, componentName, stickerID, segStart, segEnd):
        stickerDesc = self.__stickers[componentName]
        if stickerDesc['damageStickers'].has_key(code):
            return
        desc = items.vehicles.g_cache.damageStickers['descrs'][stickerID]
        texParams = random.choice(desc['variants'])
        texName = texParams['texName']
        bumpTexName = texParams['bumpTexName']
        sizes = texParams['modelSizes']
        segment = segEnd - segStart
        segLen = segment.lengthSquared
        if segLen != 0:
            segStart -= 0.25 * segment / math.sqrt(segLen)
        angle = random.random() * math.pi * 2.0
        rotAxis = 0
        for i in xrange(1, 3):
            if abs(segment[i]) > abs(segment[rotAxis]):
                rotAxis = i

        up = Math.Vector3()
        up[(rotAxis + 1) % 3] = math.sin(angle)
        up[(rotAxis + 2) % 3] = math.cos(angle)
        stickerDesc = self.__stickers[componentName]
        model = self.modelsDesc[componentName]['model']
        handle = stickerDesc['stickers'].addDamageSticker(texName, bumpTexName, segStart, segEnd, sizes, up)
        stickerDesc['damageStickers'][code] = {'rayStart': segStart,
         'rayEnd': segEnd,
         'up': up,
         'sizes': sizes,
         'handle': handle}

    def receiveShotImpulse(self, dir, impulse):
        if self.__curDamageState == 'undamaged':
            self.__fashion.receiveShotImpulse(dir, impulse)
            self.__crashedTracksCtrl.receiveShotImpulse(dir, impulse)

    def addCrashedTrack(self, isLeft):
        self.__crashedTracksCtrl.addTrack(isLeft)
        if not self.__vehicle.isEnteringWorld:
            sound = self.__trackSounds[0 if isLeft else 1]
            if sound is not None and sound[1] is not None:
                sound[1].play()
        return

    def delCrashedTrack(self, isLeft):
        self.__crashedTracksCtrl.delTrack(isLeft)

    def __fetchModels(self, modelState):
        self.__curDamageState = modelState
        self.__loadingProgress = 0
        for desc in self.modelsDesc.itervalues():
            BigWorld.fetchModel(desc['_stateFunc'](self.__vehicle, modelState), getattr(self, desc['_callbackFunc']))

    def __attemptToSetupModels(self):
        self.__loadingProgress += 1
        if self.__loadingProgress == len(self.modelsDesc):
            if self.__invalidateLoading:
                self.__invalidateLoading = False
                self.__fetchModels(self.__actualDamageState)
            else:
                self.__setupModels()

    def __setupModels(self):
        vehicle = self.__vehicle
        chassis = self.modelsDesc['chassis']
        hull = self.modelsDesc['hull']
        turret = self.modelsDesc['turret']
        gun = self.modelsDesc['gun']
        if not self.__firstInit:
            self.__detachStickers()
            delattr(gun['model'], 'wg_gunRecoil')
            self.__gunFireNode = None
            self.__attachExhaust(False)
            self.__trailEffects.stopEffects()
            self.__destroyTrackDamageSounds()
            self.__skeletonCollider.detach()
            self.__crashedTracksCtrl.reset()
            chassis['model'].stopSoundsOnDestroy = False
            hull['model'].stopSoundsOnDestroy = False
            turret['model'].stopSoundsOnDestroy = False
            hull['_node'].detach(hull['model'])
            turret['_node'].detach(turret['model'])
            gun['_node'].detach(gun['model'])
            chassis['model'] = chassis['_fetchedModel']
            hull['model'] = hull['_fetchedModel']
            turret['model'] = turret['_fetchedModel']
            gun['model'] = gun['_fetchedModel']
            delattr(vehicle.model, 'wg_fashion')
            self.__reattachEffects()
        vehicle.model = None
        vehicle.model = chassis['model']
        vehicle.model.delMotor(vehicle.model.motors[0])
        matrix = vehicle.matrix
        matrix.notModel = True
        vehicle.model.addMotor(BigWorld.Servo(matrix))
        self.__assembleModels()
        self.__skeletonCollider.attach()
        if not self.__firstInit:
            chassis['boundEffects'].reattachTo(chassis['model'])
            hull['boundEffects'].reattachTo(hull['model'])
            turret['boundEffects'].reattachTo(turret['model'])
            gun['boundEffects'].reattachTo(gun['model'])
        modelsState = self.__curDamageState
        if modelsState == 'undamaged':
            self.__attachStickers()
            try:
                vehicle.model.wg_fashion = self.__fashion
            except:
                LOG_CURRENT_EXCEPTION()

            self.__attachExhaust(True)
            gun['model'].wg_gunRecoil = self.__gunRecoil
            self.__gunFireNode = gun['model'].node('HP_gunFire')
        elif modelsState == 'destroyed' or modelsState == 'exploded':
            self.__destroyExhaust()
            self.__attachStickers(items.vehicles.g_cache.commonConfig['miscParams']['damageStickerAlpha'], True)
        else:
            raise False or AssertionError
        self.__updateCamouflage()
        self.__applyVisibility()
        self.onModelChanged()
        if 'observer' in vehicle.typeDescriptor.type.tags:
            vehicle.model.visible = False
            vehicle.model.visibleAttachments = False
        return

    def __reattachEffects(self):
        if self.__effectsPlayer is not None:
            self.__effectsPlayer.reattachTo(self.modelsDesc['hull']['model'])
        return

    def __playEffect(self, kind, *modifs):
        if self.__effectsPlayer is not None:
            self.__effectsPlayer.stop()
        enableDecal = True
        if kind in ('explosion', 'destruction'):
            return self.isUnderwater and None
        else:
            filter = self.__vehicle.filter
            if filter.numLeftTrackContacts < 2:
                isFlying = filter.numRightTrackContacts < 2
                if isFlying:
                    enableDecal = False
            vehicle = self.__vehicle
            effects = vehicle.typeDescriptor.type.effects[kind]
            if not effects:
                return
            effects = random.choice(effects)
            self.__effectsPlayer = EffectsListPlayer(effects[1], effects[0], showShockWave=vehicle.isPlayer, showFlashBang=vehicle.isPlayer, isPlayer=vehicle.isPlayer, showDecal=enableDecal, start=vehicle.position + Math.Vector3(0.0, -1.0, 0.0), end=vehicle.position + Math.Vector3(0.0, 1.0, 0.0))
            self.__effectsPlayer.play(self.modelsDesc['hull']['model'], *modifs)
            return

    def __updateCamouflage(self):
        texture = ''
        colors = [0,
         0,
         0,
         0]
        weights = Math.Vector4(1, 0, 0, 0)
        camouflagePresent = False
        vDesc = self.__vehicle.typeDescriptor
        camouflageParams = self.__getCamouflageParams(self.__vehicle)
        customization = items.vehicles.g_cache.customization(vDesc.type.id[0])
        defaultTiling = None
        if camouflageParams is not None and customization is not None:
            camouflage = customization['camouflages'].get(camouflageParams[0])
            if camouflage is not None:
                camouflagePresent = True
                texture = camouflage['texture']
                colors = camouflage['colors']
                weights = Math.Vector4((colors[0] >> 24) / 255.0, (colors[1] >> 24) / 255.0, (colors[2] >> 24) / 255.0, (colors[3] >> 24) / 255.0)
                defaultTiling = camouflage['tiling'].get(vDesc.type.compactDescr)
        if self.__curDamageState != 'undamaged':
            weights *= 0.1
        if camouflageParams is not None:
            _, camStartTime, camNumDays = camouflageParams
            if camNumDays > 0:
                timeAmount = (time.time() - camStartTime) / (camNumDays * 86400)
                if timeAmount > 1.0:
                    weights *= _CAMOUFLAGE_MIN_INTENSITY
                elif timeAmount > 0:
                    weights *= (1.0 - timeAmount) * (1.0 - _CAMOUFLAGE_MIN_INTENSITY) + _CAMOUFLAGE_MIN_INTENSITY
        for descId in ('chassis', 'hull', 'turret', 'gun'):
            exclusionMap = vDesc.type.camouflageExclusionMask
            tiling = defaultTiling
            if tiling is None:
                tiling = vDesc.type.camouflageTiling
            model = self.modelsDesc[descId]['model']
            tgDesc = None
            if descId == 'turret':
                tgDesc = vDesc.turret
            elif descId == 'gun':
                tgDesc = vDesc.gun
            if tgDesc is not None:
                coeff = tgDesc.get('camouflageTiling')
                if coeff is not None:
                    if tiling is not None:
                        tiling = (tiling[0] * coeff[0],
                         tiling[1] * coeff[1],
                         tiling[2] * coeff[2],
                         tiling[3] * coeff[3])
                    else:
                        tiling = coeff
                if tgDesc.has_key('camouflageExclusionMask'):
                    exclusionMap = tgDesc['camouflageExclusionMask']
            if camouflagePresent and exclusionMap != '':
                useCamouflage = texture != ''
                fashion = None
                if hasattr(model, 'wg_fashion'):
                    fashion = model.wg_fashion
                elif hasattr(model, 'wg_gunRecoil'):
                    fashion = model.wg_gunRecoil
                elif useCamouflage:
                    fashion = model.wg_baseFashion = BigWorld.WGBaseFashion()
                elif hasattr(model, 'wg_baseFashion'):
                    delattr(model, 'wg_baseFashion')
                if fashion is not None:
                    useCamouflage and fashion.setCamouflage(texture, exclusionMap, tiling, colors[0], colors[1], colors[2], colors[3], weights)
                else:
                    fashion.removeCamouflage()

        return

    def __getCamouflageParams(self, vehicle):
        vDesc = vehicle.typeDescriptor
        vehicleInfo = BigWorld.player().arena.vehicles.get(vehicle.id)
        if vehicleInfo is not None:
            camouflagePseudoname = vehicleInfo['events'].get('hunting', None)
            if camouflagePseudoname is not None:
                camouflIdsByNation = {0: {'black': 29,
                     'gold': 30,
                     'red': 31,
                     'silver': 32},
                 1: {'black': 25,
                     'gold': 26,
                     'red': 27,
                     'silver': 28},
                 2: {'black': 52,
                     'gold': 50,
                     'red': 51,
                     'silver': 53},
                 3: {'black': 48,
                     'gold': 46,
                     'red': 47,
                     'silver': 49},
                 4: {'black': 60,
                     'gold': 58,
                     'red': 59,
                     'silver': 61},
                 5: {'black': 56,
                     'gold': 54,
                     'red': 55,
                     'silver': 57}}
                camouflIds = camouflIdsByNation.get(vDesc.type.id[0])
                if camouflIds is not None:
                    ret = camouflIds.get(camouflagePseudoname)
                    if ret is not None:
                        return (ret, time.time(), 100.0)
        arenaType = BigWorld.player().arena.arenaType
        camouflageKind = arenaType.vehicleCamouflageKind
        return vDesc.camouflages[camouflageKind]

    def __stopEffects(self):
        if self.__effectsPlayer is not None:
            self.__effectsPlayer.stop()
        self.__effectsPlayer = None
        return

    def __calcIsUnderwater(self):
        if not self.__isInWater:
            return False
        chassisModel = self.modelsDesc['chassis']['model']
        turretOffs = self.__vehicle.typeDescriptor.chassis['hullPosition'] + self.__vehicle.typeDescriptor.hull['turretPositions'][0]
        turretOffsetMat = Math.Matrix()
        turretOffsetMat.setTranslate(turretOffs)
        turretJointMat = Math.Matrix(chassisModel.matrix)
        turretJointMat.preMultiply(turretOffsetMat)
        turretHeight = turretJointMat.translation.y - self.__vehicle.position.y
        return turretHeight < self.__waterHeight

    def __updateWaterStatus(self):
        self.__waterHeight = BigWorld.wg_collideWater(self.__vehicle.position, self.__vehicle.position + Math.Vector3(0, 1, 0))
        self.__isInWater = self.__waterHeight != -1
        self.__isUnderWater = self.__calcIsUnderwater()
        wasSplashed = self.__splashedWater
        self.__splashedWater = False
        waterHitPoint = None
        if self.__isInWater:
            self.__splashedWater = True
            waterHitPoint = self.__vehicle.position + Math.Vector3(0, self.__waterHeight, 0)
        else:
            trPoint = self.__vehicle.typeDescriptor.chassis['topRightCarryingPoint']
            cornerPoints = [Math.Vector3(trPoint.x, 0, trPoint.y),
             Math.Vector3(trPoint.x, 0, -trPoint.y),
             Math.Vector3(-trPoint.x, 0, -trPoint.y),
             Math.Vector3(-trPoint.x, 0, trPoint.y)]
            vehMat = Math.Matrix(self.__vehicle.model.matrix)
            for cornerPoint in cornerPoints:
                pointToTest = vehMat.applyPoint(cornerPoint)
                dist = BigWorld.wg_collideWater(pointToTest, pointToTest + Math.Vector3(0, 1, 0))
                if dist != -1:
                    self.__splashedWater = True
                    waterHitPoint = pointToTest + Math.Vector3(0, dist, 0)
                    break

        if self.__splashedWater and not wasSplashed:
            lightVelocityThreshold = self.__vehicle.typeDescriptor.type.collisionEffectVelocities['waterContact']
            heavyVelocityThreshold = self.__vehicle.typeDescriptor.type.heavyCollisionEffectVelocities['waterContact']
            vehicleVelocity = abs(self.__vehicle.filter.speedInfo.value[0])
            if vehicleVelocity >= lightVelocityThreshold:
                collRes = BigWorld.wg_collideSegment(self.__vehicle.spaceID, waterHitPoint, waterHitPoint + (0, -_MIN_DEPTH_FOR_HEAVY_SPLASH, 0), 18, lambda matKind, collFlags, itemId, chunkId: collFlags & 8)
                deepEnough = collRes is None
                effectName = 'waterCollisionLight' if vehicleVelocity < heavyVelocityThreshold or not deepEnough else 'waterCollisionHeavy'
                self.__vehicle.showCollisionEffect(waterHitPoint, effectName, Math.Vector3(0, 1, 0))
        if self.isUnderwater and self.__effectsPlayer is not None:
            self.__effectsPlayer.stop()
        return

    def __onPeriodicTimer(self):
        self.__periodicTimerID = None
        try:
            self.__updateVibrations()
        except Exception:
            LOG_CURRENT_EXCEPTION()

        try:
            if self.__lightFxCtrl is not None:
                self.__lightFxCtrl.update(self.__vehicle)
            if self.__auxiliaryFxCtrl is not None:
                self.__auxiliaryFxCtrl.update(self.__vehicle)
            self.__updateWaterStatus()
        except:
            LOG_CURRENT_EXCEPTION()

        if not self.__vehicle.isAlive():
            self.__periodicTimerID = BigWorld.callback(_PERIODIC_TIME, self.__onPeriodicTimer)
            return
        else:
            try:
                self.__distanceFromPlayer = (BigWorld.camera().position - self.__vehicle.position).length
                for extraData in self.__vehicle.extras.values():
                    extra = extraData.get('extra', None)
                    if isinstance(extra, vehicle_extras.Fire):
                        extra.checkUnderwater(extraData, self.__vehicle, self.isUnderwater)
                        break

                self.__updateCurrTerrainMatKinds()
                self.__updateMovementSounds()
                self.__updateBlockedMovement()
                self.__updateEffectsLOD()
                self.__trailEffects.update()
            except:
                LOG_CURRENT_EXCEPTION()

            self.__periodicTimerID = BigWorld.callback(_PERIODIC_TIME, self.__onPeriodicTimer)
            return

    def __updateMovementSounds(self):
        vehicle = self.__vehicle
        isTooFar = self.__distanceFromPlayer > _LOD_DISTANCE_SOUNDS
        if isTooFar != self.__isEngineSoundMutedByLOD:
            self.__isEngineSoundMutedByLOD = isTooFar
            if isTooFar:
                if self.__engineSound is not None:
                    self.__engineSound.stop()
                if self.__movementSound is not None:
                    self.__movementSound.stop()
            else:
                self.changeEngineMode(self.__engineMode)
        if not isTooFar:
            if self.__engineSound is not None:
                VehicleAppearance.VehicleSoundsChecker.checkAndPlay(self.__engineSound)
            if self.__movementSound is not None:
                VehicleAppearance.VehicleSoundsChecker.checkAndPlay(self.__movementSound)
        time = BigWorld.time()
        sound = self.__engineSound
        powerMode = self.__engineMode[0]
        if sound is not None:
            param = sound.param('load')
            if param is not None:
                if param.value == 0.0 and param.value != powerMode:
                    seekSpeed = param.seekSpeed
                    param.seekSpeed = 0
                    param.value = powerMode
                    param.seekSpeed = seekSpeed
                    self.__engineSndVariation = [time + 1.0, False]
                if time >= self.__engineSndVariation[0]:
                    if powerMode >= 3.0:
                        if self.__engineSndVariation[1]:
                            self.__engineSndVariation[1] = False
                            param.value = powerMode + (random.random() * 0.1 - 0.05)
                        elif random.random() < 0.35:
                            peak = random.random() * 0.35 + 0.1
                            self.__engineSndVariation[0] = time + peak * 0.9
                            self.__engineSndVariation[1] = True
                            param.value = powerMode + peak
                    elif powerMode >= 2.0:
                        self.__engineSndVariation[0] = time + random.choice((0.5, 0.25, 0.75, 0.25))
                        value = param.value + (random.random() * 0.17 - 0.085)
                        value = min(value, powerMode + 0.25)
                        value = max(value, powerMode - 0.1)
                        param.value = value
        self.__updateTrackSounds()
        return

    def __updateTrackSounds(self):
        sound = self.__movementSound
        if sound is None:
            return
        else:
            filter = self.__vehicle.filter
            isFlyingParam = sound.param('flying')
            if isFlyingParam is not None:
                contactsWithGround = filter.numLeftTrackContacts + filter.numRightTrackContacts
                isFlyingParam.value = 0.0 if contactsWithGround > 0 else 1.0
            speedFraction = filter.speedInfo.value[0]
            speedFraction = abs(speedFraction / self.__vehicle.typeDescriptor.physics['speedLimits'][0])
            param = sound.param('speed')
            if param is not None:
                param.value = min(1.0, speedFraction)
            if not self.__vehicle.isPlayer:
                toZeroParams = _EFFECT_MATERIALS_HARDNESS.keys()
                toZeroParams += ['hardness', 'friction', 'roughness']
                for paramName in toZeroParams:
                    param = sound.param(paramName)
                    if param is not None:
                        param.value = 0.0

                return
            matEffectsUnderTracks = dict(((effectMaterial, 0.0) for effectMaterial in _EFFECT_MATERIALS_HARDNESS))
            powerMode = self.__engineMode[0]
            if self.__isInWater and powerMode > 1.0 and speedFraction > 0.01:
                matEffectsUnderTracks['water'] = len(self.__currTerrainMatKind)
            else:
                for matKind in self.__currTerrainMatKind:
                    effectIndex = helpers.calcEffectMaterialIndex(matKind)
                    if effectIndex is not None:
                        effectMaterial = material_kinds.EFFECT_MATERIALS[effectIndex]
                        if effectMaterial in matEffectsUnderTracks:
                            matEffectsUnderTracks[effectMaterial] = matEffectsUnderTracks.get(effectMaterial, 0) + 1.0

            hardness = 0.0
            for effectMaterial, amount in matEffectsUnderTracks.iteritems():
                param = sound.param(effectMaterial)
                if param is not None:
                    param.value = amount / len(self.__currTerrainMatKind)
                hardness += _EFFECT_MATERIALS_HARDNESS.get(effectMaterial, 0) * amount

            hardnessParam = sound.param('hardness')
            if hardnessParam is not None:
                hardnessParam.value = hardness / len(self.__currTerrainMatKind)
            strafeParam = sound.param('friction')
            if strafeParam is not None:
                angPart = min(abs(filter.angularSpeed) * _FRICTION_ANG_FACTOR, _FRICTION_ANG_BOUND)
                strafePart = min(abs(filter.strafeSpeed) * _FRICTION_STRAFE_FACTOR, _FRICTION_STRAFE_BOUND)
                frictionValue = max(angPart, strafePart)
                strafeParam.value = frictionValue
            roughnessParam = sound.param('roughness')
            if roughnessParam is not None:
                speed = filter.speedInfo.value[2]
                rds = _ROUGHNESS_DECREASE_SPEEDS
                decFactor = (speed - rds[0]) / (rds[1] - rds[0])
                decFactor = 0.0 if decFactor <= 0.0 else (decFactor if decFactor <= 1.0 else 1.0)
                subs = _ROUGHNESS_DECREASE_FACTOR2 * decFactor
                decFactor = 1.0 - (1.0 - _ROUGHNESS_DECREASE_FACTOR) * decFactor
                surfaceCurvature = filter.suspCompressionRate
                roughness = max(0.0, min((surfaceCurvature * 2 * speedFraction - subs) * decFactor, 1.0))
                roughnessParam.value = roughness
            return

    def __updateBlockedMovement(self):
        blockingForce = 0.0
        powerMode, dirFlags = self.__engineMode
        vehSpeed = self.__vehicle.filter.speedInfo.value[0]
        if abs(vehSpeed) < 0.25 and powerMode > 1:
            if dirFlags & 1:
                blockingForce = -0.5
            elif dirFlags & 2:
                blockingForce = 0.5

    def __updateEffectsLOD(self):
        enableExhaust = self.__distanceFromPlayer <= _LOD_DISTANCE_EXHAUST
        if enableExhaust != self.__exhaustEffects.enabled:
            self.__exhaustEffects.enable(enableExhaust)
            self.__changeExhaust(self.__engineMode[0])
        enableTrails = self.__distanceFromPlayer <= _LOD_DISTANCE_TRAIL_PARTICLES and BigWorld.wg_isVehicleDustEnabled()
        self.__trailEffects.enable(enableTrails)

    def __setupTrailParticles(self):
        self.__trailEffects = VehicleTrailEffects(self.__vehicle)

    def __setupTrackDamageSounds(self):
        for i in xrange(2):
            try:
                fakeModel = BigWorld.player().newFakeModel()
                self.__trailEffects.getTrackCenterNode(i).attach(fakeModel)
                self.__trackSounds[i] = (fakeModel, fakeModel.getSound('/tanks/tank_breakdown/hit_treads'))
            except:
                self.__trackSounds[i] = None
                LOG_CURRENT_EXCEPTION()

        return

    def __destroyTrackDamageSounds(self):
        for i in xrange(2):
            if self.__trackSounds[i] is not None:
                self.__trailEffects.getTrackCenterNode(i).detach(self.__trackSounds[i][0])

        self.__trackSounds = [None, None]
        return

    def __updateCurrTerrainMatKinds(self):
        wasOnSoftTerrain = self.__isOnSoftTerrain()
        testPoints = []
        for iTrack in xrange(2):
            centerNode = self.__trailEffects.getTrackCenterNode(iTrack)
            mMidNode = Math.Matrix(centerNode)
            testPoints.append(mMidNode.translation)

        testPoints.append(self.__vehicle.position)
        for idx, testPoint in enumerate(testPoints):
            res = BigWorld.wg_collideSegment(self.__vehicle.spaceID, testPoint + (0, 2, 0), testPoint + (0, -2, 0), 18)
            self.__currTerrainMatKind[idx] = res[2] if res is not None else 0

        isOnSoftTerrain = self.__isOnSoftTerrain()
        if self.__vehicle.isPlayer and wasOnSoftTerrain != isOnSoftTerrain:
            if isOnSoftTerrain:
                TriggersManager.g_manager.activateTrigger(TRIGGER_TYPE.PLAYER_VEHICLE_ON_SOFT_TERRAIN)
            else:
                TriggersManager.g_manager.deactivateTrigger(TRIGGER_TYPE.PLAYER_VEHICLE_ON_SOFT_TERRAIN)
        self.__fashion.setCurrTerrainMatKinds(self.__currTerrainMatKind[0], self.__currTerrainMatKind[1])
        return

    def __isOnSoftTerrain(self):
        for matKind in self.__currTerrainMatKind:
            groundStr = material_kinds.GROUND_STRENGTHS_BY_IDS.get(matKind)
            if groundStr == 'soft':
                return True

        return False

    def switchFireVibrations(self, bStart):
        if self.__vibrationsCtrl is not None:
            self.__vibrationsCtrl.switchFireVibrations(bStart)
        return

    def executeHitVibrations(self, hitEffectCode):
        if self.__vibrationsCtrl is not None:
            self.__vibrationsCtrl.executeHitVibrations(hitEffectCode)
        return

    def executeRammingVibrations(self, matKind = None):
        if self.__vibrationsCtrl is not None:
            self.__vibrationsCtrl.executeRammingVibrations(self.__vehicle.getSpeed(), matKind)
        return

    def executeShootingVibrations(self, caliber):
        if self.__vibrationsCtrl is not None:
            self.__vibrationsCtrl.executeShootingVibrations(caliber)
        return

    def executeCriticalHitVibrations(self, vehicle, extrasName):
        if self.__vibrationsCtrl is not None:
            self.__vibrationsCtrl.executeCriticalHitVibrations(vehicle, extrasName)
        return

    def __updateVibrations(self):
        if self.__vibrationsCtrl is None:
            return
        else:
            vehicle = self.__vehicle
            crashedTrackCtrl = self.__crashedTracksCtrl
            self.__vibrationsCtrl.update(vehicle, crashedTrackCtrl.isLeftTrackBroken(), crashedTrackCtrl.isRightTrackBroken())
            return

    def __getDamageModelsState(self, vehicleHealth):
        if vehicleHealth > 0:
            return 'undamaged'
        elif vehicleHealth == 0:
            return 'destroyed'
        else:
            return 'exploded'

    def __onChassisModelLoaded(self, model):
        self.__onModelLoaded('chassis', model)

    def __onHullModelLoaded(self, model):
        self.__onModelLoaded('hull', model)

    def __onTurretModelLoaded(self, model):
        self.__onModelLoaded('turret', model)

    def __onGunModelLoaded(self, model):
        self.__onModelLoaded('gun', model)

    def __onModelLoaded(self, name, model):
        if self.modelsDesc is None:
            return
        else:
            desc = self.modelsDesc[name]
            if model is not None:
                desc['_fetchedModel'] = model
            else:
                desc['_fetchedModel'] = desc['model']
                modelState = desc['_stateFunc'](self.__vehicle, self.__curDamageState)
                LOG_ERROR('Model %s not loaded.' % modelState)
            self.__attemptToSetupModels()
            return

    def __assembleModels(self):
        vehicle = self.__vehicle
        hull = self.modelsDesc['hull']
        turret = self.modelsDesc['turret']
        gun = self.modelsDesc['gun']
        try:
            hull['_node'] = vehicle.model.node(_ROOT_NODE_NAME)
            hull['_node'].attach(hull['model'])
            turret['_node'] = hull['model'].node('HP_turretJoint', self.turretMatrix)
            turret['_node'].attach(turret['model'])
            gun['_node'] = turret['model'].node('HP_gunJoint', self.gunMatrix)
            gun['_node'].attach(gun['model'])
            if vehicle.isPlayer:
                player = BigWorld.player()
                if player.inputHandler is not None:
                    arcadeCamera = player.inputHandler.ctrls['arcade'].camera
                    if arcadeCamera is not None:
                        arcadeCamera.addModelsToCollideWith([hull['model'], turret['model']])
        except Exception:
            LOG_ERROR('Can not assemble models for %s.' % vehicle.typeDescriptor.name)
            raise

        if IS_DEVELOPMENT and _ENABLE_VEHICLE_VALIDATION:
            self.__validateCallbackId = BigWorld.callback(0.01, self.__validateAssembledModel)
        return

    def __applyVisibility(self):
        vehicle = self.__vehicle
        chassis = self.modelsDesc['chassis']
        hull = self.modelsDesc['hull']
        turret = self.modelsDesc['turret']
        gun = self.modelsDesc['gun']
        chassis['model'].visible = chassis['_visibility'][0]
        chassis['model'].visibleAttachments = chassis['_visibility'][1]
        hull['model'].visible = hull['_visibility'][0]
        hull['model'].visibleAttachments = hull['_visibility'][1]
        turret['model'].visible = turret['_visibility'][0]
        turret['model'].visibleAttachments = turret['_visibility'][1]
        gun['model'].visible = gun['_visibility'][0]
        gun['model'].visibleAttachments = gun['_visibility'][1]

    def __validateAssembledModel(self):
        self.__validateCallbackId = None
        vehicle = self.__vehicle
        vDesc = vehicle.typeDescriptor
        state = self.__curDamageState
        chassis = self.modelsDesc['chassis']
        hull = self.modelsDesc['hull']
        turret = self.modelsDesc['turret']
        gun = self.modelsDesc['gun']
        _validateCfgPos(chassis, hull, vDesc.chassis['hullPosition'], 'hullPosition', vehicle, state)
        _validateCfgPos(hull, turret, vDesc.hull['turretPositions'][0], 'turretPosition', vehicle, state)
        _validateCfgPos(turret, gun, vDesc.turret['gunPosition'], 'gunPosition', vehicle, state)
        return

    def __createExhaust(self):
        self.__exhaustEffects = VehicleExhaustEffects(self.__vehicle.typeDescriptor)

    def __attachExhaust(self, attach):
        hullModel = self.modelsDesc['hull']['model']
        nodes = self.__vehicle.typeDescriptor.hull['exhaust']['nodes']
        self.__exhaustEffects.attach(hullModel, nodes, attach)

    def __destroyExhaust(self):
        self.__exhaustEffects.destroy()

    def __changeExhaust(self, engineMode):
        self.__exhaustEffects.changeExhaust(self.__vehicle.typeDescriptor, engineMode)

    def __createGunRecoil(self):
        recoilDescr = self.__vehicle.typeDescriptor.gun['recoil']
        recoil = BigWorld.WGGunRecoil(_GUN_RECOIL_NODE_NAME)
        recoil.setLod(recoilDescr['lodDist'])
        recoil.setDuration(recoilDescr['backoffTime'], recoilDescr['returnTime'])
        recoil.setDepth(recoilDescr['amplitude'])
        self.__gunRecoil = recoil

    def __createStickers(self, prereqs):
        vDesc = self.__vehicle.typeDescriptor
        g_cache = items.vehicles.g_cache
        emblemPositions = (('hull', vDesc.hull['emblemSlots']), ('gun' if vDesc.turret['showEmblemsOnGun'] else 'turret', vDesc.turret['emblemSlots']), ('turret' if vDesc.turret['showEmblemsOnGun'] else 'gun', []))
        clanID = BigWorld.player().arena.vehicles[self.__vehicle.id]['clanDBID']
        for componentName, slots in emblemPositions:
            stickers = VehicleStickers.VehicleStickers(vDesc, slots, componentName == 'hull', prereqs)
            stickers.setClanID(clanID)
            self.__stickers[componentName] = {'stickers': stickers,
             'damageStickers': {},
             'alpha': 1.0}

    def __attachStickers(self, alpha = 1.0, emblemsOnly = False):
        actualAlpha = alpha * self.__vehicle.typeDescriptor.type.emblemsAlpha
        actualAlpha = alpha if self.__showStickers else 0.0
        isDamaged = self.__curDamageState != 'undamaged'
        for componentName, stickerDesc in self.__stickers.iteritems():
            stickers = stickerDesc['stickers']
            stickers.setAlphas(actualAlpha, actualAlpha)
            stickerDesc['alpha'] = actualAlpha
            model = self.modelsDesc[componentName]['model']
            node = self.modelsDesc[componentName]['_node']
            stickers.attachStickers(model, node, isDamaged)
            if emblemsOnly:
                continue
            for dmgSticker in stickerDesc['damageStickers'].itervalues():
                if dmgSticker['handle'] is not None:
                    stickers.delDamageSticker(dmgSticker['handle'])
                    dmgSticker['handle'] = None
                    LOG_WARNING('Adding %s damage sticker to occupied slot' % componentName)
                dmgSticker['handle'] = stickers.addDamageSticker(dmgSticker['texName'], dmgSticker['bumpTexName'], dmgSticker['rayStart'], dmgSticker['rayEnd'], dmgSticker['sizes'], dmgSticker['rayUp'])

        return

    def __detachStickers(self):
        for componentName, stickerDesc in self.__stickers.iteritems():
            stickerDesc['stickers'].detachStickers()
            for dmgSticker in stickerDesc['damageStickers'].itervalues():
                dmgSticker['handle'] = None

        return

    def __disableStipple(self):
        self.__vehicle.model.stipple = False
        self.__stippleCallbackID = None
        return


class StippleManager():

    def __init__(self):
        self.__stippleDescs = {}
        self.__stippleToAddDescs = {}

    def showFor(self, vehicle, model):
        if not model.stipple:
            model.stipple = True
            callbackID = BigWorld.callback(0.0, partial(self.__addStippleModel, vehicle.id))
            self.__stippleToAddDescs[vehicle.id] = (model, callbackID)

    def hideIfExistFor(self, vehicle):
        desc = self.__stippleDescs.get(vehicle.id)
        if desc is not None:
            BigWorld.cancelCallback(desc[1])
            BigWorld.player().delModel(desc[0])
            del self.__stippleDescs[vehicle.id]
        desc = self.__stippleToAddDescs.get(vehicle.id)
        if desc is not None:
            BigWorld.cancelCallback(desc[1])
            del self.__stippleToAddDescs[vehicle.id]
        return

    def destroy(self):
        for model, callbackID in self.__stippleDescs.itervalues():
            BigWorld.cancelCallback(callbackID)
            BigWorld.player().delModel(model)

        for model, callbackID in self.__stippleToAddDescs.itervalues():
            BigWorld.cancelCallback(callbackID)

        self.__stippleDescs = None
        self.__stippleToAddDescs = None
        return

    def __addStippleModel(self, vehID):
        model = self.__stippleToAddDescs[vehID][0]
        if model.attached:
            callbackID = BigWorld.callback(0.0, partial(self.__addStippleModel, vehID))
            self.__stippleToAddDescs[vehID] = (model, callbackID)
            return
        del self.__stippleToAddDescs[vehID]
        BigWorld.player().addModel(model)
        callbackID = BigWorld.callback(_VEHICLE_DISAPPEAR_TIME, partial(self.__removeStippleModel, vehID))
        self.__stippleDescs[vehID] = (model, callbackID)

    def __removeStippleModel(self, vehID):
        BigWorld.player().delModel(self.__stippleDescs[vehID][0])
        del self.__stippleDescs[vehID]


class _CrashedTrackController():

    def __init__(self, vehicle, va):
        self.__vehicle = vehicle.proxy
        self.__va = weakref.ref(va)
        self.__flags = 0
        self.__model = None
        self.__fashion = None
        self.__inited = True
        self.__forceHide = False
        self.__loadInfo = [False, False]
        return

    def isLeftTrackBroken(self):
        return self.__flags & 1

    def isRightTrackBroken(self):
        return self.__flags & 2

    def destroy(self):
        self.__vehicle = None
        return

    def setVisible(self, bool):
        self.__forceHide = not bool
        self.__setupTracksHiding(not bool)

    def addTrack(self, isLeft):
        if not self.__inited:
            return
        else:
            if self.__flags == 0 and self.__vehicle is not None and self.__vehicle.isPlayer:
                TriggersManager.g_manager.activateTrigger(TRIGGER_TYPE.PLAYER_VEHICLE_TRACKS_DAMAGED)
            if isLeft:
                self.__flags |= 1
            else:
                self.__flags |= 2
            if self.__model is None:
                self.__loadInfo = [True, isLeft]
                BigWorld.fetchModel(self.__va().modelsDesc['chassis']['_stateFunc'](self.__vehicle, 'destroyed'), self.__onModelLoaded)
            if self.__fashion is None:
                self.__fashion = BigWorld.WGVehicleFashion(True)
                _setupVehicleFashion(self.__fashion, self.__vehicle, True)
            self.__setupTracksHiding()
            return

    def delTrack(self, isLeft):
        if not self.__inited or self.__fashion is None:
            return
        else:
            if self.__loadInfo[0] and self.__loadInfo[1] == isLeft:
                self.__loadInfo = [False, False]
            if isLeft:
                self.__flags &= -2
            else:
                self.__flags &= -3
            self.__setupTracksHiding()
            if self.__flags == 0 and self.__model is not None:
                self.__va().modelsDesc['chassis']['model'].root.detach(self.__model)
                self.__model = None
                self.__fashion = None
            if self.__flags != 0 and self.__vehicle is not None and self.__vehicle.isPlayer:
                TriggersManager.g_manager.deactivateTrigger(TRIGGER_TYPE.PLAYER_VEHICLE_TRACKS_DAMAGED)
            return

    def receiveShotImpulse(self, dir, impulse):
        if not self.__inited or self.__fashion is None:
            return
        else:
            self.__fashion.receiveShotImpulse(dir, impulse)
            return

    def reset(self):
        if not self.__inited:
            return
        else:
            self.__flags = 0
            if self.__model is not None:
                self.__va().modelsDesc['chassis']['model'].root.detach(self.__model)
                self.__model = None
                self.__fashion = None
            return

    def __setupTracksHiding(self, force = False):
        if force or self.__forceHide:
            tracks = (True, True)
            invTracks = (True, True)
        else:
            tracks = (self.__flags & 1, self.__flags & 2)
            invTracks = (not tracks[0], not tracks[1])
        self.__va().fashion.hideTracks(*tracks)
        if self.__fashion is not None:
            self.__fashion.hideTracks(*invTracks)
        return

    def __onModelLoaded(self, model):
        if self.__va() is None or not self.__loadInfo[0] or not self.__inited:
            return
        else:
            va = self.__va()
            self.__loadInfo = [False, False]
            if model:
                self.__model = model
            else:
                self.__inited = False
                modelState = va.modelsDesc['chassis']['_stateFunc'](self.__vehicle, 'destroyed')
                LOG_ERROR('Model %s not loaded.' % modelState)
                return
            try:
                self.__model.wg_fashion = self.__fashion
                va.modelsDesc['chassis']['model'].root.attach(self.__model)
            except:
                va.fashion.hideTracks(False, False)
                self.__inited = False
                LOG_CURRENT_EXCEPTION()

            return


class _SkeletonCollider():

    def __init__(self, vehicle, vehicleAppearance):
        self.__vehicle = vehicle.proxy
        self.__vAppearance = weakref.proxy(vehicleAppearance)
        self.__boxAttachments = list()
        descr = vehicle.typeDescriptor
        descList = [('Scene Root', descr.chassis['hitTester'].bbox),
         ('Scene Root', descr.hull['hitTester'].bbox),
         ('Scene Root', descr.turret['hitTester'].bbox),
         ('Scene Root', descr.gun['hitTester'].bbox)]
        self.__createBoxAttachments(descList)
        vehicle.skeletonCollider = BigWorld.SkeletonCollider()
        for boxAttach in self.__boxAttachments:
            vehicle.skeletonCollider.addCollider(boxAttach)

        self.__vehicleHeight = self.__computeVehicleHeight()

    def destroy(self):
        delattr(self.__vehicle, 'skeletonCollider')
        self.__vehicle = None
        self.__vAppearance = None
        self.__boxAttachments = None
        return

    def attach(self):
        va = self.__vAppearance.modelsDesc
        collider = self.__vehicle.skeletonCollider.getCollider(0)
        va['chassis']['model'].node(collider.name).attach(collider)
        collider = self.__vehicle.skeletonCollider.getCollider(1)
        va['hull']['model'].node(collider.name).attach(collider)
        collider = self.__vehicle.skeletonCollider.getCollider(2)
        va['turret']['model'].node(collider.name).attach(collider)
        collider = self.__vehicle.skeletonCollider.getCollider(3)
        va['gun']['model'].node(collider.name).attach(collider)
        self.__vehicle.model.height = self.__vehicleHeight

    def detach(self):
        va = self.__vAppearance.modelsDesc
        collider = self.__vehicle.skeletonCollider.getCollider(0)
        va['chassis']['model'].node(collider.name).detach(collider)
        collider = self.__vehicle.skeletonCollider.getCollider(1)
        va['hull']['model'].node(collider.name).detach(collider)
        collider = self.__vehicle.skeletonCollider.getCollider(2)
        va['turret']['model'].node(collider.name).detach(collider)
        collider = self.__vehicle.skeletonCollider.getCollider(3)
        va['gun']['model'].node(collider.name).detach(collider)

    def __computeVehicleHeight(self):
        desc = self.__vehicle.typeDescriptor
        turretBBox = desc.turret['hitTester'].bbox
        gunBBox = desc.gun['hitTester'].bbox
        hullBBox = desc.hull['hitTester'].bbox
        hullTopY = desc.chassis['hullPosition'][1] + hullBBox[1][1]
        turretTopY = desc.chassis['hullPosition'][1] + desc.hull['turretPositions'][0][1] + turretBBox[1][1]
        gunTopY = desc.chassis['hullPosition'][1] + desc.hull['turretPositions'][0][1] + desc.turret['gunPosition'][1] + gunBBox[1][1]
        return max(hullTopY, max(turretTopY, gunTopY))

    def __createBoxAttachments(self, descList):
        for desc in descList:
            boxAttach = BigWorld.BoxAttachment()
            boxAttach.name = desc[0]
            boxAttach.minBounds = desc[1][0]
            boxAttach.maxBounds = desc[1][1]
            self.__boxAttachments.append(boxAttach)


def _almostZero(val, epsilon = 0.0004):
    return -epsilon < val < epsilon


def _createWheelsListByTemplate(startIndex, template, count):
    return [ '%s%d' % (template, i) for i in range(startIndex, startIndex + count) ]


def _setupVehicleFashion(fashion, vehicle, isCrashedTrack = False):
    vDesc = vehicle.typeDescriptor
    tracesCfg = vDesc.chassis['traces']
    tracksCfg = vDesc.chassis['tracks']
    wheelsCfg = vDesc.chassis['wheels']
    swingingCfg = vDesc.hull['swinging']
    if isinstance(vehicle.filter, BigWorld.WGVehicleFilter):
        fashion.placingCompensationMatrix = vehicle.filter.placingCompensationMatrix
        fashion.physicsInfo = vehicle.filter.physicsInfo
    fashion.movementInfo = vehicle.filter.movementInfo
    fashion.maxMovement = vDesc.physics['speedLimits'][0]
    pp = tuple((p * m for p, m in zip(swingingCfg['pitchParams'], _PITCH_SWINGING_MODIFIERS)))
    fashion.setPitchSwinging(_ROOT_NODE_NAME, *pp)
    fashion.setRollSwinging(_ROOT_NODE_NAME, *swingingCfg['rollParams'])
    fashion.setShotSwinging(_ROOT_NODE_NAME, swingingCfg['sensitivityToImpulse'])
    fashion.setLods(tracesCfg['lodDist'], wheelsCfg['lodDist'], tracksCfg['lodDist'], swingingCfg['lodDist'])
    try:
        fashion.setTracks(tracksCfg['leftMaterial'], tracksCfg['rightMaterial'], tracksCfg['textureScale'])
        if isCrashedTrack:
            return
        for group in wheelsCfg['groups']:
            nodes = _createWheelsListByTemplate(group[3], group[1], group[2])
            fashion.addWheelGroup(group[0], group[4], nodes)

        for wheel in wheelsCfg['wheels']:
            fashion.addWheel(wheel[0], wheel[2], wheel[1])

        textures = {}
        bumpTexId = -1
        for matKindName, texId in DecalMap.g_instance.getTextureSet(tracesCfg['textureSet']).iteritems():
            if matKindName == 'bump':
                bumpTexId = texId
            else:
                for matKind in material_kinds.EFFECT_MATERIAL_IDS_BY_NAMES[matKindName]:
                    textures[matKind] = texId

        fashion.setTrackTraces(tracesCfg['bufferPrefs'], textures, tracesCfg['centerOffset'], tracesCfg['size'], bumpTexId)
    except:
        LOG_CURRENT_EXCEPTION()


def _getSound(model, soundName):
    try:
        sound = model.playSound(soundName)
        if sound is None:
            raise Exception, "can not load sound '%s'" % soundName
        return sound
    except Exception:
        LOG_CURRENT_EXCEPTION()
        return

    return


def _restoreSoundParam(sound, paramName, paramValue):
    param = sound.param(paramName)
    if param is not None and param.value == 0.0 and param.value != paramValue:
        seekSpeed = param.seekSpeed
        param.seekSpeed = 0
        param.value = paramValue
        param.seekSpeed = seekSpeed
    return


def _seekSoundParam(sound, paramName, paramValue):
    param = sound.param(paramName)
    if param is not None and param.value != paramValue:
        seekSpeed = param.seekSpeed
        param.seekSpeed = 0
        param.value = paramValue
        param.seekSpeed = seekSpeed
    return


def _validateCfgPos(srcModelDesc, dstModelDesc, cfgPos, paramName, vehicle, state):
    invMat = Math.Matrix(srcModelDesc['model'].root)
    invMat.invert()
    invMat.preMultiply(Math.Matrix(dstModelDesc['_node']))
    realOffset = invMat.applyToOrigin()
    length = (realOffset - cfgPos).length
    if length > 0.01 and not _almostZero(realOffset.length):
        modelState = srcModelDesc['_stateFunc'](self.__vehicle, state)
        LOG_WARNING('%s parameter is incorrect. \n Note: it must be <%s>.\nPlayer: %s; Model: %s' % (paramName,
         realOffset,
         vehicle.publicInfo['name'],
         modelState))
        dstModelDesc['model'].visibleAttachments = True
        dstModelDesc['model'].visible = False

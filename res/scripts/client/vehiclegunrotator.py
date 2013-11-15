# 2013.11.15 11:27:27 EST
# Embedded file name: scripts/client/VehicleGunRotator.py
import BigWorld, Math
import weakref
import math
from AvatarInputHandler.CallbackDelayer import CallbackDelayer, TimeDeltaMeter
from account_helpers.SettingsCore import g_settingsCore
from constants import SERVER_TICK_LENGTH, SHELL_TRAJECTORY_EPSILON_CLIENT, AIMING_MODE
from projectile_trajectory import getShotAngles
from ProjectileMover import collideDynamicAndStatic, collideVehiclesAndStaticScene
from debug_utils import *
from math import pi, sin, cos, atan, atan2, sqrt, fmod
from projectile_trajectory import computeProjectileTrajectory
from ModelHitTester import segmentMayHitVehicle
import BattleReplay
from gun_rotation_shared import calcPitchLimitsFromDesc
from account_helpers.AccountSettings import AccountSettings
_ENABLE_TURRET_ROTATOR_SOUND = True

class VehicleGunRotator(object):
    __INSUFFICIENT_TIME_DIFF = 0.02
    __MAX_TIME_DIFF = 0.2
    __ROTATION_TICK_LENGTH = SERVER_TICK_LENGTH
    USE_LOCK_PREDICTION = True

    def __init__(self, avatar):
        self.__avatar = weakref.proxy(avatar)
        self.__isStarted = False
        self.__prevSentShotPoint = None
        self.__targetLastShotPoint = False
        self.__lastShotPoint = Math.Vector3(0, 0, 0)
        self.__shotPointSourceFunctor = self.__shotPointSourceFunctor_Default
        self.__maxTurretRotationSpeed = None
        self.__maxGunRotationSpeed = None
        self.__turretYaw = 0.0
        self.__gunPitch = 0.0
        self.__turretRotationSpeed = 0.0
        self.__dispersionAngle = 0.0
        self.__markerInfo = (Math.Vector3(0.0, 0.0, 0.0), Math.Vector3(0.0, 1.0, 0.0), 1.0)
        self.__clientMode = True
        self.__showServerMarker = False
        self.__time = None
        self.__timerID = None
        self.__turretMatrixAnimator = _MatrixAnimator(self.__avatar)
        self.__gunMatrixAnimator = _MatrixAnimator(self.__avatar)
        self.__isLocked = False
        self.estimatedTurretRotationTime = 0
        self.__turretRotationSoundEffect = _PlayerTurretRotationSoundEffect()
        BigWorld.player().inputHandler.onCameraChanged += self.__onCameraChanged
        return

    def destroy(self):
        self.stop()
        self.__turretMatrixAnimator.destroy(self.__avatar)
        self.__gunMatrixAnimator.destroy(self.__avatar)
        self.__avatar = None
        self.__shotPointSourceFunctor = None
        self.__turretRotationSoundEffect.destroy()
        BigWorld.player().inputHandler.onCameraChanged -= self.__onCameraChanged
        return

    def start(self):
        if self.__isStarted:
            return
        elif self.__maxTurretRotationSpeed is None:
            return
        elif not self.__avatar.isOnArena or not self.__avatar.isVehicleAlive:
            return
        else:
            self.showServerMarker = g_settingsCore.getSetting('useServerAim')
            g_settingsCore.onSettingsChanged += self.applySettings
            self.__isStarted = True
            self.__updateGunMarker()
            self.__timerID = BigWorld.callback(self.__ROTATION_TICK_LENGTH, self.__onTick)
            if self.__clientMode:
                self.__time = BigWorld.time()
                if self.__showServerMarker:
                    self.__avatar.inputHandler.showGunMarker2(True)
            return

    def applySettings(self, diff):
        if 'useServerAim' in diff:
            self.showServerMarker = diff['useServerAim']

    def stop(self):
        if not self.__isStarted:
            return
        else:
            if self.__timerID is not None:
                BigWorld.cancelCallback(self.__timerID)
                self.__timerID = None
            if self.__avatar.inputHandler is None:
                return
            if self.__clientMode and self.__showServerMarker:
                self.__avatar.inputHandler.showGunMarker2(False)
            g_settingsCore.onSettingsChanged -= self.applySettings
            self.__isStarted = False
            return

    def lock(self, isLocked):
        self.__isLocked = isLocked

    def update(self, turretYaw, gunPitch, maxTurretRotationSpeed, maxGunRotationSpeed):
        if self.__timerID is None or maxTurretRotationSpeed < self.__maxTurretRotationSpeed:
            self.__turretYaw = turretYaw
            self.__gunPitch = gunPitch
            self.__updateTurretMatrix(turretYaw, 0.0)
            self.__updateGunMatrix(gunPitch, 0.0)
        self.__maxTurretRotationSpeed = maxTurretRotationSpeed
        self.__maxGunRotationSpeed = maxGunRotationSpeed
        self.__turretRotationSpeed = 0.0
        self.__dispersionAngle = self.__avatar.getOwnVehicleShotDispersionAngle(0.0)
        self.start()
        return

    def setShotPosition(self, shotPos, shotVec, dispersionAngle):
        if self.__clientMode and not self.__showServerMarker:
            return
        self.__dispersionAngle = dispersionAngle
        if not self.__clientMode and VehicleGunRotator.USE_LOCK_PREDICTION:
            lockEnabled = BigWorld.player().inputHandler.getAimingMode(AIMING_MODE.TARGET_LOCK)
            if lockEnabled:
                predictedTargetPos = self.__predictLockedTargetShotPoint()
                dirToTarget = predictedTargetPos - shotPos
                dirToTarget.normalise()
                shotDir = Math.Vector3(shotVec)
                shotDir.normalise()
                if shotDir.dot(dirToTarget) > 0.0:
                    return
        markerPos, markerDir, markerSize, collData = self.__getGunMarkerPosition(shotPos, shotVec, dispersionAngle)
        if self.__clientMode and self.__showServerMarker:
            self.__avatar.inputHandler.updateGunMarker2(markerPos, markerDir, markerSize, SERVER_TICK_LENGTH, collData)
        if not self.__clientMode:
            self.__lastShotPoint = markerPos
            self.__avatar.inputHandler.updateGunMarker(markerPos, markerDir, markerSize, SERVER_TICK_LENGTH, collData)
            self.__turretYaw, self.__gunPitch = getShotAngles(self.__avatar.vehicleTypeDescriptor, self.__avatar.getOwnVehicleMatrix(), (self.__turretYaw, self.__gunPitch), markerPos, True)
            self.__updateTurretMatrix(self.__turretYaw, SERVER_TICK_LENGTH)
            self.__updateGunMatrix(self.__gunPitch, SERVER_TICK_LENGTH)
            self.__markerInfo = (markerPos, markerDir, markerSize)

    def __predictLockedTargetShotPoint(self):
        autoAimVehicle = BigWorld.player().autoAimVehicle
        if autoAimVehicle is not None:
            autoAimPosition = Math.Vector3(autoAimVehicle.position)
            autoAimPosition.y += autoAimVehicle.typeDescriptor.chassis['hullPosition'].y + autoAimVehicle.typeDescriptor.hull['turretPositions'][0].y
            return autoAimPosition
        else:
            return

    def getShotParams(self, targetPoint, ignoreYawLimits = False):
        descr = self.__avatar.vehicleTypeDescriptor
        shotTurretYaw, shotGunPitch = getShotAngles(descr, self.__avatar.getOwnVehicleMatrix(), (self.__turretYaw, self.__gunPitch), targetPoint)
        gunPitchLimits = calcPitchLimitsFromDesc(shotTurretYaw, descr.gun['pitchLimits'])
        closestLimit = self.__isOutOfLimits(shotGunPitch, gunPitchLimits)
        if closestLimit is not None:
            shotGunPitch = closestLimit
        turretYawLimits = descr.gun['turretYawLimits']
        if not ignoreYawLimits:
            closestLimit = self.__isOutOfLimits(shotTurretYaw, turretYawLimits)
            if closestLimit is not None:
                shotTurretYaw = closestLimit
        pos, vel = self.__getShotPosition(shotTurretYaw, shotGunPitch)
        grav = Math.Vector3(0.0, -descr.shot['gravity'], 0.0)
        return (pos, vel, grav)

    def __set_clientMode(self, value):
        if self.__clientMode == value:
            return
        self.__clientMode = value
        if not self.__isStarted:
            return
        if self.__clientMode:
            self.__time = BigWorld.time()
        if self.__showServerMarker:
            self.__avatar.inputHandler.showGunMarker2(self.__clientMode)

    clientMode = property(lambda self: self.__clientMode, __set_clientMode)

    def __set_showServerMarker(self, value):
        if self.__showServerMarker == value:
            return
        self.__showServerMarker = value
        BigWorld.player().enableServerAim(self.showServerMarker)
        if not self.__isStarted:
            return
        if self.__clientMode:
            self.__avatar.inputHandler.showGunMarker2(self.__showServerMarker)

    showServerMarker = property(lambda self: self.__showServerMarker, __set_showServerMarker)

    def __set_targetLastShotPoint(self, value):
        self.__targetLastShotPoint = value

    targetLastShotPoint = property(lambda self: self.__targetLastShotPoint, __set_targetLastShotPoint)

    def __set_shotPointSourceFunctor(self, value):
        if value is not None:
            self.__shotPointSourceFunctor = value
        else:
            self.__shotPointSourceFunctor = self.__shotPointSourceFunctor_Default
        return

    shotPointSourceFunctor = property(lambda self: self.__shotPointSourceFunctor, __set_shotPointSourceFunctor)

    def __shotPointSourceFunctor_Default(self):
        pt = None
        replayCtrl = BattleReplay.g_replayCtrl
        if replayCtrl.isPlaying:
            pt = replayCtrl.getGunRotatorTargetPoint()
        else:
            pt = self.__avatar.inputHandler.getDesiredShotPoint()
            if replayCtrl.isRecording:
                if pt is not None:
                    replayCtrl.setGunRotatorTargetPoint(pt)
        return pt

    turretMatrix = property(lambda self: self.__turretMatrixAnimator.matrix)
    gunMatrix = property(lambda self: self.__gunMatrixAnimator.matrix)
    turretRotationSpeed = property(lambda self: self.__turretRotationSpeed)
    dispersionAngle = property(lambda self: self.__dispersionAngle)
    markerInfo = property(lambda self: self.__markerInfo)

    def __onTick(self):
        self.__timerID = BigWorld.callback(self.__ROTATION_TICK_LENGTH, self.__onTick)
        lockEnabled = BigWorld.player().inputHandler.getAimingMode(AIMING_MODE.TARGET_LOCK)
        usePredictedLockShotPoint = lockEnabled and VehicleGunRotator.USE_LOCK_PREDICTION
        replayCtrl = BattleReplay.g_replayCtrl
        if not self.__clientMode and not replayCtrl.isPlaying and not usePredictedLockShotPoint:
            return
        else:
            predictedLockShotPoint = self.__predictLockedTargetShotPoint() if usePredictedLockShotPoint else None
            shotPoint = self.__shotPointSourceFunctor() if predictedLockShotPoint is None else predictedLockShotPoint
            if shotPoint is None and self.__targetLastShotPoint:
                shotPoint = self.__lastShotPoint
            self.__updateShotPointOnServer(shotPoint)
            timeDiff = self.__getTimeDiff()
            if timeDiff is None:
                return
            self.__time = BigWorld.time()
            self.__rotate(shotPoint, timeDiff)
            self.__updateGunMarker()
            return

    def __getTimeDiff(self):
        timeDiff = BigWorld.time() - self.__time
        if timeDiff < self.__INSUFFICIENT_TIME_DIFF:
            return None
        else:
            if timeDiff > self.__MAX_TIME_DIFF:
                timeDiff = self.__MAX_TIME_DIFF
            return timeDiff

    def __updateShotPointOnServer(self, shotPoint):
        if shotPoint == self.__prevSentShotPoint:
            return
        else:
            self.__prevSentShotPoint = shotPoint
            if shotPoint is None:
                self.__avatar.base.vehicle_stopTrackingWithGun(self.__turretYaw, self.__gunPitch)
            else:
                vehicle = BigWorld.entity(self.__avatar.playerVehicleID)
                if vehicle is not None:
                    vehicle.cell.trackPointWithGun(shotPoint)
                else:
                    self.__avatar.base.vehicle_trackPointWithGun(shotPoint)
            return

    def __rotate(self, shotPoint, timeDiff):
        self.__turretRotationSpeed = 0.0
        if shotPoint is None or self.__isLocked:
            self.__dispersionAngle = self.__avatar.getOwnVehicleShotDispersionAngle(0.0)
            return
        else:
            avatar = self.__avatar
            descr = avatar.vehicleTypeDescriptor
            turretYawLimits = descr.gun['turretYawLimits']
            maxTurretRotationSpeed = self.__maxTurretRotationSpeed
            prevTurretYaw = self.__turretYaw
            shotTurretYaw, shotGunPitch = getShotAngles(descr, avatar.getOwnVehicleMatrix(), (prevTurretYaw, self.__gunPitch), shotPoint)
            self.__turretYaw = turretYaw = self.__getNextTurretYaw(prevTurretYaw, shotTurretYaw, maxTurretRotationSpeed * timeDiff, turretYawLimits)
            if maxTurretRotationSpeed != 0:
                self.estimatedTurretRotationTime = abs(turretYaw - shotTurretYaw) / maxTurretRotationSpeed
            else:
                self.estimatedTurretRotationTime = 0
            gunPitchLimits = calcPitchLimitsFromDesc(turretYaw, descr.gun['pitchLimits'])
            self.__gunPitch = self.__getNextGunPitch(self.__gunPitch, shotGunPitch, self.__maxGunRotationSpeed * timeDiff, gunPitchLimits)
            self.__updateTurretMatrix(turretYaw, self.__ROTATION_TICK_LENGTH)
            self.__updateGunMatrix(self.__gunPitch, self.__ROTATION_TICK_LENGTH)
            diff = abs(turretYaw - prevTurretYaw)
            if diff > pi:
                diff = 2 * pi - diff
            self.__turretRotationSpeed = diff / timeDiff
            self.__dispersionAngle = avatar.getOwnVehicleShotDispersionAngle(self.__turretRotationSpeed)
            return

    def __updateGunMarker(self):
        shotPos, shotVec = self.__getCurShotPosition()
        markerPos, markerDir, markerSize, collData = self.__getGunMarkerPosition(shotPos, shotVec, self.__dispersionAngle)
        if not self.__targetLastShotPoint:
            self.__lastShotPoint = markerPos
        self.__avatar.inputHandler.updateGunMarker(markerPos, markerDir, markerSize, self.__ROTATION_TICK_LENGTH, collData)
        self.__markerInfo = (markerPos, markerDir, markerSize)

    def __getNextTurretYaw(self, curAngle, shotAngle, speedLimit, angleLimits):
        replayCtrl = BattleReplay.g_replayCtrl
        if replayCtrl.isPlaying:
            turretYaw = replayCtrl.getTurretYaw()
            if turretYaw > -100000:
                return turretYaw
        if curAngle == shotAngle:
            return curAngle
        shortWayDiff, longWayDiff = self.__getRotationWays(curAngle, shotAngle)
        if speedLimit < 1e-05:
            return curAngle
        closestLimit = self.__isOutOfLimits(curAngle, angleLimits)
        if closestLimit is not None:
            return closestLimit
        shortWayDiffLimited = self.__applyTurretYawLimits(shortWayDiff, curAngle, angleLimits)
        if shortWayDiffLimited == shortWayDiff:
            return self.__getTurretYawWithSpeedLimit(curAngle, shortWayDiff, speedLimit)
        longWayDiffLimited = self.__applyTurretYawLimits(longWayDiff, curAngle, angleLimits)
        if longWayDiffLimited == longWayDiff:
            return self.__getTurretYawWithSpeedLimit(curAngle, longWayDiff, speedLimit)
        else:
            return self.__getTurretYawWithSpeedLimit(curAngle, shortWayDiffLimited, speedLimit)

    def __getRotationWays(self, curAngle, shotAngle):
        shotDiff1 = shotAngle - curAngle
        if shotDiff1 < 0:
            shotDiff2 = 2 * pi + shotDiff1
        else:
            shotDiff2 = -2 * pi + shotDiff1
        if abs(shotDiff1) <= pi:
            return (shotDiff1, shotDiff2)
        else:
            return (shotDiff2, shotDiff1)

    def __isOutOfLimits(self, angle, limits):
        if limits is None:
            return
        elif abs(limits[1] - angle) < 1e-05 or abs(limits[0] - angle) < 1e-05:
            return
        else:
            dpi = 2 * pi
            minDiff = fmod(limits[0] - angle + dpi, dpi)
            maxDiff = fmod(limits[1] - angle + dpi, dpi)
            if minDiff > maxDiff:
                return
            elif minDiff < dpi - maxDiff:
                return limits[0]
            return limits[1]
            return

    def __applyTurretYawLimits(self, diff, angle, limits):
        if limits is None:
            return diff
        else:
            dpi = 2 * pi
            if diff > 0:
                if abs(limits[1] - angle) < 1e-05:
                    return 0
                maxDiff = fmod(limits[1] - angle + dpi, dpi)
                return min(maxDiff, diff)
            if abs(limits[0] - angle) < 1e-05:
                return 0
            maxDiff = fmod(limits[0] - angle - dpi, dpi)
            return max(maxDiff, diff)
            return

    def __getTurretYawWithSpeedLimit(self, angle, diff, limit):
        dpi = 2 * pi
        if diff > 0:
            return fmod(pi + angle + min(diff, limit), dpi) - pi
        else:
            return fmod(-pi + angle + max(diff, -limit), dpi) + pi

    def __getNextGunPitch(self, curAngle, shotAngle, speedLimit, angleLimits):
        replayCtrl = BattleReplay.g_replayCtrl
        if replayCtrl.isPlaying:
            gunPitch = replayCtrl.getGunPitch()
            if gunPitch > -100000:
                return gunPitch
        if curAngle == shotAngle:
            return curAngle
        else:
            shotDiff = shotAngle - curAngle
            if angleLimits is not None:
                if shotAngle < angleLimits[0]:
                    shotDiff = angleLimits[0] - curAngle
                elif shotAngle > angleLimits[1]:
                    shotDiff = angleLimits[1] - curAngle
            if shotDiff > 0:
                return curAngle + min(shotDiff, speedLimit)
            return curAngle + max(shotDiff, -speedLimit)
            return

    def __getShotPosition(self, turretYaw, gunPitch):
        descr = self.__avatar.vehicleTypeDescriptor
        turretOffs = descr.hull['turretPositions'][0] + descr.chassis['hullPosition']
        gunOffs = descr.turret['gunPosition']
        shotSpeed = descr.shot['speed']
        turretWorldMatrix = Math.Matrix()
        turretWorldMatrix.setRotateY(turretYaw)
        turretWorldMatrix.translation = turretOffs
        turretWorldMatrix.postMultiply(Math.Matrix(self.__avatar.getOwnVehicleMatrix()))
        position = turretWorldMatrix.applyPoint(gunOffs)
        gunWorldMatrix = Math.Matrix()
        gunWorldMatrix.setRotateX(gunPitch)
        gunWorldMatrix.postMultiply(turretWorldMatrix)
        vector = gunWorldMatrix.applyVector(Math.Vector3(0, 0, shotSpeed))
        return (position, vector)

    def __getCurShotPosition(self):
        return self.__getShotPosition(self.__turretYaw, self.__gunPitch)

    def __getGunMarkerPosition(self, shotPos, shotVec, dispersionAngle):
        shotDescr = self.__avatar.vehicleTypeDescriptor.shot
        gravity = Math.Vector3(0.0, -shotDescr['gravity'], 0.0)
        maxDist = shotDescr['maxDistance']
        vehicles = []
        testStartPoint = shotPos
        testEndPoint = shotPos + shotVec * 10000.0
        for vehicleID in BigWorld.player().arena.vehicles.iterkeys():
            if vehicleID == self.__avatar.playerVehicleID:
                continue
            vehicle = BigWorld.entity(vehicleID)
            if vehicle is None or not vehicle.isStarted:
                continue
            if segmentMayHitVehicle(vehicle.typeDescriptor, testStartPoint, testEndPoint, vehicle.position):
                vehicles.append(vehicle)

        prevPos = shotPos
        prevVelocity = shotVec
        dt = 0.0
        maxDistCheckFlag = False
        while True:
            dt += SERVER_TICK_LENGTH
            checkPoints = computeProjectileTrajectory(prevPos, prevVelocity, gravity, SERVER_TICK_LENGTH, SHELL_TRAJECTORY_EPSILON_CLIENT)
            prevCheckPoint = prevPos
            bBreak = False
            for curCheckPoint in checkPoints:
                testRes = collideVehiclesAndStaticScene(prevCheckPoint, curCheckPoint, vehicles)
                if testRes is not None:
                    collData = testRes[1]
                    dir = testRes[0] - prevCheckPoint
                    endPos = testRes[0]
                    bBreak = True
                    break
                pos = self.__avatar.arena.collideWithSpaceBB(prevCheckPoint, curCheckPoint)
                if pos is not None:
                    collData = None
                    maxDistCheckFlag = True
                    dir = pos - prevCheckPoint
                    endPos = pos
                    bBreak = True
                    break
                prevCheckPoint = curCheckPoint

            if bBreak:
                break
            prevPos = shotPos + shotVec.scale(dt) + gravity.scale(dt * dt * 0.5)
            prevVelocity = shotVec + gravity.scale(dt)

        dir.normalise()
        distance = (endPos - shotPos).length
        markerDiameter = 2.0 * distance * dispersionAngle
        if maxDistCheckFlag:
            if endPos.distTo(shotPos) >= maxDist:
                dir = endPos - shotPos
                dir.normalise()
                endPos = shotPos + dir.scale(maxDist)
                distance = maxDist
                markerDiameter = 2.0 * distance * dispersionAngle
        replayCtrl = BattleReplay.g_replayCtrl
        if replayCtrl.isPlaying and replayCtrl.isClientReady:
            markerDiameter, endPos, dir = replayCtrl.getGunMarkerParams(endPos, dir)
        elif replayCtrl.isRecording:
            replayCtrl.setGunMarkerParams(markerDiameter, endPos, dir)
        return (endPos,
         dir,
         markerDiameter,
         collData)

    def __updateTurretMatrix(self, yaw, time):
        m = Math.Matrix()
        m.setRotateY(yaw)
        self.__turretMatrixAnimator.update(m, time)
        replayCtrl = BattleReplay.g_replayCtrl
        if replayCtrl.isRecording:
            replayCtrl.setTurretYaw(yaw)

    def __updateGunMatrix(self, pitch, time):
        m = Math.Matrix()
        m.setRotateX(pitch)
        self.__gunMatrixAnimator.update(m, time)
        replayCtrl = BattleReplay.g_replayCtrl
        if replayCtrl.isRecording:
            replayCtrl.setGunPitch(pitch)

    def __onCameraChanged(self, cameraName, currentVehicleId = None):
        self.__turretRotationSoundEffect.enable(cameraName == 'sniper' and _ENABLE_TURRET_ROTATOR_SOUND)


class _MatrixAnimator(object):

    def __init__(self, avatar):
        m = Math.Matrix()
        m.setIdentity()
        self.__animMat = Math.MatrixAnimation()
        self.__animMat.keyframes = ((0.0, m),)

    def destroy(self, avatar):
        self.__animMat = None
        return

    matrix = property(lambda self: self.__animMat)

    def update(self, matrix, time):
        self.__animMat.keyframes = ((0.0, Math.Matrix(self.__animMat)), (time, matrix))
        self.__animMat.time = 0.0


class _PlayerTurretRotationSoundEffect(CallbackDelayer, TimeDeltaMeter):
    __TURRET_MIN_YAW_SPEED = 0.001
    __SOUND_PARAM_DAMAGED = 'manual_traverse'

    def __init__(self, updatePeriod = 0.0):
        CallbackDelayer.__init__(self)
        TimeDeltaMeter.__init__(self)
        self.__updatePeriod = updatePeriod
        self.__turretSound = None
        self.__prevTurretYaw = None
        return

    def destroy(self):
        CallbackDelayer.destroy(self)
        if self.__turretSound is not None:
            self.__turretSound.stop()
        return

    def enable(self, enableSound):
        if enableSound:
            self.measureDeltaTime()
            self.delayCallback(self.__updatePeriod, self.__update)
            if self.__turretSound is None:
                self.__turretSound = self.__getSound()
            if self.__turretSound is not None:
                self.__turretSound.play()
        else:
            if self.__turretSound is not None:
                self.__turretSound.stop()
            self.__prevTurretYaw = None
            self.stopCallback(self.__update)
        return

    def __getSound(self):
        turretDesc = BigWorld.player().vehicleTypeDescriptor.turret
        eventName = turretDesc['turretRotatorSound']['event']
        if eventName != '':
            return BigWorld.getSound(eventName)
        else:
            return None

    def __update(self):
        deltaTime = self.measureDeltaTime()
        player = BigWorld.player()
        gunRotator = player.gunRotator
        currYaw = Math.Matrix(gunRotator.turretMatrix).yaw
        if self.__prevTurretYaw is None or self.__turretSound is None:
            self.__prevTurretYaw = currYaw
            return self.__updatePeriod
        else:
            turretDesc = BigWorld.player().vehicleTypeDescriptor.turret
            gearTypes = turretDesc['turretRotatorSound']['params']
            yawSpeed = abs(currYaw - self.__prevTurretYaw) / deltaTime
            self.__prevTurretYaw = currYaw
            if yawSpeed >= _PlayerTurretRotationSoundEffect.__TURRET_MIN_YAW_SPEED:
                param = self.__turretSound.param('speed')
                if param is not None:
                    param.value = yawSpeed
                isTurretDamaged = BigWorld.player().deviceStates.get('turretRotator', None) is not None
                audibleParams = []
                ceaseParams = []
                if not isTurretDamaged:
                    audibleParams = gearTypes
                    ceaseParams = [_PlayerTurretRotationSoundEffect.__SOUND_PARAM_DAMAGED] if _PlayerTurretRotationSoundEffect.__SOUND_PARAM_DAMAGED not in gearTypes else []
                else:
                    audibleParams = [_PlayerTurretRotationSoundEffect.__SOUND_PARAM_DAMAGED]
                    ceaseParams = [ x for x in gearTypes if x != _PlayerTurretRotationSoundEffect.__SOUND_PARAM_DAMAGED ]
                traverseValue = 1.0 / len(gearTypes)
                self.__setTurretSoundParams(self.__turretSound, audibleParams, traverseValue)
                self.__setTurretSoundParams(self.__turretSound, ceaseParams, 0.0)
            else:
                param = self.__turretSound.param('speed')
                if param is not None:
                    param.value = 0.0
                eventParams = gearTypes + [_PlayerTurretRotationSoundEffect.__SOUND_PARAM_DAMAGED]
                self.__setTurretSoundParams(self.__turretSound, eventParams, 0.0)
            return self.__updatePeriod

    def __setTurretSoundParams(self, turretSound, paramNames, value):
        for traverse in paramNames:
            param = turretSound.param(traverse)
            if param is not None:
                param.value = value

        return
# okay decompyling res/scripts/client/vehiclegunrotator.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:27:28 EST

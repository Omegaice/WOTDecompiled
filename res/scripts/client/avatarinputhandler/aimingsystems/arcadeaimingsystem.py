import BigWorld
import Math
from Math import Vector3, Matrix
import math
from AvatarInputHandler import mathUtils, AimingSystems, cameras
from AvatarInputHandler.AimingSystems import IAimingSystem
from ProjectileMover import collideDynamic
from debug_utils import LOG_WARNING
import gun_rotation_shared

class ArcadeAimingSystem(IAimingSystem):

    def __setDistanceFromFocus(self, value):
        shotPoint = self.getThirdPersonShotPoint()
        self.__cursor.distanceFromFocus = value
        posOnVehicleProv = self.positionAboveVehicleProv.value
        posOnVehicle = Vector3(posOnVehicleProv.x, posOnVehicleProv.y, posOnVehicleProv.z)
        camPos = self.matrix.translation
        triBase = camPos - posOnVehicle
        pivotToTarget = shotPoint - posOnVehicle
        camPosToTarget = shotPoint - camPos
        if triBase.dot(camPosToTarget) * triBase.dot(pivotToTarget) > 0:
            self.focusOnPos(shotPoint)

    def __setVehicleMProv(self, value):
        self.__vehicleMProv = value
        self.__cursor.base = value

    def __setYaw(self, value):
        self.__cursor.yaw = value
        if self.__cursor.yaw > 2.0 * math.pi:
            self.__cursor.yaw -= 2.0 * math.pi
        elif self.__cursor.yaw < -2.0 * math.pi:
            self.__cursor.yaw += 2.0 * math.pi

    def __setPitch(self, value):
        self.__cursor.pitch = mathUtils.clamp(self.__anglesRange[0], self.__anglesRange[1], value)

    vehicleMProv = property(lambda self: self.__vehicleMProv, __setVehicleMProv)
    positionAboveVehicleProv = property(lambda self: self.__cursor.positionAboveBaseProvider)
    distanceFromFocus = property(lambda self: self.__cursor.distanceFromFocus, __setDistanceFromFocus)
    yaw = property(lambda self: self.__cursor.yaw, __setYaw)
    pitch = property(lambda self: self.__cursor.pitch, __setPitch)

    def __init__(self, vehicleMProv, heightAboveTarget, focusRadius, aim, anglesRange, enableSmartShotPointCalc = True):
        IAimingSystem.__init__(self)
        self.__aimOffset = aim.offset()
        self.__vehicleMProv = vehicleMProv
        self.__anglesRange = anglesRange
        self.__cursor = BigWorld.ThirdPersonProvider()
        self.__cursor.base = vehicleMProv
        self.__cursor.heightAboveBase = heightAboveTarget
        self.__cursor.focusRadius = focusRadius
        self.__shotPointCalculator = ShotPointCalculator() if enableSmartShotPointCalc else None
        return

    def getPivotSettings(self):
        return (self.__cursor.heightAboveBase, self.__cursor.focusRadius)

    def setPivotSettings(self, heightAboveBase, focusRadius):
        self.__cursor.heightAboveBase = heightAboveBase
        self.__cursor.focusRadius = focusRadius

    def destroy(self):
        IAimingSystem.destroy(self)

    def enable(self, targetPos, turretYaw = None, gunPitch = None):
        if targetPos is not None:
            self.focusOnPos(targetPos)
            if turretYaw is None or gunPitch is None:
                return
            if self.__shotPointCalculator is not None:
                aimMatrix = cameras.getAimMatrix(*self.__aimOffset)
                scanStart, scanDir = self.__getScanRay()
                self.pitch = self.__shotPointCalculator.focusAtPos(scanStart, scanDir, turretYaw, gunPitch) - aimMatrix.pitch
        return

    def disable(self):
        pass

    def setModelsToCollideWith(self, models):
        self.__cursor.setModelsToCollideWith(models)

    def focusOnPos(self, preferredPos):
        vehPos = Matrix(self.__vehicleMProv).translation
        posOnVehicle = vehPos + Vector3(0, self.__cursor.heightAboveBase, 0)
        self.yaw = (preferredPos - vehPos).yaw
        xzDir = Vector3(self.__cursor.focusRadius * math.sin(self.__cursor.yaw), 0, self.__cursor.focusRadius * math.cos(self.__cursor.yaw))
        pivotPos = posOnVehicle + xzDir
        self.pitch = self.__calcPitchAngle(self.__cursor.distanceFromFocus, preferredPos - pivotPos)
        self.__cursor.update(True)
        aimMatrix = self.__getLookToAimMatrix()
        aimMatrix.postMultiply(self.__cursor.matrix)
        self._matrix.set(aimMatrix)

    def __calcPitchAngle(self, distanceFromFocus, dir):
        fov = BigWorld.projection().fov
        near = BigWorld.projection().nearPlane
        yLength = near * math.tan(fov * 0.5)
        alpha = math.atan2(yLength * self.__aimOffset[1], near)
        a = distanceFromFocus
        b = dir.length
        A = 2.0 * a * math.cos(alpha)
        B = a * a - b * b
        D = A * A - 4.0 * B
        if D > 0.0:
            c1 = (A + math.sqrt(D)) * 0.5
            c2 = (A - math.sqrt(D)) * 0.5
            c = c1 if c1 > c2 else c2
            cosValue = (a * a + b * b - c * c) / (2.0 * a * b)
            if cosValue < -1.0 or cosValue > 1.0:
                LOG_WARNING('Invalid arg for acos: %f; distanceFromFocus: %f, dir: %s' % (cosValue, distanceFromFocus, dir))
                return -dir.pitch
            beta = math.acos(cosValue)
            eta = math.pi - beta
            return -dir.pitch - eta
        else:
            return -dir.pitch

    def getDesiredShotPoint(self):
        scanStart, scanDir = self.__getScanRay()
        if self.__shotPointCalculator is None:
            return self.getThirdPersonShotPoint()
        else:
            return self.__shotPointCalculator.getDesiredShotPoint(scanStart, scanDir)
            return

    def getThirdPersonShotPoint(self):
        return AimingSystems.getDesiredShotPoint(*self.__getScanRay())

    def handleMovement(self, dx, dy):
        self.yaw += dx
        self.pitch += dy

    def update(self, deltaTime):
        self.__cursor.update(True)
        aimMatrix = self.__getLookToAimMatrix()
        aimMatrix.postMultiply(self.__cursor.matrix)
        self._matrix.set(aimMatrix)
        if self.__shotPointCalculator is not None:
            self.__shotPointCalculator.update(*self.__getScanRay())
        return 0.0

    def __getScanRay(self):
        scanDir = self.matrix.applyVector(Vector3(0, 0, 1))
        scanStart = self.matrix.translation + scanDir * 0.3
        return (scanStart, scanDir)

    def __getLookToAimMatrix(self):
        aimMatrix = cameras.getAimMatrix(-self.__aimOffset[0], -self.__aimOffset[1])
        return aimMatrix


class ShotPointCalculator(object):
    __STATE_WAIT_FOR_MOUSE_MOVE = 0
    __STATE_MOUSE_TRACK = 1
    __STATE_SMART_TRACK = 2
    MIN_DIST = 50
    TERRAIN_MIN_ANGLE = math.pi / 6

    def __init__(self):
        self.__turretWorldYaw = 0
        self.__gunWorldPitch = 0
        self.__state = ShotPointCalculator.__STATE_WAIT_FOR_MOUSE_MOVE
        self.__pitchDelta = 0
        self.__yawDelta = 0
        self.__vehicleMat = BigWorld.player().getOwnVehicleMatrix()
        self.__vehicleDesc = BigWorld.player().vehicleTypeDescriptor

    def update(self, scanStart, scanDir):
        scanTargetPoint = self.__updateMode(scanStart, scanDir)
        self.__updateDirections(scanDir, scanTargetPoint)

    def focusAtPos(self, scanStart, scanDir, turretYaw, gunPitch):
        turretMat = AimingSystems.getTurretJointMat(self.__vehicleDesc, self.__vehicleMat, turretYaw)
        gunMat = AimingSystems.getGunJointMat(self.__vehicleDesc, turretMat, gunPitch)
        self.__turretWorldYaw = turretMat.yaw
        self.__gunWorldPitch = gunMat.pitch
        self.__yawDelta = self.__turretWorldYaw - scanDir.yaw
        scanPos, enableSmartTrack = self.__testMouseTargetPoint(scanStart, scanDir)
        refocusedPitch = scanDir.pitch
        if enableSmartTrack:
            if self.__isMouseTrack():
                self.__pitchDelta = 0.0
            refocusedPitch = self.__gunWorldPitch - self.__pitchDelta
        else:
            self.__pitchDelta = self.__gunWorldPitch - scanDir.pitch
        return -refocusedPitch

    def getDesiredShotPoint(self, scanStart, scanDir):
        if self.__isMouseTrack():
            return AimingSystems.getDesiredShotPoint(scanStart, scanDir)
        return self.__getTargetPointFromTurret()

    def __isMouseTrack(self):
        return self.__state in (ShotPointCalculator.__STATE_WAIT_FOR_MOUSE_MOVE, ShotPointCalculator.__STATE_MOUSE_TRACK)

    def __updateMode(self, scanStart, scanDir, ignoreYawLimits = False):
        scanTargetPoint, enableSmartTrack = self.__testMouseTargetPoint(scanStart, scanDir)
        if self.__state == ShotPointCalculator.__STATE_WAIT_FOR_MOUSE_MOVE:
            self.__updateDirections(scanDir, scanTargetPoint)
            self.__state = ShotPointCalculator.__STATE_MOUSE_TRACK
        if not enableSmartTrack and not self.__state == ShotPointCalculator.__STATE_MOUSE_TRACK:
            self.__state = ShotPointCalculator.__STATE_MOUSE_TRACK
        elif enableSmartTrack and self.__state == ShotPointCalculator.__STATE_MOUSE_TRACK:
            self.__enterSmartTrackMode(scanDir, ignoreYawLimits)
        return scanTargetPoint

    def __updateDirections(self, scanDir, scanTargetPoint):
        if scanTargetPoint is None:
            return
        else:
            if self.__isMouseTrack():
                turretStartPoint = self.__getTurretPos()
                turretLookDir = scanTargetPoint - turretStartPoint
                self.__turretWorldYaw = turretLookDir.yaw
                turretStartPoint, gunStartPoint = self.__getTurretStartPoints()
                gunLookDir = scanTargetPoint - gunStartPoint
                self.__gunWorldPitch = gunLookDir.pitch
            else:
                self.__turretWorldYaw = scanDir.yaw + self.__yawDelta
                self.__gunWorldPitch = scanDir.pitch + self.__pitchDelta
                minPitch, maxPitch = self.__getMinMaxPitchWorld(self.__turretWorldYaw)
                self.__gunWorldPitch = mathUtils.clamp(minPitch, maxPitch, self.__gunWorldPitch)
            return

    def __getMinMaxPitchWorld(self, worldYaw):
        player = BigWorld.player()
        desc = player.vehicleTypeDescriptor
        if desc is None:
            return (0, 0)
        else:
            vehMat = Matrix(self.__vehicleMat)
            turretYaw = worldYaw - vehMat.yaw
            localPitches = gun_rotation_shared.calcPitchLimitsFromDesc(turretYaw, desc.gun['pitchLimits'])
            return (localPitches[0] + vehMat.pitch, localPitches[1] + vehMat.pitch)

    def __testMouseTargetPoint(self, start, dir):
        dir.normalise()
        end = start + dir.scale(10000.0)
        testResTerrain = BigWorld.wg_collideSegment(BigWorld.player().spaceID, start, end, 128, lambda matKind, collFlags, itemId, chunkId: collFlags & 8)
        if testResTerrain:
            terrainSuitsForCheck = testResTerrain[1].dot(Math.Vector3(0, 1, 0)) <= math.cos(ShotPointCalculator.TERRAIN_MIN_ANGLE)
            testResNonTerrain = BigWorld.wg_collideSegment(BigWorld.player().spaceID, start, end, 136)
            testResDynamic = collideDynamic(start, end, (BigWorld.player().playerVehicleID,), False)
            closestPoint = None
            closestDist = 1000000
            enableSmartTrack = False
            if testResTerrain:
                closestPoint = testResTerrain[0]
                closestDist = (testResTerrain[0] - start).length
            if terrainSuitsForCheck:
                enableSmartTrack = closestDist <= ShotPointCalculator.MIN_DIST
            if testResNonTerrain is not None:
                dist = (testResNonTerrain[0] - start).length
                if dist < closestDist:
                    closestPoint = testResNonTerrain[0]
                    closestDist = dist
                    enableSmartTrack = closestDist <= ShotPointCalculator.MIN_DIST
            return closestPoint is None and testResDynamic is None and (AimingSystems.shootInSkyPoint(start, dir), False)
        else:
            if testResDynamic is not None:
                dynDist = testResDynamic[1]
                if dynDist <= closestDist:
                    dir = end - start
                    dir.normalise()
                    closestPoint = start + dir * dynDist
                    enableSmartTrack = False
            if enableSmartTrack:
                turretPos = self.__getTurretPos()
                turretLookDirYaw = (closestPoint - turretPos).yaw
                turretPos, gunPos = self.__getTurretStartPoints()
                gunLookDirPitch = (closestPoint - gunPos).pitch
                minPitch, maxPitch = self.__getMinMaxPitchWorld(turretLookDirYaw)
                pitchInBorders = gunLookDirPitch <= maxPitch
                tooLow = closestPoint.y < turretPos.y
                if enableSmartTrack and pitchInBorders:
                    enableSmartTrack = not tooLow
                enableSmartTrack = enableSmartTrack or self.__isTurretTurnRequired(dir, closestPoint)
            return (closestPoint, enableSmartTrack)

    def __isTurretTurnRequired(self, viewDir, targetPoint):
        turretPos = self.__getTurretPos()
        dirFromTurretPos = targetPoint - turretPos
        turretPos, gunStartToLookOnTarget = self.__getTurretStartPoints(dirFromTurretPos.yaw)
        dirFromSniperPos = targetPoint - gunStartToLookOnTarget
        viewDir = Math.Vector3(viewDir)
        viewDir.y = 0
        viewDir.normalise()
        dirFromSniperPos.y = 0
        dirFromSniperPos.normalise()
        dirFromTurretPos.y = 0
        dirFromTurretPos.normalise()
        return viewDir.dot(dirFromSniperPos) < 0 or viewDir.dot(dirFromTurretPos) < 0

    def __getMaxYawDelta(self):
        if ShotPointCalculator.MIN_DIST <= 0.0:
            return 0.0
        player = BigWorld.player()
        vehicleTypeDescriptor = player.vehicleTypeDescriptor
        vehicleMatrix = Matrix(player.getOwnVehicleMatrix())
        turretMat = AimingSystems.getTurretJointMat(vehicleTypeDescriptor, vehicleMatrix)
        vehiclePos = vehicleMatrix.translation
        shiftVec = vehiclePos - turretMat.translation
        shiftVec.y = 0.0
        shift = shiftVec.length
        return abs(math.atan(shift / ShotPointCalculator.MIN_DIST))

    def __enterSmartTrackMode(self, viewDir, ignoreYawLimits = False):
        self.__state = ShotPointCalculator.__STATE_SMART_TRACK
        self.__pitchDelta = self.__gunWorldPitch - viewDir.pitch
        self.__yawDelta = self.__turretWorldYaw - viewDir.yaw
        maxYawDelta = math.pi if ignoreYawLimits else self.__getMaxYawDelta()
        self.__yawDelta = mathUtils.clamp(-maxYawDelta, maxYawDelta, self.__yawDelta)
        self.__smartTrackYaw = viewDir.yaw + self.__yawDelta

    def __getTurretStartPoints(self, predefinedWorldYaw = None):
        yaw = self.__turretWorldYaw if predefinedWorldYaw is None else predefinedWorldYaw
        turretMat, gunMat = AimingSystems.getPlayerTurretMats(yaw - Matrix(self.__vehicleMat).yaw)
        return (turretMat.translation, gunMat.translation)

    def __getTurretPos(self):
        return AimingSystems.getTurretJointMat(self.__vehicleDesc, self.__vehicleMat).translation

    def __getTargetPointFromTurret(self):
        turretTranslation, gunTranslation = self.__getTurretStartPoints()
        dirMat = Math.Matrix()
        dirMat.setRotateYPR((self.__turretWorldYaw, self.__gunWorldPitch, 0))
        dir = dirMat.applyToAxis(2)
        return AimingSystems.getDesiredShotPoint(gunTranslation, dir)

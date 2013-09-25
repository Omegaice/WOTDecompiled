import BigWorld
import Math
import GUI
from Math import Vector3, Matrix
import math
from AvatarInputHandler import mathUtils
from AvatarInputHandler import AimingSystems
from AvatarInputHandler.AimingSystems import IAimingSystem
from AvatarInputHandler.Oscillator import Oscillator
from gun_rotation_shared import calcPitchLimitsFromDesc
from projectile_trajectory import getShotAngles

class SniperAimingSystem(IAimingSystem):
    turretYaw = property(lambda self: self.__idealTurretYaw + self.__oscillator.deviation.x)
    gunPitch = property(lambda self: self.__idealGunPitch + self.__oscillator.deviation.y)
    USE_DAMPING = True

    def __init__(self):
        IAimingSystem.__init__(self)
        self.__idealTurretYaw = 0.0
        self.__idealGunPitch = 0.0
        self.__worldYaw = 0.0
        self.__worldPitch = 0.0
        self.__vehicleTypeDescriptor = None
        self.__vehicleMProv = None
        self.__vehiclePrevMat = None
        self.__oscillator = Oscillator(1.0, Vector3(0.0, 0.0, 15.0), Vector3(0.0, 0.0, 3.5), Vector3(math.pi * 2.1, math.pi / 2 * 0.95, 0.0))
        return

    def destroy(self):
        IAimingSystem.destroy(self)

    def enableHorizontalStabilizer(self, enable):
        yawConstraint = math.pi * 2.1 if enable else 0.0
        self.__oscillator.constraints.x = yawConstraint

    def enable(self, targetPos):
        player = BigWorld.player()
        self.__vehicleTypeDescriptor = player.vehicleTypeDescriptor
        self.__vehicleMProv = player.getOwnVehicleMatrix()
        self.__vehiclePrevMat = Matrix(self.__vehicleMProv)
        IAimingSystem.enable(self, targetPos)
        player = BigWorld.player()
        desc = player.vehicleTypeDescriptor
        self.__yawLimits = desc.gun['turretYawLimits']
        self.__idealTurretYaw, self.__idealGunPitch = getShotAngles(desc, player.getOwnVehicleMatrix(), (0, 0), targetPos, False)
        self.__idealTurretYaw, self.__idealGunPitch = self.__clampToLimits(self.__idealTurretYaw, self.__idealGunPitch)
        currentGunMat = AimingSystems.getPlayerGunMat(self.__idealTurretYaw, self.__idealGunPitch)
        self.__worldYaw = currentGunMat.yaw
        self.__worldPitch = (targetPos - currentGunMat.translation).pitch
        self._matrix.set(currentGunMat)
        self.__idealTurretYaw, self.__idealGunPitch = self.__worldYawPitchToTurret(self.__worldYaw, self.__worldPitch)
        self.__idealTurretYaw, self.__idealGunPitch = self.__clampToLimits(self.__idealTurretYaw, self.__idealGunPitch)
        self.__oscillator.reset()

    def getDesiredShotPoint(self):
        start = self.matrix.translation
        scanDir = self.matrix.applyVector(Vector3(0, 0, 1))
        return AimingSystems.getDesiredShotPoint(start, scanDir)

    def handleMovement(self, dx, dy):
        self.__idealTurretYaw, self.__idealGunPitch = self.__worldYawPitchToTurret(self.__worldYaw, self.__worldPitch)
        self.__idealTurretYaw, self.__idealGunPitch = self.__clampToLimits(self.__idealTurretYaw, self.__idealGunPitch)
        self.__idealTurretYaw += dx
        self.__idealGunPitch += dy
        self.__idealTurretYaw, self.__idealGunPitch = self.__clampToLimits(self.__idealTurretYaw, self.__idealGunPitch)
        currentGunMat = AimingSystems.getPlayerGunMat(self.__idealTurretYaw, self.__idealGunPitch)
        self.__worldYaw = currentGunMat.yaw
        self.__worldPitch = currentGunMat.pitch
        self._matrix.set(currentGunMat)
        self.__oscillator.velocity = Vector3(0, 0, 0)

    def __clampToLimits(self, turretYaw, gunPitch):
        if self.__yawLimits is not None:
            turretYaw = mathUtils.clamp(self.__yawLimits[0], self.__yawLimits[1], turretYaw)
        desc = BigWorld.player().vehicleTypeDescriptor
        pitchLimits = calcPitchLimitsFromDesc(turretYaw, desc.gun['pitchLimits'])
        pitchLimitsMin = pitchLimits[0]
        pitchLimitsMax = pitchLimits[1]
        gunPitch = mathUtils.clamp(pitchLimitsMin, pitchLimitsMax, gunPitch)
        return (turretYaw, gunPitch)

    def __worldYawPitchToTurret(self, worldYaw, worldPitch):
        worldToTurret = Matrix(self.__vehicleMProv)
        worldToTurret.invert()
        worldToTurret.preMultiply(mathUtils.createRotationMatrix((worldYaw, worldPitch, 0)))
        return (worldToTurret.yaw, worldToTurret.pitch)

    def update(self, deltaTime):
        if not SniperAimingSystem.USE_DAMPING:
            self.__oscillator.reset()
            currentGunMat = AimingSystems.getPlayerGunMat(self.__idealTurretYaw, self.__idealGunPitch)
            self.__worldYaw = currentGunMat.yaw
            self.__worldPitch = currentGunMat.pitch
            self._matrix.set(currentGunMat)
            return
        vehicleMat = Matrix(self.__vehicleMProv)
        curTurretYaw, curGunPitch = self.__worldYawPitchToTurret(self.__worldYaw, self.__worldPitch)
        yprDelta = Vector3(curTurretYaw - self.__idealTurretYaw, curGunPitch - self.__idealGunPitch, 0)
        self.__oscillator.deviation = yprDelta
        self.__oscillator.update(deltaTime)
        curTurretYaw = self.__idealTurretYaw + self.__oscillator.deviation.x
        curGunPitch = self.__idealGunPitch + self.__oscillator.deviation.y
        curTurretYaw, curGunPitch = self.__clampToLimits(curTurretYaw, curGunPitch)
        yprDelta = Vector3(curTurretYaw - self.__idealTurretYaw, curGunPitch - self.__idealGunPitch, 0)
        self.__oscillator.deviation = yprDelta
        currentGunMat = AimingSystems.getPlayerGunMat(curTurretYaw, curGunPitch)
        self.__worldYaw = currentGunMat.yaw
        self.__worldPitch = currentGunMat.pitch
        self._matrix.set(currentGunMat)
        self.__vehiclePrevMat = vehicleMat
        return 0.0

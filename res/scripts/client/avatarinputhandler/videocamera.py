import Math
from Math import Vector3, Matrix
import BigWorld
from AvatarInputHandler.CallbackDelayer import CallbackDelayer
from AvatarInputHandler.aims import createAim
import GUI
import Keys
import functools
import math
from ProjectileMover import collideDynamicAndStatic
import constants
import BattleReplay
from gui.BattleContext import g_battleContext

class KeySensor:

    def __init__(self, keyMappings, sensitivity, sensitivityIncDecKeys = None, sensitivityAcceleration = None):
        self.keyMappings = keyMappings
        self.sensitivity = sensitivity
        self.__sensitivityKeys = {}
        if sensitivityIncDecKeys is not None:
            self.__sensitivityKeys[sensitivityIncDecKeys[0]] = sensitivityAcceleration
            self.__sensitivityKeys[sensitivityIncDecKeys[1]] = -sensitivityAcceleration
        self.currentVelocity = None
        self.__currentKeys = set()
        return

    def addVelocity(self, velocity):
        if self.currentVelocity is None:
            self.currentVelocity = velocity
        else:
            self.currentVelocity += velocity
        return

    def reset(self, defaultVelocity):
        self.__currentKeys.clear()
        self.currentVelocity = defaultVelocity

    def handleKeyEvent(self, key, isDown):
        for senseKey, acceleration in self.__sensitivityKeys.iteritems():
            if senseKey == key:
                if isDown:
                    self.__currentKeys.add(key)
                else:
                    self.__currentKeys.discard(key)
                return True

        for mappingKey, shift in self.keyMappings.iteritems():
            if mappingKey == key:
                if isDown:
                    self.__currentKeys.add(key)
                else:
                    self.__currentKeys.discard(key)
                return True

        return False

    def update(self, delta):
        for senseKey, acceleration in self.__sensitivityKeys.iteritems():
            if senseKey in self.__currentKeys:
                self.sensitivity += acceleration * delta

        for mappingKey, shift in self.keyMappings.iteritems():
            if mappingKey in self.__currentKeys:
                addValue = shift * self.sensitivity
                if self.currentVelocity is None:
                    self.currentVelocity = addValue * self.sensitivity
                else:
                    self.currentVelocity += addValue * self.sensitivity

        return


class _Inertia:

    def __init__(self, frictionCoeff):
        self.frictionCoeff = frictionCoeff

    def integrate(self, thrust, velocity, delta):
        acc = thrust - self.frictionCoeff * velocity
        if acc.x * thrust.x < 0:
            acc.x = 0.0
        if acc.y * thrust.y < 0:
            acc.y = 0.0
        if acc.z * thrust.z < 0:
            acc.z = 0.0
        return velocity + acc * delta


class _AlignerToLand:
    MIN_HEIGHT = 0.5
    enabled = property(lambda self: self.__desiredHeightShift is not None)

    def __init__(self):
        self.__desiredHeightShift = None
        return

    def enable(self, position):
        landPosition = self.__getLandAt(position)
        if landPosition is not None:
            self.__desiredHeightShift = position - landPosition
            if self.__desiredHeightShift.y < _AlignerToLand.MIN_HEIGHT:
                self.__desiredHeightShift.y = _AlignerToLand.MIN_HEIGHT
        else:
            self.__desiredHeightShift = None
        return

    def disable(self):
        self.__desiredHeightShift = None
        return

    def __getLandAt(self, position):
        upPoint = Math.Vector3(position)
        upPoint.y += 1000
        downPoint = Math.Vector3(position)
        downPoint.y = -1000
        collideRes = BigWorld.wg_collideSegment(BigWorld.player().spaceID, upPoint, downPoint, 16, self.__isTerrain)
        if collideRes is None:
            return
        else:
            return collideRes[0]

    def __isTerrain(self, matKind, collFlags, itemId, chunkId):
        return collFlags & 8

    def getAlignedPosition(self, position):
        if self.__desiredHeightShift is None:
            return position
        else:
            landPos = self.__getLandAt(position)
            if landPos is None:
                return position
            return landPos + self.__desiredHeightShift


class VideoCamera(CallbackDelayer):

    def __init__(self, configDataSec):
        CallbackDelayer.__init__(self)
        self.__cam = BigWorld.FreeCamera()
        self.__ypr = Math.Vector3()
        self.__position = Math.Vector3()
        self.__defaultFov = BigWorld.projection().fov
        self.__velocity = Math.Vector3()
        self.__isVerticalVelocitySeparated = False
        self.__yprVelocity = Math.Vector3()
        self.__zoomVelocity = 0.0
        self.__inertiaEnabled = False
        self.__movementInertia = None
        self.__rotationInertia = None
        self.__movementSensor = None
        self.__verticalMovementSensor = None
        self.__rotationSensor = None
        self.__zoomSensor = None
        self.__targetRadiusSensor = None
        self.__mouseSensitivity = 0.0
        self.__scrollSensitivity = 0.0
        self.__prevTime = 0.0
        self.__rotateAroundPointEnabled = False
        self.__rotationRadius = 40.0
        self.__boundVehicleMProv = None
        self.__alignerToLand = _AlignerToLand()
        self.__predefinedVelocities = {}
        self.__predefinedVerticalVelocities = {}
        self.__keySwitches = {}
        self.__readCfg(configDataSec)
        self.__aim = None
        return

    def create(self):
        pass

    def destroy(self):
        CallbackDelayer.destroy(self)
        self.__cam = None
        if self.__aim is not None:
            self.__aim.destroy()
            self.__aim = None
        return

    def enable(self, **args):
        self.__prevTime = BigWorld.time()
        self.delayCallback(0.0, self.__update)
        camMatrix = args.get('camMatrix')
        self.__cam.set(camMatrix)
        BigWorld.camera(self.__cam)
        worldMat = Math.Matrix(self.__cam.invViewMatrix)
        self.__ypr = Math.Vector3(worldMat.yaw, worldMat.pitch, worldMat.roll)
        self.__position = worldMat.translation
        self.__velocity = Math.Vector3()
        self.__yprVelocity = Math.Vector3()
        self.__zoomVelocity = 0.0
        self.__movementSensor.reset(Math.Vector3())
        self.__verticalMovementSensor.reset(0.0)
        self.__rotationSensor.reset(Math.Vector3())
        self.__zoomSensor.reset(0.0)
        self.__targetRadiusSensor.reset(0.0)
        if g_battleContext.isPlayerObserver():
            BigWorld.player().positionControl.moveTo(self.__position)
            BigWorld.player().positionControl.followCamera(True)

    def disable(self):
        self.stopCallback(self.__update)
        BigWorld.projection().fov = self.__defaultFov
        BigWorld.camera(None)
        self.__alignerToLand.disable()
        BigWorld.player().positionControl.followCamera(False)
        return

    def handleKeyEvent(self, key, isDown):
        if key is None:
            return False
        else:
            if isDown:
                if self.__keySwitches['keySwitchInertia'] == key:
                    self.__inertiaEnabled = not self.__inertiaEnabled
                    return True
                if self.__keySwitches['keySwitchRotateAroundPoint'] == key:
                    self.__rotateAroundPointEnabled = not self.__rotateAroundPointEnabled
                    self.__boundVehicleMProv = None
                    return True
                if self.__keySwitches['keySwitchLandCamera'] == key:
                    if self.__alignerToLand.enabled:
                        self.__alignerToLand.disable()
                    else:
                        self.__alignerToLand.enable(self.__position)
                    return True
                if self.__keySwitches['keySetDefaultFov'] == key:
                    BigWorld.projection().fov = self.__defaultFov
                    return True
                if self.__keySwitches['keySetDefaultRoll'] == key:
                    self.__ypr.z = 0.0
                    return True
                if self.__keySwitches['keyRevertVerticalVelocity'] == key:
                    self.__isVerticalVelocitySeparated = False
                    return True
                if self.__keySwitches['keyBindToVehicle'] == key:
                    if BigWorld.isKeyDown(Keys.KEY_LSHIFT) or BigWorld.isKeyDown(Keys.KEY_RSHIFT):
                        self.__showAim(True if self.__aim is None else not self.__aim.isActive)
                    else:
                        self.__boundVehicleMProv = self.__pickVehicle()
                        self.__rotateAroundPointEnabled = False
                    return True
                if BigWorld.isKeyDown(Keys.KEY_LSHIFT) or BigWorld.isKeyDown(Keys.KEY_RSHIFT):
                    if self.__verticalMovementSensor.handleKeyEvent(key, isDown) and key not in self.__verticalMovementSensor.keyMappings:
                        self.__isVerticalVelocitySeparated = True
                        return True
                    for velocityKey, velocity in self.__predefinedVerticalVelocities.iteritems():
                        if velocityKey == key:
                            self.__verticalMovementSensor.sensitivity = velocity
                            self.__isVerticalVelocitySeparated = True
                            return True

                for velocityKey, velocity in self.__predefinedVelocities.iteritems():
                    if velocityKey == key:
                        self.__movementSensor.sensitivity = velocity
                        return True

            if key in self.__verticalMovementSensor.keyMappings:
                self.__verticalMovementSensor.handleKeyEvent(key, isDown)
            return self.__movementSensor.handleKeyEvent(key, isDown) or self.__rotationSensor.handleKeyEvent(key, isDown) or self.__zoomSensor.handleKeyEvent(key, isDown) or self.__targetRadiusSensor.handleKeyEvent(key, isDown)

    def handleMouseEvent(self, dx, dy, dz):
        self.__rotationSensor.addVelocity(Math.Vector3(dx, dy, 0) * self.__mouseSensitivity)
        movementShift = Vector3(0, dz * self.__movementSensor.sensitivity * self.__scrollSensitivity, 0)
        self.__movementSensor.addVelocity(movementShift)
        GUI.mcursor().position = Math.Vector2(0, 0)

    def __calcCurrentDelta(self):
        curTime = BigWorld.time()
        delta = curTime - self.__prevTime
        self.__prevTime = curTime
        replaySpeed = BattleReplay.g_replayCtrl.playbackSpeed
        if replaySpeed == 0:
            replaySpeed = 1e-08
        delta = delta / replaySpeed
        if delta > 1.0:
            delta = 0.0
        return delta

    def __getMovementDirections(self):
        m = Math.Matrix(self.__cam.invViewMatrix)
        result = (m.applyVector(Vector3(1, 0, 0)), Vector3(0, 1, 0), m.applyVector(Vector3(0, 0, 1)))
        if self.__alignerToLand.enabled:
            result[0].y = 0.0
            result[2].y = 0.0
        return result

    def __update(self):
        prevPos = Math.Vector3(self.__position)
        delta = self.__calcCurrentDelta()
        self.__movementSensor.update(delta)
        self.__rotationSensor.update(delta)
        self.__zoomSensor.update(delta)
        self.__targetRadiusSensor.update(delta)
        self.__rotationRadius += self.__targetRadiusSensor.currentVelocity * delta
        if self.__isVerticalVelocitySeparated:
            self.__verticalMovementSensor.update(delta)
        else:
            self.__verticalMovementSensor.currentVelocity = self.__movementSensor.currentVelocity.y
            self.__verticalMovementSensor.sensitivity = self.__movementSensor.sensitivity
        if self.__inertiaEnabled:
            self.__inertialMovement(delta)
        else:
            self.__simpleMovement(delta)
        self.__ypr += self.__yprVelocity * delta
        self.__position += self.__velocity * delta
        if self.__alignerToLand.enabled and abs(self.__velocity.y) > 0.1:
            self.__alignerToLand.enable(self.__position)
        self.__position = self.__alignerToLand.getAlignedPosition(self.__position)
        if self.__boundVehicleMProv is not None:
            self.__ypr = self.__getLookAtYPR(Matrix(self.__boundVehicleMProv).translation)
        self.__ypr[0] = math.fmod(self.__ypr[0], 2 * math.pi)
        self.__ypr[1] = max(-0.9 * math.pi / 2, min(0.9 * math.pi / 2, self.__ypr[1]))
        self.__ypr[2] = math.fmod(self.__ypr[2], 2 * math.pi)
        camMat = Math.Matrix()
        camMat.setRotateYPR(self.__ypr)
        if self.__rotateAroundPointEnabled:
            self.__position = self.__getAlignedToPointPosition(camMat)
        moveDir = self.__position - prevPos
        moveDir.normalise()
        collisionPointWithBorders = BigWorld.player().arena.collideWithSpaceBB(prevPos - moveDir, self.__position + moveDir)
        if collisionPointWithBorders is not None:
            self.__position = collisionPointWithBorders
        camMat.translation = self.__position
        camMat.invert()
        self.__cam.set(camMat)
        fov = BigWorld.projection().fov + self.__zoomSensor.currentVelocity
        if fov <= 0.1:
            fov = 0.1
        if fov >= math.pi - 0.1:
            fov = math.pi - 0.1
        BigWorld.projection().fov = fov
        self.__movementSensor.currentVelocity = Math.Vector3()
        self.__verticalMovementSensor.currentVelocity = 0.0
        self.__rotationSensor.currentVelocity = Math.Vector3()
        self.__zoomSensor.currentVelocity = 0.0
        self.__targetRadiusSensor.currentVelocity = 0.0
        return 0.0

    def __simpleMovement(self, delta):
        self.__yprVelocity = self.__rotationSensor.currentVelocity
        shift = self.__movementSensor.currentVelocity
        shift.y = self.__verticalMovementSensor.currentVelocity
        moveDirs = self.__getMovementDirections()
        self.__velocity = moveDirs[0] * shift.x + moveDirs[1] * shift.y + moveDirs[2] * shift.z

    def __inertialMovement(self, delta):
        self.__yprVelocity = self.__rotationInertia.integrate(self.__rotationSensor.currentVelocity, self.__yprVelocity, delta)
        thrust = self.__movementSensor.currentVelocity
        thrust.y = self.__verticalMovementSensor.currentVelocity
        moveDirs = self.__getMovementDirections()
        thrust = moveDirs[0] * thrust.x + moveDirs[1] * thrust.y + moveDirs[2] * thrust.z
        self.__velocity = self.__movementInertia.integrate(thrust, self.__velocity, delta)

    def __getAlignedToPointPosition(self, rotationMat):
        dirVector = Math.Vector3(0, 0, self.__rotationRadius)
        camMat = Math.Matrix(self.__cam.invViewMatrix)
        point = camMat.applyPoint(dirVector)
        return point + rotationMat.applyVector(-dirVector)

    def __readCfg(self, configDataSec):
        movementMappings = dict()
        movementMappings[getattr(Keys, configDataSec.readString('keyMoveLeft', 'KEY_A'))] = Vector3(-1, 0, 0)
        movementMappings[getattr(Keys, configDataSec.readString('keyMoveRight', 'KEY_D'))] = Vector3(1, 0, 0)
        keyMoveUp = getattr(Keys, configDataSec.readString('keyMoveUp', 'KEY_PGUP'))
        keyMoveDown = getattr(Keys, configDataSec.readString('keyMoveDown', 'KEY_PGDN'))
        movementMappings[keyMoveUp] = Vector3(0, 1, 0)
        movementMappings[keyMoveDown] = Vector3(0, -1, 0)
        movementMappings[getattr(Keys, configDataSec.readString('keyMoveForward', 'KEY_W'))] = Vector3(0, 0, 1)
        movementMappings[getattr(Keys, configDataSec.readString('keyMoveBackward', 'KEY_S'))] = Vector3(0, 0, -1)
        linearSensitivity = configDataSec.readFloat('linearVelocity', 40.0)
        linearSensitivityAcc = configDataSec.readFloat('linearVelocityAcceleration', 30.0)
        linearIncDecKeys = (getattr(Keys, configDataSec.readString('keyLinearVelocityIncrement', 'KEY_I')), getattr(Keys, configDataSec.readString('keyLinearVelocityDecrement', 'KEY_K')))
        self.__movementSensor = KeySensor(movementMappings, linearSensitivity, linearIncDecKeys, linearSensitivityAcc)
        self.__verticalMovementSensor = KeySensor({keyMoveUp: 1,
         keyMoveDown: -1}, linearSensitivity, linearIncDecKeys, linearSensitivityAcc)
        self.__movementSensor.currentVelocity = Math.Vector3()
        self.__keySwitches['keyRevertVerticalVelocity'] = getattr(Keys, configDataSec.readString('keyRevertVerticalVelocity', 'KEY_Z'))
        self.__mouseSensitivity = configDataSec.readFloat('sensitivity', 1.0)
        self.__scrollSensitivity = configDataSec.readFloat('scrollSensitivity', 1.0)
        rotationMappings = dict()
        rotationMappings[getattr(Keys, configDataSec.readString('keyRotateLeft', 'KEY_LEFTARROW'))] = Vector3(-1, 0, 0)
        rotationMappings[getattr(Keys, configDataSec.readString('keyRotateRight', 'KEY_RIGHTARROW'))] = Vector3(1, 0, 0)
        rotationMappings[getattr(Keys, configDataSec.readString('keyRotateUp', 'KEY_UPARROW'))] = Vector3(0, -1, 0)
        rotationMappings[getattr(Keys, configDataSec.readString('keyRotateDown', 'KEY_DOWNARROW'))] = Vector3(0, 1, 0)
        rotationMappings[getattr(Keys, configDataSec.readString('keyRotateClockwise', 'KEY_HOME'))] = Vector3(0, 0, -1)
        rotationMappings[getattr(Keys, configDataSec.readString('keyRotateCClockwise', 'KEY_END'))] = Vector3(0, 0, 1)
        rotationSensitivity = configDataSec.readFloat('angularVelocity', 0.7)
        rotationSensitivityAcc = configDataSec.readFloat('angularVelocityAcceleration', 0.8)
        rotationIncDecKeys = (getattr(Keys, configDataSec.readString('keyAngularVelocityIncrement', 'KEY_O')), getattr(Keys, configDataSec.readString('keyAngularVelocityDecrement', 'KEY_L')))
        self.__rotationSensor = KeySensor(rotationMappings, rotationSensitivity, rotationIncDecKeys, rotationSensitivityAcc)
        self.__rotationSensor.currentVelocity = Math.Vector3()
        self.__keySwitches['keySetDefaultRoll'] = getattr(Keys, configDataSec.readString('keySetDefaultRoll', 'KEY_R'))
        zoomMappings = dict()
        zoomMappings[getattr(Keys, configDataSec.readString('keyZoomGrowUp', 'KEY_INSERT'))] = -1
        zoomMappings[getattr(Keys, configDataSec.readString('keyZoomGrowDown', 'KEY_DELETE'))] = 1
        zoomSensitivity = configDataSec.readFloat('zoomVelocity', 2.0)
        zoomSensitivityAcc = configDataSec.readFloat('zoomVelocityAcceleration', 1.5)
        zoomIncDecKeys = (getattr(Keys, configDataSec.readString('keyZoomVelocityIncrement', 'KEY_NUMPADMINUS')), getattr(Keys, configDataSec.readString('keyZoomVelocityDecrement', 'KEY_ADD')))
        self.__zoomSensor = KeySensor(zoomMappings, zoomSensitivity, zoomIncDecKeys, zoomSensitivityAcc)
        self.__zoomSensor.currentVelocity = 0.0
        self.__keySwitches['keySwitchInertia'] = getattr(Keys, configDataSec.readString('keySwitchInertia', 'KEY_P'))
        self.__movementInertia = _Inertia(configDataSec.readFloat('linearFriction', 0.1))
        self.__rotationInertia = _Inertia(configDataSec.readFloat('rotationFriction', 0.1))
        self.__keySwitches['keySwitchRotateAroundPoint'] = getattr(Keys, configDataSec.readString('keySwitchRotateAroundPoint', 'KEY_B'))
        aroundPointMappings = dict()
        aroundPointMappings[getattr(Keys, configDataSec.readString('keyTargetRadiusIncrement', 'KEY_NUMPAD7'))] = 1
        aroundPointMappings[getattr(Keys, configDataSec.readString('keyTargetRadiusDecrement', 'KEY_NUMPAD1'))] = -1
        aroundPointRadiusVelocity = configDataSec.readFloat('targetRadiusVelocity', 3.0)
        self.__targetRadiusSensor = KeySensor(aroundPointMappings, aroundPointRadiusVelocity)
        self.__targetRadiusSensor.currentVelocity = 0.0
        self.__keySwitches['keySwitchLandCamera'] = getattr(Keys, configDataSec.readString('keySwitchLandCamera', 'KEY_L'))
        self.__keySwitches['keySetDefaultFov'] = getattr(Keys, configDataSec.readString('keySetDefaultFov', 'KEY_F'))
        self.__keySwitches['keyBindToVehicle'] = getattr(Keys, configDataSec.readString('keyBindToVehicle', ''), None)
        predefVelocitySec = configDataSec['predefinedVelocities']
        if predefVelocitySec is not None:
            for v in predefVelocitySec.items():
                key = getattr(Keys, v[0], None)
                if key is not None:
                    self.__predefinedVelocities[key] = v[1].asFloat

        predefVelocitySec = configDataSec['predefinedVerticalVelocities']
        if predefVelocitySec is not None:
            for v in predefVelocitySec.items():
                key = getattr(Keys, v[0], None)
                if key is not None:
                    self.__predefinedVerticalVelocities[key] = v[1].asFloat

        return

    def __pickVehicle(self):
        if self.__boundVehicleMProv is not None:
            return
        else:
            x, y = GUI.mcursor().position
            from AvatarInputHandler import cameras
            dir, start = cameras.getWorldRayAndPoint(x, y)
            end = start + dir.scale(100000.0)
            pos, colldata = collideDynamicAndStatic(start, end, (), 0)
            vehicle = None
            if colldata is not None:
                entity = colldata[0]
                from Vehicle import Vehicle
                if isinstance(entity, Vehicle):
                    vehMatProv = entity.matrix
                    vehMatInv = Matrix(vehMatProv)
                    vehMatInv.invert()
                    localPos = vehMatInv.applyPoint(pos)
                    result = Math.MatrixProduct()
                    localTransMat = Matrix()
                    localTransMat.translation = localPos
                    result.a = localTransMat
                    result.b = vehMatProv
                    return result
            return

    def __getLookAtYPR(self, lookAtPosition):
        lookDir = lookAtPosition - self.__position
        camMat = Matrix()
        camMat.lookAt(self.__position, lookDir, Vector3(0, 1, 0))
        camMat.invert()
        yaw = camMat.yaw
        pitch = camMat.pitch
        return Vector3(yaw, pitch, self.__ypr.z)

    def __showAim(self, show):
        if self.__aim is None:
            self.__aim = createAim('postmortem')
            self.__aim.create()
        if show:
            self.__aim.enable()
        else:
            self.__aim.disable()
        return

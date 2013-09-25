# Embedded file name: scripts/client/AvatarInputHandler/control_modes.py
import BigWorld, Math, Keys, GUI, ResMgr
import math
import stat
import weakref
import string
from AvatarInputHandler import mathUtils, AimingSystems
import cameras
import aims
import CommandMapping
import constants
import BattleReplay
import TriggersManager
from TriggersManager import TRIGGER_TYPE
from post_processing import g_postProcessing
from constants import AIMING_MODE
from gui import DEPTH_OF_GunMarker
from gui.Scaleform.Flash import Flash
from debug_utils import *
from ProjectileMover import collideDynamicAndStatic, collideDynamic
from PlayerEvents import g_playerEvents
from PostmortemDelay import PostmortemDelay
from account_helpers.AccountSettings import AccountSettings
import gun_rotation_shared
import VideoCamera
from gui.BattleContext import g_battleContext
from DynamicCameras import SniperCamera, StrategicCamera, ArcadeCamera
_ARCADE_CAM_PIVOT_POS = Math.Vector3(0, 4, 3)

class IControlMode():

    def prerequisites(self):
        return []

    def create(self):
        pass

    def destroy(self):
        pass

    def dumpState(self):
        pass

    def enable(self, **args):
        pass

    def disable(self):
        pass

    def handleKeyEvent(self, isDown, key, mods, event = None):
        pass

    def handleMouseEvent(self, dx, dy, dz):
        pass

    def showGunMarker(self, flag):
        pass

    def showGunMarker2(self, flag):
        pass

    def updateGunMarker(self, pos, dir, size, relaxTime, collData):
        pass

    def updateGunMarker2(self, pos, dir, size, relaxTime, collData):
        pass

    def setAimingMode(self, enable, mode):
        pass

    def getAimingMode(self, mode):
        pass

    def getDesiredShotPoint(self):
        pass

    def updateShootingStatus(self, canShoot):
        pass

    def updateTrajectory(self):
        pass

    def onRecreateDevice(self):
        pass

    def getAim(self):
        return None

    def setReloading(self, duration, startTime):
        pass

    def setGUIVisible(self, isVisible):
        pass

    def selectPlayer(self, index):
        pass

    def onMinimapClicked(self, worldPos):
        pass

    def isSelfVehicle(self):
        return True

    def isManualBind(self):
        return False

    def getPreferredAutorotationMode(self):
        return None

    def enableSwitchAutorotationMode(self):
        return True


class VideoCameraControlMode(IControlMode):
    curVehicleID = property(lambda self: self.__curVehicleID)

    def __init__(self, dataSection, avatarInputHandler):
        self.__aih = weakref.proxy(avatarInputHandler)
        self.__enabled = False
        self.__prevModeName = None
        cameraDataSection = dataSection['camera'] if dataSection is not None else ResMgr.DataSection('camera')
        self.__videoCamera = VideoCamera.VideoCamera(cameraDataSection)
        self.__curVehicleID = None
        return

    def create(self):
        pass

    def destroy(self):
        pass

    def enable(self, **args):
        self.__enabled = True
        self.__prevModeName = args.get('prevModeName')
        self.__videoCamera.enable(**args)
        self.__curVehicleID = args.get('curVehicleID')
        if self.__curVehicleID is None:
            self.__curVehicleID = BigWorld.player().playerVehicleID
        return

    def disable(self):
        self.__enabled = False
        self.__videoCamera.disable()

    def handleKeyEvent(self, isDown, key, mods, event = None):
        if self.__videoCamera.handleKeyEvent(key, isDown):
            return True
        elif BigWorld.isKeyDown(Keys.KEY_CAPSLOCK) and isDown and key == Keys.KEY_F3 and self.__prevModeName is not None:
            self.__aih.onControlModeChanged(self.__prevModeName)
            return True
        else:
            return False

    def handleMouseEvent(self, dx, dy, dz):
        self.__videoCamera.handleMouseEvent(dx, dy, dz)
        return True

    def setGUIVisible(self, isVisible):
        pass

    def dumpState(self):
        return dumpStateEmpty()

    def onPostmortemActivation(self):
        self.__prevModeName = 'postmortem'


class DebugControlMode(IControlMode):

    def __init__(self, dataSection, avatarInputHandler):
        self.__aih = weakref.proxy(avatarInputHandler)
        self.__cam = cameras.FreeCamera()
        self.__isCreated = False
        self.__isEnabled = False
        self.__prevModeName = None
        self.__videoControl = None
        return

    def prerequisites(self):
        return []

    def create(self):
        self.__isCreated = True

    def destroy(self):
        self.disable()
        self.__cam.destroy()
        self.__cam = None
        self.__isCreated = False
        return

    def dumpState(self):
        return dumpStateEmpty()

    def enable(self, **args):
        ctrlState = args.get('ctrlState')
        self.__prevModeName = args.get('prevModeName')
        camMatrix = args.get('camMatrix')
        self.__cam.enable(camMatrix)
        BigWorld.setWatcher('Client Settings/Strafe Rate', 50)
        BigWorld.setWatcher('Client Settings/Camera Mass', 1)
        raise constants.IS_DEVELOPMENT or AssertionError
        import Cat
        Cat.Tasks.VideoEngineer.SetEnable(True)
        self.__videoControl = Cat.Tasks.VideoEngineer.VideoControl(self.__cam)
        self.__videoControl.setEnable(True)
        self.__isEnabled = True
        g_postProcessing.enable('debug')

    def disable(self):
        self.__isEnabled = False
        if self.__videoControl is not None:
            self.__videoControl.setEnable(False)
            self.__videoControl.destroy()
            self.__videoControl = None
        self.__cam.disable()
        g_postProcessing.disable()
        return

    def handleKeyEvent(self, isDown, key, mods, event = None):
        if not self.__isEnabled:
            raise AssertionError
            if key == Keys.KEY_SYSRQ:
                return False
            if BigWorld.isKeyDown(Keys.KEY_CAPSLOCK) and constants.IS_DEVELOPMENT and isDown and key == Keys.KEY_F1:
                self.__aih.onControlModeChanged(self.__prevModeName)
                return True
            return self.__videoControl.handleKeyEvent(isDown, key, mods, event) and True
        return self.__cam.handleKey(event)

    def handleMouseEvent(self, dx, dy, dz):
        raise self.__isEnabled or AssertionError
        GUI.mcursor().position = (0, 0)
        return self.__videoControl.handleMouseEvent(dx, dy, dz)

    def getDesiredShotPoint(self):
        raise self.__isEnabled or AssertionError
        return None

    def updateShootingStatus(self, canShot):
        raise self.__isEnabled or AssertionError
        return None

    def setCameraPosition(self, x, y, z):
        mat = Math.Matrix()
        mat.lookAt(Math.Vector3(x, y, z), (0, 0, 1), (0, 1, 0))
        self.__cam.camera.set(mat)

    def getDebugVideoControl(self):
        return self.__videoControl

    def isManualBind(self):
        return True


class CatControlMode(IControlMode):

    def __init__(self, dataSection, avatarInputHandler):
        self.__aih = weakref.proxy(avatarInputHandler)
        self.__cam = cameras.FreeCamera()
        self.__isCreated = False
        self.__isEnabled = False
        self.__shellingControl = None
        self.__sens = (3.0, 3.0, 3.0)
        return

    def prerequisites(self):
        return []

    def create(self):
        self.__shellingControl = _ShellingControl(self.__cam)
        self.__isCreated = True

    def destroy(self):
        self.disable()
        self.__shellingControl.destroy()
        self.__shellingControl = None
        self.__cam.destroy()
        self.__cam = None
        self.__isCreated = False
        return

    def dumpState(self):
        return dumpStateEmpty()

    def enable(self, **args):
        ctrlState = args.get('ctrlState')
        camMatrix = args.get('camMatrix')
        self.__cam.enable(camMatrix)
        BigWorld.setWatcher('Client Settings/Strafe Rate', 50)
        BigWorld.setWatcher('Client Settings/Camera Mass', 1)
        self.__shellingControl.setEnable(True)
        self.__isEnabled = True

    def disable(self):
        self.__shellingControl.setEnable(False)
        self.__cam.disable()
        self.__isEnabled = False

    def handleKeyEvent(self, isDown, key, mods, event = None):
        if not self.__isEnabled:
            raise AssertionError
            BigWorld.isKeyDown(Keys.KEY_CAPSLOCK) and constants.IS_DEVELOPMENT and isDown and key == Keys.KEY_F2 and self.__aih.onControlModeChanged('arcade')
        self.__shellingControl.handleKeyEvent(isDown, key, mods, event)
        return self.__cam.handleKey(event)

    def handleMouseEvent(self, dx, dy, dz):
        raise self.__isEnabled or AssertionError
        GUI.mcursor().position = (0, 0)
        return self.__cam.handleMouse(int(self.__sens[0] * dx), int(self.__sens[1] * dy), int(self.__sens[2] * dz))

    def onRecreateDevice(self):
        self.__shellingControl.recreate()

    def getEnabled(self):
        return bool(self.__isEnabled)

    def setCameraPosition(self, x, y, z):
        mat = Math.Matrix()
        mat.lookAt(Math.Vector3(x, y, z), (0, 0, 1), (0, 1, 0))
        self.__cam.camera.set(mat)

    def getCameraPosition(self):
        return tuple(self.__cam.camera.position)

    def setSensitivity(self, sens):
        self.__sens = tuple(sens)

    def getShellingControl(self):
        return self.__shellingControl

    def isManualBind(self):
        return True


class ArcadeControlMode(IControlMode):
    postmortemCamParams = property(lambda self: (self.__cam.angles, self.__cam.camera.pivotMaxDist))
    camera = property(lambda self: self.__cam)

    def __init__(self, dataSection, avatarInputHandler):
        self.__aih = weakref.proxy(avatarInputHandler)
        self.__gunMarker = _SuperGunMarker(mode='arcade')
        self.__aim = aims.createAim(dataSection.readString('aim'))
        self.__cam = ArcadeCamera.ArcadeCamera(dataSection['camera'], self.__aim)
        self.__mouseVehicleRotator = _MouseVehicleRotator()
        self.__aimingMode = 0
        self.__canShot = False
        self.__isEnabled = False
        self.__isArenaStarted = False
        self.__sightOffset = list(self.__aim.offset())
        self.__videoControlModeAvailable = dataSection.readBool('videoModeAvailable', False)

    def prerequisites(self):
        out = []
        out += self.__gunMarker.prerequisites()
        out += self.__aim.prerequisites()
        return out

    def create(self):
        self.__aim.create()
        self.__gunMarker.create()
        self.__cam.create(_ARCADE_CAM_PIVOT_POS, self.onChangeControlModeByScroll)
        self.disable()

    def destroy(self):
        self.disable()
        self.__aim.destroy()
        self.__gunMarker.destroy()
        self.__cam.destroy()
        self.__mouseVehicleRotator.destroy()
        self.__aih = None
        self.__mouseVehicleRotator = None
        return

    def dumpState(self):
        return {'gunMarker': self.__gunMarker.dumpState()}

    def enable(self, **args):
        ctrlState = args.get('ctrlState')
        self.__aimingMode = args.get('aimingMode', self.__aimingMode)
        self.__gunMarker.enable(ctrlState.get('gunMarker'))
        self.__aim.enable()
        self.__cam.enable(args.get('preferredPos'), args.get('closesDist', False), turretYaw=args.get('turretYaw', 0.0), gunPitch=args.get('gunPitch', 0.0))
        self.__isEnabled = True
        arena = BigWorld.player().arena
        if arena is not None:
            arena.onPeriodChange += self.__onArenaStarted
            self.__onArenaStarted(arena.period)
        g_postProcessing.enable('arcade')
        return

    def disable(self):
        self.__isEnabled = False
        self.__cam.disable()
        self.__gunMarker.disable()
        self.__aim.disable()
        arena = BigWorld.player().arena
        if arena is not None:
            arena.onPeriodChange -= self.__onArenaStarted
        g_postProcessing.disable()
        return

    def handleKeyEvent(self, isDown, key, mods, event = None):
        if not self.__isEnabled:
            raise AssertionError
            cmdMap = CommandMapping.g_instance
            return self.__cam.handleKeyEvent(isDown, key, mods, event) and True
        elif BigWorld.isKeyDown(Keys.KEY_CAPSLOCK) and constants.IS_DEVELOPMENT and isDown and key == Keys.KEY_F1:
            self.__aih.onControlModeChanged('debug', prevModeName='arcade', camMatrix=self.__cam.camera.matrix)
            return True
        elif BigWorld.isKeyDown(Keys.KEY_CAPSLOCK) and constants.IS_DEVELOPMENT and isDown and key == Keys.KEY_F2:
            self.__aih.onControlModeChanged('cat', camMatrix=self.__cam.camera.matrix)
            return True
        elif BigWorld.isKeyDown(Keys.KEY_CAPSLOCK) and isDown and key == Keys.KEY_F3 and BattleReplay.g_replayCtrl.isPlaying and self.__videoControlModeAvailable:
            self.__aih.onControlModeChanged('video', prevModeName='arcade', camMatrix=self.__cam.camera.matrix)
            return True
        isFiredFreeCamera = cmdMap.isFired(CommandMapping.CMD_CM_FREE_CAMERA, key)
        if cmdMap.isFired(CommandMapping.CMD_CM_LOCK_TARGET, key):
            isFiredLockTarget = isDown
            if isFiredFreeCamera or isFiredLockTarget:
                if isFiredFreeCamera:
                    self.setAimingMode(isDown, AIMING_MODE.USER_DISABLED)
                if isFiredLockTarget:
                    BigWorld.player().autoAim(BigWorld.target())
            if cmdMap.isFired(CommandMapping.CMD_CM_SHOOT, key) and isDown:
                BigWorld.player().shoot()
                return True
            if cmdMap.isFired(CommandMapping.CMD_CM_LOCK_TARGET_OFF, key) and isDown:
                BigWorld.player().autoAim(None)
                return True
            if cmdMap.isFired(CommandMapping.CMD_CM_VEHICLE_SWITCH_AUTOROTATION, key) and isDown:
                self.__aih.switchAutorotation()
                return True
            if cmdMap.isFiredList((CommandMapping.CMD_CM_CAMERA_ROTATE_LEFT,
             CommandMapping.CMD_CM_CAMERA_ROTATE_RIGHT,
             CommandMapping.CMD_CM_CAMERA_ROTATE_UP,
             CommandMapping.CMD_CM_CAMERA_ROTATE_DOWN,
             CommandMapping.CMD_CM_INCREASE_ZOOM,
             CommandMapping.CMD_CM_DECREASE_ZOOM), key):
                dx = dy = dz = 0.0
                if cmdMap.isActive(CommandMapping.CMD_CM_CAMERA_ROTATE_LEFT):
                    dx = -1.0
                if cmdMap.isActive(CommandMapping.CMD_CM_CAMERA_ROTATE_RIGHT):
                    dx = 1.0
                if cmdMap.isActive(CommandMapping.CMD_CM_CAMERA_ROTATE_UP):
                    dy = -1.0
                if cmdMap.isActive(CommandMapping.CMD_CM_CAMERA_ROTATE_DOWN):
                    dy = 1.0
                if cmdMap.isActive(CommandMapping.CMD_CM_INCREASE_ZOOM):
                    dz = 1.0
                if cmdMap.isActive(CommandMapping.CMD_CM_DECREASE_ZOOM):
                    dz = -1.0
                self.__cam.update(dx, dy, dz, True, True, False if dx == dy == dz == 0.0 else True)
                return True
            if cmdMap.isFired(CommandMapping.CMD_CM_ALTERNATE_MODE, key) and isDown:
                self.__activateAlternateMode()
                return True
            cmdMap.isFired(CommandMapping.CMD_CM_CAMERA_RESTORE_DEFAULT, key) and isDown and self.__cam.restoreDefaultsState()
            return True
        else:
            return False

    def handleMouseEvent(self, dx, dy, dz):
        raise self.__isEnabled or AssertionError
        GUI.mcursor().position = self.__aim.offset()
        self.__cam.update(dx, dy, mathUtils.clamp(-1, 1, dz))
        self.__mouseVehicleRotator.handleMouse(dx)
        return True

    def setReloading(self, duration, startTime):
        self.__gunMarker.setReloading(duration, startTime)

    def onMinimapClicked(self, worldPos):
        if self.__aih.isSPG:
            self.__activateAlternateMode(worldPos)

    def showGunMarker(self, flag):
        raise self.__isEnabled or AssertionError
        self.__gunMarker.show(flag)

    def showGunMarker2(self, flag):
        raise self.__isEnabled or AssertionError
        self.__gunMarker.show2(flag)

    def updateGunMarker(self, pos, dir, size, relaxTime, collData):
        raise self.__isEnabled or AssertionError
        self.__gunMarker.update(pos, dir, size, relaxTime, collData)

    def updateGunMarker2(self, pos, dir, size, relaxTime, collData):
        raise self.__isEnabled or AssertionError
        self.__gunMarker.update2(pos, dir, size, relaxTime, collData)

    def setAimingMode(self, enable, mode):
        if enable:
            self.__aimingMode |= mode
        else:
            self.__aimingMode &= -1 - mode

    def getAimingMode(self, mode):
        return self.__aimingMode & mode == mode

    def getDesiredShotPoint(self):
        if not self.__isEnabled:
            raise AssertionError
            return self.__aimingMode == 0 and self.__cam.aimingSystem.getDesiredShotPoint()
        else:
            return None

    def updateShootingStatus(self, canShot):
        raise self.__isEnabled or AssertionError
        self.__canShot = canShot

    def onChangeControlModeByScroll(self):
        self.__activateAlternateMode(pos=None, bByScroll=True)
        return

    def onRecreateDevice(self):
        self.__gunMarker.onRecreateDevice()
        self.__aim.onRecreateDevice()

    def getAim(self):
        return self.__aim

    def __onArenaStarted(self, period, *args):
        self.__isArenaStarted = True if period == constants.ARENA_PERIOD.BATTLE else False

    def setGUIVisible(self, isVisible):
        self.__aim.setVisible(isVisible)
        self.__gunMarker.setGUIVisible(isVisible, valueUpdate=not self.__isArenaStarted)

    def __activateAlternateMode(self, pos = None, bByScroll = False):
        ownVehicle = BigWorld.entity(BigWorld.player().playerVehicleID)
        if ownVehicle is not None and ownVehicle.isStarted and ownVehicle.appearance.isUnderwater:
            return
        elif self.__aih.isSPG and not bByScroll:
            self.__cam.update(0, 0, 0, False, False)
            if pos is None:
                pos = self.camera.aimingSystem.getDesiredShotPoint()
                if pos is None:
                    pos = Math.Matrix(self.__gunMarker.matrixProvider()).applyToOrigin()
            self.__aih.onControlModeChanged('strategic', preferredPos=pos, aimingMode=self.__aimingMode, saveDist=True)
            return
        elif not self.__aih.isSPG:
            self.__cam.update(0, 0, 0, False, False)
            desiredShotPoint = self.camera.aimingSystem.getDesiredShotPoint()
            self.__aih.onControlModeChanged('sniper', preferredPos=desiredShotPoint, aimingMode=self.__aimingMode, saveZoom=True)
            return
        else:
            return


class StrategicControlMode(IControlMode):
    camera = property(lambda self: self.__cam)

    def __init__(self, dataSection, avatarInputHandler):
        self.__aih = weakref.proxy(avatarInputHandler)
        self.__trajectoryDrawer = BigWorld.wg_trajectory_drawer()
        self.__gunMarker = _SuperGunMarker(mode='strategic', isStrategic=True)
        self.__aim = aims.createAim(dataSection.readString('aim'))
        self.__cam = StrategicCamera.StrategicCamera(dataSection['camera'], self.__aim)
        self.__canShoot = False
        self.__isEnabled = False
        self.__aimingMode = 0
        self.__trajectoryDrawerClbk = None
        self.__updateInterval = 0.1
        return

    def prerequisites(self):
        out = []
        out += self.__gunMarker.prerequisites()
        out += self.__aim.prerequisites()
        return out

    def create(self):
        self.__aim.create()
        self.__gunMarker.create()
        self.__cam.create(None)
        self.__initTrajectoryDrawer()
        self.disable()
        return

    def destroy(self):
        self.disable()
        self.__aim.destroy()
        self.__gunMarker.destroy()
        self.__cam.destroy()
        self.__delTrajectoryDrawer()
        self.__aih = None
        return

    def dumpState(self):
        return {'gunMarker': self.__gunMarker.dumpState()}

    def enable(self, **args):
        ctrlState = args.get('ctrlState')
        self.__aimingMode = args.get('aimingMode', self.__aimingMode)
        self.__aim.enable()
        self.__cam.enable(args['preferredPos'], args['saveDist'])
        self.__gunMarker.enable(ctrlState.get('gunMarker', None))
        self.__trajectoryDrawer.visible = BigWorld.player().isGuiVisible
        self.__isEnabled = True
        BigWorld.player().autoAim(None)
        self.__updateTrajectoryDrawer()
        g_postProcessing.enable('strategic')
        return

    def disable(self):
        self.__isEnabled = False
        self.__cam.disable()
        self.__gunMarker.disable()
        self.__aim.disable()
        self.__trajectoryDrawer.visible = False
        if self.__trajectoryDrawerClbk is not None:
            BigWorld.cancelCallback(self.__trajectoryDrawerClbk)
            self.__trajectoryDrawerClbk = None
        g_postProcessing.disable()
        return

    def handleKeyEvent(self, isDown, key, mods, event = None):
        if not self.__isEnabled:
            raise AssertionError
            cmdMap = CommandMapping.g_instance
            cmdMap.isFired(CommandMapping.CMD_CM_SHOOT, key) and isDown and BigWorld.player().shoot()
            return True
        elif cmdMap.isFired(CommandMapping.CMD_CM_VEHICLE_SWITCH_AUTOROTATION, key) and isDown:
            self.__aih.switchAutorotation()
            return True
        elif cmdMap.isFired(CommandMapping.CMD_CM_ALTERNATE_MODE, key) and isDown:
            pos = self.__cam.aimingSystem.getDesiredShotPoint()
            if pos is None:
                pos = Math.Matrix(self.__gunMarker.matrixProvider()).applyToOrigin()
            self.__aih.onControlModeChanged('arcade', preferredPos=pos, aimingMode=self.__aimingMode, closesDist=False)
            return True
        elif cmdMap.isFired(CommandMapping.CMD_CM_FREE_CAMERA, key):
            self.setAimingMode(isDown, AIMING_MODE.USER_DISABLED)
            return True
        elif cmdMap.isFiredList((CommandMapping.CMD_CM_CAMERA_ROTATE_LEFT,
         CommandMapping.CMD_CM_CAMERA_ROTATE_RIGHT,
         CommandMapping.CMD_CM_CAMERA_ROTATE_UP,
         CommandMapping.CMD_CM_CAMERA_ROTATE_DOWN,
         CommandMapping.CMD_CM_INCREASE_ZOOM,
         CommandMapping.CMD_CM_DECREASE_ZOOM), key):
            dx = dy = dz = 0.0
            if cmdMap.isActive(CommandMapping.CMD_CM_CAMERA_ROTATE_LEFT):
                dx = -1.0
            if cmdMap.isActive(CommandMapping.CMD_CM_CAMERA_ROTATE_RIGHT):
                dx = 1.0
            if cmdMap.isActive(CommandMapping.CMD_CM_CAMERA_ROTATE_UP):
                dy = -1.0
            if cmdMap.isActive(CommandMapping.CMD_CM_CAMERA_ROTATE_DOWN):
                dy = 1.0
            if cmdMap.isActive(CommandMapping.CMD_CM_INCREASE_ZOOM):
                dz = 1.0
            if cmdMap.isActive(CommandMapping.CMD_CM_DECREASE_ZOOM):
                dz = -1.0
            self.__cam.update(dx, dy, dz, False if dx == dy == dz == 0.0 else True)
            return True
        elif cmdMap.isFired(CommandMapping.CMD_CM_CAMERA_RESTORE_DEFAULT, key) and isDown:
            self.__cam.update(0, 0, 0, False)
            self.__cam.restoreDefaultsState()
            return True
        else:
            return False

    def handleMouseEvent(self, dx, dy, dz):
        raise self.__isEnabled or AssertionError
        GUI.mcursor().position = self.__aim.offset()
        self.__cam.update(dx, dy, dz)
        return True

    def setReloading(self, duration, startTime):
        self.__gunMarker.setReloading(duration, startTime)

    def onMinimapClicked(self, worldPos):
        self.__cam.teleport(worldPos)

    def showGunMarker(self, flag):
        raise self.__isEnabled or AssertionError
        self.__gunMarker.show(flag)

    def showGunMarker2(self, flag):
        raise self.__isEnabled or AssertionError
        self.__gunMarker.show2(flag)

    def updateGunMarker(self, pos, dir, size, relaxTime, collData):
        raise self.__isEnabled or AssertionError
        self.__gunMarker.update(pos, dir, size, relaxTime, collData)

    def updateGunMarker2(self, pos, dir, size, relaxTime, collData):
        raise self.__isEnabled or AssertionError
        self.__gunMarker.update2(pos, dir, size, relaxTime, collData)

    def setAimingMode(self, enable, mode):
        if enable:
            self.__aimingMode |= mode
        else:
            self.__aimingMode &= -1 - mode

    def getAimingMode(self, mode):
        return self.__aimingMode & mode == mode

    def getDesiredShotPoint(self):
        if not self.__isEnabled:
            raise AssertionError
            return self.__aimingMode == 0 and self.__cam.aimingSystem.getDesiredShotPoint()
        else:
            return None

    def updateShootingStatus(self, canShoot):
        raise self.__isEnabled or AssertionError
        self.__canShoot = canShoot

    def onRecreateDevice(self):
        self.__gunMarker.onRecreateDevice()
        self.__aim.onRecreateDevice()

    def getAim(self):
        return self.__aim

    def setGUIVisible(self, isVisible):
        self.__aim.setVisible(isVisible)
        self.__gunMarker.setGUIVisible(isVisible)
        self.__trajectoryDrawer.visible = isVisible

    def isManualBind(self):
        return True

    def __updateTrajectoryDrawer(self):
        self.__trajectoryDrawerClbk = BigWorld.callback(self.__updateInterval, self.__updateTrajectoryDrawer)
        try:
            R = self.camera.aimingSystem.getDesiredShotPoint()
            if R is None:
                return
            r0, v0, g0 = BigWorld.player().gunRotator.getShotParams(R, True)
            self.__trajectoryDrawer.update(R, r0, v0, self.__updateInterval)
        except:
            LOG_CURRENT_EXCEPTION()

        return

    def __onGunShotChanged(self):
        shotDescr = BigWorld.player().vehicleTypeDescriptor.shot
        self.__trajectoryDrawer.setParams(shotDescr['maxDistance'], Math.Vector3(0, -shotDescr['gravity'], 0), self.__aim.offset())

    def __initTrajectoryDrawer(self):
        BigWorld.player().onGunShotChanged += self.__onGunShotChanged
        self.__trajectoryDrawer.setColors(Math.Vector4(0, 255, 0, 255), Math.Vector4(255, 0, 0, 255), Math.Vector4(128, 128, 128, 255))
        self.__onGunShotChanged()

    def __delTrajectoryDrawer(self):
        BigWorld.player().onGunShotChanged -= self.__onGunShotChanged
        self.__trajectoryDrawer = None
        return


class SniperControlMode(IControlMode):
    camera = property(lambda self: self.__cam)

    def __init__(self, dataSection, avatarInputHandler):
        self.__aih = weakref.proxy(avatarInputHandler)
        self.__gunMarker = _SuperGunMarker('sniper')
        self.__aim = aims.createAim(dataSection.readString('aim'))
        self.__binoculars = BigWorld.wg_binoculars()
        self.__binoculars.setBackgroundTexture(dataSection.readString('binoculars/background'))
        self.__cam = SniperCamera.SniperCamera(dataSection['camera'], self.__aim, self.__binoculars)
        self.__isEnabled = False
        self.__aimingMode = 0
        self.__canShoot = False

    def prerequisites(self):
        out = []
        out += self.__gunMarker.prerequisites()
        out += self.__aim.prerequisites()
        return out

    def create(self):
        self.__aim.create()
        self.__gunMarker.create()
        self.__cam.create(self.onChangeControlModeByScroll)
        self.disable()

    def destroy(self):
        self.disable(True)
        self.__aim.destroy()
        self.__gunMarker.destroy()
        self.__cam.destroy()
        self.__binoculars.enabled = False
        self.__aih = None
        return

    def dumpState(self):
        return {'gunMarker': self.__gunMarker.dumpState()}

    def enable(self, **args):
        ctrlState = args.get('ctrlState')
        self.__aimingMode = args.get('aimingMode', self.__aimingMode)
        self.__aim.enable()
        self.__cam.enable(args['preferredPos'], args['saveZoom'])
        self.__gunMarker.enable(ctrlState.get('gunMarker', None))
        self.__binoculars.enabled = True
        self.__isEnabled = True
        BigWorld.wg_enableTreeHiding(True)
        BigWorld.wg_setTreeHidingRadius(15.0, 10.0)
        TriggersManager.g_manager.activateTrigger(TRIGGER_TYPE.SNIPER_MODE)
        g_postProcessing.enable('sniper')
        desc = BigWorld.player().vehicleTypeDescriptor
        isHorizontalStabilizerAllowed = desc.gun['turretYawLimits'] is None
        self.__cam.aimingSystem.enableHorizontalStabilizer(isHorizontalStabilizerAllowed)
        return

    def disable(self, isDestroy = False):
        self.__isEnabled = False
        self.__aim.disable()
        self.__gunMarker.disable()
        self.__binoculars.enabled = False
        self.__cam.disable()
        BigWorld.wg_enableTreeHiding(False)
        g_postProcessing.disable()
        TriggersManager.g_manager.deactivateTrigger(TRIGGER_TYPE.SNIPER_MODE)

    def handleKeyEvent(self, isDown, key, mods, event = None):
        if not self.__isEnabled:
            raise AssertionError
            cmdMap = CommandMapping.g_instance
            isFiredFreeCamera = cmdMap.isFired(CommandMapping.CMD_CM_FREE_CAMERA, key)
            if cmdMap.isFired(CommandMapping.CMD_CM_LOCK_TARGET, key):
                isFiredLockTarget = isDown
                if isFiredFreeCamera or isFiredLockTarget:
                    if isFiredFreeCamera:
                        self.setAimingMode(isDown, AIMING_MODE.USER_DISABLED)
                    isFiredLockTarget and BigWorld.player().autoAim(BigWorld.target())
            cmdMap.isFired(CommandMapping.CMD_CM_SHOOT, key) and isDown and BigWorld.player().shoot()
            return True
        elif cmdMap.isFired(CommandMapping.CMD_CM_LOCK_TARGET_OFF, key) and isDown:
            BigWorld.player().autoAim(None)
            return True
        elif cmdMap.isFired(CommandMapping.CMD_CM_ALTERNATE_MODE, key) and isDown:
            self.__aih.onControlModeChanged('arcade', preferredPos=self.camera.aimingSystem.getDesiredShotPoint(), turretYaw=self.__cam.aimingSystem.turretYaw, gunPitch=self.__cam.aimingSystem.gunPitch, aimingMode=self.__aimingMode, closesDist=False)
            return True
        elif cmdMap.isFired(CommandMapping.CMD_CM_VEHICLE_SWITCH_AUTOROTATION, key) and isDown:
            self.__aih.switchAutorotation()
            return True
        elif cmdMap.isFiredList((CommandMapping.CMD_CM_CAMERA_ROTATE_LEFT,
         CommandMapping.CMD_CM_CAMERA_ROTATE_RIGHT,
         CommandMapping.CMD_CM_CAMERA_ROTATE_UP,
         CommandMapping.CMD_CM_CAMERA_ROTATE_DOWN,
         CommandMapping.CMD_CM_INCREASE_ZOOM,
         CommandMapping.CMD_CM_DECREASE_ZOOM), key):
            dx = dy = dz = 0.0
            if cmdMap.isActive(CommandMapping.CMD_CM_CAMERA_ROTATE_LEFT):
                dx = -1.0
            if cmdMap.isActive(CommandMapping.CMD_CM_CAMERA_ROTATE_RIGHT):
                dx = 1.0
            if cmdMap.isActive(CommandMapping.CMD_CM_CAMERA_ROTATE_UP):
                dy = -1.0
            if cmdMap.isActive(CommandMapping.CMD_CM_CAMERA_ROTATE_DOWN):
                dy = 1.0
            if cmdMap.isActive(CommandMapping.CMD_CM_INCREASE_ZOOM):
                dz = 1.0
            if cmdMap.isActive(CommandMapping.CMD_CM_DECREASE_ZOOM):
                dz = -1.0
            self.__cam.update(dx, dy, dz, False if dx == dy == 0.0 else True)
            return True
        else:
            return False

    def handleMouseEvent(self, dx, dy, dz):
        raise self.__isEnabled or AssertionError
        GUI.mcursor().position = self.__aim.offset()
        self.__cam.update(dx, dy, dz)
        return True

    def setReloading(self, duration, startTime):
        self.__gunMarker.setReloading(duration, startTime)

    def showGunMarker(self, flag):
        raise self.__isEnabled or AssertionError
        self.__gunMarker.show(flag)

    def showGunMarker2(self, flag):
        raise self.__isEnabled or AssertionError
        self.__gunMarker.show2(flag)

    def updateGunMarker(self, pos, dir, size, relaxTime, collData):
        raise self.__isEnabled or AssertionError
        self.__gunMarker.update(pos, dir, size, relaxTime, collData)

    def updateGunMarker2(self, pos, dir, size, relaxTime, collData):
        raise self.__isEnabled or AssertionError
        self.__gunMarker.update2(pos, dir, size, relaxTime, collData)

    def setAimingMode(self, enable, mode):
        if enable:
            self.__aimingMode |= mode
        else:
            self.__aimingMode &= -1 - mode

    def getAimingMode(self, mode):
        return self.__aimingMode & mode == mode

    def getDesiredShotPoint(self):
        if not self.__isEnabled:
            raise AssertionError
            return self.__aimingMode == 0 and self.__cam.aimingSystem.getDesiredShotPoint()
        else:
            return None

    def updateShootingStatus(self, canShoot):
        raise self.__isEnabled or AssertionError
        self.__canShoot = canShoot

    def onRecreateDevice(self):
        self.__gunMarker.onRecreateDevice()
        self.__aim.onRecreateDevice()
        self.__cam.onRecreateDevice()

    def getAim(self):
        return self.__aim

    def setGUIVisible(self, isVisible):
        self.__aim.setVisible(isVisible)
        self.__gunMarker.setGUIVisible(isVisible)

    def getPreferredAutorotationMode(self):
        vehicle = BigWorld.entities.get(BigWorld.player().playerVehicleID)
        if vehicle is None:
            return
        else:
            desc = vehicle.typeDescriptor
            isRotationAroundCenter = desc.chassis['rotationIsAroundCenter']
            turretHasYawLimits = desc.gun['turretYawLimits'] is not None
            return isRotationAroundCenter and not turretHasYawLimits

    def enableSwitchAutorotationMode(self):
        return self.getPreferredAutorotationMode() != False

    def onChangeControlModeByScroll(self):
        raise self.__isEnabled or AssertionError
        self.__aih.onControlModeChanged('arcade', preferredPos=self.camera.aimingSystem.getDesiredShotPoint(), turretYaw=self.__cam.aimingSystem.turretYaw, gunPitch=self.__cam.aimingSystem.gunPitch, aimingMode=self.__aimingMode, closesDist=True)

    def recreateCamera(self):
        preferredPos = self.camera.aimingSystem.getDesiredShotPoint()
        self.__cam.disable()
        self.__cam.enable(preferredPos, True)


class PostMortemControlMode(IControlMode):
    POSTMORTEM_DELAY_ENABLED = True
    __CAM_FLUENCY = 0.0
    camera = property(lambda self: self.__cam)

    def __init__(self, dataSection, avatarInputHandler):
        self.__aih = weakref.proxy(avatarInputHandler)
        self.__aim = aims.createAim('postmortem')
        self.__cam = ArcadeCamera.ArcadeCamera(dataSection['camera'], self.__aim)
        self.__vIDs = list()
        self.__curIndex = -1
        self.__curVehicleID = None
        self.__selfVehicleID = None
        self.__isEnabled = False
        self.__cbIDWaitForCameraTarget = None
        self.__postmortemDelay = None
        self.__isObserverMode = False
        self.__videoControlModeAvailable = dataSection.readBool('videoModeAvailable', False)
        return

    def prerequisites(self):
        return self.__aim.prerequisites()

    def create(self):
        self.__aim.create()
        self.__cam.create(_ARCADE_CAM_PIVOT_POS, None, True)
        return

    def destroy(self):
        self.disable()
        self.__aim.destroy()
        self.__cam = None
        return

    def dumpState(self):
        return dumpStateEmpty()

    def enable(self, **args):
        ctrlState = args.get('ctrlState')
        player = BigWorld.player()
        if player:
            self.__selfVehicleID = player.playerVehicleID
            self.__isObserverMode = 'observer' in player.vehicleTypeDescriptor.type.tags
        self.__cam.enable(None, False, args.get('postmortemParams'))
        self.__aim.enable()
        self.__connectToArena()
        _setCameraFluency(self.__cam.camera, self.__CAM_FLUENCY)
        self.__isEnabled = True
        if self.__isObserverMode:
            self.__switchToVehicle(-1)
            return
        else:
            if self.POSTMORTEM_DELAY_ENABLED and bool(args.get('bPostmortemDelay')):
                self.__postmortemDelay = PostmortemDelay(self.__cam, self.__onPostmortemDelayStop)
                self.__postmortemDelay.start()
            else:
                self.__switchToVehicle(None)
            g_postProcessing.enable('postmortem')
            return

    def disable(self):
        self.__destroyPostmortemDelay()
        self.__waitForCameraTargetCancel()
        self.__isEnabled = False
        self.__aim.disable()
        self.__disconnectFromArena()
        self.__cam.disable()
        self.__curIndex = -1
        self.__curVehicleID = None
        self.__selfVehicleID = None
        g_postProcessing.disable()
        return

    def handleKeyEvent(self, isDown, key, mods, event = None):
        if not self.__isEnabled:
            raise AssertionError
            cmdMap = CommandMapping.g_instance
            if BigWorld.isKeyDown(Keys.KEY_CAPSLOCK) and constants.IS_DEVELOPMENT and isDown and key == Keys.KEY_F1:
                self.__aih.onControlModeChanged('debug', prevModeName='postmortem', camMatrix=self.__cam.camera.matrix)
                return True
            if BigWorld.isKeyDown(Keys.KEY_CAPSLOCK) and isDown and key == Keys.KEY_F3 and (self.__videoControlModeAvailable or g_battleContext.isPlayerObserver()):
                self.__aih.onControlModeChanged('video', prevModeName='postmortem', camMatrix=self.__cam.camera.matrix, curVehicleID=self.__curVehicleID)
                return True
            if cmdMap.isFired(CommandMapping.CMD_CM_POSTMORTEM_NEXT_VEHICLE, key) and isDown:
                self.__switchToVehicle(-1, True)
                return True
            cmdMap.isFired(CommandMapping.CMD_CM_POSTMORTEM_SELF_VEHICLE, key) and isDown and self.__switchToVehicle(-1, False)
            return True

    def handleMouseEvent(self, dx, dy, dz):
        if not self.__isEnabled:
            raise AssertionError
            return self.__postmortemDelay is not None and True
        else:
            GUI.mcursor().position = self.__aim.offset()
            self.__cam.update(dx, dy, _clamp(-1, 1, dz))
            return True

    def onRecreateDevice(self):
        self.__aim.onRecreateDevice()

    def selectPlayer(self, vehId):
        self.__switchToVehicle(vehId, False)

    def getAim(self):
        return self.__aim

    def setGUIVisible(self, isVisible):
        self.__aim.setVisible(isVisible)

    def __destroyPostmortemDelay(self):
        if self.__postmortemDelay is not None:
            self.__postmortemDelay.destroy()
            self.__postmortemDelay = None
        return

    def __onPostmortemDelayStop(self):
        self.__destroyPostmortemDelay()
        self.__switchToVehicle(None)
        return

    def __switchToVehicle(self, toId = None, toPrevious = False):
        if self.__postmortemDelay is not None:
            return
        else:
            player = BigWorld.player()
            replayCtrl = BattleReplay.g_replayCtrl
            self.__waitForCameraTargetCancel()
            if toId == None and not self.__isObserverMode:
                self.__curIndex = self.__vIDs.index(player.playerVehicleID)
            elif toId >= 0:
                if toId in self.__vIDs:
                    self.__curIndex = self.__vIDs.index(toId)
                else:
                    self.__curIndex = 0
            else:
                if toPrevious:
                    self.__curIndex -= 1
                    if self.__curIndex < 0:
                        self.__curIndex = len(self.__vIDs) - 1
                else:
                    self.__curIndex += 1
                    if self.__curIndex >= len(self.__vIDs):
                        self.__curIndex = 0
                if self.__isObserverMode and len(self.__vIDs) > 0 and self.__vIDs[self.__curIndex] == player.playerVehicleID:
                    self.__curIndex += -1 if toPrevious else 1
                    if self.__curIndex < 0:
                        self.__curIndex = len(self.__vIDs) - 1
                    elif self.__curIndex >= len(self.__vIDs):
                        self.__curIndex = 0
            if replayCtrl.isPlaying:
                self.__curVehicleID = replayCtrl.playerVehicleID
            else:
                newVehicleID = None
                if len(self.__vIDs) == 0:
                    newVehicleID = player.playerVehicleID
                else:
                    newVehicleID = self.__vIDs[self.__curIndex]
                if self.__isObserverMode:
                    if self.__curVehicleID != player.playerVehicleID and newVehicleID == player.playerVehicleID:
                        return
                self.__curVehicleID = newVehicleID
            player.positionControl.bindToVehicle(True, self.__curVehicleID)
            self.__aim.changeVehicle(self.__curVehicleID)
            self.__aih.onPostmortemVehicleChanged(self.__curVehicleID)
            if self.__isObserverMode:
                if self.__cam.vehicleMProv is None:
                    self.__cam.vehicleMProv = player.getOwnVehicleMatrix()
            if self.__curVehicleID != player.playerVehicleID and BigWorld.entity(self.__curVehicleID) is None and not replayCtrl.isPlaying and not self.__isObserverMode and player.arena.positions.get(self.__curVehicleID) is None:
                self.__switchToVehicle(-1, toPrevious)
                return
            self.__cbIDWaitForCameraTarget = BigWorld.callback(0.001, self.__waitForCameraTarget)
            if not replayCtrl.isPlaying:
                self.__cam.vehicleMProv = Math.Matrix(self.__cam.vehicleMProv)
            return

    def __onVehicleAdded(self, vehicleID):
        player = BigWorld.player()
        vDesc = player.arena.vehicles[vehicleID]
        if vDesc['team'] == player.team and vDesc['isAlive']:
            self.__updateVIDsList()

    def __onVehicleKilled(self, victimID, killerID, reason):
        player = BigWorld.player()
        vDesc = player.arena.vehicles[victimID]
        if vDesc['team'] == player.team and not vDesc['isAlive']:
            self.__delAndAdjustIDs(victimID)

    def __onPeriodChange(self, period, *args):
        if period != constants.ARENA_PERIOD.AFTERBATTLE:
            return
        elif self.__isObserverMode:
            return
        else:
            self.__vIDs = list()
            self.__vIDs.append(BigWorld.player().playerVehicleID)
            self.__switchToVehicle(None)
            return

    def __onVehicleLeaveWorld(self, vehicle):
        if vehicle.id == self.__curVehicleID:
            self.__switchToVehicle(None)
        return

    def _playerComparator(self, x1, x2):
        if x1[0] < x2[0]:
            return 1
        if x1[0] > x2[0]:
            return -1
        if x1[1] < x2[1]:
            return 1
        if x1[1] > x2[1]:
            return -1
        if x1[2] < x2[2]:
            return -1
        if x1[2] > x2[2]:
            return 1
        if x1[3] < x2[3]:
            return -1
        if x1[3] > x2[3]:
            return 1

    def __updateVIDsList(self):
        player = BigWorld.player()
        vehicles = player.arena.vehicles
        self.__vIDs = list()
        data = []
        for id, desc in vehicles.items():
            if desc['team'] == player.team and desc['isAlive'] or id == player.playerVehicleID and not desc['isAlive']:
                vehicleType = desc['vehicleType']
                if 'observer' not in vehicleType.type.tags:
                    data.append((desc['isAlive'],
                     vehicleType.balanceWeight,
                     vehicleType.type.shortUserString,
                     desc['name'],
                     id))

        data = sorted(data, cmp=self._playerComparator)
        for item in data:
            self.__vIDs.append(item[4])

    def __connectToArena(self):
        player = BigWorld.player()
        player.arena.onVehicleAdded += self.__onVehicleAdded
        player.arena.onVehicleKilled += self.__onVehicleKilled
        player.arena.onPeriodChange += self.__onPeriodChange
        player.onVehicleLeaveWorld += self.__onVehicleLeaveWorld
        self.__updateVIDsList()

    def __disconnectFromArena(self):
        player = BigWorld.player()
        player.arena.onVehicleAdded -= self.__onVehicleAdded
        player.arena.onVehicleKilled -= self.__onVehicleKilled
        player.arena.onPeriodChange -= self.__onPeriodChange
        player.onVehicleLeaveWorld -= self.__onVehicleLeaveWorld

    def __delAndAdjustIDs(self, id):
        if id == BigWorld.player().playerVehicleID:
            return
        index = self.__vIDs.index(id)
        del self.__vIDs[index]
        if index <= self.__curIndex:
            self.__curIndex -= 1

    def __prepareNextVehicle(self, curNextIndex):
        player = BigWorld.player()
        curVPos = player.position
        nextIndex = curNextIndex
        curLen = 0
        for index in range(curNextIndex, len(self.__vIDs)):
            v = BigWorld.entity(self.__vIDs[index])
            p = player.arena.positions.get(self.__vIDs[index], None)
            if v is not None or p is not None:
                pos = v.position if v is not None else p
                tmpLen = curVPos.flatDistTo(pos)
                if tmpLen < curLen or curLen == 0.0:
                    curLen = tmpLen
                    nextIndex = index

        _swap(self.__vIDs, curNextIndex, nextIndex)
        return

    def __waitForCameraTarget(self):
        self.__cbIDWaitForCameraTarget = None
        targetMProv = self.__cam.vehicleMProv
        targetPos = Math.Matrix(targetMProv).translation
        groundPos = Math.Vector3(targetPos)
        colRes = BigWorld.wg_collideSegment(BigWorld.player().spaceID, (groundPos.x, 1000.0, groundPos.z), (groundPos.x, -1000.0, groundPos.z), 128)
        if colRes is None:
            self.__cbIDWaitForCameraTarget = BigWorld.callback(0.1, self.__waitForCameraTarget)
            return
        else:
            groundPos.y = colRes[0].y
            vehicle = BigWorld.entity(self.__curVehicleID)
            if vehicle is None:
                targetMProv = Math.Matrix()
                targetMProv.setTranslate(groundPos)
                self.__cam.vehicleMProv = targetMProv
                self.__cbIDWaitForCameraTarget = BigWorld.callback(0.1, self.__waitForCameraTarget)
                return
            self.__cam.vehicleMProv = vehicle.matrix
            self.__aih.onCameraChanged('postmortem', self.__curVehicleID)
            return

    def __waitForCameraTargetCancel(self):
        if self.__cbIDWaitForCameraTarget is not None:
            BigWorld.cancelCallback(self.__cbIDWaitForCameraTarget)
            self.__cbIDWaitForCameraTarget = None
        return

    def isSelfVehicle(self):
        return self.__curVehicleID == self.__selfVehicleID

    @property
    def curVehicleID(self):
        return self.__curVehicleID


class _ShellingControl():
    __TARGET_MODEL_FILE_NAME = 'cat/models/position_gizmo.model'
    __TARGET_POINTER_FILE_NAME = 'cat/target_pointer.dds'

    def __init__(self, camera):
        self.__bEnable = False
        self.__shellingObject = None
        self.__camera = camera
        self.__targetPointer = self.__createTargetPointer()
        self.__targetModel = self.__createTargetModel()
        self.__targetModelVisible = False
        self.__targetModelAutoUpdateCallbackID = None
        self.__targetModelAutoUpdateOnGetMatrix = None
        return

    def destroy(self):
        self.setEnable(False)
        if self.__shellingObject is not None:
            self.__shellingObject.deselectTarget()
            self.installShellingObject(None)
        self.__createTargetPointer(bDelete=True)
        self.__targetModelVisible = None
        self.__createTargetModel(bDelete=True)
        self.__camera = None
        return

    def setEnable(self, value):
        if self.__bEnable == value:
            return
        if value:
            self.__showTargetPointer_directly(True)
            self.__showTargetModel_directly(self.__targetModelVisible)
        else:
            self.__showTargetPointer_directly(False)
            self.__showTargetModel_directly(False)
        self.__bEnable = value

    def installShellingObject(self, shellingObject):
        if shellingObject is not None:
            self.installShellingObject(None)
            self.__shellingObject = shellingObject
            self.__shellingObject._setCamera(self.__camera.camera)
        elif self.__shellingObject is not None:
            self.__shellingObject._setCamera(None)
            self.__shellingObject = None
        return

    def getShellingObjectInstalled(self):
        return self.__shellingObject is not None

    def getShellingObject(self):
        return self.__shellingObject

    def showTargetPointer(self, value):
        self.__showTargetPointer_directly(value)

    def showTargetModel(self, value):
        self.__targetModelVisible = value
        if self.__bEnable:
            self.__showTargetModel_directly(value)

    def setTargetModelMatrix(self, worldMatrix):
        self.__targetModel.motors[0].signal = Math.Matrix(worldMatrix)

    def setTargetModelAutoUpdate(self, onGetMatrix = None):
        if self.__targetModelAutoUpdateCallbackID is not None:
            BigWorld.cancelCallback(self.__targetModelAutoUpdateCallbackID)
            self.__targetModelAutoUpdateCallbackID = None
        self.__targetModelAutoUpdateOnGetMatrix = onGetMatrix
        if self.__targetModelAutoUpdateOnGetMatrix is not None:
            self.__targetModelAutoUpdateCallbackID = BigWorld.callback(0.001, self.__targetModelAutoUpdateCallbackFunc)
        return

    def recreate(self):
        isVisible = self.__targetPointer.visible
        self.__createTargetPointer(bDelete=True)
        self.__targetPointer = self.__createTargetPointer()
        self.__targetPointer.visible = isVisible
        isVisible = self.__targetModel.visible
        self.__createTargetModel(bDelete=True)
        self.__targetModel = self.__createTargetModel()
        self.__targetModel.visible = isVisible

    def handleKeyEvent(self, isDown, key, mods, event = None):
        if self.__shellingObject is not None:
            if key == Keys.KEY_LEFTMOUSE and isDown:
                self.__shellingObject.shoot()
                return True
            if key == Keys.KEY_RIGHTMOUSE and isDown:
                self.__shellingObject.selectTarget()
                return True
            if key == Keys.KEY_MIDDLEMOUSE and isDown:
                self.__shellingObject.deselectTarget()
                return True
        return False

    def __targetModelAutoUpdateCallbackFunc(self):
        self.__targetModelAutoUpdateCallbackID = None
        nextCallbackInterval = 0.001
        try:
            newMatrix = self.__targetModelAutoUpdateOnGetMatrix()
            if newMatrix is not None:
                self.__targetModel.motors[0].signal = Math.Matrix(newMatrix)
            else:
                nextCallbackInterval = 2.0
        except:
            nextCallbackInterval = 2.0
            LOG_DEBUG('<_targetModelAutoUpdateCallbackFunc>: target model is not updated')

        self.__targetModelAutoUpdateCallbackID = BigWorld.callback(nextCallbackInterval, self.__targetModelAutoUpdateCallbackFunc)
        return

    def __createTargetPointer(self, bDelete = False):
        result = None
        if not bDelete:
            result = GUI.Simple(_ShellingControl.__TARGET_POINTER_FILE_NAME)
            result.position[2] = 0.7
            result.size = (2, 2)
            result.materialFX = 'BLEND_INVERSE_COLOUR'
            result.filterType = 'LINEAR'
            result.visible = False
            GUI.addRoot(result)
        elif self.__targetPointer is not None:
            GUI.delRoot(self.__targetPointer)
            self.__targetPointer = None
        return result

    def __createTargetModel(self, bDelete = False):
        result = None
        if not bDelete:
            result = BigWorld.Model(_ShellingControl.__TARGET_MODEL_FILE_NAME)
            result.addMotor(BigWorld.Servo(Math.Matrix()))
            result.visible = False
            BigWorld.addModel(result)
        elif self.__targetModel is not None:
            self.setTargetModelAutoUpdate(None)
            BigWorld.delModel(self.__targetModel)
            self.__targetModel = None
        return result

    def __showTargetPointer_directly(self, value):
        self.__targetPointer.visible = value

    def __showTargetModel_directly(self, value):
        self.__targetModel.visible = value


class _SuperGunMarker():

    def __init__(self, mode = 'arcade', isStrategic = False):
        self.__show2 = useServerAim()
        if not constants.IS_DEVELOPMENT:
            self.__show1 = not self.__show2
            self.__isGuiVisible = True
            if isStrategic:
                self.__gm1 = _SPGFlashGunMarker()
            else:
                self.__gm1 = _FlashGunMarker(mode)
            self.__gm2 = isStrategic and _SPGFlashGunMarker(True)
        else:
            self.__gm2 = _FlashGunMarker(mode)

    def prerequisites(self):
        return self.__gm1.prerequisites() + self.__gm2.prerequisites()

    def create(self):
        self.__gm1.create()
        self.__gm2.create()

    def destroy(self):
        self.__gm1.destroy()
        self.__gm2.destroy()

    def enable(self, state):
        if state is not None:
            self.__show1 = state.get('show1', False)
            self.__show2 = state.get('show2', False)
        self.__gm1.enable(state)
        self.__gm2.enable(state)
        self.show(self.__show1)
        self.show2(self.__show2)
        self.onRecreateDevice()
        return

    def disable(self):
        self.__gm1.disable()
        self.__gm2.disable()

    def dumpState(self):
        out = self.__gm1.dumpState()
        out['pos2'] = self.__gm2.getPosition()
        out['show1'] = self.__show1
        out['show2'] = self.__show2
        return out

    def matrixProvider(self):
        return self.__gm1.matrixProvider

    def setReloading(self, duration, startTime = None):
        self.__gm1.setReloading(duration, startTime)
        self.__gm2.setReloading(duration, startTime)

    def show(self, flag):
        self.__show1 = flag
        self.__gm1.show(flag and self.__isGuiVisible)

    def show2(self, flag):
        if BattleReplay.isPlaying():
            return
        show2Prev = self.__show2
        if flag:
            self.__show2 = self.__isGuiVisible
            if self.__show2 and show2Prev != self.__show2:
                self.__gm2.setPosition(self.__gm1.getPosition())
            self.__gm2.show(self.__show2)
            constants.IS_DEVELOPMENT or self.show(not flag)

    def setGUIVisible(self, isVisible, valueUpdate = False):
        self.__isGuiVisible = isVisible
        if not valueUpdate:
            serverAim = useServerAim()
            self.show(constants.IS_DEVELOPMENT or not serverAim)
            self.show2(serverAim)

    def update(self, pos, dir, size, relaxTime, collData):
        self.__gm1.update(pos, dir, size, relaxTime, collData)

    def update2(self, pos, dir, size, relaxTime, collData):
        self.__gm2.update(pos, dir, size, relaxTime, collData)

    def onRecreateDevice(self):
        self.__gm1.onRecreateDevice()
        self.__gm2.onRecreateDevice()

    def setPosition(self, pos):
        self.__gm1.setPosition(pos)

    def setPosition2(self, pos):
        self.__gm2.setPosition(pos)

    def getPosition(self):
        return self.__gm1.getPosition()

    def getPosition2(self):
        return self.__gm2.getPosition()


class _SPGFlashGunMarker(Flash):
    _FLASH_CLASS = 'WGSPGCrosshairFlash'
    _SWF_FILE_NAME = 'crosshair_strategic.swf'
    _SWF_SIZE = (620, 620)

    def __init__(self, isDebug = False):
        Flash.__init__(self, self._SWF_FILE_NAME, self._FLASH_CLASS)
        self.component.wg_inputKeyMode = 2
        self.component.position.z = DEPTH_OF_GunMarker
        self.component.focus = False
        self.component.moveFocus = False
        self.component.heightMode = 'PIXEL'
        self.component.widthMode = 'PIXEL'
        self.movie.backgroundAlpha = 0
        self.flashSize = self._SWF_SIZE
        self.__animMat = None
        if isDebug:
            self.call('Crosshair.setAsDebug', [isDebug])
        return

    def prerequisites(self):
        return []

    def dumpState(self):
        return {'reload': dict(self.__reload),
         'pos1': self.getPosition(),
         'size': 0.0}

    def create(self):
        self.component.wg_maxTime = 5.0
        self.component.wg_serverTickLength = 0.1
        self.component.wg_sizeScaleRate = 10.0
        self.component.wg_sizeConstraints = Math.Vector2(50.0, 100.0)
        self.component.wg_usePyCollDetect = False
        self.component.wg_setRelaxTime(0.1)
        self.active(True)
        self.__reload = {'start_time': 0,
         'duration': 0,
         'isReloading': False}
        replayCtrl = BattleReplay.g_replayCtrl
        if replayCtrl.isPlaying and replayCtrl.replayContainsGunReloads:
            self.__cbIdSetReloading = BigWorld.callback(0.0, self.setReloadingFromReplay)
        else:
            self.__cbIdSetReloading = None
        self.onRecreateDevice()
        return

    def destroy(self):
        if self.__cbIdSetReloading is not None:
            BigWorld.cancelCallback(self.__cbIdSetReloading)
            self.__cbIdSetReloading = None
        self.active(False)
        return

    def enable(self, state):
        if state is not None:
            rs = state['reload']
            self.setReloading(rs['duration'], rs['startTime'], rs['isReloading'], correction=rs.get('correction'))
            self.setPosition(state['pos1'])
        return

    def disable(self):
        self.show(False)

    def matrixProvider(self):
        return self.__animMat

    def show(self, flag):
        self.component.visible = flag

    def setReloading(self, duration, startTime = None, isReloading = True, correction = None):
        rs = self.__reload
        rs['isReloading'] = isReloading
        rs['startTime'] = BigWorld.time() if startTime is None else startTime
        rs['duration'] = duration
        rs['correction'] = correction
        replayCtrl = BattleReplay.g_replayCtrl
        if replayCtrl.isPlaying and replayCtrl.replayContainsGunReloads:
            return
        else:
            startTime = 0.0 if startTime is None else BigWorld.time() - startTime
            self.call('Crosshair.setReloading', [duration, startTime, isReloading])
            return

    def setReloadingAsPercent(self, percent):
        self.call('Crosshair.setReloadingAsPercent', [percent])

    def setReloadingFromReplay(self):
        self.setReloadingAsPercent(100.0 * BattleReplay.g_replayCtrl.getGunReloadAmountLeft())
        self.__cbIdSetReloading = BigWorld.callback(0.0, self.setReloadingFromReplay)

    def update(self, pos, dir, size, relaxTime, collData):
        m = Math.Matrix()
        m.setTranslate(pos)
        self.__setupMatrixAnimation()
        self.__animMat.keyframes = ((0.0, Math.Matrix(self.__animMat)), (relaxTime, m))
        self.__animMat.time = 0.0
        self.__spgUpdate(size)

    def onRecreateDevice(self):
        self.component.size = GUI.screenResolution()

    def setPosition(self, pos):
        m = Math.Matrix()
        m.setTranslate(pos)
        self.__setupMatrixAnimation()
        self.__animMat.keyframes = ((0.0, m), (0.0, m))
        self.__animMat.time = 0.0

    def getPosition(self):
        if self.__animMat is None:
            return Math.Vector3(0.0, 0.0, 0.0)
        else:
            return Math.Matrix(self.__animMat).translation

    def __setupMatrixAnimation(self):
        if self.__animMat is not None:
            return
        else:
            self.__animMat = Math.MatrixAnimation()
            return

    def __spgUpdate(self, size):
        gunRotator = BigWorld.player().gunRotator
        shotDesc = BigWorld.player().vehicleTypeDescriptor.shot
        try:
            dispersionAngle = gunRotator.dispersionAngle
            pos3d, vel3d = gunRotator._VehicleGunRotator__getCurShotPosition()
            gravity3d = Math.Vector3(0.0, -shotDesc['gravity'], 0.0)
            replayCtrl = BattleReplay.g_replayCtrl
            if replayCtrl.isPlaying and replayCtrl.isClientReady:
                d, s = replayCtrl.getSPGGunMarkerParams()
                if d != -1.0 and s != -1.0:
                    dispersionAngle = d
                    size = s
            elif replayCtrl.isRecording:
                replayCtrl.setSPGGunMarkerParams(dispersionAngle, size)
            self.component.wg_update(pos3d, vel3d, gravity3d, dispersionAngle, size)
        except:
            LOG_CURRENT_EXCEPTION()


class _FlashGunMarker(Flash):
    _FLASH_CLASS = 'WGCrosshairFlash'
    _SWF_FILE_NAME = 'crosshair_sniper.swf'
    _SWF_SIZE = (620, 620)
    _colorsByPiercing = {'default': {'not_pierced': 'red',
                 'little_pierced': 'orange',
                 'great_pierced': 'green'},
     'color_blind': {'not_pierced': 'purple',
                     'little_pierced': 'yellow',
                     'great_pierced': 'green'}}

    def __init__(self, mode):
        Flash.__init__(self, self._SWF_FILE_NAME, self._FLASH_CLASS)
        self.component.wg_inputKeyMode = 2
        self.component.position.z = DEPTH_OF_GunMarker
        self.component.focus = False
        self.component.moveFocus = False
        self.component.heightMode = 'PIXEL'
        self.component.widthMode = 'PIXEL'
        self.movie.backgroundAlpha = 0
        self.flashSize = self._SWF_SIZE
        self.mode = mode
        self.__curSize = 0.0
        self.__animMat = None
        return

    def prerequisites(self):
        return []

    def dumpState(self):
        return {'reload': dict(self.__reload),
         'pos1': self.getPosition(),
         'size': self.__curSize}

    def create(self):
        type = 'color_blind' if AccountSettings.getSettings('isColorBlind') else 'default'
        self._curColors = self._colorsByPiercing[type]
        from account_helpers.SettingsCore import g_settingsCore
        g_settingsCore.onSettingsChanged += self.applySettings
        self.component.wg_sizeConstraint = (10, 300)
        self.component.wg_setStartSize(10.0)
        self.active(True)
        self.__reload = {'start_time': 0,
         'duration': 0,
         'isReloading': False}
        replayCtrl = BattleReplay.g_replayCtrl
        if replayCtrl.isPlaying and replayCtrl.replayContainsGunReloads:
            self.__cbIdSetReloading = BigWorld.callback(0.0, self.setReloadingFromReplay)
        else:
            self.__cbIdSetReloading = None
        self.onRecreateDevice()
        return

    def applySettings(self, diff):
        from account_helpers.SettingsCore import g_settingsCore
        if self.mode in diff:
            for type in ('arcade', 'sniper'):
                if type in diff:
                    settings = g_settingsCore.getSetting(type)
                    current = settings['gunTag']
                    currentType = settings['gunTagType']
                    self.call('Crosshair.setGunTag', [current, currentType])
                    current = settings['mixing']
                    currentType = settings['mixingType']
                    self.call('Crosshair.setMixing', [current, currentType])

        if 'isColorBlind' in diff:
            type = 'color_blind' if diff['isColorBlind'] else 'default'
            self._curColors = self._colorsByPiercing[type]

    def destroy(self):
        from account_helpers.SettingsCore import g_settingsCore
        g_settingsCore.onSettingsChanged -= self.applySettings
        self.active(False)
        if self.__cbIdSetReloading is not None:
            BigWorld.cancelCallback(self.__cbIdSetReloading)
            self.__cbIdSetReloading = None
        self.__animMat = None
        return

    def enable(self, state):
        self.applySettings(self.mode)
        if state is not None:
            rs = state['reload']
            self.setReloading(rs['duration'], rs['startTime'], rs['isReloading'], correction=rs.get('correction'), switched=True)
            self.setPosition(state['pos1'])
            self.component.wg_updateSize(state['size'], 0)
        return

    def disable(self):
        self.show(False)

    def matrixProvider(self):
        return self.__animMat

    def show(self, flag):
        self.component.visible = flag

    def setReloading(self, duration, startTime = None, isReloading = True, correction = None, switched = False):
        rs = self.__reload
        _isReloading = rs.get('isReloading', False)
        _startTime = rs.get('startTime', 0)
        _duration = rs.get('duration', 0)
        isReloading = duration > 0
        rs['isReloading'] = isReloading
        rs['correction'] = None
        replayCtrl = BattleReplay.g_replayCtrl
        if replayCtrl.isPlaying:
            allowFlashCall = not replayCtrl.replayContainsGunReloads
            if not switched and _isReloading and duration > 0 and _duration > 0:
                current = BigWorld.time()
                rs['correction'] = {'timeRemaining': duration,
                 'startTime': current,
                 'startPosition': (current - _startTime) / _duration}
                allowFlashCall and self.call('Crosshair.correctReloadingTime', [duration])
        else:
            rs['startTime'] = BigWorld.time() if startTime is None else startTime
            rs['duration'] = duration
            if correction is not None:
                params = self._getCorrectionReloadingParams(correction)
                if params is not None:
                    rs['correction'] = correction
                    if allowFlashCall:
                        self.call('Crosshair.setReloading', params)
            else:
                startTime = 0.0 if startTime is None else BigWorld.time() - startTime
                if allowFlashCall:
                    self.call('Crosshair.setReloading', [duration, startTime, isReloading])
        return

    def setReloadingFromReplay(self):
        self._setReloadingAsPercent(100.0 * BattleReplay.g_replayCtrl.getGunReloadAmountLeft())
        self.__cbIdSetReloading = BigWorld.callback(0.0, self.setReloadingFromReplay)

    def _setReloadingAsPercent(self, percent):
        self.call('Crosshair.setReloadingAsPercent', [percent])

    def update(self, pos, dir, size, relaxTime, collData):
        m = Math.Matrix()
        m.setTranslate(pos)
        self.__setupMatrixAnimation()
        self.__animMat.keyframes = ((0.0, Math.Matrix(self.__animMat)), (relaxTime, m))
        self.__animMat.time = 0.0
        self.__curSize = _calcScale(m, size) * (GUI.screenResolution()[0] * 0.5)
        replayCtrl = BattleReplay.g_replayCtrl
        if replayCtrl.isPlaying and replayCtrl.isClientReady:
            s = replayCtrl.getArcadeGunMarkerSize()
            if s != -1.0:
                self.__curSize = s
        elif replayCtrl.isRecording:
            replayCtrl.setArcadeGunMarkerSize(self.__curSize)
        if collData is None or collData[0].health <= 0 or collData[0].publicInfo['team'] == BigWorld.player().team:
            self.call('Crosshair.setMarkerType', ['normal'])
        else:
            self._changeColor(pos, collData[2])
        self.component.wg_updateSize(self.__curSize, relaxTime)
        return

    def onRecreateDevice(self):
        self.component.size = GUI.screenResolution()

    def setPosition(self, pos):
        m = Math.Matrix()
        m.setTranslate(pos)
        self.__setupMatrixAnimation()
        self.__animMat.keyframes = ((0.0, m), (0.0, m))
        self.__animMat.time = 0.0

    def getPosition(self):
        if self.__animMat is None:
            return Math.Vector3(0.0, 0.0, 0.0)
        else:
            return Math.Matrix(self.__animMat).translation

    def __setupMatrixAnimation(self):
        if self.__animMat is not None:
            return
        else:
            self.__animMat = Math.MatrixAnimation()
            self.component.wg_positionMatProv = self.__animMat
            return

    def _changeColor(self, hitPoint, armor):
        vDesc = BigWorld.player().vehicleTypeDescriptor
        ppDesc = vDesc.shot['piercingPower']
        maxDist = vDesc.shot['maxDistance']
        dist = (hitPoint - BigWorld.player().getOwnVehiclePosition()).length
        if dist <= 100.0:
            piercingPower = ppDesc[0]
        elif maxDist > dist:
            p100, p500 = ppDesc
            piercingPower = p100 + (p500 - p100) * (dist - 100.0) / 400.0
            if piercingPower < 0.0:
                piercingPower = 0.0
        else:
            piercingPower = 0.0
        piercingPercent = 1000.0
        if piercingPower > 0.0:
            piercingPercent = 100.0 + (armor - piercingPower) / piercingPower * 100.0
        type = 'great_pierced'
        if piercingPercent >= 150:
            type = 'not_pierced'
        elif 90 < piercingPercent < 150:
            type = 'little_pierced'
        self.call('Crosshair.setMarkerType', [self._curColors[type]])

    def _getCorrectionReloadingParams(self, correction):
        cTimeRemaining = correction.get('timeRemaining', 0)
        cStartTime = correction.get('startTime', 0)
        cStartPosition = correction.get('startPosition', 0)
        if not cTimeRemaining > 0:
            LOG_WARNING('timeRemaining - invalid value ', cTimeRemaining)
            return None
        else:
            delta = BigWorld.time() - cStartTime
            currentPosition = cStartPosition + delta / cTimeRemaining * (1 - cStartPosition)
            return [cTimeRemaining - delta,
             cStartTime,
             True,
             currentPosition * 100.0]


class _GunMarker():

    def __init__(self, dataSection):
        self._readCfg(dataSection)
        self.__mover = None
        self.__gui = None
        self.__model = None
        self.__animMat = None
        return

    def prerequisites(self):
        return [self.__cfg['texture']]

    def create(self):
        cfg = self.__cfg
        sr = GUI.screenResolution()
        self.__gui = GUI.Window('')
        self.__gui.heightMode = 'PIXEL'
        self.__gui.widthMode = 'PIXEL'
        self.__gui.width = sr[0]
        self.__gui.height = sr[1]
        self.__gui.position[2] = DEPTH_OF_GunMarker
        self.__gui.visible = False
        mover = GUI.MatrixShader()
        mover.target = None
        mover.eta = 0
        mover.blend = True
        self.__gui.addShader(mover, 'mover')
        elems = cfg['elems']
        self._createGui(elems['top'], 'top')
        self._createGui(elems['right'], 'right')
        self._createGui(elems['bottom'], 'bottom')
        self._createGui(elems['left'], 'left')
        center = GUI.Simple(cfg['texture'])
        center.mapping = _buildTexCoord(elems['center'][0], cfg['size'])
        center.heightMode = 'PIXEL'
        center.widthMode = 'PIXEL'
        center.materialFX = 'BLEND'
        center.size = elems['center'][1]
        self.__gui.addChild(center, 'center')
        GUI.addRoot(self.__gui)
        return

    def destroy(self):
        GUI.delRoot(self.__gui)
        self.__animMat = None
        return

    def matrixProvider(self):
        return self.__animMat

    def show(self, flag):
        self.__gui.visible = flag

    def update(self, pos, dir, size, relaxTime, collData):
        m = Math.Matrix()
        m.setTranslate(pos)
        self.__setupMatrixAnimation(relaxTime)
        self.__animMat.keyframes = ((0.0, Math.Matrix(self.__animMat)), (relaxTime, m))
        self.__animMat.time = 0.0
        sr = GUI.screenResolution()
        aspect = sr[0] / float(sr[1])
        scale = _calcScale(m, size)
        self._transformGui(Math.Vector3(0, scale * aspect, 0), relaxTime, 'top')
        self._transformGui(Math.Vector3(scale, 0, 0), relaxTime, 'right')
        self._transformGui(Math.Vector3(0, -scale * aspect, 0), relaxTime, 'bottom')
        self._transformGui(Math.Vector3(-scale, 0, 0), relaxTime, 'left')

    def onRecreateDevice(self):
        sr = GUI.screenResolution()
        self.__gui.width = sr[0]
        self.__gui.height = sr[1]

    def setPosition(self, pos):
        m = Math.Matrix()
        m.setTranslate(pos)
        self.__setupMatrixAnimation(0.0)
        self.__animMat.keyframes = ((0.0, m), (0.0, m))
        self.__animMat.time = 0.0

    def getPosition(self):
        if self.__animMat is None:
            return Math.Vector3(0.0, 0.0, 0.0)
        else:
            return Math.Matrix(self.__animMat).translation

    def _createGui(self, elemDesc, name):
        mover = GUI.MatrixShader()
        mover.blend = True
        mover.eta = 0.0
        gui = GUI.Simple(self.__cfg['texture'])
        gui.mapping = _buildTexCoord(elemDesc[0], self.__cfg['size'])
        gui.verticalPositionMode = 'CLIP'
        gui.horizontalPositionMode = 'CLIP'
        gui.heightMode = 'PIXEL'
        gui.widthMode = 'PIXEL'
        gui.materialFX = 'BLEND'
        gui.size = elemDesc[1]
        gui.addShader(mover, 'mover')
        self.__gui.addChild(gui, name)

    def _transformGui(self, translate, relaxTime, name):
        mat = Math.Matrix()
        mat.setTranslate(translate)
        mov = getattr(self.__gui, name).mover
        mov.target = mat
        mov.eta = relaxTime

    def _readCfg(self, dataSection):
        self.__cfg = dict()
        self.__cfg['texture'] = dataSection.readString('texture')
        self.__cfg['size'] = dataSection.readVector2('size')
        self.__cfg['elems'] = dict()
        self.__readElem(dataSection['elems/top'], 'top')
        self.__readElem(dataSection['elems/right'], 'right')
        self.__readElem(dataSection['elems/bottom'], 'bottom')
        self.__readElem(dataSection['elems/left'], 'left')
        self.__readElem(dataSection['elems/center'], 'center')

    def __readElem(self, dataSection, name):
        mapping = dataSection.readVector4('mapping', Math.Vector4(0, 0, 0, 0))
        size = dataSection.readVector2('size', Math.Vector2(0, 0))
        self.__cfg['elems'][name] = (mapping, size)

    def __setupMatrixAnimation(self, relaxTime):
        if self.__animMat is not None:
            return
        else:
            self.__animMat = Math.MatrixAnimation()
            _wtcMat = GUI.WorldToClipMP()
            _wtcMat.target = self.__animMat
            _wtcMat.onlyFront = True
            self.__gui.mover.target = _wtcMat
            self.__gui.mover.eta = relaxTime
            return


class _MouseVehicleRotator():
    ROTATION_ACTIVITY_INTERVAL = 0.2

    def __init__(self):
        self.__rotationState = 0
        self.__cbIDActivity = None
        return

    def destroy(self):
        self.unforceRotation(isDestroy=True)

    def handleMouse(self, dx):
        import Avatar
        player = BigWorld.player()
        if not isinstance(player, Avatar.PlayerAvatar):
            return
        else:
            cmdMap = CommandMapping.g_instance
            if not cmdMap.isActive(CommandMapping.CMD_MOVE_FORWARD_SPEC):
                return
            if dx * self.__rotationState > 0:
                return
            self.__rotationState = _clamp(-1, 1, dx)
            bStartRotation = dx != 0
            if self.__cbIDActivity is not None:
                BigWorld.cancelCallback(self.__cbIDActivity)
                self.__cbIDActivity = None
            if bStartRotation:
                self.__cbIDActivity = BigWorld.callback(self.ROTATION_ACTIVITY_INTERVAL, self.__cbActivity)
            if bStartRotation:
                forceMask = 12
                if dx < 0:
                    forceFlags = 4
                if dx > 0:
                    forceFlags = 8
            else:
                forceMask = 0
                forceFlags = 204
            BigWorld.player().moveVehicleByCurrentKeys(bStartRotation, forceFlags, forceMask)
            return

    def unforceRotation(self, isDestroy = False):
        self.__rotationState = 0
        if self.__cbIDActivity is not None:
            BigWorld.cancelCallback(self.__cbIDActivity)
            self.__cbIDActivity = None
        if not isDestroy:
            import Avatar
            player = BigWorld.player()
            if not isinstance(player, Avatar.PlayerAvatar):
                return
            player.moveVehicleByCurrentKeys(False)
        return

    def __cbActivity(self):
        self.__cbIDActivity = None
        self.unforceRotation()
        return


def getFocalPoint():
    dir, start = cameras.getWorldRayAndPoint(0, 0)
    end = start + dir.scale(100000.0)
    point = collideDynamicAndStatic(start, end, (BigWorld.player().playerVehicleID,), 0)
    if point is not None:
        return point[0]
    else:
        return AimingSystems.shootInSkyPoint(start, dir)
        return


def useServerAim():
    from account_helpers.SettingsCore import g_settingsCore
    return g_settingsCore.getSetting('useServerAim')


def dumpStateEmpty():
    return {'gunMarkerPosition': None,
     'gunMarkerPosition2': None,
     'aimState': None}


def _clamp(minVal, maxVal, val):
    tmpVal = val
    tmpVal = max(minVal, val)
    tmpVal = min(maxVal, tmpVal)
    return tmpVal


def _sign(val):
    if val > 0:
        return 1.0
    elif val < 0:
        return -1.0
    else:
        return 0.0


def _buildTexCoord(vec4, textureSize):
    out = ((vec4[0] / textureSize[0], vec4[1] / textureSize[1]),
     (vec4[0] / textureSize[0], vec4[3] / textureSize[1]),
     (vec4[2] / textureSize[0], vec4[3] / textureSize[1]),
     (vec4[2] / textureSize[0], vec4[1] / textureSize[1]))
    return out


def _setCameraFluency(cam, value):
    pass


def _swap(data, index1, index2):
    if index1 == index2:
        return
    tmp = data[index1]
    data[index1] = data[index2]
    data[index2] = tmp


def _calcScale(worldMat, size):
    sr = GUI.screenResolution()
    aspect = sr[0] / sr[1]
    proj = BigWorld.projection()
    wtcMat = Math.Matrix()
    wtcMat.perspectiveProjection(proj.fov, aspect, proj.nearPlane, proj.farPlane)
    wtcMat.preMultiply(BigWorld.camera().matrix)
    wtcMat.preMultiply(worldMat)
    pointMat = Math.Matrix()
    pointMat.set(BigWorld.camera().matrix)
    transl = Math.Matrix()
    transl.setTranslate(Math.Vector3(size, 0, 0))
    pointMat.postMultiply(transl)
    pointMat.postMultiply(BigWorld.camera().invViewMatrix)
    p = pointMat.applyToOrigin()
    pV4 = wtcMat.applyV4Point(Math.Vector4(p[0], p[1], p[2], 1))
    oV4 = wtcMat.applyV4Point(Math.Vector4(0, 0, 0, 1))
    pV3 = Math.Vector3(pV4[0], pV4[1], pV4[2]).scale(1.0 / pV4[3])
    oV3 = Math.Vector3(oV4[0], oV4[1], oV4[2]).scale(1.0 / oV4[3])
    return math.fabs(pV3[0] - oV3[0]) + math.fabs(pV3[1] - oV3[1])
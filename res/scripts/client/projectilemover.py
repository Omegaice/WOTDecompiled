# Embedded file name: scripts/client/ProjectileMover.py
import BigWorld
import Math
import math
import items
import constants
import ClientArena
import TriggersManager
import AreaDestructibles
from TriggersManager import TRIGGER_TYPE
from ClientArena import Plane
from debug_utils import *
from projectile_trajectory import computeProjectileTrajectory
from constants import DESTRUCTIBLE_MATKIND

class ProjectileMover(object):
    __PROJECTILE_HIDING_TIME = 0.05
    __PROJECTILE_TIME_AFTER_DEATH = 2.0
    __AUTO_SCALE_DISTANCE = 180.0

    def __init__(self):
        self.__projectiles = dict()
        self.__movementCallbackId = None
        return

    def destroy(self):
        if self.__movementCallbackId is not None:
            BigWorld.cancelCallback(self.__movementCallbackId)
            self.__movementCallbackId = None
        for shotID, proj in self.__projectiles.items():
            projEffects = proj['effectsDescr']['projectile'][2]
            projEffects.detachAllFrom(proj['effectsData'])
            BigWorld.player().delModel(proj['model'])
            del self.__projectiles[shotID]

        return

    def add(self, shotID, effectsDescr, gravity, refStartPoint, refVelocity, startPoint, isOwnShoot = False, tracerCameraPos = Math.Vector3(0, 0, 0)):
        import BattleReplay
        if BattleReplay.g_replayCtrl.isTimeWarpInProgress:
            return
        elif shotID in self.__projectiles:
            return
        else:
            proj = dict()
            projModelName, projModelOwnShotName, projEffects = effectsDescr['projectile']
            proj['model'] = BigWorld.Model(projModelOwnShotName if isOwnShoot else projModelName)
            proj['startTime'] = BigWorld.time()
            proj['effectsDescr'] = effectsDescr
            proj['refStartPoint'] = refStartPoint
            proj['refVelocity'] = refVelocity
            proj['startPoint'] = startPoint
            proj['stopPlane'] = None
            proj['gravity'] = Math.Vector3(0.0, -gravity, 0.0)
            proj['showExpolosion'] = False
            proj['impactVelDir'] = None
            proj['deathTime'] = None
            proj['fireMissedTrigger'] = isOwnShoot
            proj['autoScaleProjectile'] = isOwnShoot
            trajectory = self.__calcTrajectory(refStartPoint, refVelocity, proj['gravity'], isOwnShoot, tracerCameraPos)
            trajectoryEnd = trajectory[len(trajectory) - 1]
            if (trajectoryEnd[0] - startPoint).length == 0.0 or trajectoryEnd[1] == 0.0:
                LOG_CODEPOINT_WARNING()
                return
            proj['collisions'] = trajectory
            proj['velocity'] = self.__calcStartVelocity(trajectoryEnd[0], startPoint, trajectoryEnd[1], proj['gravity'])
            BigWorld.player().addModel(proj['model'])
            proj['model'].position = startPoint
            proj['model'].visible = False
            proj['model'].visibleAttachments = True
            proj['effectsData'] = {}
            projEffects.attachTo(proj['model'], proj['effectsData'], 'flying')
            if self.__movementCallbackId is None:
                self.__movementCallbackId = BigWorld.callback(0.001, self.__movementCallback)
            self.__projectiles[shotID] = proj
            return

    def hide(self, shotID, endPoint):
        proj = self.__projectiles.get(shotID, None)
        if proj is None:
            return
        else:
            proj['fireMissedTrigger'] = False
            proj['showExpolosion'] = False
            proj['stopPlane'] = self.__getStopPlane(endPoint, proj['refStartPoint'], proj['refVelocity'], proj['gravity'])
            self.__notifyProjectileHit(endPoint, proj)
            return

    def explode(self, shotID, effectsDescr, effectMaterial, endPoint, velocityDir):
        proj = self.__projectiles.get(shotID)
        if proj is None:
            self.__addExplosionEffect(endPoint, effectsDescr, effectMaterial, velocityDir)
            return
        else:
            if proj['fireMissedTrigger']:
                proj['fireMissedTrigger'] = False
                TriggersManager.g_manager.fireTrigger(TRIGGER_TYPE.PLAYER_SHOT_MISSED)
            if proj['deathTime'] is not None:
                pos = proj['model'].position
                self.__addExplosionEffect(pos, effectsDescr, effectMaterial, proj['impactVelDir'])
            else:
                proj['showExpolosion'] = True
                proj['effectMaterial'] = effectMaterial
                proj['stopPlane'] = self.__getStopPlane(endPoint, proj['refStartPoint'], proj['refVelocity'], proj['gravity'])
                nearestDist = None
                nearestCollision = None
                for p, t, d in proj['collisions']:
                    dist = (Math.Vector3(p) - Math.Vector3(endPoint)).lengthSquared
                    if dist < nearestDist or nearestDist is None:
                        nearestCollision = (p, t, d)
                        nearestDist = dist

                proj['collisions'] = [nearestCollision]
            self.__notifyProjectileHit(endPoint, proj)
            return

    def __notifyProjectileHit(self, hitPosition, proj):
        caliber = proj['effectsDescr']['caliber']
        isOwnShot = proj['autoScaleProjectile']
        BigWorld.player().inputHandler.onProjectileHit(hitPosition, caliber, isOwnShot)

    def __addExplosionEffect(self, position, effectsDescr, effectMaterial, velocityDir):
        effectTypeStr = effectMaterial + 'Hit'
        p0 = Math.Vector3(position.x, 1000, position.z)
        p1 = Math.Vector3(position.x, -1000, position.z)
        waterDist = BigWorld.wg_collideWater(p0, p1)
        if waterDist > 0:
            waterY = p0.y - waterDist
            testRes = BigWorld.wg_collideSegment(BigWorld.player().spaceID, p0, p1, 128)
            staticY = testRes[0].y if testRes is not None else waterY
            if staticY < waterY and position.y - waterY <= 0.1:
                shallowWaterDepth, rippleDiameter = effectsDescr['waterParams']
                if waterY - staticY < shallowWaterDepth:
                    effectTypeStr = 'shallowWaterHit'
                else:
                    effectTypeStr = 'deepWaterHit'
                position = Math.Vector3(position.x, waterY, position.z)
                self.__addWaterRipples(position, rippleDiameter, 5)
        stages, effects, _ = effectsDescr[effectTypeStr]
        BigWorld.player().terrainEffects.addNew(position, effects, stages, None, dir=velocityDir, start=position + velocityDir.scale(-1.0), end=position + velocityDir.scale(1.0))
        return

    def __calcTrajectory(self, r0, v0, gravity, isOwnShoot, tracerCameraPos):
        ret = []
        prevPos = r0
        prevVelocity = v0
        dt = 0.0
        while True:
            dt += constants.SERVER_TICK_LENGTH
            checkPoints = computeProjectileTrajectory(prevPos, prevVelocity, gravity, constants.SERVER_TICK_LENGTH, constants.SHELL_TRAJECTORY_EPSILON_CLIENT)
            prevCheckPoint = prevPos
            for curCheckPoint in checkPoints:
                hitPoint = BigWorld.player().arena.collideWithSpaceBB(prevCheckPoint, curCheckPoint)
                if hitPoint is not None:
                    ret.append((hitPoint, (hitPoint[0] - r0[0]) / v0[0], None))
                    return ret
                testRes = BigWorld.wg_collideSegment(BigWorld.player().spaceID, prevCheckPoint, curCheckPoint, 128)
                if testRes is not None:
                    hitPoint = testRes[0]
                    distStatic = (hitPoint - prevCheckPoint).length
                    destructibleDesc = None
                    matKind = testRes[2]
                    if matKind in xrange(DESTRUCTIBLE_MATKIND.NORMAL_MIN, DESTRUCTIBLE_MATKIND.NORMAL_MAX + 1):
                        destructibleDesc = (testRes[5], testRes[4], matKind)
                    distWater = -1.0
                    if isOwnShoot:
                        rayDir = hitPoint - tracerCameraPos
                        rayDir.normalise()
                        rayEnd = hitPoint + rayDir * 1.5
                        testRes = BigWorld.wg_collideSegment(BigWorld.player().spaceID, tracerCameraPos, rayEnd, 128)
                        if testRes is not None:
                            distStatic = (testRes[0] - tracerCameraPos).length
                            distWater = BigWorld.wg_collideWater(tracerCameraPos, rayEnd)
                    else:
                        distWater = BigWorld.wg_collideWater(prevCheckPoint, curCheckPoint)
                    if distWater < 0 or distWater > distStatic:
                        ret.append((hitPoint, self.__getCollisionTime(r0, hitPoint, v0), destructibleDesc))
                        if destructibleDesc is None:
                            return ret
                    if distWater >= 0:
                        srcPoint = tracerCameraPos if isOwnShoot else prevCheckPoint
                        hitDirection = hitPoint - srcPoint
                        hitDirection.normalise()
                        hitPoint = srcPoint + hitDirection * distWater
                        ret.append((hitPoint, self.__getCollisionTime(r0, hitPoint, v0), None))
                        return ret
                prevCheckPoint = curCheckPoint

            prevPos = r0 + v0.scale(dt) + gravity.scale(dt * dt * 0.5)
            prevVelocity = v0 + gravity.scale(dt)

        return

    def __getCollisionTime(self, startPoint, hitPoint, velocity):
        if velocity[0] != 0:
            return (hitPoint[0] - startPoint[0]) / velocity[0]
        elif velocity[2] != 0:
            return (hitPoint[2] - startPoint[2]) / velocity[2]
        else:
            return 1000000.0

    def __getStopPlane(self, point, r0, v0, gravity):
        t = (point[0] - r0[0]) / v0[0]
        v = v0 + gravity.scale(t)
        v.normalise()
        d = v.dot(point)
        return Plane(v, d)

    def __moveByTrajectory(self, proj, time):
        model = proj['model']
        gravity = proj['gravity']
        r0 = proj['startPoint']
        v0 = proj['velocity']
        dt = time - proj['startTime']
        if not model.visible and dt >= self.__PROJECTILE_HIDING_TIME:
            model.visible = True
        endPoint = None
        endTime = None
        for p, t, destrDesc in proj['collisions']:
            if dt < t:
                break
            if destrDesc is not None:
                areaDestr = AreaDestructibles.g_destructiblesManager.getController(destrDesc[0])
                if areaDestr is not None:
                    if areaDestr.isDestructibleBroken(destrDesc[1], destrDesc[2]):
                        continue
            endPoint = p
            endTime = t
            break

        if endPoint is not None:
            dir = endPoint - model.position
            dir.normalise()
            proj['impactVelDir'] = dir
            model.visible = False
            self.__setModelLocation(model, endPoint - dir.scale(0.01), dir, proj['autoScaleProjectile'])
            return True
        else:
            r = r0 + v0.scale(dt) + gravity.scale(dt * dt * 0.5)
            v = v0 + gravity.scale(dt)
            stopPlane = proj['stopPlane']
            if stopPlane is not None and stopPlane.testPoint(r):
                testRes = stopPlane.intersectSegment(model.position, r)
                if testRes is None:
                    testRes = stopPlane.intersectSegment(proj['refStartPoint'], r0)
                    if testRes is None:
                        testRes = model.position
                dir = testRes - model.position
                dir.normalise()
                proj['impactVelDir'] = dir
                model.visible = False
                self.__setModelLocation(model, testRes - dir.scale(0.01), dir, proj['autoScaleProjectile'])
                return True
            self.__setModelLocation(model, r, v, proj['autoScaleProjectile'])
            return False

    def __setModelLocation(self, model, pos, dir, autoScaleProjectile):
        model.straighten()
        model.rotate(dir.pitch, Math.Vector3(1.0, 0.0, 0.0))
        model.rotate(dir.yaw, Math.Vector3(0.0, 1.0, 0.0))
        model.position = pos
        if autoScaleProjectile:
            model.scale = self.__calcModelAutoScale(pos)

    def __calcModelAutoScale(self, modelPos):
        camera = BigWorld.camera()
        distance = (camera.position - modelPos).length
        inputHandler = BigWorld.player().inputHandler
        from AvatarInputHandler.control_modes import SniperControlMode
        if distance <= ProjectileMover.__AUTO_SCALE_DISTANCE or not isinstance(inputHandler.ctrl, SniperControlMode):
            return Math.Vector3(1, 1, 1)
        return Math.Vector3(1, 1, 1) * distance / ProjectileMover.__AUTO_SCALE_DISTANCE

    def __movementCallback(self):
        self.__movementCallbackId = None
        time = BigWorld.time()
        for shotID, proj in self.__projectiles.items():
            player = BigWorld.player()
            effectsDescr = proj['effectsDescr']
            deathTime = proj['deathTime']
            if deathTime is None and self.__moveByTrajectory(proj, time):
                proj['deathTime'] = time
                projEffects = effectsDescr['projectile'][2]
                projEffects.detachFrom(proj['effectsData'], 'stopFlying')
                if proj['showExpolosion']:
                    pos = proj['model'].position
                    dir = proj['impactVelDir']
                    self.__addExplosionEffect(pos, effectsDescr, proj['effectMaterial'], dir)
            if deathTime is not None and time - deathTime >= self.__PROJECTILE_TIME_AFTER_DEATH:
                projEffects = effectsDescr['projectile'][2]
                projEffects.detachAllFrom(proj['effectsData'])
                player.delModel(proj['model'])
                del self.__projectiles[shotID]
                if proj['fireMissedTrigger']:
                    TriggersManager.g_manager.fireTrigger(TRIGGER_TYPE.PLAYER_SHOT_MISSED)

        self.__movementCallbackId = BigWorld.callback(0.001, self.__movementCallback)
        return

    def __calcStartVelocity(self, r, r0, dt, gravity):
        v0 = (r - r0).scale(1.0 / dt) - gravity.scale(dt * 0.5)
        return v0

    def __addWaterRipples(self, position, rippleDiameter, ripplesLeft):
        BigWorld.wg_addWaterRipples(position, rippleDiameter)
        if ripplesLeft > 0:
            BigWorld.callback(0, lambda : self.__addWaterRipples(position, rippleDiameter, ripplesLeft - 1))


def collideVehicles(startPoint, endPoint, vehicles, skipGun = False):
    res = None
    dir = endPoint - startPoint
    dir.normalise()
    for vehicle in vehicles:
        collRes = vehicle.collideSegment(startPoint, endPoint, skipGun)
        if collRes is None:
            continue
        dist = collRes[0]
        if dist < startPoint.distTo(endPoint):
            endPoint = startPoint + dir * dist
            res = (vehicle,
             dist,
             collRes[1],
             collRes[2])

    return res


def collideVehiclesAndStaticScene(startPoint, endPoint, vehicles, collisionFlags = 128, skipGun = False):
    testResStatic = BigWorld.wg_collideSegment(BigWorld.player().spaceID, startPoint, endPoint, collisionFlags)
    testResDynamic = collideVehicles(startPoint, endPoint if testResStatic is None else testResStatic[0], vehicles, skipGun)
    if testResStatic is None and testResDynamic is None:
        return
    else:
        distDynamic = 1000000.0
        if testResDynamic is not None:
            distDynamic = testResDynamic[1]
        distStatic = 1000000.0
        if testResStatic is not None:
            distStatic = (testResStatic[0] - startPoint).length
        if distDynamic <= distStatic:
            dir = endPoint - startPoint
            dir.normalise()
            return (startPoint + distDynamic * dir, (testResDynamic[0], testResDynamic[2], testResDynamic[3]))
        return (testResStatic[0], None)
        return


def _getVehicles(exceptIDs):
    vehicles = []
    for vehicleID in BigWorld.player().arena.vehicles.iterkeys():
        if vehicleID in exceptIDs:
            continue
        vehicle = BigWorld.entity(vehicleID)
        if vehicle is None or not vehicle.isStarted:
            continue
        vehicles.append(vehicle)

    return vehicles


def collideDynamic(startPoint, endPoint, exceptIDs, skipGun = False):
    return collideVehicles(startPoint, endPoint, _getVehicles(exceptIDs), skipGun)


def collideDynamicAndStatic(startPoint, endPoint, exceptIDs, collisionFlags = 128, skipGun = False):
    return collideVehiclesAndStaticScene(startPoint, endPoint, _getVehicles(exceptIDs), collisionFlags, skipGun)
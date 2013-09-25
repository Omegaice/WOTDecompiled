# Embedded file name: scripts/client/gui/ClientHangarSpace.py
import BigWorld, Math, ResMgr
import copy
from debug_utils import *
from functools import partial
from gui import g_tankActiveCamouflage
import items.vehicles
import math
import time
import VehicleStickers
from PlayerEvents import g_playerEvents
from ConnectionManager import connectionManager
from ModelHitTester import ModelHitTester
from AvatarInputHandler import mathUtils
import MapActivities
_SERVER_CMD_CHANGE_HANGAR = 'cmd_change_hangar'
_SERVER_CMD_CHANGE_HANGAR_PREM = 'cmd_change_hangar_prem'
_HANGAR_UNDERGUN_EMBLEM_ANGLE_SHIFT = math.pi / 4
_CAMOUFLAGE_MIN_INTENSITY = 1.0
_CFG = {}
_DEFAULT_CFG = {}
_SPECIAL_HANGARS_CFG = {}
_EVENT_HANGAR_PATHS = {}

class ClientHangarSpace():

    def __init__(self):
        global _DEFAULT_CFG
        global _SPECIAL_HANGARS_CFG
        global _CFG
        self.__spaceId = None
        self.__cam = None
        self.__waitCallback = None
        self.__loadingStatus = 0.0
        self.__destroyFunc = None
        self.__spaceMappingId = None
        self.__onLoadedCallback = None
        self.__boundingRadius = None
        self.__vAppearance = None
        self.__vEntityId = None
        self.__selectedEmblemInfo = None
        xml = ResMgr.openSection('gui/hangars.xml')
        for type in (self.getSpaceType(False), self.getSpaceType(True)):
            cfg = {}
            self.__loadConfig(cfg, xml['defaultHangars'][type])
            self.__loadConfigValue('fakeShadowMapModelName', xml, xml.readString, cfg)
            self.__loadConfigValue('fakeShadowMapDefaultTexName', xml, xml.readString, cfg)
            self.__loadConfigValue('fakeShadowMapEmptyTexName', xml, xml.readString, cfg)
            _DEFAULT_CFG[type] = cfg

        xml = xml['specialHangars']
        for _, data in xml.items():
            if data.has_key('path'):
                _SPECIAL_HANGARS_CFG[data.readString('path')] = data

        _CFG = copy.copy(_DEFAULT_CFG[self.getSpaceType(False)])
        return

    def create(self, isPremium, onSpaceLoadedCallback = None):
        global _EVENT_HANGAR_PATHS
        global _CFG
        BigWorld.worldDrawEnabled(False)
        BigWorld.wg_setSpecialFPSMode()
        self.__onLoadedCallback = onSpaceLoadedCallback
        self.__spaceId = BigWorld.createSpace()
        type = self.getSpaceType(isPremium)
        _CFG = copy.copy(_DEFAULT_CFG[type])
        spacePath = _DEFAULT_CFG[type]['path']
        LOG_DEBUG('load hangar: hangar type = <{0:>s}>, space = <{1:>s}>'.format(type, spacePath))
        if _EVENT_HANGAR_PATHS.has_key(isPremium):
            spacePath = _EVENT_HANGAR_PATHS[isPremium]
        safeSpacePath = _DEFAULT_CFG[type]['path']
        if ResMgr.openSection(spacePath) is None:
            LOG_ERROR('Failed to load hangar from path: %s; default hangar will be loaded instead' % spacePath)
            spacePath = safeSpacePath
        try:
            self.__spaceMappingId = BigWorld.addSpaceGeometryMapping(self.__spaceId, None, spacePath)
        except:
            try:
                LOG_CURRENT_EXCEPTION()
                spacePath = safeSpacePath
                self.__spaceMappingId = BigWorld.addSpaceGeometryMapping(self.__spaceId, None, spacePath)
            except:
                BigWorld.releaseSpace(self.__spaceId)
                self.__spaceMappingId = None
                self.__spaceId = None
                LOG_CURRENT_EXCEPTION()
                return

        if _SPECIAL_HANGARS_CFG.has_key(spacePath):
            self.__loadConfig(_CFG, _SPECIAL_HANGARS_CFG[spacePath], _CFG)
        self.__vEntityId = BigWorld.createEntity('OfflineEntity', self.__spaceId, 0, _CFG['v_start_pos'], (_CFG['v_start_angles'][2], _CFG['v_start_angles'][1], _CFG['v_start_angles'][0]), dict())
        self.__vAppearance = _VehicleAppearance(self.__spaceId, self.__vEntityId)
        self.__setupCamera()
        self.__waitCallback = BigWorld.callback(0.1, self.__waitLoadingSpace)
        MapActivities.g_mapActivities.generateHangarActivities(spacePath)
        return

    def recreateVehicle(self, vDesc, vState, onVehicleLoadedCallback = None):
        if self.__vAppearance is None:
            LOG_ERROR('ClientHangarSpace.recreateVehicle failed because hangar space has not been loaded correctly.')
            return
        else:
            self.__vAppearance.recreate(vDesc, vState, onVehicleLoadedCallback)
            hitTester = vDesc.type.hull['hitTester']
            hitTester.loadBspModel()
            self.__boundingRadius = (hitTester.bbox[2] + 1) * _CFG['v_scale']
            hitTester.releaseBspModel()
            dz = 0
            if self.__cam.targetMaxDist > self.__cam.pivotMaxDist:
                dz = (self.__cam.pivotMaxDist - _CFG['cam_start_dist']) / _CFG['cam_sens']
            self.updateCameraByMouseMove(0, 0, dz)
            return

    def removeVehicle(self):
        self.__boundingRadius = None
        self.__vAppearance.destroy()
        self.__vAppearance = _VehicleAppearance(self.__spaceId, self.__vEntityId)
        BigWorld.entity(self.__vEntityId).model = None
        self.__selectedEmblemInfo = None
        return

    def moveVehicleTo(self, position):
        try:
            vehicle = BigWorld.entity(self.__vEntityId)
            vehicle.model.motors[0].signal = _createMatrix(_CFG['v_scale'], _CFG['v_start_angles'], position)
        except Exception:
            LOG_CURRENT_EXCEPTION()

    def updateVehicleCamouflage(self, camouflageID = None):
        self.__vAppearance.updateCamouflage(camouflageID=camouflageID)

    def updateVehicleSticker(self, model):
        self.__vAppearance.updateVehicleSticker(model[0], model[1])

    def destroy(self):
        if self.__waitCallback is not None and not self.spaceLoaded():
            self.__destroyFunc = self.__destroy
            return
        else:
            self.__destroy()
            return

    def handleMouseEvent(self, dx, dy, dz):
        if not self.spaceLoaded():
            return False
        self.updateCameraByMouseMove(dx, dy, dz)
        return True

    def getCamera(self):
        return self.__cam

    def getCameraLocation(self):
        sourceMat = Math.Matrix(self.__cam.source)
        targetMat = Math.Matrix(self.__cam.target)
        return {'targetPos': targetMat.translation,
         'pivotPos': self.__cam.pivotPosition,
         'yaw': sourceMat.yaw,
         'pitch': sourceMat.pitch,
         'dist': self.__cam.pivotMaxDist}

    def setCameraLocation(self, targetPos = None, pivotPos = None, yaw = None, pitch = None, dist = None, ignoreConstraints = False):
        sourceMat = Math.Matrix(self.__cam.source)
        if yaw is None:
            yaw = sourceMat.yaw
        if pitch is None:
            pitch = sourceMat.pitch
        if dist is None:
            dist = self.__cam.pivotMaxDist
        if not ignoreConstraints:
            if yaw > 2.0 * math.pi:
                yaw -= 2.0 * math.pi
            elif yaw < -2.0 * math.pi:
                yaw += 2.0 * math.pi
            pitch = mathUtils.clamp(math.radians(_CFG['cam_pitch_constr'][0]), math.radians(_CFG['cam_pitch_constr'][1]), pitch)
            dist = mathUtils.clamp(_CFG['cam_dist_constr'][0], _CFG['cam_dist_constr'][1], dist)
            if self.__boundingRadius is not None:
                dist = dist if dist > self.__boundingRadius else self.__boundingRadius
        mat = Math.Matrix()
        pitch = mathUtils.clamp(-math.pi / 2 * 0.99, math.pi / 2 * 0.99, pitch)
        mat.setRotateYPR((yaw, pitch, 0.0))
        self.__cam.source = mat
        self.__cam.pivotMaxDist = dist
        if targetPos is not None:
            self.__cam.target.setTranslate(targetPos)
        if pivotPos is not None:
            self.__cam.pivotPosition = pivotPos
        return

    def locateCameraToPreview(self):
        self.setCameraLocation(targetPos=_CFG['preview_cam_start_target_pos'], pivotPos=_CFG['preview_cam_pivot_pos'], yaw=math.radians(_CFG['preview_cam_start_angles'][0]), pitch=math.radians(_CFG['preview_cam_start_angles'][1]), dist=_CFG['preview_cam_start_dist'])

    def locateCameraOnEmblem(self, onHull, emblemType, emblemIdx, relativeSize = 0.5):
        self.__selectedEmblemInfo = (onHull,
         emblemType,
         emblemIdx,
         relativeSize)
        targetPosDirEmblem = self.__vAppearance.getEmblemPos(onHull, emblemType, emblemIdx)
        if targetPosDirEmblem is None:
            return False
        else:
            targetPos, dir, emblemDesc = targetPosDirEmblem
            emblemSize = emblemDesc[3] * _CFG['v_scale']
            halfF = emblemSize / (2 * relativeSize)
            dist = halfF / math.tan(BigWorld.projection().fov / 2)
            self.setCameraLocation(targetPos, Math.Vector3(0, 0, 0), dir.yaw, -dir.pitch, dist, True)
            return True

    def clearSelectedEmblemInfo(self):
        self.__selectedEmblemInfo = None
        return

    def updateCameraByMouseMove(self, dx, dy, dz):
        sourceMat = Math.Matrix(self.__cam.source)
        yaw = sourceMat.yaw
        pitch = sourceMat.pitch
        dist = self.__cam.pivotMaxDist
        yaw += dx * _CFG['cam_sens']
        pitch -= dy * _CFG['cam_sens']
        dist -= dz * _CFG['cam_sens']
        if yaw > 2.0 * math.pi:
            yaw -= 2.0 * math.pi
        elif yaw < -2.0 * math.pi:
            yaw += 2.0 * math.pi
        pitch = mathUtils.clamp(math.radians(_CFG['cam_pitch_constr'][0]), math.radians(_CFG['cam_pitch_constr'][1]), pitch)
        prevDist = dist
        dist = mathUtils.clamp(_CFG['cam_dist_constr'][0], _CFG['cam_dist_constr'][1], dist)
        if self.__boundingRadius is not None:
            dist = dist if dist > self.__boundingRadius else self.__boundingRadius
        if dist > prevDist and dz > 0:
            if self.__selectedEmblemInfo is not None:
                self.locateCameraOnEmblem(*self.__selectedEmblemInfo)
                return
        mat = Math.Matrix()
        mat.setRotateYPR((yaw, pitch, 0.0))
        self.__cam.source = mat
        self.__cam.pivotMaxDist = dist
        return

    def spaceLoaded(self):
        return not self.__loadingStatus < 1

    def spaceLoading(self):
        return self.__waitCallback is not None

    def getSpaceType(self, isPremium):
        if isPremium:
            return 'premium'
        return 'basic'

    def __destroy(self):
        LOG_DEBUG('Hangar successfully destroyed.')
        if self.__cam == BigWorld.camera():
            self.__cam.spaceID = 0
            BigWorld.camera(None)
            BigWorld.worldDrawEnabled(False)
        self.__cam = None
        self.__loadingStatus = 0.0
        if self.__vAppearance is not None:
            self.__vAppearance.destroy()
            self.__vAppearance = None
        self.__onLoadedCallback = None
        self.__boundingRadius = None
        entity = None if self.__vEntityId is None else BigWorld.entity(self.__vEntityId)
        BigWorld.SetDrawInflux(False)
        MapActivities.g_mapActivities.stop()
        if self.__spaceId is not None and BigWorld.isClientSpace(self.__spaceId):
            if self.__spaceMappingId is not None:
                BigWorld.delSpaceGeometryMapping(self.__spaceId, self.__spaceMappingId)
            BigWorld.clearSpace(self.__spaceId)
            BigWorld.releaseSpace(self.__spaceId)
        self.__spaceMappingId = None
        self.__spaceId = None
        if entity is None or not entity.inWorld:
            return
        else:
            BigWorld.destroyEntity(self.__vEntityId)
            self.__vEntityId = None
            BigWorld.wg_disableSpecialFPSMode()
            return

    def __setupCamera(self):
        self.__cam = BigWorld.CursorCamera()
        self.__cam.spaceID = self.__spaceId
        self.__cam.pivotMaxDist = _CFG['cam_start_dist']
        self.__cam.pivotMinDist = 0.0
        self.__cam.maxDistHalfLife = _CFG['cam_fluency']
        self.__cam.turningHalfLife = _CFG['cam_fluency']
        self.__cam.movementHalfLife = 0.0
        self.__cam.pivotPosition = _CFG['cam_pivot_pos']
        mat = Math.Matrix()
        mat.setRotateYPR((math.radians(_CFG['cam_start_angles'][0]), math.radians(_CFG['cam_start_angles'][1]), 0.0))
        self.__cam.source = mat
        mat = Math.Matrix()
        mat.setTranslate(_CFG['cam_start_target_pos'])
        self.__cam.target = mat
        BigWorld.camera(self.__cam)
        from gui.WindowsManager import g_windowsManager
        container = g_windowsManager.window.containerManager.getContainer('lobbySubView')
        from gui.Scaleform.daapi.settings.views import VIEW_ALIAS
        if container is not None and container.getView().uniqueName == VIEW_ALIAS.LOBBY_CUSTOMIZATION:
            self.locateCameraToPreview()
        return

    def __waitLoadingSpace(self):
        self.__waitCallback = None
        self.__loadingStatus = BigWorld.spaceLoadStatus()
        if self.__loadingStatus < 1:
            self.__waitCallback = BigWorld.callback(0.1, self.__waitLoadingSpace)
        else:
            BigWorld.worldDrawEnabled(True)
            BigWorld.wg_multiplyChunkModelScale(BigWorld.camera().spaceID, 0, 0, _CFG['fakeShadowMapModelName'], Math.Vector3(_CFG['v_scale'], 1.0, _CFG['v_scale']))
            if self.__onLoadedCallback is not None:
                self.__onLoadedCallback()
                self.__onLoadedCallback = None
            if self.__destroyFunc:
                self.__destroyFunc()
                self.__destroyFunc = None
        return

    def __loadConfig(self, cfg, xml, defaultCfg = None):
        if defaultCfg is None:
            defaultCfg = cfg
        self.__loadConfigValue('path', xml, xml.readString, cfg, defaultCfg)
        self.__loadConfigValue('v_scale', xml, xml.readFloat, cfg, defaultCfg)
        self.__loadConfigValue('v_start_angles', xml, xml.readVector3, cfg, defaultCfg)
        self.__loadConfigValue('v_start_pos', xml, xml.readVector3, cfg, defaultCfg)
        self.__loadConfigValue('cam_start_target_pos', xml, xml.readVector3, cfg, defaultCfg)
        self.__loadConfigValue('cam_start_dist', xml, xml.readFloat, cfg, defaultCfg)
        self.__loadConfigValue('cam_start_angles', xml, xml.readVector2, cfg, defaultCfg)
        self.__loadConfigValue('cam_dist_constr', xml, xml.readVector2, cfg, defaultCfg)
        self.__loadConfigValue('cam_pitch_constr', xml, xml.readVector2, cfg, defaultCfg)
        self.__loadConfigValue('cam_sens', xml, xml.readFloat, cfg, defaultCfg)
        self.__loadConfigValue('cam_pivot_pos', xml, xml.readVector3, cfg, defaultCfg)
        self.__loadConfigValue('cam_fluency', xml, xml.readFloat, cfg, defaultCfg)
        self.__loadConfigValue('emblems_alpha_damaged', xml, xml.readFloat, cfg, defaultCfg)
        self.__loadConfigValue('emblems_alpha_undamaged', xml, xml.readFloat, cfg, defaultCfg)
        self.__loadConfigValue('shadow_light_dir', xml, xml.readVector3, cfg, defaultCfg)
        self.__loadConfigValue('preview_cam_start_dist', xml, xml.readFloat, cfg, defaultCfg)
        self.__loadConfigValue('preview_cam_start_angles', xml, xml.readVector2, cfg, defaultCfg)
        self.__loadConfigValue('preview_cam_pivot_pos', xml, xml.readVector3, cfg, defaultCfg)
        self.__loadConfigValue('preview_cam_start_target_pos', xml, xml.readVector3, cfg, defaultCfg)
        for i in range(0, 3):
            cfg['v_start_angles'][i] = math.radians(cfg['v_start_angles'][i])

        return

    def __loadConfigValue(self, name, xml, fn, cfg, defaultCfg = None):
        if xml.has_key(name):
            cfg[name] = fn(name)
        else:
            cfg[name] = defaultCfg.get(name) if defaultCfg is not None else None
        return


class _VehicleAppearance():
    __ROOT_NODE_NAME = 'V'

    def __init__(self, spaceId, vEntityId):
        self.__isLoaded = False
        self.__curBuildInd = 0
        self.__vDesc = None
        self.__spaceId = spaceId
        self.__vEntityId = vEntityId
        self.__onLoadedCallback = None
        self.__emblemsAlpha = _CFG['emblems_alpha_undamaged']
        self.__models = ()
        self.__stickers = []
        self.__isVehicleDestroyed = False
        self.__smCb = None
        self.__smRemoveCb = None
        self.__removeHangarShadowMap()
        return

    def recreate(self, vDesc, vState, onVehicleLoadedCallback = None):
        self.__onLoadedCallback = onVehicleLoadedCallback
        self.__isLoaded = False
        self.__startBuild(vDesc, vState)

    def destroy(self):
        self.__onLoadedCallback = None
        self.__vDesc = None
        self.__isLoaded = False
        self.__curBuildInd = 0
        self.__vEntityId = None
        if self.__smCb is not None:
            BigWorld.cancelCallback(self.__smCb)
            self.__smCb = None
        if self.__smRemoveCb is not None:
            BigWorld.cancelCallback(self.__smRemoveCb)
            self.__smRemoveCb = None
        return

    def isLoaded(self):
        return self.__isLoaded

    def __startBuild(self, vDesc, vState):
        self.__curBuildInd += 1
        self.__vDesc = vDesc
        self.__resources = {}
        self.__stickers = []
        self.__componentIDs = {'chassis': vDesc.chassis['models'][vState],
         'hull': vDesc.hull['models'][vState],
         'turret': vDesc.turret['models'][vState],
         'gun': vDesc.gun['models'][vState],
         'camouflageExclusionMask': vDesc.type.camouflageExclusionMask}
        customization = items.vehicles.g_cache.customization(vDesc.type.id[0])
        if customization is not None and vDesc.camouflages is not None:
            camouflageID = vDesc.camouflages[g_tankActiveCamouflage.get(vDesc.type.compactDescr, 0)][0]
            camouflageDesc = customization['camouflages'].get(camouflageID)
            if camouflageDesc is not None:
                self.__componentIDs['camouflageTexture'] = camouflageDesc['texture']
        if vState == 'undamaged':
            self.__emblemsAlpha = _CFG['emblems_alpha_undamaged']
            self.__isVehicleDestroyed = False
        else:
            self.__emblemsAlpha = _CFG['emblems_alpha_damaged']
            self.__isVehicleDestroyed = True
        resources = self.__componentIDs.values()
        BigWorld.loadResourceListBG(tuple(resources), partial(self.__onResourcesLoaded, self.__curBuildInd))
        return

    def __onResourcesLoaded(self, buildInd, resourceRefs):
        if buildInd != self.__curBuildInd:
            return
        failedIDs = resourceRefs.failedIDs
        resources = self.__resources
        succesLoaded = True
        for resID, resource in resourceRefs.items():
            if resID not in failedIDs:
                resources[resID] = resource
            else:
                LOG_ERROR('Could not load %s' % resID)
                succesLoaded = False

        if succesLoaded:
            self.__setupModel(buildInd)

    def __assembleModel(self):
        resources = self.__resources
        compIDs = self.__componentIDs
        chassis = resources[compIDs['chassis']]
        hull = resources[compIDs['hull']]
        turret = resources[compIDs['turret']]
        gun = resources[compIDs['gun']]
        self.__models = (chassis,
         hull,
         turret,
         gun)
        chassis.node(self.__ROOT_NODE_NAME).attach(hull)
        hull.node('HP_turretJoint').attach(turret)
        turret.node('HP_gunJoint').attach(gun)
        self.__setupEmblems(self.__vDesc)
        for sticker, alpha in self.__stickers:
            sticker.setAlphas(0, 0)

        for model in self.__models:
            model.visible = False
            model.visibleAttachments = True

        return chassis

    def __removeHangarShadowMap(self):
        if self.__smCb is not None:
            BigWorld.cancelCallback(self.__smCb)
            self.__smCb = None
        if BigWorld.spaceLoadStatus() < 1.0:
            self.__smRemoveCb = BigWorld.callback(0, self.__removeHangarShadowMap)
            return
        else:
            self.__smRemoveCb = None
            BigWorld.wg_setChunkModelTexture(BigWorld.camera().spaceID, 0, 0, _CFG['fakeShadowMapModelName'], 'diffuseMap', _CFG['fakeShadowMapEmptyTexName'])
            return

    def __setupHangarShadowMap(self):
        if self.__smRemoveCb is not None:
            BigWorld.cancelCallback(self.__smRemoveCb)
            self.__smRemoveCb = None
        if BigWorld.spaceLoadStatus() < 1.0:
            self.__smCb = BigWorld.callback(0, self.__setupHangarShadowMap)
            return
        else:
            self.__smCb = None
            if 'observer' in self.__vDesc.type.tags:
                self.__removeHangarShadowMap()
                return
            vehiclePath = self.__vDesc.chassis['models']['undamaged']
            vehiclePath = vehiclePath[:vehiclePath.rfind('/normal')]
            dsVehicle = ResMgr.openSection(vehiclePath)
            shadowMapTexFileName = _CFG['fakeShadowMapDefaultTexName']
            if dsVehicle is not None:
                for fileName, _ in dsVehicle.items():
                    if fileName.lower().find('_hangarshadowmap.dds') != -1:
                        shadowMapTexFileName = vehiclePath + '/' + fileName

            BigWorld.wg_setChunkModelTexture(BigWorld.camera().spaceID, 0, 0, _CFG['fakeShadowMapModelName'], 'diffuseMap', shadowMapTexFileName)
            return

    def __setupEmblems(self, vDesc):
        for vehicleStickers, _ in self.__stickers:
            vehicleStickers.detachStickers()

        self.__stickers = []
        chassis = self.__models[0]
        hull = self.__models[1]
        turret = self.__models[2]
        gun = self.__models[3]
        emblemAlpha = self.__emblemsAlpha * vDesc.type.emblemsAlpha
        emblemPositions = ((hull, chassis.node(self.__ROOT_NODE_NAME), vDesc.hull['emblemSlots']), (gun if vDesc.turret['showEmblemsOnGun'] else turret, hull.node('HP_turretJoint'), vDesc.turret['emblemSlots']))
        for targetModel, parentNode, slots in emblemPositions:
            sticker = VehicleStickers.VehicleStickers(vDesc, slots, targetModel == hull, self.__resources)
            sticker.setAlphas(emblemAlpha, emblemAlpha)
            sticker.attachStickers(targetModel, parentNode, self.__isVehicleDestroyed)
            self.__stickers.append((sticker, emblemAlpha))

        BigWorld.player().stats.get('clanDBID', self.__onClanDBIDRetrieved)

    def updateVehicleSticker(self, playerEmblems, playerInscriptions):
        initialEmblems = copy.deepcopy(self.__vDesc.playerEmblems)
        initialInscriptions = copy.deepcopy(self.__vDesc.playerInscriptions)
        for idx, (emblemId, startTime, duration) in enumerate(playerEmblems):
            self.__vDesc.setPlayerEmblem(idx, emblemId, startTime, duration)

        for idx, (inscriptionId, startTime, duration, color) in enumerate(playerInscriptions):
            self.__vDesc.setPlayerInscription(idx, inscriptionId, startTime, duration, color)

        self.__setupEmblems(self.__vDesc)
        self.__vDesc.playerEmblems = initialEmblems
        self.__vDesc.playerInscriptions = initialInscriptions

    def __onClanDBIDRetrieved(self, _, clanID):
        for sticker, _ in self.__stickers:
            sticker.setClanID(clanID)

    def __setupModel(self, buildIdx):
        model = self.__assembleModel()
        model.addMotor(BigWorld.Servo(_createMatrix(_CFG['v_scale'], _CFG['v_start_angles'], _CFG['v_start_pos'])))
        BigWorld.addModel(model)
        BigWorld.callback(0.0, partial(self.__doFinalSetup, buildIdx, model, True))

    def __doFinalSetup(self, buildIdx, model, delModel):
        if delModel:
            BigWorld.delModel(model)
        if model.attached:
            BigWorld.callback(0.0, partial(self.__doFinalSetup, buildIdx, model, False))
            return
        elif buildIdx != self.__curBuildInd:
            return
        else:
            entity = BigWorld.entity(self.__vEntityId)
            if entity:
                for m in self.__models:
                    m.visible = True
                    m.visibleAttachments = True

                for sticker, alpha in self.__stickers:
                    sticker.setAlphas(alpha, alpha)

                entity.model = model
                entity.model.delMotor(entity.model.motors[0])
                entity.model.addMotor(BigWorld.Servo(_createMatrix(_CFG['v_scale'], _CFG['v_start_angles'], _CFG['v_start_pos'])))
                if self.__onLoadedCallback is not None:
                    self.__onLoadedCallback()
                    self.__onLoadedCallback = None
                self.updateCamouflage()
                if self.__smCb is None:
                    self.__setupHangarShadowMap()
            if self.__vDesc is not None and 'observer' in self.__vDesc.type.tags:
                model.visible = False
                model.visibleAttachments = False
            return

    def getEmblemPos(self, onHull, emblemType, emblemIdx):
        model = None
        emblemsDesc = None
        hitTester = ModelHitTester()
        worldMat = None
        chassis = self.__models[0]
        if onHull:
            model = self.__models[1]
            hitTester.bspModelName = self.__vDesc.hull['models']['undamaged']
            emblemsDesc = self.__vDesc.hull['emblemSlots']
            worldMat = Math.Matrix(model.matrix)
        else:
            if self.__vDesc.turret['showEmblemsOnGun']:
                model = self.__models[3]
                hitTester.bspModelName = self.__vDesc.gun['models']['undamaged']
            else:
                model = self.__models[2]
                hitTester.bspModelName = self.__vDesc.turret['models']['undamaged']
            emblemsDesc = self.__vDesc.turret['emblemSlots']
            worldMat = Math.Matrix(model.matrix)
        if model is None:
            return
        else:
            desiredEmblems = [ emblem for emblem in emblemsDesc if emblem[5] == emblemType ]
            if emblemIdx >= len(desiredEmblems):
                return
            emblem = desiredEmblems[emblemIdx]
            dir = emblem[1] - emblem[0]
            dir.normalise()
            startPos = emblem[0] - dir * 5
            endPos = emblem[1] + dir * 5
            hitTester.loadBspModel()
            collideRes = hitTester.localHitTest(startPos, endPos)
            hitTester.releaseBspModel()
            if collideRes is not None:
                collideRes = sorted(collideRes, lambda t1, t2: cmp(t1[0], t2[0]))
                distanceFromStart, normal = collideRes[0][0], collideRes[0][1]
                hitPos = startPos + dir * distanceFromStart
                hitPos = worldMat.applyPoint(hitPos)
                dir = -worldMat.applyVector(normal)
                dir.normalise()
                upVecWorld = worldMat.applyVector(emblem[2])
                upVecWorld.normalise()
                if abs(dir.pitch - math.pi / 2) < 0.1:
                    dir = Math.Vector3(0, -1, 0) + upVecWorld * 0.01
                    dir.normalise()
                dir = self.__correctEmblemLookAgainstGun(hitPos, dir, upVecWorld, emblem)
                return (hitPos, dir, emblem)
            return
            return

    def __getEmblemCorners(self, hitPos, dir, up, emblem):
        size = emblem[3] * _CFG['v_scale']
        m = Math.Matrix()
        m.lookAt(hitPos, dir, up)
        m.invert()
        result = (Math.Vector3(size * 0.5, size * 0.5, -0.25),
         Math.Vector3(size * 0.5, -size * 0.5, -0.25),
         Math.Vector3(-size * 0.5, -size * 0.5, -0.25),
         Math.Vector3(-size * 0.5, size * 0.5, -0.25))
        return [ m.applyPoint(vec) for vec in result ]

    def __correctEmblemLookAgainstGun(self, hitPos, dir, up, emblem):
        turretModel = self.__models[2]
        gunModel = self.__models[3]
        hitTester = self.__vDesc.gun['hitTester']
        hitTester.loadBspModel()
        toLocalGun = Math.Matrix(gunModel.matrix)
        toLocalGun.invert()
        checkDirLocal = toLocalGun.applyVector(dir) * -10
        cornersLocal = self.__getEmblemCorners(hitPos, dir, up, emblem)
        cornersLocal = [ toLocalGun.applyPoint(vec) for vec in cornersLocal ]
        testResult = hitTester.localCollidesWithTriangle((cornersLocal[0], cornersLocal[2], cornersLocal[1]), checkDirLocal)
        if not testResult:
            testResult = hitTester.localCollidesWithTriangle((cornersLocal[0], cornersLocal[3], cornersLocal[2]), checkDirLocal)
            hitTester.releaseBspModel()
            if not testResult:
                return dir
            dirRot = Math.Matrix()
            angle = _HANGAR_UNDERGUN_EMBLEM_ANGLE_SHIFT
            turretMat = Math.Matrix(turretModel.matrix)
            fromTurretToHit = hitPos - turretMat.translation
            gunDir = turretMat.applyVector(Math.Vector3(0, 0, 1))
            angle = Math.Vector3(0, 1, 0).dot(gunDir * fromTurretToHit) < 0 and -angle
        dirRot.setRotateY(angle)
        normRot = Math.Matrix()
        normRot.setRotateYPR((dir.yaw, dir.pitch, 0))
        dirRot.postMultiply(normRot)
        dir = dirRot.applyVector(Math.Vector3(0, 0, 1))
        return dir

    def updateCamouflage(self, camouflageID = None):
        texture = ''
        colors = [0,
         0,
         0,
         0]
        weights = Math.Vector4(1, 0, 0, 0)
        camouflagePresent = True
        vDesc = self.__vDesc
        if vDesc is None:
            return
        else:
            if camouflageID is None and vDesc.camouflages is not None:
                camouflageID = vDesc.camouflages[g_tankActiveCamouflage.get(vDesc.type.compactDescr, 0)][0]
            if camouflageID is None:
                for camouflageData in vDesc.camouflages:
                    if camouflageData[0] is not None:
                        camouflageID = camouflageData[0]
                        break

            customization = items.vehicles.g_cache.customization(vDesc.type.id[0])
            defaultTiling = None
            if camouflageID is not None and customization is not None:
                camouflage = customization['camouflages'].get(camouflageID)
                if camouflage is not None:
                    camouflagePresent = True
                    texture = camouflage['texture']
                    colors = camouflage['colors']
                    weights = Math.Vector4((colors[0] >> 24) / 255.0, (colors[1] >> 24) / 255.0, (colors[2] >> 24) / 255.0, (colors[3] >> 24) / 255.0)
                    defaultTiling = camouflage['tiling'].get(vDesc.type.compactDescr)
            if self.__isVehicleDestroyed:
                weights *= 0.1
            if vDesc.camouflages is not None:
                _, camStartTime, camNumDays = vDesc.camouflages[g_tankActiveCamouflage.get(vDesc.type.compactDescr, 0)]
                if camNumDays > 0:
                    timeAmount = (time.time() - camStartTime) / (camNumDays * 86400)
                    if timeAmount > 1.0:
                        weights *= _CAMOUFLAGE_MIN_INTENSITY
                    elif timeAmount > 0:
                        weights *= (1.0 - timeAmount) * (1.0 - _CAMOUFLAGE_MIN_INTENSITY) + _CAMOUFLAGE_MIN_INTENSITY
            for model in self.__models:
                exclusionMap = vDesc.type.camouflageExclusionMask
                tiling = defaultTiling
                if tiling is None:
                    tiling = vDesc.type.camouflageTiling
                tgDesc = None
                if model == self.__models[2]:
                    tgDesc = vDesc.turret
                elif model == self.__models[3]:
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
                if not camouflagePresent or exclusionMap == '' or texture == '':
                    if hasattr(model, 'wg_fashion'):
                        delattr(model, 'wg_fashion')
                else:
                    if not hasattr(model, 'wg_fashion'):
                        if model == self.__models[0]:
                            tracksCfg = vDesc.chassis['tracks']
                            fashion = BigWorld.WGVehicleFashion()
                            fashion.setTracks(tracksCfg['leftMaterial'], tracksCfg['rightMaterial'], tracksCfg['textureScale'])
                            model.wg_fashion = fashion
                        else:
                            model.wg_fashion = BigWorld.WGBaseFashion()
                    model.wg_fashion.setCamouflage(texture, exclusionMap, tiling, colors[0], colors[1], colors[2], colors[3], weights)

            return


class _ClientHangarSpacePathOverride():

    def __init__(self):
        g_playerEvents.onEventNotificationsChanged += self.__onEventNotificationsChanged
        connectionManager.onDisconnected += self.__onDisconnected

    def destroy(self):
        g_playerEvents.onEventNotificationsChanged -= self.__onEventNotificationsChanged
        connectionManager.onDisconnected -= self.__onDisconnected

    def __onDisconnected(self):
        global _EVENT_HANGAR_PATHS
        _EVENT_HANGAR_PATHS = {}

    def __onEventNotificationsChanged(self, notificationsDiff):
        from gui.shared.utils.HangarSpace import g_hangarSpace
        isPremium = g_hangarSpace.isPremium
        hasChanged = False
        for notification in notificationsDiff['removed']:
            if notification['type'] == _SERVER_CMD_CHANGE_HANGAR:
                del _EVENT_HANGAR_PATHS[False]
                if not isPremium:
                    hasChanged = True
            elif notification['type'] == _SERVER_CMD_CHANGE_HANGAR_PREM:
                del _EVENT_HANGAR_PATHS[True]
                if isPremium:
                    hasChanged = True

        for notification in notificationsDiff['added']:
            if not notification.has_key('data') or notification['data'] == '':
                continue
            if notification['type'] == _SERVER_CMD_CHANGE_HANGAR:
                _EVENT_HANGAR_PATHS[False] = notification['data']
                if not isPremium:
                    hasChanged = True
            elif notification['type'] == _SERVER_CMD_CHANGE_HANGAR_PREM:
                _EVENT_HANGAR_PATHS[True] = notification['data']
                if isPremium:
                    hasChanged = True

        if hasChanged:
            g_hangarSpace.refreshSpace(isPremium, True)


g_clientHangarSpaceOverride = _ClientHangarSpacePathOverride()

def _createMatrix(scale, angles, pos):
    mat = Math.Matrix()
    mat.setScale((scale, scale, scale))
    mat2 = Math.Matrix()
    mat2.setTranslate(pos)
    mat3 = Math.Matrix()
    mat3.setRotateYPR(angles)
    mat.preMultiply(mat3)
    mat.postMultiply(mat2)
    return mat
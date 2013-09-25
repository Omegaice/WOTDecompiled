import BigWorld
import Math
import Pixie
from Math import Vector3, Matrix
import math
import helpers
import material_kinds

class VehicleTrailEffects():
    _DRAW_ORDER_IDX = 102
    enabled = property(lambda self: self.__enabled)

    def __init__(self, vehicle):
        self.__vehicle = vehicle
        chassisModel = self.__vehicle.appearance.modelsDesc['chassis']['model']
        topRightCarryingPoint = self.__vehicle.typeDescriptor.chassis['topRightCarryingPoint']
        self.__enabled = True
        self.__trailParticleNodes = []
        self.__trailParticles = {}
        mMidLeft = Math.Matrix()
        mMidLeft.setTranslate((-topRightCarryingPoint[0], 0, 0))
        mMidRight = Math.Matrix()
        mMidRight.setTranslate((topRightCarryingPoint[0], 0, 0))
        self.__trailParticleNodes = [chassisModel.node('', mMidLeft), chassisModel.node('', mMidRight)]
        i = 0
        for nodeName in ('HP_Track_LFront', 'HP_Track_RFront', 'HP_Track_LRear', 'HP_Track_RRear'):
            node = None
            try:
                identity = Math.Matrix()
                identity.setIdentity()
                node = chassisModel.node(nodeName, identity)
            except:
                matr = mMidLeft if i % 2 == 0 else mMidRight
                node = chassisModel.node('', Math.Matrix(matr))

            self.__trailParticleNodes.append(node)

        identity = Math.Matrix()
        identity.setIdentity()
        self.__centerNode = chassisModel.node('', identity)
        self.__trailParticlesDelayBeforeShow = BigWorld.time() + 4.0
        return

    def destroy(self):
        self.stopEffects()
        self.__trailParticleNodes = None
        self.__trailParticles = None
        self.__centerNode = None
        self.__vehicle = None
        return

    def getTrackCenterNode(self, trackIdx):
        return self.__trailParticleNodes[trackIdx]

    def enable(self, isEnabled):
        if self.__enabled and not isEnabled:
            self.stopEffects()
        self.__enabled = isEnabled

    def stopEffects(self):
        for node in self.__trailParticles.iterkeys():
            for trail in self.__trailParticles[node]:
                node.detach(trail[0])

        self.__trailParticles = {}

    def update(self):
        vehicle = self.__vehicle
        vehicleAppearance = self.__vehicle.appearance
        if not self.__enabled:
            return
        elif vehicle.typeDescriptor.chassis['effects'] is None:
            self.__enabled = False
            return
        else:
            time = BigWorld.time()
            if time < self.__trailParticlesDelayBeforeShow:
                return
            movementInfo = Math.Vector4(vehicleAppearance.fashion.movementInfo.value)
            vehicleSpeedRel = vehicle.filter.speedInfo.value[2] / vehicle.typeDescriptor.physics['speedLimits'][0]
            tooSlow = abs(vehicleSpeedRel) < 0.1
            waterHeight = None if not vehicleAppearance.isInWater else vehicleAppearance.waterHeight
            effectIndexes = self.__getEffectIndexesUnderVehicle(vehicleAppearance)
            self.__updateNodePosition(self.__centerNode, vehicle.position, waterHeight)
            centerEffectIdx = effectIndexes[2]
            if not tooSlow and not vehicleAppearance.isUnderwater:
                self.__createTrailParticlesIfNeeded(self.__centerNode, 0, 'dust', centerEffectIdx, VehicleTrailEffects._DRAW_ORDER_IDX, True)
            centerNodeEffects = self.__trailParticles.get(self.__centerNode)
            if centerNodeEffects is not None:
                for nodeEffect in centerNodeEffects:
                    stopParticles = nodeEffect[1] != centerEffectIdx or vehicleAppearance.isUnderwater or tooSlow
                    self.__updateNodeEffect(nodeEffect, self.__centerNode, centerNodeEffects, vehicleSpeedRel, stopParticles)

            for iTrack in xrange(2):
                trackSpeedRel = movementInfo[iTrack + 1]
                trackSpeedRel = 0.0 if trackSpeedRel == 0 else abs(vehicleSpeedRel) * trackSpeedRel / abs(trackSpeedRel)
                activeCornerNode = self.__trailParticleNodes[2 + iTrack + (0 if trackSpeedRel <= 0 else 2)]
                inactiveCornerNode = self.__trailParticleNodes[2 + iTrack + (0 if trackSpeedRel > 0 else 2)]
                self.__updateNodePosition(activeCornerNode, vehicle.position, waterHeight)
                self.__updateNodePosition(inactiveCornerNode, vehicle.position, waterHeight)
                currEffectIndex = effectIndexes[iTrack]
                if not tooSlow and not vehicleAppearance.isUnderwater:
                    self.__createTrailParticlesIfNeeded(activeCornerNode, iTrack, 'mud', currEffectIndex, VehicleTrailEffects._DRAW_ORDER_IDX + iTrack, True)
                    self.__createTrailParticlesIfNeeded(inactiveCornerNode, iTrack, 'mud', currEffectIndex, VehicleTrailEffects._DRAW_ORDER_IDX + iTrack, False)
                for node in (activeCornerNode, inactiveCornerNode):
                    nodeEffects = self.__trailParticles.get(node)
                    if nodeEffects is not None:
                        for nodeEffect in nodeEffects:
                            createdForActiveNode = nodeEffect[5]
                            stopParticlesOnDirChange = node == activeCornerNode and not createdForActiveNode or node == inactiveCornerNode and createdForActiveNode
                            stopParticles = nodeEffect[1] != currEffectIndex or stopParticlesOnDirChange or vehicleAppearance.isUnderwater or tooSlow
                            self.__updateNodeEffect(nodeEffect, node, nodeEffects, trackSpeedRel, stopParticles)

            return

    def __getEffectIndexesUnderVehicle(self, vehicleAppearance):
        correctedMatKinds = [ (material_kinds.WATER_MATERIAL_KIND if vehicleAppearance.isInWater else matKind) for matKind in vehicleAppearance.terrainMatKind ]
        return map(helpers.calcEffectMaterialIndex, correctedMatKinds)

    def __updateNodePosition(self, node, vehiclePos, waterHeight):
        if waterHeight is not None:
            toCenterShift = vehiclePos.y - (Math.Matrix(node).translation.y - node.local.translation.y)
            node.local.translation = Math.Vector3(0, waterHeight + toCenterShift, 0)
        else:
            node.local.translation = Math.Vector3(0, 0, 0)
        return

    def __createTrailParticlesIfNeeded(self, node, iTrack, effectGroup, effectIndex, drawOrder, isActiveNode):
        if effectIndex is None:
            return
        else:
            effectDesc = self.__vehicle.typeDescriptor.chassis['effects'].get(effectGroup)
            if effectDesc is None:
                return
            effectName = effectDesc[0].get(effectIndex)
            if effectName is None or effectName == 'none' or effectName == 'None':
                return
            if isinstance(effectName, list):
                effectIdx = iTrack
                effectIdx += 0 if isActiveNode else 2
                effectName = effectName[effectIdx]
            nodeEffects = self.__trailParticles.get(node)
            if nodeEffects is None:
                nodeEffects = []
                self.__trailParticles[node] = nodeEffects
            else:
                for nodeEffect in nodeEffects:
                    createdForActiveNode = nodeEffect[5]
                    if nodeEffect[1] == effectIndex and createdForActiveNode == isActiveNode:
                        return

            pixie = Pixie.create(effectName)
            pixie.drawOrder = drawOrder
            node.attach(pixie)
            basicRates = []
            for i in xrange(pixie.nSystems()):
                try:
                    source = pixie.system(i).action(1)
                    basicRates.append(source.rate)
                    source.rate = source.rate * 0.001
                except:
                    basicRates.append(-1.0)
                    source = pixie.system(i).action(16)
                    source.MultRate(0.01)

            nodeEffects.append([pixie,
             effectIndex,
             0,
             0,
             basicRates,
             isActiveNode])
            return

    def __updateNodeEffect(self, nodeEffect, node, nodeEffects, relSpeed, stopParticles):
        relEmissionRate = 0.0 if stopParticles else abs(relSpeed)
        basicEmissionRates = nodeEffect[4]
        pixie = nodeEffect[0]
        for i in xrange(pixie.nSystems()):
            if basicEmissionRates[i] < 0:
                source = pixie.system(i).action(16)
                source.MultRate(relEmissionRate)
            else:
                source = pixie.system(i).action(1)
                source.rate = relEmissionRate * basicEmissionRates[i]

        effectInactive = relEmissionRate < 0.0001
        if effectInactive:
            time = BigWorld.time()
            timeOfStop = nodeEffect[3]
            if timeOfStop == 0:
                nodeEffect[3] = time
            elif time - timeOfStop > 5.0 or material_kinds.EFFECT_MATERIALS[nodeEffect[1]] == 'water':
                pixie = nodeEffect[0]
                node.detach(pixie)
                nodeEffects.remove(nodeEffect)
        else:
            nodeEffect[3] = 0


class VehicleExhaustEffects():
    enabled = property(lambda self: self.__enabled)

    def __init__(self, vehicleTypeDescriptor):
        self.__enabled = True
        self.__exhaust = []
        exhaust = vehicleTypeDescriptor.hull['exhaust']
        engineTags = vehicleTypeDescriptor.engine['tags']
        pixieName = None
        for tag in engineTags:
            pixieName = exhaust.get('pixie/' + tag, pixieName)

        rates = exhaust['rates']
        for i in xrange(len(exhaust['nodes'])):
            pixie = Pixie.create(pixieName)
            pixie.drawOrder = 50 + i
            self.__exhaust.append([None, pixie])
            for i in xrange(pixie.nSystems()):
                source = pixie.system(i).action(1)
                source.rate = rates[0]

        return

    def destroy(self):
        for _, pixie in self.__exhaust:
            pixie.clear()

        self.__exhaust = []

    def enable(self, isEnabled):
        self.__enabled = isEnabled

    def attach(self, hullModel, nodes, attachEffects):
        if attachEffects:
            for i in xrange(len(nodes)):
                node, pixie = self.__exhaust[i]
                node = hullModel.node(nodes[i])
                node.attach(pixie)

        else:
            for node, pixie in self.__exhaust:
                if node is not None:
                    node.detach(pixie)

        return

    def changeExhaust(self, vehicleTypeDescriptor, engineMode):
        rates = vehicleTypeDescriptor.hull['exhaust']['rates']
        for pair in self.__exhaust:
            pixie = pair[1]
            for i in xrange(pixie.nSystems()):
                source = pixie.system(i).action(1)
                source.rate = rates[engineMode] if self.__enabled else 0

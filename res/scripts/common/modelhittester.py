# Embedded file name: scripts/common/ModelHitTester.py
import math
import BigWorld
from Math import Vector3, Vector2, Matrix
from debug_utils import *

class ModelHitTester(object):
    bbox = None

    def __setBspModelName(self, value):
        self.releaseBspModel()
        self.__bspModelName = value

    bspModelName = property(lambda self: self.__bspModelName, __setBspModelName)

    def __init__(self, dataSection = None):
        self.__bspModel = None
        self.__bspModelName = None
        if dataSection is not None:
            self.__bspModelName = dataSection.readString('collisionModel')
            if not self.__bspModelName:
                raise Exception, '<collisionModel> is missing or wrong'
        return

    def isBspModelLoaded(self):
        return self.__bspModel is not None

    def loadBspModel(self):
        if self.__bspModel is not None:
            return
        else:
            bspModel = BigWorld.WGBspCollisionModel()
            if not bspModel.setModelName(self.bspModelName):
                raise Exception, "wrong collision model '%s'" % self.bspModelName
            self.__bspModel = bspModel
            self.bbox = bspModel.getBoundingBox()
            return

    def releaseBspModel(self):
        if self.__bspModel is not None:
            self.__bspModel = None
            del self.bbox
        return

    def localAnyHitTest(self, start, stop):
        return self.__bspModel.collideSegmentAny(start, stop)

    def localHitTest(self, start, stop):
        return self.__bspModel.collideSegment(start, stop)

    def worldHitTest(self, start, stop, worldMatrix):
        worldToLocal = Matrix(worldMatrix)
        worldToLocal.invert()
        testRes = self.__bspModel.collideSegment(worldToLocal.applyPoint(start), worldToLocal.applyPoint(stop))
        if testRes is None:
            return
        else:
            res = []
            for dist, normal, hitAngleCos, matKind in testRes:
                res.append((dist,
                 worldMatrix.applyVector(normal),
                 hitAngleCos,
                 matKind))

            return res

    def localSphericHitTest(self, center, radius, bOutsidePolygonsOnly = True):
        return self.__bspModel.collideSphere(center, radius, bOutsidePolygonsOnly)

    def localCollidesWithTriangle(self, triangle, hitDir):
        return self.__bspModel.collidesWithTriangle(triangle, hitDir)


def segmentMayHitVehicle(vehicleDescr, segmentStart, segmentEnd, vehicleCenter):
    radiusSquared = vehicleDescr.boundingRadius
    radiusSquared *= radiusSquared
    segmentStart = segmentStart - vehicleCenter
    segmentEnd = segmentEnd - vehicleCenter
    ao = Vector2(-segmentStart.x, -segmentStart.z)
    bo = Vector2(-segmentEnd.x, -segmentEnd.z)
    ab = ao - bo
    e = ao.dot(ab)
    if e <= 0.0:
        return ao.lengthSquared <= radiusSquared
    if e >= ab.lengthSquared:
        return bo.lengthSquared <= radiusSquared
    return ao.lengthSquared - e * e / ab.lengthSquared <= radiusSquared
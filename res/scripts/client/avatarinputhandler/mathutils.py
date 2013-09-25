# Embedded file name: scripts/client/AvatarInputHandler/mathUtils.py
import BigWorld
import Math
from Math import Vector2, Vector3, Matrix
import random
import math

def createIdentityMatrix():
    result = Matrix()
    result.setIdentity()
    return result


def createRotationMatrix(rotation):
    result = Matrix()
    result.setRotateYPR(rotation)
    return result


def createTranslationMatrix(translation):
    result = Matrix()
    result.setTranslate(translation)
    return result


def createRTMatrix(rotation, translation):
    result = Matrix()
    result.setRotateYPR(rotation)
    result.translation = translation
    return result


def createSRTMatrix(scale, rotation, translation):
    scaleMatrix = Matrix()
    scaleMatrix.setScale(scale)
    result = Matrix()
    result.setRotateYPR(rotation)
    result.translation = translation
    result.preMultiply(scaleMatrix)
    return result


def clamp(minVal, maxVal, val):
    if minVal > val:
        return minVal
    if maxVal < val:
        return maxVal
    return val


def clampVector3(minVal, maxVal, val):
    return Vector3(clamp(minVal.x, maxVal.x, val.x), clamp(minVal.y, maxVal.y, val.y), clamp(minVal.z, maxVal.z, val.z))


def clampVectorLength(minLength, maxLength, vector):
    length = vector.length
    if not almostZero(length):
        if minLength > length:
            return vector / length * minLength
        if maxLength < length:
            return vector / length * maxLength
    return vector * 1.0


def almostZero(val, epsilon = 0.0004):
    return -epsilon < val < epsilon


class RandomVectors:

    @staticmethod
    def random2(magnitude = 1.0, randomGenerator = None):
        if randomGenerator is None:
            randomGenerator = random
        u = randomGenerator.random()
        yaw = 2 * math.pi * u
        return Vector2(math.sin(yaw) * magnitude, math.cos(yaw) * magnitude)

    @staticmethod
    def random3Flat(magnitude = 1.0, randomGenerator = None):
        randomVec2 = RandomVectors.random2(magnitude, randomGenerator)
        return Vector3(randomVec2.x, 0.0, randomVec2.y)

    @staticmethod
    def random3(magnitude = 1.0, randomGenerator = None):
        if randomGenerator is None:
            randomGenerator = random
        u = randomGenerator.random()
        v = randomGenerator.random()
        yaw = 2 * math.pi * u
        pitch = math.acos(2 * v - 1)
        sin = math.sin(pitch)
        return Vector3(math.sin(yaw) * sin * magnitude, math.cos(pitch) * magnitude, math.cos(yaw) * sin * magnitude)


class FIRFilter(object):

    def __init__(self, coeffs = None):
        self.coeffs = coeffs
        self.values = [ Vector3(0) for x in xrange(len(self.coeffs)) ]
        self.__id = 0
        self.value = Vector3(0)

    def reset(self):
        self.values = [ Vector3(0) for x in xrange(len(self.coeffs)) ]
        self.__id = 0

    def add(self, value):
        self.values[self.__id] = value
        self.value = Vector3(0)
        for id, coeff in enumerate(self.coeffs):
            self.value += self.values[self.__id - id] * coeff

        self.__id += 1
        if self.__id >= len(self.values):
            self.__id = 0
        return self.value


class SMAFilter(FIRFilter):

    def __init__(self, length):
        FIRFilter.__init__(self, [ 1.0 / length for x in xrange(length) ])


class LowPassFilter(object):

    def __init__(self, alpha):
        self.value = Vector3(0)
        self.alpha = alpha

    def reset(self):
        self.value = Vector3(0)

    def add(self, value):
        self.value = value * self.alpha + (1 - self.alpha) * self.value
        return self.value


class RangeFilter(object):

    def __init__(self, minThreshold, maxLength, cutOffThreshold, filter):
        self.minThreshold = minThreshold
        self.maxLength = maxLength
        self.cutOffThreshold = cutOffThreshold
        self.filter = filter

    def reset(self):
        self.filter.reset()

    def add(self, value):
        valueLength = value.length
        valueToAdd = Vector3(value)
        if valueLength < self.minThreshold or valueLength >= self.cutOffThreshold:
            valueToAdd *= 0.0
        if valueLength > self.maxLength:
            valueToAdd *= self.maxLength / valueLength
        return self.filter.add(valueToAdd)
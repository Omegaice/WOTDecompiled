# Embedded file name: scripts/common/gun_rotation_shared.py
import BigWorld
from math import pi
from constants import DEFAULT_GUN_PITCH_LIMITS_TRANSITION

def calcPitchLimitsFromDesc(turretYaw, pitchLimitsDesc):
    basicLimits = pitchLimitsDesc['basic']
    frontLimits = pitchLimitsDesc.get('front')
    backLimits = pitchLimitsDesc.get('back')
    if frontLimits is None and backLimits is None:
        return basicLimits
    else:
        if frontLimits is None:
            frontLimits = (basicLimits[0], basicLimits[1], 0.0)
        if backLimits is None:
            backLimits = (basicLimits[0], basicLimits[1], 0.0)
        transition = pitchLimitsDesc.get('transition')
        if transition is None:
            transition = DEFAULT_GUN_PITCH_LIMITS_TRANSITION
        return BigWorld.wg_calcGunPitchLimits(turretYaw, basicLimits, frontLimits, backLimits, transition)


def calcPitchLimits(turretYaw, basicLimits, frontLimits, backLimits, transition):
    return calcPitchLimitsFromDesc(turretYaw, {'basic': basicLimits,
     'front': frontLimits,
     'back': backLimits,
     'transition': transition})


def encodeAngleToUint(angle, bits):
    mask = (1 << bits) - 1
    return int(round((mask + 1) * (angle + pi) / (pi * 2.0))) & mask


def decodeAngleFromUint(code, bits):
    return pi * 2.0 * code / (1 << bits) - pi


def encodeRestrictedAngleToUint(angle, bits, minBound, maxBound):
    t = (angle - minBound) / (maxBound - minBound)
    t = _clamp(0.0, t, 1.0)
    mask = (1 << bits) - 1
    return int(round(mask * t)) & mask


def decodeRestrictedAngleFromUint(code, bits, minBound, maxBound):
    t = float(code) / ((1 << bits) - 1)
    return minBound + t * (maxBound - minBound)


def encodeGunAngles(yaw, pitch, pitchLimits):
    return encodeAngleToUint(yaw, 10) << 6 | encodeRestrictedAngleToUint(pitch, 6, *pitchLimits)


def decodeGunAngles(code, pitchLimits):
    return (decodeAngleFromUint(code >> 6 & 1023, 10), decodeRestrictedAngleFromUint((code & 63), 6, *pitchLimits))


def _clamp(minBound, value, maxBound):
    if value < minBound:
        return minBound
    if value > maxBound:
        return maxBound
    return value
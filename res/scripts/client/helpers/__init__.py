# 2013.11.15 11:27:07 EST
# Embedded file name: scripts/client/helpers/__init__.py
import BigWorld
import ResMgr
import Settings
import i18n, constants
from debug_utils import LOG_CURRENT_EXCEPTION
import material_kinds

def isPlayerAccount():
    return hasattr(BigWorld.player(), 'databaseID')


def isPlayerAvatar():
    return hasattr(BigWorld.player(), 'arena')


def getClientLanguage():
    """
    Return client string of language code
    """
    lng = constants.DEFAULT_LANGUAGE
    try:
        lng = i18n.makeString('#settings:LANGUAGE_CODE')
        if not lng.strip() or lng == '#settings:LANGUAGE_CODE' or lng == 'LANGUAGE_CODE':
            lng = constants.DEFAULT_LANGUAGE
    except Exception:
        LOG_CURRENT_EXCEPTION()

    return lng


def getClientOverride():
    if constants.IS_KOREA:
        return 'KR'
    elif constants.IS_CHINA:
        return 'CN'
    elif constants.IS_VIETNAM:
        return 'VN'
    else:
        return None


def getLocalizedData(dataDict, key, defVal = ''):
    resVal = defVal
    if dataDict:
        lng = getClientLanguage()
        localesDict = dataDict.get(key, {})
        if localesDict:
            if lng in localesDict:
                resVal = localesDict[lng]
            elif constants.DEFAULT_LANGUAGE in localesDict:
                resVal = localesDict[constants.DEFAULT_LANGUAGE]
            else:
                resVal = localesDict.items()[0][1]
    return resVal


def int2roman(number):
    """
    Convert arabic number to roman number
    @param number: int - number
    @return: string - roman number
    """
    numerals = {1: 'I',
     4: 'IV',
     5: 'V',
     9: 'IX',
     10: 'X',
     40: 'XL',
     50: 'L',
     90: 'XC',
     100: 'C',
     400: 'CD',
     500: 'D',
     900: 'CM',
     1000: 'M'}
    result = ''
    for value, numeral in sorted(numerals.items(), reverse=True):
        while number >= value:
            result += numeral
            number -= value

    return result


def getClientVersion():
    sec = ResMgr.openSection('../version.xml')
    version = i18n.makeString(sec.readString('appname')) + ' ' + sec.readString('version')
    return version


def getClientOverride():
    if constants.IS_KOREA:
        return 'KR'
    elif constants.IS_CHINA:
        return 'CN'
    elif constants.IS_VIETNAM:
        return 'VN'
    else:
        return None


def isShowStartupVideo():
    if not BigWorld.wg_isSSE2Supported():
        return False
    else:
        p = Settings.g_instance.userPrefs
        return p is None or p.readInt(Settings.KEY_SHOW_STARTUP_MOVIE, 1) == 1


def calcEffectMaterialIndex(matKind):
    if matKind != 0:
        return material_kinds.EFFECT_MATERIAL_INDEXES_BY_IDS.get(matKind)
    else:
        effectIndex = -1
        if isPlayerAvatar():
            arenaSpecificEffect = BigWorld.player().arena.arenaType.defaultGroundEffect
            if arenaSpecificEffect is not None:
                if arenaSpecificEffect == 'None':
                    return
                if not isinstance(arenaSpecificEffect, int):
                    effectIndex = material_kinds.EFFECT_MATERIAL_INDEXES_BY_NAMES.get(arenaSpecificEffect)
                    effectIndex = -1 if effectIndex is None else effectIndex
                    BigWorld.player().arena.arenaType.defaultGroundEffect = effectIndex
                else:
                    effectIndex = arenaSpecificEffect
        return effectIndex
        return
# okay decompyling res/scripts/client/helpers/__init__.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:27:07 EST

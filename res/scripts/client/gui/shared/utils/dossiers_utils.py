# Embedded file name: scripts/client/gui/shared/utils/dossiers_utils.py
import BigWorld
import pickle
import dossiers
from gui.Scaleform.locale.MENU import MENU
from gui import GUI_NATIONS_ORDER_INDEX, nationCompareByIndex
from helpers.i18n import makeString
from gui.shared.utils.RareAchievementsCache import g_rareAchievesCache
from constants import DOSSIER_TYPE, CLAN_MEMBER_FLAGS
from items.vehicles import getVehicleType, VEHICLE_CLASS_TAGS
from debug_utils import LOG_ERROR, LOG_CURRENT_EXCEPTION
from dossiers.achievements import ACHIEVEMENTS, ACHIEVEMENT_SECTIONS_ORDER, DEFAULT_WEIGHT, ACHIEVEMENT_TYPE
from dossiers.dependences import getTankExpertRequirements, getMechanicEngineerRequirements
ACHIEVEMENT_VEHICLES_MAX = 16
ACHIEVEMENT_VEHICLES_SHOW = 10
TANK_EXPERT_GROUP = ['tankExpert']
MECH_ENGINEER_GROUP = ['mechanicEngineer']
for name, nationID in GUI_NATIONS_ORDER_INDEX.iteritems():
    TANK_EXPERT_GROUP.append('tankExpert%d' % nationID)
    MECH_ENGINEER_GROUP.append('mechanicEngineer%d' % nationID)

EXCLUDED_ACHIEVES = ('lumberjack', 'alaric', 'tankExpert6', 'mechanicEngineer6')

def __defineMedalsBlocks():
    global ACCOUNT_MEDALS_LAYOUT
    global TANKMEN_MEDALS_LAYOUT
    global VEHICLE_MEDALS_LAYOUT
    ACCOUNT_MEDALS_LAYOUT = []
    TANKMEN_MEDALS_LAYOUT = []
    VEHICLE_MEDALS_LAYOUT = []

    def getSectionAchieves(sectionName, condition):
        result = []
        for k, v in ACHIEVEMENTS.iteritems():
            if v['section'] != sectionName:
                continue
            if not condition(k):
                continue
            if k in EXCLUDED_ACHIEVES:
                continue
            if k.startswith('tankExpert') and k not in TANK_EXPERT_GROUP:
                continue
            if k.startswith('mechanicEngineer') and k not in MECH_ENGINEER_GROUP:
                continue
            result.append(k)

        return tuple(sorted(result))

    for section in ACHIEVEMENT_SECTIONS_ORDER:
        ACCOUNT_MEDALS_LAYOUT.append(getSectionAchieves(section, isAccountMedal))
        VEHICLE_MEDALS_LAYOUT.append(getSectionAchieves(section, isVehicleMedal))
        TANKMEN_MEDALS_LAYOUT.append(getSectionAchieves(section, isTankmanMedal))

    ACCOUNT_MEDALS_LAYOUT = tuple(ACCOUNT_MEDALS_LAYOUT)
    TANKMEN_MEDALS_LAYOUT = tuple(TANKMEN_MEDALS_LAYOUT)
    VEHICLE_MEDALS_LAYOUT = tuple(VEHICLE_MEDALS_LAYOUT)


def getAccountAchievementsLayout():
    try:
        ACCOUNT_MEDALS_LAYOUT
    except NameError:
        __defineMedalsBlocks()

    return ACCOUNT_MEDALS_LAYOUT


def getTankmenAchievementsLayout():
    try:
        TANKMEN_MEDALS_LAYOUT
    except NameError:
        __defineMedalsBlocks()

    return TANKMEN_MEDALS_LAYOUT


def getVehiclesAchievementsLayout():
    try:
        VEHICLE_MEDALS_LAYOUT
    except NameError:
        __defineMedalsBlocks()

    return VEHICLE_MEDALS_LAYOUT


def getAchievementsLayout(dossierType):
    if dossierType == DOSSIER_TYPE.ACCOUNT:
        return getAccountAchievementsLayout()
    if dossierType == DOSSIER_TYPE.TANKMAN:
        return getTankmenAchievementsLayout()
    if dossierType == DOSSIER_TYPE.VEHICLE:
        return getVehiclesAchievementsLayout()
    return tuple()


def getAchievementSection(name):
    if name in ACHIEVEMENTS:
        return ACHIEVEMENTS[name]['section']
    else:
        return None


def getAchievementType(name):
    if name in ACHIEVEMENTS:
        return ACHIEVEMENTS[name]['type']
    else:
        return None


def getAchievementRecord(name):
    if name in ACHIEVEMENTS:
        return ACHIEVEMENTS[name].get('record')
    else:
        return None


def getAchievementCurRecord(name):
    if name in ACHIEVEMENTS:
        return ACHIEVEMENTS[name].get('curRecord')
    else:
        return None


def getAchievementWeight(name):
    if name in ACHIEVEMENTS:
        return ACHIEVEMENTS[name].get('weight', DEFAULT_WEIGHT)
    else:
        return None


def isAccountMedal(name):
    return name in dossiers._ACCOUNT_RECORDS_LAYOUT[0] or name == 'rareAchievements' or name == 'whiteTiger'


def isVehicleMedal(name):
    return name in dossiers._VEHICLE_RECORDS_LAYOUT[0] and getAchievementType(name) != ACHIEVEMENT_TYPE.CLASS


def isTankmanMedal(name):
    return name in dossiers._TANKMAN_RECORDS_LAYOUT[0]


MEDALS_UNIC_FOR_RANK = ('medalKay', 'medalCarius', 'medalKnispel', 'medalPoppel', 'medalAbrams', 'medalLeClerc', 'medalLavrinenko', 'medalEkins', 'markOfMastery')
MEDALS_TITLES = ['lumberjack']
MEDALS_TITLES.extend(TANK_EXPERT_GROUP)
MEDALS_TITLES.extend(MECH_ENGINEER_GROUP)
CLAN_MEMBERS = {CLAN_MEMBER_FLAGS.LEADER: 'leader',
 CLAN_MEMBER_FLAGS.VICE_LEADER: 'vice_leader',
 CLAN_MEMBER_FLAGS.RECRUITER: 'recruiter',
 CLAN_MEMBER_FLAGS.TREASURER: 'treasurer',
 CLAN_MEMBER_FLAGS.DIPLOMAT: 'diplomat',
 CLAN_MEMBER_FLAGS.COMMANDER: 'commander',
 CLAN_MEMBER_FLAGS.PRIVATE: 'private',
 CLAN_MEMBER_FLAGS.RECRUIT: 'recruit'}
_ICONS_MASK = '../maps/icons/vehicle/small/%s.png'

def getCommonInfo(userName, dossier, clanInfo, clanEmblemFile):
    clanNameProp = 'clanName'
    clanNameDescrProp = 'clanNameDescr'
    clanJoinTimeProp = 'clanJoinTime'
    clanPositionProp = 'clanPosition'
    clanEmblemProp = 'clanEmblem'
    import cgi
    lastBattleTimeUserString = makeString(MENU.ACCOUNT_PROFILE_EMPTYBATTLELIST)
    if dossier['lastBattleTime']:
        lastBattleTimeUserString = '%s %s' % (BigWorld.wg_getLongDateFormat(dossier['lastBattleTime']), BigWorld.wg_getLongTimeFormat(dossier['lastBattleTime']))
    value = {'name': userName,
     'registrationDate': '%s %s' % (BigWorld.wg_getLongDateFormat(dossier['creationTime']), BigWorld.wg_getLongTimeFormat(dossier['creationTime'])),
     'lastBattleDate': lastBattleTimeUserString,
     clanNameProp: '',
     clanNameDescrProp: '',
     clanJoinTimeProp: '',
     clanPositionProp: '',
     clanEmblemProp: None}

    def getGoldFmt(str):
        return str

    if clanInfo is not None:
        value[clanNameProp] = cgi.escape(clanInfo[1])
        value[clanNameDescrProp] = cgi.escape(clanInfo[0])
        value[clanJoinTimeProp] = makeString(MENU.PROFILE_HEADER_CLAN_JOINDATE) % getGoldFmt(BigWorld.wg_getLongDateFormat(clanInfo[4]))
        clanPosition = makeString('#menu:profile/header/clan/position/%s' % CLAN_MEMBERS[clanInfo[3]] if clanInfo[3] in CLAN_MEMBERS else '')
        value[clanPositionProp] = getGoldFmt(clanPosition) if clanInfo[3] in CLAN_MEMBERS else ''
        clanEmblemId = None
        if clanEmblemFile:
            clanEmblemId = 'userInfoId' + userName
            BigWorld.wg_addTempScaleformTexture(clanEmblemId, clanEmblemFile)
        value[clanEmblemProp] = clanEmblemId
    return value


def getDossierVehicleList(dossier, isOnlyTotal = False):
    battlesCount = float(dossier['battlesCount'])
    winsCount = float(dossier['wins'])
    data = ['ALL',
     '#menu:profile/list/totalName',
     None,
     0,
     -1,
     __getData('battlesCount', dossier),
     '%d%%' % round(100 * winsCount / battlesCount) if battlesCount != 0 else '',
     0]
    if not isOnlyTotal:
        vehList = dossier['vehDossiersCut'].items()
        vehList.sort(cmp=__dossierComparator)
        for vehTypeCompactDesr, battles in vehList:
            try:
                vehType = getVehicleType(vehTypeCompactDesr)
                data.append(vehTypeCompactDesr)
                data.append(vehType.userString)
                data.append(_ICONS_MASK % vehType.name.replace(':', '-'))
                data.append(vehType.level)
                data.append(vehType.id[0])
                data.append(battles[0])
                data.append('%d%%' % round(100 * float(battles[1]) / battles[0]) if battles[0] != 0 else '')
                data.append(battles[2])
            except Exception:
                LOG_ERROR('Get vehicle info error vehTypeCompactDesr: %s' % str(vehTypeCompactDesr))
                LOG_CURRENT_EXCEPTION()

    return data


def __vehiclesListSort(i1, i2):
    res = i1['level'] - i2['level']
    if res:
        return res
    return nationCompareByIndex(i1['nation'], i2['nation'])


def checkTankExpertActivity(type, dossier):
    res = getTankExpertRequirements(dossiers.g_cache, dossier['vehTypeFrags'])
    if not len(res.get(type, [])):
        return (bool(dossier[type]), None, 0)
    else:
        vList = __makeVehiclesList(res.get(type, []))
        vList.sort(__vehiclesListSort)
        fullVehListLength = len(vList)
        isActive = bool(dossier[type])
        if fullVehListLength >= ACHIEVEMENT_VEHICLES_MAX:
            vList = vList[:ACHIEVEMENT_VEHICLES_SHOW]
        return (isActive, vList, fullVehListLength)


def checkTechEngineerActivity(type, dossier, nationID, unlocks = None):
    achieveName = 'mechanicEngineer'
    if nationID > -1:
        achieveName = '%s%d' % (achieveName, nationID)
    if unlocks is None:
        unlocks = dossiers.g_cache['vehiclesInTrees']
    res = getMechanicEngineerRequirements(dossiers.g_cache, set(), unlocks, nationID)
    if not len(res.get(achieveName, list())):
        return (True, None, 0)
    else:
        vList = __makeVehiclesList(res.get(type, []))
        vList.sort(__vehiclesListSort)
        fullVehListLength = len(vList)
        if fullVehListLength >= ACHIEVEMENT_VEHICLES_MAX:
            vList = vList[:ACHIEVEMENT_VEHICLES_SHOW]
        return (False, vList, fullVehListLength)


def __makeVehiclesList(vTypeCompDescrs):
    vehiclesList = []
    for vehTypeCompDescr in vTypeCompDescrs:
        try:
            vType = getVehicleType(vehTypeCompDescr)
            classTag = tuple(VEHICLE_CLASS_TAGS & vType.tags)[0]
            vehiclesList.append({'name': vType.userString,
             'nation': vType.id[0],
             'level': vType.level,
             'type': classTag})
        except Exception:
            LOG_CURRENT_EXCEPTION()
            continue

    return vehiclesList


ACTIVITY_HANDLERS = {'tankExpert': lambda t, d, u: checkTankExpertActivity(t, d),
 'tankExpert0': lambda t, d, u: checkTankExpertActivity(t, d),
 'tankExpert1': lambda t, d, u: checkTankExpertActivity(t, d),
 'tankExpert2': lambda t, d, u: checkTankExpertActivity(t, d),
 'tankExpert3': lambda t, d, u: checkTankExpertActivity(t, d),
 'tankExpert4': lambda t, d, u: checkTankExpertActivity(t, d),
 'tankExpert5': lambda t, d, u: checkTankExpertActivity(t, d),
 'tankExpert6': lambda t, d, u: checkTankExpertActivity(t, d),
 'tankExpert7': lambda t, d, u: checkTankExpertActivity(t, d),
 'tankExpert8': lambda t, d, u: checkTankExpertActivity(t, d),
 'tankExpert9': lambda t, d, u: checkTankExpertActivity(t, d),
 'tankExpert10': lambda t, d, u: checkTankExpertActivity(t, d),
 'tankExpert11': lambda t, d, u: checkTankExpertActivity(t, d),
 'tankExpert12': lambda t, d, u: checkTankExpertActivity(t, d),
 'tankExpert13': lambda t, d, u: checkTankExpertActivity(t, d),
 'tankExpert14': lambda t, d, u: checkTankExpertActivity(t, d),
 'mechanicEngineer': lambda t, d, u: checkTechEngineerActivity(t, d, -1, u),
 'mechanicEngineer0': lambda t, d, u: checkTechEngineerActivity(t, d, 0, u),
 'mechanicEngineer1': lambda t, d, u: checkTechEngineerActivity(t, d, 1, u),
 'mechanicEngineer2': lambda t, d, u: checkTechEngineerActivity(t, d, 2, u),
 'mechanicEngineer3': lambda t, d, u: checkTechEngineerActivity(t, d, 3, u),
 'mechanicEngineer4': lambda t, d, u: checkTechEngineerActivity(t, d, 4, u),
 'mechanicEngineer5': lambda t, d, u: checkTechEngineerActivity(t, d, 5, u),
 'mechanicEngineer6': lambda t, d, u: checkTechEngineerActivity(t, d, 6, u),
 'mechanicEngineer7': lambda t, d, u: checkTechEngineerActivity(t, d, 7, u),
 'mechanicEngineer8': lambda t, d, u: checkTechEngineerActivity(t, d, 8, u),
 'mechanicEngineer9': lambda t, d, u: checkTechEngineerActivity(t, d, 9, u),
 'mechanicEngineer10': lambda t, d, u: checkTechEngineerActivity(t, d, 10, u),
 'mechanicEngineer11': lambda t, d, u: checkTechEngineerActivity(t, d, 11, u),
 'mechanicEngineer12': lambda t, d, u: checkTechEngineerActivity(t, d, 12, u),
 'mechanicEngineer13': lambda t, d, u: checkTechEngineerActivity(t, d, 13, u),
 'mechanicEngineer14': lambda t, d, u: checkTechEngineerActivity(t, d, 14, u)}

def __packMedalData(type, isActive = True, icon = '../maps/icons/achievement/noImage.png', rareIconId = None, value = 0, isUnic = False, isRare = False, isTitle = False, descr = '', vehiclesList = None):
    data = [type,
     not isActive,
     icon,
     value,
     isUnic,
     isRare,
     isTitle,
     descr,
     rareIconId]
    if vehiclesList is not None:
        data.append(len(vehiclesList))
        data.extend([ x for x in vehiclesList ])
    else:
        data.append(0)
    data.append(False)
    return data


def getMedalDict(achievementType, rank = None, rareAchieveId = None):
    packedList = getMedal(achievementType, rank, rareAchieveId)
    result = dict()
    result['type'] = packedList.pop(0)
    result['inactive'] = packedList.pop(0)
    result['icon'] = packedList.pop(0)
    result['rank'] = packedList.pop(0)
    result['unic'] = packedList.pop(0)
    result['rare'] = packedList.pop(0)
    result['title'] = packedList.pop(0)
    result['description'] = packedList.pop(0)
    result['rareIconId'] = packedList.pop(0)
    result['vehicles'] = list()
    vehiclesCount = packedList.pop(0)
    for i in xrange(vehiclesCount):
        result['vehicles'].append(packedList.pop(0))

    result['last'] = packedList.pop(0)
    return result


def checkWhiteTigerMedal(dossier):
    try:
        whiteTigerCompDescr = 56337
        return dossier['vehTypeFrags'].get(whiteTigerCompDescr, 0)
    except Exception:
        return 0


def getRareAchievementMedalData(dossier, medalId):
    import imghdr, uuid
    type = str(medalId)
    iconId = None
    iconData = g_rareAchievesCache.getImageData(medalId)
    if iconData and imghdr.what(None, iconData) is not None:
        iconId = str(uuid.uuid4())
        BigWorld.wg_addTempScaleformTexture(iconId, iconData)
    return __packMedalData(type=type, icon='../maps/icons/achievement/actionUnknown.png', rareIconId=iconId, isTitle=True, isRare=True, descr=g_rareAchievesCache.getDescription(medalId))


def getWhiteTigerMedalData(dossier = None, value = 0):
    type = 'whiteTiger'
    return __packMedalData(type=type, icon='../maps/icons/achievement/%s.png' % type, value=value or checkWhiteTigerMedal(dossier), descr=getMedalDescription(type))


def getMedalDescription(medalName, rank = 0):
    return makeString('#achievements:%s_descr' % medalName)


def getMedalHeroInfo(medalName):
    infoKey = '%s_heroInfo' % medalName
    msg = makeString('#achievements:%s' % infoKey)
    if msg == infoKey:
        return ''
    return msg


def getMedalValue(medalName, dossier):
    if dossier is None:
        return 0
    elif medalName == 'whiteTiger':
        return checkWhiteTigerMedal(dossier)
    elif getAchievementType(medalName) == 'class':
        if not dossier[medalName]:
            return 5
        if getAchievementType(medalName) == 'series':
            return dossier[ACHIEVEMENTS[medalName]['record']]
        max_value = dossiers.getRecordMaxValue(medalName)
        return dossier[medalName] >= max_value and makeString('#achievements:achievement/maxMedalValue') % (max_value - 1)
    else:
        return dossier[medalName]


def getDossierMedals(dossier, dossier_type = DOSSIER_TYPE.ACCOUNT, unlocks = None):
    medals = [dossier_type, pickle.dumps(dossier.makeCompDescr())]
    blocks = getAchievementsLayout(dossier_type)
    for group in blocks:
        for type in group:
            if type == 'markOfMastery':
                continue
            if type == 'whiteTiger':
                if checkWhiteTigerMedal(dossier):
                    medals.extend(getWhiteTigerMedalData(dossier=dossier))
            elif type == 'rareAchievements':
                for a in dossier[type]:
                    medals.extend(getRareAchievementMedalData(dossier, a))

            elif dossier[type]:
                iconFileName = type
                if type in MEDALS_UNIC_FOR_RANK:
                    iconFileName = '%s%d' % (iconFileName, dossier[type])
                handler = ACTIVITY_HANDLERS.get(type, lambda *args: (True, None))
                isActive, vehiclesNames = handler(type, dossier, unlocks)
                medals.extend(__packMedalData(type=type, isActive=isActive, icon='../maps/icons/achievement/%s.png' % iconFileName, value=getMedalValue(type, dossier), isUnic=type in MEDALS_UNIC_FOR_RANK, isTitle=type in MEDALS_TITLES, descr=getMedalDescription(type), vehiclesList=vehiclesNames))

        if len(medals) > 2:
            medals[-1] = blocks[-1] != group

    return medals


def getMedal(achievementType, rank = None, rareAchieveId = None):
    if achievementType == 'whiteTiger':
        return getWhiteTigerMedalData()
    elif achievementType == 'rareAchievements':
        return getRareAchievementMedalData(medalId=rareAchieveId)
    else:
        iconFileName = achievementType
        if achievementType in MEDALS_UNIC_FOR_RANK:
            iconFileName = '%s%d' % (iconFileName, rank)
        return __packMedalData(type=achievementType, icon='../maps/icons/achievement/%s.png' % iconFileName, isUnic=achievementType in MEDALS_UNIC_FOR_RANK, isTitle=achievementType in MEDALS_TITLES, descr=getMedalDescription(achievementType), value=rank)
        return None


TOTAL_BLOCKS = (('common', ('battlesCount', 'wins', 'losses', 'survivedBattles')), ('battleeffect', ('frags', 'maxFrags', 'effectiveShots', 'damageDealt')), ('credits', ('xp', 'avgExperience', 'maxXP')))
VEHICLE_BLOCKS = (('common', ('battlesCount', 'wins', 'losses', 'survivedBattles')), ('battleeffect', ('frags', 'maxFrags', 'effectiveShots', 'damageDealt')), ('credits', ('xp', 'avgExperience', 'maxXP')))

def getDossierTotalBlocks(dossier):
    data = ['#menu:profile/list/totalName', len(TOTAL_BLOCKS)]
    for blockType, fields in TOTAL_BLOCKS:
        data.append(blockType)
        data.append(len(fields))
        for fieldType in fields:
            data.append(fieldType)
            data.append(__getData(fieldType, dossier))
            data.append(__getDataExtra(blockType, fieldType, dossier, True, True))

    return data


def getDossierTotalBlocksSummary(dossier, isCompact = False):
    data = []
    for blockType, fields in TOTAL_BLOCKS:
        for fieldType in fields:
            data.append('#menu:profile/stats/items/' + fieldType)
            data.append(__getData(fieldType, dossier))
            data.append(__getDataExtra(blockType, fieldType, dossier, True, isCompact))

    return data


def getDossierVehicleBlocks(dossier, vehTypeId):
    vehType = getVehicleType(int(vehTypeId))
    data = [makeString('#menu:profile/list/descr', vehType.userString), len(VEHICLE_BLOCKS)]
    for blockType, fields in VEHICLE_BLOCKS:
        data.append(blockType)
        data.append(len(fields))
        for fieldType in fields:
            data.append(fieldType)
            data.append(__getData(fieldType, dossier))
            data.append(__getDataExtra(blockType, fieldType, dossier))

    return data


def __getData(fieldType, dossier):
    if fieldType == 'effectiveShots':
        if dossier['shots'] != 0:
            return '%d%%' % round(float(dossier['hits']) / dossier['shots'] * 100)
        return '0%'
    if fieldType == 'avgExperience':
        if dossier['battlesCount'] != 0:
            return BigWorld.wg_getIntegralFormat(round(float(dossier['xp']) / dossier['battlesCount']))
        return BigWorld.wg_getIntegralFormat(0)
    return BigWorld.wg_getIntegralFormat(dossier[fieldType])


def __getDataExtra(blockType, fieldType, dossier, isTotal = False, isCompact = False):
    extra = ''
    if blockType == 'common':
        if fieldType != 'battlesCount' and dossier['battlesCount'] != 0:
            extra = '(%d%%)' % round(float(dossier[fieldType]) / dossier['battlesCount'] * 100)
    if isTotal:
        if fieldType == 'maxFrags' and dossier['maxFrags'] != 0:
            extra = getVehicleType(dossier['maxFragsVehicle']).userString if not isCompact else getVehicleType(dossier['maxFragsVehicle']).shortUserString
        if fieldType == 'maxXP' and dossier['maxXP'] != 0:
            extra = getVehicleType(dossier['maxXPVehicle']).userString if not isCompact else getVehicleType(dossier['maxXPVehicle']).shortUserString
    return extra


def __dossierComparator(x1, x2):
    if x1[1][0] < x2[1][0]:
        return 1
    if x1[1][0] > x2[1][0]:
        return -1
    if x1[1][1] < x2[1][1]:
        return 1
    if x1[1][1] > x2[1][1]:
        return -1
    return 0


def __getMedalKayNextLevelValue(dossier):
    medalKayCfg = dossiers.RECORD_CONFIGS['medalKay']
    battleHeroes = dossier['battleHeroes']
    maxMedalClass = len(medalKayCfg)
    if not dossier['medalKay']:
        curClass = 5
        return curClass == 1 and None
    else:
        return medalKayCfg[maxMedalClass - curClass + 1] - battleHeroes
        return None


def __getMedalCariusNextLevelValue(dossier):
    medalCariusCfg = dossiers.RECORD_CONFIGS['medalCarius']
    frags = dossier['frags']
    maxMedalClass = len(medalCariusCfg)
    if not dossier['medalCarius']:
        curClass = 5
        return curClass == 1 and None
    else:
        return medalCariusCfg[maxMedalClass - curClass + 1] - frags
        return None


def __getMedalKnispelNextLevelValue(dossier):
    medalKnispelCfg = dossiers.RECORD_CONFIGS['medalKnispel']
    damageDealt = dossier['damageDealt']
    damageReceived = dossier['damageReceived']
    maxMedalClass = len(medalKnispelCfg)
    if not dossier['medalKnispel']:
        curClass = 5
        return curClass == 1 and None
    else:
        return medalKnispelCfg[maxMedalClass - curClass + 1] - (damageDealt + damageReceived)
        return None


def __getMedalPoppelNextLevelValue(dossier):
    medalPoppelCfg = dossiers.RECORD_CONFIGS['medalPoppel']
    spotted = dossier['spotted']
    maxMedalClass = len(medalPoppelCfg)
    if not dossier['medalPoppel']:
        curClass = 5
        return curClass == 1 and None
    else:
        return medalPoppelCfg[maxMedalClass - curClass + 1] - spotted
        return None


def __getMedalAbramsNextLevelValue(dossier):
    medalAbramsCfg = dossiers.RECORD_CONFIGS['medalAbrams']
    winAndSurvived = dossier['winAndSurvived']
    maxMedalClass = len(medalAbramsCfg)
    if not dossier['medalAbrams']:
        curClass = 5
        return curClass == 1 and None
    else:
        return medalAbramsCfg[maxMedalClass - curClass + 1] - winAndSurvived
        return None


def __getMedalLeClercNextLevelValue(dossier):
    medalLeClercCfg = dossiers.RECORD_CONFIGS['medalLeClerc']
    capturePoints = dossier['capturePoints']
    maxMedalClass = len(medalLeClercCfg)
    if not dossier['medalLeClerc']:
        curClass = 5
        return curClass == 1 and None
    else:
        return medalLeClercCfg[maxMedalClass - curClass + 1] - capturePoints
        return None


def __getMedalLavrinenkoNextLevelValue(dossier):
    medalLavrinenkoCfg = dossiers.RECORD_CONFIGS['medalLavrinenko']
    droppedCapturePoints = dossier['droppedCapturePoints']
    maxMedalClass = len(medalLavrinenkoCfg)
    if not dossier['medalLavrinenko']:
        curClass = 5
        return curClass == 1 and None
    else:
        return medalLavrinenkoCfg[maxMedalClass - curClass + 1] - droppedCapturePoints
        return None


def __getMedalEkinsNextLevelValue(dossier):
    medalEkinsCfg = dossiers.RECORD_CONFIGS['medalEkins']
    frags = dossier['frags8p']
    maxMedalClass = len(medalEkinsCfg)
    if not dossier['medalEkins']:
        curClass = 5
        return curClass == 1 and None
    else:
        return medalEkinsCfg[maxMedalClass - curClass + 1] - frags
        return None


def __getMedalBeasthunterNextLevelValue(dossier):
    minFrags = dossiers.RECORD_CONFIGS['beasthunter']
    beastFrags = dossier['fragsBeast']
    medals, series = divmod(beastFrags, minFrags)
    return minFrags - medals


def __getMedalMousebanNextLevelValue(dossier):
    minFrags = dossiers.RECORD_CONFIGS['mousebane']
    mausFrags = dossier['vehTypeFrags'].get(dossiers.g_cache['mausTypeCompDescr'], 0)
    medals, series = divmod(mausFrags, minFrags)
    return minFrags - medals


ACHIEVEMENTS_NEXT_LEVEL_VALUES = {'medalKay': {'name': 'heroesLeft',
              'func': __getMedalKayNextLevelValue},
 'medalCarius': {'name': 'vehiclesLeft',
                 'func': __getMedalCariusNextLevelValue},
 'medalKnispel': {'name': 'damageLeft',
                  'func': __getMedalKnispelNextLevelValue},
 'medalPoppel': {'name': 'vehiclesLeft',
                 'func': __getMedalPoppelNextLevelValue},
 'medalAbrams': {'name': 'battlesLeft',
                 'func': __getMedalAbramsNextLevelValue},
 'medalLeClerc': {'name': 'capturePointsLeft',
                  'func': __getMedalLeClercNextLevelValue},
 'medalLavrinenko': {'name': 'dropPointsLeft',
                     'func': __getMedalLavrinenkoNextLevelValue},
 'medalEkins': {'name': 'vehiclesLeft',
                'func': __getMedalEkinsNextLevelValue},
 'beasthunter': {'name': 'vehiclesLeft',
                 'func': __getMedalBeasthunterNextLevelValue},
 'mousebane': {'name': 'vehiclesLeft',
               'func': __getMedalMousebanNextLevelValue}}
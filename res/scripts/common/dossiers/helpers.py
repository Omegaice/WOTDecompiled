# Embedded file name: scripts/common/dossiers/helpers.py
import time
import dossiers
import utils
import arena_achievements
from itertools import izip
from constants import ARENA_BONUS_TYPE_CAPS as BONUS_CAPS
from constants import DESTR_CODES_BY_TAGS
from debug_utils import *

def updateVehicleDossier(descr, battleResults, originalXP, dossierXP, vehTypeCompDescr, resultsOverriding = None):
    results = _resultOverriding(battleResults, resultsOverriding)
    stop, _, _ = _updateDossierCommonPart(descr, results, originalXP, dossierXP)
    if not stop:
        _updateVehicleDossierImpl(vehTypeCompDescr, descr, results)
    return set(descr.popUps)


def updateAccountDossier(databaseID, descr, battleResults, originalXP, dossierXP, vehTypeCompDescr, vehDossierDescr, resultsOverriding = None):
    results = _resultOverriding(battleResults, resultsOverriding)
    stop, isMaxFragsGained, isMaxXPGained = _updateDossierCommonPart(descr, results, originalXP, dossierXP)
    if not stop:
        _updateAccountDossierImpl(descr, results, vehTypeCompDescr, vehDossierDescr, isMaxFragsGained, isMaxXPGained)
        _validateAccountAndVehicleDossiers(databaseID, descr, vehDossierDescr, vehTypeCompDescr)
    return set(descr.popUps)


def updateTankmanDossier(descr, battleResults, resultsOverriding = None):
    results = _resultOverriding(battleResults, resultsOverriding)
    _updateTankmanDossierImpl(descr, results)
    return set(descr.popUps)


def _resultOverriding(battleResults, resultsOverriding):
    if resultsOverriding is None:
        return battleResults
    else:
        results = dict(battleResults)
        results.update(resultsOverriding)
        return results


def _updateDossierCommonPart(descr, results, originalXP, dossierXP):
    if not bool(BONUS_CAPS.get(results['bonusType']) & BONUS_CAPS.DOSSIER_TOTAL_VALUES):
        return (True, False, False)
    descr.expand()
    descr['battleLifeTime'] += results['lifeTime']
    descr['lastBattleTime'] = int(time.time())
    descr['originalXP'] += originalXP
    descr['damageAssistedTrack'] += results['damageAssistedTrack']
    descr['damageAssistedRadio'] += results['damageAssistedRadio']
    descr['mileage'] += results['mileage']
    descr['shotsReceived'] += results['shotsReceived']
    descr['noDamageShotsReceived'] += results['noDamageShotsReceived']
    descr['piercedReceived'] += results['piercedReceived']
    descr['heHitsReceived'] += results['heHitsReceived']
    descr['he_hits'] += results['he_hits']
    descr['pierced'] += results['pierced']
    _updateDossierRecordsWithBonusTypePrefix(descr, '', results, dossierXP)
    if bool(BONUS_CAPS.get(results['bonusType']) & BONUS_CAPS.DOSSIER_COMPANY_VALUES):
        _updateDossierRecordsWithBonusTypePrefix(descr, 'company/', results, dossierXP)
    if bool(BONUS_CAPS.get(results['bonusType']) & BONUS_CAPS.DOSSIER_CLAN_VALUES):
        _updateDossierRecordsWithBonusTypePrefix(descr, 'clan/', results, dossierXP)
    if results['killerID'] == 0 and results['winnerTeam'] == results['team']:
        descr['winAndSurvived'] += 1
    kill_list = results['kill_list']
    if kill_list:
        vehTypeFrags = dict(descr['vehTypeFrags'])
        vehicles8p = dossiers.g_cache['vehicles8+']
        beastVehicles = dossiers.g_cache['beastVehicles']
        sinaiVehicles = dossiers.g_cache['sinaiVehicles']
        pattonVehicles = dossiers.g_cache['pattonVehicles']
        frags8p = fragsBeast = fragsSinai = fragsPatton = 0
        for _, vtcd, _ in kill_list:
            frags = vehTypeFrags.get(vtcd, 0)
            vehTypeFrags[vtcd] = min(frags + 1, 60001)
            if vtcd in vehicles8p:
                frags8p += 1
            if vtcd in beastVehicles:
                fragsBeast += 1
            if vtcd in sinaiVehicles:
                fragsSinai += 1
            if vtcd in pattonVehicles:
                fragsPatton += 1

        descr['vehTypeFrags'] = vehTypeFrags
        if frags8p != 0:
            descr['frags8p'] += frags8p
        if fragsBeast != 0:
            descr['fragsBeast'] += fragsBeast
        if fragsSinai != 0:
            descr['fragsSinai'] += fragsSinai
        if fragsPatton != 0:
            descr['fragsPatton'] += fragsPatton
    if not bool(BONUS_CAPS.get(results['bonusType']) & BONUS_CAPS.DOSSIER_RND_VALUES):
        return (False, False, False)
    isMaxXPGained = False
    if dossierXP != 0 and dossierXP >= descr['maxXP']:
        isMaxXPGained = True
        descr['maxXP'] = dossierXP
    for achieveIdx in results['achievements']:
        arena_achievements.updateDossierRecord(descr, achieveIdx)

    isMaxFragsGained = False
    if kill_list and len(kill_list) >= descr['maxFrags']:
        descr['maxFrags'] = len(kill_list)
        isMaxFragsGained = True
    descr['treesCut'] += results['destroyedObjects'].get(DESTR_CODES_BY_TAGS['tree'], 0)
    return (False, isMaxFragsGained, isMaxXPGained)


def _updateDossierRecordsWithBonusTypePrefix(descr, prefix, results, dossierXP):
    descr[prefix + 'battlesCount'] += 1
    if dossierXP != 0:
        descr[prefix + 'xp'] += dossierXP
    if results['winnerTeam'] == results['team']:
        descr[prefix + 'wins'] += 1
    elif results['winnerTeam'] == 3 - results['team']:
        descr[prefix + 'losses'] += 1
    if results['killerID'] == 0:
        descr[prefix + 'survivedBattles'] += 1
    shots = results['shots']
    if shots != 0:
        descr[prefix + 'shots'] += shots
    hits = results['hits']
    if hits != 0:
        descr[prefix + 'hits'] += hits
    spotted = results['spotted']
    if spotted:
        descr[prefix + 'spotted'] += spotted
    damageDealt = results['damageDealt']
    if damageDealt != 0:
        descr[prefix + 'damageDealt'] += damageDealt
    damageReceived = results['damageReceived']
    if damageReceived != 0:
        descr[prefix + 'damageReceived'] += damageReceived
    capturePoints = results['capturePoints']
    if capturePoints != 0:
        descr[prefix + 'capturePoints'] += capturePoints
    droppedCapturePoints = min(results['droppedCapturePoints'], 100)
    if droppedCapturePoints != 0:
        descr[prefix + 'droppedCapturePoints'] += droppedCapturePoints
    kills = results['kills']
    if kills:
        descr[prefix + 'frags'] += kills


def _updateVehicleDossierImpl(vehTypeCompDescr, descr, results):
    if not bool(BONUS_CAPS.get(results['bonusType']) & BONUS_CAPS.DOSSIER_RND_VALUES):
        return
    if descr['markOfMastery'] < results['markOfMastery']:
        descr['markOfMastery'] = results['markOfMastery']
    tags = utils.vehicleTypeByCompactDescr(vehTypeCompDescr)['tags']
    _updatePerBattleSeries(descr, 'invincibleSeries', results['killerID'] == 0 and results['damageReceived'] == 0 and 'SPG' not in tags)
    _updatePerBattleSeries(descr, 'diehardSeries', results['killerID'] == 0 and 'SPG' not in tags)
    _updateInBattleSeries(descr, 'sniper', results)
    _updateInBattleSeries(descr, 'killing', results)
    _updateInBattleSeries(descr, 'piercing', results)


def _updatePerBattleSeries(descr, achieveName, isNotInterrupted):
    if achieveName not in descr:
        return
    if isNotInterrupted:
        descr[achieveName] += 1
    else:
        descr[achieveName] = 0


def _updateInBattleSeries(descr, achieveName, results):
    achieveIdx = arena_achievements.INBATTLE_SERIES_INDICES[achieveName]
    recordName = achieveName + 'Series'
    if recordName not in descr:
        return
    series = results['series'].get(achieveIdx, [])
    if series:
        descr[recordName] = descr[recordName] + series[0]
    for runLength in series[1:]:
        descr[recordName] = runLength


def _updateAccountDossierImpl(descr, results, vehTypeCompDescr, vehDossierDescr, isMaxFragsGained, isMaxXPGained):
    if not vehDossierDescr is not None:
        raise AssertionError
        vehDossiersCut = dict(descr['vehDossiersCut'])
        battlesCount, wins, _, _ = vehDossiersCut.get(vehTypeCompDescr, (0, 0, 0, 0))
        if results['winnerTeam'] == results['team']:
            wins += 1
        vehDossiersCut[vehTypeCompDescr] = (battlesCount + 1,
         wins,
         vehDossierDescr['markOfMastery'],
         vehDossierDescr['xp'])
        descr['vehDossiersCut'] = vehDossiersCut
        return bool(BONUS_CAPS.get(results['bonusType']) & BONUS_CAPS.DOSSIER_RND_VALUES) or None
    else:
        series = ('maxInvincibleSeries', 'maxDiehardSeries', 'maxSniperSeries', 'maxKillingSeries', 'maxPiercingSeries')
        for recordName in series:
            if vehDossierDescr[recordName] > descr[recordName]:
                descr[recordName] = vehDossierDescr[recordName]

        if isMaxXPGained:
            descr['maxXPVehicle'] = vehTypeCompDescr
        if isMaxFragsGained:
            descr['maxFragsVehicle'] = vehTypeCompDescr
        return


def _updateTankmanDossierImpl(descr, results):
    if not bool(BONUS_CAPS.get(results['bonusType']) & BONUS_CAPS.DOSSIER_TOTAL_VALUES):
        return
    descr['battlesCount'] += 1
    if not bool(BONUS_CAPS.get(results['bonusType']) & BONUS_CAPS.DOSSIER_RND_VALUES):
        return
    for achieveIdx in results['achievements']:
        arena_achievements.updateDossierRecord(descr, achieveIdx)


def _validateAccountAndVehicleDossiers(databaseID, accDossier, vehDossier, vehTypeCompDescr):
    needRecalculateBattlesCountAndWins = False
    try:
        if accDossier['battlesCount'] < vehDossier['battlesCount']:
            raise Exception, "Sum 'battlesCount' mismatch (%s, %s, %s, %s)" % (databaseID,
             vehTypeCompDescr,
             accDossier['battlesCount'],
             vehDossier['battlesCount'])
    except Exception:
        LOG_CURRENT_EXCEPTION()
        needRecalculateBattlesCountAndWins = True

    battlesCount, wins, markOfMastery, xp = accDossier['vehDossiersCut'].get(vehTypeCompDescr, (0, 0, 0, 0))
    try:
        if battlesCount != vehDossier['battlesCount']:
            raise Exception, "'battlesCount' mismatch (%s, %s, %s, %s)" % (databaseID,
             vehTypeCompDescr,
             battlesCount,
             vehDossier['battlesCount'])
    except Exception:
        LOG_CURRENT_EXCEPTION()
        vehDossiersCut = dict(accDossier['vehDossiersCut'])
        vehDossiersCut[vehTypeCompDescr] = (vehDossier['battlesCount'],
         wins,
         markOfMastery,
         xp)
        accDossier['vehDossiersCut'] = vehDossiersCut
        battlesCount = vehDossier['battlesCount']
        needRecalculateBattlesCountAndWins = True

    try:
        if wins != vehDossier['wins']:
            raise Exception, "'wins' mismatch (%s, %s, %s, %s)" % (databaseID,
             vehTypeCompDescr,
             wins,
             vehDossier['wins'])
    except Exception:
        LOG_CURRENT_EXCEPTION()
        vehDossiersCut = dict(accDossier['vehDossiersCut'])
        vehDossiersCut[vehTypeCompDescr] = (battlesCount,
         vehDossier['wins'],
         markOfMastery,
         xp)
        accDossier['vehDossiersCut'] = vehDossiersCut
        wins = vehDossier['wins']
        needRecalculateBattlesCountAndWins = True

    try:
        if markOfMastery != vehDossier['markOfMastery']:
            raise Exception, "'markOfMastery' mismatch (%s, %s, %s, %s)" % (databaseID,
             vehTypeCompDescr,
             markOfMastery,
             vehDossier['markOfMastery'])
    except Exception:
        LOG_CURRENT_EXCEPTION()
        vehDossiersCut = dict(accDossier['vehDossiersCut'])
        vehDossiersCut[vehTypeCompDescr] = (battlesCount,
         wins,
         vehDossier['markOfMastery'],
         xp)
        accDossier['vehDossiersCut'] = vehDossiersCut
        markOfMastery = vehDossier['markOfMastery']

    try:
        if xp != vehDossier['xp']:
            raise Exception, "'xp' mismatch (%s, %s, %s, %s)" % (databaseID,
             vehTypeCompDescr,
             xp,
             vehDossier['xp'])
    except Exception:
        LOG_CURRENT_EXCEPTION()
        vehDossiersCut = dict(accDossier['vehDossiersCut'])
        vehDossiersCut[vehTypeCompDescr] = (battlesCount,
         wins,
         markOfMastery,
         vehDossier['xp'])
        accDossier['vehDossiersCut'] = vehDossiersCut

    if needRecalculateBattlesCountAndWins:
        _recalculateBattlesCountAndWins(accDossier)
    try:
        if accDossier['maxXP'] < vehDossier['maxXP']:
            raise Exception, "'maxXP' mismatch (%s, %s, %s, %s)" % (databaseID,
             vehTypeCompDescr,
             accDossier['maxXP'],
             vehDossier['maxXP'])
    except Exception:
        LOG_CURRENT_EXCEPTION()
        accDossier['maxXP'] = vehDossier['maxXP']
        accDossier['maxXPVehicle'] = vehTypeCompDescr

    try:
        if accDossier['maxFrags'] < vehDossier['maxFrags']:
            raise Exception, "'maxFrags' mismatch (%s, %s, %s, %s)" % (databaseID,
             vehTypeCompDescr,
             accDossier['maxFrags'],
             vehDossier['maxFrags'])
    except Exception:
        LOG_CURRENT_EXCEPTION()
        accDossier['maxFrags'] = vehDossier['maxFrags']
        accDossier['maxFragsVehicle'] = vehTypeCompDescr

    for record in arena_achievements.ACHIEVEMENTS:
        try:
            if record in accDossier and record in vehDossier and accDossier[record] < vehDossier[record]:
                raise Exception, "'%s' mismatch (%s, %s, %s, %s)" % (record,
                 databaseID,
                 vehTypeCompDescr,
                 accDossier[record],
                 vehDossier[record])
        except Exception:
            LOG_CURRENT_EXCEPTION()
            accDossier[record] = vehDossier[record]


def _recalculateBattlesCountAndWins(accDossier):
    battlesCountSum = winsSum = 0
    for battlesCount, wins, _, _ in accDossier['vehDossiersCut'].itervalues():
        battlesCountSum += battlesCount
        winsSum += wins

    accDossier['battlesCount'] = battlesCountSum
    accDossier['wins'] = winsSum
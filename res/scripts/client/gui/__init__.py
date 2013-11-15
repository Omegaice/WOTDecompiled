# 2013.11.15 11:25:31 EST
# Embedded file name: scripts/client/gui/__init__.py
import ResMgr, nations
from collections import defaultdict
from constants import IS_DEVELOPMENT
from gui.GuiSettings import GuiSettings
from debug_utils import LOG_ERROR, LOG_CURRENT_EXCEPTION
from helpers.html.templates import XMLCollection
g_guiResetters = set()
g_repeatKeyHandlers = set()
g_tankActiveCamouflage = {}
GUI_SETTINGS = GuiSettings()
DEPTH_OF_Disconnect = 0.0
DEPTH_OF_Postmortem = 0.01
DEPTH_OF_BotsMenu = 0.05
DEPTH_OF_Battle = 0.1
DEPTH_OF_Statistic = 0.1
DEPTH_OF_PlayerBonusesPanel = 0.2
DEPTH_OF_Minimap = 0.5
DEPTH_OF_Aim = 0.6
DEPTH_OF_Binoculars = 0.55
DEPTH_OF_GunMarker = 0.56
DEPTH_OF_VehicleMarker = 0.9
CLIENT_ENCODING = '1251'
VERSION_FILE_PATH = '../version.xml'
TANKMEN_ROLES_ORDER_DICT = {'plain': ('commander', 'gunner', 'driver', 'radioman', 'loader'),
 'enum': ('commander', 'gunner1', 'gunner2', 'driver', 'radioman1', 'radioman2', 'loader1', 'loader2')}

def onRepeatKeyEvent(event):
    safeCopy = frozenset(g_repeatKeyHandlers)
    processed = False
    for handler in safeCopy:
        try:
            processed = handler(event)
            if processed:
                break
        except Exception:
            LOG_CURRENT_EXCEPTION()

    safeCopy = None
    return processed


NONE_NATION_NAME = 'none'
ALL_NATION_INDEX = -1
GUI_NATIONS = tuple((n for i, n in enumerate(nations.AVAILABLE_NAMES)))
try:
    new_order_list = [ x for x in GUI_SETTINGS.nations_order if x in nations.AVAILABLE_NAMES ]
    for i, n in enumerate(nations.AVAILABLE_NAMES):
        if n not in new_order_list:
            new_order_list.append(n)

    GUI_NATIONS = tuple(new_order_list)
except AttributeError:
    LOG_ERROR('Could not read nations order from XML. Default order.')

GUI_NATIONS_ORDER_INDEX = dict(((n, i) for i, n in enumerate(GUI_NATIONS)))
GUI_NATIONS_ORDER_INDEX[NONE_NATION_NAME] = nations.NONE_INDEX

def nationCompareByName(first, second):
    return GUI_NATIONS_ORDER_INDEX[first] - GUI_NATIONS_ORDER_INDEX[second]


def nationCompareByIndex(first, second):

    def getNationName(idx):
        if idx != nations.NONE_INDEX:
            return nations.NAMES[idx]
        return NONE_NATION_NAME

    return nationCompareByName(getNationName(first), getNationName(second))


def getNationIndex(nationOrderIndex):
    if nationOrderIndex < len(GUI_NATIONS):
        return nations.INDICES.get(GUI_NATIONS[nationOrderIndex])
    else:
        return None


HTML_TEMPLATES_DIR_PATH = 'gui/{0:>s}.xml'
HTML_TEMPLATES_PATH_DELIMITER = ':'

class HtmlTemplatesCache(defaultdict):

    def __missing__(self, key):
        path = key.split(HTML_TEMPLATES_PATH_DELIMITER, 1)
        domain = HTML_TEMPLATES_DIR_PATH.format(path[0])
        ns = path[1] if len(path) > 1 else ''
        value = XMLCollection(domain, ns)
        value.load()
        self[key] = value
        return value


g_htmlTemplates = HtmlTemplatesCache()
if IS_DEVELOPMENT:

    def _reload_ht():
        for collection in g_htmlTemplates.itervalues():
            collection.load(clear=True)


def makeHtmlString(path, key, ctx = None, **kwargs):
    return g_htmlTemplates[path].format(key, ctx=ctx, **kwargs)


if IS_DEVELOPMENT:
    from debug_utils import LOG_DEBUG

    def buyVehicle(typeName):
        import BigWorld
        from items import vehicles
        nation, id = vehicles.VehicleDescr(typeName=typeName).type.id
        BigWorld.player().shop.buyVehicle(nation, id, True, True, 0, lambda *args: LOG_DEBUG(args))


    def showBattleResults():
        TEST_DATA = {'personal': {'spotted': 13,
                      'repair': 1545,
                      'xpPenalty': 0,
                      'creditsPenalty': 0,
                      'damageAssistedTrack': 0,
                      'killerID': 0,
                      'damageReceived': 1681,
                      'heHitsReceived': 0,
                      'originalCredits': 102491,
                      'piercedReceived': 5,
                      'premiumCreditsFactor10': 15,
                      'damageAssistedRadio': 0,
                      'shotsReceived': 31,
                      'premiumXPFactor10': 15,
                      'xp': 5701,
                      'droppedCapturePoints': 0,
                      'creditsContributionIn': 0,
                      'eventFreeXP': 0,
                      'damaged': 13,
                      'autoRepairCost': 1545,
                      'typeCompDescr': 9297,
                      'deathReason': -1,
                      'capturePoints': 0,
                      'aogasFactor10': 10,
                      'eventCredits': 0,
                      'health': 1878,
                      'details': {1248: {'spotted': 1,
                                         'hits': 1,
                                         'damageAssistedTrack': 0,
                                         'fire': 0,
                                         'deathReason': 0,
                                         'damageDealt': 1144,
                                         'crits': 65602,
                                         'pierced': 1,
                                         'damageAssistedRadio': 0,
                                         'he_hits': 0},
                                  1249: {'spotted': 1,
                                         'hits': 2,
                                         'damageAssistedTrack': 0,
                                         'fire': 1,
                                         'deathReason': 1,
                                         'damageDealt': 2700,
                                         'crits': 192,
                                         'pierced': 2,
                                         'damageAssistedRadio': 0,
                                         'he_hits': 0},
                                  1235: {'spotted': 1,
                                         'hits': 1,
                                         'damageAssistedTrack': 0,
                                         'fire': 0,
                                         'deathReason': 0,
                                         'damageDealt': 840,
                                         'crits': 100663536,
                                         'pierced': 1,
                                         'damageAssistedRadio': 0,
                                         'he_hits': 0},
                                  1236: {'spotted': 1,
                                         'hits': 1,
                                         'damageAssistedTrack': 0,
                                         'fire': 0,
                                         'deathReason': 0,
                                         'damageDealt': 590,
                                         'crits': 33554432,
                                         'pierced': 1,
                                         'damageAssistedRadio': 0,
                                         'he_hits': 0},
                                  1237: {'spotted': 1,
                                         'hits': 1,
                                         'damageAssistedTrack': 0,
                                         'fire': 0,
                                         'deathReason': 0,
                                         'damageDealt': 860,
                                         'crits': 67108880,
                                         'pierced': 1,
                                         'damageAssistedRadio': 0,
                                         'he_hits': 0},
                                  1239: {'spotted': 1,
                                         'hits': 2,
                                         'damageAssistedTrack': 0,
                                         'fire': 0,
                                         'deathReason': 0,
                                         'damageDealt': 1461,
                                         'crits': 65536,
                                         'pierced': 2,
                                         'damageAssistedRadio': 0,
                                         'he_hits': 0},
                                  1241: {'spotted': 1,
                                         'hits': 1,
                                         'damageAssistedTrack': 0,
                                         'fire': 0,
                                         'deathReason': 0,
                                         'damageDealt': 1470,
                                         'crits': 67108930,
                                         'pierced': 1,
                                         'damageAssistedRadio': 0,
                                         'he_hits': 0},
                                  1242: {'spotted': 1,
                                         'hits': 1,
                                         'damageAssistedTrack': 0,
                                         'fire': 0,
                                         'deathReason': 0,
                                         'damageDealt': 780,
                                         'crits': 144,
                                         'pierced': 1,
                                         'damageAssistedRadio': 0,
                                         'he_hits': 0},
                                  1243: {'spotted': 1,
                                         'hits': 2,
                                         'damageAssistedTrack': 0,
                                         'fire': 0,
                                         'deathReason': 0,
                                         'damageDealt': 1544,
                                         'crits': 327744,
                                         'pierced': 2,
                                         'damageAssistedRadio': 0,
                                         'he_hits': 0},
                                  1244: {'spotted': 1,
                                         'hits': 1,
                                         'damageAssistedTrack': 0,
                                         'fire': 1,
                                         'deathReason': 1,
                                         'damageDealt': 1650,
                                         'crits': 65554,
                                         'pierced': 1,
                                         'damageAssistedRadio': 0,
                                         'he_hits': 0},
                                  1245: {'spotted': 1,
                                         'hits': 1,
                                         'damageAssistedTrack': 0,
                                         'fire': 0,
                                         'deathReason': 0,
                                         'damageDealt': 1400,
                                         'crits': 80,
                                         'pierced': 1,
                                         'damageAssistedRadio': 0,
                                         'he_hits': 0},
                                  1246: {'spotted': 1,
                                         'hits': 1,
                                         'damageAssistedTrack': 0,
                                         'fire': 0,
                                         'deathReason': 0,
                                         'damageDealt': 600,
                                         'crits': 72,
                                         'pierced': 1,
                                         'damageAssistedRadio': 0,
                                         'he_hits': 0},
                                  1247: {'spotted': 1,
                                         'hits': 1,
                                         'damageAssistedTrack': 0,
                                         'fire': 0,
                                         'deathReason': 0,
                                         'damageDealt': 1111,
                                         'crits': 33554448,
                                         'pierced': 1,
                                         'damageAssistedRadio': 0,
                                         'he_hits': 0}},
                      'team': 1,
                      'achievements': [74,
                                       38,
                                       34,
                                       40,
                                       36,
                                       55],
                      'originalFreeXP': 285,
                      'isPremium': False,
                      'mileage': 686,
                      'freeXP': 285,
                      'noDamageShotsReceived': 26,
                      'kills': 13,
                      'eventTMenXP': 0,
                      'thits': 0,
                      'tmenXP': 5701,
                      'pierced': 16,
                      'credits': 102491,
                      'eventGold': 0,
                      'igrXPFactor10': 10,
                      'accountDBID': 161,
                      'autoEquipCost': (0, 0),
                      'gold': 0,
                      'tdamageDealt': 0,
                      'markOfMastery': 4,
                      'isTeamKiller': False,
                      'hits': 16,
                      'dossierPopUps': [(63, 1),
                                        (79, 4),
                                        (38, 1),
                                        (218, 16150),
                                        (42, 4),
                                        (62, 1),
                                        (43, 4),
                                        (40, 1),
                                        (34, 2),
                                        (55, 2),
                                        (36, 1),
                                        (74, 1),
                                        (12, 13),
                                        (58, 1),
                                        (2, 5701)],
                      'eventXP': 0,
                      'tkills': 0,
                      'potentialDamageReceived': 5575,
                      'damageDealt': 16150,
                      'autoLoadCost': (0, 160),
                      'shots': 16,
                      'he_hits': 0,
                      'originalXP': 5701,
                      'lifeTime': 180,
                      'questsProgress': {},
                      'creditsContributionOut': 0,
                      'dailyXPFactor10': 10},
         'players': {161: {'name': 'abtest2',
                           'prebattleID': 1142,
                           'igrType': 0,
                           'clanAbbrev': '',
                           'team': 1,
                           'clanDBID': 0}},
         'vehicles': {1233: {'spotted': 13,
                             'damageAssistedTrack': 0,
                             'killerID': 0,
                             'damageReceived': 1681,
                             'heHitsReceived': 0,
                             'piercedReceived': 5,
                             'damageAssistedRadio': 0,
                             'shotsReceived': 31,
                             'xp': 5701,
                             'droppedCapturePoints': 0,
                             'damaged': 13,
                             'typeCompDescr': 9297,
                             'deathReason': -1,
                             'capturePoints': 0,
                             'health': 1878,
                             'team': 1,
                             'achievements': [74,
                                              38,
                                              34,
                                              40,
                                              36,
                                              55],
                             'mileage': 686,
                             'noDamageShotsReceived': 26,
                             'kills': 13,
                             'thits': 0,
                             'pierced': 16,
                             'credits': 102491,
                             'accountDBID': 161,
                             'gold': 0,
                             'tdamageDealt': 0,
                             'isTeamKiller': False,
                             'hits': 16,
                             'tkills': 0,
                             'potentialDamageReceived': 5575,
                             'damageDealt': 16150,
                             'shots': 16,
                             'he_hits': 0,
                             'lifeTime': 180}},
         'common': {'finishReason': 1,
                    'guiType': 2,
                    'arenaCreateTime': 1381314520,
                    'duration': 180.90000000002328,
                    'arenaTypeID': 2,
                    'winnerTeam': 1,
                    'vehLockMode': 0,
                    'bonusType': 1},
         'arenaUniqueID': 1066533203928L}
        from gui.shared import events
        from gui.shared import g_eventBus
        g_eventBus.handleEvent(events.ShowWindowEvent(events.ShowWindowEvent.SHOW_BATTLE_RESULTS, {'testData': TEST_DATA}))


    def startBattle():
        import BigWorld
        from CurrentVehicle import g_currentVehicle
        from account_helpers import gameplay_ctx

        def response(code):
            LOG_DEBUG('Developers room creation result', code)
            if code >= 0:
                for team in (1, 2):
                    BigWorld.player().prb_teamReady(team, True, gameplay_ctx.getDefaultMask(), lambda code: None)

        BigWorld.player().prb_createDev(1024, 60, BigWorld.player().name)
        BigWorld.player().prb_ready(g_currentVehicle.invID, response)
# okay decompyling res/scripts/client/gui/__init__.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:25:31 EST

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
        TEST_DATA = {'personal': {'spotted': 5,
                      'repair': 327,
                      'xpPenalty': 0,
                      'creditsPenalty': 0,
                      'damageAssistedTrack': 0,
                      'killerID': 0,
                      'damageReceived': 0,
                      'heHitsReceived': 0,
                      'originalCredits': 19725,
                      'piercedReceived': 0,
                      'premiumCreditsFactor10': 15,
                      'damageAssistedRadio': 0,
                      'shotsReceived': 10,
                      'premiumXPFactor10': 15,
                      'xp': 1138,
                      'droppedCapturePoints': 0,
                      'creditsContributionIn': 0,
                      'eventFreeXP': 0,
                      'damaged': 5,
                      'autoRepairCost': 0,
                      'typeCompDescr': 14609,
                      'deathReason': -1,
                      'capturePoints': 0,
                      'aogasFactor10': 10,
                      'eventCredits': 0,
                      'health': 1950,
                      'details': {312: {'spotted': 1,
                                        'hits': 1,
                                        'damageAssistedTrack': 0,
                                        'fire': 0,
                                        'deathReason': 0,
                                        'damageDealt': 150,
                                        'crits': 0,
                                        'pierced': 1,
                                        'damageAssistedRadio': 0,
                                        'he_hits': 0},
                                  313: {'spotted': 1,
                                        'hits': 1,
                                        'damageAssistedTrack': 0,
                                        'fire': 0,
                                        'deathReason': 0,
                                        'damageDealt': 220,
                                        'crits': 0,
                                        'pierced': 1,
                                        'damageAssistedRadio': 0,
                                        'he_hits': 0},
                                  314: {'spotted': 1,
                                        'hits': 2,
                                        'damageAssistedTrack': 0,
                                        'fire': 0,
                                        'deathReason': 0,
                                        'damageDealt': 510,
                                        'crits': 16777216,
                                        'pierced': 2,
                                        'damageAssistedRadio': 0,
                                        'he_hits': 0},
                                  315: {'spotted': 1,
                                        'hits': 1,
                                        'damageAssistedTrack': 0,
                                        'fire': 0,
                                        'deathReason': 0,
                                        'damageDealt': 250,
                                        'crits': 0,
                                        'pierced': 1,
                                        'damageAssistedRadio': 0,
                                        'he_hits': 0},
                                  311: {'spotted': 1,
                                        'hits': 1,
                                        'damageAssistedTrack': 0,
                                        'fire': 0,
                                        'deathReason': 0,
                                        'damageDealt': 150,
                                        'crits': 0,
                                        'pierced': 1,
                                        'damageAssistedRadio': 0,
                                        'he_hits': 0}},
                      'team': 1,
                      'achievements': [151, 148, 55],
                      'originalFreeXP': 28,
                      'isPremium': False,
                      'mileage': 689,
                      'freeXP': 56,
                      'noDamageShotsReceived': 10,
                      'kills': 5,
                      'eventTMenXP': 0,
                      'thits': 0,
                      'tmenXP': 1138,
                      'pierced': 6,
                      'credits': 19725,
                      'eventGold': 0,
                      'igrXPFactor10': 10,
                      'accountDBID': 66,
                      'autoEquipCost': (0, 0),
                      'gold': 0,
                      'tdamageDealt': 0,
                      'markOfMastery': 0,
                      'isTeamKiller': False,
                      'hits': 6,
                      'dossierPopUps': [(63, 1),
                                        (55, 1),
                                        (2, 569),
                                        (62, 1),
                                        (151, 1),
                                        (148, 1)],
                      'eventXP': 0,
                      'tkills': 0,
                      'potentialDamageReceived': 261,
                      'damageDealt': 1280,
                      'autoLoadCost': (0, 0),
                      'shots': 9,
                      'he_hits': 0,
                      'originalXP': 569,
                      'lifeTime': 117,
                      'questsProgress': {'RU_02-31_Aug_2013_q3': (None, {}, {'bonusCount': 0,
                                                                   'xp': 1138}),
                                         'RU_02-31_Aug_2013_q1': (None, {}, {'bonusCount': 0,
                                                                   'kills': 5})},
                      'creditsContributionOut': 0,
                      'dailyXPFactor10': 20},
         'players': {66: {'name': 'zeo5',
                          'prebattleID': 149,
                          'igrType': 0,
                          'clanAbbrev': '',
                          'team': 1,
                          'clanDBID': 0}},
         'vehicles': {304: {'spotted': 5,
                            'damageAssistedTrack': 0,
                            'killerID': 0,
                            'damageReceived': 0,
                            'heHitsReceived': 0,
                            'piercedReceived': 0,
                            'damageAssistedRadio': 0,
                            'shotsReceived': 10,
                            'xp': 569,
                            'droppedCapturePoints': 0,
                            'damaged': 5,
                            'typeCompDescr': 14609,
                            'deathReason': -1,
                            'capturePoints': 0,
                            'health': 1950,
                            'team': 1,
                            'achievements': [151, 148, 55],
                            'mileage': 689,
                            'noDamageShotsReceived': 10,
                            'kills': 5,
                            'thits': 0,
                            'pierced': 6,
                            'credits': 19725,
                            'accountDBID': 66,
                            'gold': 0,
                            'tdamageDealt': 0,
                            'isTeamKiller': False,
                            'hits': 6,
                            'tkills': 0,
                            'potentialDamageReceived': 261,
                            'damageDealt': 1280,
                            'shots': 9,
                            'he_hits': 0,
                            'lifeTime': 117}},
         'common': {'finishReason': 1,
                    'guiType': 2,
                    'arenaCreateTime': 1376902521,
                    'duration': 117.70000000018626,
                    'arenaTypeID': 2,
                    'winnerTeam': 1,
                    'vehLockMode': 0,
                    'bonusType': 1},
         'arenaUniqueID': 649916964217L}
        from gui.shared import events
        from gui.shared import g_eventBus
        g_eventBus.handleEvent(events.ShowWindowEvent(events.ShowWindowEvent.SHOW_BATTLE_RESULTS, {'testData': TEST_DATA}))
        return None


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
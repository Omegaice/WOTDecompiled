# Embedded file name: scripts/client/account_helpers/AccountSettings.py
import BigWorld, Settings, Event, pickle, base64
from account_helpers import gameplay_ctx
KEY_FILTERS = 'filters'
KEY_SETTINGS = 'settings'
KEY_FAVORITES = 'favorites'
CAROUSEL_FILTER = 'CAROUSEL_FILTER'
BARRACKS_FILTER = 'barracks_filter'
VEHICLE_BUY_WINDOW_SETTINGS = 'vehicleBuyWindowSettings'
CURRENT_VEHICLE = 'current'
DEFAULT_VALUES = {KEY_FILTERS: {'shop_current': (-1, 'vehicle'),
               'shop_vehicle': (5, 'lightTank', 'mediumTank', 'heavyTank', 'at-spg', 'spg', 'locked'),
               'shop_module': (5, 'vehicleGun', 'vehicleTurret', 'vehicleEngine', 'vehicleChassis', 'vehicleRadio', 'myVehicles', 0, 'locked', 'inHangar'),
               'shop_shell': (4, 'ARMOR_PIERCING', 'ARMOR_PIERCING_CR', 'HOLLOW_CHARGE', 'HIGH_EXPLOSIVE', 'myVehicleGun', 0),
               'shop_optionalDevice': ('myVehicle', 0, 'onVehicle'),
               'shop_equipment': ('myVehicle', 0, 'onVehicle'),
               'inventory_current': (-1, 'vehicle'),
               'inventory_vehicle': (5, 'lightTank', 'mediumTank', 'heavyTank', 'at-spg', 'spg', 'brocken', 'locked'),
               'inventory_module': (5, 'vehicleGun', 'vehicleTurret', 'vehicleEngine', 'vehicleChassis', 'vehicleRadio', 'myVehicles', 0),
               'inventory_shell': (4, 'ARMOR_PIERCING', 'ARMOR_PIERCING_CR', 'HOLLOW_CHARGE', 'HIGH_EXPLOSIVE', 'myVehicleGun', 0),
               'inventory_optionalDevice': ('myVehicle', 0, 'onVehicle'),
               'inventory_equipment': ('myVehicle', 0, 'onVehicle'),
               CAROUSEL_FILTER: {'nation': -1,
                                 'tankType': -1,
                                 'ready': False},
               BARRACKS_FILTER: {'nation': -1,
                                 'role': 'None',
                                 'tankType': 'None',
                                 'location': 3,
                                 'nationID': None}},
 KEY_FAVORITES: {CURRENT_VEHICLE: 0},
 KEY_SETTINGS: {'vehicleSellDialog': {'isOpened': False},
                'tankmanDropSkillIdx': 0,
                'cursor': False,
                'arcade': {'mixing': {'alpha': 90,
                                      'type': 0},
                           'gunTag': {'alpha': 90,
                                      'type': 0},
                           'centralTag': {'alpha': 90,
                                          'type': 0},
                           'net': {'alpha': 90,
                                   'type': 0},
                           'reloader': {'alpha': 90,
                                        'type': 0},
                           'condition': {'alpha': 90,
                                         'type': 0},
                           'cassette': {'alpha': 90,
                                        'type': 0}},
                'sniper': {'mixing': {'alpha': 90,
                                      'type': 0},
                           'gunTag': {'alpha': 90,
                                      'type': 0},
                           'centralTag': {'alpha': 90,
                                          'type': 0},
                           'net': {'alpha': 90,
                                   'type': 0},
                           'reloader': {'alpha': 90,
                                        'type': 0},
                           'condition': {'alpha': 90,
                                         'type': 0},
                           'cassette': {'alpha': 90,
                                        'type': 0}},
                'markers': {'ally': {'markerBaseIcon': False,
                                     'markerBaseLevel': False,
                                     'markerBaseHpIndicator': False,
                                     'markerBaseDamage': True,
                                     'markerBaseHp': 0,
                                     'markerBaseVehicleName': False,
                                     'markerBasePlayerName': True,
                                     'markerAltIcon': True,
                                     'markerAltLevel': True,
                                     'markerAltHpIndicator': True,
                                     'markerAltDamage': True,
                                     'markerAltHp': 1,
                                     'markerAltVehicleName': True,
                                     'markerAltPlayerName': False},
                            'enemy': {'markerBaseIcon': False,
                                      'markerBaseLevel': False,
                                      'markerBaseHpIndicator': False,
                                      'markerBaseDamage': True,
                                      'markerBaseHp': 0,
                                      'markerBaseVehicleName': False,
                                      'markerBasePlayerName': True,
                                      'markerAltIcon': True,
                                      'markerAltLevel': True,
                                      'markerAltHpIndicator': True,
                                      'markerAltDamage': True,
                                      'markerAltHp': 1,
                                      'markerAltVehicleName': True,
                                      'markerAltPlayerName': False},
                            'dead': {'markerBaseIcon': False,
                                     'markerBaseLevel': False,
                                     'markerBaseHpIndicator': False,
                                     'markerBaseDamage': True,
                                     'markerBaseHp': 0,
                                     'markerBaseVehicleName': False,
                                     'markerBasePlayerName': True,
                                     'markerAltIcon': True,
                                     'markerAltLevel': True,
                                     'markerAltHpIndicator': True,
                                     'markerAltDamage': True,
                                     'markerAltHp': 1,
                                     'markerAltVehicleName': True,
                                     'markerAltPlayerName': False}},
                VEHICLE_BUY_WINDOW_SETTINGS: True,
                'showVehicleIcon': False,
                'showVehicleLevel': False,
                'showExInf4Destroyed': False,
                'ingameHelpVersion': -1,
                'isColorBlind': False,
                'useServerAim': False,
                'showVehiclesCounter': True,
                'minimapAlpha': 0,
                'minimapSize': 0,
                'nationalVoices': False,
                'players_panel': {'state': 'medium',
                                  'showLevels': True,
                                  'showTypes': True},
                'gameplayMask': gameplay_ctx.getDefaultMask(),
                'statsSorting': {'iconType': 'tank',
                                 'sortDirection': 'descending'},
                'backDraftInvert': False,
                'quests': {'lastVisitTime': -1,
                           'visited': []}}}

class AccountSettings(object):
    onSettingsChanging = Event.Event()
    version = 7
    __cache = {'login': None,
     'section': None}
    __isFirstRun = True

    @staticmethod
    def __readSection(ds, name):
        if not ds.has_key(name):
            ds.write(name, '')
        return ds[name]

    @staticmethod
    def __readUserSection():
        if AccountSettings.__isFirstRun:
            AccountSettings.convert()
            AccountSettings.__isFirstRun = False
        userLogin = getattr(BigWorld.player(), 'name', '')
        if AccountSettings.__cache['login'] != userLogin:
            ads = AccountSettings.__readSection(Settings.g_instance.userPrefs, Settings.KEY_ACCOUNT_SETTINGS)
            for key, section in ads.items():
                if key == 'account' and section.readString('login') == userLogin:
                    AccountSettings.__cache['login'] = userLogin
                    AccountSettings.__cache['section'] = section
                    break
            else:
                newSection = ads.createSection('account')
                newSection.writeString('login', userLogin)
                AccountSettings.__cache['login'] = userLogin
                AccountSettings.__cache['section'] = newSection

        return AccountSettings.__cache['section']

    @staticmethod
    def convert():
        ads = AccountSettings.__readSection(Settings.g_instance.userPrefs, Settings.KEY_ACCOUNT_SETTINGS)
        currVersion = ads.readInt('version', 0)
        if currVersion != AccountSettings.version:
            if currVersion < 1:
                for key, section in ads.items()[:]:
                    newSection = ads.createSection('account')
                    newSection.copy(section)
                    newSection.writeString('login', key)
                    ads.deleteSection(key)

            if currVersion < 2:
                MARKER_SETTINGS_MAP = {'showVehicleIcon': 'markerBaseIcon',
                 'showVehicleLevel': 'markerBaseLevel',
                 'showExInf4Destroyed': 'markerBaseDead'}
                for key, section in ads.items()[:]:
                    if key == 'account':
                        accSettings = AccountSettings.__readSection(section, KEY_SETTINGS)
                        defaultMarker = DEFAULT_VALUES[KEY_SETTINGS]['markers'].copy()
                        needUpdate = False
                        for key1, section1 in accSettings.items()[:]:
                            if key1 in MARKER_SETTINGS_MAP:
                                defaultMarker[MARKER_SETTINGS_MAP[key1]] = pickle.loads(base64.b64decode(accSettings.readString(key1)))
                                accSettings.deleteSection(key1)
                                needUpdate = True

                        if needUpdate:
                            accSettings.write('markers', base64.b64encode(pickle.dumps(defaultMarker)))

            if currVersion < 3:
                for key, section in ads.items()[:]:
                    if key == 'account':
                        accSettings = AccountSettings.__readSection(section, KEY_SETTINGS)
                        defaultCursor = DEFAULT_VALUES[KEY_SETTINGS]['arcade'].copy()
                        cassetteDefValues = DEFAULT_VALUES[KEY_SETTINGS]['arcade'].copy()['cassette']
                        for key1, section1 in accSettings.items()[:]:
                            if key1 == 'cursors':
                                defaultCursor = pickle.loads(base64.b64decode(section1.asString))
                                defaultCursor['cassette'] = cassetteDefValues
                                accSettings.deleteSection(key1)
                                break

                        accSettings.write('cursors', base64.b64encode(pickle.dumps(defaultCursor)))

            if currVersion < 4:
                for key, section in ads.items()[:]:
                    if key == 'account':
                        accSettings = AccountSettings.__readSection(section, KEY_SETTINGS)
                        defaultCursor = DEFAULT_VALUES[KEY_SETTINGS]['arcade'].copy()
                        for key1, section1 in accSettings.items()[:]:
                            if key1 == 'cursors':
                                defaultCursor = pickle.loads(base64.b64decode(section1.asString))
                                accSettings.deleteSection(key1)
                                break

                        accSettings.write('arcade', base64.b64encode(pickle.dumps(defaultCursor)))

            if currVersion < 5:
                for key, section in ads.items()[:]:
                    if key == 'account':
                        accSettings = AccountSettings.__readSection(section, KEY_SETTINGS)
                        for key1, section1 in accSettings.items()[:]:
                            if key1 == 'markers':
                                accSettings.deleteSection(key1)

            if currVersion < 6:
                for key, section in ads.items()[:]:
                    if key == 'account':
                        accSettings = AccountSettings.__readSection(section, KEY_SETTINGS)
                        defaultSorting = DEFAULT_VALUES[KEY_SETTINGS]['statsSorting'].copy()
                        accSettings.write('statsSorting', base64.b64encode(pickle.dumps(defaultSorting)))

            if currVersion < 7:
                for key, section in ads.items()[:]:
                    if key == 'account':
                        accSettings = AccountSettings.__readSection(section, KEY_SETTINGS)
                        result = DEFAULT_VALUES[KEY_SETTINGS]['sniper'].copy()
                        for settingName, settingPickle in accSettings.items()[:]:
                            if settingName == 'sniper':
                                settingValues = pickle.loads(base64.b64decode(settingPickle.asString))
                                accSettings.deleteSection(settingName)
                                try:
                                    for k, v in settingValues.iteritems():
                                        newName = k[3].lower() + k[4:]
                                        result[newName] = v

                                except Exception:
                                    pass

                            break

                        accSettings.write('sniper', base64.b64encode(pickle.dumps(result)))

            ads.writeInt('version', AccountSettings.version)

    @staticmethod
    def getFilterDefault(name):
        return DEFAULT_VALUES[KEY_FILTERS].get(name, None)

    @staticmethod
    def getFilter(name):
        return AccountSettings.__getValue(name, KEY_FILTERS)

    @staticmethod
    def setFilter(name, value):
        AccountSettings.__setValue(name, value, KEY_FILTERS)

    @staticmethod
    def getSettingsDefault(name):
        return DEFAULT_VALUES[KEY_SETTINGS].get(name, None)

    @staticmethod
    def getSettings(name):
        return AccountSettings.__getValue(name, KEY_SETTINGS)

    @staticmethod
    def setSettings(name, value):
        AccountSettings.__setValue(name, value, KEY_SETTINGS)

    @staticmethod
    def getFavorites(name):
        return AccountSettings.__getValue(name, KEY_FAVORITES)

    @staticmethod
    def setFavorites(name, value):
        AccountSettings.__setValue(name, value, KEY_FAVORITES)

    @staticmethod
    def __getValue(name, type):
        if DEFAULT_VALUES[type].has_key(name):
            fds = AccountSettings.__readSection(AccountSettings.__readUserSection(), type)
            try:
                if fds.has_key(name):
                    return pickle.loads(base64.b64decode(fds.readString(name)))
            except:
                pass

            return DEFAULT_VALUES[type][name]
        else:
            return None

    @staticmethod
    def __setValue(name, value, type):
        if DEFAULT_VALUES[type].has_key(name) and AccountSettings.__getValue(name, type) != value:
            fds = AccountSettings.__readSection(AccountSettings.__readUserSection(), type)
            if DEFAULT_VALUES[type][name] != value:
                fds.write(name, base64.b64encode(pickle.dumps(value)))
            else:
                fds.deleteSection(name)
            AccountSettings.onSettingsChanging(name, value)
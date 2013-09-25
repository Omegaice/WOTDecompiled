# Embedded file name: scripts/client/gui/shared/utils/__init__.py
import types
import itertools
import AccountCommands
from items import vehicles as vehs_core
ScalarTypes = (types.IntType,
 types.LongType,
 types.FloatType,
 types.BooleanType) + types.StringTypes
SHELLS_COUNT_PROP_NAME = 'shellsCount'
RELOAD_TIME_PROP_NAME = 'reloadTime'
RELOAD_MAGAZINE_TIME_PROP_NAME = 'reloadMagazineTime'
SHELL_RELOADING_TIME_PROP_NAME = 'shellReloadingTime'
DISPERSION_RADIUS_PROP_NAME = 'dispersionRadius'
AIMING_TIME_PROP_NAME = 'aimingTime'
PIERCING_POWER_PROP_NAME = 'piercingPower'
DAMAGE_PROP_NAME = 'damage'
SHELLS_PROP_NAME = 'shells'
CLIP_VEHICLES_PROP_NAME = 'clipVehicles'
UNICHARGED_VEHICLES_PROP_NAME = 'uniChargedVehicles'
VEHICLES_PROP_NAME = 'vehicles'
CLIP_VEHICLES_CD_PROP_NAME = 'clipVehiclesCD'
GUN_RELOADING_TYPE = 'gunReloadingType'
GUN_CAN_BE_CLIP = 1
GUN_CLIP = 2
GUN_NORMAL = 4
CLIP_ICON_PATH = '../maps/icons/modules/magazineGunIcon.png'
EXTRA_MODULE_INFO = 'extraModuleInfo'
_FLASH_OBJECT_SYS_ATTRS = ('isPrototypeOf', 'propertyIsEnumerable', 'hasOwnProperty')

class CONST_CONTAINER:

    @classmethod
    def ALL(cls):
        return tuple([ v for k, v in cls.__dict__.iteritems() if not k.startswith('_') and type(v) in ScalarTypes ])


def flashObject2Dict(obj):
    if hasattr(obj, 'children'):
        return dict(map(lambda (k, v): (k, flashObject2Dict(v)), itertools.ifilter(lambda (x, y): x not in _FLASH_OBJECT_SYS_ATTRS, obj.children.iteritems())))
    return obj


def code2str(code):
    if code == AccountCommands.RES_SUCCESS:
        return 'Request succedded'
    if code == AccountCommands.RES_STREAM:
        return 'Stream is sent to the client'
    if code == AccountCommands.RES_CACHE:
        return 'Data is taken from cache'
    if code == AccountCommands.RES_FAILURE:
        return 'Unknown reason'
    if code == AccountCommands.RES_WRONG_ARGS:
        return 'Wrong arguments'
    if code == AccountCommands.RES_NON_PLAYER:
        return 'Account become non player'
    if code == AccountCommands.RES_SHOP_DESYNC:
        return 'Shop cache is desynchronized'
    if code == AccountCommands.RES_COOLDOWN:
        return 'Identical requests cooldown'
    if code == AccountCommands.RES_HIDDEN_DOSSIER:
        return 'Player dossier is hidden'
    if code == AccountCommands.RES_CENTER_DISCONNECTED:
        return 'Dossiers are unavailable'
    return 'Unknown error code'


def isVehicleObserver(vehTypeCompDescr):
    item_type_id, nation_id, item_id_within_nation = vehs_core.parseIntCompactDescr(vehTypeCompDescr)
    return 'observer' in vehs_core.g_cache.vehicle(nation_id, item_id_within_nation).tags
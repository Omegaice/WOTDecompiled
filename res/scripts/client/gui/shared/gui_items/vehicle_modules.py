# 2013.11.15 11:26:54 EST
# Embedded file name: scripts/client/gui/shared/gui_items/vehicle_modules.py
import BigWorld
import nations
from helpers import i18n
from items import vehicles as veh_core
from gui.shared.gui_items import FittingItem, _ICONS_MASK
from gui.shared.utils import ParametersCache, CLIP_VEHICLES_CD_PROP_NAME
MODULE_TYPES_ORDER = ('vehicleGun', 'vehicleTurret', 'vehicleEngine', 'vehicleChassis', 'vehicleRadio', 'vehicleFuelTank')
MODULE_TYPES_ORDER_INDICES = dict(((n, i) for i, n in enumerate(MODULE_TYPES_ORDER)))
SHELL_TYPES_ORDER = ('ARMOR_PIERCING', 'ARMOR_PIERCING_CR', 'HOLLOW_CHARGE', 'HIGH_EXPLOSIVE')
SHELL_TYPES_ORDER_INDICES = dict(((n, i) for i, n in enumerate(SHELL_TYPES_ORDER)))

class VehicleModule(FittingItem):
    """
    Root vehicle module class.
    """

    def __init__(self, intCompactDescr, proxy = None, descriptor = None):
        super(VehicleModule, self).__init__(intCompactDescr, proxy)
        self._vehicleModuleDescriptor = descriptor

    @property
    def icon(self):
        return self.descriptor.icon[0]

    @property
    def descriptor(self):
        if self._vehicleModuleDescriptor is not None:
            return self._vehicleModuleDescriptor
        else:
            return super(VehicleModule, self).descriptor

    def _sortByType(self, other):
        return MODULE_TYPES_ORDER_INDICES[self.itemTypeName] - MODULE_TYPES_ORDER_INDICES[other.itemTypeName]


class VehicleChassis(VehicleModule):
    """
    Vehicle chassis class.
    """

    def mayInstall(self, vehicle, slotIdx = 0):
        installPossible, reason = FittingItem.mayInstall(self, vehicle, slotIdx)
        if not installPossible and reason == 'too heavy':
            return (False, 'too heavy chassis')
        return (installPossible, reason)


class VehicleTurret(VehicleModule):
    """
    Vehicle turret class.
    """

    def mayInstall(self, vehicle, slotIdx = 0, gunCD = 0):
        return vehicle.descriptor.mayInstallTurret(self.intCD, gunCD)


class VehicleGun(VehicleModule):
    """
    Vehicle gun class.
    """

    def __init__(self, intCompactDescr, proxy = None, descriptor = None):
        super(VehicleGun, self).__init__(intCompactDescr, proxy, descriptor)
        self.defaultAmmo = self._getDefaultAmmo(proxy)

    def mayInstall(self, vehicle, slotIdx = 0):
        installPossible, reason = FittingItem.mayInstall(self, vehicle)
        if not installPossible and reason == 'not for current vehicle':
            return (False, 'need turret')
        return (installPossible, reason)

    def isClipGun(self, vehicleDescr = None):
        compatibles = ParametersCache.g_instance.getGunCompatibles(self.descriptor, vehicleDescr)
        clipVehicleList = compatibles[CLIP_VEHICLES_CD_PROP_NAME]
        if vehicleDescr is not None:
            if len(clipVehicleList) > 0:
                for cVdescr in clipVehicleList:
                    if cVdescr == vehicleDescr.type.compactDescr:
                        return True

        elif len(clipVehicleList) > 0 and len(compatibles['vehicles']) == 0:
            return True
        return False

    def _getDefaultAmmo(self, proxy):
        result = []
        shells = veh_core.getDefaultAmmoForGun(self.descriptor)
        for i in range(0, len(shells), 2):
            result.append(Shell(shells[i], defaultCount=shells[i + 1], proxy=proxy))

        return result


class VehicleEngine(VehicleModule):
    """
    Vehicle engine class.
    """
    pass


class VehicleFuelTank(VehicleModule):
    """
    Vehicle fuel tank class.
    """
    pass


class VehicleRadio(VehicleModule):
    """
    Vehicle radio class.
    """
    pass


class Shell(FittingItem):
    """
    Vehicle shells class.
    """

    def __init__(self, intCompactDescr, count = 0, defaultCount = 0, proxy = None, isBoughtForCredits = False):
        """
        Ctor.
        
        @param intCompactDescr: item int compact descriptor
        @param count: count of shells in ammo bay
        @param defaultCount: count default shells in ammo bay
        @param proxy: instance of ItemsRequester
        """
        FittingItem.__init__(self, intCompactDescr, proxy, isBoughtForCredits)
        self.count = count
        self.defaultCount = defaultCount

    def _getActionPrice(self, buyPrice, proxy):
        """ Overridden method for receiving special action price value for shells
        @param buyPrice:
        @param proxy:
        @return:
        """
        return (buyPrice[0] + buyPrice[1] * proxy.shop.exchangeRateForShellsAndEqs, buyPrice[1])

    @property
    def type(self):
        """ Returns shells type string (`HOLLOW_CHARGE` etc.). """
        return self.descriptor['kind']

    @property
    def longUserName(self):
        if self.nationID == nations.INDICES['germany']:
            caliber = float(self.descriptor['caliber']) / 10
            dimension = i18n.makeString('#item_types:shell/dimension/sm')
        elif self.nationID == nations.INDICES['usa']:
            caliber = float(self.descriptor['caliber']) / 25.4
            dimension = i18n.makeString('#item_types:shell/dimension/inch')
        else:
            caliber = self.descriptor['caliber']
            dimension = i18n.makeString('#item_types:shell/dimension/mm')
        return i18n.makeString('#item_types:shell/name') % {'kind': i18n.makeString('#item_types:shell/kinds/' + self.descriptor['kind']),
         'name': self.userName,
         'caliber': BigWorld.wg_getNiceNumberFormat(caliber),
         'dimension': dimension}

    @property
    def icon(self):
        return _ICONS_MASK[:-4] % {'type': self.itemTypeName,
         'subtype': '',
         'unicName': self.descriptor['icon'][0]}

    def getCtorArgs(self):
        return [self.intCD, self.count, self.defaultCount]

    def toDict(self):
        d = FittingItem.toDict(self)
        d.update({'count': self.count,
         'defaulCount': self.defaultCount,
         'kind': self.type})
        return d

    def _sortByType(self, other):
        return SHELL_TYPES_ORDER_INDICES[self.itemTypeName] - SHELL_TYPES_ORDER_INDICES[other.itemTypeName]
# okay decompyling res/scripts/client/gui/shared/gui_items/vehicle_modules.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:26:54 EST

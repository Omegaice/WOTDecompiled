# Embedded file name: scripts/client/gui/shared/gui_items/artefacts.py
__author__ = 'i_maliavko'
from debug_utils import *
from items import artefacts
from gui.shared.gui_items import FittingItem

class VehicleArtefact(FittingItem):
    """
    Root class for equipments and optional devices.
    """

    @property
    def icon(self):
        return self.descriptor.icon[0]

    def _getShortInfo(self, _ = None):
        return self.shortDescription

    @property
    def isStimulator(self):
        """ Is item stimulator which can increase crew role levels. """
        return isinstance(self.descriptor, artefacts.Stimulator)

    @property
    def crewLevelIncrease(self):
        """ Value of crew role levels increasing. """
        if not self.isStimulator:
            return 0
        return self.descriptor['crewLevelIncrease']


class Equipment(VehicleArtefact):
    """
    Equipment item.
    """

    def _getActionPrice(self, buyPrice, proxy):
        """ Overridden method for receiving special action price value for shells
        @param buyPrice:
        @param proxy:
        @return: (gold, credits)
        """
        return (buyPrice[0] + buyPrice[1] * proxy.shop.exchangeRateForShellsAndEqs, buyPrice[1])

    @property
    def tags(self):
        return self.descriptor.tags

    def mayInstall(self, vehicle, slotIdx = 0):
        for idx, eq in enumerate(vehicle.eqs):
            if idx == slotIdx or eq is None:
                continue
            if eq.intCD != self.intCD:
                installPossible = eq.descriptor.checkCompatibilityWithActiveEquipment(self.descriptor)
                if installPossible:
                    if not self.descriptor.checkCompatibilityWithEquipment(eq.descriptor):
                        return (False, 'not with installed equipment')

        return (True, '')


class OptionalDevice(VehicleArtefact):
    """
    Optional device item.
    """

    @property
    def isRemovable(self):
        return self.descriptor['removable']

    def mayInstall(self, vehicle, slotIdx):
        return vehicle.descriptor.mayInstallOptionalDevice(self.intCD, slotIdx)

    def mayRemove(self, vehicle):
        try:
            slotIdx = vehicle.optDevices.index(self)
            return vehicle.descriptor.mayRemoveOptionalDevice(slotIdx)
        except Exception:
            LOG_CURRENT_EXCEPTION()
            return (False, 'not installed on vehicle')
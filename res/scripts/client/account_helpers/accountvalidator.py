__author__ = 'i_maliavko'
from adisp import process, async
from items import vehicles, ITEM_TYPE_NAMES
from debug_utils import *
from gui.shared.utils.requesters import InventoryRequester

class AccountValidator:
    """
    Do validation of account's server data
    """

    class CODES:
        """
        Validation error codes
        """
        OK = 0
        INVENTORY_VEHICLE_MISMATCH = 1001
        INVENTORY_CHASSIS_MISMATCH = 1002
        INVENTORY_TURRET_MISMATCH = 1003
        INVENTORY_GUN_MISMATCH = 1004
        INVENTORY_ENGINE_MISMATCH = 1005
        INVENTORY_FUEL_TANK_MISMATCH = 1006
        INVENTORY_RADIO_MISMATCH = 1007
        INVENTORY_OPT_DEV_MISMATCH = 1009
        INVENTORY_SHELL_MISMATCH = 1010
        INVENTORY_EQ_MISMATCH = 1011

    def __init__(self):
        self.__inventory = InventoryRequester()

    def __validateInventoryVehicles(self):
        """
        Method validates inventory vehicles' data.
        @return: <CODES> error code
        """
        for invId, vehData in self.__inventory.getItems(vehicles._VEHICLE).iteritems():
            try:
                vehicles.VehicleDescr(compactDescr=vehData['compDescr'])
            except Exception:
                nationIdx, innation_id = vehicles.parseVehicleCompactDescr(vehData['compDescr'])
                LOG_ERROR('There is exception while validating vehicle', vehData['compDescr'], (nationIdx, innation_id))
                LOG_CURRENT_EXCEPTION()
                return self.CODES.INVENTORY_VEHICLE_MISMATCH

        return self.CODES.OK

    def __validateInventoryItem(self, type, errorCode):
        """
        Method validates inventory items' data.
        
        @param type: <int> type index of item
        @param errorCode: <CODES> code to return in error case
        
        @return: <CODES> eror code
        """
        for intCompactDescr in self.__inventory.getItems(type).iterkeys():
            try:
                vehicles.getDictDescr(intCompactDescr)
            except Exception:
                item_type_id, nationIdx, innation_id = vehicles.parseIntCompactDescr(intCompactDescr)
                LOG_ERROR('There is exception while validation item (%s)' % ITEM_TYPE_NAMES[type], intCompactDescr, (item_type_id, nationIdx, innation_id))
                LOG_CURRENT_EXCEPTION()
                return errorCode

        return self.CODES.OK

    @async
    @process
    def start(self, callback):
        """
        Starting validation. Iterates through all validation
        handlers. Breaks after first error caseand return code.
        
        @return: <CODES> error code
        """
        handlers = [lambda : self.__validateInventoryItem(vehicles._CHASSIS, self.CODES.INVENTORY_CHASSIS_MISMATCH),
         lambda : self.__validateInventoryItem(vehicles._TURRET, self.CODES.INVENTORY_TURRET_MISMATCH),
         lambda : self.__validateInventoryItem(vehicles._GUN, self.CODES.INVENTORY_GUN_MISMATCH),
         lambda : self.__validateInventoryItem(vehicles._ENGINE, self.CODES.INVENTORY_ENGINE_MISMATCH),
         lambda : self.__validateInventoryItem(vehicles._FUEL_TANK, self.CODES.INVENTORY_FUEL_TANK_MISMATCH),
         lambda : self.__validateInventoryItem(vehicles._RADIO, self.CODES.INVENTORY_RADIO_MISMATCH),
         lambda : self.__validateInventoryItem(vehicles._OPTIONALDEVICE, self.CODES.INVENTORY_OPT_DEV_MISMATCH),
         lambda : self.__validateInventoryItem(vehicles._SHELL, self.CODES.INVENTORY_SHELL_MISMATCH),
         lambda : self.__validateInventoryItem(vehicles._EQUIPMENT, self.CODES.INVENTORY_EQ_MISMATCH),
         self.__validateInventoryVehicles]
        yield self.__inventory.request()
        for handler in handlers:
            code = handler()
            if code > 0:
                callback(code)
                return

        callback(self.CODES.OK)

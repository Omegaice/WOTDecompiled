import time

class VehicleCustomizationModel:
    _playerEmblems = None
    _playerInscriptions = None
    _playerEmblemsInit = None
    _playerInscriptionsInit = None

    @classmethod
    def setVehicleDescriptor(cls, vehicleDescriptor):
        VehicleCustomizationModel._playerEmblemsInit = list(vehicleDescriptor.playerEmblems)
        VehicleCustomizationModel._playerInscriptionsInit = list(vehicleDescriptor.playerInscriptions)
        VehicleCustomizationModel._playerEmblems = list(vehicleDescriptor.playerEmblems)
        VehicleCustomizationModel._playerInscriptions = list(vehicleDescriptor.playerInscriptions)

    @classmethod
    def updateVehicleSticker(cls, itemType, itemID = None, itemPosition = 0, duration = 0):
        if itemType == 'player':
            list = VehicleCustomizationModel._playerEmblems
            initList = VehicleCustomizationModel._playerEmblemsInit
            sticker = (itemID, round(time.time()), duration)
        else:
            list = VehicleCustomizationModel._playerInscriptions
            initList = VehicleCustomizationModel._playerInscriptionsInit
            sticker = (itemID,
             round(time.time()),
             duration,
             0)
        list[itemPosition] = sticker if itemID is not None else initList[itemPosition]
        return

    @classmethod
    def getVehicleModel(cls):
        return (tuple(VehicleCustomizationModel._playerEmblems), tuple(VehicleCustomizationModel._playerInscriptions))

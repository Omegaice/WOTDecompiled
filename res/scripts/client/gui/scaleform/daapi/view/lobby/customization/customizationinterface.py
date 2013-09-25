import Event
from gui.Scaleform.framework.entities.DAAPIModule import DAAPIModule

class CustomizationInterface(DAAPIModule):
    _eventManager = Event.EventManager()
    onDataInited = Event.Event(_eventManager)
    onCustomizationChangeSuccess = Event.Event(_eventManager)
    onCustomizationChangeFailed = Event.Event(_eventManager)
    onCustomizationDropSuccess = Event.Event(_eventManager)
    onCustomizationDropFailed = Event.Event(_eventManager)
    onCurrentItemChange = Event.Event(_eventManager)

    def __init__(self, name, nationId, position = -1):
        super(CustomizationInterface, self).__init__()
        self._name = name
        self._position = position
        self._nationID = nationId

    def fetchCurrentItem(self, vehDescr):
        pass

    def invalidateData(self, vehType, refresh = False):
        pass

    def isNewItemSelected(self):
        return False

    def getSelectedItemCost(self):
        return (-1, 0)

    def getSelectedItemsCount(self, *args):
        return int(self.isNewItemSelected())

    def getItemCost(self, itemId, priceIndex):
        return (-1, 0)

    def isCurrentItemRemove(self):
        return True

    def isEnabled(self):
        return True

    def change(self, vehInvID, section):
        self.onCustomizationChangeFailed('Section {0:>s} is not implemented'.format(self._name))

    def drop(self, vehInvID, kind):
        self.onCustomizationDropFailed('Section {0:>s} is not implemented'.format(self._name))

    def update(self, vehicleDescr):
        pass

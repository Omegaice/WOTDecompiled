import BigWorld
from debug_utils import LOG_ERROR
from gui.Scaleform.framework.entities.DAAPIDataProvider import DAAPIDataProvider

class ChannelsDataProvider(DAAPIDataProvider):

    def __init__(self):
        super(ChannelsDataProvider, self).__init__()
        self.__data = {}
        self.__list = []
        self.__isInited = False

    def initGUI(self, flashObj):
        if not self.__isInited:
            self.setFlashObject(flashObj, autoPopulate=False)
            self.create()
            self.__isInited = True

    def finiGUI(self):
        if self.__isInited:
            self.destroy()
            self.__isInited = False

    def clear(self):
        self.__data.clear()
        self.__list = []

    def addItem(self, clientID, data):
        item = {'clientID': clientID,
         'label': data['label'],
         'canClose': data.get('canClose', False),
         'isNotified': data.get('isNotified', False),
         'icon': data.get('icon'),
         'order': data.get('order', (0, BigWorld.time()))}
        self.__data[clientID] = item
        self.buildList()
        self.refresh()

    def removeItem(self, clientID):
        if clientID in self.__data:
            self.__data.pop(clientID)
            self.buildList()
            self.refresh()

    def setItemField(self, clientID, key, value):
        if clientID in self.__data:
            item = self.__data[clientID]
            if key in item:
                item[key] = value
                self.buildList()
                self.refresh()
            else:
                LOG_ERROR('Key is invalid', key)

    @property
    def collection(self):
        return self.__list

    def buildList(self):
        self.__list = sorted(self.__data.itervalues(), key=lambda item: item['order'])

    def emptyItem(self):
        return {'clientID': 0,
         'label': '',
         'canClose': False,
         'isNotified': False,
         'icon': None}

    def refresh(self):
        if self.flashObject:
            super(ChannelsDataProvider, self).refresh()

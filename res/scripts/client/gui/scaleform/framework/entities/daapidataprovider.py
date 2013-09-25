from abc import ABCMeta, abstractmethod, abstractproperty
from debug_utils import LOG_DEBUG
from gui.Scaleform.framework.entities.DAAPIModule import DAAPIModule

class DAAPIDataProvider(DAAPIModule):
    __metaclass__ = ABCMeta

    def __init__(self):
        super(DAAPIDataProvider, self).__init__()

    @abstractproperty
    def collection(self):
        pass

    @abstractmethod
    def buildList(self, *args):
        pass

    @abstractmethod
    def emptyItem(self):
        pass

    def lengthHandler(self):
        return len(self.collection)

    def requestItemAtHandler(self, idx):
        if -1 < idx < self.pyLength():
            return self.collection[int(idx)]
        else:
            return None

    def requestItemRangeHandler(self, startIndex, endIndex):
        items = self.collection[int(startIndex):int(endIndex) + 1]
        return items

    def refresh(self):
        self.flashObject.invalidate(self.pyLength())

    def pyLength(self):
        return len(self.collection)

    def pyRequestItemAt(self, idx):
        if -1 < idx < self.pyLength():
            return self.collection[int(idx)]
        else:
            return None

    def pyRequestItemRange(self, startIndex, endIndex):
        return self.collection[int(startIndex):int(endIndex) + 1]

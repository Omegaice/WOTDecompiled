import nations
from gui import GUI_NATIONS
from gui.Scaleform.framework.entities.abstract.UtilsManagerMeta import UtilsManagerMeta

class UtilsManager(UtilsManagerMeta):

    def getGUINations(self):
        return GUI_NATIONS

    def getNationNames(self):
        return nations.NAMES

    def getNationIndices(self):
        return nations.INDICES

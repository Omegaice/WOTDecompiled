# Embedded file name: scripts/client/gui/Scaleform/managers/GlobalVarsManager.py
from gui import GUI_SETTINGS
from gui.Scaleform.framework.entities.abstract.GlobalVarsMgrMeta import GlobalVarsMgrMeta
from helpers import getClientOverride
import constants

class GlobalVarsManager(GlobalVarsMgrMeta):

    def __init__(self):
        super(GlobalVarsManager, self).__init__()
        self.__isTutorialDisabled = False
        self.__isTutorialRunning = False

    def isDevelopment(self):
        return constants.IS_DEVELOPMENT

    def isShowLangaugeBar(self):
        return GUI_SETTINGS.isShowLanguageBar

    def isShowServerStats(self):
        return constants.IS_SHOW_SERVER_STATS

    def isChina(self):
        return constants.IS_CHINA

    def isTutorialDisabled(self):
        return self.__isTutorialDisabled

    def setTutorialDisabled(self, isDisabled):
        self.__isTutorialDisabled = isDisabled

    def isTutorialRunning(self):
        return self.__isTutorialRunning

    def setTutorialRunning(self, isRunning):
        self.__isTutorialRunning = isRunning

    def isFreeXpToTankman(self):
        return GUI_SETTINGS.freeXpToTankman

    def getLocaleOverride(self):
        return getClientOverride()
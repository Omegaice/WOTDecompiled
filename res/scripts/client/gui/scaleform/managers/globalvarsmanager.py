# 2013.11.15 11:26:39 EST
# Embedded file name: scripts/client/gui/Scaleform/managers/GlobalVarsManager.py
from gui import GUI_SETTINGS, game_control
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

    def isKorea(self):
        return constants.IS_KOREA

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

    def isRoamingEnabled(self):
        return game_control.g_instance.roaming.isEnabled()

    def isInRoaming(self):
        return game_control.g_instance.roaming.isInRoaming()

    def isWalletAvailable(self):
        return game_control.g_instance.wallet.isAvailable
# okay decompyling res/scripts/client/gui/scaleform/managers/globalvarsmanager.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:26:39 EST

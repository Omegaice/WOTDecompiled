from gui.Scaleform.framework.entities.DAAPIModule import DAAPIModule

class GlobalVarsMgrMeta(DAAPIModule):

    def isDevelopment(self):
        self._printOverrideError('isDevelopment')

    def isShowLangaugeBar(self):
        self._printOverrideError('isShowLangaugeBar')

    def isShowServerStats(self):
        self._printOverrideError('isShowServerStats')

    def isChina(self):
        self._printOverrideError('isChina')

    def isTutorialDisabled(self):
        self._printOverrideError('isTutorialDisabled')

    def setTutorialDisabled(self, isDisabled):
        self._printOverrideError('setTutorialDisabled')

    def isTutorialRunning(self):
        self._printOverrideError('isTutorialRunning')

    def setTutorialRunning(self, isRunning):
        self._printOverrideError('setTutorialRunning')

    def isFreeXpToTankman(self):
        self._printOverrideError('isFreeXpToTankman')

    def getLocaleOverride(self):
        self._printOverrideError('getLocaleOverride')

# Embedded file name: scripts/client/gui/Scaleform/daapi/view/meta/LobbyHeaderMeta.py
from gui.Scaleform.framework.entities.DAAPIModule import DAAPIModule

class LobbyHeaderMeta(DAAPIModule):

    def menuItemClick(self, alias):
        self._printOverrideError('menuItemClick')

    def showLobbyMenu(self):
        self._printOverrideError('showLobbyMenu')

    def showExchangeWindow(self, initData):
        self._printOverrideError('showExchangeWindow')

    def showExchangeXPWindow(self, initData):
        self._printOverrideError('showExchangeXPWindow')

    def showPremiumDialog(self, event):
        self._printOverrideError('showPremiumDialog')

    def onPayment(self):
        self._printOverrideError('onPayment')

    def as_setScreenS(self, alias):
        if self._isDAAPIInited():
            return self.flashObject.as_setScreen(alias)

    def as_creditsResponseS(self, credits):
        if self._isDAAPIInited():
            return self.flashObject.as_creditsResponse(credits)

    def as_goldResponseS(self, gold):
        if self._isDAAPIInited():
            return self.flashObject.as_goldResponse(gold)

    def as_setFreeXPS(self, freeXP):
        if self._isDAAPIInited():
            return self.flashObject.as_setFreeXP(freeXP)

    def as_nameResponseS(self, name, isTeamKiller, isClan):
        if self._isDAAPIInited():
            return self.flashObject.as_nameResponse(name, isTeamKiller, isClan)

    def as_setClanEmblemS(self, tID):
        if self._isDAAPIInited():
            return self.flashObject.as_setClanEmblem(tID)

    def as_setProfileTypeS(self, premiumLabel):
        if self._isDAAPIInited():
            return self.flashObject.as_setProfileType(premiumLabel)

    def as_setPremiumParamsS(self, timeLabel, premiumLabel, isYear):
        if self._isDAAPIInited():
            return self.flashObject.as_setPremiumParams(timeLabel, premiumLabel, isYear)

    def as_setServerStatsS(self, data):
        if self._isDAAPIInited():
            return self.flashObject.as_setServerStats(data)

    def as_setServerInfoS(self, serverUserName, tooltipFullData):
        if self._isDAAPIInited():
            return self.flashObject.as_setServerInfo(serverUserName, tooltipFullData)

    def as_premiumResponseS(self, isPremiumAccount):
        if self._isDAAPIInited():
            return self.flashObject.as_premiumResponse(isPremiumAccount)

    def as_setTankNameS(self, name):
        if self._isDAAPIInited():
            return self.flashObject.as_setTankName(name)

    def as_setTankTypeS(self, type):
        if self._isDAAPIInited():
            return self.flashObject.as_setTankType(type)

    def as_setTankEliteS(self, isElite):
        if self._isDAAPIInited():
            return self.flashObject.as_setTankElite(isElite)

    def as_doDisableNavigationS(self):
        if self._isDAAPIInited():
            return self.flashObject.as_doDisableNavigation()
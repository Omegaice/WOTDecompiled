from gui.Scaleform.framework.entities.DAAPIModule import DAAPIModule

class BattleQueueMeta(DAAPIModule):

    def startClick(self):
        self._printOverrideError('startClick')

    def exitClick(self):
        self._printOverrideError('exitClick')

    def onEscape(self):
        self._printOverrideError('onEscape')

    def as_setTimerS(self, textLabel, timeLabel):
        if self._isDAAPIInited():
            return self.flashObject.as_setTimer(textLabel, timeLabel)

    def as_setTypeS(self, type):
        if self._isDAAPIInited():
            return self.flashObject.as_setType(type)

    def as_setPlayersS(self, textLabel, numberOfPlayers):
        if self._isDAAPIInited():
            return self.flashObject.as_setPlayers(textLabel, numberOfPlayers)

    def as_setListByLevelS(self, listData):
        if self._isDAAPIInited():
            return self.flashObject.as_setListByLevel(listData)

    def as_setListByTypeS(self, listData):
        if self._isDAAPIInited():
            return self.flashObject.as_setListByType(listData)

    def as_showStartS(self, vis):
        if self._isDAAPIInited():
            return self.flashObject.as_showStart(vis)

    def as_showExitS(self, vis):
        if self._isDAAPIInited():
            return self.flashObject.as_showExit(vis)

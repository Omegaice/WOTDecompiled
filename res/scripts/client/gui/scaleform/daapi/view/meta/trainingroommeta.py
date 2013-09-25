# Embedded file name: scripts/client/gui/Scaleform/daapi/view/meta/TrainingRoomMeta.py
from gui.Scaleform.framework.entities.DAAPIModule import DAAPIModule

class TrainingRoomMeta(DAAPIModule):

    def showTrainingSettings(self):
        self._printOverrideError('showTrainingSettings')

    def selectCommonVoiceChat(self, index):
        self._printOverrideError('selectCommonVoiceChat')

    def startTraining(self):
        self._printOverrideError('startTraining')

    def swapTeams(self):
        self._printOverrideError('swapTeams')

    def changeTeam(self, accID, slot):
        self._printOverrideError('changeTeam')

    def closeTrainingRoom(self):
        self._printOverrideError('closeTrainingRoom')

    def showPrebattleInvitationsForm(self):
        self._printOverrideError('showPrebattleInvitationsForm')

    def onEscape(self):
        self._printOverrideError('onEscape')

    def as_updateCommentS(self, commentStr):
        if self._isDAAPIInited():
            return self.flashObject.as_updateComment(commentStr)

    def as_updateMapS(self, arenaTypeID, maxPlayersCount, arenaName, title, arenaSubType, descriptionStr):
        if self._isDAAPIInited():
            return self.flashObject.as_updateMap(arenaTypeID, maxPlayersCount, arenaName, title, arenaSubType, descriptionStr)

    def as_updateTimeoutS(self, roundLenString):
        if self._isDAAPIInited():
            return self.flashObject.as_updateTimeout(roundLenString)

    def as_setTeam1S(self, data):
        if self._isDAAPIInited():
            return self.flashObject.as_setTeam1(data)

    def as_setTeam2S(self, data):
        if self._isDAAPIInited():
            return self.flashObject.as_setTeam2(data)

    def as_setOtherS(self, data):
        if self._isDAAPIInited():
            return self.flashObject.as_setOther(data)

    def as_setInfoS(self, data):
        if self._isDAAPIInited():
            return self.flashObject.as_setInfo(data)

    def as_setArenaVoipChannelsS(self, arenaVoipChannels):
        if self._isDAAPIInited():
            return self.flashObject.as_setArenaVoipChannels(arenaVoipChannels)

    def as_disableStartButtonS(self, value):
        if self._isDAAPIInited():
            return self.flashObject.as_disableStartButton(value)

    def as_startCoolDownVoiceChatS(self, time):
        if self._isDAAPIInited():
            return self.flashObject.as_startCoolDownVoiceChat(time)

    def as_startCoolDownSettingS(self, time):
        if self._isDAAPIInited():
            return self.flashObject.as_startCoolDownSetting(time)

    def as_startCoolDownSwapButtonS(self, time):
        if self._isDAAPIInited():
            return self.flashObject.as_startCoolDownSwapButton(time)

    def as_setPlayerStateInTeam1S(self, uid, stateString, vContourIcon, vShortName, vLevel):
        if self._isDAAPIInited():
            return self.flashObject.as_setPlayerStateInTeam1(uid, stateString, vContourIcon, vShortName, vLevel)

    def as_setPlayerStateInTeam2S(self, uid, stateString, vContourIcon, vShortName, vLevel):
        if self._isDAAPIInited():
            return self.flashObject.as_setPlayerStateInTeam2(uid, stateString, vContourIcon, vShortName, vLevel)

    def as_setPlayerStateInOtherS(self, uid, stateString, vContourIcon, vShortName, vLevel):
        if self._isDAAPIInited():
            return self.flashObject.as_setPlayerStateInOther(uid, stateString, vContourIcon, vShortName, vLevel)

    def as_setPlayerChatRosterInTeam1S(self, uid, chatRoster):
        if self._isDAAPIInited():
            return self.flashObject.as_setPlayerChatRosterInTeam1(uid, chatRoster)

    def as_setPlayerChatRosterInTeam2S(self, uid, chatRoster):
        if self._isDAAPIInited():
            return self.flashObject.as_setPlayerChatRosterInTeam2(uid, chatRoster)

    def as_setPlayerChatRosterInOtherS(self, uid, chatRoster):
        if self._isDAAPIInited():
            return self.flashObject.as_setPlayerChatRosterInOther(uid, chatRoster)
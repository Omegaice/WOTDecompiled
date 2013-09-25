# Embedded file name: scripts/client/gui/Scaleform/daapi/view/meta/BattleLoadingMeta.py
from gui.Scaleform.framework.entities.DAAPIModule import DAAPIModule

class BattleLoadingMeta(DAAPIModule):

    def getData(self):
        self._printOverrideError('getData')

    def as_setMapBGS(self, imgsource):
        if self._isDAAPIInited():
            return self.flashObject.as_setMapBG(imgsource)

    def as_setProgressS(self, val):
        if self._isDAAPIInited():
            return self.flashObject.as_setProgress(val)

    def as_setMapNameS(self, val):
        if self._isDAAPIInited():
            return self.flashObject.as_setMapName(val)

    def as_setBattleTypeNameS(self, name):
        if self._isDAAPIInited():
            return self.flashObject.as_setBattleTypeName(name)

    def as_setBattleTypeFrameNumS(self, frameNum):
        if self._isDAAPIInited():
            return self.flashObject.as_setBattleTypeFrameNum(frameNum)

    def as_setBattleTypeFrameNameS(self, frameName):
        if self._isDAAPIInited():
            return self.flashObject.as_setBattleTypeFrameName(frameName)

    def as_setWinTextS(self, val):
        if self._isDAAPIInited():
            return self.flashObject.as_setWinText(val)

    def as_setTeamsS(self, name1, name2):
        if self._isDAAPIInited():
            return self.flashObject.as_setTeams(name1, name2)

    def as_setTipS(self, val):
        if self._isDAAPIInited():
            return self.flashObject.as_setTip(val)

    def as_setTeamValuesS(self, val):
        if self._isDAAPIInited():
            return self.flashObject.as_setTeamValues(val)
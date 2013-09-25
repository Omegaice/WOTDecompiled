# Embedded file name: scripts/client/gui/Scaleform/daapi/view/meta/BattleResultsMeta.py
from gui.Scaleform.framework.entities.DAAPIModule import DAAPIModule

class BattleResultsMeta(DAAPIModule):

    def saveSorting(self, iconType, sortDirection):
        self._printOverrideError('saveSorting')

    def showQuestsWindow(self, questID):
        self._printOverrideError('showQuestsWindow')

    def as_setDataS(self, data):
        if self._isDAAPIInited():
            return self.flashObject.as_setData(data)
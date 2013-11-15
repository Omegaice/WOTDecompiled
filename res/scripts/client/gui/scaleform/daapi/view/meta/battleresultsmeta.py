# 2013.11.15 11:26:24 EST
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
# okay decompyling res/scripts/client/gui/scaleform/daapi/view/meta/battleresultsmeta.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:26:24 EST

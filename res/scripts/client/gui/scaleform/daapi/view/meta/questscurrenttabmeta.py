# 2013.11.15 11:26:26 EST
# Embedded file name: scripts/client/gui/Scaleform/daapi/view/meta/QuestsCurrentTabMeta.py
from gui.Scaleform.framework.entities.DAAPIModule import DAAPIModule

class QuestsCurrentTabMeta(DAAPIModule):

    def sort(self, type, hideDone):
        self._printOverrideError('sort')

    def getQuestInfo(self, questID):
        self._printOverrideError('getQuestInfo')

    def as_setQuestsDataS(self, data, totalTasks):
        if self._isDAAPIInited():
            return self.flashObject.as_setQuestsData(data, totalTasks)

    def as_setSelectedQuestS(self, questID):
        if self._isDAAPIInited():
            return self.flashObject.as_setSelectedQuest(questID)
# okay decompyling res/scripts/client/gui/scaleform/daapi/view/meta/questscurrenttabmeta.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:26:26 EST

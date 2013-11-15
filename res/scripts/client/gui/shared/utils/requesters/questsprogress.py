# 2013.11.15 11:27:06 EST
# Embedded file name: scripts/client/gui/shared/utils/requesters/QuestsProgress.py
import BigWorld
from adisp import async
from gui.shared.utils.requesters.abstract import RequesterAbstract

class QuestsProgress(RequesterAbstract):

    def getQuestProgress(self, qID):
        return self.__getQuestsData().get(qID, {}).get('progress')

    @async
    def _requestCache(self, callback = None):
        BigWorld.player().questProgress.getCache(lambda resID, value: self._response(resID, value, callback))

    def __getQuestsData(self):
        return self.getCacheValue('quests', {})
# okay decompyling res/scripts/client/gui/shared/utils/requesters/questsprogress.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:27:06 EST

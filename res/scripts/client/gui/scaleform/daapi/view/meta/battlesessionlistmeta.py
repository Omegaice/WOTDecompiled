# Embedded file name: scripts/client/gui/Scaleform/daapi/view/meta/BattleSessionListMeta.py
from gui.Scaleform.framework.entities.DAAPIModule import DAAPIModule

class BattleSessionListMeta(DAAPIModule):

    def requestToJoinTeam(self, prbID, prbType):
        self._printOverrideError('requestToJoinTeam')

    def getClientID(self):
        self._printOverrideError('getClientID')

    def as_refreshListS(self, data):
        if self._isDAAPIInited():
            return self.flashObject.as_refreshList(data)
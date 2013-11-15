# 2013.11.15 11:26:26 EST
# Embedded file name: scripts/client/gui/Scaleform/daapi/view/meta/ProfileSummaryMeta.py
from gui.Scaleform.framework.entities.DAAPIModule import DAAPIModule

class ProfileSummaryMeta(DAAPIModule):

    def getPersonalScoreWarningText(self, data):
        self._printOverrideError('getPersonalScoreWarningText')

    def getGlobalRating(self, userName):
        self._printOverrideError('getGlobalRating')

    def as_setUserDataS(self, data):
        if self._isDAAPIInited():
            return self.flashObject.as_setUserData(data)
# okay decompyling res/scripts/client/gui/scaleform/daapi/view/meta/profilesummarymeta.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:26:26 EST

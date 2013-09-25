from gui.Scaleform.framework.entities.DAAPIModule import DAAPIModule

class ProfileSummaryMeta(DAAPIModule):

    def getPersonalScoreWarningText(self, data):
        self._printOverrideError('getPersonalScoreWarningText')

    def getGlobalRating(self, userName):
        self._printOverrideError('getGlobalRating')

# Embedded file name: scripts/client/gui/Scaleform/daapi/view/lobby/profile/ProfileSummaryWindow.py
from adisp import process
from gui.Scaleform.daapi.view.lobby.profile.ProfileSummary import ProfileSummary
from gui.shared import g_itemsCache

class ProfileSummaryWindow(ProfileSummary):

    def __init__(self):
        super(ProfileSummaryWindow, self).__init__()
        self.__rating = 0

    def getGlobalRating(self, userName):
        if userName is not None:
            self._receiveRating(userName)
        return self.__rating

    @process
    def _receiveRating(self, userName):
        req = g_itemsCache.items.dossiers.getUserDossierRequester(userName)
        rating = yield req.getGlobalRating()
        self.__rating = rating
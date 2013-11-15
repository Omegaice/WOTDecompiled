# 2013.11.15 11:26:11 EST
# Embedded file name: scripts/client/gui/Scaleform/daapi/view/lobby/profile/ProfileSummaryWindow.py
from adisp import process
from gui.Scaleform.daapi.view.lobby.profile.ProfileSummary import ProfileSummary
from gui.shared import g_itemsCache

class ProfileSummaryWindow(ProfileSummary):

    def __init__(self, *args):
        ProfileSummary.__init__(self, *args)
        self.__rating = 0

    def getGlobalRating(self, databaseID):
        if databaseID is not None:
            self._receiveRating(databaseID)
        return self.__rating

    @process
    def _receiveRating(self, databaseID):
        req = g_itemsCache.items.dossiers.getUserDossierRequester(int(databaseID))
        self.__rating = yield req.getGlobalRating()
# okay decompyling res/scripts/client/gui/scaleform/daapi/view/lobby/profile/profilesummarywindow.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:26:11 EST

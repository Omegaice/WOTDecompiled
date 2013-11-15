# 2013.11.15 11:26:11 EST
# Embedded file name: scripts/client/gui/Scaleform/daapi/view/lobby/profile/ProfileSummaryPage.py
from gui.Scaleform.daapi.view.lobby.profile.ProfileSummary import ProfileSummary
from gui.Scaleform.locale.PROFILE import PROFILE
from gui.shared import g_itemsCache

class ProfileSummaryPage(ProfileSummary):

    def __init__(self, *args):
        ProfileSummary.__init__(self, *args)

    def _getInitData(self):
        outcome = ProfileSummary._getInitData(self)
        outcome['nextAwardsLabel'] = PROFILE.SECTION_SUMMARY_LABELS_NEXTAWARDS
        outcome['nextAwardsErrorText'] = PROFILE.SECTION_SUMMARY_ERRORTEXT_NEXTAWARDS
        return outcome

    def getGlobalRating(self, userName):
        return g_itemsCache.items.stats.getGlobalRating()
# okay decompyling res/scripts/client/gui/scaleform/daapi/view/lobby/profile/profilesummarypage.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:26:11 EST

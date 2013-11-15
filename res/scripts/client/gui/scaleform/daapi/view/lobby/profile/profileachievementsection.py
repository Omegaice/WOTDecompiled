# 2013.11.15 11:26:10 EST
# Embedded file name: scripts/client/gui/Scaleform/daapi/view/lobby/profile/ProfileAchievementSection.py
from gui.Scaleform.daapi.view.lobby.profile.ProfileSection import ProfileSection
from gui.Scaleform.daapi.view.meta.ProfileAchievementSectionMeta import ProfileAchievementSectionMeta
from gui.shared import g_itemsCache
from gui.shared.utils.RareAchievementsCache import g_rareAchievesCache

class ProfileAchievementSection(ProfileSection, ProfileAchievementSectionMeta):

    def __init__(self, *args):
        ProfileAchievementSectionMeta.__init__(self)
        ProfileSection.__init__(self, *args)
        g_rareAchievesCache.onTextReceived += self._onRareTextReceived
        g_rareAchievesCache.onImageReceived += self._onRareImageReceived

    def request(self, data):
        dossier = g_itemsCache.items.getAccountDossier(data)
        if dossier is not None:
            g_rareAchievesCache.request(dossier.getRecord('rareAchievements'))
        return

    def _onRareTextReceived(self, rareID, title, descr):
        self.invokeUpdate()

    def _onRareImageReceived(self, rareID, imageData):
        self.invokeUpdate()

    def _disposeRequester(self):
        g_rareAchievesCache.onImageReceived -= self._onRareImageReceived
        g_rareAchievesCache.onTextReceived -= self._onRareTextReceived
# okay decompyling res/scripts/client/gui/scaleform/daapi/view/lobby/profile/profileachievementsection.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:26:10 EST

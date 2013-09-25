# Embedded file name: scripts/client/gui/Scaleform/daapi/view/lobby/profile/ProfileAchievementSection.py
from gui.Scaleform.daapi.view.lobby.profile.ProfileSection import ProfileSection
from gui.Scaleform.daapi.view.meta.ProfileAchievementSectionMeta import ProfileAchievementSectionMeta
from gui.shared import g_itemsCache
from gui.shared.utils.RareAchievementsCache import g_rareAchievesCache

class ProfileAchievementSection(ProfileSection, ProfileAchievementSectionMeta):

    def __init__(self):
        super(ProfileAchievementSection, self).__init__()
        g_rareAchievesCache.onTextReceived += self._onRareTextReceived
        g_rareAchievesCache.onImageReceived += self._onRareImageReceived

    def request(self, data):
        dossier = g_itemsCache.items.getAccountDossier(data)
        if dossier is not None:
            g_rareAchievesCache.request(dossier.getRecord('rareAchievements'))
        return

    def _onRareTextReceived(self, rareID, title, descr):
        pass

    def _onRareImageReceived(self, rareID, imageData):
        pass

    def _disposeRequester(self):
        g_rareAchievesCache.onImageReceived -= self._onRareImageReceived
        g_rareAchievesCache.onTextReceived -= self._onRareTextReceived
# Embedded file name: scripts/client/gui/Scaleform/daapi/view/lobby/profile/ProfileAwards.py
from gui.Scaleform.daapi.view.lobby.profile.ProfileAchievementSection import ProfileAchievementSection
from gui.Scaleform.daapi.view.meta.ProfileAwardsMeta import ProfileAwardsMeta

class ProfileAwards(ProfileAchievementSection, ProfileAwardsMeta):

    def __init__(self):
        super(ProfileAwards, self).__init__()

    def requestData(self, data):
        self.request(data)

    def _onRareTextReceived(self, rareID, title, descr):
        self.as_updateS(None)
        return

    def _onRareImageReceived(self, rareID, imageData):
        self.as_updateS(None)
        return

    def _dispose(self):
        self._disposeRequester()
        super(ProfileAwards, self)._dispose()
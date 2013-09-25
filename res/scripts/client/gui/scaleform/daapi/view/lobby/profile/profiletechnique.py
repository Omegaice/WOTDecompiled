from gui.Scaleform.daapi.view.lobby.profile.ProfileSection import ProfileSection
from gui.Scaleform.daapi.view.meta.ProfileTechniqueMeta import ProfileTechniqueMeta

class ProfileTechnique(ProfileSection, ProfileTechniqueMeta):

    def __init__(self):
        super(ProfileTechnique, self).__init__()

    def requestData(self, data):
        self.as_updateS(data)

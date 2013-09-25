# Embedded file name: scripts/client/gui/Scaleform/daapi/view/lobby/profile/ProfileTechniquePage.py
from gui.Scaleform.daapi.view.lobby.profile.ProfileTechnique import ProfileTechnique
from gui.Scaleform.locale.PROFILE import PROFILE
from helpers.i18n import makeString

class ProfileTechniquePage(ProfileTechnique):

    def __init__(self):
        super(ProfileTechniquePage, self).__init__()

    def _populate(self):
        super(ProfileTechniquePage, self)._populate()
        self.as_setInitDataS({'hangarVehiclesLabel': makeString(PROFILE.SECTION_TECHNIQUE_WINDOW_HANGARVEHICLESLABEL)})
from adisp import process
from debug_utils import LOG_ERROR
from gui.Scaleform.daapi.view.lobby.profile.ProfileTechnique import ProfileTechnique
from gui.shared import g_itemsCache

class ProfileTechniqueWindow(ProfileTechnique):

    def __init__(self):
        super(ProfileTechniqueWindow, self).__init__()

    def _populate(self):
        super(ProfileTechniqueWindow, self)._populate()

    @process
    def requestData(self, data):
        userName = data.userName
        vehicleId = data.vehicleId
        vehDossier = yield g_itemsCache.items.requestUserVehicleDossier(userName, vehicleId)
        if vehDossier:
            self.as_updateS({'userName': userName,
             'vehicleId': vehicleId})
        else:
            LOG_ERROR("Couldn't receive vehicle dossier! Vehicle id: " + vehicleId + ', User id: ' + vehicleId)

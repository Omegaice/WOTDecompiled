# 2013.11.15 11:26:11 EST
# Embedded file name: scripts/client/gui/Scaleform/daapi/view/lobby/profile/ProfileTechniquePage.py
from gui.Scaleform.daapi.view.lobby.profile.ProfileTechnique import ProfileTechnique
from gui.Scaleform.daapi.view.meta.ProfileTechniqueMeta import ProfileTechniqueMeta
import gui.Scaleform.daapi.view.meta.ProfileTechniquePageMeta
from gui.Scaleform.daapi.view.meta.ProfileTechniquePageMeta import ProfileTechniquePageMeta
from gui.Scaleform.locale.PROFILE import PROFILE
from helpers.i18n import makeString

class ProfileTechniquePage(ProfileTechnique, ProfileTechniquePageMeta):

    def __init__(self, *args):
        ProfileTechnique.__init__(self, *args)
        ProfileTechniquePageMeta.__init__(self)
        self.__isInHangarSelected = False

    def _sendAccountData(self, targetData, accountDossier):
        if self.__isInHangarSelected:
            self.as_responseDossierS(self._battlesType, self._getTechniqueListVehicles(targetData, True))
        else:
            ProfileTechnique._sendAccountData(self, targetData, accountDossier)

    def _populate(self):
        super(ProfileTechniquePage, self)._populate()
        self.as_setInitDataS({'hangarVehiclesLabel': makeString(PROFILE.SECTION_TECHNIQUE_WINDOW_HANGARVEHICLESLABEL),
         'isInHangarSelected': self.__isInHangarSelected})

    def setIsInHangarSelected(self, value):
        self.__isInHangarSelected = value
        self.invokeUpdate()

    def requestData(self, data):
        self._receiveVehicleDossier(data.vehicleId, None)
        return
# okay decompyling res/scripts/client/gui/scaleform/daapi/view/lobby/profile/profiletechniquepage.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:26:11 EST

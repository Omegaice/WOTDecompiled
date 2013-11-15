# 2013.11.15 11:26:10 EST
# Embedded file name: scripts/client/gui/Scaleform/daapi/view/lobby/profile/ProfileSection.py
from adisp import process
from debug_utils import LOG_DEBUG
from gui.Scaleform.daapi.view.meta.ProfileSectionMeta import ProfileSectionMeta
from gui.Scaleform.locale.PROFILE import PROFILE
from gui.shared import g_itemsCache
from helpers import i18n

class ProfileSection(ProfileSectionMeta):

    def __init__(self, *args):
        super(ProfileSection, self).__init__()
        self.__isActive = False
        self._battlesType = None
        self._userName = args[0]
        self._userID = args[1]
        self._databaseID = args[2]
        self.__needUpdate = False
        self._isTotalStatisticsTempSolution = False
        return

    def _populate(self):
        super(ProfileSection, self)._populate()
        self.requestDossier(PROFILE.PROFILE_DROPDOWN_LABELS_ALL)

    def requestDossier(self, type):
        self._battlesType = type
        self.invokeUpdate()

    def __receiveDossier(self):
        if self.__isActive and self.__needUpdate:
            self.__needUpdate = False
            accountDossier = g_itemsCache.items.getAccountDossier(self._userID)
            self._isTotalStatisticsTempSolution = False
            data = None
            if self._battlesType == PROFILE.PROFILE_DROPDOWN_LABELS_RANDOM:
                pass
            elif self._battlesType == PROFILE.PROFILE_DROPDOWN_LABELS_COMPANY:
                data = accountDossier.getCompanyStats()
            elif self._battlesType == PROFILE.PROFILE_DROPDOWN_LABELS_CLAN:
                data = accountDossier.getClanStats()
            elif self._battlesType == PROFILE.PROFILE_DROPDOWN_LABELS_TEAM:
                data = accountDossier.getTeam7x7Stats()
            else:
                data = accountDossier.getTotalStats()
                self._isTotalStatisticsTempSolution = True
            self._sendAccountData(data, accountDossier)
        return

    def _sendAccountData(self, targetData, accountDossier):
        pass

    def setActive(self, value):
        self.__isActive = value
        self.__receiveDossier()

    def invokeUpdate(self):
        self.__needUpdate = True
        self.__receiveDossier()

    @property
    def isActive(self):
        return self.__isActive

    def _formIconLabelInitObject(self, i18key, icon):
        return {'description': i18n.makeString(i18key),
         'icon': icon}
# okay decompyling res/scripts/client/gui/scaleform/daapi/view/lobby/profile/profilesection.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:26:10 EST

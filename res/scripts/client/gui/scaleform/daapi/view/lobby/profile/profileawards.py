# 2013.11.15 11:26:10 EST
# Embedded file name: scripts/client/gui/Scaleform/daapi/view/lobby/profile/ProfileAwards.py
from gui.Scaleform.daapi.view.lobby.profile.ProfileAchievementSection import ProfileAchievementSection
from gui.Scaleform.daapi.view.lobby.profile.ProfileUtils import ProfileUtils
from gui.Scaleform.daapi.view.meta.ProfileAwardsMeta import ProfileAwardsMeta
from gui.Scaleform.locale.PROFILE import PROFILE
from web_stubs import i18n
from gui.shared.gui_items.dossier.stats import AccountTotalStatsBlock

class ProfileAwards(ProfileAchievementSection, ProfileAwardsMeta):

    def __init__(self, *args):
        ProfileAchievementSection.__init__(self, *args)
        ProfileAwardsMeta.__init__(self)
        self.__achievementsFilter = PROFILE.SECTION_AWARDS_DROPDOWN_LABELS_ALL

    def _sendAccountData(self, targetData, accountDossier):
        super(ProfileAwards, self)._sendAccountData(targetData, accountDossier)
        achievements = accountDossier.getAchievements(None)
        totalItemsList = []
        for block in achievements:
            totalItemsList.append(len(block))

        if self.__achievementsFilter == PROFILE.SECTION_AWARDS_DROPDOWN_LABELS_INPROCESS:
            achievements = accountDossier.getAchievements(True)
        elif self.__achievementsFilter == PROFILE.SECTION_AWARDS_DROPDOWN_LABELS_NONE:
            achievements = accountDossier.getAchievements(False)
        packedList = []
        for achievementBlockList in achievements:
            packedList.append(ProfileUtils.packAchievementList(achievementBlockList, accountDossier, self._userID is None))

        self.as_responseDossierS(self._battlesType, {'achievementsList': packedList,
         'totalItemsList': totalItemsList,
         'battlesCount': targetData.getBattlesCount()})
        return

    def _populate(self):
        super(ProfileAwards, self)._populate()
        initData = {'achievementFilter': {'dataProvider': [self.__packProviderItem(PROFILE.SECTION_AWARDS_DROPDOWN_LABELS_ALL), self.__packProviderItem(PROFILE.SECTION_AWARDS_DROPDOWN_LABELS_INPROCESS), self.__packProviderItem(PROFILE.SECTION_AWARDS_DROPDOWN_LABELS_NONE)],
                               'selectedItem': self.__achievementsFilter}}
        self.as_setInitDataS(initData)

    def __packProviderItem(self, key):
        return {'label': i18n.makeString(key),
         'key': key}

    def setFilter(self, data):
        self.__achievementsFilter = data
        self.invokeUpdate()

    def requestData(self, data):
        self.request(self._userID)

    def _dispose(self):
        self._disposeRequester()
        super(ProfileAwards, self)._dispose()
# okay decompyling res/scripts/client/gui/scaleform/daapi/view/lobby/profile/profileawards.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:26:10 EST

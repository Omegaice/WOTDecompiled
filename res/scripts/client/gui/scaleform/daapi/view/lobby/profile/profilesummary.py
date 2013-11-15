# 2013.11.15 11:26:10 EST
# Embedded file name: scripts/client/gui/Scaleform/daapi/view/lobby/profile/ProfileSummary.py
import BigWorld
import pickle
from adisp import process
from gui.Scaleform.daapi.view.lobby.profile import ProfileCommon
from gui.Scaleform.daapi.view.lobby.profile.ProfileAchievementSection import ProfileAchievementSection
from gui.Scaleform.daapi.view.lobby.profile.ProfileUtils import ProfileUtils
from gui.Scaleform.daapi.view.meta.ProfileSummaryMeta import ProfileSummaryMeta
from gui.Scaleform.locale.PROFILE import PROFILE
from gui.shared.gui_items.dossier.stats import TotalStatsBlock, AccountTotalStatsBlock
from helpers import i18n
from PlayerEvents import g_playerEvents
from gui.shared import g_itemsCache
from gui.shared.utils import dossiers_utils
from helpers.i18n import makeString
from gui.Scaleform.locale.MENU import MENU

class ProfileSummary(ProfileAchievementSection, ProfileSummaryMeta):

    def __init__(self, *args):
        ProfileAchievementSection.__init__(self, *args)
        ProfileSummaryMeta.__init__(self)

    def _sendAccountData(self, targetData, accountDossier):
        outcome = ProfileUtils.packProfileDossierInfo(targetData)
        outcome['avgDamage'] = targetData.getAvgDamage()
        outcome['maxDestroyed'] = targetData.getMaxFrags()
        vehicle = g_itemsCache.items.getItemByCD(targetData.getMaxFragsVehicle())
        outcome['maxDestroyedByVehicle'] = vehicle.shortUserName if vehicle is not None else ''
        outcome['globalRating'] = self.getGlobalRating(self._databaseID)
        outcome['significantAchievements'] = ProfileUtils.packAchievementList(accountDossier.getSignificantAchievements(), accountDossier, self._userID is None)
        outcome['nearestAchievements'] = ProfileUtils.packAchievementList(accountDossier.getNearestAchievements(), accountDossier, self._userID is None)
        self.as_responseDossierS(self._battlesType, outcome)
        return

    def _populate(self):
        super(ProfileSummary, self)._populate()
        g_playerEvents.onDossiersResync += self.__dossierResyncHandler
        self.__updateUserInfo()
        self.as_setInitDataS(self._getInitData())

    def __dossierResyncHandler(self, *args):
        self.__updateUserInfo()

    @process
    def __updateUserInfo(self):
        req = g_itemsCache.items.dossiers.getUserDossierRequester(self._databaseID)
        dossier = yield req.getAccountDossier()
        clanInfo = yield req.getClanInfo()
        info = dossiers_utils.getCommonInfo(self._userName, dossier, clanInfo[1], None)
        info['name'] = makeString(PROFILE.PROFILE_TITLE, info['name'])
        info['clanLabel'] = makeString(PROFILE.SECTION_SUMMARY_BOTTOMBAR_CLANSROLELBL)
        registrationDate = makeString(MENU.PROFILE_HEADER_REGISTRATIONDATETITLE) + ' ' + info['registrationDate']
        info['registrationDate'] = registrationDate
        if info['lastBattleDate'] is not None:
            info['lastBattleDate'] = makeString(MENU.PROFILE_HEADER_LASTBATTLEDATETITLE) + ' ' + info['lastBattleDate']
        else:
            info['lastBattleDate'] = ''
        self.as_setUserDataS(info)
        return

    def _getInitData(self):
        return {'commonScores': {'battles': self._formIconLabelInitObject(PROFILE.SECTION_SUMMARY_SCORES_TOTALBATTLES, ProfileCommon.getIconPath('battles40x32.png')),
                          'wins': self._formIconLabelInitObject(PROFILE.SECTION_SUMMARY_SCORES_TOTALWINS, ProfileCommon.getIconPath('wins40x32.png')),
                          'coolSigns': self._formIconLabelInitObject(PROFILE.SECTION_SUMMARY_SCORES_COOLSIGNS, ProfileCommon.getIconPath('markOfMastery40x32.png')),
                          'maxDestroyed': self._formIconLabelInitObject(PROFILE.SECTION_SUMMARY_SCORES_MAXDESTROYED, ProfileCommon.getIconPath('maxDestroyed40x32.png')),
                          'maxExperience': self._formIconLabelInitObject(PROFILE.SECTION_SUMMARY_SCORES_MAXEXPERIENCE, ProfileCommon.getIconPath('maxExp40x32.png')),
                          'avgExperience': self._formIconLabelInitObject(PROFILE.SECTION_SUMMARY_SCORES_AVGEXPERIENCE, ProfileCommon.getIconPath('avgExp40x32.png')),
                          'hits': self._formIconLabelInitObject(PROFILE.SECTION_SUMMARY_SCORES_HITS, ProfileCommon.getIconPath('hits40x32.png')),
                          'avgDamage': self._formIconLabelInitObject(PROFILE.SECTION_SUMMARY_SCORES_AVGDAMAGE, ProfileCommon.getIconPath('avgDamage40x32.png')),
                          'personalScore': self._formIconLabelInitObject(PROFILE.SECTION_SUMMARY_SCORES_PERSONALSCORE, ProfileCommon.getIconPath('battles40x32.png'))},
         'significantAwardsLabel': PROFILE.SECTION_SUMMARY_LABELS_SIGNIFICANTAWARDS,
         'significantAwardsErrorText': PROFILE.SECTION_SUMMARY_ERRORTEXT_SIGNIFICANTAWARDS}

    def requestData(self, data):
        self.request(self._userID)

    def getPersonalScoreWarningText(self, data):
        battlesCount = BigWorld.wg_getIntegralFormat(data)
        return i18n.makeString(PROFILE.SECTION_SUMMARY_WARNING_PERSONALSCORE, count=battlesCount)

    def _dispose(self):
        g_playerEvents.onDossiersResync -= self.__dossierResyncHandler
        self._disposeRequester()
        super(ProfileSummary, self)._dispose()
# okay decompyling res/scripts/client/gui/scaleform/daapi/view/lobby/profile/profilesummary.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:26:10 EST

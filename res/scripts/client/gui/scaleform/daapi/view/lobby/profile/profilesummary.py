# Embedded file name: scripts/client/gui/Scaleform/daapi/view/lobby/profile/ProfileSummary.py
import BigWorld
from gui.Scaleform.daapi.view.lobby.profile import ProfileCommon
from gui.Scaleform.daapi.view.lobby.profile.ProfileAchievementSection import ProfileAchievementSection
from gui.Scaleform.daapi.view.meta.ProfileSummaryMeta import ProfileSummaryMeta
from gui.Scaleform.locale.PROFILE import PROFILE
from helpers import i18n

class ProfileSummary(ProfileAchievementSection, ProfileSummaryMeta):

    def __init__(self):
        super(ProfileSummary, self).__init__()
        self._userName = None
        return

    def _populate(self):
        super(ProfileSummary, self)._populate()
        self.as_setInitDataS(self._getInitData())

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
        self.request(data)

    def _onRareTextReceived(self, rareID, title, descr):
        self.as_updateS(None)
        return

    def _onRareImageReceived(self, rareID, imageData):
        self.as_updateS(None)
        return

    def getPersonalScoreWarningText(self, data):
        battlesCount = BigWorld.wg_getIntegralFormat(data)
        return i18n.makeString(PROFILE.SECTION_SUMMARY_WARNING_PERSONALSCORE, count=battlesCount)

    def _dispose(self):
        self._disposeRequester()
        super(ProfileSummary, self)._dispose()
# Embedded file name: scripts/client/gui/Scaleform/daapi/view/lobby/profile/ProfileStatistics.py
from gui.Scaleform.daapi.view.lobby.profile import ProfileCommon
from gui.Scaleform.daapi.view.lobby.profile.ProfileSection import ProfileSection
from gui.Scaleform.daapi.view.meta.ProfileStatisticsMeta import ProfileStatisticsMeta
from gui.Scaleform.locale.PROFILE import PROFILE
from helpers import i18n

class ProfileStatistics(ProfileSection, ProfileStatisticsMeta):

    def __init__(self):
        super(ProfileStatistics, self).__init__()

    def _populate(self):
        super(ProfileStatistics, self)._populate()
        initData = {'mainDropDownMenu': (PROFILE.SECTION_STATISTICS_DROPDOWN_LABELS_ALL,
                              PROFILE.SECTION_STATISTICS_DROPDOWN_LABELS_RANDOM,
                              PROFILE.SECTION_STATISTICS_DROPDOWN_LABELS_COMPANY,
                              PROFILE.SECTION_STATISTICS_DROPDOWN_LABELS_CLAN,
                              PROFILE.SECTION_STATISTICS_DROPDOWN_LABELS_TEAM),
         'detailedScores': {'killed': i18n.makeString(PROFILE.SECTION_STATISTICS_DETAILED_KILLED),
                            'destroyed': i18n.makeString(PROFILE.SECTION_STATISTICS_DETAILED_DESTROYED),
                            'destructionCoefficient': i18n.makeString(PROFILE.SECTION_STATISTICS_DETAILED_DESTRUCTIONCOEFFICIENT),
                            'dealOutDamage': i18n.makeString(PROFILE.SECTION_STATISTICS_DETAILED_DEALOUTDAMAGE),
                            'receivedDamage': i18n.makeString(PROFILE.SECTION_STATISTICS_DETAILED_RECEIVEDDAMAGE),
                            'damageCoefficient': i18n.makeString(PROFILE.SECTION_STATISTICS_DETAILED_DAMAGECOEFFICIENT),
                            'avgDestroyedVehicles': i18n.makeString(PROFILE.SECTION_STATISTICS_DETAILED_AVGDESTROYEDVEHICLES),
                            'maxDestroyedVehicles': i18n.makeString(PROFILE.SECTION_STATISTICS_DETAILED_MAXDESTROYEDVEHICLES),
                            'avgDamage': i18n.makeString(PROFILE.SECTION_STATISTICS_DETAILED_AVGDAMAGE),
                            'avgReceivedDamage': i18n.makeString(PROFILE.SECTION_STATISTICS_DETAILED_AVGRECEIVEDDAMAGE),
                            'avgDetectedEnemies': i18n.makeString(PROFILE.SECTION_STATISTICS_DETAILED_AVGDETECTEDENEMIES)},
         'commonScores': {'battles': self._formIconLabelInitObject(PROFILE.SECTION_STATISTICS_SCORES_TOTALBATTLES, ProfileCommon.getIconPath('battles40x32.png')),
                          'wins': self._formIconLabelInitObject(PROFILE.SECTION_STATISTICS_SCORES_TOTALWINS, ProfileCommon.getIconPath('wins40x32.png')),
                          'coolSigns': self._formIconLabelInitObject(PROFILE.SECTION_STATISTICS_SCORES_COOLSIGNS, ProfileCommon.getIconPath('markOfMastery40x32.png')),
                          'survival': self._formIconLabelInitObject(PROFILE.SECTION_STATISTICS_SCORES_SURVIVAL, ProfileCommon.getIconPath('survival40x32.png')),
                          'maxExperience': self._formIconLabelInitObject(PROFILE.SECTION_STATISTICS_SCORES_MAXEXPERIENCE, ProfileCommon.getIconPath('maxExp40x32.png')),
                          'avgExperience': self._formIconLabelInitObject(PROFILE.SECTION_STATISTICS_SCORES_AVGEXPERIENCE, ProfileCommon.getIconPath('avgExp40x32.png')),
                          'hits': self._formIconLabelInitObject(PROFILE.SECTION_STATISTICS_SCORES_HITS, ProfileCommon.getIconPath('hits40x32.png'))},
         'battlesOnTech': i18n.makeString(PROFILE.SECTION_STATISTICS_LABELS_BATTLESONTECH),
         'chartsTitles': (i18n.makeString(PROFILE.SECTION_STATISTICS_CHARTS_BYTYPELABEL), i18n.makeString(PROFILE.SECTION_STATISTICS_CHARTS_BYNATIONLABEL), i18n.makeString(PROFILE.SECTION_STATISTICS_CHARTS_BYLEVELLABEL)),
         'charts': ((self.__getChartData('../maps/icons/filters/tanks/lightTank.png'),
                     self.__getChartData('../maps/icons/filters/tanks/AT-SPG.png'),
                     self.__getChartData('../maps/icons/filters/tanks/SPG.png'),
                     self.__getChartData('../maps/icons/filters/tanks/mediumTank.png'),
                     self.__getChartData('../maps/icons/filters/tanks/heavyTank.png')), (self.__getChartData('../maps/icons/filters/nations/ussr.png'),
                     self.__getChartData('../maps/icons/filters/nations/germany.png'),
                     self.__getChartData('../maps/icons/filters/nations/usa.png'),
                     self.__getChartData('../maps/icons/filters/nations/france.png'),
                     self.__getChartData('../maps/icons/filters/nations/uk.png'),
                     self.__getChartData('../maps/icons/filters/nations/china.png')), (self.__getChartData(self.__generateLevelIconPath(1)),
                     self.__getChartData(self.__generateLevelIconPath(2)),
                     self.__getChartData(self.__generateLevelIconPath(3)),
                     self.__getChartData(self.__generateLevelIconPath(4)),
                     self.__getChartData(self.__generateLevelIconPath(5)),
                     self.__getChartData(self.__generateLevelIconPath(6)),
                     self.__getChartData(self.__generateLevelIconPath(7)),
                     self.__getChartData(self.__generateLevelIconPath(8)),
                     self.__getChartData(self.__generateLevelIconPath(9)),
                     self.__getChartData(self.__generateLevelIconPath(10))))}
        self.as_setInitDataS(initData)

    def __getChartData(self, iconName, value = 0):
        return {'icon': iconName,
         'count': value}

    def __generateLevelIconPath(self, num):
        return '../maps/icons/levels/tank_level_' + str(num) + '.png'

    def _dispose(self):
        super(ProfileStatistics, self)._dispose()
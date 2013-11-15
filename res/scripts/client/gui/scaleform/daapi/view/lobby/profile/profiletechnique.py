# 2013.11.15 11:26:11 EST
# Embedded file name: scripts/client/gui/Scaleform/daapi/view/lobby/profile/ProfileTechnique.py
from gui import GUI_NATIONS_ORDER_INDEX
from gui.Scaleform.daapi.view.lobby.profile.ProfileSection import ProfileSection
from gui.Scaleform.daapi.view.lobby.profile.ProfileUtils import ProfileUtils
from gui.Scaleform.daapi.view.meta.ProfileTechniqueMeta import ProfileTechniqueMeta
from gui.Scaleform.locale.PROFILE import PROFILE
from gui.shared import g_itemsCache
from gui.shared.gui_items.Vehicle import VEHICLE_TYPES_ORDER_INDICES
from nations import NAMES

class ProfileTechnique(ProfileSection, ProfileTechniqueMeta):

    def __init__(self, *args):
        ProfileSection.__init__(self, *args)
        ProfileTechniqueMeta.__init__(self)

    def _sendAccountData(self, targetData, accountDossier):
        self.as_responseDossierS(self._battlesType, self._getTechniqueListVehicles(targetData))

    def _getTechniqueListVehicles(self, targetData, addVehiclesThatInHangarOnly = False):
        result = []
        for intCD, (battlesCount, wins, markOfMastery, xp) in targetData.getVehicles().iteritems():
            avgXP = xp / battlesCount if battlesCount else 0
            vehicle = g_itemsCache.items.getItemByCD(intCD)
            if vehicle is not None:
                isInHangar = vehicle.invID > 0
                if addVehiclesThatInHangarOnly and not isInHangar:
                    continue
                result.append({'id': intCD,
                 'inventoryID': vehicle.invID,
                 'shortUserName': vehicle.shortUserName,
                 'battlesCount': battlesCount,
                 'winsEfficiency': round(100.0 * wins / battlesCount) if battlesCount else 0,
                 'avgExperience': avgXP,
                 'userName': vehicle.userName,
                 'typeIndex': VEHICLE_TYPES_ORDER_INDICES[vehicle.type],
                 'nationIndex': GUI_NATIONS_ORDER_INDEX[NAMES[vehicle.nationID]],
                 'nationID': vehicle.nationID,
                 'level': vehicle.level,
                 'markOfMastery': markOfMastery if self._isTotalStatisticsTempSolution else ProfileUtils.UNAVAILABLE_VALUE,
                 'tankIconPath': vehicle.iconSmall,
                 'typeIconPath': '../maps/icons/filters/tanks/%s.png' % vehicle.type,
                 'isInHangar': isInHangar})

        return result

    def requestData(self, data):
        pass

    def _receiveVehicleDossier(self, vehicleIntCD, databaseId):
        vehDossier = g_itemsCache.items.getVehicleDossier(vehicleIntCD, databaseId)
        data = None
        if self._battlesType == PROFILE.PROFILE_DROPDOWN_LABELS_RANDOM:
            pass
        elif self._battlesType == PROFILE.PROFILE_DROPDOWN_LABELS_COMPANY:
            data = vehDossier.getCompanyStats()
        elif self._battlesType == PROFILE.PROFILE_DROPDOWN_LABELS_CLAN:
            data = vehDossier.getClanStats()
        elif self._battlesType == PROFILE.PROFILE_DROPDOWN_LABELS_TEAM:
            data = vehDossier.getTeam7x7Stats()
        else:
            data = vehDossier.getTotalStats()
        self._sendVehicleData(data, vehDossier)
        return

    def _sendVehicleData(self, targetData, vehDossier):
        outcome = ProfileUtils.packProfileCommonInfo(targetData)
        outcome['lossesEfficiency'] = targetData.getLossesEfficiency()
        outcome['survivalEfficiency'] = targetData.getSurvivalEfficiency()
        outcome['maxVehicleFrags'] = targetData.getMaxFrags()
        outcome['fragsCount'] = targetData.getFragsCount()
        outcome['deathsCount'] = targetData.getDeathsCount()
        outcome['fragsEfficiency'] = targetData.getFragsEfficiency()
        outcome['damageDealt'] = targetData.getDamageDealt()
        outcome['damageReceived'] = targetData.getDamageReceived()
        outcome['damageEfficiency'] = targetData.getDamageEfficiency()
        outcome['avgFrags'] = targetData.getAvgFrags()
        outcome['avgEnemiesSpotted'] = targetData.getAvgEnemiesSpotted()
        outcome['avgDamageDealt'] = targetData.getAvgDamageDealt()
        outcome['avgDamageReceived'] = targetData.getAvgDamageReceived()
        packedList = None
        if self._isTotalStatisticsTempSolution:
            packedList = []
            achievements = vehDossier.getAchievements(True)
            for achievementBlockList in achievements:
                packedList.append(ProfileUtils.packAchievementList(achievementBlockList, vehDossier, self._userID is None))

        outcome['achievements'] = packedList
        self.as_responseVehicleDossierS(outcome)
        return
# okay decompyling res/scripts/client/gui/scaleform/daapi/view/lobby/profile/profiletechnique.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:26:11 EST

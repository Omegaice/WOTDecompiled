# 2013.11.15 11:26:06 EST
# Embedded file name: scripts/client/gui/Scaleform/daapi/view/lobby/PersonalCase.py
import pickle
from adisp import async
from CurrentVehicle import g_currentVehicle
from debug_utils import LOG_ERROR
from gui.Scaleform.framework import AppRef
from gui.prb_control.dispatcher import g_prbLoader
from gui.prb_control.prb_helpers import GlobalListener
from items import vehicles, tankmen
from gui import TANKMEN_ROLES_ORDER_DICT, SystemMessages
from gui.ClientUpdateManager import g_clientUpdateManager
from gui.Scaleform.framework.entities.View import View
from gui.Scaleform.daapi.view.meta.PersonalCaseMeta import PersonalCaseMeta
from gui.Scaleform.daapi.view.meta.WindowViewMeta import WindowViewMeta
from gui.shared.events import ShowWindowEvent
from gui.shared.utils import decorators, isVehicleObserver
from gui.shared.gui_items import GUI_ITEM_TYPE
from gui.shared.gui_items.Tankman import TankmanSkill
from gui.shared.gui_items.serializers import g_itemSerializer
from gui.shared.gui_items.processors.tankman import TankmanDismiss, TankmanUnload, TankmanRetraining, TankmanAddSkill, TankmanChangePassport
from gui.shared import EVENT_BUS_SCOPE, events, g_itemsCache, REQ_CRITERIA
from helpers.i18n import makeString

class PersonalCase(View, WindowViewMeta, PersonalCaseMeta, GlobalListener, AppRef):

    def __init__(self, ctx):
        super(PersonalCase, self).__init__()
        self.tmanInvID = ctx.get('tankmanID')
        self.tabIndex = ctx.get('page', -1)
        self.dataProvider = PersonalCaseDataProvider(self.tmanInvID)

    def onClientChanged(self, diff):
        inventory = diff.get('inventory', {})
        stats = diff.get('stats', {})
        cache = diff.get('cache', {})
        isTankmanChanged = False
        if vehicles._TANKMAN in inventory:
            isTankmanChanged = True
            tankmanData = inventory[vehicles._TANKMAN].get('compDescr')
            if tankmanData is not None and self.tmanInvID in tankmanData:
                if tankmanData[self.tmanInvID] is None:
                    return self.destroy()
            self.__setCommonData()
            self.__setSkillsData()
            self.__setDossierData()
        if not 'credits' in stats:
            if not 'gold' in stats:
                isMoneyChanged = 'mayConsumeWalletResources' in cache
                isVehicleChanged = 'unlocks' in stats
                (isTankmanChanged or isMoneyChanged or isVehicleChanged) and self.__setRetrainingData()
            (isTankmanChanged or isMoneyChanged) and self.__setDocumentsData()
        return

    def onPrbFunctionalFinished(self):
        self.__setCommonData()

    def onPlayerStateChanged(self, functional, roster, accountInfo):
        if accountInfo.isCurrentPlayer():
            self.__setCommonData()

    def onUnitFunctionalFinished(self):
        self.__setCommonData()

    def onUnitPlayerStateChanged(self, pInfo):
        if pInfo.isCurrentPlayer():
            self.__setCommonData()

    def onWindowClose(self):
        self.destroy()

    def getCommonData(self):
        self.__setCommonData()

    def getDossierData(self):
        self.__setDossierData()

    def getRetrainingData(self):
        self.__setRetrainingData()

    def getSkillsData(self):
        self.__setSkillsData()

    def getDocumentsData(self):
        self.__setDocumentsData()

    @decorators.process('updating')
    def dismissTankman(self, tmanInvID):
        tankman = g_itemsCache.items.getTankman(int(tmanInvID))
        proc = TankmanDismiss(tankman)
        result = yield proc.request()
        if len(result.userMsg):
            SystemMessages.g_instance.pushMessage(result.userMsg, type=result.sysMsgType)

    @decorators.process('retraining')
    def retrainingTankman(self, inventoryID, innationID, tankmanCostTypeIdx):
        tankman = g_itemsCache.items.getTankman(int(inventoryID))
        vehicleToRecpec = g_itemsCache.items.getItem(GUI_ITEM_TYPE.VEHICLE, tankman.nationID, int(innationID))
        proc = TankmanRetraining(tankman, vehicleToRecpec, tankmanCostTypeIdx)
        result = yield proc.request()
        if len(result.userMsg):
            SystemMessages.g_instance.pushI18nMessage(result.userMsg, type=result.sysMsgType)

    @decorators.process('unloading')
    def unloadTankman(self, tmanInvID, currentVehicleID):
        tankman = g_itemsCache.items.getTankman(int(tmanInvID))
        tmanVehicle = g_itemsCache.items.getVehicle(int(tankman.vehicleInvID))
        if tmanVehicle is None:
            LOG_ERROR("Target tankman's vehicle is not found in inventory", tankman, tankman.vehicleInvID)
            return
        else:
            unloader = TankmanUnload(tmanVehicle, tankman.vehicleSlotIdx)
            result = yield unloader.request()
            if len(result.userMsg):
                SystemMessages.g_instance.pushI18nMessage(result.userMsg, type=result.sysMsgType)
            return

    @decorators.process('updating')
    def changeTankmanPassport(self, invengoryID, firstNameID, lastNameID, iconID):
        tankman = g_itemsCache.items.getTankman(int(invengoryID))
        processor = TankmanChangePassport(tankman, firstNameID, lastNameID, iconID)
        result = yield processor.request()
        if len(result.userMsg):
            SystemMessages.g_instance.pushI18nMessage(result.userMsg, type=result.sysMsgType)

    @decorators.process('studying')
    def addTankmanSkill(self, invengoryID, skillName):
        tankman = g_itemsCache.items.getTankman(int(invengoryID))
        processor = TankmanAddSkill(tankman, skillName)
        result = yield processor.request()
        if len(result.userMsg):
            SystemMessages.g_instance.pushI18nMessage(result.userMsg, type=result.sysMsgType)

    def openExchangeFreeToTankmanXpWindow(self):
        self.fireEvent(events.ShowWindowEvent(events.ShowWindowEvent.SHOW_EXCHANGE_FREE_TO_TANKMAN_XP_WINDOW, {'tankManId': self.tmanInvID}), EVENT_BUS_SCOPE.LOBBY)

    def dropSkills(self):
        self.fireEvent(ShowWindowEvent(ShowWindowEvent.SHOW_TANKMAN_DROP_SKILLS_WINDOW, {'tankmanID': self.tmanInvID}))

    def _populate(self):
        super(PersonalCase, self)._populate()
        g_clientUpdateManager.addCallbacks({'': self.onClientChanged})
        self.startGlobalListening()

    def _dispose(self):
        super(PersonalCase, self)._dispose()
        self.stopGlobalListening()
        g_clientUpdateManager.removeObjectCallbacks(self)

    @decorators.process('updating')
    def __setCommonData(self):
        data = yield self.dataProvider.getCommonData()
        data.update({'tabIndex': self.tabIndex})
        self.as_setCommonDataS(data)

    @decorators.process('updating')
    def __setDossierData(self):
        data = yield self.dataProvider.getDossierData()
        self.as_setDossierDataS(data)

    @decorators.process('updating')
    def __setRetrainingData(self):
        data = yield self.dataProvider.getRetrainingData()
        self.as_setRetrainingDataS(data)

    @decorators.process('updating')
    def __setDocumentsData(self):
        data = yield self.dataProvider.getDocumentsData()
        self.as_setDocumentsDataS(data)

    @decorators.process('updating')
    def __setSkillsData(self):
        data = yield self.dataProvider.getSkillsData()
        self.as_setSkillsDataS(data)


class PersonalCaseDataProvider(object):

    def __init__(self, tmanInvID):
        """
        @param tmanInvID: tankman inventory id
        """
        self.tmanInvID = tmanInvID

    @async
    def getCommonData(self, callback):
        """
        Returns common personal case data for tankman, tankman's vehicles,
        message, flags and so on.
        """
        tankman = g_itemsCache.items.getTankman(self.tmanInvID)
        nativeVehicle = g_itemsCache.items.getItemByCD(tankman.vehicleNativeDescr.type.compactDescr)
        currentVehicle = None
        if tankman.isInTank:
            currentVehicle = g_itemsCache.items.getItemByCD(tankman.vehicleDescr.type.compactDescr)
        isLocked, reason = self.__getTankmanLockMessage(currentVehicle)
        callback({'tankman': g_itemSerializer.pack(tankman),
         'currentVehicle': g_itemSerializer.pack(currentVehicle) if currentVehicle is not None else None,
         'nativeVehicle': g_itemSerializer.pack(nativeVehicle),
         'isOpsLocked': isLocked or g_currentVehicle.isLocked(),
         'lockMessage': reason})
        return

    @async
    def getDossierData(self, callback):
        """
        Returns dict of dossier data: information stats blocks and
        achievements list.
        """
        tmanDossier = g_itemsCache.items.getTankmanDossier(self.tmanInvID)
        if tmanDossier is None:
            callback(None)
            return
        else:
            achieves = tmanDossier.getAchievements()
            packedAchieves = []
            for sectionIdx, section in enumerate(achieves):
                packedAchieves.append([])
                for achievement in section:
                    data = g_itemSerializer.pack(achievement)
                    data['dossierType'] = GUI_ITEM_TYPE.TANKMAN_DOSSIER
                    data['dossierCompDescr'] = pickle.dumps(tmanDossier.getDossierDescr().makeCompDescr())
                    packedAchieves[sectionIdx].append(data)

            callback({'achievements': packedAchieves,
             'stats': tmanDossier.getStats()})
            return

    @async
    def getRetrainingData(self, callback):
        items = g_itemsCache.items
        tankman = items.getTankman(self.tmanInvID)
        criteria = REQ_CRITERIA.NATIONS([tankman.nationID]) | REQ_CRITERIA.UNLOCKED
        vData = items.getVehicles(criteria)
        tDescr = tankman.descriptor
        vehiclesData = sorted(vData.values())
        result = []
        for vehicle in vehiclesData:
            vDescr = vehicle.descriptor
            if isVehicleObserver(vDescr.type.compactDescr):
                continue
            for role in vDescr.type.crewRoles:
                if tDescr.role == role[0]:
                    result.append({'innationID': vehicle.innationID,
                     'vehicleType': vehicle.type,
                     'userName': vehicle.shortUserName})
                    break

        callback({'money': (items.stats.credits, items.stats.gold),
         'tankmanCost': items.shop.tankmanCost,
         'vehicles': result})

    @async
    def getSkillsData(self, callback):
        tankman = g_itemsCache.items.getTankman(self.tmanInvID)
        tankmanDescr = tankman.descriptor
        result = []
        commonSkills = []
        for skill in tankmen.COMMON_SKILLS:
            if skill not in tankmanDescr.skills:
                commonSkills.append(self.__packSkill(tankman, TankmanSkill(skill)))

        result.append({'id': 'common',
         'skills': commonSkills})
        for role in TANKMEN_ROLES_ORDER_DICT['plain']:
            roleSkills = tankmen.SKILLS_BY_ROLES.get(role, tuple())
            if role not in tankman.combinedRoles:
                continue
            skills = []
            for skill in roleSkills:
                if skill not in tankmen.COMMON_SKILLS and skill not in tankmanDescr.skills:
                    skills.append(self.__packSkill(tankman, TankmanSkill(skill)))

            result.append({'id': role,
             'skills': skills})

        callback(result)

    @async
    def getDocumentsData(self, callback):
        items = g_itemsCache.items
        config = tankmen.getNationConfig(items.getTankman(self.tmanInvID).nationID)
        callback({'money': (items.stats.credits, items.stats.gold),
         'passportChangeCost': items.shop.passportChangeCost,
         'firstnames': self.__getDocNormalGroupValues(config, 'firstNames'),
         'lastnames': self.__getDocNormalGroupValues(config, 'lastNames'),
         'icons': self.__getDocNormalGroupValues(config, 'icons')})

    @staticmethod
    def __getDocNormalGroupValues(config, groupName):
        result = []
        for group in config['normalGroups']:
            for id in group['%sList' % groupName]:
                result.append({'id': id,
                 'value': config[groupName][id]})

        if groupName != 'icons':
            result = sorted(result, key=lambda sortField: sortField['value'])
        return result

    @staticmethod
    def __packSkill(tankman, skillItem):
        return {'id': skillItem.name,
         'name': skillItem.userName,
         'desc': skillItem.shortDescription,
         'enabled': True,
         'tankmanID': tankman.invID,
         'tooltip': None}

    @staticmethod
    def __getTankmanLockMessage(vehicle):
        if vehicle is None:
            return (False, '')
        elif vehicle.isInBattle:
            return (False, makeString('#menu:tankmen/lockReason/inbattle'))
        elif vehicle.isBroken:
            return (False, makeString('#menu:tankmen/lockReason/broken'))
        else:
            if g_currentVehicle.item == vehicle:
                dispatcher = g_prbLoader.getDispatcher()
                if dispatcher is not None:
                    permission = dispatcher.getGUIPermissions()
                    if not permission.canChangeVehicle():
                        return (True, makeString('#menu:tankmen/lockReason/prebattle'))
            return (False, '')
# okay decompyling res/scripts/client/gui/scaleform/daapi/view/lobby/personalcase.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:26:06 EST

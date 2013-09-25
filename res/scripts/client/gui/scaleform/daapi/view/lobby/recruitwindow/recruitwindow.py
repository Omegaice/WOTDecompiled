from debug_utils import LOG_ERROR, LOG_CURRENT_EXCEPTION, LOG_DEBUG
from gui.ClientUpdateManager import g_clientUpdateManager
import nations
from gui.Scaleform.locale.DIALOGS import DIALOGS
from gui.Scaleform.locale.MENU import MENU
from adisp import process, async
from items import vehicles
from items.tankmen import getSkillsConfig
from helpers.i18n import convert
from gui import GUI_NATIONS, SystemMessages
from gui.Scaleform.Waiting import Waiting
from gui.Scaleform.daapi.view.meta.RecruitWindowMeta import RecruitWindowMeta
from gui.Scaleform.framework.entities.View import View
from gui.shared import g_itemsCache, REQ_CRITERIA
from gui.shared.utils import decorators
from gui.shared.utils.requesters import StatsRequester, Requester, ItemsRequester
from gui.shared.gui_items import GUI_ITEM_TYPE
from gui.shared.gui_items.processors.tankman import TankmanRecruit, TankmanEquip

class RecruitWindow(View, RecruitWindowMeta):

    def __init__(self, ctx):
        View.__init__(self)
        self._initData = ctx.get('data', None)
        self._menuEnabled = ctx.get('menuEnabled', False)
        self._currentVehicleInvId = ctx.get('currentVehicleId', -1)
        return

    def _populate(self):
        View._populate(self)
        self.__getInitialData()
        if self._currentVehicleInvId != -1:
            g_clientUpdateManager.addCallbacks({'inventory': self.onInventoryChanged})
        g_clientUpdateManager.addCallbacks({'stats.credits': self.onCreditsChange,
         'stats.gold': self.onGoldChange})

    def onGoldChange(self, value):
        if self._currentVehicleInvId is not None:
            self.as_setGoldChangedS(value)
        return

    def onCreditsChange(self, value):
        if self._currentVehicleInvId is not None:
            self.as_setCreditsChangedS(value)
        return

    def onInventoryChanged(self, inventory):
        if GUI_ITEM_TYPE.VEHICLE in inventory and 'compDescr' in inventory[GUI_ITEM_TYPE.VEHICLE]:
            changedVehicles = inventory[GUI_ITEM_TYPE.VEHICLE]['compDescr']
            if changedVehicles[self._currentVehicleInvId] is None:
                self._currentVehicleInvId = None
                self.onWindowClose()
        return

    def _dispose(self):
        g_clientUpdateManager.removeObjectCallbacks(self)

    @process
    def __getInitialData(self):
        credits = yield StatsRequester().getCredits()
        gold = yield StatsRequester().getGold()
        upgradeParams = yield StatsRequester().getTankmanCost()
        data = {'credits': credits,
         'gold': gold,
         'schoolUpgrade': round(upgradeParams[1]['credits']),
         'academyUpgrade': round(upgradeParams[2]['gold']),
         'data': self._initData,
         'menuEnabled': self._menuEnabled}
        self.flashObject.as_initData(data)

    @process
    def updateAllDropdowns(self, nationID, tankType, typeID, roleType):
        nationsDP = [{'id': None,
          'label': MENU.NATIONS_ALL}, {'id': nationID,
          'label': MENU.nations(nations.NAMES[int(nationID)])}]
        classesDP = [{'id': None,
          'label': DIALOGS.RECRUITWINDOW_MENUEMPTYROW}, {'id': tankType,
          'label': DIALOGS.recruitwindow_vehicleclassdropdown(tankType)}]
        typesDP = [{'id': None,
          'label': DIALOGS.RECRUITWINDOW_MENUEMPTYROW}]
        rolesDP = [{'id': None,
          'label': DIALOGS.RECRUITWINDOW_MENUEMPTYROW}]
        unlocks = yield StatsRequester().getUnlocks()
        modulesAll = yield Requester('vehicle').getFromShop()
        for module in modulesAll:
            compdecs = module.descriptor.type.compactDescr
            if compdecs in unlocks and module.descriptor.type.id[0] == nationID and module.descriptor.type.id[1] == typeID:
                typesDP.append({'id': module.descriptor.type.id[1],
                 'label': module.descriptor.type.shortUserString})
                for role in module.descriptor.type.crewRoles:
                    if role[0] == roleType:
                        rolesDP.append({'id': role[0],
                         'label': convert(getSkillsConfig()[role[0]]['userString'])})

                break

        self.flashObject.as_setAllDropdowns(nationsDP, classesDP, typesDP, rolesDP)
        return

    def updateNationDropdown(self):
        try:
            vehsItems = g_itemsCache.items.getVehicles(REQ_CRITERIA.UNLOCKED)
            data = [{'id': None,
              'label': MENU.NATIONS_ALL}]
            for name in GUI_NATIONS:
                nationIdx = nations.INDICES[name]
                vehiclesAvailable = len(vehsItems.filter(REQ_CRITERIA.NATIONS([nationIdx]))) > 0
                if name in nations.AVAILABLE_NAMES and vehiclesAvailable:
                    data.append({'id': nationIdx,
                     'label': MENU.nations(name)})

            self.flashObject.as_setNations(data)
        except Exception:
            LOG_ERROR('There is exception while setting data to the recruit window')
            LOG_CURRENT_EXCEPTION()

        return

    @process
    def updateVehicleClassDropdown(self, nationID):
        Waiting.show('updating')
        unlocks = yield StatsRequester().getUnlocks()
        modulesAll = yield Requester('vehicle').getFromShop()
        classes = []
        data = [{'id': None,
          'label': DIALOGS.RECRUITWINDOW_MENUEMPTYROW}]
        modulesAll.sort()
        for module in modulesAll:
            compdecs = module.descriptor.type.compactDescr
            if compdecs in unlocks and module.descriptor.type.id[0] == nationID and module.type not in classes:
                classes.append(module.type)
                data.append({'id': module.type,
                 'label': DIALOGS.recruitwindow_vehicleclassdropdown(module.type)})

        self.flashObject.as_setVehicleClassDropdown(data)
        Waiting.hide('updating')
        return

    @process
    def updateVehicleTypeDropdown(self, nationID, vclass):
        Waiting.show('updating')
        unlocks = yield StatsRequester().getUnlocks()
        modulesAll = yield Requester('vehicle').getFromShop()
        data = [{'id': None,
          'label': DIALOGS.RECRUITWINDOW_MENUEMPTYROW}]
        modulesAll.sort()
        for module in modulesAll:
            compdecs = module.descriptor.type.compactDescr
            if compdecs in unlocks and module.descriptor.type.id[0] == nationID and module.type == vclass:
                data.append({'id': module.descriptor.type.id[1],
                 'label': module.descriptor.type.shortUserString})

        self.flashObject.as_setVehicleTypeDropdown(data)
        Waiting.hide('updating')
        return

    @process
    def updateRoleDropdown(self, nationID, vclass, typeID):
        Waiting.show('updating')
        unlocks = yield StatsRequester().getUnlocks()
        modulesAll = yield Requester('vehicle').getFromShop()
        roles = []
        data = [{'id': None,
          'label': DIALOGS.RECRUITWINDOW_MENUEMPTYROW}]
        modulesAll.sort()
        for module in modulesAll:
            compdecs = module.descriptor.type.compactDescr
            if compdecs in unlocks and module.descriptor.type.id[0] == nationID and module.descriptor.type.id[1] == typeID:
                for role in module.descriptor.type.crewRoles:
                    if role[0] not in roles:
                        roles.append(role[0])
                        data.append({'id': role[0],
                         'label': convert(getSkillsConfig()[role[0]]['userString'])})

        self.flashObject.as_setRoleDropdown(data)
        Waiting.hide('updating')
        return

    def onWindowClose(self):
        self.destroy()

    @async
    @process
    def __buyTankman(self, nationID, vehTypeID, role, studyType, callback):
        recruiter = TankmanRecruit(int(nationID), int(vehTypeID), role, int(studyType))
        success, msg, msgType, tmanInvID = yield recruiter.request()
        tankman = None
        if len(msg):
            SystemMessages.pushI18nMessage(msg, type=msgType)
        if success:
            tankman = g_itemsCache.items.getTankman(tmanInvID)
        callback(tankman)
        return

    @async
    @process
    def __equipTankman(self, tankman, vehicle, slot, callback):
        result = yield TankmanEquip(tankman, vehicle, slot).request()
        if len(result.userMsg):
            SystemMessages.pushI18nMessage(result.userMsg, type=result.sysMsgType)
        callback(result.success)

    @decorators.process('recruting')
    def buyTankman(self, nationID, vehTypeID, role, studyType, slot):
        tankman = yield self.__buyTankman(int(nationID), int(vehTypeID), role, int(studyType))
        if slot is not None and slot != -1 and tankman is not None:
            vehicle = g_itemsCache.items.getVehicle(self._currentVehicleInvId)
            _ = yield self.__equipTankman(tankman, vehicle, int(slot))
        self.onWindowClose()
        return

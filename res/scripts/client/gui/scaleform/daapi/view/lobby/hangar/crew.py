# Embedded file name: scripts/client/gui/Scaleform/daapi/view/lobby/hangar/Crew.py
from adisp import process
from CurrentVehicle import g_currentVehicle
from debug_utils import LOG_DEBUG, LOG_ERROR
from gui.Scaleform.daapi.view.meta.CrewMeta import CrewMeta
from gui import SystemMessages
from items.tankmen import getSkillsConfig, compareMastery, COMMANDER_ADDITION_RATIO, ACTIVE_SKILLS, PERKS
from helpers.i18n import convert
from gui.ClientUpdateManager import g_clientUpdateManager
from gui.shared import events, g_itemsCache
from gui.shared.events import ShowWindowEvent
from gui.Scaleform.Waiting import Waiting
from gui.shared.utils import decorators
from gui.shared.utils.requesters import Requester
from gui.shared.gui_items import GUI_ITEM_TYPE
from gui.shared.gui_items.Tankman import Tankman
from gui.shared.gui_items.processors.tankman import TankmanUnload, TankmanEquip

class Crew(CrewMeta):

    def __init__(self):
        super(Crew, self).__init__()

    def _populate(self):
        super(Crew, self)._populate()
        g_clientUpdateManager.addCallbacks({'inventory': self.onInventoryUpdate})

    def _dispose(self):
        g_clientUpdateManager.removeObjectCallbacks(self)
        super(Crew, self)._dispose()

    def onInventoryUpdate(self, invDiff):
        if GUI_ITEM_TYPE.TANKMAN in invDiff:
            self.updateTankmen()

    @process
    def updateTankmen(self):
        Waiting.show('updateTankmen')
        tankmen = yield Requester('tankman').getFromInventory()
        vehicles = yield Requester('vehicle').getFromInventory()
        vehicle = None
        if g_currentVehicle.isPresent():
            for veh in vehicles:
                if veh.inventoryId == g_currentVehicle.invID:
                    vehicle = veh
                    break

            if vehicle is None:
                LOG_ERROR('Vehicle not found', g_currentVehicle.invID)
                Waiting.hide('updateTankmen')
                return
            crew = []
            for tId in vehicle.crew:
                if tId is None:
                    crew.append(None)
                    continue
                for tankman in tankmen:
                    if tankman.inventoryId == tId:
                        crew.append(tankman)

            vehicle = g_currentVehicle.item
            commander_bonus = vehicle.bonuses['commander']
            roles = []
            brotherhood_bonus = getSkillsConfig()['brotherhood']['crewLevelIncrease']
            for t in crew:
                if t is None or 'brotherhood' not in t.skills or t.skills.index('brotherhood') == len(t.skills) - 1 and t.lastSkillLevel != 100:
                    brotherhood_bonus = 0
                break

            lessMastered = 0
            tankmenDescrs = dict(vehicle.crew)
            for slotIdx, tman in vehicle.crew:
                if slotIdx > 0 and tman is not None and (tankmenDescrs[lessMastered] is None or compareMastery(tankmenDescrs[lessMastered].descriptor, tman.descriptor) > 0):
                    lessMastered = slotIdx
                role = vehicle.descriptor.type.crewRoles[slotIdx][0]
                roles.append({'tankmanID': tman.invID if tman is not None else None,
                 'roleType': role,
                 'role': convert(getSkillsConfig()[role]['userString']),
                 'roleIcon': '%s/%s' % (Tankman.ROLE_ICON_PATH_BIG, getSkillsConfig()[role]['icon']),
                 'nationID': vehicle.nationID,
                 'typeID': vehicle.innationID,
                 'slot': slotIdx,
                 'vehicleType': vehicle.shortUserName,
                 'tankType': vehicle.type,
                 'vehicleElite': vehicle.isPremium,
                 'roles': list(vehicle.descriptor.type.crewRoles[slotIdx])})

            tankmenData = []
            crewIDs = vehicle.crewIndices.keys()
            for tankman in tankmen:
                if not tankman.isInTank or tankman.inventoryId in crewIDs:
                    bonus_role_level = commander_bonus if tankman.descriptor.role != 'commander' else 0.0
                    skills_count = len(list(ACTIVE_SKILLS))
                    skillsList = []
                    for skill in tankman.skills:
                        skillLevel = tankman.lastSkillLevel if tankman.skills.index(skill) == len(tankman.skills) - 1 else 100
                        skillsList.append({'tankmanID': tankman.inventoryId,
                         'id': skill,
                         'name': getSkillsConfig()[skill]['userString'],
                         'desc': getSkillsConfig()[skill]['description'],
                         'icon': getSkillsConfig()[skill]['icon'],
                         'level': tankman.lastSkillLevel,
                         'active': skill not in PERKS or skill == 'brotherhood' and brotherhood_bonus != 0 or skill != 'brotherhood' and skillLevel == 100})

                    newSkillsCount, lastNewSkillLvl = tankman.newSkillCount
                    if newSkillsCount > 0:
                        skillsList.append({'buy': True,
                         'tankmanID': tankman.inventoryId,
                         'level': lastNewSkillLvl})
                    tankmanData = {'firstname': tankman.firstname,
                     'lastname': tankman.lastname,
                     'rank': tankman.rank,
                     'specializationLevel': tankman.roleLevel,
                     'role': tankman.role,
                     'vehicleType': tankman.vehicle.type.shortUserString,
                     'iconFile': tankman.icon,
                     'rankIconFile': tankman.iconRank,
                     'roleIconFile': '%s/%s' % (Tankman.ROLE_ICON_PATH_BIG, tankman.iconRole),
                     'contourIconFile': tankman.vehicleIconContour,
                     'tankmanID': tankman.inventoryId,
                     'nationID': tankman.nation,
                     'typeID': tankman.vehicle.type.id[1],
                     'inTank': tankman.isInTank,
                     'roleType': tankman.descriptor.role,
                     'tankType': tankman.vehicleType,
                     'efficiencyLevel': tankman.efficiencyRoleLevel(vehicle.descriptor),
                     'bonus': bonus_role_level,
                     'lastSkillLevel': tankman.lastSkillLevel,
                     'isLessMastered': vehicle.crewIndices.get(tankman.inventoryId) == lessMastered and vehicle.isXPToTman,
                     'compact': tankman.pack(),
                     'availableSkillsCount': skills_count,
                     'skills': skillsList}
                    tankmenData.append(tankmanData)

            self.as_tankmenResponseS(roles, tankmenData)
        Waiting.hide('updateTankmen')
        return

    def onShowRecruitWindowClick(self, rendererData, menuEnabled):
        self.fireEvent(ShowWindowEvent(ShowWindowEvent.SHOW_RECRUIT_WINDOW, {'data': rendererData,
         'menuEnabled': menuEnabled,
         'currentVehicleId': g_currentVehicle.invID}))

    @decorators.process('equipping')
    def equipTankman(self, tmanInvID, slot):
        tankman = g_itemsCache.items.getTankman(int(tmanInvID))
        result = yield TankmanEquip(tankman, g_currentVehicle.item, int(slot)).request()
        if len(result.userMsg):
            SystemMessages.g_instance.pushI18nMessage(result.userMsg, type=result.sysMsgType)

    @decorators.process('unloading')
    def unloadTankman(self, tmanInvID):
        tankman = g_itemsCache.items.getTankman(int(tmanInvID))
        result = yield TankmanUnload(g_currentVehicle.item, tankman.vehicleSlotIdx).request()
        if len(result.userMsg):
            SystemMessages.g_instance.pushI18nMessage(result.userMsg, type=result.sysMsgType)

    @decorators.process('unloading')
    def unloadAllTankman(self):
        result = yield TankmanUnload(g_currentVehicle.item).request()
        if len(result.userMsg):
            SystemMessages.g_instance.pushI18nMessage(result.userMsg, type=result.sysMsgType)

    def openPersonalCase(self, value, tabNumber):
        self.fireEvent(events.ShowWindowEvent(events.ShowWindowEvent.SHOW_TANKMAN_INFO, ctx={'tankmanID': int(value),
         'page': int(tabNumber)}))
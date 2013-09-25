# Embedded file name: scripts/client/gui/Scaleform/daapi/view/lobby/barracks/Barracks.py
import BigWorld
from AccountCommands import LOCK_REASON
from adisp import process
from gui.prb_control.dispatcher import g_prbLoader
from gui.prb_control.prb_helpers import PrbListener
from items import vehicles
from helpers.i18n import convert
from items.tankmen import getSkillsConfig, ROLES
from PlayerEvents import g_playerEvents
from account_helpers.AccountSettings import AccountSettings, BARRACKS_FILTER
from CurrentVehicle import g_currentVehicle
from helpers import i18n
from debug_utils import LOG_DEBUG, LOG_ERROR
from gui.ClientUpdateManager import g_clientUpdateManager
from gui import nationCompareByIndex, SystemMessages
from gui.shared import events, g_itemsCache
from gui.shared.event_bus import EVENT_BUS_SCOPE
from gui.Scaleform.daapi import LobbySubView
from gui.Scaleform.daapi.view.meta.BarracksMeta import BarracksMeta
from gui.shared.gui_items import GUI_ITEM_TYPE
from gui.shared.gui_items.processors.common import TankmanBerthsBuyer
from gui.shared.gui_items.processors.tankman import TankmanDismiss, TankmanUnload
from gui.shared.utils import decorators
from gui.shared.utils.requesters import StatsRequester, StatsRequesterr, ShopRequester, Requester, ItemsRequester
from gui.shared.utils.gui_items import getItemByCompact
from gui.shared.gui_items.Tankman import Tankman

class Barracks(BarracksMeta, LobbySubView, PrbListener):

    def __init__(self):
        super(Barracks, self).__init__()
        self.filter = dict(AccountSettings.getFilter(BARRACKS_FILTER))

    def _populate(self):
        super(LobbySubView, self)._populate()
        self.app.component.wg_inputKeyMode = 1
        self.startPrbListening()
        g_playerEvents.onShopResync += self.__updateTankmen
        g_clientUpdateManager.addCallbacks({'inventory.8': self.__updateTankmen,
         'stats.berths': self.__updateTankmen})
        self.setTankmenFilter()

    def _dispose(self):
        g_clientUpdateManager.removeObjectCallbacks(self)
        g_playerEvents.onShopResync -= self.__updateTankmen
        self.stopPrbListening()
        super(LobbySubView, self)._dispose()

    def openPersonalCase(self, value, tabNumber):
        self.fireEvent(events.ShowWindowEvent(events.ShowWindowEvent.SHOW_TANKMAN_INFO, ctx={'tankmanID': int(value),
         'page': int(tabNumber)}))

    def closeBarracks(self):
        self.fireEvent(events.LoadEvent(events.LoadEvent.LOAD_HANGAR), scope=EVENT_BUS_SCOPE.LOBBY)

    def invalidateTanksList(self):
        self.__updateTanksList()

    def update(self):
        self.__updateTankmen()

    def onShowRecruitWindowClick(self, rendererData, menuEnabled):
        self.fireEvent(events.ShowWindowEvent(events.ShowWindowEvent.SHOW_RECRUIT_WINDOW, {'data': rendererData,
         'menuEnabled': menuEnabled}))

    @decorators.process('buyBerths')
    def buyBerths(self):
        stats = yield StatsRequesterr().request()
        shop = yield ShopRequester().request()
        berthPrice, berthsCount = shop.getTankmanBerthPrice(stats.tankmenBerthsCount)
        result = yield TankmanBerthsBuyer((0, berthPrice), berthsCount).request()
        if len(result.userMsg):
            SystemMessages.g_instance.pushI18nMessage(result.userMsg, type=result.sysMsgType)

    @process
    def __updateTanksList(self):
        data = list()
        modulesAll = yield Requester('vehicle').getFromInventory()
        modulesAll.sort()
        for module in modulesAll:
            if self.filter['nation'] != -1 and self.filter['nation'] != module.descriptor.type.id[0] or self.filter['tankType'] != 'None' and self.filter['tankType'] != module.type:
                continue
            data.append({'data': {'type': module.type,
                      'nationID': module.descriptor.type.id[0],
                      'typeID': module.descriptor.type.id[1]},
             'label': module.descriptor.type.shortUserString})

        self.as_updateTanksListS(data)

    def setTankmenFilter(self):
        self.as_setTankmenFilterS(self.filter['nation'], self.filter['role'], self.filter['tankType'], self.filter['location'], self.filter['nationID'])

    def setFilter(self, nation, role, tankType, location, nationID):
        self.filter['nation'] = nation
        self.filter['role'] = role
        self.filter['tankType'] = tankType
        self.filter['location'] = location
        self.filter['nationID'] = nationID
        AccountSettings.setFilter(BARRACKS_FILTER, self.filter)
        self.__updateTankmen()

    @process
    def onShowRecruitWindow(self, callbackID):
        credits = yield StatsRequester().getCredits()
        gold = yield StatsRequester().getGold()
        upgradeParams = yield StatsRequester().getTankmanCost()
        data = [credits,
         gold,
         round(upgradeParams[1]['credits']),
         upgradeParams[2]['gold'],
         len(ROLES)]
        for role in ROLES:
            data.append(role)
            data.append(convert(getSkillsConfig()[role]['userString']))

        unlocks = yield StatsRequester().getUnlocks()
        modulesAll = yield Requester('vehicle').getFromShop()
        modulesAll.sort()
        for module in modulesAll:
            compdecs = module.descriptor.type.compactDescr
            if compdecs in unlocks:
                data.append(module.type)
                data.append(module.descriptor.type.id[0])
                data.append(module.descriptor.type.id[1])
                data.append(module.descriptor.type.shortUserString)

    @decorators.process('updateTankmen')
    def __updateTankmen(self, *args):
        tankmen = yield Requester('tankman').getFromInventory()
        vcls = yield Requester('vehicle').getFromInventory()
        slots = yield StatsRequester().getTankmenBerthsCount()
        berths = yield StatsRequester().getTankmenBerthsCount()
        berthsPrices = yield StatsRequester().getBerthsPrices()
        berthPrice = BigWorld.player().shop.getNextBerthPackPrice(berths, berthsPrices)
        tankmenList = list()
        tankmenInBarracks = 0
        TANKMEN_ROLES_ORDER = {'commander': 0,
         'gunner': 1,
         'driver': 2,
         'radioman': 3,
         'loader': 4}

        def tankmenSortFunc(first, second):
            if first is None or second is None:
                return 1
            res = nationCompareByIndex(first.nation, second.nation)
            if res:
                return res
            elif first.isInTank and not second.isInTank:
                return -1
            elif not first.isInTank and second.isInTank:
                return 1
            if first.isInTank and second.isInTank:
                tman1vehicle, tman2vehicle = (None, None)
                for vcl in vcls:
                    if vcl.inventoryId == first.vehicleID:
                        tman1vehicle = vcl
                    if vcl.inventoryId == second.vehicleID:
                        tman2vehicle = vcl
                    if tman1vehicle is not None and tman2vehicle is not None:
                        break

                res = tman1vehicle.__cmp__(tman2vehicle)
                if res:
                    return res
                if TANKMEN_ROLES_ORDER[first.descriptor.role] < TANKMEN_ROLES_ORDER[second.descriptor.role]:
                    return -1
                if TANKMEN_ROLES_ORDER[first.descriptor.role] > TANKMEN_ROLES_ORDER[second.descriptor.role]:
                    return 1
            if first.lastname < second.lastname:
                return -1
            elif first.lastname > second.lastname:
                return 1
            else:
                return 1

        tankmen.sort(tankmenSortFunc)
        for tankman in tankmen:
            if not tankman.isInTank:
                tankmenInBarracks += 1
            if self.filter['nation'] != -1 and tankman.nation != self.filter['nation'] or self.filter['role'] != 'None' and tankman.descriptor.role != self.filter['role'] or self.filter['tankType'] != 'None' and tankman.vehicleType != self.filter['tankType'] or self.filter['location'] == 'tanks' and tankman.isInTank != True or self.filter['location'] == 'barracks' and tankman.isInTank == True or self.filter['nationID'] is not None and (self.filter['location'] != str(tankman.vehicle.type.id[1]) or self.filter['nationID'] != str(tankman.nation)):
                continue
            slot, vehicleID, vehicle = (None, None, None)
            if tankman.isInTank:
                for vcl in vcls:
                    if vcl.inventoryId == tankman.vehicleID:
                        vehicle = vcl
                        vehicleID = vehicle.inventoryId
                        break

                for i in range(len(vehicle.crew)):
                    if vehicle.crew[i] == tankman.inventoryId:
                        slot = i
                        break

            isLocked, msg = self.getTankmanLockMessage(vehicle) if tankman.isInTank else (False, '')
            isInCurrentTank = tankman.vehicleID == g_currentVehicle.invID if tankman.isInTank and g_currentVehicle.isPresent() else False
            tankmenList.append({'firstname': tankman.firstname,
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
             'slot': slot,
             'roleType': tankman.descriptor.role,
             'tankType': tankman.vehicleType,
             'inTank': tankman.isInTank,
             'inCurrentTank': isInCurrentTank,
             'vehicleID': vehicleID,
             'compact': tankman.pack(),
             'locked': isLocked,
             'lockMessage': msg,
             'vehicleBroken': vehicle.repairCost > 0 if tankman.isInTank else None,
             'isInSelfVehicleClass': vehicle.type == tankman.vehicleType if tankman.isInTank else True,
             'isInSelfVehicleType': vehicle.shortName == tankman.vehicle.type.shortUserString if tankman.isInTank else True})

        self.as_setTankmenS(len(tankmen), slots, tankmenInBarracks, BigWorld.wg_getGoldFormat(berthPrice), berthsPrices[1], tankmenList)
        return

    @staticmethod
    def getTankmanLockMessage(invVehicle):
        if invVehicle.lock == LOCK_REASON.ON_ARENA:
            return (True, i18n.makeString('#menu:tankmen/lockReason/inbattle'))
        elif invVehicle.repairCost > 0:
            return (False, i18n.makeString('#menu:tankmen/lockReason/broken'))
        else:
            if invVehicle.isCurrent:
                dispatcher = g_prbLoader.getDispatcher()
                if dispatcher is not None:
                    permission = dispatcher.getPrbFunctional().getPermissions()
                    if permission and not permission.canChangeVehicle():
                        return (True, i18n.makeString('#menu:tankmen/lockReason/prebattle'))
            return (False, '')

    @decorators.process('updating')
    def dismissTankman(self, dataCompact):
        tmanOldItem = getItemByCompact(dataCompact)
        if tmanOldItem is None:
            LOG_ERROR('Attempt to dismiss tankman by invalid compact')
            return
        else:
            tankman = g_itemsCache.items.getTankman(tmanOldItem.inventoryId)
            result = yield TankmanDismiss(tankman).request()
            if len(result.userMsg):
                SystemMessages.g_instance.pushMessage(result.userMsg, type=result.sysMsgType)
            return

    @decorators.process('unloading')
    def unloadTankman(self, dataCompact):
        tmanOldItem = getItemByCompact(dataCompact)
        if tmanOldItem is None:
            LOG_ERROR('Attempt to unload tankman by invalid compact')
            return
        else:
            tankman = g_itemsCache.items.getTankman(tmanOldItem.inventoryId)
            tmanVehile = g_itemsCache.items.getVehicle(tankman.vehicleInvID)
            if tmanVehile is None:
                LOG_ERROR("Target tankman's vehicle is not found in inventory", tankman, tankman.vehicleInvID)
                return
            result = yield TankmanUnload(tmanVehile, tankman.vehicleSlotIdx).request()
            if len(result.userMsg):
                SystemMessages.g_instance.pushI18nMessage(result.userMsg, type=result.sysMsgType)
            return

    def onPrbFunctionalFinished(self):
        self.__updateTankmen()

    def onPlayerStateChanged(self, functional, roster, accountInfo):
        if accountInfo.isCurrentPlayer():
            self.__updateTankmen()
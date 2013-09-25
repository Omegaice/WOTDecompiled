# Embedded file name: scripts/client/CurrentVehicle.py
import BigWorld
from Event import Event
from items import vehicles
from helpers import isPlayerAccount
from account_helpers.AccountSettings import AccountSettings, CURRENT_VEHICLE
from gui.ClientUpdateManager import g_clientUpdateManager
from gui import prb_control
from gui.shared import g_itemsCache, REQ_CRITERIA
from gui.shared.utils.HangarSpace import g_hangarSpace
from gui.shared.gui_items import GUI_ITEM_TYPE
from gui.shared.gui_items.Vehicle import Vehicle
from gui.Scaleform.locale.MENU import MENU
from gui.Scaleform.Waiting import Waiting

class _CurrentVehicle():

    def __init__(self):
        self.__vehInvID = 0
        self.__changeCallbackID = None
        self.onChanged = Event()
        self.onChangeStarted = Event()
        return

    def init(self):
        g_clientUpdateManager.addCallbacks({'inventory': self.onInventoryUpdate,
         'cache.vehsLock': self.onLocksUpdate})
        prbVehicle = self.__checkPrebattleLockedVehicle()
        storedVehInvID = AccountSettings.getFavorites(CURRENT_VEHICLE)
        self.selectVehicle(prbVehicle or storedVehInvID)

    def destroy(self):
        self.__vehInvID = 0
        self.__clearChangeCallback()
        self.onChanged.clear()
        self.onChangeStarted.clear()
        g_clientUpdateManager.removeObjectCallbacks(self)
        g_hangarSpace.removeVehicle()
        self.selectNoVehicle()

    def onInventoryUpdate(self, invDiff):
        vehsDiff = invDiff.get(GUI_ITEM_TYPE.VEHICLE, {})
        isVehicleSold = False
        isVehicleDescrChanged = False
        if 'compDescr' in vehsDiff and self.__vehInvID in vehsDiff['compDescr']:
            isVehicleSold = vehsDiff['compDescr'][self.__vehInvID] is None
            isVehicleDescrChanged = not isVehicleSold
        if isVehicleSold or self.__vehInvID == 0:
            self.selectVehicle()
        elif 'repair' in vehsDiff:
            isRepaired = self.__vehInvID in vehsDiff['repair']
            if not GUI_ITEM_TYPE.TURRET in invDiff:
                isComponentsChanged = GUI_ITEM_TYPE.GUN in invDiff
                isVehicleChanged = len(filter(lambda hive: self.__vehInvID in hive, vehsDiff.itervalues())) > 0
                (isComponentsChanged or isRepaired or isVehicleDescrChanged) and self.refreshModel()
            (isVehicleChanged or isRepaired) and self.onChanged()
        return

    def onLocksUpdate(self, locksDiff):
        if self.__vehInvID in locksDiff:
            self.refreshModel()

    def refreshModel(self):
        if self.isPresent() and self.isInHangar() and self.item.modelState:
            g_hangarSpace.updateVehicle(self.item)
        else:
            g_hangarSpace.removeVehicle()

    @property
    def invID(self):
        return self.__vehInvID

    @property
    def item(self):
        if self.__vehInvID > 0:
            return g_itemsCache.items.getVehicle(self.__vehInvID)
        else:
            return None

    def isPresent(self):
        return self.item is not None

    def isBroken(self):
        return self.isPresent() and self.item.isBroken

    def isLocked(self):
        return self.isPresent() and self.item.isLocked

    def isClanLock(self):
        return self.isPresent() and self.item.clanLock > 0

    def isCrewFull(self):
        return self.isPresent() and self.item.isCrewFull

    def isInBattle(self):
        return self.isPresent() and self.item.isInBattle

    def isInHangar(self):
        return self.isPresent() and not self.item.isInBattle

    def isAwaitingBattle(self):
        return self.isPresent() and self.item.isAwaitingBattle

    def isAlive(self):
        return self.isPresent() and self.item.isAlive

    def isReadyToPrebattle(self):
        return self.isPresent() and self.item.isReadyToPrebattle

    def isReadyToFight(self):
        return self.isPresent() and self.item.isReadyToFight

    def selectVehicle(self, vehInvID = 0):
        vehicle = g_itemsCache.items.getVehicle(vehInvID)
        if vehicle is None:
            invVehs = g_itemsCache.items.getVehicles(criteria=REQ_CRITERIA.INVENTORY)
            if len(invVehs):
                vehInvID = sorted(invVehs.itervalues())[0].invID
            else:
                vehInvID = 0
        self.__selectVehicle(vehInvID)
        return

    def selectNoVehicle(self):
        self.__selectVehicle(0)

    def getHangarMessage(self):
        if self.isPresent():
            state, stateLvl = self.item.getState()
            return ('#menu:currentVehicleStatus/' + state, stateLvl)
        return (MENU.CURRENTVEHICLESTATUS_NOTPRESENT, Vehicle.VEHICLE_STATE_LEVEL.CRITICAL)

    def __selectVehicle(self, vehInvID):
        if vehInvID == self.__vehInvID:
            return
        Waiting.show('updateCurrentVehicle', isSingle=True)
        self.onChangeStarted()
        self.__vehInvID = vehInvID
        AccountSettings.setFavorites(CURRENT_VEHICLE, vehInvID)
        self.refreshModel()
        if not self.__changeCallbackID:
            self.__changeCallbackID = BigWorld.callback(0.1, self.__changeDone)

    def __changeDone(self):
        self.__clearChangeCallback()
        if isPlayerAccount():
            self.onChanged()
        Waiting.hide('updateCurrentVehicle')

    def __clearChangeCallback(self):
        if self.__changeCallbackID is not None:
            BigWorld.cancelCallback(self.__changeCallbackID)
            self.__changeCallbackID = None
        return

    def __checkPrebattleLockedVehicle(self):
        clientPrb = prb_control.getClientPrebattle()
        if clientPrb is not None:
            rosters = prb_control.getPrebattleRosters(prebattle=clientPrb)
            for rId, roster in rosters.iteritems():
                if BigWorld.player().id in roster:
                    vehCompDescr = roster[BigWorld.player().id].get('vehCompDescr', '')
                    if len(vehCompDescr):
                        vehDescr = vehicles.VehicleDescr(vehCompDescr)
                        vehicle = g_itemsCache.items.getItemByCD(vehDescr.type.compactDescr)
                        if vehicle is not None:
                            return vehicle.invID

        return 0

    def __repr__(self):
        return 'CurrentVehicle(%s)' % str(self.item)


g_currentVehicle = _CurrentVehicle()
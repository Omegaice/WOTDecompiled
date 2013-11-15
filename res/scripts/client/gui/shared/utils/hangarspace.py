# 2013.11.15 11:27:00 EST
# Embedded file name: scripts/client/gui/shared/utils/HangarSpace.py
import BigWorld
from items import vehicles
from gui import game_control
from gui.ClientHangarSpace import ClientHangarSpace
from gui.Scaleform.Waiting import Waiting
from debug_utils import LOG_DEBUG

class _HangarSpace(object):
    isPremium = property(lambda self: (self.__isSpacePremium if self.__spaceInited else self.__delayedIsPremium))

    def __init__(self):
        self.__space = ClientHangarSpace()
        self.__inited = False
        self.__spaceInited = False
        self.__isSpacePremium = False
        self.__delayedIsPremium = False
        self.__delayedForceRefresh = False
        self.__delayedRefreshCallback = None
        self.__spaceDestroyedDuringLoad = False
        self.__lastUpdatedVehicle = None
        return

    @property
    def space(self):
        if self.spaceInited:
            return self.__space
        else:
            return None

    @property
    def inited(self):
        return self.__inited

    @property
    def spaceInited(self):
        return self.__spaceInited

    def spaceLoading(self):
        return self.__space.spaceLoading()

    def init(self, isPremium):
        if not self.__spaceInited:
            LOG_DEBUG('_HangarSpace::init')
            Waiting.show('loadHangarSpace')
            self.__inited = True
            self.__isSpacePremium = isPremium
            self.__space.create(isPremium, self.__spaceDone)
            if self.__lastUpdatedVehicle is not None:
                self.updateVehicle(self.__lastUpdatedVehicle)
        return

    def refreshSpace(self, isPremium, forceRefresh = False):
        if not self.__spaceInited:
            LOG_DEBUG('_HangarSpace::refreshSpace(isPremium={0!r:s}) - is delayed until space load is done'.format(isPremium))
            if self.__delayedRefreshCallback is None:
                self.__delayedRefreshCallback = BigWorld.callback(0.1, self.__delayedRefresh)
            self.__delayedIsPremium = isPremium
            self.__delayedForceRefresh = forceRefresh
            return
        else:
            LOG_DEBUG('_HangarSpace::refreshSpace(isPremium={0!r:s})'.format(isPremium))
            if self.__isSpacePremium != isPremium or forceRefresh:
                self.destroy()
                self.init(isPremium)
            self.__isSpacePremium = isPremium
            return

    def destroy(self):
        if self.__spaceInited:
            LOG_DEBUG('_HangarSpace::destroy')
            self.__inited = False
            self.__spaceInited = False
            self.__space.destroy()
        elif self.spaceLoading():
            LOG_DEBUG('_HangarSpace::destroy - delayed until space load done')
            self.__spaceDestroyedDuringLoad = True
        if self.__delayedRefreshCallback is not None:
            BigWorld.cancelCallback(self.__delayedRefreshCallback)
            self.__delayedRefreshCallback = None
        return

    def _stripVehCompDescrIfRoaming(self, vehCompDescr):
        if game_control.g_instance.roaming.isInRoaming():
            vehCompDescr = vehicles.stripCustomizationFromVehicleCompactDescr(vehCompDescr, True, True, False)[0]
        return vehicles.VehicleDescr(compactDescr=vehCompDescr)

    def updateVehicle(self, vehicle):
        if self.__inited:
            Waiting.show('loadHangarSpaceVehicle', True)
            self.__space.recreateVehicle(self._stripVehCompDescrIfRoaming(vehicle.descriptor.makeCompactDescr()), vehicle.modelState, self.__changeDone)
            self.__lastUpdatedVehicle = vehicle

    def removeVehicle(self):
        if self.__inited:
            Waiting.show('loadHangarSpaceVehicle')
            self.__space.removeVehicle()
            self.__changeDone()
            self.__lastUpdatedVehicle = None
        return

    def __spaceDone(self):
        self.__spaceInited = True
        if self.__spaceDestroyedDuringLoad:
            self.__spaceDestroyedDuringLoad = False
            self.destroy()
        Waiting.hide('loadHangarSpace')

    def __changeDone(self):
        Waiting.hide('loadHangarSpaceVehicle')

    def __delayedRefresh(self):
        self.__delayedRefreshCallback = None
        if not self.__spaceInited:
            self.__delayedRefreshCallback = BigWorld.callback(0.1, self.__delayedRefresh)
            return
        else:
            self.refreshSpace(self.__delayedIsPremium, self.__delayedForceRefresh)
            return


g_hangarSpace = _HangarSpace()
# okay decompyling res/scripts/client/gui/shared/utils/hangarspace.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:27:01 EST

# 2013.11.15 11:27:06 EST
# Embedded file name: scripts/client/gui/shared/utils/requesters/StatsRequesterr.py
import BigWorld
from adisp import async
from gui.shared.utils.requesters.abstract import RequesterAbstract

class StatsRequesterr(RequesterAbstract):

    @async
    def _requestCache(self, callback):
        BigWorld.player().stats.getCache(lambda resID, value: self._response(resID, value, callback))

    @property
    def mayConsumeWalletResources(self):
        """
        @return: Wallet resources available flag
        """
        return bool(self.getCacheValue('mayConsumeWalletResources', 0))

    @property
    def credits(self):
        """
        @return: account credits balance as positive value
        """
        return max(self.actualCredits, 0)

    @property
    def gold(self):
        """
        @return: account gold balance as positive value
        """
        return max(self.actualGold, 0)

    @property
    def money(self):
        return (self.credits, self.gold)

    @property
    def actualCredits(self):
        """
        @return: account credits actual balance
        """
        return self.getCacheValue('credits', 0)

    @property
    def actualGold(self):
        """
        @return: account gold actual balance
        """
        from gui import game_control
        if self.mayConsumeWalletResources or not game_control.g_instance.wallet.useGold:
            return self.getCacheValue('gold', 0)
        return 0

    @property
    def actualMoney(self):
        return (self.actualCredits, self.actualGold)

    @property
    def freeXP(self):
        """
        @return: account free experience value greater then zero
        """
        return max(self.actualFreeXP, 0)

    @property
    def actualFreeXP(self):
        """
        @return: account free experience value
        """
        from gui import game_control
        if self.mayConsumeWalletResources or not game_control.g_instance.wallet.useFreeXP:
            return self.getCacheValue('freeXP', 0)
        return 0

    @property
    def vehiclesXPs(self):
        """
        @return: vehicles experience. Dict format:
                                { vehicle type int compact descriptor: xp value, }
        """
        return self.getCacheValue('vehTypeXP', dict())

    @property
    def multipliedVehicles(self):
        """
        @return: current day already multiplied vehicles list. Format:
                                [vehicle type int compact descriptor, ...]
        """
        return self.getCacheValue('multipliedXPVehs', list())

    @property
    def eliteVehicles(self):
        """
        @return: elite vehicles list. Format:
                                [vehicle type int compact descriptor, ...]
        """
        return self.getCacheValue('eliteVehicles', list())

    @property
    def vehicleTypeLocks(self):
        """
        @return: vehicles locks. Now available only clan locks [1]. Format:
                { vehicle type int compact descriptor: { 1: time to unlock in seconds }, }
        """
        return self.getCacheValue('vehTypeLocks', dict())

    @property
    def globalVehicleLocks(self):
        """
        @return: vehicles locks. Now available only clan locks [1]. Format:
                { vehicle type int compact descriptor: { 1: time to unlock in seconds }, }
        """
        return self.getCacheValue('globalVehicleLocks', dict())

    @property
    def attributes(self):
        """
        @return: account attributes. Bit combination of
                                constants.ACCOUNT_ATTR.*
        """
        return self.getCacheValue('attrs', 0)

    @property
    def restrictions(self):
        """
        @return: account restrictions. Set of values
                                constants.RESTRICTION_TYPE.*
        """
        return self.getCacheValue('restrictions', set())

    @property
    def unlocks(self):
        """
        @return: unlocked items. Format:
                                [int compact descriptor, ...]
        """
        return self.getCacheValue('unlocks', list())

    @property
    def vehicleSlots(self):
        """
        @return: vehicles carousel slots count
        """
        return self.getCacheValue('slots', 0)

    @property
    def dailyPlayHours(self):
        """
        @return: played hours per each day in current month. List of
                                hours values. Current day played hours value is
                                cache['dailyPlayHours'][0].
        """
        return self.getCacheValue('dailyPlayHours', [0])

    @property
    def playLimits(self):
        """
        @return: playing time limits, (hours per day, hours per week)
        """
        return self.getCacheValue('playLimits', ((0, ''), (0, '')))

    @property
    def tankmenBerthsCount(self):
        """
        @return: tankmen berths count in barracks.
        """
        return self.getCacheValue('berths', 0)

    @property
    def vehicleSellsLeft(self):
        """
        @return: value of vehicle sells left this day.
        """
        return self.getCacheValue('vehicleSellsLeft', 0)

    @property
    def freeTankmenLeft(self):
        """
        @return: value of free tankmen recruit operations
        of this day.
        """
        return self.getCacheValue('freeTMenLeft', 0)

    @property
    def accountDossier(self):
        """
        @return: account dossier compact descriptor
        """
        return self.getCacheValue('dossier', '')

    @property
    def denunciationsLeft(self):
        """
        @return: value of denunciations left this day.
        """
        return self.getCacheValue('denunciationsLeft', 0)

    @property
    def freeVehiclesLeft(self):
        """
        @return: value of free Vehicles left this day.
        """
        return self.getCacheValue('freeVehiclesLeft', '')

    @property
    def clanDBID(self):
        """
        @return: account credits balance
        """
        return self.getCacheValue('clanDBID', 0)

    def getGlobalRating(self):
        return self.getCacheValue('globalRating', 0)
# okay decompyling res/scripts/client/gui/shared/utils/requesters/statsrequesterr.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:27:06 EST

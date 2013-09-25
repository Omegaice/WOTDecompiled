from gui.Scaleform.framework import AppRef
from gui.ClientUpdateManager import g_clientUpdateManager
from CurrentVehicle import g_currentVehicle

class SoundEventManager(AppRef):
    SPEND_CREDITS_GOLD = 'spend_credits_and_gold'
    SPEND_CREDITS = 'spend_credits'
    SPEND_GOLD = 'spend_gold'
    EARN_CREDITS_GOLD = 'earn_credits_and_gold'
    EARN_CREDITS = 'earn_credits'
    EARN_GOLD = 'earn_gold'

    def __init__(self, credits = 0, gold = 0):
        self.__credits = credits
        self.__gold = gold
        g_clientUpdateManager.addCallbacks({'stats': self.onStatsChanged})
        g_currentVehicle.onChangeStarted += self.onVehicleChanging

    def cleanUp(self):
        g_clientUpdateManager.removeObjectCallbacks(self)
        g_currentVehicle.onChangeStarted -= self.onVehicleChanging

    def __playSound(self, soundName):
        if self.app.soundManager is not None:
            self.app.soundManager.playEffectSound(soundName)
        return

    def onVehicleChanging(self):
        """ Current vehicle starts changing event handler """
        self.__playSound('effects.vehicle_changing')

    def onStatsChanged(self, stats):
        """ Client stats changed event handler """
        newCredits = stats.get('credits', self.__credits)
        newGold = stats.get('gold', self.__gold)
        if newCredits < self.__credits and newGold < self.__gold:
            self.__playSound(SoundEventManager.SPEND_CREDITS_GOLD)
        elif newCredits > self.__credits and newGold > self.__gold:
            self.__playSound(SoundEventManager.EARN_CREDITS_GOLD)
        elif newCredits < self.__credits:
            self.__playSound(SoundEventManager.SPEND_CREDITS)
        elif newCredits > self.__credits:
            self.__playSound(SoundEventManager.EARN_CREDITS)
        elif newGold < self.__gold:
            self.__playSound(SoundEventManager.SPEND_GOLD)
        elif newGold > self.__gold:
            self.__playSound(SoundEventManager.EARN_GOLD)
        self.__credits, self.__gold = newCredits, newGold

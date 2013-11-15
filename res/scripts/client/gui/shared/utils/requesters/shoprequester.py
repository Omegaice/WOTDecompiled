# 2013.11.15 11:27:06 EST
# Embedded file name: scripts/client/gui/shared/utils/requesters/ShopRequester.py
import BigWorld
from adisp import async
from gui.shared.utils.requesters.abstract import RequesterAbstract

class ShopRequester(RequesterAbstract):

    @async
    def _requestCache(self, callback):
        """
        Overloaded method to request shop cache
        """
        BigWorld.player().shop.getCache(lambda resID, value, rev: self._response(resID, value, callback))

    def getPrices(self):
        return self.getItemsData().get('itemPrices', {})

    def getHiddens(self):
        return self.getItemsData().get('notInShopItems', set([]))

    def getVehiclesForGold(self):
        return self.getItemsData().get('vehiclesToSellForGold', set([]))

    def getItem(self, intCD):
        return (self.getPrices().get(intCD, (0, 0)), intCD in self.getHiddens(), intCD in self.getVehiclesForGold())

    @property
    def revision(self):
        """
        @return: shop revision value
        """
        return self.getCacheValue('rev', 0)

    @property
    def paidRemovalCost(self):
        """
        @return: cost of dismantling of non-removable optional
                                devices for gold
        """
        return self.getCacheValue('paidRemovalCost', 10)

    @property
    def exchangeRate(self):
        """
        @return: rate of gold for credits exchanging
        """
        return self.getCacheValue('exchangeRate', 400)

    @property
    def exchangeRateForShellsAndEqs(self):
        """
        @return: rate of gold for credits exchanging for F2W
                                premium shells and eqs action
        """
        return self.getCacheValue('exchangeRateForShellsAndEqs', 400)

    def sellPriceModifiers(self, compDescr):
        itemsData = self.getItemsData()
        sellPriceModif = self.getCacheValue('sellPriceModif', 0.5)
        sellPriceFactors = itemsData.get('vehicleSellPriceFactors', {})
        sellForGold = itemsData.get('vehiclesToSellForGold', {})
        return (self.revision,
         self.exchangeRate,
         self.exchangeRateForShellsAndEqs,
         sellPriceModif,
         sellPriceFactors.get(compDescr, sellPriceModif),
         compDescr in sellForGold)

    def getVehicleSlotsPrice(self, currentSlotsCount):
        """
        @param currentSlotsCount: current vehicle slots count
        @return: new vehicle slot price
        """
        prices = self.getCacheValue('slotsPrices', [0, [0]])
        return BigWorld.player().shop.getNextSlotPrice(currentSlotsCount, prices)

    @property
    def dropSkillsCost(self):
        """
        @return: drop tankman skill cost
        """
        return self.getCacheValue('dropSkillsCost', dict())

    @property
    def dailyXPFactor(self):
        """
        @return: daily experience multiplier
        """
        return self.getCacheValue('dailyXPFactor', 2)

    def getTankmanBerthPrice(self, berthsCount):
        """
        @param berthsCount: current barrack's berths count
        @return: (new berths pack price, pack berths count)
        """
        prices = self.getCacheValue('berthsPrices', (0, 0, [0]))
        return (BigWorld.player().shop.getNextBerthPackPrice(berthsCount, prices), prices[1])

    @property
    def isEnabledBuyingGoldShellsForCredits(self):
        """
        @return: is premium shells for credits action enabled
        """
        return self.getCacheValue('isEnabledBuyingGoldShellsForCredits', False)

    @property
    def isEnabledBuyingGoldEqsForCredits(self):
        """
        @return: is premium equipments for credits action enabled
        """
        return self.getCacheValue('isEnabledBuyingGoldEqsForCredits', False)

    @property
    def tankmanCost(self):
        """
        @return: tankman studying cost
                        tmanCost -  ( tmanCostType, ), where
                        tmanCostType = {
                                        'roleLevel' : minimal role level after operation,
                                        'credits' : cost in credits,
                                        'gold' : cost in gold,
                                        'baseRoleLoss' : float in [0, 1], fraction of role to drop,
                                        'classChangeRoleLoss' : float in [0, 1], fraction of role to drop additionally if
                                                classes of self.vehicleTypeID and newVehicleTypeID are different,
                                        'isPremium' : tankman becomes premium,
                                        }.
                                List is sorted by role level.
        """
        return self.getCacheValue('tankmanCost', tuple())

    @property
    def freeXPConversion(self):
        """
        @return: free experience to vehicle xp exchange rate and cost
                                ( discrecity, cost)
        """
        return self.getCacheValue('freeXPConversion', 25)

    @property
    def passportChangeCost(self):
        """
        @return: tankman passport replace cost in gold
        """
        return self.getCacheValue('passportChangeCost', 50)

    @property
    def ebankVCoinExchangeRate(self):
        return self.getCacheValue('ebank/vcoinExchangeRate', 20)

    @property
    def ebankMinTransactionValue(self):
        return self.getCacheValue('ebank/vcoinMinTransactionValue', 50)

    @property
    def ebankMaxTransactionValue(self):
        return self.getCacheValue('ebank/vcoinMaxTransactionValue', 50000)

    @property
    def freeXPToTManXPRate(self):
        """
        @return: free experience to tankman experience exchange rate
        """
        return self.getCacheValue('freeXPToTManXPRate', '')

    def getItemsData(self):
        return self.getCacheValue('items', {})

    def getVehCamouflagePriceFactor(self, typeCompDescr):
        return self.getItemsData().get('vehicleCamouflagePriceFactors', {}).get(typeCompDescr)

    def getHornPriceFactor(self, hornID):
        return self.getItemsData().get('vehicleHornPriceFactors', {}).get(hornID)

    def getEmblemsGroupPriceFactors(self):
        return self.getItemsData().get('playerEmblemGroupPriceFactors', {})

    def getEmblemsGroupHiddens(self):
        return self.getItemsData().get('notInShopPlayerEmblemGroups', set([]))

    def getInscriptionsGroupPriceFactors(self, nationID):
        return self.getItemsData().get('inscriptionGroupPriceFactors', [])[nationID]

    def getInscriptionsGroupHiddens(self, nationID):
        return self.getItemsData().get('notInShopInscriptionGroups', [])[nationID]

    def getCamouflagesPriceFactors(self, nationID):
        return self.getItemsData().get('camouflagePriceFactors', [])[nationID]

    def getCamouflagesHiddens(self, nationID):
        return self.getItemsData().get('notInShopCamouflages', [])[nationID]

    def getHornPrice(self, hornID):
        return self.getItemsData().get('hornPrices', {}).get(hornID)
# okay decompyling res/scripts/client/gui/shared/utils/requesters/shoprequester.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:27:06 EST

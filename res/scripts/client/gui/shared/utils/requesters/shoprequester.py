import BigWorld
from adisp import async
from items import vehicles, ITEM_TYPE_NAMES
from debug_utils import LOG_DEBUG
from gui.shared.gui_items import GUI_ITEM_TYPE
from gui.shared.utils.requesters.abstract import RequesterAbstract

class ShopRequester(RequesterAbstract):

    def __init__(self):
        super(ShopRequester, self).__init__()
        self.__newShopCache = {}

    @async
    def _requestCache(self, callback):
        """
        Overloaded method to request shop cache
        """
        BigWorld.player().shop.getCache(lambda resID, value, rev: self._response(resID, value, callback))

    def getItemsData(self):
        return self.__newShopCache

    def getPrices(self):
        return self.getItemsData().get('itemPrices', {})

    def getHiddens(self):
        return self.getItemsData().get('notInShopItems', set([]))

    def getVehiclesForGold(self):
        return self.getItemsData().get('vehiclesToSellForGold', set([]))

    def _response(self, resID, value, callback):
        itemPrices = {}
        notInShopItems = set()
        vehiclesToSellForGold = set()
        self.__newShopCache.clear()
        if value is not None:
            for nationID, nationData in value.get('items', {}).iteritems():
                for itemTypeID, itemsData in nationData.iteritems():
                    prices, extData = itemsData
                    notInShop = extData.get('notInShop', set())
                    sellForGold = extData.get('sellForGold', set())
                    for shopKey, price in prices.iteritems():
                        if itemTypeID == GUI_ITEM_TYPE.VEHICLE:
                            intCD = vehicles.makeIntCompactDescrByID(ITEM_TYPE_NAMES[itemTypeID], nationID, shopKey)
                        else:
                            intCD = shopKey
                        itemPrices[intCD] = price
                        if shopKey in notInShop:
                            notInShopItems.add(intCD)
                        if shopKey in sellForGold:
                            vehiclesToSellForGold.add(intCD)

            self.__newShopCache = {'itemPrices': itemPrices,
             'notInShopItems': notInShopItems,
             'vehiclesToSellForGold': vehiclesToSellForGold}
        super(ShopRequester, self)._response(resID, value, callback)
        return

    def getItems(self, itemTypeIdx, nationIdx, shopDataIdx = None):
        """
        Returns items data from cache by given criteria
        
        @param itemTypeIdx: item type index from common.items.ITEM_TYPE_NAMES
        @param nationIdx: item nation index from nations.NAMES
        @param shopDataIdx: optional argument. Index from shop cache for
                requested item type @itemTypeIdx. If it is specified this method
                returns only one item data for given index otherwise - data for
                all items of given type.
        """
        itemsData = self.getCacheValue('items', {}).get(nationIdx, {}).get(itemTypeIdx)
        if itemsData is not None:
            if shopDataIdx is None:
                return itemsData
            prices, extData = itemsData
            return (prices.get(shopDataIdx, (0, 0)), shopDataIdx in extData.get('notInShop', set()))
        else:
            return (None, False)

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
        itemTypeIdx, nationIdx, innationIdx = vehicles.parseIntCompactDescr(compDescr)
        itemsData = self.getCacheValue('items', {}).get(nationIdx, {}).get(itemTypeIdx, ({}, {}))
        _, extData = itemsData
        sellPriceModif = self.getCacheValue('sellPriceModif', 0.5)
        return (self.revision,
         self.exchangeRate,
         self.exchangeRateForShellsAndEqs,
         sellPriceModif,
         extData.get('sellPriceFactors', {}).get(innationIdx, sellPriceModif),
         innationIdx in extData.get('sellForGold', set()))

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

# Embedded file name: scripts/client/gui/Scaleform/daapi/view/lobby/customization/data_providers.py
import gui
import Math
import time
import Event
import BigWorld
from abc import abstractmethod, ABCMeta
from debug_utils import LOG_DEBUG
from gui import SystemMessages
from gui.Scaleform.framework.entities.DAAPIModule import DAAPIModule
from gui.Scaleform.locale.MENU import MENU
from gui.Scaleform.locale.SYSTEM_MESSAGES import SYSTEM_MESSAGES
from gui.Scaleform.locale.TOOLTIPS import TOOLTIPS
from items import vehicles
from items.vehicles import CAMOUFLAGE_KINDS
from helpers import i18n
from CurrentVehicle import g_currentVehicle
from gui.ClientHangarSpace import _CAMOUFLAGE_MIN_INTENSITY
from gui.Scaleform.framework.entities.DAAPIDataProvider import DAAPIDataProvider
from gui.shared.utils.functions import makeTooltip

class CamouflageGroupsDataProvider(DAAPIDataProvider):

    def __init__(self, nationID):
        super(CamouflageGroupsDataProvider, self).__init__()
        self.__list = []
        self._nationID = nationID

    def buildList(self):
        customization = vehicles.g_cache.customization(self._nationID)
        result = []
        if customization is not None:
            groups = customization.get('camouflageGroups', {})
            for name, info in groups.iteritems():
                result.append({'name': name,
                 'userString': info.get('userString', name),
                 'hasNew': info.get('hasNew', False),
                 'kind': CAMOUFLAGE_KINDS.get(name)})

        self.__list = sorted(result, cmp=self.__comparator)
        return

    def emptyItem(self):
        return {'name': None,
         'userString': '',
         'hasNew': False}

    @property
    def collection(self):
        return self.__list

    def __comparator(self, item, other):
        return cmp(item.get('kind'), other.get('kind'))


class HornsDataProvider(DAAPIDataProvider):

    def __init__(self):
        super(HornsDataProvider, self).__init__()
        self.__vehicleTags = set()
        self.__hornPriceFactor = 1.0
        self.__costs = {}
        self.__list = []

    def buildList(self, currentHornID):
        horns = vehicles.g_cache.horns()
        result = []
        if horns is not None:
            for id, info in horns.iteritems():
                allowedTags = info.get('vehicleTags', set())
                if self.__vehicleTags & allowedTags:
                    result.append({'id': id,
                     'userString': info.get('userString', ''),
                     'gold': self.getCost(id),
                     'current': currentHornID == id})

        self.__list = sorted(result, cmp=lambda item, other: cmp(item.get('userString'), other.get('userString')))
        return

    def emptyItem(self):
        return {'id': None,
         'userString': '',
         'gold': 0,
         'current': False}

    @classmethod
    def _makeCost(cls, defCost, priceFactor):
        return int(round(defCost * priceFactor))

    def getCost(self, hornID):
        return self._makeCost(self.__costs.get(hornID, 0), self.__hornPriceFactor)

    def makeItem(self, hornID, isCurrent):
        horn = vehicles.g_cache.horns().get(hornID, {})
        return {'id': hornID,
         'userString': horn.get('userString', ''),
         'gold': self.getCost(hornID),
         'current': isCurrent}

    def setVehicleTypeParams(self, vehicleTags, hornPriceFactor):
        self.__vehicleTags = vehicleTags
        self.__hornPriceFactor = hornPriceFactor

    def setHornDefCosts(self, costs):
        self.__costs = costs

    @property
    def collection(self):
        return self.__list


class RentalPackageDataProviderBase(DAAPIDataProvider):
    __metaclass__ = ABCMeta
    DEFAULT_RENTAL_PACKAGE_IDX = 0

    def __init__(self, nationID):
        super(RentalPackageDataProviderBase, self).__init__()
        self.__list = []
        self.__selectedPackageIndex = self.DEFAULT_RENTAL_PACKAGE_IDX
        self._eventManager = Event.EventManager()
        self.onDataInited = Event.Event(self._eventManager)
        self.onRentalPackageChange = Event.Event(self._eventManager)
        self.nationID = nationID

    @abstractmethod
    def getRentalPackages(self, refresh = False):
        pass

    def __getSelectedPackageIndex(self):
        return self.__selectedPackageIndex

    def __setSelectedPackageIndex(self, value):
        self.__selectedPackageIndex = value
        self.onRentalPackageChange(self.selectedPackageIndex)

    selectedPackageIndex = property(__getSelectedPackageIndex, __setSelectedPackageIndex)
    selectedPackage = property(lambda self: self.pyRequestItemAt(self.__selectedPackageIndex))

    def getIndexByDays(self, days):
        findIdx = self.DEFAULT_RENTAL_PACKAGE_IDX
        for idx, item in enumerate(self.__list):
            if item.get('periodDays') == days:
                findIdx = idx
                break

        return findIdx

    def emptyItem(self):
        return {'periodDays': -1,
         'cost': -1,
         'isGold': False,
         'userString': ''}

    @property
    def collection(self):
        return self.__list

    def _onGetPackagesCost(self, resultID, costs, _, refresh):
        if resultID < 0:
            SystemMessages.pushI18nMessage(SYSTEM_MESSAGES.CUSTOMIZATION_CAMOUFLAGE_GET_COST_SERVER_ERROR, type=SystemMessages.SM_TYPE.Error)
        else:
            self.buildList(costs)
        self.onDataInited(self.selectedPackage, refresh)

    def buildList(self, costs):
        items = {}
        if costs is not None:
            items = costs.copy()
        result = []
        nations = {}
        if items.has_key('nations'):
            nations = items.get('nations', {})
            del items['nations']
        if nations.has_key(self.nationID):
            items.update(nations.get(self.nationID))
        for periodDays, (cost, isGold) in items.iteritems():
            if periodDays > 1:
                i18nPeriodDays = i18n.makeString(MENU.CUSTOMIZATION_PERIOD_DAYS, periodDays)
            elif periodDays == 1:
                i18nPeriodDays = i18n.makeString(MENU.CUSTOMIZATION_PERIOD_DAY)
            else:
                i18nPeriodDays = i18n.makeString(MENU.CUSTOMIZATION_PERIOD_INFINITY)
            result.append({'periodDays': periodDays,
             'cost': cost,
             'isGold': isGold == 1,
             'userString': i18nPeriodDays})

        self.__list = sorted(result, cmp=self.__comparator, reverse=True)
        return

    def __comparator(self, item, other):
        result = 0
        if item.get('periodDays') and other.get('periodDays'):
            result = cmp(item.get('periodDays'), other.get('periodDays'))
        elif item.get('periodDays') != other.get('periodDays'):
            result = 1 if not item.get('periodDays') else -1
        return result

    def getSelectedPackageIndex(self):
        return self.selectedPackageIndex

    def setSelectedPackageIndex(self, value):
        self.selectedPackageIndex = value


class CamouflageRentalPackageDataProvider(RentalPackageDataProviderBase):

    def getRentalPackages(self, refresh = False):
        BigWorld.player().shop.getCamouflageCost(lambda resultID, costs, rev: self._onGetPackagesCost(resultID, costs, rev, refresh))


class EmblemRentalPackageDataProvider(RentalPackageDataProviderBase):

    def getRentalPackages(self, refresh = False):
        BigWorld.player().shop.getPlayerEmblemCost(lambda resultID, costs, rev: self._onGetPackagesCost(resultID, costs, rev, refresh))


class InscriptionRentalPackageDataProvider(RentalPackageDataProviderBase):

    def getRentalPackages(self, refresh = False):
        BigWorld.player().shop.getPlayerInscriptionCost(lambda resultID, costs, rev: self._onGetPackagesCost(resultID, costs, rev, refresh))


class InscriptionGroupsDataProvider(DAAPIDataProvider):

    def __init__(self, nationID):
        super(InscriptionGroupsDataProvider, self).__init__()
        self.__list = []
        self._nationID = nationID

    def buildList(self):
        customization = vehicles.g_cache.customization(self._nationID)
        result = []
        if customization is not None:
            groups = customization.get('inscriptionGroups', {})
            for name, group in groups.iteritems():
                emblemIDs, showInShop, priceFactor, groupUserString = group
                if showInShop:
                    result.append({'name': name,
                     'userString': groupUserString,
                     'hasNew': False})

        self.__list = sorted(result, cmp=self.__comparator)
        return

    def emptyItem(self):
        return {'name': None,
         'userString': '',
         'hasNew': False}

    @property
    def collection(self):
        return self.__list

    def __comparator(self, item, other):
        return cmp(item.get('name'), other.get('name'))


class EmblemGroupsDataProvider(DAAPIDataProvider):

    def __init__(self):
        super(EmblemGroupsDataProvider, self).__init__()
        self.__list = []

    def buildList(self):
        groups, emblems, names = vehicles.g_cache.playerEmblems()
        result = []
        if groups is not None:
            for name, group in groups.iteritems():
                emblemIDs, showInShop, priceFactor, groupUserString = group
                if showInShop:
                    result.append({'name': name,
                     'userString': groupUserString,
                     'hasNew': False})

        self.__list = sorted(result, cmp=self.__comparator)
        return

    def emptyItem(self):
        return {'name': None,
         'userString': '',
         'hasNew': False}

    @property
    def collection(self):
        return self.__list

    def __comparator(self, item, other):
        return cmp(item.get('name'), other.get('name'))


class EmblemsDataProvider(DAAPIModule):

    def __init__(self):
        DAAPIModule.__init__(self)
        self._defCost = -1.0
        self._isGold = 0
        self._vehPriceFactor = 1.0
        self.currentItemID = None
        return

    @classmethod
    def _makeTextureUrl(cls, width, height, texture, itemSize, coords):
        if texture is None or len(texture) == 0:
            return ''
        else:
            if texture.startswith('gui'):
                texture = texture.replace('gui', '..', 1)
            return texture

    @classmethod
    def _makeSmallTextureUrl(cls, texture, itemSize, coords):
        return EmblemsDataProvider._makeTextureUrl(67, 67, texture, itemSize, coords)

    @classmethod
    def _makeCost(cls, defCost, vehPriceFactor, itemPriceFactor):
        return int(round(defCost * vehPriceFactor * itemPriceFactor))

    @classmethod
    def _makeDescription(cls, groupName, userString):
        result = ''
        if len(groupName) > 0 and len(userString) > 0:
            result = makeTooltip(header=groupName, body=userString)
        return result

    def makeItem(self, itemID, isCurrent, lifeCycle, timeLeftString):
        groups, emblems, names = vehicles.g_cache.playerEmblems()
        itemInfo = None
        if emblems is not None:
            itemInfo = self._constructObject(itemID, groups, emblems, isCurrent)
        if itemInfo is not None:
            itemInfo['timeLeft'] = timeLeftString
        else:
            itemInfo = {'timeLeft': timeLeftString,
             'id': itemID,
             'texturePath': None,
             'description': '',
             'price': {'cost': 0,
                       'isGold': False},
             'current': isCurrent}
        return itemInfo

    def _constructObject(self, itemID, groups, emblems, isCurrent = False, withoutCheck = True):
        itemInfo = None
        emblem = emblems.get(itemID, None)
        if emblem is not None:
            groupName, texture, bumpMap, emblemUserString = emblem
            emblemIDs, showInShop, priceFactor, groupUserString = groups.get(groupName)
            if withoutCheck or showInShop:
                itemInfo = {'id': itemID,
                 'texturePath': self._makeSmallTextureUrl(texture, None, None),
                 'description': self._makeDescription(groupUserString, emblemUserString),
                 'userString': i18n.makeString(emblemUserString),
                 'price': {'cost': self._makeCost(self._defCost, self._vehPriceFactor, priceFactor),
                           'isGold': self._isGold == 1},
                 'current': isCurrent}
        return itemInfo

    def getCost(self, itemID):
        priceFactor = 0
        groups, emblems, names = vehicles.g_cache.playerEmblems()
        emblem = emblems.get(itemID)
        if emblem is not None:
            groupName, texture, bumpFile, emblemUserString = emblem
            emblemIDs, showInShop, priceFactor, groupUserString = groups.get(groupName)
        return (self._makeCost(self._defCost, self._vehPriceFactor, priceFactor), self._isGold)

    def getCostForPackagePrice(self, itemID, packagePrice, isGold):
        return (-1, False)

    def setVehicleTypeParams(self, vehPriceFactor, itemID):
        self._vehPriceFactor = vehPriceFactor
        self.currentItemID = itemID

    def setDefaultCost(self, defCost, isGold):
        self._defCost = defCost
        self._isGold = isGold == 1

    def __comparator(self, item, other):
        return cmp(item['userString'], other['userString'])

    def _populate(self):
        super(EmblemsDataProvider, self)._populate()
        LOG_DEBUG('EmblemsDataProvider _populate')

    def _dispose(self):
        LOG_DEBUG('EmblemsDataProvider _dispose')
        super(EmblemsDataProvider, self)._dispose()

    def onRequestList(self, groupName):
        groups, emblems, names = vehicles.g_cache.playerEmblems()
        group = groups.get(groupName)
        result = []
        if group is not None:
            emblemIDs, showInShop, priceFactor, groupUserString = group
            if showInShop:
                for id in emblemIDs:
                    itemInfo = self._constructObject(id, groups, emblems, self.currentItemID == id, False)
                    if itemInfo is not None:
                        result.append(itemInfo)

        return sorted(result, cmp=self.__comparator)

    def refresh(self):
        self.flashObject.invalidateRemote(True)


class InscriptionDataProvider(EmblemsDataProvider):

    def __init__(self, nationID):
        super(InscriptionDataProvider, self).__init__()
        self.nationID = nationID

    @classmethod
    def _makeSmallTextureUrl(cls, texture, itemSize, coords):
        return EmblemsDataProvider._makeTextureUrl(150, 76, texture, itemSize, coords)

    def makeItem(self, itemID, isCurrent, lifeCycle, timeLeftString):
        customization = vehicles.g_cache.customization(self.nationID)
        itemInfo = None
        if customization is not None:
            groups = customization.get('inscriptionGroups', {})
            inscriptions = customization.get('inscriptions', {})
            if inscriptions is not None:
                itemInfo = self._constructObject(itemID, groups, inscriptions, isCurrent)
            if itemInfo is not None:
                itemInfo['timeLeft'] = timeLeftString
            else:
                itemInfo = {'timeLeft': timeLeftString,
                 'id': itemID,
                 'texturePath': None,
                 'description': '',
                 'price': {'cost': 0,
                           'isGold': False},
                 'current': isCurrent}
        return itemInfo

    def _constructObject(self, itemID, groups, inscriptions, isCurrent = False, withoutCheck = True):
        itemInfo = None
        inscription = inscriptions.get(itemID, None)
        if inscription is not None:
            groupName, texture, bumpMap, inscriptionUserString, isFeatured = inscription
            inscriptionIDs, showInShop, priceFactor, groupUserString = groups.get(groupName)
            if withoutCheck or showInShop:
                itemInfo = {'id': itemID,
                 'texturePath': self._makeSmallTextureUrl(texture, None, None),
                 'description': self._makeDescription(groupUserString, inscriptionUserString),
                 'price': {'cost': self._makeCost(self._defCost, self._vehPriceFactor, priceFactor),
                           'isGold': self._isGold == 1},
                 'current': isCurrent,
                 'isFeatured': isFeatured}
        return itemInfo

    def getCost(self, itemID):
        priceFactor = 0
        customization = vehicles.g_cache.customization(self.nationID)
        if customization is not None:
            groups = customization.get('inscriptionGroups', {})
            inscriptions = customization.get('inscriptions', {})
            inscription = inscriptions.get(itemID)
            if inscription is not None:
                groupName, texture, bumpMap, inscriptionUserString, isFeatured = inscription
                inscriptionIDs, showInShop, priceFactor, groupUserString = groups.get(groupName)
        return (self._makeCost(self._defCost, self._vehPriceFactor, priceFactor), self._isGold)

    def getCostForPackagePrice(self, itemID, packagePrice, isGold):
        return (-1, False)

    def onRequestList(self, groupName):
        customization = vehicles.g_cache.customization(self.nationID)
        result = []
        if customization is not None:
            groups = customization.get('inscriptionGroups', {})
            group = groups.get(groupName, {})
            inscriptions = customization.get('inscriptions', {})
            if group is not None:
                emblemIDs, showInShop, priceFactor, groupUserString = group
                if showInShop:
                    for id in emblemIDs:
                        itemInfo = self._constructObject(id, groups, inscriptions, self.currentItemID == id, False)
                        if itemInfo is not None:
                            result.append(itemInfo)

        return sorted(result, cmp=self.__comparator)

    def __comparator(self, item, other):
        if item['isFeatured'] ^ other['isFeatured']:
            result = -1 if item['isFeatured'] else 1
        else:
            result = cmp(item['id'], other['id'])
        return result


class CamouflagesDataProvider(DAAPIModule):

    def __init__(self, nationID):
        DAAPIModule.__init__(self)
        self.currentGroup = None
        self.__defCost = -1.0
        self.__isGold = 0
        self.__vehPriceFactor = 1.0
        self.currentItemID = None
        self._nationID = nationID
        return

    @classmethod
    def _makeTextureUrl(cls, width, height, texture, colors, armorColor, lifeCycle = None):
        if texture is None or len(texture) == 0:
            return ''
        else:
            weights = Math.Vector4((colors[0] >> 24) / 255.0, (colors[1] >> 24) / 255.0, (colors[2] >> 24) / 255.0, (colors[3] >> 24) / 255.0)
            if lifeCycle is not None:
                startTime, days = lifeCycle
                if days > 0:
                    timeAmount = float((time.time() - startTime) / (days * 86400))
                    if timeAmount > 1.0:
                        weights *= _CAMOUFLAGE_MIN_INTENSITY
                    elif timeAmount > 0:
                        weights *= (1.0 - timeAmount) * (1.0 - _CAMOUFLAGE_MIN_INTENSITY) + _CAMOUFLAGE_MIN_INTENSITY
            return 'img://camouflage,{0:d},{1:d},"{2:>s}",{3[0]:d},{3[1]:d},{3[2]:d},{3[3]:d},{4[0]:n},{4[1]:n},{4[2]:n},{4[3]:n},{5:d}'.format(width, height, texture, colors, weights, armorColor)

    @classmethod
    def _makeSmallTextureUrl(cls, texture, colors, armorColor, lifeCycle = None):
        return CamouflagesDataProvider._makeTextureUrl(67, 67, texture, colors, armorColor, lifeCycle=lifeCycle)

    @classmethod
    def _makeCost(cls, defCost, vehPriceFactor, camPriceFactor):
        return int(round(defCost * vehPriceFactor * camPriceFactor))

    @classmethod
    def _makeDescription(cls, groups, groupName, description):
        if description:
            return groupName or ''
        name = groups.get(groupName, {}).get('userString')
        return makeTooltip(header=name, body=description)

    def getCamouflageDescr(self, camouflageID):
        camouflage = None
        customization = vehicles.g_cache.customization(self._nationID)
        if customization is not None:
            camouflages = customization.get('camouflages', {})
            camouflage = camouflages.get(camouflageID, None)
        return camouflage

    def makeItem(self, camouflageID, isCurrent, lifeCycle, timeLeftString, kind):
        customization = vehicles.g_cache.customization(self._nationID)
        camouflageInfo = None
        if customization is not None:
            groups = customization.get('camouflageGroups', {})
            armorColor = customization.get('armorColor', 0)
            camouflageInfo = self._constructObject(camouflageID, groups, customization.get('camouflages', {}), armorColor, lifeCycle, isCurrent)
        if camouflageInfo is not None:
            camouflageInfo['timeLeft'] = timeLeftString
        else:
            camouflageInfo = {'timeLeft': timeLeftString,
             'id': camouflageID,
             'texturePath': None,
             'description': self.getDefaultDescription(kind),
             'price': {'cost': 0,
                       'isGold': False},
             'isNew': False,
             'invisibilityLbl': '',
             'current': False}
        return camouflageInfo

    def _constructObject(self, cID, groups, camouflages, armorColor, lifeCycle = None, isCurrent = False, withoutCheck = True, currentCompactDescriptor = None):
        camouflageInfo = None
        camouflage = camouflages.get(cID, None)
        if camouflage is not None and (withoutCheck or camouflage.get('showInShop', False)):
            denyCompactDescriptor = camouflage.get('deny')
            if currentCompactDescriptor not in denyCompactDescriptor or currentCompactDescriptor is None:
                invisibilityFactor = camouflage.get('invisibilityFactor', 1)
                invisibilityPercent = int(round((invisibilityFactor - 1) * 100))
                invisibilityLbl = gui.makeHtmlString('html_templates:lobby/customization', 'camouflage-hint', {'percents': invisibilityPercent}, sourceKey=self.__getKindById(camouflage.get('kind', 0)))
                camouflageInfo = {'id': cID,
                 'texturePath': self._makeSmallTextureUrl(camouflage.get('texture'), camouflage.get('colors', (0, 0, 0, 0)), armorColor, lifeCycle=lifeCycle),
                 'description': self._makeDescription(groups, camouflage.get('groupName', ''), camouflage.get('description', '')),
                 'price': {'cost': self._makeCost(self.__defCost, self.__vehPriceFactor, camouflage.get('priceFactor', 1.0)),
                           'isGold': self.__isGold == 1},
                 'isNew': camouflage.get('isNew', False),
                 'invisibilityLbl': invisibilityLbl,
                 'current': isCurrent}
        return camouflageInfo

    def getCost(self, camouflageID):
        camouflage = vehicles.g_cache.customization(self._nationID).get('camouflages', {}).get(camouflageID, {})
        return (self._makeCost(self.__defCost, self.__vehPriceFactor, camouflage.get('priceFactor', 1.0)), self.__isGold)

    def getCostForPackagePrice(self, camouflageID, packagePrice, isGold):
        camouflage = vehicles.g_cache.customization(self._nationID).get('camouflages', {}).get(camouflageID, {})
        return (self._makeCost(packagePrice, self.__vehPriceFactor, camouflage.get('priceFactor', 1.0)), isGold)

    def setVehicleTypeParams(self, vehPriceFactor, camouflageID):
        self.__vehPriceFactor = vehPriceFactor
        self.currentItemID = camouflageID

    def setDefaultCost(self, defCost, isGold):
        self.__defCost = defCost
        self.__isGold = isGold == 1

    def __comparator(self, item, other):
        if item['isNew'] ^ other['isNew']:
            result = -1 if item['isNew'] else 1
        else:
            result = cmp(item['id'], other['id'])
        return result

    def __getKindById(self, kindId):
        kind = 'winter'
        for k, v in CAMOUFLAGE_KINDS.iteritems():
            if v == kindId:
                kind = k

        return kind

    def _populate(self):
        super(CamouflagesDataProvider, self)._populate()
        LOG_DEBUG('CamouflagesDataProvider _populate')

    def _dispose(self):
        LOG_DEBUG('CamouflagesDataProvider _dispose')
        super(CamouflagesDataProvider, self)._dispose()

    def getDefaultHintText(self, _):
        return gui.makeHtmlString('html_templates:lobby/customization', 'camouflage-hint', sourceKey='default')

    def getDefaultDescription(self, kindID):
        kindKey = '#tooltips:customization/camouflage/{0:>s}'.format(self.__getKindById(kindID))
        bodyKey = TOOLTIPS.CUSTOMIZATION_CAMOUFLAGE_EMPTY
        return makeTooltip(body=i18n.makeString(bodyKey, kind=i18n.makeString(kindKey)))

    def setGroupCurrentItemId(self, itemId):
        self.currentItemID = int(itemId) if itemId is not None else None
        return

    def onRequestList(self, groupName):
        self.currentGroup = groupName
        customization = vehicles.g_cache.customization(self._nationID)
        result = []
        if customization is not None:
            groups = customization.get('camouflageGroups', {})
            group = groups.get(groupName, {})
            camouflages = customization.get('camouflages', {})
            armorColor = customization.get('armorColor', 0)
            ids = group.get('ids', [])
            currCmpctDescr = g_currentVehicle.item.intCD
            for id in ids:
                camouflageInfo = self._constructObject(id, groups, camouflages, armorColor, isCurrent=self.currentItemID == id, withoutCheck=False, currentCompactDescriptor=currCmpctDescr)
                if camouflageInfo is not None:
                    result.append(camouflageInfo)

        return sorted(result, cmp=self.__comparator)

    def refresh(self):
        self.flashObject.invalidateRemote(True)
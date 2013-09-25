import BigWorld
import Account
import items
import Math
import BattleReplay
from helpers import isPlayerAvatar
from debug_utils import *

class VehicleStickers:

    def __init__(self, vDesc, emblemSlots, onHull = True, prereqs = None):
        self.__slotsByType = {}
        self.__texParamsBySlotType = {}
        self.__isLoadingClanEmblems = False
        self.__clanID = 0
        self.__model = None
        self.__parentNode = None
        self.__isDamaged = False
        g_cache = items.vehicles.g_cache
        self.__calcTexParams(vDesc, emblemSlots, onHull, prereqs)
        if 'clan' in self.__texParamsBySlotType:
            self.__texParamsBySlotType['clan'] = [('', '')]
        self.__stickerModel = BigWorld.WGStickerModel()
        self.__stickerModel.setLODDistances(vDesc.type.emblemsLodDist, vDesc.type.damageStickersLodDist)
        return

    def __calcTexParams(self, vDesc, emblemSlots, onHull, prereqs):
        g_cache = items.vehicles.g_cache
        customizationCache = g_cache.customization(vDesc.type.id[0])
        playerEmblemsCache = g_cache.playerEmblems()
        inscriptionsCache = (customizationCache['inscriptionGroups'], customizationCache['inscriptions'])
        for slot in emblemSlots:
            slotType = slot[5]
            if self.__slotsByType.has_key(slotType):
                self.__slotsByType[slotType].append(slot)
            else:
                self.__slotsByType[slotType] = [slot]
            if slotType not in self.__texParamsBySlotType:
                self.__texParamsBySlotType[slotType] = []
            emblemsDesc = None
            emblemsCache = None
            if slotType == 'player':
                emblemsDesc = vDesc.playerEmblems[0:2] if onHull else vDesc.playerEmblems[2:]
                emblemsCache = playerEmblemsCache
            elif slotType == 'inscription':
                emblemsDesc = vDesc.playerInscriptions[0:2] if onHull else vDesc.playerInscriptions[2:]
                emblemsCache = inscriptionsCache
            if emblemsDesc is None:
                texParams = (0, '', '')
                self.__texParamsBySlotType[slotType] = [texParams]
                continue
            descIdx = len(self.__slotsByType[slotType]) - 1
            emblemID = emblemsDesc[descIdx][0]
            if emblemID is None:
                self.__texParamsBySlotType[slotType].append(None)
                continue
            texName, bumpTexName = emblemsCache[1][emblemID][1:3]
            texParams = (texName, bumpTexName)
            self.__texParamsBySlotType[slotType].append(texParams)

        return

    def __destroy__(self):
        self.__isLoadingClanEmblems = False
        self.detachStickers()

    def attachStickers(self, model, parentNode, isDamaged):
        self.detachStickers()
        self.__model = model
        self.__parentNode = parentNode
        self.__isDamaged = isDamaged
        self.__parentNode.attach(self.__stickerModel)
        replayCtrl = BattleReplay.g_replayCtrl
        for slotType, slots in self.__slotsByType.iteritems():
            if slotType != 'clan' or self.__clanID == 0 or replayCtrl.isPlaying and replayCtrl.isOffline:
                self.__doAttachStickers(slotType)
            elif slotType == 'clan':
                if self.__isLoadingClanEmblems:
                    continue
                self.__isLoadingClanEmblems = True
                fileCache = Account.g_accountRepository.customFilesCache
                fileServerSettings = Account.g_accountRepository.fileServerSettings
                clan_emblems = fileServerSettings.get('clan_emblems')
                if clan_emblems is None:
                    continue
                url = None
                try:
                    url = clan_emblems['url_template'] % self.__clanID
                except:
                    LOG_ERROR('Failed to attach stickers to the vehicle - server returned incorrect url format: %s' % clan_emblems['url_template'])
                    continue

                fileCache.get(url, self.__onClanEmblemLoaded)

        return

    def detachStickers(self):
        if self.__model is None:
            return
        else:
            self.__parentNode.detach(self.__stickerModel)
            self.__stickerModel.clear()
            self.__model = None
            self.__parentNode = None
            self.__isDamaged = False
            return

    def addDamageSticker(self, texName, bumpTexName, segStart, segEnd, sizes, rayUp):
        if self.__model is None:
            return 0
        else:
            return self.__stickerModel.addSticker(texName, bumpTexName, self.__model, segStart, segEnd, sizes, rayUp, False)

    def delDamageSticker(self, handle):
        if self.__model is not None:
            self.__stickerModel.delSticker(handle)
        return

    def setClanID(self, clanID):
        if self.__clanID == clanID:
            return
        else:
            self.__clanID = clanID
            if self.__model is not None:
                self.attachStickers(self.__model, self.__parentNode, self.__isDamaged)
            return

    def setAlphas(self, emblemAlpha, dmgStickerAlpha):
        self.__stickerModel.setAlphas(emblemAlpha, dmgStickerAlpha)

    def __doAttachStickers(self, slotType):
        if self.__model is None or slotType == 'clan' and self.__clanID == 0:
            return
        else:
            slots = self.__slotsByType[slotType]
            for idx, (rayStart, rayEnd, rayUp, size, hideIfDamaged, _) in enumerate(slots):
                if hideIfDamaged and self.__isDamaged or self.__texParamsBySlotType[slotType][idx] is None:
                    continue
                texName, bumpTexName = self.__texParamsBySlotType[slotType][idx]
                sizes = Math.Vector2(size, size)
                isInscription = slotType == 'inscription'
                if isInscription:
                    sizes.y *= 0.5
                self.__stickerModel.addSticker(texName, bumpTexName, self.__model, rayStart, rayEnd, sizes, rayUp, isInscription)

            return

    def __onClanEmblemLoaded(self, url, data):
        if not self.__isLoadingClanEmblems:
            return
        else:
            self.__isLoadingClanEmblems = False
            if data is None:
                return
            try:
                texName, bumpTexName = self.__texParamsBySlotType['clan'][0]
                self.__stickerModel.setTextureData(data)
                self.__doAttachStickers('clan')
            except Exception:
                LOG_CURRENT_EXCEPTION()

            return

import Event
from debug_utils import *
from helpers import i18n, getClientLanguage
from account_helpers.rare_achievements import getRareAchievementImage, getRareAchievementText

class _RaresCache(object):
    DEFAULT_TITLE = i18n.makeString('#tooltips:achievement/action/unavailable/title')
    DEFAULT_DESCR = i18n.makeString('#tooltips:achievement/action/unavailable/descr')

    def __init__(self):
        self.__cache = dict()
        self.onTextReceived = Event.Event()
        self.onImageReceived = Event.Event()

    def request(self, listOfIds):
        LOG_DEBUG('Request action achievements data')
        if not len(listOfIds):
            return
        landId = getClientLanguage()
        for achieveId in listOfIds:
            getRareAchievementText(landId, achieveId, self.__onTextReceived)
            getRareAchievementImage(achieveId, self.__onImageReceived)

    def __onTextReceived(self, id, text):
        achieveData = self.__cache.setdefault(id, dict())
        title = text.get('title')
        descr = text.get('description')
        LOG_DEBUG('Text received for achievement: %d; title: %s; descr: %s' % (id, type(title), type(descr)))
        if not (descr is not None and ('descr' not in achieveData or achieveData['descr'] != descr)):
            if title is not None:
                if not 'title' not in achieveData:
                    isGenerateEvent = achieveData['title'] != title
                    achieveData['descr'] = descr is not None and text.get('description')
                achieveData['title'] = title is not None and title
            isGenerateEvent and self.onTextReceived(id, achieveData['title'], achieveData['descr'])
        return

    def __onImageReceived(self, id, imageData):
        achieveData = self.__cache.setdefault(id, dict())
        LOG_DEBUG('Image received for achievement: %d %s' % (id, type(imageData)))
        if imageData is None:
            return
        else:
            if not 'image' not in achieveData:
                isGenerateEvent = achieveData['image'] != imageData
                achieveData['image'] = imageData
                isGenerateEvent and self.onImageReceived(id, imageData)
            return

    def getTitle(self, id):
        return self.__cache.get(id, dict()).get('title') or _RaresCache.DEFAULT_TITLE

    def getDescription(self, id):
        return self.__cache.get(id, dict()).get('descr') or _RaresCache.DEFAULT_DESCR

    def getImageData(self, id):
        return self.__cache.get(id, dict()).get('image')


g_rareAchievesCache = _RaresCache()

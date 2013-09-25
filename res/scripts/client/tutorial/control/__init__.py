from abc import ABCMeta, abstractmethod
from helpers.aop import Weaver
from tutorial.logger import LOG_ERROR
from tutorial.data.chapter import EFFECT_TYPE_NAMES

class TutorialProxyHolder(object):
    _tutorial = None

    @property
    def _gui(self):
        return self._tutorial._gui

    @property
    def _data(self):
        return self._tutorial._data

    @property
    def _cache(self):
        return self._tutorial._cache

    @property
    def _bonuses(self):
        return self._tutorial._bonuses

    @property
    def _sound(self):
        return self._tutorial._sound


def setTutorialProxy(tutorial):
    TutorialProxyHolder._tutorial = tutorial


def clearTutorialProxy():
    TutorialProxyHolder._tutorial = None
    return


class ContentQuery(TutorialProxyHolder):

    def invoke(self, content, varID):
        pass

    def getVar(self, varID, default = None):
        return self._tutorial.getVars().get(varID, default=default)


class ControlsFactory:
    __meta__ = ABCMeta

    def __init__(self, funcEffects, contentQueries):
        self._funcEffects = funcEffects
        self._contentQueries = contentQueries

    @abstractmethod
    def createBonuses(self, completed):
        pass

    @abstractmethod
    def createSoundPlayer(self):
        pass

    @abstractmethod
    def createFuncScene(self, sceneModel):
        pass

    @abstractmethod
    def createFuncInfo(self):
        pass

    def createContentQuery(self, name):
        result = ContentQuery()
        if name in self._contentQueries:
            result = self._contentQueries[name]()
        else:
            LOG_ERROR('Not found ContentQuery class by name:', name)
        return result

    def createFuncEffect(self, effect):
        if effect is None:
            return
        else:
            effectType = effect.getType()
            funcEffect = None
            if effectType in self._funcEffects:
                funcEffect = self._funcEffects[effectType](effect)
            else:
                LOG_ERROR('Not found FunctionalEffect class by effect type:', EFFECT_TYPE_NAMES.get(effectType, effectType))
            return funcEffect

    def createFuncEffects(self, effects):
        return filter(lambda item: item is not None, map(self.createFuncEffect, effects))


g_tutorialWeaver = Weaver()

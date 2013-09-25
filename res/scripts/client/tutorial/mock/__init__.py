# Embedded file name: scripts/client/tutorial/mock/__init__.py
from tutorial import loader, doc_loader, logger, GlobalStorage
from tutorial.control.states import TutorialStateRunEffects
from tutorial.data import chapter
from tutorial.logger import LOG_DEBUG
from tutorial.mock import battle, offbattle
__all__ = ['reloadChapter',
 'getFlags',
 'getVars',
 'getGS',
 'playTargetedEffect',
 'stopCurrentEffect',
 'showDialog',
 'showWindow',
 'battle',
 'offbattle']

def reloadChapter(ab = False, clear = False):
    instance = loader.g_loader.tutorial
    if instance and not instance._tutorialStopped:
        instance._funcScene.reload()
        instance._sound.stop()
        if clear:
            instance._cache.clearChapterData()
        instance._cache.setAfterBattle(ab).write()
        instance._gui.reloadConfig(instance._descriptor.getGuiFilePath())
        instance._gui.clear()
        doc_loader.clearChapterData(instance._data)
        instance.loadCurrentChapter(initial=True)
    else:
        LOG_DEBUG('Tutorial is not running.')


def getFlags():
    return loader.g_loader.tutorial.getFlags()


def getVars():
    return loader.g_loader.tutorial.getVars()


def getGS():
    return GlobalStorage.all()


def setLogLevel(level):
    logger.CURRENT_LOG_LEVEL = level


def playTargetedEffect(targetID, effectType):
    instance = loader.g_loader.tutorial
    if instance and not instance._tutorialStopped:
        instance.storeEffectsInQueue([chapter.HasTargetEffect(targetID, effectType)], benefit=True)
    else:
        LOG_DEBUG('Tutorial is not running.')


def stopCurrentEffect():
    instance = loader.g_loader.tutorial
    if instance and not instance._tutorialStopped:
        if isinstance(instance._currentState, TutorialStateRunEffects) and instance._currentState._current is not None:
            instance._currentState._current.stop()
    else:
        LOG_DEBUG('Tutorial is not running.')
    return


def showDialog(targetID):
    stopCurrentEffect()
    playTargetedEffect(targetID, chapter.Effect.SHOW_DIALOG)


def showWindow(windowID):
    playTargetedEffect(windowID, chapter.Effect.SHOW_WINDOW)
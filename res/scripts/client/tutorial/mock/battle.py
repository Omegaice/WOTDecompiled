import BigWorld
from tutorial import loader, doc_loader
from tutorial.control.battle.context import BattleClientCtx
from tutorial.logger import LOG_DEBUG
from tutorial.settings import TUTORIAL_SETTINGS
__all__ = ['join', 'getCtx', 'setCompleted']
_chapters = {'vc': ('VehicleControl', {'TeleportToPoint1': True}),
 'db1': ('DestroyBot1', {'TeleportToPoint4': True}),
 'db2': ('DestroyBot2', {'TeleportToPoint5': True}),
 'db3': ('DestroyBot3', {'TeleportToPoint8': True})}

def join(short = None):
    instance = loader.g_loader.tutorial
    if instance is None or instance._tutorialStopped:
        from tutorial.TutorialCache import TutorialCache
        cache = TutorialCache(BigWorld.player().name, TUTORIAL_SETTINGS.BATTLE.space)
        cache.setRefused(False).write()
        if short is not None:
            if short not in _chapters.keys():
                LOG_DEBUG('Chapter not found. Available shot names of chapters are', _chapters.keys())
                return
            chapter, flags = _chapters[short]
            cache.update(chapter, flags)
        else:
            cache.clear()
        BigWorld.player().enqueueTutorial()
    else:
        LOG_DEBUG('Tutorial is running.')
    return


def getCtx():
    return BattleClientCtx.fetch()


def setCompleted(exclude = None):
    instance = loader.g_loader.tutorial
    if exclude is None:
        exclude = []
    if instance is not None and not instance._tutorialStopped:
        descriptor = doc_loader.loadDescriptorData(TUTORIAL_SETTINGS.BATTLE.descriptorPath)
        if descriptor is not None:
            clientCtx = BattleClientCtx.fetch()
            for idx, chapter in enumerate(descriptor):
                if chapter.hasBonus() and idx not in exclude:
                    clientCtx = clientCtx.addMask(1 << chapter.getBonusID())

            clientCtx.setChapterIdx(descriptor.getNumberOfChapters() - 1)
            arena = getattr(BigWorld.player(), 'arena', None)
            if arena is not None:
                BigWorld.player().leaveArena()
        else:
            LOG_DEBUG('Tutorial descriptor is invalid.')
    else:
        LOG_DEBUG('Tutorial is not running.')
    return

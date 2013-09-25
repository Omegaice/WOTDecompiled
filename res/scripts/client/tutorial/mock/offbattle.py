# Embedded file name: scripts/client/tutorial/mock/offbattle.py
import time
from constants import FINISH_REASON
from tutorial import doc_loader, loader
from tutorial.control.battle.context import ExtendedBattleClientCtx
from tutorial.control.offbattle import queries
from tutorial.control.offbattle.context import OffBattleClientCtx
from tutorial.control.offbattle.functional import ContentChangedEvent
from tutorial.logger import LOG_DEBUG
from tutorial.settings import TUTORIAL_SETTINGS
__all__ = ['changeContent', 'showStats', 'getCtx']

def changeContent(targetID, value):
    ContentChangedEvent(targetID).fire(value)


def showStats(exclude = None, destroyed = False, subtitle = None, audio = None):
    instance = loader.g_loader.tutorial
    if exclude is None:
        exclude = []
    if instance is not None and not instance._tutorialStopped:
        descriptor = doc_loader.loadDescriptorData(TUTORIAL_SETTINGS.BATTLE.descriptorPath)
        if descriptor is not None:
            completed = 0
            chapterIdx = -1
            for idx, chapter in enumerate(descriptor):
                if chapter.hasBonus() and idx not in exclude:
                    completed |= 1 << chapter.getBonusID()
                    chapterIdx = idx

            winTeam = 1
            reason = 0
            if len(exclude):
                winTeam = 2
                if destroyed:
                    reason = FINISH_REASON.EXTERMINATION
                else:
                    reason = FINISH_REASON.TIMEOUT
            instance._cache.setLocalCtx(ExtendedBattleClientCtx(completed, -1, -1, time.time(), chapterIdx, 1, winTeam, reason, 56321, 53, long(time.time())).makeRecord())
            MockVideoContent.subtitleTrack = subtitle
            MockVideoContent.audioTrack = audio
            instance._ctrlFactory._contentQueries['video'] = MockVideoContent
            from tutorial.mock import reloadChapter
            reloadChapter(ab=True)
        else:
            LOG_DEBUG('Tutorial descriptor is invalid.')
    else:
        LOG_DEBUG('Tutorial is not running.')
    return


class MockVideoContent(queries.VideoContent):
    subtitleTrack = None
    audioTrack = None

    def invoke(self, content, varID):
        super(MockVideoContent, self).invoke(content, varID)
        LOG_DEBUG('Custom value of subtitle track', self.subtitleTrack)
        if self.subtitleTrack is not None:
            content['subtitleTrack'] = self.subtitleTrack
        LOG_DEBUG('Custom value of audio track', self.audioTrack)
        if self.subtitleTrack is not None:
            content['audioTrack'] = self.audioTrack
        return


def getCtx():
    instance = loader.g_loader.tutorial
    ctx = None
    if instance is not None and not instance._tutorialStopped:
        ctx = OffBattleClientCtx.fetch(instance._cache)
    else:
        LOG_DEBUG('Tutorial is not running.')
    return ctx
import BigWorld
from AccountCommands import RES_SUCCESS
from constants import FINISH_REASON, IS_TUTORIAL_ENABLED
import dossiers
from tutorial import doc_loader
from tutorial.control import context
from tutorial.control.battle.context import ExtendedBattleClientCtx
from tutorial.control.context import GlobalStorage, GLOBAL_FLAG, GLOBAL_VAR
from tutorial.control.lobby.context import LobbyBonusesRequester
from tutorial.logger import LOG_ERROR
from tutorial.settings import TUTORIAL_SETTINGS, PLAYER_XP_LEVEL

class OffBattleClientCtx(ExtendedBattleClientCtx):

    @classmethod
    def fetch(cls, cache):
        return cls.makeCtx(cache.getLocalCtx())


def _getBattleDescriptor():
    return doc_loader.loadDescriptorData(TUTORIAL_SETTINGS.BATTLE.descriptorPath)


class OffbattleStartReqs(context.StartReqs):

    def isEnabled(self):
        isTutorialEnabled = IS_TUTORIAL_ENABLED
        player = BigWorld.player()
        if player is not None:
            serverSettings = getattr(player, 'serverSettings', {})
            if 'isTutorialEnabled' in serverSettings:
                isTutorialEnabled = serverSettings['isTutorialEnabled']
        return (not self._ctx.cache.isFinished() or self._ctx.restart) and isTutorialEnabled

    def process(self):
        BigWorld.player().stats.get('tutorialsCompleted', self.__cb_onGetTutorialsCompleted)

    def __cb_onGetTutorialsCompleted(self, resultID, completed):
        ctx = self._ctx
        loader = self._loader
        tutorial = loader.tutorial
        if resultID < RES_SUCCESS:
            LOG_ERROR('Server return error on request tutorialsCompleted', resultID, completed)
            loader._clear()
            self._clear()
            return
        else:
            ctx.bonusCompleted = completed
            cache = ctx.cache
            battleDesc = _getBattleDescriptor()
            if battleDesc is None:
                LOG_ERROR('Battle tutorial is not defined.')
                loader._clear()
                self._clear()
                return
            finishReason = OffBattleClientCtx.fetch(cache).finishReason
            isHistory = GlobalStorage(GLOBAL_FLAG.SHOW_HISTORY, False).value()
            if isHistory or not cache.isRefused() and loader.isAfterBattle and finishReason not in [-1, FINISH_REASON.FAILURE]:
                cache.setAfterBattle(True)
            else:
                cache.setAfterBattle(False)
            if not battleDesc.areAllBonusesReceived(completed):
                if cache.getPlayerXPLevel() == PLAYER_XP_LEVEL.NEWBIE:
                    BigWorld.player().stats.get('dossier', self.__cb_onGetDossier)
                else:
                    self._clear()
                    self._resolveTutorialState(loader, ctx)
            else:
                cache.setPlayerXPLevel(PLAYER_XP_LEVEL.NORMAL)
                self._clear()
                self._resolveTutorialState(loader, ctx)
            return

    def __cb_onGetDossier(self, resultID, dossierCD):
        loader, ctx = self._flush()
        cache = ctx.cache
        tutorial = loader.tutorial
        if resultID < RES_SUCCESS:
            LOG_ERROR('Server return error on request dossier', resultID, dossierCD)
            loader._clear()
            return
        else:
            dossierDescr = dossiers.getAccountDossierDescr(dossierCD)
            battlesCount = dossierDescr['battlesCount']
            threshold = BigWorld.player().serverSettings.get('newbieBattlesCount', 0)
            if dossierDescr['battlesCount'] < threshold:
                descriptor = tutorial._descriptor
                chapter = descriptor.getChapter(descriptor.getInitialChapterID())
                if not chapter is None:
                    isShowGreeting = not chapter.isBonusReceived(ctx.bonusCompleted)
                    (chapter is None or not chapter.isBonusReceived(ctx.bonusCompleted)) and loader._doRun(ctx)
                else:
                    self._resolveTutorialState(loader, ctx)
            else:
                cache.setPlayerXPLevel(PLAYER_XP_LEVEL.NORMAL)
                self._resolveTutorialState(loader, ctx)
            return

    def _resolveTutorialState(self, loader, ctx):
        cache = ctx.cache
        tutorial = loader.tutorial
        if cache.isRefused():
            if ctx.restart and not ctx.isInPrebattle:
                tutorial.restart(ctx)
            else:
                tutorial.pause(ctx)
            return
        if cache.isAfterBattle():
            loader._doRun(ctx)
        else:
            tutorial.pause(ctx)
            cache.setRefused(True).write()


class OffbattleBonusesRequester(LobbyBonusesRequester):

    def __init__(self, completed, chapter = None):
        super(OffbattleBonusesRequester, self).__init__(completed)
        self.__chapter = chapter

    def getChapter(self, chapterID = None):
        if self.__chapter is not None:
            return self.__chapter
        else:
            return self._data

import ArenaType
from adisp import process
from gui.Scaleform.daapi.view.lobby.trainings import formatters
from gui.prb_control.dispatcher import g_prbLoader
from gui.prb_control.context import TrainingSettingsCtx
from debug_utils import LOG_ERROR, LOG_CURRENT_EXCEPTION
from gui.Scaleform.framework.entities.View import View
from gui.Scaleform.daapi.view.meta.WindowViewMeta import WindowViewMeta
from gui.Scaleform.daapi.view.meta.TrainingWindowMeta import TrainingWindowMeta
from gui.prb_control.settings import PREBATTLE_REQUEST
from helpers import i18n

class ArenasCache(object):

    def __init__(self):
        self.__cache = []
        for arenaTypeID, arenaType in ArenaType.g_cache.iteritems():
            if arenaType.explicitRequestOnly:
                continue
            try:
                nameSuffix = '' if arenaType.gameplayName == 'ctf' else i18n.makeString('#arenas:type/%s/name' % arenaType.gameplayName)
                self.__cache.append({'label': '%s - %s' % (arenaType.name, nameSuffix) if len(nameSuffix) else arenaType.name,
                 'name': arenaType.name,
                 'arenaType': nameSuffix,
                 'key': arenaTypeID,
                 'size': arenaType.maxPlayersInTeam,
                 'time': arenaType.roundLength / 60,
                 'description': '',
                 'icon': formatters.getMapIconPath(arenaType)})
            except Exception:
                LOG_ERROR('There is error while reading arenas cache', arenaTypeID, arenaType)
                LOG_CURRENT_EXCEPTION()
                continue

        self.__cache = sorted(self.__cache, key=lambda x: (x['label'].lower(), x['name'].lower()))

    @property
    def cache(self):
        return self.__cache


class TrainingSettingsWindow(View, WindowViewMeta, TrainingWindowMeta):

    def __init__(self, ctx):
        super(TrainingSettingsWindow, self).__init__()
        self.__settingsCtx = ctx.get('settings', TrainingSettingsCtx())
        self.__arenasCache = ArenasCache()

    @process
    def __createTrainingRoom(self):
        self.__settingsCtx.setWaitingID('prebattle/create')
        yield g_prbLoader.getDispatcher().create(self.__settingsCtx)

    @process
    def __changeTrainingRoom(self):
        self.__settingsCtx.setWaitingID('prebattle/change_settings')
        yield g_prbLoader.getDispatcher().sendPrbRequest(self.__settingsCtx)

    def onWindowClose(self):
        if self.__settingsCtx is not None:
            self.__settingsCtx.clear()
            self.__settingsCtx = None
        self.destroy()
        return

    def getMapsData(self):
        return self.__arenasCache.cache

    def getInfo(self):
        return {'description': self.__settingsCtx.getComment(),
         'timeout': self.__settingsCtx.getRoundLen() / 60,
         'arena': self.__settingsCtx.getArenaTypeID(),
         'privacy': not self.__settingsCtx.isOpened(),
         'create': self.__settingsCtx.getRequestType() is PREBATTLE_REQUEST.CREATE}

    def updateTrainingRoom(self, arena, roundLength, isPrivate, comment):
        self.__settingsCtx.setArenaTypeID(arena)
        self.__settingsCtx.setRoundLen(roundLength * 60)
        self.__settingsCtx.setOpened(not isPrivate)
        self.__settingsCtx.setComment(comment)
        if self.__settingsCtx.getRequestType() is PREBATTLE_REQUEST.CREATE:
            self.__createTrainingRoom()
        else:
            self.__changeTrainingRoom()

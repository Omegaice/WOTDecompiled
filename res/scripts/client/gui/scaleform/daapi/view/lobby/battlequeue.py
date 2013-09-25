# Embedded file name: scripts/client/gui/Scaleform/daapi/view/lobby/BattleQueue.py
import BigWorld, constants, MusicController
from gui import prb_control
from gui.Scaleform.daapi.settings.views import VIEW_ALIAS
from gui.Scaleform.framework import VIEW_TYPE
from gui.Scaleform.framework.managers.containers import POP_UP_CRITERIA
from gui.shared import events
from gui.shared.event_bus import EVENT_BUS_SCOPE
from helpers.i18n import makeString
from PlayerEvents import g_playerEvents
from gui.prb_control.dispatcher import g_prbLoader
from gui.Scaleform.daapi import LobbySubView
from gui.Scaleform.daapi.view.meta.BattleQueueMeta import BattleQueueMeta

class BattleQueue(BattleQueueMeta, LobbySubView):
    TYPES_ORDERED = (('heavyTank', '#item_types:vehicle/tags/heavy_tank/name'),
     ('mediumTank', '#item_types:vehicle/tags/medium_tank/name'),
     ('lightTank', '#item_types:vehicle/tags/light_tank/name'),
     ('AT-SPG', '#item_types:vehicle/tags/at-spg/name'),
     ('SPG', '#item_types:vehicle/tags/spg/name'))
    DIVISIONS_ORDERED = (constants.PREBATTLE_COMPANY_DIVISION.JUNIOR,
     constants.PREBATTLE_COMPANY_DIVISION.MIDDLE,
     constants.PREBATTLE_COMPANY_DIVISION.CHAMPION,
     constants.PREBATTLE_COMPANY_DIVISION.ABSOLUTE)

    def __init__(self):
        super(BattleQueue, self).__init__()
        self.createTime = 0
        self.__timerCallback = None
        self.__queueCallback = None
        self.__inited = False
        return

    def _populate(self):
        super(BattleQueue, self)._populate()
        g_playerEvents.onQueueInfoReceived += self.onQueueInfoReceived
        g_playerEvents.onArenaCreated += self.onStartBattle
        self.__updateQueueInfo()
        self.__updateTimer()
        self.__updateClientState()
        MusicController.g_musicController.play(MusicController.MUSIC_EVENT_LOBBY)
        MusicController.g_musicController.play(MusicController.AMBIENT_EVENT_LOBBY)

    def _dispose(self):
        self.__stopUpdateScreen()
        g_playerEvents.onQueueInfoReceived -= self.onQueueInfoReceived
        g_playerEvents.onArenaCreated -= self.onStartBattle
        super(BattleQueue, self)._dispose()

    def __updateClientState(self):
        dispatcher = g_prbLoader.getDispatcher()
        if dispatcher is not None:
            permissions = dispatcher.getPrbFunctional().getPermissions()
            if permissions and not permissions.canExitFromRandomQueue():
                self.flashObject.as_showExit(False)
        self.flashObject.as_setType(prb_control.getArenaGUIType())
        return

    def onEscape(self):
        dialogsContainer = self.app.containerManager.getContainer(VIEW_TYPE.DIALOG)
        if not dialogsContainer.getView(criteria={POP_UP_CRITERIA.VIEW_ALIAS: VIEW_ALIAS.LOBBY_MENU}):
            self.fireEvent(events.ShowViewEvent(events.ShowViewEvent.SHOW_LOBBY_MENU), scope=EVENT_BUS_SCOPE.LOBBY)

    def startClick(self):
        currPlayer = BigWorld.player()
        if currPlayer is not None and hasattr(currPlayer, 'createArenaFromQueue'):
            currPlayer.createArenaFromQueue()
        return

    def exitClick(self):
        dispatcher = g_prbLoader.getDispatcher()
        if dispatcher is not None:
            dispatcher.exitFromRandomQueue()
        return

    def onQueueInfoReceived(self, randomsQueueInfo, companiesQueueInfo):
        if prb_control.isCompany():
            data = {'title': '#menu:prebattle/typesCompaniesTitle',
             'data': list()}
            self.flashObject.as_setPlayers(makeString('#menu:prebattle/groupsLabel'), sum(companiesQueueInfo['divisions']))
            vDivisions = companiesQueueInfo['divisions']
            if vDivisions is not None:
                vClassesLen = len(vDivisions)
                for vDivision in BattleQueue.DIVISIONS_ORDERED:
                    data['data'].append(('#menu:prebattle/CompaniesTitle/%s' % constants.PREBATTLE_COMPANY_DIVISION_NAMES[vDivision], vDivisions[vDivision] if vDivision < vClassesLen else 0))

                self.flashObject.as_setListByType(data)
            self.flashObject.as_showStart(constants.IS_DEVELOPMENT)
        else:
            self.flashObject.as_setPlayers(makeString('#menu:prebattle/playersLabel'), sum(randomsQueueInfo['levels']))
            vehLevels = randomsQueueInfo['levels']
            vehLevels = vehLevels[:] if vehLevels is not None else []
            vehLevels.reverse()
            data = {'title': '#menu:prebattle/levelsTitle',
             'data': vehLevels[:-1]}
            self.flashObject.as_setListByLevel(data)
            vClasses = randomsQueueInfo['classes']
            if vClasses is not None:
                data = {'title': '#menu:prebattle/typesTitle',
                 'data': list()}
                vClassesLen = len(vClasses)
                for vClass, message in BattleQueue.TYPES_ORDERED:
                    idx = constants.VEHICLE_CLASS_INDICES[vClass]
                    data['data'].append((message, vClasses[idx] if idx < vClassesLen else 0))

                self.flashObject.as_setListByType(data)
            self.flashObject.as_showStart(constants.IS_DEVELOPMENT and sum(randomsQueueInfo['levels']) > 1)
        if not self.__inited:
            self.__inited = True
        return

    def onStartBattle(self):
        self.__stopUpdateScreen()

    def __stopUpdateScreen(self):
        if self.__timerCallback is not None:
            BigWorld.cancelCallback(self.__timerCallback)
            self.__timerCallback = None
        if self.__queueCallback is not None:
            BigWorld.cancelCallback(self.__queueCallback)
            self.__queueCallback = None
        return

    def __updateQueueInfo(self):
        self.__queueCallback = None
        currPlayer = BigWorld.player()
        if currPlayer is not None and hasattr(currPlayer, 'requestQueueInfo'):
            if prb_control.isCompany():
                qType = constants.QUEUE_TYPE.COMPANIES
            else:
                qType = constants.QUEUE_TYPE.RANDOMS
            currPlayer.requestQueueInfo(qType)
            self.__queueCallback = BigWorld.callback(5, self.__updateQueueInfo)
        return

    def __updateTimer(self):
        self.__timerCallback = None
        self.__timerCallback = BigWorld.callback(1, self.__updateTimer)
        textLabel = makeString('#menu:prebattle/timerLabel')
        timeLabel = '%d:%02d' % divmod(self.createTime, 60)
        self.flashObject.as_setTimer(textLabel, timeLabel)
        self.createTime += 1
        return
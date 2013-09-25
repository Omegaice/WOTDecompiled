# Embedded file name: scripts/client/notification/LayoutController.py
from gui.Scaleform.daapi.settings import VIEW_ALIAS
from gui.Scaleform.framework import AppRef, VIEW_TYPE
from gui.Scaleform.framework.entities.EventSystemEntity import EventSystemEntity
from gui.shared import EVENT_BUS_SCOPE
from gui.shared.events import LoadEvent
from notification.BaseMessagesController import BaseMessagesController

class LayoutController(BaseMessagesController, EventSystemEntity, AppRef):

    def __init__(self, model):
        BaseMessagesController.__init__(self, model)
        isViewAvailable = self.app.containerManager.isViewAvailable(VIEW_TYPE.LOBBY_SUB)
        if isViewAvailable:
            view = self.app.containerManager.getView(VIEW_TYPE.LOBBY_SUB)
            isNowHangarLoading = view.settings.alias == VIEW_ALIAS.LOBBY_HANGAR
        else:
            isNowHangarLoading = self.app.loaderManager.isViewLoading(VIEW_ALIAS.LOBBY_HANGAR)
        if isNowHangarLoading:
            self.__onHangarViewSelected({})
        else:
            self.__onSomeViewSelected({})
        self.addListener(LoadEvent.LOAD_HANGAR, self.__onHangarViewSelected, EVENT_BUS_SCOPE.LOBBY)
        self.addListener(LoadEvent.LOAD_INVENTORY, self.__onSomeViewSelected, EVENT_BUS_SCOPE.LOBBY)
        self.addListener(LoadEvent.LOAD_SHOP, self.__onSomeViewSelected, EVENT_BUS_SCOPE.LOBBY)
        self.addListener(LoadEvent.LOAD_PROFILE, self.__onSomeViewSelected, EVENT_BUS_SCOPE.LOBBY)
        self.addListener(LoadEvent.LOAD_TECHTREE, self.__onSomeViewSelected, EVENT_BUS_SCOPE.LOBBY)
        self.addListener(LoadEvent.LOAD_RESEARCH, self.__onSomeViewSelected, EVENT_BUS_SCOPE.LOBBY)
        self.addListener(LoadEvent.LOAD_BARRACKS, self.__onSomeViewSelected, EVENT_BUS_SCOPE.LOBBY)
        self.addListener(LoadEvent.LOAD_CUSTOMIZATION, self.__onSomeViewSelected, EVENT_BUS_SCOPE.LOBBY)
        self.addListener(LoadEvent.LOAD_BATTLE_QUEUE, self.__onSomeViewSelected, EVENT_BUS_SCOPE.LOBBY)
        self.addListener(LoadEvent.LOAD_BATTLE_LOADING, self.__onSomeViewSelected, EVENT_BUS_SCOPE.LOBBY)
        self.addListener(LoadEvent.LOAD_TUTORIAL_LOADING, self.__onSomeViewSelected, EVENT_BUS_SCOPE.LOBBY)
        self.addListener(LoadEvent.LOAD_TRAININGS, self.__onSomeViewSelected, EVENT_BUS_SCOPE.LOBBY)
        self.addListener(LoadEvent.LOAD_TRAINING_ROOM, self.__onSomeViewSelected, EVENT_BUS_SCOPE.LOBBY)

    def __onSomeViewSelected(self, data):
        self._model.setLayoutSettings(0, 35)

    def __onHangarViewSelected(self, data):
        self._model.setLayoutSettings(4, 235)

    def cleanUp(self):
        self.removeListener(LoadEvent.LOAD_HANGAR, self.__onHangarViewSelected, EVENT_BUS_SCOPE.LOBBY)
        self.removeListener(LoadEvent.LOAD_INVENTORY, self.__onSomeViewSelected, EVENT_BUS_SCOPE.LOBBY)
        self.removeListener(LoadEvent.LOAD_SHOP, self.__onSomeViewSelected, EVENT_BUS_SCOPE.LOBBY)
        self.removeListener(LoadEvent.LOAD_PROFILE, self.__onSomeViewSelected, EVENT_BUS_SCOPE.LOBBY)
        self.removeListener(LoadEvent.LOAD_TECHTREE, self.__onSomeViewSelected, EVENT_BUS_SCOPE.LOBBY)
        self.removeListener(LoadEvent.LOAD_RESEARCH, self.__onSomeViewSelected, EVENT_BUS_SCOPE.LOBBY)
        self.removeListener(LoadEvent.LOAD_BARRACKS, self.__onSomeViewSelected, EVENT_BUS_SCOPE.LOBBY)
        self.removeListener(LoadEvent.LOAD_CUSTOMIZATION, self.__onSomeViewSelected, EVENT_BUS_SCOPE.LOBBY)
        self.removeListener(LoadEvent.LOAD_BATTLE_QUEUE, self.__onSomeViewSelected, EVENT_BUS_SCOPE.LOBBY)
        self.removeListener(LoadEvent.LOAD_BATTLE_LOADING, self.__onSomeViewSelected, EVENT_BUS_SCOPE.LOBBY)
        self.removeListener(LoadEvent.LOAD_TUTORIAL_LOADING, self.__onSomeViewSelected, EVENT_BUS_SCOPE.LOBBY)
        self.removeListener(LoadEvent.LOAD_TRAININGS, self.__onSomeViewSelected, EVENT_BUS_SCOPE.LOBBY)
        self.removeListener(LoadEvent.LOAD_TRAINING_ROOM, self.__onSomeViewSelected, EVENT_BUS_SCOPE.LOBBY)
        BaseMessagesController.cleanUp(self)
# Embedded file name: scripts/client/messenger/gui/Scaleform/data/ChannelsCarouselHandler.py
from debug_utils import LOG_ERROR
from gui.Scaleform.daapi.view.meta.ChannelCarouselMeta import ChannelCarouselMeta
from gui.Scaleform.framework import AppRef, VIEW_TYPE
from gui.Scaleform.framework.managers.containers import ExternalCriteria
from gui.shared import g_eventBus, EVENT_BUS_SCOPE
from gui.shared.events import ChannelManagementEvent, ChannelCarouselEvent
from messenger.ext import channel_num_gen
from messenger.gui import events_dispatcher
from messenger.gui.Scaleform.data.ChannelsDataProvider import ChannelsDataProvider

class ChannelFindCriteria(ExternalCriteria):

    def __init__(self, criteria = None):
        super(ChannelFindCriteria, self).__init__(criteria)

    def find(self, name, obj):
        return getattr(obj, '_clientID', 0) == self._criteria


class ChannelsCarouselHandler(AppRef):

    def __init__(self, guiEntry):
        super(ChannelsCarouselHandler, self).__init__()
        self.__guiEntry = guiEntry
        self.__channelsDP = None
        self.__handlers = {}
        return

    def init(self):
        self.__channelsDP = ChannelsDataProvider()
        add = g_eventBus.addListener
        add(ChannelManagementEvent.REQUEST_TO_ADD, self.__handleRequestToAdd, scope=EVENT_BUS_SCOPE.LOBBY)
        add(ChannelManagementEvent.REQUEST_TO_REMOVE, self.__handleRequestToRemove, scope=EVENT_BUS_SCOPE.LOBBY)
        add(ChannelManagementEvent.REQUEST_TO_CHANGE, self.__handleRequestToChange, scope=EVENT_BUS_SCOPE.LOBBY)

    def clear(self):
        self.__guiEntry = None
        self.__handlers.clear()
        if self.__channelsDP is not None:
            self.__channelsDP.clear()
            self.__channelsDP.finiGUI()
            self.__channelsDP = None
        remove = g_eventBus.removeListener
        remove(ChannelManagementEvent.REQUEST_TO_ADD, self.__handleRequestToAdd, scope=EVENT_BUS_SCOPE.LOBBY)
        remove(ChannelManagementEvent.REQUEST_TO_REMOVE, self.__handleRequestToRemove, scope=EVENT_BUS_SCOPE.LOBBY)
        remove(ChannelManagementEvent.REQUEST_TO_CHANGE, self.__handleRequestToChange, scope=EVENT_BUS_SCOPE.LOBBY)
        return

    def start(self):
        add = g_eventBus.addListener
        add(ChannelCarouselEvent.CAROUSEL_INITED, self.__handleCarouselInited, scope=EVENT_BUS_SCOPE.LOBBY)
        add(ChannelCarouselEvent.CAROUSEL_DESTROYED, self.__handleCarouselDestroyed, scope=EVENT_BUS_SCOPE.LOBBY)
        add(ChannelCarouselEvent.OPEN_BUTTON_CLICK, self.__handleOpenButtonClick, scope=EVENT_BUS_SCOPE.LOBBY)
        add(ChannelCarouselEvent.CLOSE_BUTTON_CLICK, self.__handleCloseButtonClick, scope=EVENT_BUS_SCOPE.LOBBY)

    def stop(self):
        remove = g_eventBus.removeListener
        remove(ChannelCarouselEvent.CAROUSEL_INITED, self.__handleCarouselInited, scope=EVENT_BUS_SCOPE.LOBBY)
        remove(ChannelCarouselEvent.CAROUSEL_DESTROYED, self.__handleCarouselDestroyed, scope=EVENT_BUS_SCOPE.LOBBY)
        remove(ChannelCarouselEvent.OPEN_BUTTON_CLICK, self.__handleOpenButtonClick, scope=EVENT_BUS_SCOPE.LOBBY)
        remove(ChannelCarouselEvent.CLOSE_BUTTON_CLICK, self.__handleCloseButtonClick, scope=EVENT_BUS_SCOPE.LOBBY)
        self.__channelsDP.finiGUI()

    def addChannel(self, channel, lazy = False, isNotified = False):
        clientID = channel.getClientID()
        isSystem = channel.isSystem()
        if lazy:
            order = channel_num_gen.getOrder4LazyChannel(channel.getName())
            openHandler = lambda : events_dispatcher.showLazyChannelWindow(clientID)
        else:
            order = channel_num_gen.genOrder4Channel(channel)
            openHandler = lambda : events_dispatcher.showLobbyChannelWindow(clientID)
        self.__handlers[clientID] = (ChannelFindCriteria(clientID), openHandler)
        self.__channelsDP.addItem(clientID, {'label': channel.getFullName(),
         'canClose': not isSystem,
         'isNotified': isNotified,
         'icon': None,
         'order': order})
        return

    def removeChannel(self, channel):
        clientID = channel.getClientID()
        if clientID in self.__handlers:
            criteria, openHandler = self.__handlers.pop(clientID)
            window = None
            if self.app is not None:
                window = self.app.containerManager.getView(VIEW_TYPE.WINDOW, criteria)
            if window is not None:
                window.destroy()
        self.__channelsDP.removeItem(clientID)
        return

    def notifyChannel(self, channel, isNotified = True):
        self.__channelsDP.setItemField(channel.getClientID(), 'isNotified', isNotified)

    def updateChannel(self, channel):
        self.__channelsDP.setItemField(channel.getClientID(), 'label', channel.getFullName())

    def removeChannels(self):
        if self.__channelsDP is not None:
            self.__channelsDP.clear()
        self.__handlers.clear()
        return

    def __handleCarouselInited(self, event):
        carousel = event.target
        if isinstance(carousel, ChannelCarouselMeta):
            self.__channelsDP.initGUI(carousel.as_getDataProviderS())
        else:
            LOG_ERROR('Channel carousel must be extends ChannelCarouselMeta', carousel)

    def __handleCarouselDestroyed(self, _):
        self.__channelsDP.finiGUI()

    def __handleRequestToAdd(self, event):
        ctx = event.ctx
        label = ctx.get('label')
        if label is None:
            LOG_ERROR('Label is not defined', event.ctx)
            return
        else:
            criteria = ctx.get('criteria')
            if criteria is None:
                LOG_ERROR('Criteria is not defined', event.ctx)
                return
            openHandler = ctx.get('openHandler')
            if openHandler is None:
                LOG_ERROR('Open handler is not defined', event.ctx)
                return
            clientID = event.clientID
            if clientID not in self.__handlers:
                self.__handlers[clientID] = (criteria, openHandler)
                self.__channelsDP.addItem(clientID, ctx)
            return

    def __handleRequestToRemove(self, event):
        clientID = event.clientID
        if clientID in self.__handlers:
            criteria, openHandler = self.__handlers.pop(clientID)
            window = None
            if self.app is not None:
                window = self.app.containerManager.getView(VIEW_TYPE.WINDOW, criteria)
            if window is not None:
                window.destroy()
            self.__channelsDP.removeItem(clientID)
        return

    def __handleRequestToChange(self, event):
        ctx = event.ctx
        key = ctx.get('key')
        if key is None:
            LOG_ERROR('Key of item field is not defined', ctx)
            return
        else:
            value = ctx.get('value')
            if value is None:
                LOG_ERROR('Value of item field is not defined', ctx)
                return
            self.__channelsDP.setItemField(event.clientID, key, value)
            return

    def __handleOpenButtonClick(self, event):
        clientID = event.clientID
        if not clientID:
            return
        elif clientID not in self.__handlers:
            return
        else:
            criteria, openHandler = self.__handlers[clientID]
            viewContainer = self.app.containerManager
            window = viewContainer.getView(VIEW_TYPE.WINDOW, criteria)
            if window is not None:
                wName = window.uniqueName
                isOnTop = viewContainer.as_isOnTopS(VIEW_TYPE.WINDOW, wName)
                if not isOnTop:
                    viewContainer.as_bringToFrontS(VIEW_TYPE.WINDOW, wName)
                    return
                window.onWindowMinimize()
            else:
                self.__channelsDP.setItemField(clientID, 'isNotified', False)
                openHandler()
            return

    def __handleCloseButtonClick(self, event):
        clientID = event.clientID
        if not clientID:
            return
        elif clientID not in self.__handlers:
            return
        else:
            criteria, openHandler = self.__handlers[clientID]
            window = self.app.containerManager.getView(VIEW_TYPE.WINDOW, criteria)
            if window is not None:
                window.onWindowClose()
            elif self.__guiEntry:
                controller = self.__guiEntry.channelsCtrl.getController(clientID)
                if controller:
                    controller.exit()
            return
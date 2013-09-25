from gui.Scaleform.daapi.view.meta.WindowViewMeta import WindowViewMeta
from gui.Scaleform.framework.entities.View import View
from messenger.gui.Scaleform.meta.BaseChannelWindowMeta import BaseChannelWindowMeta
from gui.shared import events, EVENT_BUS_SCOPE
from messenger.gui.Scaleform.sf_settings import MESSENGER_VIEW_ALIAS
from messenger.inject import InjectMessengerEntry, channelsCtrlProperty

class SimpleChannelWindow(View, WindowViewMeta, BaseChannelWindowMeta):
    __metaclass__ = InjectMessengerEntry

    def __init__(self, clientID):
        super(SimpleChannelWindow, self).__init__()
        self._clientID = clientID
        self._controller = self.channelsCtrl.getController(self._clientID)
        if self._controller is None:
            raise ValueError, 'Controller for lobby channel by clientID={0:1} is not found'.format(self._clientID)
        return

    @channelsCtrlProperty
    def channelsCtrl(self):
        return None

    def onWindowClose(self):
        chat = self.chat
        if chat:
            chat.close()
        self.destroy()

    def onWindowMinimize(self):
        chat = self.chat
        if chat:
            chat.minimize()
        self.destroy()

    def showFAQWindow(self):
        self.fireEvent(events.ShowWindowEvent(events.ShowWindowEvent.SHOW_FAQ_WINDOW), scope=EVENT_BUS_SCOPE.LOBBY)

    def getClientID(self):
        return self._clientID

    def getChannelID(self):
        return self._controller.getChannel().getID()

    def getProtoType(self):
        return self._controller.getChannel().getProtoType()

    @property
    def chat(self):
        chat = None
        if MESSENGER_VIEW_ALIAS.CHANNEL_COMPONENT in self.components:
            chat = self.components[MESSENGER_VIEW_ALIAS.CHANNEL_COMPONENT]
        return chat

    def _populate(self):
        super(SimpleChannelWindow, self)._populate()
        channel = self._controller.getChannel()
        channel.onChannelInfoUpdated += self.__ce_onChannelInfoUpdated
        self.as_setTitleS(channel.getFullName())
        self.as_setCloseEnabledS(not channel.isSystem())

    def _dispose(self):
        if self._controller is not None:
            channel = self._controller.getChannel()
            if channel is not None:
                channel.onChannelInfoUpdated -= self.__ce_onChannelInfoUpdated
            self._controller = None
        super(SimpleChannelWindow, self)._dispose()
        return

    def _onRegisterFlashComponent(self, viewPy, alias):
        if alias == MESSENGER_VIEW_ALIAS.CHANNEL_COMPONENT:
            self._controller.setView(viewPy)

    def __ce_onChannelInfoUpdated(self, channel):
        self.as_setTitleS(channel.getFullName())

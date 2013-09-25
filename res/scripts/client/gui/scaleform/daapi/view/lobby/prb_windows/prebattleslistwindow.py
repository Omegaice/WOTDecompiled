from debug_utils import LOG_ERROR
from gui.Scaleform.daapi.view.meta.WindowViewMeta import WindowViewMeta
from gui.Scaleform.framework.entities.View import View
from gui.prb_control.prb_helpers import PrbListener
from gui.shared import events, EVENT_BUS_SCOPE
from messenger import MessengerEntry
from messenger.gui.Scaleform.sf_settings import MESSENGER_VIEW_ALIAS
from messenger.proto.bw import find_criteria

class PrebattlesListWindow(View, WindowViewMeta, PrbListener):

    def __init__(self, name):
        super(PrebattlesListWindow, self).__init__()
        self._name = name

    @property
    def chat(self):
        chat = None
        if MESSENGER_VIEW_ALIAS.CHANNEL_COMPONENT in self.components:
            chat = self.components[MESSENGER_VIEW_ALIAS.CHANNEL_COMPONENT]
        return chat

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

    def _dispose(self):
        self.removeListener(events.MessengerEvent.LAZY_CHANNEL_CTRL_INITED, self.__handleLazyChannelControllerInited, scope=EVENT_BUS_SCOPE.LOBBY)
        super(PrebattlesListWindow, self)._dispose()

    def _onRegisterFlashComponent(self, viewPy, alias):
        if alias == MESSENGER_VIEW_ALIAS.CHANNEL_COMPONENT:
            channels = MessengerEntry.g_instance.gui.channelsCtrl
            controller = None
            if channels:
                controller = channels.getControllerByCriteria(find_criteria.BWLazyChannelFindCriteria(self._name))
            if controller is not None:
                controller.setView(viewPy)
            else:
                self.addListener(events.MessengerEvent.LAZY_CHANNEL_CTRL_INITED, self.__handleLazyChannelControllerInited, scope=EVENT_BUS_SCOPE.LOBBY)
        return

    def __handleLazyChannelControllerInited(self, event):
        ctx = event.ctx
        channelName = ctx.get('channelName')
        if channelName is None:
            LOG_ERROR('Channel name type is not defined', ctx)
            return
        else:
            controller = ctx.get('controller')
            if controller is None:
                LOG_ERROR('Channel controller is not defined', ctx)
                return
            if channelName == self._name:
                chat = self.chat
                if chat is not None:
                    controller.setView(chat)
            return

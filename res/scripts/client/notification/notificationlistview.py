# Embedded file name: scripts/client/notification/NotificationListView.py
from debug_utils import LOG_ERROR, LOG_DEBUG
from gui.Scaleform.daapi.view.meta.NotificationsListMeta import NotificationsListMeta
from gui.Scaleform.framework.entities.View import View
from notification.NotificationLayoutView import NotificationLayoutView
from gui.shared import events
from notification import NotificationMVC
from helpers.links import openSecuritySettingsPage

class NotificationListView(NotificationsListMeta, View, NotificationLayoutView):
    SCROLL_STEP_FACTOR = 10

    def __init__(self, ctx):
        View.__init__(self)
        NotificationLayoutView.__init__(self, ctx.get('model'))
        self._model.onMessageReceived += self.__onMessageReceived
        self.__closeCallBack = ctx.get('closeCallBack')

    def onMessageShowMore(self, data):
        if hasattr(data, 'command'):
            command = data.command
        else:
            LOG_ERROR('Command is not defined')
            return
        ctx = {}
        if hasattr(data, 'param'):
            param = data.param
            if hasattr(param, 'key') and hasattr(param, 'value'):
                ctx = {param.key: param.value}
        self.fireEvent(events.ShowWindowEvent(command, ctx))

    def onSecuritySettingsLinkClick(self):
        openSecuritySettingsPage()

    def _populate(self):
        super(NotificationListView, self)._populate()
        self.as_setInitDataS({'scrollStepFactor': self.SCROLL_STEP_FACTOR})
        messagesList = self._model.getMessagesList()
        formedList = []
        for message, isServerMsg, flag, notify, auxData in messagesList:
            notificationObject = self._formFullNotificationObject(message, flag, notify, auxData)
            formedList.append(notificationObject)

        self.as_setMessagesListS(formedList)
        self.onLayoutSettingsChanged({})

    def onLayoutSettingsChanged(self, settings):
        self.as_layoutInfoS({'paddingBottom': 25,
         'paddingRight': 0})

    def __onMessageReceived(self, message, priority, notify, auxData):
        messageObject = self._formFullNotificationObject(message, priority, notify, auxData)
        if priority:
            NotificationMVC.g_instance.getAlertController().showAlertMessage(messageObject)
        self.as_appendMessageS(messageObject)

    def onWindowClose(self):
        if self.__closeCallBack:
            self.__closeCallBack()
        self.destroy()

    def _dispose(self):
        self._model.onMessageReceived -= self.__onMessageReceived
        self.__closeCallBack = None
        self.cleanUp()
        super(NotificationListView, self)._dispose()
        return
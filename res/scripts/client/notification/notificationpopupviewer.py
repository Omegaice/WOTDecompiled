# Embedded file name: scripts/client/notification/NotificationPopUpViewer.py
from gui.Scaleform.daapi.view.meta.NotificationPopUpViewerMeta import NotificationPopUpViewerMeta
from notification import NotificationsModel
from messenger import g_settings
from notification.NotificationLayoutView import NotificationLayoutView
from gui.shared import events
from notification import NotificationMVC
from helpers.links import openSecuritySettingsPage

class NotificationPopUpViewer(NotificationPopUpViewerMeta, NotificationLayoutView):

    def __init__(self):
        mvc = NotificationMVC.g_instance
        mvc.initialize()
        settings = g_settings.lobby.serviceChannel
        self.__maxAvailableItemsCount = settings.stackLength
        self.__messageLivingTime = settings.lifeTime
        self.__animationSpeed = settings.alphaSpeed
        self.__messagesPadding = settings.padding
        self.__noDisplayingPopups = True
        self.__pendingMessagesQueue = []
        NotificationLayoutView.__init__(self, mvc.getModel())
        NotificationPopUpViewerMeta.__init__(self)
        self._model.onMessageReceived += self.__onMessageReceived
        self._model.onDisplayStateChanged += self.__displayStateChangeHandler
        mvc.getAlertController().onAllAlertsClosed += self.__allAlertsMessageCloseHandler

    def onLayoutSettingsChanged(self, settings):
        self.as_layoutInfoS(settings)

    def _populate(self):
        self.as_layoutInfoS(self._model.getLayoutSettings())
        self.as_initInfoS(self.__maxAvailableItemsCount, self.__messageLivingTime, self.__messagesPadding, self.__animationSpeed)
        self._model.requestUnreadMessages()

    def __onMessageReceived(self, message, priority, notify, auxData):
        currentDisplayState = self._model.getDisplayState()
        if currentDisplayState == NotificationsModel.POPUPS_STATE:
            messageObject = self._formFullNotificationObject(message, priority, notify, auxData)
            if NotificationMVC.g_instance.getAlertController().isAlertShowing():
                self.__pendingMessagesQueue.append(messageObject)
            elif len(self.__pendingMessagesQueue) > 0:
                self.__pendingMessagesQueue.append(messageObject)
            elif priority:
                if self.__noDisplayingPopups:
                    self.__showAlertMessage(messageObject)
                else:
                    self.__pendingMessagesQueue.append(messageObject)
            else:
                self.__sendMessageForDisplay(messageObject)

    def onMessageShowMore(self, data):
        self.fireEvent(events.ShowWindowEvent(data.command, {data.param.key: data.param.value}))

    def onSecuritySettingsLinkClick(self):
        openSecuritySettingsPage()

    def onMessageHided(self, byTimeout, wasNotified):
        if self._model.getDisplayState() == NotificationsModel.POPUPS_STATE:
            if not byTimeout and wasNotified:
                self._model.decrementNotifiedMessagesCount()

    def __sendMessageForDisplay(self, messageObject):
        if messageObject.get('notify'):
            self._model.incrementNotifiedMessagesCount()
        self.as_appendMessageS(messageObject)
        self.__noDisplayingPopups = False

    def __showAlertMessage(self, messageObject):
        NotificationMVC.g_instance.getAlertController().showAlertMessage(messageObject)

    def setListClear(self):
        self.__noDisplayingPopups = True
        if self._model.getDisplayState() == NotificationsModel.POPUPS_STATE:
            if len(self.__pendingMessagesQueue) > 0:
                self.__showAlertMessage(self.__pendingMessagesQueue.pop(0))

    def __allAlertsMessageCloseHandler(self):
        if len(self.__pendingMessagesQueue) > 0:
            needToShowFromQueueMessages = []
            while len(self.__pendingMessagesQueue) > 0:
                messageObject = self.__pendingMessagesQueue.pop(0)
                isPriorityVal = messageObject.get('priority')
                if isPriorityVal:
                    self.__showAlertMessage(messageObject)
                    return
                needToShowFromQueueMessages.append(messageObject)

            while len(needToShowFromQueueMessages) > 0:
                messageObject = needToShowFromQueueMessages.pop(0)
                if len(needToShowFromQueueMessages) < self.__maxAvailableItemsCount:
                    self.__sendMessageForDisplay(messageObject)

    def __displayStateChangeHandler(self, oldState, newState, data):
        if newState == NotificationsModel.LIST_STATE:
            self.as_removeAllMessagesS()

    def _dispose(self):
        self.__pendingMessagesQueue = []
        self._model.onMessageReceived -= self.__onMessageReceived
        self._model.onDisplayStateChanged -= self.__displayStateChangeHandler
        mvcInstance = NotificationMVC.g_instance
        mvcInstance.getAlertController().onAllAlertsClosed -= self.__allAlertsMessageCloseHandler
        self.cleanUp()
        mvcInstance.cleanUp()
        super(NotificationPopUpViewer, self)._dispose()
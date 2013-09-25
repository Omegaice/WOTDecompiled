from gui.Scaleform.framework.entities.DAAPIModule import DAAPIModule

class NotificationPopUpViewerMeta(DAAPIModule):

    def setListClear(self):
        self._printOverrideError('setListClear')

    def onMessageHided(self, byTimeout, wasNotified):
        self._printOverrideError('onMessageHided')

    def onMessageShowMore(self, data):
        self._printOverrideError('onMessageShowMore')

    def onSecuritySettingsLinkClick(self):
        self._printOverrideError('onSecuritySettingsLinkClick')

    def as_appendMessageS(self, messageData):
        if self._isDAAPIInited():
            return self.flashObject.as_appendMessage(messageData)

    def as_removeAllMessagesS(self):
        if self._isDAAPIInited():
            return self.flashObject.as_removeAllMessages()

    def as_layoutInfoS(self, data):
        if self._isDAAPIInited():
            return self.flashObject.as_layoutInfo(data)

    def as_initInfoS(self, maxMessagessCount, messagelivingTime, padding, animationSpeed):
        if self._isDAAPIInited():
            return self.flashObject.as_initInfo(maxMessagessCount, messagelivingTime, padding, animationSpeed)

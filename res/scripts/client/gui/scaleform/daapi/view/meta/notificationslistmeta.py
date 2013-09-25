from gui.Scaleform.framework.entities.DAAPIModule import DAAPIModule

class NotificationsListMeta(DAAPIModule):

    def onWindowClose(self):
        self._printOverrideError('onWindowClose')

    def onMessageShowMore(self, data):
        self._printOverrideError('onMessageShowMore')

    def onSecuritySettingsLinkClick(self):
        self._printOverrideError('onSecuritySettingsLinkClick')

    def as_setInitDataS(self, value):
        if self._isDAAPIInited():
            return self.flashObject.as_setInitData(value)

    def as_setMessagesListS(self, value):
        if self._isDAAPIInited():
            return self.flashObject.as_setMessagesList(value)

    def as_appendMessageS(self, messageData):
        if self._isDAAPIInited():
            return self.flashObject.as_appendMessage(messageData)

    def as_layoutInfoS(self, data):
        if self._isDAAPIInited():
            return self.flashObject.as_layoutInfo(data)

from gui.Scaleform.framework.entities.DAAPIModule import DAAPIModule

class MessengerBarMeta(DAAPIModule):

    def channelButtonClick(self):
        self._printOverrideError('channelButtonClick')

    def contactsButtonClick(self):
        self._printOverrideError('contactsButtonClick')

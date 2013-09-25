from gui.Scaleform.daapi.view.dialogs import IDialogMeta
from gui.Scaleform.locale.AOGAS import AOGAS
from gui.Scaleform.locale.MESSENGER import MESSENGER
from gui.shared import events
from web_stubs import i18n

class SystemMessageMeta(IDialogMeta):
    AOGAS = 'AOGAS'

    def __init__(self, messageObject):
        super(SystemMessageMeta, self).__init__()
        self.__messageObject = messageObject
        auxData = self.__messageObject.get('auxData')
        if len(auxData) > 0 and auxData[0] == self.AOGAS:
            self.__title = i18n.makeString(AOGAS.NOTIFICATION_TITLE)
            self.__cancelLabel = i18n.makeString(AOGAS.NOTIFICATION_CLOSE)
        else:
            self.__title = i18n.makeString(MESSENGER.SERVICECHANNELMESSAGES_PRIORITYMESSAGETITLE)
            self.__cancelLabel = i18n.makeString(MESSENGER.SERVICECHANNELMESSAGES_BUTTONS_CLOSE)

    def getMessageObject(self):
        return self.__messageObject

    def getEventType(self):
        return events.ShowDialogEvent.SHOW_SYSTEM_MESSAGE_DIALOG

    def getTitle(self):
        return self.__title

    def getCancelLabel(self):
        return self.__cancelLabel

    def cleanUp(self):
        self.__messageObject = None
        return

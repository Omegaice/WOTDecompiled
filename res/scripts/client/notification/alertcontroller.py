# Embedded file name: scripts/client/notification/AlertController.py
from gui import DialogsInterface
from gui.Scaleform.daapi.view.dialogs.SystemMessageMeta import SystemMessageMeta
from notification.BaseMessagesController import BaseMessagesController
import Event
from adisp import process

class AlertController(BaseMessagesController):

    def __init__(self, model):
        BaseMessagesController.__init__(self, model)
        self.__actualDisplayingAlerts = 0
        self.onAllAlertsClosed = Event.Event()

    @process
    def showAlertMessage(self, data):
        self.__actualDisplayingAlerts += 1
        closeSuccess = yield DialogsInterface.showDialog(SystemMessageMeta(data))
        self.__actualDisplayingAlerts -= 1
        if self.__actualDisplayingAlerts == 0:
            self.onAllAlertsClosed()

    def isAlertShowing(self):
        return self.__actualDisplayingAlerts > 0
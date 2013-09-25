from debug_utils import LOG_DEBUG
from notification.BaseNotificationView import BaseNotificationView

class NotificationLayoutView(BaseNotificationView):

    def __init__(self, model):
        BaseNotificationView.__init__(self, model)
        self._model.onLayoutSettingsChanged += self.onLayoutSettingsChanged

    def onLayoutSettingsChanged(self, settings):
        pass

    def cleanUp(self):
        self._model.onLayoutSettingsChanged -= self.onLayoutSettingsChanged
        self.model = None
        return

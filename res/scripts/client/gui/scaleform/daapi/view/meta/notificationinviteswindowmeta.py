# Embedded file name: scripts/client/gui/Scaleform/daapi/view/meta/NotificationInvitesWindowMeta.py
from gui.Scaleform.framework.entities.DAAPIModule import DAAPIModule

class NotificationInvitesWindowMeta(DAAPIModule):

    def requestInvites(self):
        self._printOverrideError('requestInvites')

    def selectedInvite(self, value):
        self._printOverrideError('selectedInvite')

    def as_setInvitesS(self, value):
        if self._isDAAPIInited():
            return self.flashObject.as_setInvites(value)
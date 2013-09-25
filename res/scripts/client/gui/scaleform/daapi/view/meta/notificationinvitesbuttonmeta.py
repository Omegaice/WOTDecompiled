from gui.Scaleform.framework.entities.DAAPIModule import DAAPIModule

class NotificationInvitesButtonMeta(DAAPIModule):

    def handleClick(self):
        self._printOverrideError('handleClick')

    def as_setStateS(self, isBlinking):
        if self._isDAAPIInited():
            return self.flashObject.as_setState(isBlinking)

from gui.Scaleform.framework.entities.DAAPIModule import DAAPIModule

class ContainerManagerMeta(DAAPIModule):

    def as_getViewS(self, name):
        if self._isDAAPIInited():
            return self.flashObject.as_getView(name)

    def as_showS(self, token, x, y):
        if self._isDAAPIInited():
            return self.flashObject.as_show(token, x, y)

    def as_hideS(self, token):
        if self._isDAAPIInited():
            return self.flashObject.as_hide(token)

    def as_registerContainerS(self, type, token):
        if self._isDAAPIInited():
            return self.flashObject.as_registerContainer(type, token)

    def as_unregisterContainerS(self, type):
        if self._isDAAPIInited():
            return self.flashObject.as_unregisterContainer(type)

    def as_closePopUpsS(self):
        if self._isDAAPIInited():
            return self.flashObject.as_closePopUps()

    def as_isOnTopS(self, cType, vName):
        if self._isDAAPIInited():
            return self.flashObject.as_isOnTop(cType, vName)

    def as_bringToFrontS(self, cType, vName):
        if self._isDAAPIInited():
            return self.flashObject.as_bringToFront(cType, vName)

from gui.Scaleform.framework.entities.DAAPIModule import DAAPIModule

class MinimapEntityMeta(DAAPIModule):

    def as_updatePointsS(self):
        if self._isDAAPIInited():
            return self.flashObject.as_updatePoints()

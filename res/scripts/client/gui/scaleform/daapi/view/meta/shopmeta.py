from gui.Scaleform.framework.entities.DAAPIModule import DAAPIModule

class ShopMeta(DAAPIModule):

    def buyItem(self, data):
        self._printOverrideError('buyItem')

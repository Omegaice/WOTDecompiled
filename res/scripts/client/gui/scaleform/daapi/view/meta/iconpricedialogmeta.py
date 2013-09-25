from gui.Scaleform.framework.entities.DAAPIModule import DAAPIModule

class IconPriceDialogMeta(DAAPIModule):

    def as_setMessagePriceS(self, valueStr, currency):
        if self._isDAAPIInited():
            return self.flashObject.as_setMessagePrice(valueStr, currency)

    def as_setPriceLabelS(self, label):
        if self._isDAAPIInited():
            return self.flashObject.as_setPriceLabel(label)

    def as_setOperationAllowedS(self, isAllowed):
        if self._isDAAPIInited():
            return self.flashObject.as_setOperationAllowed(isAllowed)

from gui.Scaleform.framework.entities.DAAPIModule import DAAPIModule

class ExchangeWindowMeta(DAAPIModule):

    def as_setSecondaryCurrencyS(self, credits):
        if self._isDAAPIInited():
            return self.flashObject.as_setSecondaryCurrency(credits)

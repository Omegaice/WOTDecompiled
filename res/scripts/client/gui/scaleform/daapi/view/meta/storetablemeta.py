# Embedded file name: scripts/client/gui/Scaleform/daapi/view/meta/StoreTableMeta.py
from gui.Scaleform.framework.entities.DAAPIModule import DAAPIModule

class StoreTableMeta(DAAPIModule):

    def as_setTableS(self, tableData):
        if self._isDAAPIInited():
            return self.flashObject.as_setTable(tableData)

    def as_scrollToFirstS(self, level, disabled, currency):
        if self._isDAAPIInited():
            return self.flashObject.as_scrollToFirst(level, disabled, currency)

    def as_setGoldS(self, gold):
        if self._isDAAPIInited():
            return self.flashObject.as_setGold(gold)

    def as_setCreditsS(self, credits):
        if self._isDAAPIInited():
            return self.flashObject.as_setCredits(credits)
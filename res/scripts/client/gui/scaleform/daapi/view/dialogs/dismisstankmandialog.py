from adisp import process
from gui import makeHtmlString
from gui.Scaleform.locale.DIALOGS import DIALOGS
from gui.shared.gui_items.serializers import g_itemSerializer
from helpers import i18n
from items import tankmen
from gui.Scaleform.daapi.view.dialogs.SimpleDialog import SimpleDialog
from gui.Scaleform.daapi.view.meta.DismissTankmanDialogMeta import DismissTankmanDialogMeta
from gui.shared.utils.requesters.ItemsRequester import ItemsRequester
__author__ = 'd_savitski'

class DismissTankmanDialog(DismissTankmanDialogMeta, SimpleDialog):

    def __init__(self, meta, handler):
        SimpleDialog.__init__(self, meta.getMessage(), meta.getTitle(), meta.getButtonLabels(), meta.getCallbackWrapper(handler))
        DismissTankmanDialogMeta.__init__(self)
        self._meta = meta
        self.tankman = self._meta.getTankman()
        self.controlNumber = None
        return

    def _populate(self):
        super(DismissTankmanDialog, self)._populate()
        self.as_enabledButtonS(False)
        self.__prepareTankmanData()

    @process
    def __prepareTankmanData(self):
        items = yield ItemsRequester().request()
        dropSkillsCost = []
        for k in sorted(items.shop.dropSkillsCost.keys()):
            dropSkillsCost.append(items.shop.dropSkillsCost[k])

        skills_count = list(tankmen.ACTIVE_SKILLS)
        availableSkillsCount = len(skills_count) - len(self.tankman.skills)
        if self.tankman.roleLevel == tankmen.MAX_SKILL_LEVEL and availableSkillsCount:
            hasNewSkills = self.tankman.descriptor.lastSkillLevel == tankmen.MAX_SKILL_LEVEL or not len(self.tankman.skills)
            self.as_tankManS({'money': (items.stats.credits, items.stats.gold),
             'tankman': g_itemSerializer.pack(self.tankman),
             'dropSkillsCost': dropSkillsCost,
             'hasNewSkills': hasNewSkills,
             'defaultSavingMode': 0})
            self.controlNumber = len(self.tankman.skills) < 1 and str(self.tankman.roleLevel)
            question = makeHtmlString('html_templates:lobby/dialogs', 'dismissTankmanMain', {'roleLevel': str(self.tankman.roleLevel)})
        else:
            if self.tankman.skills[-1].isPerk:
                skillType = DIALOGS.PROTECTEDDISMISSTANKMAN_ADDITIONALMESSAGE_ISPERK
            else:
                skillType = DIALOGS.PROTECTEDDISMISSTANKMAN_ADDITIONALMESSAGE_ISABILLITY
            question = makeHtmlString('html_templates:lobby/dialogs', 'dismissTankmanAdditional', {'skillType': i18n.makeString(skillType),
             'skillName': self.tankman.skills[-1].userName,
             'roleLevel': str(self.tankman.skills[-1].level)})
            self.controlNumber = str(self.tankman.skills[-1].level)
        self.as_controlTextInputS(str(self.controlNumber))
        self.as_setQuestionForUserS(question)

    def sendControlNumber(self, value):
        if value and value == self.controlNumber:
            self.as_enabledButtonS(True)
        else:
            self.as_enabledButtonS(False)

    def _dispose(self):
        super(DismissTankmanDialog, self)._dispose()
        self.controlNumber = None
        self.tankman = None
        self._meta = None
        return

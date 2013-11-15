# 2013.11.15 11:26:26 EST
# Embedded file name: scripts/client/gui/Scaleform/daapi/view/meta/TrainingFormMeta.py
from gui.Scaleform.framework.entities.DAAPIModule import DAAPIModule

class TrainingFormMeta(DAAPIModule):

    def joinTrainingRequest(self, id):
        self._printOverrideError('joinTrainingRequest')

    def createTrainingRequest(self):
        self._printOverrideError('createTrainingRequest')

    def onEscape(self):
        self._printOverrideError('onEscape')

    def as_setListS(self, provider, totalPlayers):
        if self._isDAAPIInited():
            return self.flashObject.as_setList(provider, totalPlayers)
# okay decompyling res/scripts/client/gui/scaleform/daapi/view/meta/trainingformmeta.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:26:26 EST

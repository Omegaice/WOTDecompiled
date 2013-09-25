from gui.Scaleform.framework.entities.DAAPIModule import DAAPIModule

class SoundManagerMeta(DAAPIModule):

    def soundEventHandler(self, group, state, type, id):
        self._printOverrideError('soundEventHandler')

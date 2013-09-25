from gui.Scaleform.framework.entities.DAAPIModule import DAAPIModule

class LobbyChannelWindowMeta(DAAPIModule):

    def as_getMembersDPS(self):
        if self._isDAAPIInited():
            return self.flashObject.as_getMembersDP()

    def as_hideMembersListS(self):
        if self._isDAAPIInited():
            return self.flashObject.as_hideMembersList()

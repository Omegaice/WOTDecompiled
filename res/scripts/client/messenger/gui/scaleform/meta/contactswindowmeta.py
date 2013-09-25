from gui.Scaleform.framework.entities.DAAPIModule import DAAPIModule

class ContactsWindowMeta(DAAPIModule):

    def searchContact(self, criteria):
        self._printOverrideError('searchContact')

    def addToFriends(self, uid, name):
        self._printOverrideError('addToFriends')

    def addToIgnored(self, uid, name):
        self._printOverrideError('addToIgnored')

    def as_getFriendsDPS(self):
        if self._isDAAPIInited():
            return self.flashObject.as_getFriendsDP()

    def as_getClanDPS(self):
        if self._isDAAPIInited():
            return self.flashObject.as_getClanDP()

    def as_getIgnoredDPS(self):
        if self._isDAAPIInited():
            return self.flashObject.as_getIgnoredDP()

    def as_getMutedDPS(self):
        if self._isDAAPIInited():
            return self.flashObject.as_getMutedDP()

    def as_getSearchDPS(self):
        if self._isDAAPIInited():
            return self.flashObject.as_getSearchDP()

    def as_setSearchResultTextS(self, message):
        if self._isDAAPIInited():
            return self.flashObject.as_setSearchResultText(message)

    def as_frozenSearchActionS(self, flag):
        if self._isDAAPIInited():
            return self.flashObject.as_frozenSearchAction(flag)

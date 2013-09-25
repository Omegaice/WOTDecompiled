# Embedded file name: scripts/client/messenger/gui/entry_decorator.py
from __builtin__ import property
from collections import defaultdict
from messenger.gui import setGUIEntries
from messenger.gui.interfaces import IGUIEntryDecorator, IGUIEntry
from messenger.m_constants import MESSENGER_SCOPE

class _EntriesCollection(defaultdict):

    def __missing__(self, key):
        self[key] = value = _UnknownGUIEntry(key)
        return value


class _UnknownGUIEntry(IGUIEntry):

    def __init__(self, scope):
        super(_UnknownGUIEntry, self).__init__()
        self.__scope = scope


class GUIDecorator(IGUIEntryDecorator):

    def __init__(self):
        super(GUIDecorator, self).__init__()
        self.__entries = _EntriesCollection()
        self.__currentScope = MESSENGER_SCOPE.UNKNOWN

    @property
    def channelsCtrl(self):
        return self.__current().channelsCtrl

    def getEntry(self, scope):
        return self.__entries[scope]

    def setEntry(self, scope, entry):
        self.__entries[scope] = entry

    def switch(self, scope):
        if self.__currentScope ^ scope:
            self.close(scope)
            self.__currentScope = scope
            self.show()

    def init(self):
        setGUIEntries(self)
        for entry in self.__entries.itervalues():
            entry.init()

    def clear(self):
        self.close(MESSENGER_SCOPE.UNKNOWN)
        self.__currentScope = MESSENGER_SCOPE.UNKNOWN
        while len(self.__entries):
            _, entry = self.__entries.popitem()
            entry.clear()

    def show(self):
        self.__current().show()

    def close(self, nextScope):
        self.__current().close(nextScope)

    def invoke(self, method, *args, **kwargs):
        self.__current().invoke(method, *args, **kwargs)

    def isEditing(self, event):
        return self.__current().isFocused()

    def isFocused(self):
        return self.__current().isFocused()

    def addClientMessage(self, message, isCurrentPlayer = False):
        self.__current().addClientMessage(message, isCurrentPlayer=isCurrentPlayer)

    def __current(self):
        return self.__entries[self.__currentScope]
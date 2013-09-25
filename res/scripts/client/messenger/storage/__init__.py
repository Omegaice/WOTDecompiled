from messenger import error
from messenger.ext.ROPropertyMeta import ROPropertyMeta
from messenger.storage.ChannelsStorage import ChannelsStorage
from messenger.storage.PlayerCtxStorage import PlayerCtxStorage
from messenger.storage.UsersStorage import UsersStorage
_STORAGE = {'channels': ChannelsStorage(),
 'users': UsersStorage(),
 'playerCtx': PlayerCtxStorage()}

class storage_getter(object):

    def __init__(self, name):
        super(storage_getter, self).__init__()
        if name not in _STORAGE:
            raise error, 'Storage "{0:>s}" not found'.format(name)
        self.__name = name

    def __call__(self, *args):
        return _STORAGE[self.__name]


class StorageDecorator(object):
    __metaclass__ = ROPropertyMeta
    __readonly__ = _STORAGE

    def __repr__(self):
        return 'StorageDecorator(id=0x{0:08X}, ro={1!r:s})'.format(id(self), self.__readonly__.keys())

    def clear(self):
        for storage in self.__readonly__.itervalues():
            storage.clear()

# Embedded file name: scripts/client/messenger/proto/__init__.py
from messenger.ext.ROPropertyMeta import ROPropertyMeta
from messenger.m_constants import PROTO_TYPE, PROTO_TYPE_NAMES
from messenger.proto.bw import BWProtoPlugin
from messenger.proto.interfaces import IProtoPlugin
from messenger.proto.xmpp import XmppPlugin
__all__ = ('BWProtoPlugin', 'XmppPlugin')
SUPPORTED_PROTO_PLUGINS = {PROTO_TYPE_NAMES[PROTO_TYPE.BW]: BWProtoPlugin(),
 PROTO_TYPE_NAMES[PROTO_TYPE.XMPP]: XmppPlugin()}

class proto_getter(object):

    def __init__(self, protoType):
        super(proto_getter, self).__init__()
        self.__attr = PROTO_TYPE_NAMES[protoType]

    def __call__(self, _):
        return SUPPORTED_PROTO_PLUGINS[self.__attr]


class ProtoPluginsDecorator(IProtoPlugin):
    __metaclass__ = ROPropertyMeta
    __readonly__ = SUPPORTED_PROTO_PLUGINS

    def __repr__(self):
        return 'ProtoPluginsDecorator(id=0x{0:08X}, ro={1!r:s})'.format(id(self), self.__readonly__.keys())

    def connect(self, scope):
        for plugin in self.__readonly__.itervalues():
            plugin.connect(scope)

    def disconnect(self):
        for plugin in self.__readonly__.itervalues():
            plugin.disconnect()

    def clear(self):
        for plugin in self.__readonly__.itervalues():
            plugin.clear()
# Embedded file name: scripts/client/gui/shared/gui_items/serializers.py
__author__ = 'i_maliavko'
import pickle
from debug_utils import *

class ISerializer(object):
    """
    Serializator interface.
    """

    def pack(self, item):
        """
        Pack gui item.
        
        @param item: gui item object
        @return: serialized object. Depends on serializator
                implementation.
        """
        raise NotImplementedError, 'Method need to be overriden'

    def unpack(self, packedData):
        """
        Unpack given data to the gui item object.
        
        @param packedData: packed object to unpack
        @return: gui item unpacked object
        """
        raise NotImplementedError, 'Method need to be overriden'


class DAAIPSerializer(ISerializer):
    """
    Make conversion on gui item. Convert format is open dictionary
    with some vital data to unpacking and build item.
    """
    CLASS_KEY = '__class__'
    ARGS_KEY = '__args__'

    def pack(self, item):
        result = item.toDict()
        result.update({self.CLASS_KEY: pickle.dumps(item.__class__),
         self.ARGS_KEY: pickle.dumps(item.getCtorArgs())})
        return result

    def unpack(self, packedData):
        try:
            if not isinstance(packedData, dict):
                packedData = packedData.children
            clazz = pickle.loads(packedData.get(self.CLASS_KEY))
            args = pickle.loads(packedData.get(self.ARGS_KEY))
            item = clazz(*args)
            item.fromDict(packedData)
            return item
        except Exception:
            LOG_CURRENT_EXCEPTION()
            return None

        return None


class PickleSerializer(ISerializer):
    """
    Converts gui items to the pickle string and back.
    """

    def pack(self, item):
        return pickle.dumps([item.__class__, item.getCtorArgs(), item.toDict()])

    def unpack(self, packedData):
        try:
            clazz, args, values = pickle.loads(packedData)
            item = clazz(*args)
            item.fromDict(values)
            return item
        except Exception:
            LOG_CURRENT_EXCEPTION()
            return None

        return None


g_itemSerializer = DAAIPSerializer()
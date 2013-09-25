# Embedded file name: scripts/client/gui/shared/ItemsCache.py
from Event import Event
from adisp import async
from debug_utils import LOG_DEBUG
from PlayerEvents import g_playerEvents
from gui.shared.utils.requesters import ItemsRequester, REQ_CRITERIA

class _ItemsCache(object):

    def __init__(self):
        self.__items = ItemsRequester()
        self.__waitForSync = False
        self.onSyncStarted = Event()
        self.onSyncCompleted = Event()

    def init(self):
        g_playerEvents.onInventoryResync += self._onResync
        g_playerEvents.onDossiersResync += self._onResync
        g_playerEvents.onStatsResync += self._onResync
        g_playerEvents.onCenterIsLongDisconnected += self._onCenterIsLongDisconnected

    def fini(self):
        self.onSyncStarted.clear()
        self.onSyncCompleted.clear()
        g_playerEvents.onCenterIsLongDisconnected -= self._onCenterIsLongDisconnected
        g_playerEvents.onStatsResync -= self._onResync
        g_playerEvents.onDossiersResync -= self._onResync
        g_playerEvents.onInventoryResync -= self._onResync

    @property
    def waitForSync(self):
        return self.__waitForSync

    @property
    def items(self):
        return self.__items

    @async
    def update(self, diff = None, callback = None):
        self.__invalidateData(diff, callback)

    def clear(self):
        return self.items.clear()

    def _onResync(self, *args):
        if not self.__waitForSync:
            self.__invalidateData()

    def _onCenterIsLongDisconnected(self, isLongDisconnected):
        self.items.dossiers.onCenterIsLongDisconnected(isLongDisconnected)

    def __invalidateData(self, diff = None, callback = lambda *args: None):

        def cbWrapper(*args):
            self.__waitForSync = False
            self.onSyncCompleted()
            callback(*args)

        self.__waitForSync = True
        self.onSyncStarted()
        self.__items.invalidateCache(diff)
        self.__items.request()(cbWrapper)


g_itemsCache = _ItemsCache()
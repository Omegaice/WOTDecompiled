from gui.shared.ItemsCache import g_itemsCache, REQ_CRITERIA
from gui.shared.quests.QuestsCache import g_questsCache
from gui.shared.event_bus import EventBus, EVENT_BUS_SCOPE
__all__ = ['g_eventBus',
 'g_loader',
 'getBattleUI',
 'getLobbyUI',
 'g_itemsCache',
 'g_questsCache',
 'init',
 'start',
 'fini',
 'EVENT_BUS_SCOPE',
 'REQ_CRITERIA']
g_eventBus = EventBus()
g_loader = None

def getBattleUI():
    pass


def getLobbyUI():
    pass

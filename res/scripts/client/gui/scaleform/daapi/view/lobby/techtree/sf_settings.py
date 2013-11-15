# 2013.11.15 11:26:19 EST
# Embedded file name: scripts/client/gui/Scaleform/daapi/view/lobby/techtree/sf_settings.py
from gui.Scaleform.framework.managers.loaders import PackageBusinessHandler
from gui.Scaleform.daapi.settings import VIEW_ALIAS
from gui.Scaleform.framework import ViewSettings, VIEW_TYPE, VIEW_SCOPE
from gui.shared import EVENT_BUS_SCOPE, g_eventBus
from gui.shared.events import LoadEvent

def getViewSettings():
    from gui.Scaleform.daapi.view.lobby.techtree.Research import Research
    from gui.Scaleform.daapi.view.lobby.techtree.TechTree import TechTree
    return [ViewSettings(VIEW_ALIAS.LOBBY_TECHTREE, TechTree, 'techtree.swf', VIEW_TYPE.LOBBY_SUB, LoadEvent.LOAD_TECHTREE, VIEW_SCOPE.DEFAULT), ViewSettings(VIEW_ALIAS.LOBBY_RESEARCH, Research, 'research.swf', VIEW_TYPE.LOBBY_SUB, LoadEvent.LOAD_RESEARCH, VIEW_SCOPE.DEFAULT)]


def getBusinessHandlers():
    return [TechTreePackageBusinessHandler()]


class TechTreePackageBusinessHandler(PackageBusinessHandler):

    def __init__(self):
        listeners = [(LoadEvent.LOAD_TECHTREE, self.__loadTechTree), (LoadEvent.LOAD_RESEARCH, self.__loadResearch), (LoadEvent.EXIT_FROM_RESEARCH, self.__exitFromResearch)]
        super(TechTreePackageBusinessHandler, self).__init__(listeners, EVENT_BUS_SCOPE.LOBBY)
        self.__exitEvent = None
        return

    def __loadTechTree(self, event):
        self.app.loadView(VIEW_ALIAS.LOBBY_TECHTREE, ctx=event.ctx)

    def __loadResearch(self, event):
        ctx = event.ctx
        self.__exitEvent = ctx.get('exit')
        self.app.loadView(VIEW_ALIAS.LOBBY_RESEARCH, ctx=ctx)

    def __exitFromResearch(self, _):
        if self.__exitEvent is not None:
            g_eventBus.handleEvent(self.__exitEvent, scope=EVENT_BUS_SCOPE.LOBBY)
        return
# okay decompyling res/scripts/client/gui/scaleform/daapi/view/lobby/techtree/sf_settings.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:26:19 EST

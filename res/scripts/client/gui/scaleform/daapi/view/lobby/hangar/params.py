# Embedded file name: scripts/client/gui/Scaleform/daapi/view/lobby/hangar/Params.py
from gui.Scaleform.daapi.view.meta.ParamsMeta import ParamsMeta
from CurrentVehicle import g_currentVehicle
from gui.shared import events
from gui.shared.utils import ItemsParameters
from gui.shared.event_bus import EVENT_BUS_SCOPE

class Params(ParamsMeta):

    def __init__(self):
        super(Params, self).__init__()

    def update(self):
        data = []
        if g_currentVehicle.isPresent():
            params = ItemsParameters.g_instance.getParameters(g_currentVehicle.item.descriptor)
            if params is not None:
                for p in params:
                    data.append({'text': p[0],
                     'param': p[1],
                     'selected': False})

        self.as_setValuesS(data)
        return

    def _populate(self):
        super(Params, self)._populate()
        self.addListener(events.LobbySimpleEvent.HIGHLIGHT_TANK_PARAMS, self.__onHighlightParams, EVENT_BUS_SCOPE.LOBBY)
        self.update()

    def __onHighlightParams(self, event):
        self.as_highlightParamsS(event.ctx.get('type', 'empty'))

    def _dispose(self):
        self.removeListener(events.LobbySimpleEvent.HIGHLIGHT_TANK_PARAMS, self.__onHighlightParams, EVENT_BUS_SCOPE.LOBBY)
        super(Params, self)._dispose()
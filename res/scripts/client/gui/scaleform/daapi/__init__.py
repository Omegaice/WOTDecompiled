from gui.Scaleform.framework import AppRef
from gui.Scaleform.framework.entities.View import View

class LobbySubView(View, AppRef):

    def __init__(self, backAlpha = 0.6):
        super(LobbySubView, self).__init__()
        self.gfx.backgroundAlpha = backAlpha

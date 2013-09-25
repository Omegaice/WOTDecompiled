from debug_utils import LOG_DEBUG
__author__ = 'd_trofimov'
from gui.Scaleform.framework.entities.DAAPIModule import DAAPIModule

class View(DAAPIModule):

    def __init__(self):
        super(View, self).__init__()
        self.__token = None
        self.__settings = None
        self.__uniqueName = None
        self.__canViewSkip = True
        return

    def __del__(self):
        LOG_DEBUG('View deleted:', self)

    def getSubContainerType(self):
        """
        Called by container manager. Should return container type of view sub-container, if it exists.
        Returns None by default
        Override in sub-classes if needed.
        """
        return None

    @property
    def token(self):
        return self.__token

    def setCanViewSkip(self, canViewSkip):
        self.__canViewSkip = canViewSkip

    def isCanViewSkip(self):
        return self.__canViewSkip

    def setToken(self, token):
        if token is not None:
            self.__token = token
        else:
            LOG_DEBUG('token can`t be None!')
        return

    @property
    def settings(self):
        return self.__settings

    def setSettings(self, settings):
        if settings is not None:
            self.__settings = settings
        else:
            LOG_DEBUG('settings can`t be None!')
        return

    @property
    def alias(self):
        return self.__settings.alias

    @property
    def uniqueName(self):
        return self.__uniqueName

    def setUniqueName(self, name):
        if name is not None:
            self.__uniqueName = name
        else:
            LOG_DEBUG('uniqueName can`t be None!')
        return

    def _dispose(self):
        super(View, self)._dispose()

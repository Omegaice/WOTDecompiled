# 2013.11.15 11:26:28 EST
# Embedded file name: scripts/client/gui/Scaleform/framework/entities/View.py
from debug_utils import LOG_DEBUG, LOG_ERROR
__author__ = 'd_trofimov'
from gui.Scaleform.framework.entities.DAAPIModule import DAAPIModule

class View(DAAPIModule):

    def __init__(self):
        super(View, self).__init__()
        self.__token = None
        self.__settings = None
        self.__uniqueName = None
        self.__canViewSkip = True
        from gui.Scaleform.framework import VIEW_SCOPE
        self.__scope = VIEW_SCOPE.DEFAULT
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

    def setCurrentScope(self, scope):
        from gui.Scaleform.framework import VIEW_SCOPE
        FOR_ALIAS = 'for ' + self.settings.alias + ' view.'
        if self.__settings is not None:
            if self.__settings.scope == VIEW_SCOPE.DYNAMIC:
                if scope != VIEW_SCOPE.DYNAMIC:
                    self.__scope = scope
                else:
                    raise Exception('View.__scope can`t be a VIEW_SCOPE.DYNAMIC value. This value might have only ' + 'settings.scope ' + FOR_ALIAS)
            else:
                raise Exception('You can not change a non-dynamic scope. Declare VIEW_SCOPE.DYNAMIC in settings ' + FOR_ALIAS)
        else:
            LOG_ERROR('You can not change a current scope, until unimplemented __settings ')
        return

    def getCurrentScope(self):
        return self.__scope

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
        from gui.Scaleform.framework import VIEW_SCOPE
        if settings is not None:
            self.__settings = settings
            if self.__settings.scope != VIEW_SCOPE.DYNAMIC:
                self.__scope = self.__settings.scope
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
# okay decompyling res/scripts/client/gui/scaleform/framework/entities/view.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:26:28 EST

# 2013.11.15 11:26:28 EST
# Embedded file name: scripts/client/gui/Scaleform/framework/managers/containers.py
import weakref, types
from Event import Event
from debug_utils import LOG_DEBUG, LOG_WARNING, LOG_ERROR
from gui.Scaleform.framework import VIEW_TYPE, VIEW_SCOPE
from gui.Scaleform.framework.entities.abstract.ContainerManagerMeta import ContainerManagerMeta

class IViewContainer(object):

    def add(self, pyView):
        raise NotImplementedError, 'IViewContainer.add must be implemented'

    def remove(self, pyView):
        raise NotImplementedError, 'IViewContainer.remove must be implemented'

    def clear(self):
        raise NotImplementedError, 'IViewContainer.clear must be implemented'

    def destroy(self):
        raise NotImplementedError, 'IViewContainer.destroy must be implemented'

    def getView(self, criteria = None):
        raise NotImplementedError, 'IViewContainer.getView must be implemented'

    def getViewCount(self):
        raise NotImplementedError, 'IViewContainer.getViewCount must be implemented'


class _DefaultContainer(IViewContainer):

    def __init__(self, manager):
        super(_DefaultContainer, self).__init__()
        self.__manager = manager
        self.__view = None
        return

    def add(self, pyView):
        if self.__view is not None:
            self.__manager.cleanUpDirtyViewsByScope(self.__view.settings.type, self.__view.alias)
            self.__view.destroy()
        pyView.onModuleDispose += self.__handleModuleDispose
        self.__view = pyView
        return True

    def remove(self, pyView):
        if self.__view == pyView:
            self.__view.onModuleDispose -= self.__handleModuleDispose
            self.__manager.as_hideS(self.__view.token)
            self.__view = None
        return

    def clear(self):
        global isHangarLoaded
        if self.__view is not None:
            subContainerType = self.__view.getSubContainerType()
            if subContainerType is not None:
                self.__manager.removeContainer(subContainerType)
            self.__view.onModuleDispose -= self.__handleModuleDispose
            self.__manager.as_hideS(self.__view.token)
            self.__view.destroy()
            if self.__view.alias == 'hangar':
                isHangarLoaded = False
            self.__view = None
        return

    def destroy(self):
        self.clear()
        self.__manager = None
        return

    def __handleModuleDispose(self, pyView):
        global isHangarLoaded
        subContainerType = pyView.getSubContainerType()
        if subContainerType is not None:
            self.__manager.removeContainer(subContainerType)
        if pyView.settings.alias == 'hangar':
            isHangarLoaded = False
        self.remove(pyView)
        return

    def getView(self, criteria = None):
        return self.__view

    def getViewCount(self):
        if self.__view is not None:
            return 1
        else:
            return 0


class POP_UP_CRITERIA(object):
    VIEW_ALIAS = 1
    UNIQUE_NAME = 2


class ExternalCriteria(object):

    def __init__(self, criteria = None):
        super(ExternalCriteria, self).__init__()
        self._criteria = criteria

    def find(self, name, obj):
        raise NotImplemented, 'ExternalCriteria.find must be implemented'


class _PopUpContainer(IViewContainer):

    def __init__(self, manager):
        super(_PopUpContainer, self).__init__()
        self.__manager = manager
        self.__popUps = {}

    def add(self, pyView):
        uniqueName = pyView.uniqueName
        if uniqueName in self.__popUps:
            LOG_WARNING('PopUp already exists', pyView, uniqueName)
            return False
        self.__popUps[uniqueName] = pyView
        pyView.onModuleDispose += self.__handleModuleDispose
        return True

    def remove(self, pyView):
        uniqueName = pyView.uniqueName
        if uniqueName in self.__popUps:
            popUp = self.__popUps.pop(uniqueName)
            popUp.onModuleDispose -= self.__handleModuleDispose
            self.__manager.as_hideS(popUp.token)
            LOG_DEBUG('PopUp has been successfully removed', pyView, uniqueName)
        else:
            LOG_WARNING('PopUp not found', pyView, uniqueName)

    def clear(self):
        while len(self.__popUps):
            _, popUp = self.__popUps.popitem()
            subContainerType = popUp.getSubContainerType()
            if subContainerType is not None:
                self.__manager.removeContainer(subContainerType)
            popUp.onModuleDispose -= self.__handleModuleDispose
            self.__manager.as_hideS(popUp.token)
            popUp.destroy()

        return

    def destroy(self):
        self.clear()
        self.__manager = None
        return

    def getView(self, criteria = None):
        popUp = None
        if criteria is not None:
            if type(criteria) is types.DictionaryType:
                popUp = self.__findByDictCriteria(criteria)
            elif isinstance(criteria, ExternalCriteria):
                popUp = self.__findByExCriteria(criteria)
            else:
                LOG_ERROR('Criteria is invalid', criteria)
        return popUp

    def getViewCount(self):
        return len(self.__popUps)

    def __findByDictCriteria(self, criteria):
        popUp = None
        if POP_UP_CRITERIA.UNIQUE_NAME in criteria:
            uniqueName = criteria[POP_UP_CRITERIA.UNIQUE_NAME]
            if uniqueName in self.__popUps:
                popUp = self.__popUps[uniqueName]
        elif POP_UP_CRITERIA.VIEW_ALIAS in criteria:
            viewAlias = criteria[POP_UP_CRITERIA.VIEW_ALIAS]
            popUps = filter(lambda popUp: popUp.settings.alias == viewAlias, self.__popUps.values())
            if len(popUps):
                popUp = popUps[0]
        return popUp

    def __findByExCriteria(self, criteria):
        popUp = None
        popUps = filter(lambda item: criteria.find(*item), self.__popUps.iteritems())
        if len(popUps):
            popUp = popUps[0][1]
        return popUp

    def __handleModuleDispose(self, pyView):
        subContainerType = pyView.getSubContainerType()
        if subContainerType is not None:
            self.__manager.removeContainer(subContainerType)
        self.remove(pyView)
        return


class ContainerManager(ContainerManagerMeta):
    onViewAddedToContainer = Event()
    __DESTROY_ORDER = (VIEW_TYPE.DEFAULT,
     VIEW_TYPE.LOBBY_SUB,
     VIEW_TYPE.WINDOW,
     VIEW_TYPE.DIALOG,
     VIEW_TYPE.WAITING,
     VIEW_TYPE.CURSOR,
     VIEW_TYPE.SERVICE_LAYOUT)

    def __init__(self, loader):
        super(ContainerManager, self).__init__()
        proxy = weakref.proxy(self)
        self.__containers = {VIEW_TYPE.DEFAULT: _DefaultContainer(proxy),
         VIEW_TYPE.CURSOR: _DefaultContainer(proxy),
         VIEW_TYPE.WAITING: _DefaultContainer(proxy),
         VIEW_TYPE.WINDOW: _PopUpContainer(proxy),
         VIEW_TYPE.DIALOG: _PopUpContainer(proxy),
         VIEW_TYPE.SERVICE_LAYOUT: _DefaultContainer(proxy)}
        self.__loadingTokens = {}
        self.__loadedTokens = {}
        self.__loader = loader
        self.__loader.onViewLoaded += self.__loader_onViewLoaded
        self.__currentRootScopeTarget = VIEW_SCOPE.VIEW + '/' + '**'
        self.__currentSubScopeTarget = VIEW_SCOPE.LOBBY_SUB + '/' + '**'

    def load(self, alias, name = None, *args, **kwargs):
        global isHangarLoaded
        if name is None:
            name = alias
        isViewExists = self.as_getViewS(name)
        if not isViewExists:
            if name == 'hangar':
                if isHangarLoaded:
                    return
                isHangarLoaded = True
            token = self.__loader.loadView(alias, name, *args, **kwargs)
            scope = self.as_getViewTypeByTokenS(token)
            self.__addLoadingToken(VIEW_SCOPE.VIEW, token)
            self.__addLoadingToken(VIEW_SCOPE.LOBBY_SUB, token)
        return

    def addContainer(self, containerType, token, container = None):
        result = True
        if containerType not in self.__containers:
            if container is None:
                self.__containers[containerType] = _DefaultContainer(weakref.proxy(self))
                self.as_registerContainerS(containerType, token)
            elif isinstance(container, IViewContainer):
                self.__containers[containerType] = container
                self.as_registerContainerS(containerType, token)
            else:
                LOG_ERROR('Container must be implemented IViewContainer', container)
                result = False
        else:
            LOG_ERROR('Container already registered', containerType)
            result = False
        return result

    def cleanUpDirtyViewsByScope(self, scope, viewAlias):
        scopeTarget = '%s/%s' % (scope, viewAlias)
        if scopeTarget in self.__loadedTokens:
            for token in self.__loadedTokens[scopeTarget]:
                incorrectViewName = self.as_getNameByTokenS(token)
                if incorrectViewName:
                    incorrectViewType = self.as_getViewTypeByTokenS(token)
                    if incorrectViewType not in (VIEW_TYPE.VIEW, VIEW_TYPE.LOBBY_SUB):
                        criteria = {POP_UP_CRITERIA.UNIQUE_NAME: incorrectViewName}
                        pyView = self.getView(incorrectViewType, criteria)
                        if pyView:
                            LOG_DEBUG('%s was automatically closed, because its scope has been destroyed.' % pyView.settings.alias)
                            pyView.destroy()
                        else:
                            LOG_WARNING('pyView is not found', scopeTarget)

            self.__loadedTokens.pop(scopeTarget, None)
        return

    def removeContainer(self, viewType):
        result = True
        if viewType in self.__containers:
            container = self.__containers.pop(viewType)
            container.destroy()
            self.as_unregisterContainerS(viewType)
        else:
            result = False
        return result

    def getContainer(self, viewType):
        if viewType in self.__containers:
            return self.__containers[viewType]
        else:
            return None

    def getView(self, viewType, criteria = None):
        view = None
        container = self.getContainer(viewType)
        if container is not None:
            view = container.getView(criteria=criteria)
        else:
            LOG_WARNING('Container for %s view is None!' % viewType)
            raise Exception('sdf')
        return view

    def isViewAvailable(self, viewType, criteria = None):
        container = self.getContainer(viewType)
        if container is not None:
            return container.getView(criteria=criteria) is not None
        else:
            return False
            return

    def closePopUps(self):
        for viewType in [VIEW_TYPE.DIALOG, VIEW_TYPE.WINDOW]:
            container = self.getContainer(viewType)
            if container is not None:
                container.clear()

        self.as_closePopUpsS()
        return

    def _dispose(self):
        if self.__loader is not None:
            self.__loader.onViewLoaded -= self.__loader_onViewLoaded
            self.__loader = None
        for viewType in self.__DESTROY_ORDER:
            if viewType in self.__containers:
                container = self.__containers.pop(viewType)
                container.destroy()

        if len(self.__containers):
            LOG_ERROR('No all containers are destructed.')
        self.__containers.clear()
        self.onViewAddedToContainer.clear()
        super(ContainerManager, self)._dispose()
        return

    def __addTokenTo(self, tokenDict, scope, token):
        if self.isViewAvailable(scope):
            rootView = self.getView(scope)
            if rootView is not None:
                rootViewName = rootView.alias
                scopeTarget = '%s/%s' % (scope, rootViewName)
                if scopeTarget not in tokenDict:
                    tokenDict[scopeTarget] = []
                tokenDict[scopeTarget].append(token)
        return

    def __removeTokenFrom(self, tokenDict, scope, scopeViewName, token):
        scopeTarget = '%s/%s' % (scope, scopeViewName)
        tokenDict[scopeTarget].remove(token)
        if len(tokenDict[scopeTarget]) == 0:
            tokenDict.pop(scopeTarget, None)
        return

    def __addLoadingToken(self, scope, token):
        self.__addTokenTo(self.__loadingTokens, scope, token)

    def __removeLoadingToken(self, scope, scopeViewName, token):
        self.__removeTokenFrom(self.__loadingTokens, scope, scopeViewName, token)

    def __addLoadedToken(self, scope, token):
        self.__addTokenTo(self.__loadedTokens, scope, token)

    def __removeLoadedToken(self, scope, scopeViewName, token):
        self.__removeTokenFrom(self.__loadedTokens, scope, scopeViewName, token)

    def __onScopeSwitched(self, oldScopeTarget, newScopeTarget):
        LOG_DEBUG('Scope switched: %s -> %s' % (oldScopeTarget, newScopeTarget))

    def __loader_onViewLoaded(self, pyView):
        viewType = pyView.settings.type
        viewScope = pyView.settings.scope
        scopeIsGlobal = False
        if viewScope == VIEW_SCOPE.DYNAMIC:
            viewScope = pyView.getCurrentScope()
        if viewScope == VIEW_SCOPE.GLOBAL:
            viewScope = VIEW_SCOPE.VIEW
            scopeIsGlobal = True
        if viewType is None:
            LOG_ERROR('Type of view is not defined', pyView.settings)
        if viewType in self.__containers:
            currentViewIsRoot = VIEW_TYPE.DEFAULT == viewType
            rootScopeView = self.getView(viewScope)
            if rootScopeView is not None and not scopeIsGlobal:
                rootScopeViewName = rootScopeView.alias
                scopeTarget = '%s/%s' % (viewScope, rootScopeViewName)
                if not scopeTarget in self.__loadingTokens:
                    if not currentViewIsRoot:
                        LOG_WARNING('View %s skipped, because current parent view %s has not loading threads.' % (pyView, rootScopeViewName))
                        return
                    loadingIsActual = pyView.token in self.__loadingTokens[scopeTarget]
                    loadingIsSkipable = pyView.isCanViewSkip()
                    if not loadingIsActual:
                        if not currentViewIsRoot and loadingIsSkipable:
                            LOG_WARNING('View %s skipped, because parent view has been disposed.' % pyView)
                            return
                        if loadingIsActual:
                            self.__removeLoadingToken(viewScope, rootScopeViewName, pyView.token)
                            self.__addLoadedToken(viewScope, pyView.token)
                    container = self.__containers[viewType]
                    if currentViewIsRoot:
                        self.closePopUps()
                    container.add(pyView) and self.as_showS(pyView.token, 0, 0)
                    pyView.create()
                    subContainerType = pyView.getSubContainerType()
                    subContainerType is not None and self.addContainer(subContainerType, pyView.token)
                LOG_DEBUG('View added to container', pyView)
                self.__detectScopeSwitching(pyView.settings.type, pyView.settings.alias)
                self.onViewAddedToContainer(container, pyView)
        else:
            LOG_ERROR('Type "%s" of view "%s" is not supported' % (viewType, pyView))
        return

    def __detectScopeSwitching(self, newViewType, newViewAlias):
        newScopeTarget = '%s/%s' % (newViewType, newViewAlias)
        if newViewType == VIEW_TYPE.VIEW:
            if newScopeTarget != self.__currentRootScopeTarget:
                self.__onScopeSwitched(self.__currentRootScopeTarget, newScopeTarget)
                self.__currentRootScopeTarget = newScopeTarget
        elif newViewType == VIEW_TYPE.LOBBY_SUB:
            if newScopeTarget != self.__currentSubScopeTarget:
                self.__onScopeSwitched(self.__currentSubScopeTarget, newScopeTarget)
                self.__currentSubScopeTarget = newScopeTarget


isHangarLoaded = False
# okay decompyling res/scripts/client/gui/scaleform/framework/managers/containers.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:26:29 EST

from gui.Scaleform.framework import VIEW_TYPE, AppRef
from gui.Scaleform.framework.managers.containers import ExternalCriteria
from tutorial import LOG_WARNING

class AttributeCriteria(ExternalCriteria):

    def __init__(self, dottedPath, value):
        super(AttributeCriteria, self).__init__((dottedPath.split('.'), value))

    def find(self, name, obj):
        path, value = self._criteria
        return self.__getValue(obj, path) == value

    def __getValue(self, popUp, path):
        nextAttr = popUp
        for attr in path:
            nextAttr = getattr(nextAttr, attr, None)

        return nextAttr


class ItemsManager(AppRef):

    def __init__(self):
        super(ItemsManager, self).__init__()

    def findTargetByCriteria(self, targetPath, valuePath, value):
        result = None
        if targetPath == VIEW_TYPE.DIALOG:
            result = self.__findDialog(valuePath, value)
        else:
            LOG_WARNING('Dialogs supported only')
        return result

    def __findDialog(self, path, value):
        result = None
        view = self.app.containerManager.getView(VIEW_TYPE.DIALOG, criteria=AttributeCriteria(path, value))
        if view is not None:
            result = (VIEW_TYPE.DIALOG, view.uniqueName)
        return result

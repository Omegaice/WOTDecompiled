

class BaseNotificationView:
    DEF_ICON_PATH = '../maps/icons/library/'

    def __init__(self, model):
        self._model = model

    def cleanUp(self):
        self._model = None
        return

    @classmethod
    def _formFullNotificationObject(cls, message, isPriority, notify, auxData):
        iconPropName = 'icon'
        if message.get(iconPropName) is not None:
            message[iconPropName] = cls._formIconPath(message.get(iconPropName))
        defIconPropName = 'defaultIcon'
        if message.get(defIconPropName) is not None:
            message[defIconPropName] = cls._formIconPath(message.get(defIconPropName))
        return {'message': message,
         'priority': isPriority,
         'notify': notify,
         'auxData': auxData}

    @classmethod
    def _formIconPath(cls, target_):
        return cls.DEF_ICON_PATH + target_ + '-1.png'

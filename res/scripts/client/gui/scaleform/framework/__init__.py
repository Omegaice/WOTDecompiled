# Embedded file name: scripts/client/gui/Scaleform/framework/__init__.py
from collections import namedtuple
from gui.Scaleform.framework.factories import EntitiesFactories, DAAPIModuleFactory, ViewFactory

class VIEW_TYPE(object):
    DEFAULT = 'view'
    LOBBY_SUB = 'lobbySubView'
    CURSOR = 'cursor'
    WAITING = 'waiting'
    WINDOW = 'window'
    DIALOG = 'dialog'
    COMPONENT = 'component'
    SERVICE_LAYOUT = 'serviceLayout'


class COMMON_VIEW_ALIAS(object):
    LOGIN = 'login'
    INTRO_VIDEO = 'introVideo'
    LOBBY = 'lobby'
    CURSOR = 'cursor'
    WAITING = 'waiting'


ViewSettings = namedtuple('ViewSettings', ('alias', 'clazz', 'url', 'type', 'event'))
GroupedViewSettings = namedtuple('GroupedViewSettings', ('alias', 'clazz', 'url', 'type', 'group', 'event'))
g_entitiesFactories = EntitiesFactories((DAAPIModuleFactory((VIEW_TYPE.COMPONENT,)), ViewFactory((VIEW_TYPE.DEFAULT,
  VIEW_TYPE.LOBBY_SUB,
  VIEW_TYPE.CURSOR,
  VIEW_TYPE.WAITING,
  VIEW_TYPE.WINDOW,
  VIEW_TYPE.DIALOG,
  VIEW_TYPE.SERVICE_LAYOUT))))

class AppRef(object):
    __reference = None

    @property
    def app(self):
        return AppRef.__reference

    @property
    def gfx(self):
        return AppRef.__reference.movie

    @classmethod
    def setReference(cls, app):
        cls.__reference = app

    @classmethod
    def clearReference(cls):
        cls.__reference = None
        return
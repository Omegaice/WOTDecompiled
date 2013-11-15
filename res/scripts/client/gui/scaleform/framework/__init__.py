# 2013.11.15 11:26:27 EST
# Embedded file name: scripts/client/gui/Scaleform/framework/__init__.py
from collections import namedtuple
from gui.Scaleform.framework.factories import EntitiesFactories, DAAPIModuleFactory, ViewFactory

class VIEW_TYPE(object):
    VIEW = 'view'
    LOBBY_SUB = 'lobbySubView'
    CURSOR = 'cursor'
    WAITING = 'waiting'
    WINDOW = 'window'
    DIALOG = 'dialog'
    COMPONENT = 'component'
    SERVICE_LAYOUT = 'serviceLayout'
    DEFAULT = VIEW


class VIEW_SCOPE(object):
    GLOBAL = 'global'
    DYNAMIC = 'dynamic'
    VIEW = VIEW_TYPE.VIEW
    LOBBY_SUB = VIEW_TYPE.LOBBY_SUB
    DEFAULT = VIEW


class COMMON_VIEW_ALIAS(object):
    LOGIN = 'login'
    INTRO_VIDEO = 'introVideo'
    LOBBY = 'lobby'
    CURSOR = 'cursor'
    WAITING = 'waiting'


ViewSettings = namedtuple('ViewSettings', ('alias', 'clazz', 'url', 'type', 'event', 'scope'))
GroupedViewSettings = namedtuple('GroupedViewSettings', ('alias', 'clazz', 'url', 'type', 'group', 'event', 'scope'))
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
# okay decompyling res/scripts/client/gui/scaleform/framework/__init__.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:26:27 EST

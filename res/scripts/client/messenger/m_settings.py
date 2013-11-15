# 2013.11.15 11:27:14 EST
# Embedded file name: scripts/client/messenger/m_settings.py
from collections import namedtuple, defaultdict
import Event
from account_helpers.AccountSettings import AccountSettings
from debug_utils import LOG_ERROR
from helpers.html.templates import XMLCollection
from messenger import doc_loaders
from messenger.doc_loaders.html_templates import MessageTemplates

class _ColorScheme(defaultdict):

    def __init__(self, names, default_factory = None, **kwargs):
        self.__colorsNames = names
        self.__current = names[0]
        super(_ColorScheme, self).__init__(default_factory, **kwargs)

    def __missing__(self, key):
        self[key] = value = dict(((k, 0) for k in self.__colorsNames))
        return value

    def getColorsNames(self):
        return self.__colorsNames

    def getDefColorName(self):
        return self.__colorsNames[0]

    def getColor(self, key):
        return self[key][self.__current]

    def getColors(self, key):
        return map(lambda name: self[key][name], self.__colorsNames)

    def setCurrent(self, name):
        result = False
        if name in self.__colorsNames and self.__current != name:
            self.__current = name
            result = True
        return result

    def getHexStr(self, key):
        return '{0:06X}'.format(self[key][self.__current])

    def iterColors(self):
        for key, colors in self.iteritems():
            yield (key, colors[self.__current])

    def iterHexs(self):
        for key, colors in self.iteritems():
            yield (key, '{0:06X}'.format(colors[self.__current]))


_ServiceChannelSettings = namedtuple('_ServiceChannelSettings', ('lifeTime', 'alphaSpeed', 'stackLength', 'padding'))

class _LobbySettings(object):
    __slots__ = ('serviceChannel', 'messageRawFormat', 'badWordFormat', '__messageFormats')

    def __init__(self):
        super(_LobbySettings, self).__init__()
        self.serviceChannel = _ServiceChannelSettings(5.0, 0, 5, 0)
        self.messageRawFormat = u'{0:>s} {1:>s} {2:>s}'
        self.badWordFormat = u'{0:>s}'
        self.__messageFormats = {}

    def getMessageFormat(self, key):
        try:
            return self.__messageFormats[key]
        except KeyError:
            LOG_ERROR('Message formatter not found', key)
            return self.messageRawFormat % {'user': '000000'}

    def _onSettingsLoaded(self, root):
        for key in ['groups', 'rosters']:
            colorScheme = root.getColorScheme(key)
            for name, userColor in colorScheme.iterHexs():
                if name == 'breaker':
                    timeColor = colorScheme.getHexStr('other')
                else:
                    timeColor = userColor
                self.__messageFormats[name] = self.messageRawFormat % {'user': userColor,
                 'time': timeColor}


_BattleMessageLifeCycle = namedtuple('_MessageInBattle', ('lifeTime', 'alphaSpeed'))

class _BattleSettings(object):
    __slots__ = ('messageLifeCycle', 'messageFormat', 'targetFormat', 'inactiveStateAlpha', 'hintText', 'toolTipText', 'receivers')

    def __init__(self):
        super(_BattleSettings, self).__init__()
        self.messageLifeCycle = _BattleMessageLifeCycle(5, 0)
        self.messageFormat = u'%(playerName)s : %(messageText)s'
        self.targetFormat = '%(target)s'
        self.inactiveStateAlpha = 100
        self.hintText = ''
        self.toolTipText = ''
        self.receivers = {}


_UserPrefs = namedtuple('_UserPrefs', ('version', 'datetimeIdx', 'enableOlFilter', 'enableSpamFilter', 'invitesFromFriendsOnly', 'storeReceiverInBattle'))

class MessengerSettings(object):
    __messageFormat = '<font color="#%(user)s">{0:>s}</font><font color="#%(user)s">{1:>s}</font> <font color="#%(message)s">{2:>s}</font>'
    __slots__ = ('__colorsSchemes', '__messageFormatters', '__eManager', 'lobby', 'battle', 'userPrefs', 'htmlTemplates', 'msgTemplates', 'onUserPreferencesUpdated', 'onColorsSchemesUpdated')

    def __init__(self):
        self.__colorsSchemes = {'groups': _ColorScheme(['default']),
         'rosters': _ColorScheme(['online', 'offline']),
         'battle/player': _ColorScheme(['default', 'colorBlind']),
         'battle/message': _ColorScheme(['default', 'colorBlind']),
         'battle/receiver': _ColorScheme(['default', 'colorBlind'])}
        self.lobby = _LobbySettings()
        self.battle = _BattleSettings()
        self.userPrefs = _UserPrefs(1, 2, True, False, False, False)
        self.htmlTemplates = XMLCollection('', '')
        self.msgTemplates = MessageTemplates('', '')
        self.__messageFormatters = {}
        self.__eManager = Event.EventManager()
        self.onUserPreferencesUpdated = Event.Event(self.__eManager)
        self.onColorsSchemesUpdated = Event.Event(self.__eManager)

    def init(self):
        doc_loaders.load(self)
        self.lobby._onSettingsLoaded(self)
        from account_helpers.SettingsCore import g_settingsCore
        g_settingsCore.onSettingsChanged += self.__accs_onSettingsChanged

    def fini(self):
        from account_helpers.SettingsCore import g_settingsCore
        g_settingsCore.onSettingsChanged -= self.__accs_onSettingsChanged
        self.__eManager.clear()
        self.__colorsSchemes.clear()
        self.__messageFormatters.clear()

    def update(self):
        if AccountSettings.getSettings('isColorBlind'):
            csName = 'colorBlind'
        else:
            csName = 'default'
        for colorScheme in self.__colorsSchemes.itervalues():
            colorScheme.setCurrent(csName)

    def getColorScheme(self, key):
        try:
            return self.__colorsSchemes[key]
        except KeyError:
            LOG_ERROR('Color scheme not found', key)
            return None

        return None

    def saveUserPreferences(self, data):
        if doc_loaders.user_prefs.flush(self, data):
            self.onUserPreferencesUpdated()

    def __accs_onSettingsChanged(self, diff):
        if 'isColorBlind' in diff:
            result = False
            for colorScheme in self.__colorsSchemes.itervalues():
                csName = 'colorBlind' if diff['isColorBlind'] else 'default'
                if colorScheme.setCurrent(csName):
                    result = True

            if result:
                self.onColorsSchemesUpdated()
# okay decompyling res/scripts/client/messenger/m_settings.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:27:14 EST

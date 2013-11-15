# 2013.11.15 11:27:10 EST
# Embedded file name: scripts/client/messenger/ext/__init__.py
import types
import constants
from messenger import g_settings
from messenger.ext import dictionaries
MESSENGER_OLDICT_FILE_PATH = 'text/messenger_oldictionary.xml'
MESSENGER_DOMAIN_FILE_PATH = 'text/messenger_dndictionary.xml'
g_dnDictionary = dictionaries.DomainNameDictionary.load(MESSENGER_DOMAIN_FILE_PATH)
if constants.SPECIAL_OL_FILTER:
    g_olDictionary = dictionaries.SpecialOLDictionary.load(MESSENGER_OLDICT_FILE_PATH)
else:
    g_olDictionary = dictionaries.BasicOLDictionary.load(MESSENGER_OLDICT_FILE_PATH)

def passCensor(text):
    if text is None:
        return u''
    else:
        if type(text) is not types.UnicodeType:
            text = unicode(text, 'utf-8')
        if g_settings.userPrefs.enableOlFilter:
            return g_olDictionary.searchAndReplace(text)
        return text
# okay decompyling res/scripts/client/messenger/ext/__init__.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:27:10 EST

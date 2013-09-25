# Embedded file name: scripts/client/gui/Scaleform/daapi/view/login/EULADispatcher.py
import ResMgr
from debug_utils import LOG_ERROR, LOG_WARNING, LOG_CURRENT_EXCEPTION
from helpers import getClientLanguage
from gui import VERSION_FILE_PATH, makeHtmlString, GUI_SETTINGS
from gui.shared.events import ShowWindowEvent, CloseWindowEvent
from gui.Scaleform.framework.entities.EventSystemEntity import EventSystemEntity
SHOW_LICENCE_TAG = 'showLicense'
EULA_TEMPLATES_FILE_PATH = 'gui/EULA_templates.xml'
EULA_FILE_PATH = 'text/EULA.xml'

class EULADispatcher(EventSystemEntity):

    def _populate(self):
        EventSystemEntity._populate(self)
        if self.__isShowLicense():
            isShowFullEULA = GUI_SETTINGS.eula.full
            if isShowFullEULA:
                self.__eulaText = self.__readEULAFull()
                if not len(self.__eulaText):
                    isShowFullEULA = False
            if not isShowFullEULA:
                self.__eulaText = self.__readEULAShort()
            if len(self.__eulaText):
                self.addListener(CloseWindowEvent.EULA_CLOSED, self.__onEulaClosed)
                self.fireEvent(ShowWindowEvent(ShowWindowEvent.SHOW_EULA, ctx={'isFull': isShowFullEULA,
                 'text': self.__eulaText}))

    def __onEulaClosed(self, event):
        if event.isAgree:
            self.__saveVersionFile()

    def __isShowLicense(self):
        dSection = ResMgr.openSection(VERSION_FILE_PATH)
        if dSection is None:
            LOG_ERROR('Can not open file:', VERSION_FILE_PATH)
            return False
        else:
            return bool(dSection.readInt(SHOW_LICENCE_TAG, 0))

    def __saveVersionFile(self):
        dSection = ResMgr.openSection(VERSION_FILE_PATH)
        if dSection is None:
            LOG_ERROR('Can not open file:', VERSION_FILE_PATH)
            self.__showLicense = False
            return
        else:
            dSection.writeInt(SHOW_LICENCE_TAG, 0)
            isReleaseVer = False
            try:
                f = open('version.xml', 'rb')
                f.close()
                isReleaseVer = True
            except IOError:
                pass

            f = open('version.xml' if isReleaseVer else VERSION_FILE_PATH, 'wb')
            f.write(dSection.asBinary)
            f.close()
            return

    def __readEULAShort(self):
        return makeHtmlString('html_templates:lobby/dialogs', 'eula', {'eulaURL': GUI_SETTINGS.eula.url.format(getClientLanguage())})

    def __readEULAFull(self):
        if not GUI_SETTINGS.eula.full:
            return ''
        else:
            dSection = ResMgr.openSection(EULA_FILE_PATH)
            text = []
            if dSection is None:
                LOG_WARNING('Can not open file:', EULA_FILE_PATH)
                self.__showLicense = False
                return ''
            try:
                processor = _LicenseXMLProcessor()
                for child in dSection.values():
                    result = processor.execute(child, result=[])
                    if len(result) > 0:
                        text.extend(result)

            except Exception:
                LOG_CURRENT_EXCEPTION()

            return ''.join(text)


class _TagTemplate(object):

    def __init__(self, template):
        self._template = template

    def execute(self, section, processor, result):
        result.append(self._template)


class _LinkTemplate(_TagTemplate):

    def execute(self, section, processor, result):
        name = section['name'].asWideString if section.has_key('name') else section.asWideString
        if section.has_key('url'):
            if section['url'].asWideString == '#eulaUrl':
                lng = getClientLanguage()
                url = GUI_SETTINGS.eula.url.format(lng)
            else:
                url = section['url'].asWideString
        else:
            url = section.asWideString
        result.append(self._template % (url, name))


class _TitleTemplate(_TagTemplate):

    def execute(self, section, processor, result):
        result.append(self._template % section.asWideString)


class _ContentTemplate(_TagTemplate):

    def execute(self, section, processor, result):
        values = section.values()
        if len(values) > 0:
            selfResult = []
            for tSection in values:
                processor.execute(tSection, processor, selfResult)

        else:
            selfResult = [section.asWideString]
        result.append(self._template % u''.join(selfResult))


class _ChapterTemplate(object):

    def __init__(self, titleTemplate, contentTemplate):
        self.__title = _TitleTemplate(titleTemplate)
        self.__content = _ContentTemplate(contentTemplate)

    def execute(self, section, processor, result):
        tSection = section['title']
        if tSection is not None:
            self.__title.execute(tSection, processor, result)
        cSection = section['content']
        if cSection is not None:
            self.__content.execute(cSection, processor, result)
        return


class _LicenseXMLProcessor(object):
    __templates = {}

    def __init__(self):
        self.__loadTemplates()

    def __loadTemplates(self):
        dSection = ResMgr.openSection(EULA_TEMPLATES_FILE_PATH)
        if dSection is None:
            LOG_ERROR('Can not open file:', EULA_TEMPLATES_FILE_PATH)
        for tagName, child in dSection.items():
            className = child.readString('class')
            if className is None:
                continue
            clazz = globals().get(className)
            if clazz is None:
                LOG_ERROR('Not found class:', clazz)
                continue
            args = []
            argsSection = child['args'] if child.has_key('args') else []
            for argSection in argsSection.values():
                arg = argSection.asString
                if len(arg) > 0:
                    args.append(arg)

            self.__templates[tagName] = clazz(*args)

        return

    def execute(self, section, processor = None, result = None):
        template = self.__templates.get(section.name)
        if result is None:
            result = []
        if template is not None:
            template.execute(section, self, result)
        else:
            result.append(section.asWideString)
        return result
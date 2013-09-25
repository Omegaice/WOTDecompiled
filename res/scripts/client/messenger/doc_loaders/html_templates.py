from helpers.html import translation as html_translation, templates

class _MessageTemplate(templates.Template):

    def __init__(self, source, data):
        super(_MessageTemplate, self).__init__({'message': source})
        self.data = data

    def _makeShowMore(self, data):
        original = self.data['showMore']
        return {'enabled': original['enabled'],
         'command': original['command'],
         'param': data if data else None}

    def format(self, ctx = None, data = None):
        vo = self.data.copy()
        vo['showMore'] = self._makeShowMore(data)
        vo['message'] = super(_MessageTemplate, self).format(ctx=ctx, sourceKey='message')
        return vo


class MessageTemplates(templates.XMLCollection):

    def __missing__(self, key):
        self[key] = value = _MessageTemplate(key, {})
        return value

    def _make(self, source):
        data = {'type': source.readString('type'),
         'icon': source.readString('icon'),
         'defaultIcon': source.readString('defaultIcon'),
         'filters': [],
         'showMore': {'enabled': False,
                      'command': None}}
        message = html_translation(source.readString('message'))
        section = source['filters']
        if section is None:
            section = {}
        for _, subSec in section.items():
            data['filters'].append({'name': subSec.readString('name'),
             'color': subSec.readString('color')})

        section = source['showMore']
        if section is not None:
            data['showMore'] = {'enabled': section.readBool('enabled'),
             'command': section.readString('command')}
        return _MessageTemplate(message, data)


def loadForMessage(_, section, settings):
    settings.msgTemplates.load(section=section)


def loadForOthers(_, section, settings):
    settings.htmlTemplates.load(section=section)

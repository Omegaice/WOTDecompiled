# Embedded file name: scripts/client/gui/Scaleform/framework/ToolTip.py
from gui.Scaleform.framework import AppRef
from debug_utils import LOG_DEBUG
from gui.Scaleform.framework.entities.abstract.ToolTipMgrMeta import ToolTipMgrMeta
from helpers import i18n

class ToolTip(ToolTipMgrMeta, AppRef):
    TOOLTIP_KIND = ['header', 'body', 'note']
    BLOCK_TAGS_MAP = {'HEADER': {'INFO': ["<font color='#FFCB65'><b>", '</b></font>'],
                'WARNING': ["<font color='#9b0202'><b>", '</b></font>']},
     'BODY': {},
     'NOTE': {'INFO': ["<font color='#777777'>", '</font>'],
              'WARNING': ["<font color='#777777'>", '</font>']}}

    def __init__(self):
        super(ToolTip, self).__init__()

    def onCreateTypedTooltip(self, type, args, stateType):
        from gui.Scaleform.daapi.settings.tooltips import TOOLTIPS
        if type in TOOLTIPS:
            item = TOOLTIPS[type]
            getDataMethod = item['method']
            tooltipType = item['tooltip']
            if getDataMethod is not None:
                tooltipData = getDataMethod(self.app.tooltipManager, *args)
                if tooltipData:
                    complexCondition = item['complex']
                    if complexCondition is not None:
                        if complexCondition(tooltipData['data']):
                            self.as_showS(tooltipData, tooltipType)
                        else:
                            tooltipId = '{HEADER}' + (tooltipData['data']['name'] + '{/HEADER}{BODY}') + (tooltipData['data']['descr'] + '{/BODY}')
                            self.__genComplexToolTip(tooltipId, stateType, self.__getDefaultTooltipType())
                    else:
                        self.as_showS(tooltipData, tooltipType)
            else:
                self.as_showS(args, tooltipType)
        return

    def onCreateComplexTooltip(self, tooltipId, stateType):
        self.__genComplexToolTip(tooltipId, stateType, self.__getDefaultTooltipType())

    def __getDefaultTooltipType(self):
        from gui.Scaleform.daapi.settings.tooltips import TOOLTIPS
        item = TOOLTIPS['default']
        return item['tooltip']

    def __genComplexToolTip(self, tooltipId, stateType, tooltipType):
        if not len(tooltipId):
            return
        tooltipIsKey = tooltipId[0] == '#'
        if tooltipIsKey:
            tooltipData = self.__getToolTipFromKey(tooltipId, stateType)
        else:
            tooltipData = self.__getToolTipFromText(tooltipId, stateType)
        if len(tooltipData):
            self.as_showS(tooltipData, self.__getDefaultTooltipType())

    def __getToolTipFromKey(self, tooltipId, stateType):
        result = ''
        for kind in self.TOOLTIP_KIND:
            contentKey = tooltipId + '/' + kind
            content = i18n.makeString(contentKey)
            subkey = contentKey[1:].split(':', 1)
            if content is not None and len(content) != 0 and content != subkey[1]:
                result += self.__getFormattedText(content, kind.upper(), stateType)

        return result

    def __getToolTipFromText(self, tooltipId, stateType):
        result = ''
        for tooltipKind in self.TOOLTIP_KIND:
            tooltipBlock = tooltipKind.upper()
            tags = {'open': '{' + tooltipBlock + '}',
             'close': '{/' + tooltipBlock + '}'}
            indicies = {'start': tooltipId.find(tags['open']),
             'end': tooltipId.find(tags['close'])}
            if indicies['start'] != -1 and indicies['end'] != -1:
                indicies['start'] += len(tags['open'])
                result += self.__getFormattedText(tooltipId[indicies['start']:indicies['end']], tooltipBlock, stateType)

        return result

    def __getFormattedText(self, text, block_type, format_type):
        if format_type is None:
            format_type = 'INFO'
        tags = self.__getTags(block_type, format_type)
        return tags[0] + text + tags[1] + '\n' + "<font size='1' > </font>" + '\n'

    def __getTags(self, block_type, format_type):
        blockTag = self.BLOCK_TAGS_MAP[block_type]
        if format_type in blockTag:
            formatTag = blockTag[format_type]
            return [formatTag[0], formatTag[1]]
        return ['', '']
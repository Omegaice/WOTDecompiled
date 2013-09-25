# Embedded file name: scripts/client/messenger/gui/Scaleform/view/FAQWindow.py
from debug_utils import LOG_ERROR
from gui.Scaleform.daapi.view.meta.WindowViewMeta import WindowViewMeta
from gui.Scaleform.framework.entities.View import View
from messenger.gui.Scaleform.meta.FAQWindowMeta import FAQWindowMeta
from messenger import g_settings
from helpers import i18n
import re
FAQ_BATCH_SIZE = 5

class FAQWindow(View, WindowViewMeta, FAQWindowMeta):
    __questionPattern = re.compile('^question_(\\d+)$')
    __answerFormat = 'answer_{0:d}'

    def __init__(self):
        super(FAQWindow, self).__init__()
        self.__faqDictLoaded = False

    def _populate(self):
        super(FAQWindow, self)._populate()
        self.updateData()

    def onWindowClose(self):
        self.destroy()

    def __buildFAQDict(self):
        if self.__faqDictLoaded:
            return
        else:
            self.__faqDict = {}
            translator = i18n.g_translators['faq']
            for key in translator._catalog.iterkeys():
                if len(key) > 0:
                    sreMatch = self.__questionPattern.match(key)
                    if sreMatch is not None and len(sreMatch.groups()) > 0:
                        number = int(sreMatch.groups()[0])
                        answer = translator.gettext(self.__answerFormat.format(number))
                        if answer is not None and len(answer) > 0:
                            self.__faqDict[number] = (translator.gettext(key), answer)
                        else:
                            LOG_ERROR('Answer %s is not found' % number)

            self.__faqDictLoaded = True
            return

    def updateData(self):
        self.__buildFAQDict()
        faq = sorted(self.__faqDict.items(), cmp=lambda item, other: cmp(item[0], other[0]))
        formatHtml = g_settings.htmlTemplates.format
        batch = []
        if len(faq) > 0:
            number, (question, answer) = faq[0]
            batch = [formatHtml('firstFAQItem', ctx={'number': number,
              'question': question,
              'answer': answer})]
        for number, (question, answer) in faq[1:]:
            if FAQ_BATCH_SIZE > len(batch):
                self.as_appendTextS(''.join(batch))
                batch = []
            batch.append(formatHtml('nextFAQItem', ctx={'number': number,
             'question': question,
             'answer': answer}))

        if len(batch) > 0:
            self.as_appendTextS(''.join(batch))
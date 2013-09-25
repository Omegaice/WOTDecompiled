import BigWorld
import Event
from gui.ClientUpdateManager import g_clientUpdateManager
from helpers import i18n, time_utils
from gui import makeHtmlString
from gui.shared import events, g_itemsCache
from gui.Scaleform.framework import AppRef
from gui.Scaleform.locale.DIALOGS import DIALOGS
I18N_PRICE_KEY = '{0:>s}/messagePrice'
I18N_TITLE_KEY = '{0:>s}/title'
I18N_MESSAGE_KEY = '{0:>s}/message'
I18N_CANCEL_KEY = '{0:>s}/cancel'
I18N_SUBMIT_KEY = '{0:>s}/submit'

class DIALOG_BUTTON_ID(object):
    SUBMIT = 'submit'
    CLOSE = 'close'


class IDialogMeta(object):

    def getEventType(self):
        raise NotImplementedError, 'Dialog event type must be specified'


class ISimpleDialogButtonsMeta(object):

    def getLabels(self):
        pass


class ISimpleDialogMeta(IDialogMeta):

    def getTitle(self):
        return ''

    def getMessage(self):
        return ''

    def getButtonLabels(self):
        return []

    def canViewSkip(self):
        return True


class InfoDialogButtons(ISimpleDialogButtonsMeta):

    def __init__(self, close):
        super(InfoDialogButtons, self).__init__()
        self._close = close

    def getLabels(self):
        return [{'id': DIALOG_BUTTON_ID.CLOSE,
          'label': self._close,
          'focused': True}]


class ConfirmDialogButtons(InfoDialogButtons):

    def __init__(self, submit, close):
        super(ConfirmDialogButtons, self).__init__(close)
        self._submit = submit

    def getLabels(self):
        return [{'id': DIALOG_BUTTON_ID.SUBMIT,
          'label': self._submit,
          'focused': True}, {'id': DIALOG_BUTTON_ID.SUBMIT,
          'label': self._close,
          'focused': False}]


class I18nInfoDialogButtons(ISimpleDialogButtonsMeta):

    def __init__(self, i18nKey = 'common'):
        super(I18nInfoDialogButtons, self).__init__()
        self._i18nKey = i18nKey

    def getLabels(self):
        return [{'id': DIALOG_BUTTON_ID.CLOSE,
          'label': DIALOGS.all(I18N_CANCEL_KEY.format(self._i18nKey)),
          'focused': True}]


class I18nConfirmDialogButtons(I18nInfoDialogButtons):

    def __init__(self, i18nKey = 'common', focusedIndex = None):
        super(I18nInfoDialogButtons, self).__init__()
        self._i18nKey = i18nKey
        self._focusedIndex = focusedIndex

    def getLabels(self):
        return [self.__getButtonInfoObject(DIALOG_BUTTON_ID.SUBMIT, DIALOGS.all(I18N_SUBMIT_KEY.format(self._i18nKey)), self._focusedIndex == DIALOG_BUTTON_ID.SUBMIT if self._focusedIndex is not None else True), self.__getButtonInfoObject(DIALOG_BUTTON_ID.CLOSE, DIALOGS.all(I18N_CANCEL_KEY.format(self._i18nKey)), self._focusedIndex == DIALOG_BUTTON_ID.CLOSE if self._focusedIndex is not None else False)]

    def __getButtonInfoObject(self, id, label, focused):
        return {'id': id,
         'label': label,
         'focused': focused}


class SimpleDialogMeta(ISimpleDialogMeta):

    def __init__(self, title = None, message = None, buttons = None):
        super(SimpleDialogMeta, self).__init__()
        self._title = title
        self._message = message
        self._buttons = buttons

    def getTitle(self):
        return self._title

    def getMessage(self):
        return self._message

    def getButtonLabels(self):
        result = []
        if self._buttons is not None:
            result = self._buttons.getLabels()
        return result

    def getEventType(self):
        return events.ShowDialogEvent.SHOW_SIMPLE_DLG

    def getCallbackWrapper(self, callback):
        return callback

    def canViewSkip(self):
        return True


class I18nDialogMeta(SimpleDialogMeta):

    def __init__(self, key, buttons, titleCtx = None, messageCtx = None, meta = None):
        super(I18nDialogMeta, self).__init__()
        self._key = key
        self._titleCtx = titleCtx if titleCtx is not None else {}
        self._messageCtx = messageCtx if messageCtx is not None else {}
        self._buttons = buttons
        self._meta = meta
        return

    def getTitle(self):
        result = None
        if self._meta is not None:
            result = self._meta.getTitle()
        if result is None or not len(result):
            result = self._makeString(I18N_TITLE_KEY.format(self._key), self._titleCtx)
        return result

    def getMessage(self):
        result = None
        if self._meta is not None:
            result = self._meta.getMessage()
        if result is None or not len(result):
            result = self._makeString(I18N_MESSAGE_KEY.format(self._key), self._messageCtx)
        return result

    def getButtonLabels(self):
        labels = []
        if self._buttons is not None:
            labels = self._buttons.getLabels()
        elif self._meta is not None:
            labels = self._meta.getButtonLabels()
        return labels

    def _makeString(self, key, ctx):
        return i18n.makeString(DIALOGS.all(key), **ctx)


class I18nInfoDialogMeta(I18nDialogMeta):

    def __init__(self, key, titleCtx = None, messageCtx = None, meta = None):
        buttons = I18nInfoDialogButtons(key)
        super(I18nInfoDialogMeta, self).__init__(key, buttons, titleCtx, messageCtx, meta)


class I18nConfirmDialogMeta(I18nDialogMeta):

    def __init__(self, key, titleCtx = None, messageCtx = None, meta = None, focusedID = None):
        buttons = I18nConfirmDialogButtons(key, focusedID)
        super(I18nConfirmDialogMeta, self).__init__(key, buttons, titleCtx, messageCtx, meta)


class DismissTankmanDialogMeta(I18nConfirmDialogMeta):

    def __init__(self, key, tankman = None, focusedID = None):
        super(DismissTankmanDialogMeta, self).__init__(key, None, None, None, focusedID)
        self.__tankman = tankman
        return

    def getEventType(self):
        return events.ShowDialogEvent.SHOW_DISMISS_TANKMAN_DIALOG

    def getTankman(self):
        return self.__tankman


class IconDialogMeta(I18nConfirmDialogMeta):

    def __init__(self, key, titleCtx = None, messageCtx = None, meta = None, focusedID = None):
        super(IconDialogMeta, self).__init__(key, titleCtx, messageCtx, meta, focusedID)

    def getEventType(self):
        return events.ShowDialogEvent.SHOW_ICON_DIALOG

    def getIcon(self):
        result = None
        if self._meta is not None:
            result = self._meta.getIcon()
        if result is None or not len(result):
            result = self._messageCtx.get('icon')
        return result


class IconPriceDialogMeta(IconDialogMeta):

    def __init__(self, key, titleCtx = None, messageCtx = None, meta = None, focusedID = None):
        super(IconPriceDialogMeta, self).__init__(key, titleCtx, messageCtx, meta, focusedID)
        self._operationPrice = self.__calcMessagePrice()

    def __calcMessagePrice(self):
        result = None
        if self._meta is not None:
            result = self._meta.getMessagePrice()
        if result is None or not len(result):
            result = self._messageCtx.get('price')
        return result

    def getEventType(self):
        return events.ShowDialogEvent.SHOW_ICON_PRICE_DIALOG

    def getMessagePrice(self):
        return self._operationPrice


class DestroyDeviceDialogMeta(IconDialogMeta):

    def __init__(self, key, titleCtx = None, messageCtx = None, meta = None, focusedID = None):
        super(DestroyDeviceDialogMeta, self).__init__(key, titleCtx, messageCtx, meta, focusedID)

    def getEventType(self):
        return events.ShowDialogEvent.SHOW_DESTROY_DEVICE_DIALOG


class DemountDeviceDialogMeta(IconPriceDialogMeta):
    DISMANTLE_DEVICE_PATH = '../maps/icons/modules/dismantleDevice.png'

    def __init__(self, key, titleCtx = None, messageCtx = None, meta = None, focusedID = None):
        super(DemountDeviceDialogMeta, self).__init__(key, titleCtx, messageCtx, meta, focusedID)
        self.onConfirmationStatusChnaged = Event.Event()
        self.__userGoldAmount = g_itemsCache.items.stats.gold
        self.__isOperationAllowed = False
        self.__checkIsOperationAllowed()
        g_clientUpdateManager.addCallbacks({'stats.gold': self.__goldChangeHandler,
         'shop.paidRemovalCost': self.__paidRemovalCostChangeHandler})

    @property
    def isOperationAllowed(self):
        return self.__isOperationAllowed

    def getIcon(self):
        return self.DISMANTLE_DEVICE_PATH

    def __goldChangeHandler(self, gold):
        self.__userGoldAmount = gold
        self.__checkIsOperationAllowed()

    def __paidRemovalCostChangeHandler(self, paidRemovalCost):
        self._operationPrice = paidRemovalCost
        self.__checkIsOperationAllowed()

    def __checkIsOperationAllowed(self):
        self.__isOperationAllowed = self.__userGoldAmount >= self._operationPrice
        self.onConfirmationStatusChnaged(self.__isOperationAllowed)

    def getEventType(self):
        return events.ShowDialogEvent.SHOW_DEMOUNT_DEVICE_DIALOG

    def dispose(self):
        self.onConfirmationStatusChnaged.clear()
        g_clientUpdateManager.removeObjectCallbacks(self)


class HtmlMessageDialogMeta(SimpleDialogMeta):

    def __init__(self, path, key, ctx = None):
        super(HtmlMessageDialogMeta, self).__init__()
        self._path = path
        self._key = key
        self._ctx = ctx

    def getTitle(self):
        return None

    def getMessage(self):
        return makeHtmlString(self._path, self._key, ctx=self._ctx)


class DisconnectMeta(I18nInfoDialogMeta, AppRef):

    def __init__(self, reason = None, isBan = False, expiryTime = None):
        super(DisconnectMeta, self).__init__('disconnected')
        self.reason = reason
        self.isBan = isBan
        self.expiryTime = expiryTime
        if hasattr(BigWorld.player(), 'setForcedGuiControlMode'):
            BigWorld.player().setForcedGuiControlMode(True)

    def getCallbackWrapper(self, callback):

        def wrapper(args):
            self.app.logoff()
            callback(args)

        return wrapper

    def getMessage(self):
        formatArgs = {'reason': '',
         'expiryTime': ''}
        if self.reason:
            formatArgs['reason'] = i18n.makeString(DIALOGS.DISCONNECTED_REASON, i18n.makeString(self.reason))
        if self.expiryTime:
            expiryTime = time_utils.makeLocalServerTime(int(self.expiryTime))
            formatArgs['expiryTime'] = '%s %s' % (BigWorld.wg_getLongDateFormat(expiryTime), BigWorld.wg_getLongTimeFormat(expiryTime))
        key = DIALOGS.DISCONNECTED_MESSAGEKICK
        if self.isBan:
            key = DIALOGS.DISCONNECTED_MESSAGEBANPERIOD if self.expiryTime else DIALOGS.DISCONNECTED_MESSAGEBAN
        return i18n.makeString(key, **formatArgs)

    def canViewSkip(self):
        return False

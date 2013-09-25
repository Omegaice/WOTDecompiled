# Embedded file name: scripts/client/messenger/gui/Scaleform/view/BattleChannelView.py
import weakref
from debug_utils import LOG_DEBUG
from gui.Scaleform.CommandArgsParser import CommandArgsParser
from gui.Scaleform.windows import UIInterface
from messenger import g_settings
from messenger.gui.Scaleform import BTMS_COMMANDS
from messenger.m_constants import BATTLE_CHANNEL

class BattleChannelView(UIInterface):
    _lastReceiver = BATTLE_CHANNEL.TEAM[1]

    def __init__(self, receiver):
        super(BattleChannelView, self).__init__()
        self._receiver = receiver
        self._channelID = 0
        self._controller = lambda : None

    def populateUI(self, proxy):
        super(BattleChannelView, self).populateUI(proxy)
        self.uiHolder.addExternalCallbacks({BTMS_COMMANDS.CheckCooldownPeriod(): self.__onCheckCooldownPeriod,
         BTMS_COMMANDS.SendMessage(): self.__onSendChannelMessage,
         BTMS_COMMANDS.ReceiverChanged(): self.__onReceiverChanged})
        controller = self._controller()
        if controller and controller.getChannel().isJoined():
            self.setJoined()

    def dispossessUI(self):
        if self.uiHolder:
            self.uiHolder.removeExternalCallback(BTMS_COMMANDS.CheckCooldownPeriod(), self.__onCheckCooldownPeriod)
            self.uiHolder.removeExternalCallback(BTMS_COMMANDS.SendMessage(), self.__onSendChannelMessage)
            self.uiHolder.removeExternalCallback(BTMS_COMMANDS.ReceiverChanged(), self.__onReceiverChanged)
        super(BattleChannelView, self).dispossessUI()

    @classmethod
    def resetReceiver(cls):
        if not g_settings.userPrefs.storeReceiverInBattle:
            cls._lastReceiver = BATTLE_CHANNEL.TEAM[1]

    def setController(self, controller):
        channel = controller.getChannel()
        self._controller = weakref.ref(controller)
        self._channelID = channel.getID()
        if channel.isJoined():
            self.setJoined()

    def removeController(self):
        self._controller = lambda : None
        self._channelID = 0

    def setJoined(self):
        args = self.getRecvConfig()[:]
        args.insert(0, self._channelID)
        self.__flashCall(BTMS_COMMANDS.JoinToChannel(), args)

    def addMessage(self, message, isCurrentPlayer = False):
        self.__flashCall(BTMS_COMMANDS.ReceiveMessage(), [self._channelID, message, isCurrentPlayer])

    def getRecvConfig(self):
        config = ['', 0, False]
        receivers = g_settings.battle.receivers
        if self._receiver in receivers:
            color = g_settings.getColorScheme('battle/receiver').getHexStr(self._receiver)
            receiver = receivers[self._receiver]._asdict()
            byDefault = False
            if g_settings.userPrefs.storeReceiverInBattle:
                byDefault = self._receiver == BattleChannelView._lastReceiver
            config = [receiver['label'] % color, receiver['order'], byDefault]
            config.extend(receiver['modifiers'])
        return config

    def __flashCall(self, funcName, args = None):
        if self.uiHolder:
            self.uiHolder.call(funcName, args)

    def __flashRespond(self, args = None):
        self.uiHolder.respond(args)

    def __onReceiverChanged(self, *args):
        parser = CommandArgsParser(self.__onReceiverChanged.__name__, 1, [long])
        channelID, = parser.parse(*args)
        if self._channelID == channelID:
            LOG_DEBUG('BattleChannelView.__onReceiverChanged', self._receiver)
            BattleChannelView._lastReceiver = self._receiver

    def __onCheckCooldownPeriod(self, *args):
        controller = self._controller()
        if controller is None:
            return
        else:
            parser = CommandArgsParser(self.__onCheckCooldownPeriod.__name__, 1, [long])
            channelID, = parser.parse(*args)
            if channelID == self._channelID:
                LOG_DEBUG('BattleChannelView.__onCheckCooldownPeriod', channelID)
                result, errorMsg = controller.canSendMessage()
                parser.addArgs([channelID, result])
                self.__flashRespond(parser.args())
                if not result:
                    message = g_settings.htmlTemplates.format('battleErrorMessage', ctx={'error': errorMsg})
                    self.__flashCall(BTMS_COMMANDS.ReceiveMessage(), [channelID, message, False])
            return

    def __onSendChannelMessage(self, *args):
        controller = self._controller()
        if controller is None:
            return
        else:
            parser = CommandArgsParser(self.__onSendChannelMessage.__name__, 2, [long])
            channelID, rawMsgText = parser.parse(*args)
            if self._channelID == channelID:
                LOG_DEBUG('BattleChannelView.__onSendChannelMessage', channelID)
                controller.sendMessage(rawMsgText)
            return
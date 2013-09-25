# Embedded file name: scripts/client/messenger/proto/bw/battle_chat_cmd.py
from chat_shared import CHAT_COMMANDS
from debug_utils import LOG_ERROR
from gui.BattleContext import g_battleContext
from helpers import i18n
from messenger import g_settings
from messenger.m_constants import PROTO_TYPE
from messenger.proto.bw.wrappers import ChatActionWrapper
from messenger.proto.entities import ChatCommand
from messenger.storage import storage_getter
_PUBLIC_ADR_CMD_INDEXES = (CHAT_COMMANDS.ATTACKENEMY.index(),
 CHAT_COMMANDS.SUPPORTMEWITHFIRE.index(),
 CHAT_COMMANDS.POSITIVE.index(),
 CHAT_COMMANDS.NEGATIVE.index(),
 CHAT_COMMANDS.RELOADINGGUN.index(),
 CHAT_COMMANDS.HELPME.index())
_PRIVATE_ADR_CMD_INDEXES = (CHAT_COMMANDS.TURNBACK.index(),
 CHAT_COMMANDS.FOLLOWME.index(),
 CHAT_COMMANDS.HELPMEEX.index(),
 CHAT_COMMANDS.STOP.index())
_VEHICLE_TARGET_CMD_INDEXES = (CHAT_COMMANDS.ATTACKENEMY.index(),
 CHAT_COMMANDS.TURNBACK.index(),
 CHAT_COMMANDS.FOLLOWME.index(),
 CHAT_COMMANDS.HELPMEEX.index(),
 CHAT_COMMANDS.SUPPORTMEWITHFIRE.index(),
 CHAT_COMMANDS.STOP.index())
_SHOW_MARKER_FOR_RECEIVER_CMD_INDEXES = (CHAT_COMMANDS.ATTACKENEMY.index(), CHAT_COMMANDS.SUPPORTMEWITHFIRE.index())

def makeDecorator(commandData, playerVehID):
    return ChatCommandDecorator(commandData, playerVehID)


class ChatCommandDecorator(ChatCommand):
    __slots__ = ('_chatAction', '_playerVehID', '_cmdArgs')

    def __init__(self, commandData, playerVehID):
        super(ChatCommandDecorator, self).__init__()
        self._chatAction = ChatActionWrapper(**dict(commandData))
        self._playerVehID = playerVehID
        self._cmdArgs = ()

    def getID(self):
        return self._chatAction.channel

    def getProtoType(self):
        return PROTO_TYPE.BW

    def getProtoData(self):
        return self._chatAction

    def getCommandText(self):
        index = self.getCommandIndex()
        command = CHAT_COMMANDS[index]
        if command is None:
            LOG_ERROR('Chat command not found', self._chatAction)
            return ''
        else:
            if command.argsCnt > 0:
                if index == CHAT_COMMANDS.ATTENTIONTOCELL.index():
                    text = self._makeMinimapCommandMessage(command)
                elif index in _VEHICLE_TARGET_CMD_INDEXES:
                    text = self._makeTargetedCommandMessage(command)
                else:
                    LOG_ERROR('Chat command is not supported', command.name())
                    text = ''
            else:
                text = i18n.makeString(command.msgText)
            return unicode(text, 'utf-8', errors='ignore')

    def getSenderID(self):
        return self._chatAction.originator

    def getCommandIndex(self):
        return self._chatAction.data[0]

    def getFirstTargetID(self):
        data = self._chatAction.data
        if len(data) > 1:
            return data[1]
        return 0

    def getSecondTargetID(self):
        data = self._chatAction.data
        if len(data) > 2:
            return data[2]
        return 0

    def getVehMarker(self, mode = None, vehicle = None):
        command = CHAT_COMMANDS[self.getCommandIndex()]
        result = ''
        if command is None:
            LOG_ERROR('Chat command not found', self._chatAction)
        else:
            result = command.get('vehMarker', defval='')
        if vehicle:
            mode = 'SPG' if 'SPG' in vehicle['vehicleType'].type.tags else ''
        if mode:
            result = '{0:>s}{1:>s}'.format(result, mode)
        return result

    def getVehMarkers(self, vehicle = None):
        mode = ''
        if vehicle:
            mode = 'SPG' if 'SPG' in vehicle['vehicleType'].type.tags else ''
        return (self.getVehMarker(mode=mode), 'attackSender{0:>s}'.format(mode))

    def getSoundEventName(self):
        return 'chat_shortcut_common_fx'

    def setCmdArgs(self, *args):
        self._cmdArgs = args

    def isIgnored(self):
        user = storage_getter('users')().getUser(self.getSenderID())
        if user:
            return user.isIgnored()
        return False

    def isPrivate(self):
        return self.getCommandIndex() in _PRIVATE_ADR_CMD_INDEXES

    def isPublic(self):
        return self.getCommandIndex() in _PUBLIC_ADR_CMD_INDEXES

    def isReceiver(self):
        return self.getFirstTargetID() == self._playerVehID

    def isSender(self):
        user = storage_getter('users')().getUser(self.getSenderID())
        if user:
            return user.isCurrentPlayer()
        return False

    def showMarkerForReceiver(self):
        return self.getCommandIndex() in _SHOW_MARKER_FOR_RECEIVER_CMD_INDEXES

    def _makeMinimapCommandMessage(self, command):
        return i18n.makeString(command.msgText, *self._cmdArgs)

    def _makeTargetedCommandMessage(self, command):
        target = g_battleContext.getFullPlayerName(vID=self.getFirstTargetID())
        text = command.msgText
        if self.isReceiver():
            target = g_settings.battle.targetFormat % {'target': target}
        return i18n.makeString(text, target)
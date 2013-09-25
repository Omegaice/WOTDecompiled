# Embedded file name: scripts/client/messenger/gui/Scaleform/BattleEntry.py
import Keys
import VOIP
from constants import CHAT_MESSAGE_MAX_LENGTH_IN_BATTLE
from debug_utils import LOG_DEBUG, LOG_ERROR, LOG_CURRENT_EXCEPTION
from gui.Scaleform.CommandArgsParser import CommandArgsParser
from gui.shared import g_eventBus, EVENT_BUS_SCOPE
from gui.shared.events import MessengerEvent
from messenger import g_settings
from messenger.formatters.users_messages import getUserRosterChangedMessage
from messenger.gui.Scaleform.channels import bw_battle_controllers
from messenger.gui.Scaleform.view.BattleChannelView import BattleChannelView
from messenger.m_constants import BATTLE_CHANNEL, PROTO_TYPE
from messenger.gui.interfaces import IGUIEntry
from messenger.gui.Scaleform import BTMS_COMMANDS, channels
from messenger.proto import proto_getter
from messenger.proto.bw.entities import BWChannelLightEntity
from messenger.proto.events import g_messengerEvents
from messenger.storage import storage_getter

class BattleEntry(IGUIEntry):

    def __init__(self):
        self.__ui = None
        self.__focused = False
        self.__initialized = 0
        self.__channelsCtrl = None
        self.__views = []
        return

    @storage_getter('channels')
    def channelsStorage(self):
        return None

    @proto_getter(PROTO_TYPE.BW)
    def proto(self):
        return None

    @property
    def channelsCtrl(self):
        return self.__channelsCtrl

    def populateUI(self, parentUI):
        self.__ui = parentUI
        self.__ui.addExternalCallbacks({BTMS_COMMANDS.PopulateUI(): self.__onPopulateUI,
         BTMS_COMMANDS.ChangeFocus(): self.__onChangeFocus,
         BTMS_COMMANDS.AddToFriends(): self.__onAddToFriends,
         BTMS_COMMANDS.RemoveFromFriends(): self.__onRemoveFromFriends,
         BTMS_COMMANDS.AddToIgnored(): self.__onAddToIgnored,
         BTMS_COMMANDS.RemoveFromIgnored(): self.__onRemoveFromIgnored,
         BTMS_COMMANDS.AddMuted(): self.__onSetMuted,
         BTMS_COMMANDS.RemoveMuted(): self.__onUnsetMuted})
        self.__flashCall(BTMS_COMMANDS.RefreshUI())
        for view in self.__views:
            view.populateUI(parentUI)

        if self.__initialized is BATTLE_CHANNEL.INITIALIZED:
            self.enable()

    def dispossessUI(self):
        self.__flashCall(BTMS_COMMANDS.ClearMessages())
        if self.__ui:
            self.__ui.removeExternalCallbacks(BTMS_COMMANDS.PopulateUI(), BTMS_COMMANDS.CheckCooldownPeriod(), BTMS_COMMANDS.SendMessage(), BTMS_COMMANDS.ChangeFocus(), BTMS_COMMANDS.AddToFriends(), BTMS_COMMANDS.RemoveFromFriends(), BTMS_COMMANDS.AddToIgnored(), BTMS_COMMANDS.RemoveFromIgnored(), BTMS_COMMANDS.AddMuted(), BTMS_COMMANDS.RemoveMuted())
        while len(self.__views):
            self.__views.pop().dispossessUI()

        self.__ui = None
        return

    def enable(self):
        import BattleReplay
        if BattleReplay.g_replayCtrl.isPlaying:
            return
        self.__flashCall(BTMS_COMMANDS.ChannelsInit())

    def show(self):
        g_messengerEvents.channels.onMessageReceived += self.__me_onMessageReceived
        g_messengerEvents.channels.onCommandReceived += self.__me_onCommandReceived
        g_messengerEvents.users.onUserRosterChanged += self.__me_onUsersRosterChanged
        g_messengerEvents.onServerErrorReceived += self.__me_onServerErrorReceived
        g_settings.onUserPreferencesUpdated += self.__ms_onUserPreferencesUpdated
        g_settings.onColorsSchemesUpdated += self.__ms_onColorsSchemesUpdated
        self.__initialized = 0
        g_eventBus.addListener(MessengerEvent.BATTLE_CHANNEL_CTRL_INITED, self.__handleChannelControllerInited, scope=EVENT_BUS_SCOPE.BATTLE)
        self.__channelsCtrl = channels.BattleControllers()
        controllers = self.__channelsCtrl.init()
        for controller in controllers:
            controller.activate()

    def close(self, nextScope):
        g_messengerEvents.channels.onMessageReceived -= self.__me_onMessageReceived
        g_messengerEvents.channels.onCommandReceived -= self.__me_onCommandReceived
        g_messengerEvents.users.onUserRosterChanged -= self.__me_onUsersRosterChanged
        g_messengerEvents.onServerErrorReceived -= self.__me_onServerErrorReceived
        g_settings.onUserPreferencesUpdated -= self.__ms_onUserPreferencesUpdated
        g_settings.onColorsSchemesUpdated -= self.__ms_onColorsSchemesUpdated
        self.dispossessUI()
        BattleChannelView.resetReceiver()
        self.__initialized = 0
        if self.__channelsCtrl is not None:
            self.__channelsCtrl.clear()
            self.__channelsCtrl = None
        g_eventBus.removeListener(MessengerEvent.BATTLE_CHANNEL_CTRL_INITED, self.__handleChannelControllerInited, scope=EVENT_BUS_SCOPE.BATTLE)
        return

    def invoke(self, method, *args, **kwargs):
        if method in ('populateUI', 'dispossessUI'):
            try:
                getattr(self, method)(*args, **kwargs)
            except TypeError:
                LOG_CURRENT_EXCEPTION()

        else:
            LOG_ERROR('Method is not specific', method)

    def addClientMessage(self, message, isCurrentPlayer = False):
        self.__flashCall(BTMS_COMMANDS.ReceiveMessage(), [0, message, isCurrentPlayer])

    def isEditing(self, event):
        return self.__focused and event.key != Keys.KEY_SYSRQ

    def isFocused(self):
        return self.__focused

    def __showErrorMessage(self, message):
        self.__flashCall(BTMS_COMMANDS.ShowActionFailureMessage(), [g_settings.htmlTemplates.format('battleErrorMessage', ctx={'error': message})])

    def __me_onUsersRosterChanged(self, action, user):
        message = getUserRosterChangedMessage(action, user)
        if message:
            self.__showErrorMessage(message)

    def __me_onMessageReceived(self, message, channel):
        if channel is not None:
            controller = self.__channelsCtrl.getController(channel.getClientID())
            if controller:
                controller.addMessage(message)
            else:
                bw_battle_controllers.addDefMessage(message)
        return

    def __me_onCommandReceived(self, command):
        channel = self.channelsStorage.getChannel(BWChannelLightEntity(command.getID()))
        if channel is not None:
            controller = self.__channelsCtrl.getController(channel.getClientID())
            if controller:
                controller.addCommand(command)
            else:
                LOG_ERROR('Controller not found', command)
        else:
            LOG_ERROR('Channel not found', command)
        return

    def __me_onServerErrorReceived(self, error):
        self.__showErrorMessage(error.getMessage())

    def __ms_onUserPreferencesUpdated(self):
        self.__flashCall(BTMS_COMMANDS.UserPreferencesUpdated(), [g_settings.userPrefs.storeReceiverInBattle])

    def __ms_onColorsSchemesUpdated(self):
        args = []
        for view in self.__views:
            args.append(view._channelID)
            args.append(view.getRecvConfig()[0])

        if len(args):
            self.__flashCall(BTMS_COMMANDS.UpdateReceivers(), args)

    def __handleChannelControllerInited(self, event):
        ctx = event.ctx
        settings = ctx.get('settings')
        if settings is None:
            LOG_ERROR('Settings is not defined', event.ctx)
            return
        else:
            controller = ctx.get('controller')
            if controller is None:
                LOG_ERROR('Controller is not defined', event.ctx)
                return
            if not self.__channelsCtrl.hasController(controller):
                LOG_DEBUG('Controller is ignored', controller)
                return
            flag = settings[0]
            if flag & self.__initialized > 0:
                LOG_DEBUG('Channel is already inited', settings[1])
                return
            self.__initialized |= flag
            view = BattleChannelView(settings[1])
            if self.__ui:
                view.populateUI(self.__ui)
            self.__views.append(view)
            controller.setView(view)
            if self.__ui and self.__initialized == BATTLE_CHANNEL.INITIALIZED:
                self.enable()
            return

    def __flashCall(self, funcName, args = None):
        if self.__ui:
            self.__ui.call(funcName, args)

    def __flashRespond(self, args = None):
        self.__ui.respond(args)

    def __onChangeFocus(self, _, focused):
        LOG_DEBUG('[BattleMessanger]', '__onChangeFocus = %s' % focused)
        if focused:
            responseHandler = VOIP.getVOIPManager()
            if responseHandler is not None and responseHandler.channelsMgr.currentChannel:
                responseHandler.setMicMute(muted=True)
        self.__focused = focused
        return

    def __onPopulateUI(self, *args):
        LOG_DEBUG('[BattleMessanger]', '__onPopulateUI')
        settings = g_settings.battle
        parser = CommandArgsParser(self.__onPopulateUI.__name__)
        parser.parse(*args)
        parser.addArgs([settings.messageLifeCycle.lifeTime,
         settings.messageLifeCycle.alphaSpeed,
         settings.inactiveStateAlpha,
         CHAT_MESSAGE_MAX_LENGTH_IN_BATTLE,
         settings.hintText,
         settings.toolTipText,
         g_settings.userPrefs.storeReceiverInBattle])
        self.__flashRespond(parser.args())

    def __onAddToFriends(self, _, uid, userName):
        self.proto.users.addFriend(uid, userName)

    def __onRemoveFromFriends(self, _, uid):
        self.proto.users.removeFriend(uid)

    def __onAddToIgnored(self, _, uid, userName):
        self.proto.users.addIgnored(uid, userName)

    def __onRemoveFromIgnored(self, _, uid):
        self.proto.users.removeIgnored(uid)

    def __onSetMuted(self, _, uid, userName):
        self.proto.users.setMuted(uid, userName)

    def __onUnsetMuted(self, _, uid):
        self.proto.users.unsetMuted(uid)
# Embedded file name: scripts/client/gui/Scaleform/managers/ContextMenuManager.py
import BigWorld
import ResMgr
from adisp import process
import constants
from debug_utils import LOG_DEBUG
from account_helpers import isMoneyTransfer
from gui import DialogsInterface
from gui.Scaleform.daapi.view.dialogs import I18nInfoDialogMeta
from helpers import i18n
from gui import SystemMessages
from gui.shared import g_itemsCache
from gui.Scaleform.framework.entities.abstract.ContextMenuManagerMeta import ContextMenuManagerMeta
from gui.Scaleform.locale.MENU import MENU
from gui.Scaleform.locale.SYSTEM_MESSAGES import SYSTEM_MESSAGES
from messenger.m_constants import PROTO_TYPE
from messenger.proto import proto_getter
from messenger.storage import storage_getter
from gui.shared import events, EVENT_BUS_SCOPE

class ContextMenuManager(ContextMenuManagerMeta):
    DENUNCIATIONS = {'bot': constants.DENUNCIATION.BOT,
     'flood': constants.DENUNCIATION.FLOOD,
     'offend': constants.DENUNCIATION.OFFEND,
     'notFairPlay': constants.DENUNCIATION.NOT_FAIR_PLAY,
     'teamKill': constants.DENUNCIATION.TEAMKILL,
     'allyEjection': constants.DENUNCIATION.ALLY_EJECTION,
     'openingOfAllyPos': constants.DENUNCIATION.OPENING_OF_ALLY_POS}

    @storage_getter('users')
    def usersStorage(self):
        return None

    @proto_getter(PROTO_TYPE.BW)
    def proto(self):
        return None

    @process
    def showUserInfo(self, uid, userName):
        userDossier, isHidden = yield g_itemsCache.items.requestUserDossier(userName)
        if userDossier is None:
            if isHidden:
                key = 'messenger/userInfoHidden'
            else:
                key = 'messenger/userInfoNotAvailable'
            DialogsInterface.showI18nInfoDialog(key, lambda result: None, I18nInfoDialogMeta(key, messageCtx={'userName': userName}))
        else:
            self.fireEvent(events.ShowWindowEvent(events.ShowWindowEvent.SHOW_PROFILE_WINDOW, {'userName': userName}), EVENT_BUS_SCOPE.LOBBY)
        return

    def showMoneyTransfer(self, uid, userName):
        LOG_DEBUG('Money transfer window is not implemented yet', uid, userName)

    def createPrivateChannel(self, uid, userName):
        self.proto.users.createPrivateChannel(uid, userName)

    def addFriend(self, uid, userName):
        self.proto.users.addFriend(uid, userName)

    def removeFriend(self, uid):
        self.proto.users.removeFriend(uid)

    def setMuted(self, uid, userName):
        self.proto.users.setMuted(uid, userName)

    def unsetMuted(self, uid):
        self.proto.users.unsetMuted(uid)

    def setIgnored(self, uid, userName):
        self.proto.users.addIgnored(uid, userName)

    def unsetIgnored(self, uid):
        self.proto.users.removeIgnored(uid)

    def appeal(self, uid, userName, topic):
        topicID = self.DENUNCIATIONS.get(topic)
        if topicID is not None:
            BigWorld.player().makeDenunciation(uid, topicID, constants.VIOLATOR_KIND.UNKNOWN)
            topicStr = i18n.makeString(MENU.denunciation(topicID))
            sysMsg = i18n.makeString(SYSTEM_MESSAGES.DENUNCIATION_SUCCESS) % {'name': userName,
             'topic': topicStr}
            SystemMessages.pushMessage(sysMsg, type=SystemMessages.SM_TYPE.Information)
        return

    def kickPlayer(self, accId):
        BigWorld.player().prb_kick(accId, lambda resultID: None)

    def copyToClipboard(self, name):
        BigWorld.wg_copyToClipboard(name)

    def _getUserInfo(self, uid, userName):
        user = self.usersStorage.getUser(uid)
        if user is not None:
            result = {'isFriend': user.isFriend(),
             'isIgnored': user.isIgnored(),
             'isMuted': user.isMuted(),
             'displayName': user.getFullName()}
        else:
            result = {'isFriend': False,
             'isIgnored': False,
             'isMuted': False,
             'displayName': userName}
        return result

    def _getDenunciations(self):
        return g_itemsCache.items.stats.denunciationsLeft

    def _isMoneyTransfer(self):
        return isMoneyTransfer(g_itemsCache.items.stats.attributes)
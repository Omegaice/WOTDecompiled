# 2013.11.15 11:26:38 EST
# Embedded file name: scripts/client/gui/Scaleform/managers/ContextMenuManager.py
import BigWorld
import ResMgr
from adisp import process
import constants
from debug_utils import LOG_DEBUG
from account_helpers import isMoneyTransfer
from gui import DialogsInterface, game_control
from gui.Scaleform.daapi.view.dialogs import I18nInfoDialogMeta
from gui.prb_control import context
from gui.prb_control.functional.no_prebattle import NoPrbFunctional
from gui.prb_control.functional.unit import UnitFunctional
from gui.prb_control.prb_helpers import prbDispatcherProperty
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

    @prbDispatcherProperty
    def prbDispatcher(self):
        return None

    @storage_getter('users')
    def usersStorage(self):
        return None

    @proto_getter(PROTO_TYPE.BW)
    def proto(self):
        return None

    @process
    def showUserInfo(self, uid, userName):
        userDossier, isHidden = yield g_itemsCache.items.requestUserDossier(int(uid))
        if userDossier is None:
            if isHidden:
                key = 'messenger/userInfoHidden'
            else:
                key = 'messenger/userInfoNotAvailable'
            DialogsInterface.showI18nInfoDialog(key, lambda result: None, I18nInfoDialogMeta(key, messageCtx={'userName': userName}))
        else:
            self.fireEvent(events.ShowWindowEvent(events.ShowWindowEvent.SHOW_PROFILE_WINDOW, {'userName': userName,
             'databaseID': int(uid)}), EVENT_BUS_SCOPE.LOBBY)
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
        self._kickPlayerProcess(accId)

    @process
    def _kickPlayerProcess(self, accId):
        prbF = self.prbDispatcher.getPrbFunctional()
        unitF = self.prbDispatcher.getUnitFunctional()
        if not isinstance(prbF, NoPrbFunctional):
            yield self.prbDispatcher.sendPrbRequest(context.KickPlayerCtx(accId, 'prebattle/change_settings'))
        elif isinstance(unitF, UnitFunctional):
            yield self.prbDispatcher.sendUnitRequest(context.KickPlayerCtx(accId, 'prebattle/change_settings'))
        else:
            LOG_DEBUG('Trying to kick player from non compatible functional')
            yield lambda : 0

    def copyToClipboard(self, name):
        BigWorld.wg_copyToClipboard(name)

    def _getUserInfo(self, uid, userName):
        user = self.usersStorage.getUser(uid)
        if user is not None:
            result = {'isFriend': user.isFriend(),
             'isIgnored': user.isIgnored(),
             'isMuted': user.isMuted(),
             'displayName': user.getFullName(),
             'isEnabledInRoaming': self.__isEnabledInRoaming(uid)}
        else:
            result = {'isFriend': False,
             'isIgnored': False,
             'isMuted': False,
             'displayName': userName,
             'isEnabledInRoaming': self.__isEnabledInRoaming(uid)}
        return result

    def __isEnabledInRoaming(self, playerDBID):
        roamingCtrl = game_control.g_instance.roaming
        return not roamingCtrl.isInRoaming() and not roamingCtrl.isPlayerInRoaming(playerDBID)

    def _getDenunciations(self):
        return g_itemsCache.items.stats.denunciationsLeft

    def _isMoneyTransfer(self):
        return isMoneyTransfer(g_itemsCache.items.stats.attributes)
# okay decompyling res/scripts/client/gui/scaleform/managers/contextmenumanager.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:26:38 EST

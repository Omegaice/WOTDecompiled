# 2013.11.15 11:26:11 EST
# Embedded file name: scripts/client/gui/Scaleform/daapi/view/lobby/profile/ProfileWindow.py
from adisp import process
from debug_utils import LOG_DEBUG
from gui.LobbyContext import g_lobbyContext
from gui.Scaleform.daapi.settings import VIEW_ALIAS
from gui.Scaleform.daapi.view.meta.ProfileWindowMeta import ProfileWindowMeta
from gui.Scaleform.framework import AppRef
from gui.Scaleform.framework.entities.View import View
from gui.Scaleform.locale.MENU import MENU
from gui.Scaleform.locale.PROFILE import PROFILE
from gui.shared.utils import dossiers_utils
from helpers.i18n import makeString
from gui.shared import g_itemsCache
from PlayerEvents import g_playerEvents
from messenger.proto.events import g_messengerEvents
from messenger.storage import storage_getter
from gui import game_control

class ProfileWindow(ProfileWindowMeta, View, AppRef):

    def __init__(self, ctx):
        super(ProfileWindow, self).__init__()
        self.__userName = ctx.get('userName')
        self.__databaseID = ctx.get('databaseID')

    def _populate(self):
        super(ProfileWindow, self)._populate()
        self.as_updateS(self.__databaseID)
        g_playerEvents.onDossiersResync += self.__dossierResyncHandler
        self.__updateUserInfo()
        g_messengerEvents.users.onUserRosterChanged += self._onUserRosterChanged
        self.__checkUserRosterInfo()

    def __checkUserRosterInfo(self):
        user = self.usersStorage.getUser(self.__databaseID)
        enabledInroaming = self.__isEnabledInRoaming(self.__databaseID)
        isFriend = user is not None and user.isFriend()
        self.as_addFriendAvailableS(enabledInroaming and not isFriend)
        isIgnored = user is not None and user.isIgnored()
        self.as_setIgnoredAvailableS(enabledInroaming and not isIgnored)
        return

    def __isEnabledInRoaming(self, uid):
        roamingCtrl = game_control.g_instance.roaming
        return not roamingCtrl.isInRoaming() and not roamingCtrl.isPlayerInRoaming(uid)

    @storage_getter('users')
    def usersStorage(self):
        return None

    def _onUserRosterChanged(self, _, user):
        if user.getID() == self.__databaseID:
            self.__checkUserRosterInfo()

    def __dossierResyncHandler(self, *args):
        self.__updateUserInfo()

    @process
    def __updateUserInfo(self):
        req = g_itemsCache.items.dossiers.getUserDossierRequester(self.__databaseID)
        dossier = yield req.getAccountDossier()
        clanInfo = yield req.getClanInfo()
        info = dossiers_utils.getCommonInfo(self.__userName, dossier, clanInfo[1], None)
        self.as_setInitDataS({'fullName': g_lobbyContext.getPlayerFullName(info['name'], clanAbbrev=info['clanName'], regionCode=g_lobbyContext.getRegionCode(self.__databaseID))})
        return

    def registerFlashComponent(self, component, alias, *args):
        if alias == VIEW_ALIAS.PROFILE_TAB_NAVIGATOR:
            super(ProfileWindow, self).registerFlashComponent(component, alias, self.__userName, self.__databaseID, self.__databaseID, {'sectionsData': [self.__getSectionDataObject(PROFILE.SECTION_SUMMARY_TITLE, PROFILE.PROFILE_TABS_TOOLTIP_SUMMARY, VIEW_ALIAS.PROFILE_SUMMARY_WINDOW),
                              self.__getSectionDataObject(PROFILE.SECTION_AWARDS_TITLE, PROFILE.PROFILE_TABS_TOOLTIP_AWARDS, VIEW_ALIAS.PROFILE_AWARDS),
                              self.__getSectionDataObject(PROFILE.SECTION_STATISTICS_TITLE, PROFILE.PROFILE_TABS_TOOLTIP_STATISTICS, VIEW_ALIAS.PROFILE_STATISTICS),
                              self.__getSectionDataObject(PROFILE.SECTION_TECHNIQUE_TITLE, PROFILE.PROFILE_TABS_TOOLTIP_TECHNIQUE, VIEW_ALIAS.PROFILE_TECHNIQUE_WINDOW)]})
        else:
            super(ProfileWindow, self).registerFlashComponent(component, alias)

    def __getSectionDataObject(self, label, tooltip, alias):
        return {'label': makeString(label),
         'alias': alias,
         'tooltip': tooltip}

    def userAddFriend(self):
        self.app.contextMenuManager.addFriend(self.__databaseID, self.__userName)

    def userSetIgnored(self):
        self.app.contextMenuManager.setIgnored(self.__databaseID, self.__userName)

    def userCreatePrivateChannel(self):
        self.app.contextMenuManager.createPrivateChannel(self.__databaseID, self.__userName)

    def onWindowClose(self):
        g_messengerEvents.users.onUserRosterChanged -= self._onUserRosterChanged
        g_playerEvents.onDossiersResync -= self.__dossierResyncHandler
        g_itemsCache.items.dossiers.closeUserDossier(self.__databaseID)
        self.destroy()
# okay decompyling res/scripts/client/gui/scaleform/daapi/view/lobby/profile/profilewindow.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:26:11 EST

# Embedded file name: scripts/client/gui/Scaleform/daapi/view/lobby/profile/ProfilePage.py
from gui.Scaleform.daapi import LobbySubView
from gui.Scaleform.daapi.settings import VIEW_ALIAS
from gui.Scaleform.daapi.view.meta.ProfileMeta import ProfileMeta
from gui.Scaleform.locale.PROFILE import PROFILE
from gui.shared import events
from gui.shared.event_bus import EVENT_BUS_SCOPE
from gui.ClientUpdateManager import g_clientUpdateManager
from helpers.i18n import makeString

class ProfilePage(LobbySubView, ProfileMeta):

    def __init__(self):
        LobbySubView.__init__(self, 0)

    def _populate(self):
        super(ProfilePage, self)._populate()
        g_clientUpdateManager.addCallbacks({'stats.dossier': self.__dossierUpdateCallBack})
        self.__updateData()

    def __dossierUpdateCallBack(self, dif):
        self.__updateData()

    def __updateData(self):
        self.as_updateS(None)
        return

    def _onRegisterFlashComponent(self, viewPy, alias):
        super(ProfilePage, self)._onRegisterFlashComponent(viewPy, alias)
        if alias == VIEW_ALIAS.PROFILE_TAB_NAVIGATOR:
            viewPy.as_setInitDataS({'sectionsData': [self.__getSectionDataObject(PROFILE.SECTION_SUMMARY_TITLE, PROFILE.PROFILE_TABS_TOOLTIP_SUMMARY, VIEW_ALIAS.PROFILE_SUMMARY_PAGE),
                              self.__getSectionDataObject(PROFILE.SECTION_AWARDS_TITLE, PROFILE.PROFILE_TABS_TOOLTIP_AWARDS, VIEW_ALIAS.PROFILE_AWARDS),
                              self.__getSectionDataObject(PROFILE.SECTION_STATISTICS_TITLE, PROFILE.PROFILE_TABS_TOOLTIP_STATISTICS, VIEW_ALIAS.PROFILE_STATISTICS),
                              self.__getSectionDataObject(PROFILE.SECTION_TECHNIQUE_TITLE, PROFILE.PROFILE_TABS_TOOLTIP_TECHNIQUE, VIEW_ALIAS.PROFILE_TECHNIQUE_PAGE)]})

    def __getSectionDataObject(self, label, tooltip, alias):
        return {'label': makeString(label),
         'alias': alias,
         'tooltip': tooltip}

    def onCloseProfile(self):
        self.fireEvent(events.LoadEvent(events.LoadEvent.LOAD_HANGAR), scope=EVENT_BUS_SCOPE.LOBBY)

    def _dispose(self):
        g_clientUpdateManager.removeObjectCallbacks(self)
        super(ProfilePage, self)._dispose()
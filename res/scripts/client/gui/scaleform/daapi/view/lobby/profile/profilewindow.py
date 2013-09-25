# Embedded file name: scripts/client/gui/Scaleform/daapi/view/lobby/profile/ProfileWindow.py
from adisp import process
from debug_utils import LOG_DEBUG
from gui.Scaleform.daapi.settings import VIEW_ALIAS
from gui.Scaleform.daapi.view.meta.ProfileWindowMeta import ProfileWindowMeta
from gui.Scaleform.framework.entities.View import View
from gui.Scaleform.locale.MENU import MENU
from gui.Scaleform.locale.PROFILE import PROFILE
from gui.shared.utils import dossiers_utils
from helpers.i18n import makeString
from gui.shared import g_itemsCache
from PlayerEvents import g_playerEvents

class ProfileWindow(ProfileWindowMeta, View):

    def __init__(self, ctx):
        super(ProfileWindow, self).__init__()
        self.__userName = ctx.get('userName')

    def _populate(self):
        super(ProfileWindow, self)._populate()
        self.as_updateS(self.__userName)
        g_playerEvents.onDossiersResync += self.__dossierResyncHandler
        self.__updateCommonInfo()

    def __dossierResyncHandler(self, *args):
        self.__updateCommonInfo()

    @process
    def __updateCommonInfo(self):
        req = g_itemsCache.items.dossiers.getUserDossierRequester(self.__userName)
        dossier = yield req.getAccountDossier()
        clanInfo = yield req.getClanInfo()
        info = dossiers_utils.getCommonInfo(self.__userName, dossier, clanInfo[1], None)
        info['name'] = makeString(PROFILE.PROFILE_TITLE, info['name'])
        info['clanLabel'] = makeString(MENU.PROFILE_CLAN_LABEL)
        registrationDate = makeString(MENU.PROFILE_HEADER_REGISTRATIONDATETITLE) + ' ' + info['registrationDate']
        info['registrationDate'] = registrationDate
        lastBattleDate = makeString(MENU.PROFILE_HEADER_LASTBATTLEDATETITLE) + ' ' + info['lastBattleDate']
        info['lastBattleDate'] = lastBattleDate
        self.as_setInitDataS(info)
        return

    def _onRegisterFlashComponent(self, viewPy, alias):
        super(ProfileWindow, self)._onRegisterFlashComponent(viewPy, alias)
        if alias == VIEW_ALIAS.PROFILE_TAB_NAVIGATOR:
            viewPy.as_setInitDataS({'sectionsData': [self.__getSectionDataObject(PROFILE.SECTION_SUMMARY_TITLE, PROFILE.PROFILE_TABS_TOOLTIP_SUMMARY, VIEW_ALIAS.PROFILE_SUMMARY_WINDOW),
                              self.__getSectionDataObject(PROFILE.SECTION_AWARDS_TITLE, PROFILE.PROFILE_TABS_TOOLTIP_AWARDS, VIEW_ALIAS.PROFILE_AWARDS),
                              self.__getSectionDataObject(PROFILE.SECTION_STATISTICS_TITLE, PROFILE.PROFILE_TABS_TOOLTIP_STATISTICS, VIEW_ALIAS.PROFILE_STATISTICS),
                              self.__getSectionDataObject(PROFILE.SECTION_TECHNIQUE_TITLE, PROFILE.PROFILE_TABS_TOOLTIP_TECHNIQUE, VIEW_ALIAS.PROFILE_TECHNIQUE_WINDOW)]})

    def __getSectionDataObject(self, label, tooltip, alias):
        return {'label': makeString(label),
         'alias': alias,
         'tooltip': tooltip}

    def onWindowClose(self):
        g_playerEvents.onDossiersResync -= self.__dossierResyncHandler
        g_itemsCache.items.dossiers.closeUserDossier(self.__userName)
        self.destroy()
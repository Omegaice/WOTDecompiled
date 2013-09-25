from gui.Scaleform.framework.managers.loaders import PackageBusinessHandler
from gui.Scaleform.framework import GroupedViewSettings, VIEW_TYPE
from gui.shared import EVENT_BUS_SCOPE
from gui.shared.events import ShowWindowEvent

class PRB_WINDOW_VIEW_ALIAS(object):
    SEND_INVITES_WINDOW = 'prb_windows/sendInvitesWindow'
    RECEIVED_INVITE_WINDOW = 'prb_windows/receivedInviteWindow'
    SQUAD_WINDOW = 'prb_windows/squadWindow'
    BATTLE_SESSION_WINDOW = 'prb_windows/battleSessionWindow'
    BATTLE_SESSION_LIST = 'prb_windows/battleSessionList'
    COMPANY_WINDOW = 'prb_windows/companyWindow'
    COMPANIES_WINDOW = 'prb_windows/companiesWindow'
    NOTIFICATION_INVITES_WINDOW = 'prb_windows/notificationInvitesWindow'


def getViewSettings():
    from gui.Scaleform.daapi.view.lobby.prb_windows.BattleSessionList import BattleSessionList
    from gui.Scaleform.daapi.view.lobby.prb_windows.BattleSessionWindow import BattleSessionWindow
    from gui.Scaleform.daapi.view.lobby.prb_windows.CompaniesWindow import CompaniesWindow
    from gui.Scaleform.daapi.view.lobby.prb_windows.CompanyWindow import CompanyWindow
    from gui.Scaleform.daapi.view.lobby.prb_windows.NotificationInvites import NotificationInvitesWindow
    from gui.Scaleform.daapi.view.lobby.prb_windows.PrbSendInvitesWindow import PrbSendInvitesWindow
    from gui.Scaleform.daapi.view.lobby.prb_windows.ReceivedInviteWindow import ReceivedInviteWindow
    from gui.Scaleform.daapi.view.lobby.prb_windows.SquadWindow import SquadWindow
    return [GroupedViewSettings(PRB_WINDOW_VIEW_ALIAS.SEND_INVITES_WINDOW, PrbSendInvitesWindow, 'prbSendInvitesWindow.swf', VIEW_TYPE.WINDOW, '', ShowWindowEvent.SHOW_SEND_INVITES_WINDOW),
     GroupedViewSettings(PRB_WINDOW_VIEW_ALIAS.RECEIVED_INVITE_WINDOW, ReceivedInviteWindow, 'receivedInviteWindow.swf', VIEW_TYPE.WINDOW, 'receivedInviteWindow', None),
     GroupedViewSettings(PRB_WINDOW_VIEW_ALIAS.SQUAD_WINDOW, SquadWindow, 'squadWindow.swf', VIEW_TYPE.WINDOW, '', ShowWindowEvent.SHOW_SQUAD_WINDOW),
     GroupedViewSettings(PRB_WINDOW_VIEW_ALIAS.COMPANY_WINDOW, CompanyWindow, 'companyWindow.swf', VIEW_TYPE.WINDOW, '', ShowWindowEvent.SHOW_COMPANY_WINDOW),
     GroupedViewSettings(PRB_WINDOW_VIEW_ALIAS.COMPANIES_WINDOW, CompaniesWindow, 'companiesListWindow.swf', VIEW_TYPE.WINDOW, '', ShowWindowEvent.SHOW_COMPANIES_WINDOW),
     GroupedViewSettings(PRB_WINDOW_VIEW_ALIAS.BATTLE_SESSION_WINDOW, BattleSessionWindow, 'battleSessionWindow.swf', VIEW_TYPE.WINDOW, '', ShowWindowEvent.SHOW_BATTLE_SESSION_WINDOW),
     GroupedViewSettings(PRB_WINDOW_VIEW_ALIAS.BATTLE_SESSION_LIST, BattleSessionList, 'battleSessionList.swf', VIEW_TYPE.WINDOW, '', ShowWindowEvent.SHOW_BATTLE_SESSION_LIST),
     GroupedViewSettings(PRB_WINDOW_VIEW_ALIAS.NOTIFICATION_INVITES_WINDOW, NotificationInvitesWindow, 'notificationInvitesWindow.swf', VIEW_TYPE.WINDOW, '', ShowWindowEvent.SHOW_NOTIFICATION_INVITES_WINDOW)]


def getBusinessHandlers():
    return [PrbPackageBusinessHandler()]


class PrbPackageBusinessHandler(PackageBusinessHandler):

    def __init__(self):
        listeners = [(ShowWindowEvent.SHOW_SQUAD_WINDOW, self.__showSquadWindow),
         (ShowWindowEvent.SHOW_COMPANY_WINDOW, self.__showCompanyWindow),
         (ShowWindowEvent.SHOW_COMPANIES_WINDOW, self.__showCompaniesWindow),
         (ShowWindowEvent.SHOW_BATTLE_SESSION_WINDOW, self.__showBattleSessionWindow),
         (ShowWindowEvent.SHOW_BATTLE_SESSION_LIST, self.__showBattleSessionList),
         (ShowWindowEvent.SHOW_SEND_INVITES_WINDOW, self.__showSendInvitesWindow),
         (ShowWindowEvent.SHOW_RECEIVED_INVITE_WINDOW, self.__showReceivedInviteWindow),
         (ShowWindowEvent.SHOW_NOTIFICATION_INVITES_WINDOW, self.__showNotificationInvitesWindow)]
        super(PrbPackageBusinessHandler, self).__init__(listeners, EVENT_BUS_SCOPE.LOBBY)

    def __showBattleSessionWindow(self, _):
        viewAlias = PRB_WINDOW_VIEW_ALIAS.BATTLE_SESSION_WINDOW
        self.app.loadView(viewAlias, viewAlias)

    def __showBattleSessionList(self, _):
        viewAlias = PRB_WINDOW_VIEW_ALIAS.BATTLE_SESSION_LIST
        self.app.loadView(viewAlias, viewAlias)

    def __showSquadWindow(self, event):
        alias = name = PRB_WINDOW_VIEW_ALIAS.SQUAD_WINDOW
        self.app.loadView(alias, name, event.ctx)

    def __showSendInvitesWindow(self, event):
        alias = name = PRB_WINDOW_VIEW_ALIAS.SEND_INVITES_WINDOW
        self.app.loadView(alias, name, event.ctx)

    def __showReceivedInviteWindow(self, event):
        alias = PRB_WINDOW_VIEW_ALIAS.RECEIVED_INVITE_WINDOW
        name = 'receivedInviteWindow_{0:n}'.format(event.ctx.get('inviteID'))
        self.app.loadView(alias, name, event.ctx)

    def __showNotificationInvitesWindow(self, _):
        self.app.loadView(PRB_WINDOW_VIEW_ALIAS.NOTIFICATION_INVITES_WINDOW)

    def __showCompaniesWindow(self, _):
        alias = name = PRB_WINDOW_VIEW_ALIAS.COMPANIES_WINDOW
        self.app.loadView(alias, name)

    def __showCompanyWindow(self, event):
        alias = name = PRB_WINDOW_VIEW_ALIAS.COMPANY_WINDOW
        self.app.loadView(alias, name, event.ctx)

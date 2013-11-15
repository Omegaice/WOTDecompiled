# 2013.11.15 11:25:51 EST
# Embedded file name: scripts/client/gui/Scaleform/daapi/settings/__init__.py
from gui.Scaleform.daapi.settings.views import VIEW_ALIAS
from gui.Scaleform.daapi.view.dialogs.DismissTankmanDialog import DismissTankmanDialog
from gui.Scaleform.daapi.view.dialogs.IconPriceDialog import IconPriceDialog
from gui.Scaleform.daapi.view.dialogs.IconDialog import IconDialog
from gui.Scaleform.daapi.view.dialogs.DemountDeviceDialog import DemountDeviceDialog
from gui.Scaleform.daapi.view.lobby.VehicleInfoWindow import VehicleInfoWindow
from gui.Scaleform.daapi.view.lobby.VehicleSellDialog import VehicleSellDialog
from gui.Scaleform.daapi.view.lobby.PremiumForm import PremiumForm
from gui.Scaleform.daapi.view.lobby.PersonalCase import PersonalCase
from gui.Scaleform.daapi.view.lobby.eliteWindow.EliteWindow import EliteWindow
from gui.Scaleform.daapi.view.lobby.hangar.TmenXpPanel import TmenXpPanel
from gui.Scaleform.daapi.view.lobby.header.QuestsControl import QuestsControl
from gui.Scaleform.daapi.view.lobby.profile.ProfileSummaryPage import ProfileSummaryPage
from gui.Scaleform.daapi.view.lobby.profile.ProfileSummaryWindow import ProfileSummaryWindow
from gui.Scaleform.daapi.view.lobby.quests import QuestsCurrentTab, QuestsFutureTab, QuestsWindow
from gui.Scaleform.daapi.view.login.EULA import EULADlg
from gui.Scaleform.daapi.view.BattleLoading import BattleLoading
from gui.Scaleform.daapi.view.login.LoginCreateAnAccountWindow import LoginCreateAnAccountWindow
from gui.Scaleform.framework.WaitingView import WaitingView
from gui.Scaleform.managers.Cursor import Cursor
from gui.Scaleform.daapi.view.BattleResultsWindow import BattleResultsWindow
from gui.Scaleform.daapi.view.IntroPage import IntroPage
from gui.Scaleform.daapi.view.dialogs.CaptchaDialog import CaptchaDialog
from gui.Scaleform.daapi.view.dialogs.SimpleDialog import SimpleDialog
from gui.Scaleform.daapi.view.dialogs.ConfirmModuleDialog import ConfirmModuleDialog
from gui.Scaleform.daapi.view.lobby.ModuleInfoWindow import ModuleInfoWindow
from gui.Scaleform.daapi.view.lobby.LobbyMenu import LobbyMenu
from gui.Scaleform.daapi.view.lobby.BrowserWindow import BrowserWindow
from gui.Scaleform.daapi.view.lobby.DemonstratorWindow import DemonstratorWindow
from gui.Scaleform.daapi.view.lobby.exchange.ExchangeWindow import ExchangeWindow
from gui.Scaleform.daapi.view.lobby.exchange.ExchangeXPWindow import ExchangeXPWindow
from gui.Scaleform.daapi.view.dialogs.SystemMessageDialog import SystemMessageDialog
from gui.Scaleform.daapi.view.lobby.LobbyView import LobbyView
from gui.Scaleform.daapi.view.lobby.barracks.Barracks import Barracks
from gui.Scaleform.daapi.view.lobby.header.TutorialControl import TutorialControl
from gui.Scaleform.daapi.view.lobby.header.Ticker import Ticker
from gui.Scaleform.daapi.view.lobby.header.FightButton import FightButton
from gui.Scaleform.daapi.view.lobby.header.LobbyHeader import LobbyHeader
from gui.Scaleform.daapi.view.lobby.messengerBar import MessengerBar, ChannelCarousel, NotificationInvitesButton, NotificationListButton
from gui.Scaleform.daapi.view.lobby.profile import ProfilePage, ProfileAwards, ProfileStatistics, ProfileTabNavigator, ProfileWindow, ProfileTechniqueWindow, ProfileTechniquePage
from gui.Scaleform.daapi.view.lobby.recruitWindow.RecruitWindow import RecruitWindow
from gui.Scaleform.daapi.view.lobby.settings import SettingsWindow
from gui.Scaleform.daapi.view.lobby.MinimapLobby import MinimapLobby
from gui.Scaleform.daapi.view.lobby.BattleQueue import BattleQueue
from gui.Scaleform.daapi.view.lobby.trainings import Trainings, TrainingSettingsWindow, TrainingRoom
from gui.Scaleform.daapi.view.lobby.customization.VehicleCustomization import VehicleCustomization
from gui.Scaleform.daapi.view.lobby.exchange.ExchangeFreeToTankmanXpWindow import ExchangeFreeToTankmanXpWindow
from gui.Scaleform.daapi.view.lobby.exchange.ExchangeVcoinWindow import ExchangeVcoinWindow
from gui.Scaleform.daapi.view.lobby.SkillDropWindow import SkillDropWindow
from gui.Scaleform.daapi.view.lobby.VehicleBuyWindow import VehicleBuyWindow
from gui.Scaleform.daapi.view.lobby.hangar import TechnicalMaintenance, TankCarousel, ResearchPanel, AmmunitionPanel, Crew, Params, Hangar
from gui.Scaleform.daapi.view.lobby.store.StoreTable import StoreTable
from gui.Scaleform.daapi.view.lobby.store.Inventory import Inventory
from gui.Scaleform.daapi.view.lobby.store.Shop import Shop
from gui.Scaleform.daapi.view.login import LoginView
from gui.Scaleform.daapi.view.login.LoginQueue import LoginQueue
from gui.Scaleform.framework import ViewSettings, GroupedViewSettings, VIEW_TYPE, VIEW_SCOPE
from gui.shared.events import LoadEvent
from notification.NotificationListView import NotificationListView
from notification.NotificationPopUpViewer import NotificationPopUpViewer
VIEWS_SETTINGS = (ViewSettings(VIEW_ALIAS.LOGIN, LoginView, 'login.swf', VIEW_TYPE.DEFAULT, None, VIEW_SCOPE.DEFAULT),
 ViewSettings(VIEW_ALIAS.INTRO_VIDEO, IntroPage, 'introPage.swf', VIEW_TYPE.DEFAULT, None, VIEW_SCOPE.DEFAULT),
 ViewSettings(VIEW_ALIAS.CURSOR, Cursor, 'cursor.swf', VIEW_TYPE.CURSOR, None, VIEW_SCOPE.DEFAULT),
 ViewSettings(VIEW_ALIAS.WAITING, WaitingView, 'waiting.swf', VIEW_TYPE.WAITING, None, VIEW_SCOPE.DEFAULT),
 ViewSettings(VIEW_ALIAS.LOBBY, LobbyView, 'lobby.swf', VIEW_TYPE.DEFAULT, None, VIEW_SCOPE.DEFAULT),
 ViewSettings(VIEW_ALIAS.LOBBY_HANGAR, Hangar, 'hangar.swf', VIEW_TYPE.LOBBY_SUB, LoadEvent.LOAD_HANGAR, VIEW_SCOPE.DEFAULT),
 ViewSettings(VIEW_ALIAS.LOBBY_SHOP, Shop, 'shop.swf', VIEW_TYPE.LOBBY_SUB, LoadEvent.LOAD_SHOP, VIEW_SCOPE.DEFAULT),
 ViewSettings(VIEW_ALIAS.LOBBY_INVENTORY, Inventory, 'inventory.swf', VIEW_TYPE.LOBBY_SUB, LoadEvent.LOAD_INVENTORY, VIEW_SCOPE.DEFAULT),
 ViewSettings(VIEW_ALIAS.LOBBY_PROFILE, ProfilePage, 'profile.swf', VIEW_TYPE.LOBBY_SUB, LoadEvent.LOAD_PROFILE, VIEW_SCOPE.DEFAULT),
 ViewSettings(VIEW_ALIAS.LOBBY_BARRACKS, Barracks, 'barracks.swf', VIEW_TYPE.LOBBY_SUB, LoadEvent.LOAD_BARRACKS, VIEW_SCOPE.DEFAULT),
 ViewSettings(VIEW_ALIAS.LOBBY_CUSTOMIZATION, VehicleCustomization, 'vehicleCustomization.swf', VIEW_TYPE.LOBBY_SUB, LoadEvent.LOAD_CUSTOMIZATION, VIEW_SCOPE.DEFAULT),
 ViewSettings(VIEW_ALIAS.LOBBY_TRAININGS, Trainings, 'trainingForm.swf', VIEW_TYPE.LOBBY_SUB, LoadEvent.LOAD_TRAININGS, VIEW_SCOPE.DEFAULT),
 ViewSettings(VIEW_ALIAS.LOBBY_TRAINING_ROOM, TrainingRoom, 'trainingRoom.swf', VIEW_TYPE.LOBBY_SUB, LoadEvent.LOAD_TRAINING_ROOM, VIEW_SCOPE.DEFAULT),
 ViewSettings(VIEW_ALIAS.BATTLE_QUEUE, BattleQueue, 'battleQueue.swf', VIEW_TYPE.LOBBY_SUB, LoadEvent.LOAD_BATTLE_QUEUE, VIEW_SCOPE.DEFAULT),
 ViewSettings(VIEW_ALIAS.BATTLE_LOADING, BattleLoading, 'battleLoading.swf', VIEW_TYPE.DEFAULT, LoadEvent.LOAD_BATTLE_LOADING, VIEW_SCOPE.DEFAULT),
 ViewSettings(VIEW_ALIAS.TUTORIAL_LOADING, BattleLoading, 'tutorialLoading.swf', VIEW_TYPE.DEFAULT, LoadEvent.LOAD_TUTORIAL_LOADING, VIEW_SCOPE.DEFAULT),
 GroupedViewSettings(VIEW_ALIAS.RECRUIT_WINDOW, RecruitWindow, 'recruitWindow.swf', VIEW_TYPE.WINDOW, 'recruitWindow', None, VIEW_SCOPE.DEFAULT),
 GroupedViewSettings(VIEW_ALIAS.ELITE_WINDOW, EliteWindow, 'eliteWindow.swf', VIEW_TYPE.WINDOW, 'eliteWindow', None, VIEW_SCOPE.DEFAULT),
 GroupedViewSettings(VIEW_ALIAS.EXCHANGE_WINDOW, ExchangeWindow, 'exchangeWindow.swf', VIEW_TYPE.WINDOW, 'exchangeWindow', None, VIEW_SCOPE.DEFAULT),
 GroupedViewSettings(VIEW_ALIAS.PROFILE_WINDOW, ProfileWindow, 'profileWindow.swf', VIEW_TYPE.WINDOW, 'profileWindow', None, VIEW_SCOPE.DEFAULT),
 GroupedViewSettings(VIEW_ALIAS.EXCHANGE_VCOIN_WINDOW, ExchangeVcoinWindow, 'exchangeVcoinWindow.swf', VIEW_TYPE.WINDOW, 'exchangeVcoinWindow', None, VIEW_SCOPE.DEFAULT),
 GroupedViewSettings(VIEW_ALIAS.EXCHANGE_XP_WINDOW, ExchangeXPWindow, 'exchangeXPWindow.swf', VIEW_TYPE.WINDOW, 'exchangeXPWindow', None, VIEW_SCOPE.DEFAULT),
 GroupedViewSettings(VIEW_ALIAS.EXCHANGE_FREE_TO_TANKMAN_XP_WINDOW, ExchangeFreeToTankmanXpWindow, 'exchangeFreeToTankmanXpWindow.swf', VIEW_TYPE.WINDOW, 'exchangeFreeToTankmanXpWindow', None, VIEW_SCOPE.DEFAULT),
 GroupedViewSettings(VIEW_ALIAS.VEHICLE_BUY_WINDOW, VehicleBuyWindow, 'vehicleBuyWindow.swf', VIEW_TYPE.WINDOW, 'vehicleBuyWindow', None, VIEW_SCOPE.DEFAULT),
 GroupedViewSettings(VIEW_ALIAS.CONFIRM_MODULE_DIALOG, ConfirmModuleDialog, 'confirmModuleWindow.swf', VIEW_TYPE.WINDOW, 'confirmModuleDialog', None, VIEW_SCOPE.DEFAULT),
 GroupedViewSettings(VIEW_ALIAS.SYSTEM_MESSAGE_DIALOG, SystemMessageDialog, 'systemMessageDialog.swf', VIEW_TYPE.WINDOW, 'systemMessageDialog', None, VIEW_SCOPE.DEFAULT),
 GroupedViewSettings(VIEW_ALIAS.NOTIFICATIONS_LIST, NotificationListView, 'notificationsList.swf', VIEW_TYPE.WINDOW, 'notificationsList', None, VIEW_SCOPE.DEFAULT),
 GroupedViewSettings(VIEW_ALIAS.VEHICLE_INFO_WINDOW, VehicleInfoWindow, 'vehicleInfo.swf', VIEW_TYPE.WINDOW, 'vehicleInfoWindow', None, VIEW_SCOPE.DEFAULT),
 GroupedViewSettings(VIEW_ALIAS.MODULE_INFO_WINDOW, ModuleInfoWindow, 'moduleInfo.swf', VIEW_TYPE.WINDOW, 'moduleInfoWindow', None, VIEW_SCOPE.DEFAULT),
 GroupedViewSettings(VIEW_ALIAS.SETTINGS_WINDOW, SettingsWindow, 'settingsWindow.swf', VIEW_TYPE.DIALOG, 'settingsWindow', None, VIEW_SCOPE.DEFAULT),
 GroupedViewSettings(VIEW_ALIAS.VEHICLE_SELL_DIALOG, VehicleSellDialog, 'vehicleSellDialog.swf', VIEW_TYPE.WINDOW, 'vehicleSellWindow', None, VIEW_SCOPE.DEFAULT),
 GroupedViewSettings(VIEW_ALIAS.PERSONAL_CASE, PersonalCase, 'personalCase.swf', VIEW_TYPE.WINDOW, 'personalCaseWindow', None, VIEW_SCOPE.DEFAULT),
 GroupedViewSettings(VIEW_ALIAS.TECHNICAL_MAINTENANCE, TechnicalMaintenance, 'technicalMaintenance.swf', VIEW_TYPE.WINDOW, '', None, VIEW_SCOPE.DEFAULT),
 GroupedViewSettings(VIEW_ALIAS.BATTLE_RESULTS, BattleResultsWindow, 'battleResults.swf', VIEW_TYPE.WINDOW, 'BattleResultsWindow', None, VIEW_SCOPE.DEFAULT),
 GroupedViewSettings(VIEW_ALIAS.QUESTS_WINDOW, QuestsWindow, 'questsWindow.swf', VIEW_TYPE.WINDOW, '', None, VIEW_SCOPE.DEFAULT),
 GroupedViewSettings(VIEW_ALIAS.TANKMAN_SKILLS_DROP_WINDOW, SkillDropWindow, 'skillDropWindow.swf', VIEW_TYPE.WINDOW, '', None, VIEW_SCOPE.DEFAULT),
 GroupedViewSettings(VIEW_ALIAS.TRAINING_SETTINGS_WINDOW, TrainingSettingsWindow, 'trainingWindow.swf', VIEW_TYPE.WINDOW, '', None, VIEW_SCOPE.DEFAULT),
 GroupedViewSettings(VIEW_ALIAS.DEMONSTRATOR_WINDOW, DemonstratorWindow, 'demonstratorWindow.swf', VIEW_TYPE.WINDOW, '', None, VIEW_SCOPE.DEFAULT),
 GroupedViewSettings(VIEW_ALIAS.BROWSER_WINDOW, BrowserWindow, 'browser.swf', VIEW_TYPE.DIALOG, '', None, VIEW_SCOPE.DEFAULT),
 GroupedViewSettings(VIEW_ALIAS.EULA, EULADlg, 'EULADlg.swf', VIEW_TYPE.DIALOG, '', None, VIEW_SCOPE.DEFAULT),
 GroupedViewSettings(VIEW_ALIAS.EULA_FULL, EULADlg, 'EULAFullDlg.swf', VIEW_TYPE.DIALOG, '', None, VIEW_SCOPE.DEFAULT),
 GroupedViewSettings(VIEW_ALIAS.LOGIN_QUEUE, LoginQueue, 'LoginQueueWindow.swf', VIEW_TYPE.DIALOG, '', None, VIEW_SCOPE.DEFAULT),
 GroupedViewSettings(VIEW_ALIAS.LOGIN_CREATE_AN_ACC, LoginCreateAnAccountWindow, 'loginCreateAnAccount.swf', VIEW_TYPE.DIALOG, '', None, VIEW_SCOPE.DEFAULT),
 GroupedViewSettings(VIEW_ALIAS.SIMPLE_DIALOG, SimpleDialog, 'simpleDialog.swf', VIEW_TYPE.DIALOG, '', None, VIEW_SCOPE.DYNAMIC),
 GroupedViewSettings(VIEW_ALIAS.DISMISS_TANKMAN_DIALOG, DismissTankmanDialog, 'dismissTankmanDialog.swf', VIEW_TYPE.DIALOG, '', None, VIEW_SCOPE.DYNAMIC),
 GroupedViewSettings(VIEW_ALIAS.ICON_DIALOG, IconDialog, 'iconDialog.swf', VIEW_TYPE.WINDOW, '', None, VIEW_SCOPE.DYNAMIC),
 GroupedViewSettings(VIEW_ALIAS.ICON_PRICE_DIALOG, IconPriceDialog, 'iconPriceDialog.swf', VIEW_TYPE.WINDOW, '', None, VIEW_SCOPE.DYNAMIC),
 GroupedViewSettings(VIEW_ALIAS.DESTROY_DEVICE_DIALOG, IconDialog, 'destroyDeviceDialog.swf', VIEW_TYPE.WINDOW, '', None, VIEW_SCOPE.DYNAMIC),
 GroupedViewSettings(VIEW_ALIAS.DEMOUNT_DEVICE_DIALOG, DemountDeviceDialog, 'demountDeviceDialog.swf', VIEW_TYPE.WINDOW, '', None, VIEW_SCOPE.DYNAMIC),
 GroupedViewSettings(VIEW_ALIAS.CAPTCHA_DIALOG, CaptchaDialog, 'CAPTCHA.swf', VIEW_TYPE.DIALOG, '', None, VIEW_SCOPE.DEFAULT),
 GroupedViewSettings(VIEW_ALIAS.LOBBY_MENU, LobbyMenu, 'lobbyMenu.swf', VIEW_TYPE.DIALOG, '', None, VIEW_SCOPE.LOBBY_SUB),
 GroupedViewSettings(VIEW_ALIAS.PREMIUM_DIALOG, PremiumForm, 'premiumForm.swf', VIEW_TYPE.WINDOW, '', None, VIEW_SCOPE.DEFAULT),
 ViewSettings(VIEW_ALIAS.SHOP_TABLE, StoreTable, None, VIEW_TYPE.COMPONENT, None, VIEW_SCOPE.DEFAULT),
 ViewSettings(VIEW_ALIAS.LOBBY_HEADER, LobbyHeader, None, VIEW_TYPE.COMPONENT, None, VIEW_SCOPE.DEFAULT),
 ViewSettings(VIEW_ALIAS.PROFILE_TAB_NAVIGATOR, ProfileTabNavigator, None, VIEW_TYPE.COMPONENT, None, VIEW_SCOPE.DEFAULT),
 ViewSettings(VIEW_ALIAS.PROFILE_SUMMARY_WINDOW, ProfileSummaryWindow, None, VIEW_TYPE.COMPONENT, None, VIEW_SCOPE.DEFAULT),
 ViewSettings(VIEW_ALIAS.PROFILE_SUMMARY_PAGE, ProfileSummaryPage, None, VIEW_TYPE.COMPONENT, None, VIEW_SCOPE.DEFAULT),
 ViewSettings(VIEW_ALIAS.PROFILE_AWARDS, ProfileAwards, None, VIEW_TYPE.COMPONENT, None, VIEW_SCOPE.DEFAULT),
 ViewSettings(VIEW_ALIAS.PROFILE_STATISTICS, ProfileStatistics, None, VIEW_TYPE.COMPONENT, None, VIEW_SCOPE.DEFAULT),
 ViewSettings(VIEW_ALIAS.PROFILE_TECHNIQUE_PAGE, ProfileTechniquePage, None, VIEW_TYPE.COMPONENT, None, VIEW_SCOPE.DEFAULT),
 ViewSettings(VIEW_ALIAS.PROFILE_TECHNIQUE_WINDOW, ProfileTechniqueWindow, None, VIEW_TYPE.COMPONENT, None, VIEW_SCOPE.DEFAULT),
 ViewSettings(VIEW_ALIAS.SYSTEM_MESSAGES, NotificationPopUpViewer, None, VIEW_TYPE.COMPONENT, None, VIEW_SCOPE.DEFAULT),
 ViewSettings(VIEW_ALIAS.MESSENGER_BAR, MessengerBar, None, VIEW_TYPE.COMPONENT, None, VIEW_SCOPE.DEFAULT),
 ViewSettings(VIEW_ALIAS.NOTIFICATION_LIST_BUTTON, NotificationListButton, None, VIEW_TYPE.COMPONENT, None, VIEW_SCOPE.DEFAULT),
 ViewSettings(VIEW_ALIAS.NOTIFICATION_INVITES_BUTTON, NotificationInvitesButton, None, VIEW_TYPE.COMPONENT, None, VIEW_SCOPE.DEFAULT),
 ViewSettings(VIEW_ALIAS.CHANNEL_CAROUSEL, ChannelCarousel, None, VIEW_TYPE.COMPONENT, None, VIEW_SCOPE.DEFAULT),
 ViewSettings(Hangar.COMPONENTS.CAROUSEL, TankCarousel, None, VIEW_TYPE.COMPONENT, None, VIEW_SCOPE.DEFAULT),
 ViewSettings(Hangar.COMPONENTS.AMMO_PANEL, AmmunitionPanel, None, VIEW_TYPE.COMPONENT, None, VIEW_SCOPE.DEFAULT),
 ViewSettings(Hangar.COMPONENTS.TMEN_XP_PANEL, TmenXpPanel, None, VIEW_TYPE.COMPONENT, None, VIEW_SCOPE.DEFAULT),
 ViewSettings(Hangar.COMPONENTS.PARAMS, Params, None, VIEW_TYPE.COMPONENT, None, VIEW_SCOPE.DEFAULT),
 ViewSettings(Hangar.COMPONENTS.CREW, Crew, None, VIEW_TYPE.COMPONENT, None, VIEW_SCOPE.DEFAULT),
 ViewSettings(Hangar.COMPONENTS.RESEARCH_PANEL, ResearchPanel, None, VIEW_TYPE.COMPONENT, None, VIEW_SCOPE.DEFAULT),
 ViewSettings(VIEW_ALIAS.MINIMAP_LOBBY, MinimapLobby, None, VIEW_TYPE.COMPONENT, None, VIEW_SCOPE.DEFAULT),
 ViewSettings(VIEW_ALIAS.TUTORIAL_CONTROL, TutorialControl, None, VIEW_TYPE.COMPONENT, None, VIEW_SCOPE.DEFAULT),
 ViewSettings(VIEW_ALIAS.QUESTS_CONTROL, QuestsControl, None, VIEW_TYPE.COMPONENT, None, VIEW_SCOPE.DEFAULT),
 ViewSettings(VIEW_ALIAS.FIGHT_BUTTON, FightButton, None, VIEW_TYPE.COMPONENT, None, VIEW_SCOPE.DEFAULT),
 ViewSettings(VIEW_ALIAS.TICKER, Ticker, None, VIEW_TYPE.COMPONENT, None, VIEW_SCOPE.DEFAULT),
 ViewSettings(VIEW_ALIAS.QUESTS_CURRENT_TAB, QuestsCurrentTab, None, VIEW_TYPE.COMPONENT, None, VIEW_SCOPE.DEFAULT),
 ViewSettings(VIEW_ALIAS.QUESTS_FUTURE_TAB, QuestsFutureTab, None, VIEW_TYPE.COMPONENT, None, VIEW_SCOPE.DEFAULT))
VIEWS_PACKAGES = ('gui.Scaleform.daapi.view.lobby.prb_windows', 'gui.Scaleform.daapi.view.lobby.techtree', 'messenger.gui.Scaleform', 'gui.Scaleform.daapi.view.lobby.cyberSport')
# okay decompyling res/scripts/client/gui/scaleform/daapi/settings/__init__.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:25:52 EST

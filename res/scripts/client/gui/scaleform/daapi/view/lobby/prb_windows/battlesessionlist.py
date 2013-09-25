from adisp import process
from gui.Scaleform.daapi.view.lobby.prb_windows.PrebattlesListWindow import PrebattlesListWindow
from gui.Scaleform.managers.windows_stored_data import DATA_TYPE, TARGET_ID
from gui.Scaleform.managers.windows_stored_data import stored_window
from gui.prb_control import context, formatters
from gui.prb_control.functional.battle_session import AutoInvitesRequester
from gui.Scaleform.daapi.view.meta.BattleSessionListMeta import BattleSessionListMeta
from messenger.ext import channel_num_gen
from messenger.m_constants import LAZY_CHANNEL

@stored_window(DATA_TYPE.CAROUSEL_WINDOW, TARGET_ID.CHANNEL_CAROUSEL)

class BattleSessionList(PrebattlesListWindow, BattleSessionListMeta):

    def __init__(self):
        super(BattleSessionList, self).__init__(LAZY_CHANNEL.SPECIAL_BATTLES)
        self.__listRequester = AutoInvitesRequester()

    @process
    def requestToJoinTeam(self, prbID, prbType):
        yield self.prbDispatcher.join(context.JoinBattleSessionCtx(prbID, prbType, 'prebattle/join'))

    def getClientID(self):
        return channel_num_gen.getClientID4LazyChannel(LAZY_CHANNEL.SPECIAL_BATTLES)

    def _populate(self):
        super(BattleSessionList, self)._populate()
        self.__listRequester.start(self.__onBSListReceived)
        self.__listRequester.request()

    def _dispose(self):
        self.__listRequester.stop()
        super(BattleSessionList, self)._dispose()

    def __onBSListReceived(self, sessions):
        result = []
        for bs in sessions:
            result.append({'prbID': bs.prbID,
             'prbType': bs.prbType,
             'descr': formatters.getPrebattleFullDescription(bs.description),
             'opponents': formatters.getPrebattleOpponentsString(bs.description),
             'startTime': formatters.getBattleSessionStartTimeString(bs.startTime)})

        self.as_refreshListS(result)

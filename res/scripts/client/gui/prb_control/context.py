# 2013.11.15 11:25:36 EST
# Embedded file name: scripts/client/gui/prb_control/context.py
import BigWorld
from CurrentVehicle import g_currentVehicle
from constants import PREBATTLE_TYPE
from constants import PREBATTLE_COMMENT_MAX_LENGTH, PREBATTLE_COMPANY_DIVISION
from debug_utils import LOG_ERROR
from external_strings_utils import truncate_utf8
from gui.Scaleform.Waiting import Waiting
from gui.prb_control import getPrebattleType, getPrebattleID
from gui.prb_control import getPrebattleTypeName, getUnitIdx
from gui.prb_control import settings as prb_settings
__all__ = ('TeamSettingsCtx', 'TrainingSettingsCtx', 'CompanySettingsCtx', 'SquadSettingsCtx', 'JoinTrainingCtx', 'JoinCompanyCtx', 'LeavePrbCtx', 'AssignPrbCtx', 'SetTeamStateCtx', 'SetPlayerStateCtx', 'SwapTeamsCtx', 'ChangeOpenedCtx', 'ChangeCommentCtx', 'ChangeDivisionCtx', 'ChangeArenaVoipCtx', 'KickPlayerCtx', 'RequestCompaniesCtx', 'SendInvitesCtx', 'CreateUnitCtx', 'JoinUnitCtx', 'LeaveUnitCtx', 'LockUnitCtx', 'CloseSlotCtx', 'AssignUnitCtx', 'AutoSearchUnitCtx', 'AcceptSearchUnitCtx', 'ChangeOpenedUnitCtx', 'ChangeCommentUnitCtx', 'SetVehicleUnitCtx', 'SetReadyUnitCtx', 'PrebattleAction', 'StartDispatcherCtx')
REQUEST_TYPE = prb_settings.REQUEST_TYPE
CTRL_ENTITY_TYPE = prb_settings.CTRL_ENTITY_TYPE

class _RequestCtx(object):

    def __init__(self, waitingID = ''):
        self.__waitingID = waitingID
        self.__callback = None
        return

    def __repr__(self):
        return '_PrbRequestCtx(waitingID = N/A, prbType = N/A)'

    def getRequestType(self):
        return 0

    def getEntityType(self):
        return 0

    def getWaitingID(self):
        return self.__waitingID

    def setWaitingID(self, waitingID):
        if not self.isProcessing():
            self.__waitingID = waitingID
        else:
            LOG_ERROR('In processing', self)

    def isProcessing(self):
        return self.__callback is not None

    def startProcessing(self, callback = None):
        if len(self.__waitingID):
            Waiting.show(self.__waitingID)
        if callback is not None and callable(callback):
            self.__callback = callback
        return

    def stopProcessing(self, result = False):
        if self.__callback is not None:
            self.__callback(result)
            self.__callback = None
        if len(self.__waitingID):
            Waiting.hide(self.__waitingID)
        return

    def onResponseReceived(self, code):
        if code < 0:
            LOG_ERROR('Server return error for prebattle request', code, self)
        self.stopProcessing(result=code >= 0)

    def clear(self):
        self.__callback = None
        return


class _PrbRequestCtx(_RequestCtx):

    def getEntityType(self):
        return CTRL_ENTITY_TYPE.PREBATTLE

    def getPrbType(self):
        return getPrebattleType()

    def getPrbTypeName(self):
        return getPrebattleTypeName(self.getPrbType())


class _PrbEntryCtx(_PrbRequestCtx):

    def __init__(self, waitingID = '', funcExit = prb_settings.FUNCTIONAL_EXIT.NO_FUNC, guiExit = prb_settings.GUI_EXIT.HANGAR):
        super(_PrbEntryCtx, self).__init__(waitingID=waitingID)
        self.__funcExit = funcExit
        self.__guiExit = guiExit

    def getFuncExit(self):
        return self.__funcExit

    def getGuiExit(self):
        return self.__guiExit


class TeamSettingsCtx(_PrbEntryCtx):

    def __init__(self, waitingID = '', isOpened = True, comment = '', isRequestToCreate = True, funcExit = prb_settings.FUNCTIONAL_EXIT.PREBATTLE, guiExit = prb_settings.GUI_EXIT.HANGAR):
        super(TeamSettingsCtx, self).__init__(waitingID=waitingID, funcExit=funcExit, guiExit=guiExit)
        self.__isOpened = isOpened
        self.__comment = truncate_utf8(comment, PREBATTLE_COMMENT_MAX_LENGTH)
        self.__isForced = False
        self._isRequestToCreate = isRequestToCreate

    def __repr__(self):
        return 'TeamSettingsCtx(waitingID = {0:>s}, isOpened = {1!r:s}, comment = {2:>s}, isRequestToCreate={3!r:s}'.format(self.getWaitingID(), self.__isOpened, self.__comment, self._isRequestToCreate)

    def getPrbType(self):
        return PREBATTLE_TYPE.COMPANY

    def getRequestType(self):
        if self._isRequestToCreate:
            return REQUEST_TYPE.CREATE
        return REQUEST_TYPE.CHANGE_SETTINGS

    def isOpened(self):
        return self.__isOpened

    def setOpened(self, isOpened):
        self.__isOpened = isOpened

    def getComment(self):
        return self.__comment

    def setComment(self, comment):
        self.__comment = truncate_utf8(comment, PREBATTLE_COMMENT_MAX_LENGTH)

    def isForced(self):
        return self.__isForced

    def setForced(self, flag):
        self.__isForced = flag

    def isOpenedChanged(self, settings):
        """
        Is setting 'isOpened' changed.
        
        @param settings: instance of prebattle_shared.PrebattleSettings.
        @return: True if setting 'isOpened' changed, otherwise - False.
        """
        return self.__isOpened != settings[prb_settings.PREBATTLE_SETTING_NAME.IS_OPENED]

    def isCommentChanged(self, settings):
        """
        Is comment changed in prebattle.
        
        @param settings: instance of prebattle_shared.PrebattleSettings.
        @return: True if setting 'comment' changed, otherwise - False.
        """
        return self.__comment != settings[prb_settings.PREBATTLE_SETTING_NAME.COMMENT]


class TrainingSettingsCtx(TeamSettingsCtx):

    def __init__(self, waitingID = '', isOpened = True, comment = '', isRequestToCreate = True, arenaTypeID = 0, roundLen = 900):
        super(TrainingSettingsCtx, self).__init__(waitingID=waitingID, isOpened=isOpened, comment=comment, isRequestToCreate=isRequestToCreate)
        self.__arenaTypeID = arenaTypeID
        self.__roundLen = int(roundLen)

    def __repr__(self):
        return 'TrainingSettingsCtx(waitingID = {0:>s}, isOpen = {1!r:s}, comment = {2:>s}, arenaTypeID={3:n}, roundLen={4:n} sec., isRequestToCreate={5!r:s})'.format(self.getWaitingID(), self.isOpened(), self.getComment(), self.__arenaTypeID, self.__roundLen, self._isRequestToCreate)

    @classmethod
    def fetch(cls, settings):
        return TrainingSettingsCtx(isOpened=settings['isOpened'], comment=settings['comment'], isRequestToCreate=False, arenaTypeID=settings['arenaTypeID'], roundLen=settings['roundLength'])

    def getPrbType(self):
        return PREBATTLE_TYPE.TRAINING

    def getArenaTypeID(self):
        return self.__arenaTypeID

    def setArenaTypeID(self, arenaTypeID):
        self.__arenaTypeID = arenaTypeID

    def getRoundLen(self):
        return self.__roundLen

    def setRoundLen(self, roundLen):
        self.__roundLen = int(roundLen)

    def isArenaTypeIDChanged(self, settings):
        return self.__arenaTypeID != settings[prb_settings.PREBATTLE_SETTING_NAME.ARENA_TYPE_ID]

    def isRoundLenChanged(self, settings):
        return self.__roundLen != settings[prb_settings.PREBATTLE_SETTING_NAME.ROUND_LENGTH]


class CompanySettingsCtx(TeamSettingsCtx):

    def __init__(self, waitingID = '', isOpened = True, comment = '', division = PREBATTLE_COMPANY_DIVISION.CHAMPION, isRequestToCreate = True):
        super(CompanySettingsCtx, self).__init__(waitingID, isOpened, comment, isRequestToCreate)
        self.__division = division

    def __repr__(self):
        return 'CompanySettingsCtx(waitingID = {0:>s}, isOpened = {1!r:s}, comment = {2:>s}, division = {3:n}, isRequestToCreate={4!r:s})'.format(self.getWaitingID(), self.isOpened(), self.getComment(), self.__division, self._isRequestToCreate)

    def getPrbType(self):
        return PREBATTLE_TYPE.COMPANY

    def getDivision(self):
        return self.__division

    def setDivision(self, division):
        self.__division = division

    def isDivisionChanged(self, settings):
        return self.__division != settings[prb_settings.PREBATTLE_SETTING_NAME.DIVISION]


class SquadSettingsCtx(_PrbRequestCtx):

    def __repr__(self):
        return 'SquadSettingsCtx(waitingID = {0:>s})'.format(self.getWaitingID())

    def getPrbType(self):
        return PREBATTLE_TYPE.SQUAD

    def getRequestType(self):
        return REQUEST_TYPE.CREATE


class _JoinPrbCtx(_PrbEntryCtx):

    def __init__(self, prbID, prbType, waitingID = '', funcExit = prb_settings.FUNCTIONAL_EXIT.NO_FUNC, guiExit = prb_settings.GUI_EXIT.HANGAR):
        super(_JoinPrbCtx, self).__init__(waitingID=waitingID, funcExit=funcExit, guiExit=guiExit)
        self.__prbID = int(prbID)
        self.__prbType = int(prbType)
        self.__isForced = False

    def getID(self):
        return self.__prbID

    def getRequestType(self):
        return REQUEST_TYPE.JOIN

    def getPrbType(self):
        return self.__prbType

    def isForced(self):
        return self.__isForced

    def setForced(self, flag):
        self.__isForced = flag


class JoinTrainingCtx(_JoinPrbCtx):

    def __init__(self, prbID, waitingID = ''):
        super(JoinTrainingCtx, self).__init__(prbID, PREBATTLE_TYPE.TRAINING, waitingID, prb_settings.FUNCTIONAL_EXIT.PREBATTLE)

    def __repr__(self):
        return 'JoinTrainingCtx(prbID = {0:n}, waitingID = {1:>s})'.format(self.getID(), self.getWaitingID())


class JoinCompanyCtx(_JoinPrbCtx):

    def __init__(self, prbID, waitingID = ''):
        super(JoinCompanyCtx, self).__init__(prbID, PREBATTLE_TYPE.COMPANY, waitingID, prb_settings.FUNCTIONAL_EXIT.PREBATTLE)

    def __repr__(self):
        return 'JoinCompanyCtx(prbID = {0:n}, waitingID = {1:>s})'.format(self.getID(), self.getWaitingID())


class LeavePrbCtx(_PrbEntryCtx):

    def __init__(self, waitingID = '', funcExit = prb_settings.FUNCTIONAL_EXIT.NO_FUNC, guiExit = prb_settings.GUI_EXIT.HANGAR):
        super(LeavePrbCtx, self).__init__(waitingID, funcExit=funcExit, guiExit=guiExit)

    def __repr__(self):
        return 'LeavePrbCtx(prbID = {0:n}, prbType = {1:>s}, waitingID = {2:>s}, exit = {3!r:s}/{4!r:s})'.format(self.getID(), self.getPrbTypeName(), self.getWaitingID(), self.getFuncExit(), self.getGuiExit())

    def getRequestType(self):
        return REQUEST_TYPE.LEAVE

    def getID(self):
        return getPrebattleID()


class JoinBattleSessionCtx(_JoinPrbCtx):

    def __init__(self, prbID, prbType, waitingID):
        super(JoinBattleSessionCtx, self).__init__(prbID, prbType, waitingID, prb_settings.FUNCTIONAL_EXIT.PREBATTLE)

    def __repr__(self):
        return 'JoinBattleSessionCtx(prbID = {0:n}, type = {1:n}, waitingID = {2:>s})'.format(self.getID(), self.getPrbType(), self.getWaitingID())


class AssignPrbCtx(_PrbRequestCtx):

    def __init__(self, pID, roster, waitingID = ''):
        super(AssignPrbCtx, self).__init__(waitingID)
        self.__pID = pID
        self.__roster = roster

    def __repr__(self):
        return 'AssignPrbCtx(pID = {0:n}, roster = 0x{1:X}, prbType = {2:>s}, waitingID = {3:>s})'.format(self.__pID, self.__roster, self.getPrbTypeName(), self.getWaitingID())

    def getPlayerID(self):
        return self.__pID

    def getRoster(self):
        return self.__roster

    def getRequestType(self):
        return REQUEST_TYPE.ASSIGN


class SetTeamStateCtx(_PrbRequestCtx):

    def __init__(self, team, isReadyState, waitingID = '', isForced = True, gamePlayMask = 0):
        super(SetTeamStateCtx, self).__init__(waitingID)
        self.__team = team
        self.__isReadyState = isReadyState
        self.__isForced = isForced
        self.__gamePlayMask = gamePlayMask

    def __repr__(self):
        return 'SetTeamStateCtx(team = {0:n}, isReadyState = {1!r:s}, waitingID = {3:>s}, isForced = {4!r:s}, gamePlayMask = {5:n})'.format(self.__team, self.__isReadyState, self.getPrbTypeName(), self.getWaitingID(), self.__isForced, self.__gamePlayMask)

    def getTeam(self):
        return self.__team

    def isReadyState(self):
        return self.__isReadyState

    def isForced(self):
        return self.__isForced

    def getGamePlayMask(self):
        return self.__gamePlayMask

    def getRequestType(self):
        return REQUEST_TYPE.SET_TEAM_STATE


class SetPlayerStateCtx(_PrbRequestCtx):

    def __init__(self, isReadyState, waitingID = ''):
        super(SetPlayerStateCtx, self).__init__(waitingID)
        self.__isReadyState = isReadyState

    def __repr__(self):
        return 'SetPlayerStateCtx(vInventoryID = {0:n}, isReadyState = {1!r:s}, waitingID = {2:>s})'.format(self.getVehicleInventoryID(), self.__isReadyState, self.getWaitingID())

    def isReadyState(self):
        return self.__isReadyState

    def getRequestType(self):
        return REQUEST_TYPE.SET_PLAYER_STATE

    def getVehicleInventoryID(self):
        return g_currentVehicle.invID


class SwapTeamsCtx(_PrbRequestCtx):

    def __repr__(self):
        return 'SwapTeamsCtx(waitingID = {0:>s})'.format(self.getWaitingID())

    def getRequestType(self):
        return REQUEST_TYPE.SWAP_TEAMS


class ChangeArenaVoipCtx(_PrbRequestCtx):

    def __init__(self, channels, waitingID = ''):
        super(ChangeArenaVoipCtx, self).__init__(waitingID)
        self.__channels = int(channels)

    def __repr__(self):
        return 'ChangeArenaVoipCtx(channels = {0:n}, waitingID = {1:>s})'.format(self.__channels, self.getWaitingID())

    def getChannels(self):
        return self.__channels

    def getRequestType(self):
        return REQUEST_TYPE.CHANGE_ARENA_VOIP


class ChangeOpenedCtx(_PrbRequestCtx):

    def __init__(self, isOpened, waitingID = ''):
        super(ChangeOpenedCtx, self).__init__(waitingID)
        self.__isOpened = isOpened

    def __repr__(self):
        return 'ChangeOpenedCtx(isOpened = {0!r:s}, waitingID = {1:>s})'.format(self.__isOpened, self.getWaitingID())

    def isOpened(self):
        return self.__isOpened

    def isOpenedChanged(self, settings):
        return self.__isOpened != settings[prb_settings.PREBATTLE_SETTING_NAME.IS_OPENED]

    def getRequestType(self):
        return REQUEST_TYPE.CHANGE_OPENED


class ChangeCommentCtx(_PrbRequestCtx):

    def __init__(self, comment, waitingID = ''):
        super(ChangeCommentCtx, self).__init__(waitingID)
        self.__comment = truncate_utf8(comment, PREBATTLE_COMMENT_MAX_LENGTH)

    def __repr__(self):
        return 'ChangeCommentCtx(comment = {0:>s}, waitingID = {1:>s})'.format(self.__comment, self.getWaitingID())

    def getComment(self):
        return self.__comment

    def isCommentChanged(self, settings):
        return self.__comment != settings[prb_settings.PREBATTLE_SETTING_NAME.COMMENT]

    def getRequestType(self):
        return REQUEST_TYPE.CHANGE_COMMENT


class ChangeDivisionCtx(_PrbRequestCtx):

    def __init__(self, division, waitingID = ''):
        super(ChangeDivisionCtx, self).__init__(waitingID)
        self.__division = int(division)

    def __repr__(self):
        return 'ChangeArenaVoipCtx(division = {0:n}, waitingID = {1:>s})'.format(self.__division, self.getWaitingID())

    def getDivision(self):
        return self.__division

    def isDivisionChanged(self, settings):
        return self.__division != settings[prb_settings.PREBATTLE_SETTING_NAME.DIVISION]

    def getRequestType(self):
        return REQUEST_TYPE.CHANGE_DIVISION


class KickPlayerCtx(_PrbRequestCtx):

    def __init__(self, pID, waitingID = ''):
        super(KickPlayerCtx, self).__init__(waitingID)
        self.__pID = pID

    def __repr__(self):
        return 'KickPlayerCtx(pID = {0:n}, waitingID = {1:>s})'.format(self.__pID, self.getWaitingID())

    def getPlayerID(self):
        return self.__pID

    def getRequestType(self):
        return REQUEST_TYPE.KICK


class RequestCompaniesCtx(object):
    __slots__ = ('isNotInBattle', 'division', 'creatorMask')

    def __init__(self, isNotInBattle = False, division = 0, creatorMask = ''):
        super(RequestCompaniesCtx, self).__init__()
        self.isNotInBattle = isNotInBattle
        self.creatorMask = creatorMask
        if division in PREBATTLE_COMPANY_DIVISION.RANGE:
            self.division = division
        else:
            self.division = 0

    def __repr__(self):
        return 'RequestCompaniesCtx(isNotInBattle = {0!r:s}, division = {1:n}, creatorMask = {2:>s})'.format(self.isNotInBattle, self.division, self.creatorMask)

    def byDivision(self):
        return self.division in PREBATTLE_COMPANY_DIVISION.RANGE

    def byName(self):
        return self.creatorMask is not None and len(self.creatorMask)


class SendInvitesCtx(_PrbRequestCtx):

    def __init__(self, databaseIDs, comment, waitingID = ''):
        super(SendInvitesCtx, self).__init__(waitingID)
        self.__databaseIDs = databaseIDs[:300]
        if comment:
            self.__comment = truncate_utf8(comment, prb_settings.INVITE_COMMENT_MAX_LENGTH)
        else:
            self.__comment = ''

    def __repr__(self):
        return 'SendInvitesCtx(databaseIDs = {0!r:s}, comment = {1:>s})'.format(self.__databaseIDs, self.__comment)

    def getDatabaseIDs(self):
        return self.__databaseIDs[:]

    def getComment(self):
        return self.__comment

    def getRequestType(self):
        return REQUEST_TYPE.SEND_INVITE


class _UnitRequestCtx(_RequestCtx):

    def __init__(self, waitingID = ''):
        super(_UnitRequestCtx, self).__init__(waitingID)
        self.__isForced = False

    def getEntityType(self):
        return CTRL_ENTITY_TYPE.UNIT

    def getUnitIdx(self):
        return getUnitIdx()

    def isForced(self):
        return self.__isForced

    def setForced(self, flag):
        self.__isForced = flag


class _UnitEntryCtx(_UnitRequestCtx):

    def __init__(self, waitingID = '', funcExit = prb_settings.FUNCTIONAL_EXIT.NO_FUNC, guiExit = prb_settings.GUI_EXIT.HANGAR):
        super(_UnitEntryCtx, self).__init__(waitingID)
        self.__funcExit = funcExit
        self.__guiExit = guiExit

    def getFuncExit(self):
        return self.__funcExit

    def getGuiExit(self):
        return self.__guiExit


class CreateUnitCtx(_UnitEntryCtx):

    def __init__(self, waitingID = '', rosterID = 0):
        super(CreateUnitCtx, self).__init__(waitingID=waitingID, funcExit=prb_settings.FUNCTIONAL_EXIT.UNIT)
        self.__rosterID = rosterID

    def __repr__(self):
        return 'CreateUnitCtx(rosterID = {0:n}, waitingID = {1:>s})'.format(self.getRosterID(), self.getWaitingID())

    def getRequestType(self):
        return REQUEST_TYPE.CREATE

    def getRosterID(self):
        return self.__rosterID


class JoinUnitCtx(_UnitEntryCtx):

    def __init__(self, unitMgrID, slotIdx = None, waitingID = ''):
        super(JoinUnitCtx, self).__init__(waitingID=waitingID, funcExit=prb_settings.FUNCTIONAL_EXIT.UNIT)
        self.__unitMgrID = unitMgrID
        self.__slotIdx = slotIdx

    def __repr__(self):
        return 'JoinUnitCtx(unitMgrID = {0:n}, waitingID = {1:>s})'.format(self.getID(), self.getWaitingID())

    def getRequestType(self):
        return REQUEST_TYPE.JOIN

    def getID(self):
        return self.__unitMgrID

    def getSlotIdx(self):
        return self.__slotIdx


class LeaveUnitCtx(_UnitEntryCtx):

    def __init__(self, waitingID = '', funcExit = prb_settings.FUNCTIONAL_EXIT.NO_FUNC):
        super(LeaveUnitCtx, self).__init__(waitingID=waitingID, funcExit=funcExit)

    def __repr__(self):
        return 'LeaveUnitCtx(unitIdx = {0:n}, exit = {1!r:s}/{2!r:s}, waitingID = {3:>s})'.format(self.getID(), self.getFuncExit(), self.getGuiExit(), self.getWaitingID())

    def getRequestType(self):
        return REQUEST_TYPE.LEAVE

    def getID(self):
        return getUnitIdx()


class LockUnitCtx(_UnitRequestCtx):

    def __init__(self, isLocked = True, waitingID = ''):
        super(LockUnitCtx, self).__init__(waitingID)
        self.__isLocked = isLocked

    def __repr__(self):
        return 'LockUnitCtx(unitIdx = {0:n}, isLocked = {1!r:s}, waitingID = {2:>s})'.format(self.getUnitIdx(), self.__isLocked, self.getWaitingID())

    def getRequestType(self):
        return REQUEST_TYPE.LOCK

    def isLocked(self):
        return self.__isLocked


class CloseSlotCtx(_UnitRequestCtx):

    def __init__(self, slotIdx, isClosed = True, waitingID = ''):
        super(CloseSlotCtx, self).__init__(waitingID)
        self.__slotIdx = slotIdx
        self.__isClosed = isClosed

    def __repr__(self):
        return 'CloseSlotCtx(unitIdx = {0:n}, slotIdx = {1:n}, isClosed = {2!r:s}, waitingID = {3:>s})'.format(self.getUnitIdx(), self.__slotIdx, self.__isClosed, self.getWaitingID())

    def getRequestType(self):
        return REQUEST_TYPE.CLOSE_SLOT

    def getSlotIdx(self):
        return self.__slotIdx

    def isClosed(self):
        return self.__isClosed


class SetVehicleUnitCtx(_UnitRequestCtx):

    def __init__(self, vTypeCD = 0, vehInvID = 0, waitingID = ''):
        super(SetVehicleUnitCtx, self).__init__(waitingID)
        self.__vehTypeCD = vTypeCD
        self.__vehInvID = vehInvID

    def __repr__(self):
        return 'SetVehicleUnitCtx(vTypeCD = {0:n}, vehInvID = {1:n}, waitingID = {2:>s})'.format(self.__vehTypeCD, self.__vehInvID, self.getWaitingID())

    def getRequestType(self):
        return REQUEST_TYPE.SET_VEHICLE

    def getVehTypeCD(self):
        return self.__vehTypeCD

    def getVehInvID(self):
        return self.__vehInvID


class ChangeOpenedUnitCtx(_UnitRequestCtx):

    def __init__(self, isOpened, waitingID = ''):
        super(ChangeOpenedUnitCtx, self).__init__(waitingID)
        self.__isOpened = isOpened

    def __repr__(self):
        return 'ChangeOpenedUnitCtx(unitIdx = {0:n}, isOpened = {1!r:s}, waitingID = {2:>s})'.format(self.getUnitIdx(), self.__isOpened, self.getWaitingID())

    def getRequestType(self):
        return prb_settings.REQUEST_TYPE.CHANGE_OPENED

    def isOpened(self):
        return self.__isOpened


class ChangeCommentUnitCtx(_UnitRequestCtx):

    def __init__(self, comment, waitingID = ''):
        super(ChangeCommentUnitCtx, self).__init__(waitingID)
        self.__comment = truncate_utf8(comment, prb_settings.UNIT_COMMENT_MAX_LENGTH)

    def __repr__(self):
        return 'ChangeCommentUnitCtx(unitIdx = {0:n}, comment = {1:>s}, waitingID = {2:>s})'.format(self.getUnitIdx(), self.__comment, self.getWaitingID())

    def getRequestType(self):
        return REQUEST_TYPE.CHANGE_COMMENT

    def getComment(self):
        return self.__comment

    def isCommentChanged(self, unit):
        return self.__comment != unit._strComment


class SetReadyUnitCtx(_UnitRequestCtx):

    def __init__(self, isReady = True, waitingID = ''):
        super(SetReadyUnitCtx, self).__init__(waitingID)
        self.__isReady = isReady

    def __repr__(self):
        return 'SetReadyUnitCtx(unitIdx = {0:n}, isReady = {1!r:s}, waitingID = {2:>s})'.format(self.getUnitIdx(), self.__isReady, self.getWaitingID())

    def isReady(self):
        return self.__isReady

    def getRequestType(self):
        return REQUEST_TYPE.SET_PLAYER_STATE


class AssignUnitCtx(_UnitRequestCtx):

    def __init__(self, pID, slotIdx, waitingID = ''):
        super(AssignUnitCtx, self).__init__(waitingID)
        self.__pID = pID
        self.__slotIdx = slotIdx

    def __repr__(self):
        return 'AssignUnitCtx(unitIdx = {0:n}, pID = {1:n}, slotIdx = {2:n}, waitingID = {3:>s})'.format(self.getUnitIdx(), self.__pID, self.__slotIdx, self.getWaitingID())

    def getRequestType(self):
        return REQUEST_TYPE.ASSIGN

    def getPlayerID(self):
        return self.__pID

    def getSlotIdx(self):
        return self.__slotIdx


class AutoSearchUnitCtx(_UnitRequestCtx):

    def __init__(self, waitingID = '', action = 1, vehTypes = None):
        super(AutoSearchUnitCtx, self).__init__(waitingID)
        self.__action = action
        self.__vehTypes = [] if vehTypes is None else vehTypes
        return

    def __repr__(self):
        return 'AutoSearchUnitCtx(action = {0:>s}, vehTypes = {1!r:s}, waitingID = {2:>s})'.format('start' if self.__action > 0 else 'stop', self.__vehTypes, self.getWaitingID())

    def getRequestType(self):
        return REQUEST_TYPE.AUTO_SEARCH

    def isRequestToStart(self):
        return self.__action > 0

    def getVehTypes(self):
        return self.__vehTypes


class AcceptSearchUnitCtx(_UnitRequestCtx):

    def __repr__(self):
        return 'AcceptSearchUnitCtx(waitingID = {0:>s})'.format(self.getWaitingID())

    def getRequestType(self):
        return REQUEST_TYPE.ACCEPT_SEARCH


class BattleQueueUnitCtx(_UnitRequestCtx):

    def __init__(self, waitingID = '', action = 1, vehTypes = None):
        super(BattleQueueUnitCtx, self).__init__(waitingID)
        self.__action = action
        self.__vehTypes = [] if vehTypes is None else vehTypes
        return

    def __repr__(self):
        return 'BattleQueueUnitCtx(action = {0:>s}, waitingID = {1:>s})'.format('start' if self.__action > 0 else 'stop', self.getWaitingID())

    def getRequestType(self):
        return REQUEST_TYPE.BATTLE_QUEUE

    def isRequestToStart(self):
        return self.__action > 0


class RosterSlotCtx(object):

    def __init__(self, vehTypeCD = None, nationNames = None, levels = None, vehClassNames = None):
        self.__vehTypeCD = vehTypeCD
        self.__nationNames = nationNames or []
        self.__vehLevels = levels or (1, 8)
        self.__vehClassNames = vehClassNames or []

    def getCriteria(self):
        criteria = {}
        if self.__vehTypeCD:
            criteria['vehTypeID'] = self.__vehTypeCD
        else:
            criteria['nationNames'] = self.__nationNames
            criteria['levels'] = self.__vehLevels
            criteria['vehClassNames'] = self.__vehClassNames
        return criteria


class SetRostersSlotsCtx(_UnitRequestCtx):

    def __init__(self, waitingID = ''):
        super(SetRostersSlotsCtx, self).__init__(waitingID)
        self.__items = {}

    def __repr__(self):
        return 'SetRostersSlotsCtx(rostersSlots = {0!r:s}, waitingID = {1:>s})'.format(self.__items, self.getWaitingID())

    def getRequestType(self):
        return REQUEST_TYPE.SET_ROSTERS_SLOTS

    def addRosterSlot(self, rosterSlotIdx, ctx):
        self.__items[rosterSlotIdx] = ctx.getCriteria()

    def getRosterSlots(self):
        return self.__items.copy()


class PrebattleAction(object):
    __slots__ = ('actionName', 'mapID')

    def __init__(self, actionName, mapID = 0):
        self.actionName = actionName if actionName is not None else ''
        self.mapID = mapID
        return

    def __repr__(self):
        return 'PrebattleAction(name = {0:>s}, mapID = {1:n}'.format(self.actionName, self.mapID)


class StartDispatcherCtx(object):
    __slots__ = ['isInRandomQueue', 'isInTutorialQueue', 'prebattleID']

    def __init__(self, **kwargs):
        super(StartDispatcherCtx, self).__init__()
        self.isInRandomQueue = kwargs.get('isInRandomQueue', False)
        self.isInTutorialQueue = kwargs.get('isInTutorialQueue', False)
        self.prebattleID = kwargs.get('prebattleID', 0L)

    def __repr__(self):
        return 'StartDispatcherCtx(inRandomQueue = {1!r:s}, inTutorialQueue = {2!r:s}, prebattleID = {3:n})'.format(self.isInRandomQueue, self.isInTutorialQueue, self.prebattleID)

    @classmethod
    def fetch(cls):
        player = BigWorld.player()
        prbID = getPrebattleID()
        return StartDispatcherCtx(isInRandomQueue=getattr(player, 'isInRandomQueue', False), isInTutorialQueue=getattr(player, 'isInTutorialQueue', False), prebattleID=prbID)
# okay decompyling res/scripts/client/gui/prb_control/context.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:25:37 EST

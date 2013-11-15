# 2013.11.15 11:25:45 EST
# Embedded file name: scripts/client/gui/prb_control/restrictions/interfaces.py


class IGUIPermissions(object):

    def canExitFromRandomQueue(self):
        return True

    def canChangeVehicle(self):
        return True


class IPrbPermissions(IGUIPermissions):

    def canSendInvite(self):
        return False

    def canKick(self, team = 1):
        return False

    def canAssignToTeam(self, team = 1):
        return False

    def canChangePlayerTeam(self):
        return False

    def canSetTeamState(self, team = 1):
        return False

    def canMakeOpenedClosed(self):
        return False

    def canChangeComment(self):
        return False

    def canChangeArena(self):
        return False

    def canChangeArenaVOIP(self):
        return False

    def canChangeDivision(self):
        return False

    def canChangeGamePlayMask(self):
        return False

    @classmethod
    def isCreator(cls, roles):
        return False


class IUnitPermissions(IGUIPermissions):

    def canSendInvite(self):
        return False

    def canKick(self):
        return False

    def canChangeUnitState(self):
        return False

    def canChangeRosters(self):
        return False

    def canSetVehicle(self):
        return False

    def canChangeClosedSlots(self):
        return False

    def canAssignToSlot(self, dbID):
        return False

    def canReassignToSlot(self):
        return False

    def canChangeComment(self):
        return False

    def canInvokeAutoSearch(self):
        return True

    def canStartBattleQueue(self):
        return False

    def canStopBattleQueue(self):
        return False

    @classmethod
    def isCreator(cls, roles):
        return False


class IVehicleLimit(object):

    def check(self, teamLimits):
        return (True, '')


class ITeamLimit(object):

    def check(self, rosters, team, teamLimits):
        return (True, '')
# okay decompyling res/scripts/client/gui/prb_control/restrictions/interfaces.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:25:45 EST

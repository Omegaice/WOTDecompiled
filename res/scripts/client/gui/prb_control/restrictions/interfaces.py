

class IPermissions(object):

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

    def canExitFromRandomQueue(self):
        return True

    def canChangeVehicle(self):
        return True

    @classmethod
    def isCreator(cls, roles):
        return False


class IVehicleLimit(object):

    def check(self, teamLimits):
        return (True, '')


class ITeamLimit(object):

    def check(self, rosters, team, teamLimits):
        return (True, '')

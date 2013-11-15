# 2013.11.15 11:25:45 EST
# Embedded file name: scripts/client/gui/prb_control/restrictions/__init__.py
from prebattle_shared import decodeRoster

def createPermissions(functional, pID = None):
    clazz = functional._permClass
    rosterKey = functional.getRosterKey(pID=pID)
    if rosterKey is not None:
        team, _ = decodeRoster(rosterKey)
        rosterInfo = functional.getPlayerInfo(pID=pID, rosterKey=rosterKey)
        if rosterInfo is not None:
            return clazz(roles=functional.getRoles(pDatabaseID=rosterInfo.dbID), pState=rosterInfo.state, teamState=functional.getTeamState(team=team))
    return clazz()
# okay decompyling res/scripts/client/gui/prb_control/restrictions/__init__.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:25:45 EST

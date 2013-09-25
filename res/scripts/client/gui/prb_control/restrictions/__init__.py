from prebattle_shared import decodeRoster

def createPermissions(functional, pID = None):
    clazz = functional._permClass
    rosterKey = functional.getRosterKey(pID=pID)
    team, _ = decodeRoster(rosterKey)
    rosterInfo = functional.getPlayerInfo(pID=pID, rosterKey=rosterKey)
    if rosterInfo is not None:
        permissions = clazz(roles=functional.getRoles(pDatabaseID=rosterInfo.dbID), pState=rosterInfo.state, teamState=functional.getTeamState(team=team))
    else:
        permissions = clazz()
    return permissions

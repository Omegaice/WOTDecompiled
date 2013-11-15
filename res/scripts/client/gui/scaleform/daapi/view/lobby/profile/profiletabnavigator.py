# 2013.11.15 11:26:11 EST
# Embedded file name: scripts/client/gui/Scaleform/daapi/view/lobby/profile/ProfileTabNavigator.py
from gui.Scaleform.daapi.view.lobby.profile.ProfileSection import ProfileSection
from gui.Scaleform.daapi.view.meta.ProfileTabNavigatorMeta import ProfileTabNavigatorMeta

class ProfileTabNavigator(ProfileTabNavigatorMeta):

    def __init__(self, *args):
        ProfileTabNavigatorMeta.__init__(self)
        self.__userName = args[0]
        self.__userID = args[1]
        self.__databaseID = args[2]
        self.__initInfo = args[3]

    def invokeUpdate(self):
        for component in self.components.itervalues():
            if isinstance(component, ProfileSection):
                component.invokeUpdate()

    def _populate(self):
        self.as_setInitDataS(self.__initInfo)
        super(ProfileTabNavigator, self)._populate()

    def registerFlashComponent(self, component, alias, *args):
        super(ProfileTabNavigator, self).registerFlashComponent(component, alias, self.__userName, self.__userID, self.__databaseID)
# okay decompyling res/scripts/client/gui/scaleform/daapi/view/lobby/profile/profiletabnavigator.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:26:11 EST

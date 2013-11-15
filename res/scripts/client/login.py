# 2013.11.15 11:27:09 EST
# Embedded file name: scripts/client/Login.py
import BigWorld
from PlayerEvents import g_playerEvents
from ConnectionManager import connectionManager
from debug_utils import *

class PlayerLogin(BigWorld.Entity):

    def __init__(self):
        pass

    def onBecomePlayer(self):
        pass

    def onBecomeNonPlayer(self):
        pass

    def onKickedFromServer(self, checkoutPeripheryID):
        LOG_MX('onKickedFromServer', checkoutPeripheryID)
        g_playerEvents.onKickWhileLoginReceived(checkoutPeripheryID)

    def receiveLoginQueueNumber(self, queueNumber):
        LOG_MX('receiveLoginQueueNumber', queueNumber)
        g_playerEvents.onLoginQueueNumberReceived(queueNumber)

    def handleKeyEvent(self, event):
        return False


Login = PlayerLogin
# okay decompyling res/scripts/client/login.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:27:09 EST

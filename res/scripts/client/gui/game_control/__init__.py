# 2013.11.15 11:25:34 EST
# Embedded file name: scripts/client/gui/game_control/__init__.py
import BigWorld
from gui.game_control.roaming import RoamingController
from gui.game_control.AOGAS import AOGASController
from gui.game_control.captcha_control import CaptchaController
from gui.game_control.GameSessionController import GameSessionController
from gui.game_control.IGR import IGRController
from gui.game_control.wallet import WalletController

class _GameControllers(object):

    def __init__(self):
        super(_GameControllers, self).__init__()
        self.__roaming = RoamingController()
        self.__captcha = CaptchaController()
        self.__aogas = AOGASController()
        self.__gameSession = GameSessionController()
        self.__igr = IGRController()
        self.__wallet = WalletController()

    @property
    def captcha(self):
        return self.__captcha

    @property
    def aogas(self):
        return self.__aogas

    @property
    def gameSession(self):
        return self.__gameSession

    @property
    def igr(self):
        return self.__igr

    @property
    def roaming(self):
        return self.__roaming

    @property
    def wallet(self):
        return self.__wallet

    def init(self):
        self.__captcha.init()
        self.__aogas.init()
        self.__gameSession.init()
        self.__igr.init()
        self.__roaming.init()
        self.__wallet.init()

    def fini(self):
        self.__igr.fini()
        self.__captcha.fini()
        self.__aogas.fini()
        self.__gameSession.fini()
        self.__roaming.fini()
        self.__wallet.fini()

    def onAccountShowGUI(self, ctx):
        self.__captcha.start()
        self.__aogas.start(ctx)
        self.__gameSession.start(ctx.get('sessionStartedAt', -1))
        self.__igr.start(ctx)
        self.__wallet.start()

    def onAvatarBecomePlayer(self):
        self.__aogas.disableNotifyAccount()
        self.__gameSession.stop(True)
        self.__roaming.stop()

    def onAccountBecomePlayer(self):
        self.__roaming.start(BigWorld.player().serverSettings)

    def onDisconnected(self):
        self.__aogas.stop()
        self.__gameSession.stop()
        self.__igr.clear()
        self.__roaming.onDisconnected()


g_instance = _GameControllers()
# okay decompyling res/scripts/client/gui/game_control/__init__.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:25:34 EST

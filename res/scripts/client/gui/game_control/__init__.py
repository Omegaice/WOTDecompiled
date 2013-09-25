from gui.game_control.AOGAS import AOGASController
from gui.game_control.captcha_control import CaptchaController
from gui.game_control.GameSessionController import GameSessionController
from gui.game_control.IGR import IGRController

class _GameControllers(object):

    def __init__(self):
        super(_GameControllers, self).__init__()
        self.__captcha = CaptchaController()
        self.__aogas = AOGASController()
        self.__gameSession = GameSessionController()
        self.__igr = IGRController()

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

    def init(self):
        self.__captcha.init()
        self.__aogas.init()
        self.__gameSession.init()
        self.__igr.init()

    def fini(self):
        self.__igr.fini()
        self.__captcha.fini()
        self.__aogas.fini()
        self.__gameSession.fini()

    def onAccountShowGUI(self, ctx):
        self.__captcha.start()
        self.__aogas.start(ctx)
        self.__gameSession.start(ctx.get('sessionStartedAt', -1))
        self.__igr.start(ctx)

    def onAvatarBecomePlayer(self):
        self.__aogas.disableNotifyAccount()
        self.__gameSession.stop(True)

    def onDisconnected(self):
        self.__aogas.stop()
        self.__gameSession.stop()
        self.__igr.clear()


g_instance = _GameControllers()

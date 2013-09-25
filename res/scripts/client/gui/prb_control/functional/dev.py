import random
import ArenaType
import BigWorld
import Keys
import Settings
from debug_utils import LOG_ERROR
from gui import InputHandler
from gui.prb_control import context
from gui.prb_control.functional.training import TrainingEntry, TrainingFunctional
from gui.prb_control.functional.interfaces import IPrbEntry
USER_PREF_KEY_DEVELOPMENT = 'development'

def init():
    InputHandler.g_instance.onKeyDown += handleKeyDown
    wrapFunctional()


def fini():
    InputHandler.g_instance.onKeyDown -= handleKeyDown


def handleKeyDown(event):
    if event.key is Keys.KEY_B and event.isCtrlDown():
        createDevPrbEntry()


def wrapFunctional():

    def wrapper(func):

        def wrapper(*args, **kwargs):
            if len(args) > 1:
                storeSettingsCtx(args[1])
            func(*args, **kwargs)

        return wrapper

    TrainingEntry.create = wrapper(TrainingEntry.create)
    TrainingFunctional.changeSettings = wrapper(TrainingFunctional.changeSettings)


def createDevPrbEntry():
    userPrefs = Settings.g_instance.userPrefs
    isStored = False
    if not userPrefs.has_key(USER_PREF_KEY_DEVELOPMENT):
        userPrefs.write(USER_PREF_KEY_DEVELOPMENT, '')
        isStored = True
    ds = userPrefs[USER_PREF_KEY_DEVELOPMENT]
    arenaTypeID = ds.readInt('storedArenaTypeID')
    roundLength = ds.readInt('storedRoundLength')
    if arenaTypeID > 0 and arenaTypeID not in ArenaType.g_cache:
        LOG_ERROR('User preferences: arena not found', arenaTypeID)
        arenaTypeID = 0
    if arenaTypeID is 0:
        arenaTypeID = random.choice(ArenaType.g_cache.keys())
        isStored = True
    if roundLength is 0:
        roundLength = 900
        isStored = True
    ctx = context.TrainingSettingsCtx(arenaTypeID=arenaTypeID, roundLen=roundLength)
    if isStored:
        storeSettingsCtx(ctx)
    DevEntry().create(ctx)


def storeSettingsCtx(ctx):
    userPrefs = Settings.g_instance.userPrefs
    ds = userPrefs[USER_PREF_KEY_DEVELOPMENT]
    if ds is not None:
        ds.writeInt('storedArenaTypeID', ctx.getArenaTypeID())
        ds.writeInt('storedRoundLength', ctx.getRoundLen())
    else:
        LOG_ERROR('User preferences: can not write section USER_PREF_KEY_DEVELOPMENT')
    return


class DevEntry(IPrbEntry):

    def doAction(self, action, dispatcher = None):
        return False

    def create(self, ctx, callback = None):
        player = BigWorld.player()
        player.prb_createDev(ctx.getArenaTypeID(), ctx.getRoundLen(), player.name)

    def join(self, ctx, callback = None):
        super(DevEntry, self).join(ctx, callback)

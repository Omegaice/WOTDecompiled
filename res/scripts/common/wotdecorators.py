# Embedded file name: scripts/common/wotdecorators.py
from debug_utils import LOG_WRAPPED_CURRENT_EXCEPTION
from debug_utils import LOG_WARNING
import time

def noexcept(func):

    def wrapper(*args, **kwArgs):
        try:
            return func(*args, **kwArgs)
        except:
            LOG_WRAPPED_CURRENT_EXCEPTION(wrapper.__name__, func.__name__, func.func_code.co_filename, func.func_code.co_firstlineno + 1)

    return wrapper


def nofail(func):

    def wrapper(*args, **kwArgs):
        try:
            return func(*args, **kwArgs)
        except:
            LOG_WRAPPED_CURRENT_EXCEPTION(wrapper.__name__, func.__name__, func.func_code.co_filename, func.func_code.co_firstlineno + 1)
            import sys
            sys.exit()

    return wrapper


def exposedtoclient(func):

    def wrapper(*args, **kwArgs):
        try:
            lastTick = time.time()
            result = func(*args, **kwArgs)
            timeSinceLastTick = time.time() - lastTick
            if timeSinceLastTick > 0.02:
                LOG_WARNING('Took %.2f sec!' % timeSinceLastTick, args[0].id, func.__name__, args, kwArgs)
            return result
        except:
            LOG_WRAPPED_CURRENT_EXCEPTION(wrapper.__name__, func.__name__, func.func_code.co_filename, func.func_code.co_firstlineno + 1)

    return wrapper
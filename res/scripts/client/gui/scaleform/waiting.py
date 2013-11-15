# 2013.11.15 11:26:46 EST
# Embedded file name: scripts/client/gui/Scaleform/Waiting.py
import BigWorld
import Keys
from helpers import i18n
from debug_utils import LOG_DEBUG, LOG_WARNING

class Waiting:
    __waitingStack = []
    __suspendStack = []
    __isVisible = False

    @classmethod
    def isVisible(cls):
        return cls.__isVisible

    @classmethod
    def isOpened(cls, msg):
        return msg in cls.__waitingStack

    @staticmethod
    def show(message, isSingle = False, interruptCallback = lambda : None):
        BigWorld.Screener.setEnabled(False)
        if isSingle:
            if not message in Waiting.__waitingStack:
                Waiting.__waitingStack.append(message)
            from gui.WindowsManager import g_windowsManager
            if g_windowsManager.window is not None:
                waitingView = g_windowsManager.window.waitingManager
                waitingView is not None and waitingView.showS(i18n.makeString('#waiting:%s' % message))
                Waiting.__isVisible = True
                waitingView.setCallback(interruptCallback)
        return

    @staticmethod
    def suspend():
        if Waiting.isSuspended():
            return
        Waiting.__suspendStack = list(Waiting.__waitingStack)
        Waiting.close()

    @staticmethod
    def resume():
        if not Waiting.isSuspended():
            return
        for id in Waiting.__suspendStack:
            Waiting.show(id)

        Waiting.__suspendStack = []

    @staticmethod
    def isSuspended():
        return len(Waiting.__suspendStack) > 0

    @staticmethod
    def hide(message):
        stack = Waiting.__suspendStack
        if message in stack:
            stack.remove(message)
        try:
            stack = Waiting.__waitingStack
            if message in stack:
                stack.remove(message)
        except:
            pass

        if len(Waiting.__waitingStack) == 0:
            Waiting.close()

    @staticmethod
    def close():
        BigWorld.Screener.setEnabled(True)
        from gui.WindowsManager import g_windowsManager
        if g_windowsManager.window is not None and g_windowsManager.window.waitingManager is not None:
            g_windowsManager.window.waitingManager.close()
        Waiting.__isVisible = False
        Waiting.__waitingStack = []
        return

    @staticmethod
    def rollback():
        Waiting.__suspendStack = []
        Waiting.close()
# okay decompyling res/scripts/client/gui/scaleform/waiting.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:26:46 EST

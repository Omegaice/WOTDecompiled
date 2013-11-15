# 2013.11.15 11:26:09 EST
# Embedded file name: scripts/client/gui/Scaleform/daapi/view/lobby/prb_windows/ReceivedInviteWindow.py
from gui.shared import actions
from gui.Scaleform.daapi.view.meta.ReceivedInviteWindowMeta import ReceivedInviteWindowMeta
from gui.Scaleform.daapi.view.meta.WindowViewMeta import WindowViewMeta
from gui.Scaleform.framework.entities.View import View
from gui.prb_control.formatters.invites import PrbInviteInfo
from gui.prb_control.prb_helpers import prbInvitesProperty, GlobalListener
__author__ = 'd_savitski'

class ReceivedInviteWindow(View, WindowViewMeta, GlobalListener, ReceivedInviteWindowMeta):

    def __init__(self, ctx):
        super(ReceivedInviteWindow, self).__init__()
        self._inviteInfo = PrbInviteInfo(ctx.get('inviteID'))

    @prbInvitesProperty
    def prbInvites(self):
        pass

    def acceptInvite(self):
        postActions = []
        if self.prbDispatcher.hasModalEntity():
            postActions.append(actions.LeavePrbModalEntity())
        inviteID = self._inviteInfo.getID()
        invite, _ = self.prbInvites.getReceivedInvite(inviteID)
        if invite.anotherPeriphery:
            postActions.append(actions.DisconnectFromPeriphery())
            postActions.append(actions.ConnectToPeriphery(invite.peripheryID))
            postActions.append(actions.PrbInvitesInit())
        self.prbInvites.acceptInvite(inviteID, postActions=postActions)
        self.onWindowClose()

    def declineInvite(self):
        self.prbInvites.declineInvite(self._inviteInfo.getID())
        self.onWindowClose()

    def cancelInvite(self):
        self.onWindowClose()

    def onWindowClose(self):
        self.destroy()

    def onPrbFunctionalInited(self):
        self.__updateReceivedInfo()

    def onPrbFunctionalFinished(self):
        self.__updateReceivedInfo()

    def onTeamStatesReceived(self, functional, team1State, team2State):
        self.__updateReceivedInfo()

    def onIntroUnitFunctionalInited(self):
        self.__updateReceivedInfo()

    def onIntroUnitFunctionalFinished(self):
        self.__updateReceivedInfo()

    def onUnitFunctionalInited(self):
        self.__updateReceivedInfo()

    def onUnitFunctionalFinished(self):
        self.__updateReceivedInfo()

    def onUnitStateChanged(self, state, timeLeft):
        self.__updateReceivedInfo()

    def _populate(self):
        super(ReceivedInviteWindow, self)._populate()
        self.startGlobalListening()
        self.prbInvites.onReceivedInviteListModified += self.__invitesListModified
        self.as_setTitleS(self._inviteInfo.getTitle())
        self.__updateReceivedInfo()

    def _dispose(self):
        self._inviteInfo = None
        self.stopGlobalListening()
        self.prbInvites.onReceivedInviteListModified -= self.__invitesListModified
        super(ReceivedInviteWindow, self)._dispose()
        return

    def __updateReceivedInfo(self):
        self.as_setReceivedInviteInfoS(self._inviteInfo.as_dict())

    def __invitesListModified(self, added, changed, deleted):
        inviteID = self._inviteInfo.getID()
        if len(deleted) > 0 and inviteID in deleted:
            self.onWindowClose()
            return
        if len(changed) > 0 and inviteID in changed:
            self.__updateReceivedInfo()
# okay decompyling res/scripts/client/gui/scaleform/daapi/view/lobby/prb_windows/receivedinvitewindow.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:26:09 EST

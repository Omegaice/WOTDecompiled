# 2013.11.15 11:25:39 EST
# Embedded file name: scripts/client/gui/prb_control/formatters/invites.py
import BigWorld
from constants import PREBATTLE_TYPE, PREBATTLE_INVITE_STATE
from gui import makeHtmlString
from gui.prb_control.prb_helpers import prbInvitesProperty
from gui.prb_control.prb_helpers import prbDispatcherProperty
from helpers import i18n
import types
from predefined_hosts import g_preDefinedHosts
INVITES_I18N_FILE = 'invites'
DEFAULT_INVITE_I18N_TEXT_KEY = '#' + INVITES_I18N_FILE + ':invites/%s/invite'
PRB_INVITE_TEXT_I18N_KEYS = {PREBATTLE_INVITE_STATE.ACTIVE: DEFAULT_INVITE_I18N_TEXT_KEY,
 PREBATTLE_INVITE_STATE.ACCEPTED: '#' + INVITES_I18N_FILE + ':invites/%s/accept',
 PREBATTLE_INVITE_STATE.DECLINED: '#' + INVITES_I18N_FILE + ':invites/%s/reject',
 PREBATTLE_INVITE_STATE.EXPIRED: ('#' + INVITES_I18N_FILE + ':invites/%s/invalidInvite/sender-side', '#' + INVITES_I18N_FILE + ':invites/%s/invalidInvite/receiver-side')}
PRB_INVITE_NOTE_I18N_KEYS = {'change': '#' + INVITES_I18N_FILE + ':invites/note/server_change',
 'leave': '#' + INVITES_I18N_FILE + ':invites/note/%s/leave'}
INVITE_I18N_TITLE_KEY = '#' + INVITES_I18N_FILE + ':gui/titles/invite'
PREBATTLE_GUI_KEYS = {PREBATTLE_TYPE.SQUAD: 'squad',
 PREBATTLE_TYPE.COMPANY: 'company',
 PREBATTLE_TYPE.TRAINING: 'training',
 PREBATTLE_TYPE.CLAN: 'clan',
 PREBATTLE_TYPE.TOURNAMENT: 'tournament',
 PREBATTLE_TYPE.UNIT: 'unit'}
DEF_PREBATTLE_GUI_KEY = 'training'
ACCEPT_NOT_ALLOWED_I18N_STRING = [i18n.makeString('#{0:>s}:invites/prebattle/acceptNotAllowed/undefinedPeriphery'.format(INVITES_I18N_FILE)), i18n.makeString('#{0:>s}:invites/prebattle/acceptNotAllowed/otherPeriphery'.format(INVITES_I18N_FILE))]

def getLongDatetimeFormat(time):
    return BigWorld.wg_getLongDateFormat(time) + ' ' + BigWorld.wg_getLongTimeFormat(time)


class InviteFormatter(object):

    def getCtx(self, invite):
        return {'sender': invite.creatorFullName,
         'receiver': invite.receiverFullName}

    def getTypeName(self, _):
        return None

    def getTemplate(self, _):
        return None

    def format(self, invite):
        text = str()
        kargs = self.getCtx(invite)
        template = self.getTemplate(invite)
        typeName = self.getTypeName(invite)
        if template and typeName and kargs:
            if type(template) is types.TupleType:
                template = template[0] if invite.isPlayerSender() else template[1]
            template = template % typeName
            text = i18n.makeString(template, **kargs)
        return text


class PrbInviteTextFormatter(InviteFormatter):

    def getTypeName(self, invite):
        return PREBATTLE_GUI_KEYS.get(invite.type, DEF_PREBATTLE_GUI_KEY)

    def getTemplate(self, invite):
        return PRB_INVITE_TEXT_I18N_KEYS.get(invite.state, DEFAULT_INVITE_I18N_TEXT_KEY)


class PrbInviteLinkFormatter(PrbInviteTextFormatter):

    def format(self, invite):
        link = ''
        text = super(PrbInviteLinkFormatter, self).format(invite)
        if text:
            link = makeHtmlString('html_templates:lobby/prebattle', 'inviteLinkFormat', {'id': invite.id,
             'message': text,
             'sentAt': getLongDatetimeFormat(invite.createTime)})
        return link


class PrbInviteTitleFormatter(PrbInviteTextFormatter):

    def format(self, _):
        return i18n.makeString(INVITE_I18N_TITLE_KEY)


class PrbInviteInfo(object):

    def __init__(self, inviteID):
        self.__inviteID = inviteID

    @prbInvitesProperty
    def prbInvites(self):
        return None

    @prbDispatcherProperty
    def prbDispatcher(self):
        return None

    def getID(self):
        return self.__inviteID

    def getTitle(self):
        invite, _ = self.prbInvites.getReceivedInvite(self.__inviteID)
        return PrbInviteTitleFormatter().format(invite)

    def as_dict(self):
        invite, _ = self.prbInvites.getReceivedInvite(self.__inviteID)
        canAccept = self.prbInvites.canAcceptInvite(invite)
        canDecline = self.prbInvites.canDeclineInvite(invite)
        text = PrbInviteTextFormatter().format(invite)
        if canAccept:
            note = self.__getNoteText(invite)
        else:
            note = self.__getAcceptNotAllowedNote(invite)
        result = {'id': self.__inviteID,
         'text': text,
         'comment': invite.comment,
         'note': note,
         'canAccept': canAccept,
         'canDecline': canDecline}
        return result

    def __getAcceptNotAllowedNote(self, invite):
        text = ''
        if invite.anotherPeriphery and invite.isActive():
            host = g_preDefinedHosts.periphery(invite.peripheryID)
            if host is not None:
                text = ACCEPT_NOT_ALLOWED_I18N_STRING[1] % host.name
            else:
                text = ACCEPT_NOT_ALLOWED_I18N_STRING[0]
        return text

    def __getNoteText(self, invite):
        note = ''
        hasModalEntity, prbType = self.prbDispatcher.getFunctionalState()
        if hasModalEntity and prbType:
            prbName = PREBATTLE_GUI_KEYS.get(prbType, DEF_PREBATTLE_GUI_KEY)
            if invite.anotherPeriphery:
                note = i18n.makeString('#{0:>s}:invites/note/{1:>s}/leave_and_change'.format(INVITES_I18N_FILE, prbName), host=g_preDefinedHosts.periphery(invite.peripheryID).name)
            else:
                note = i18n.makeString('#{0:>s}:invites/note/{1:>s}/leave'.format(INVITES_I18N_FILE, prbName))
        elif invite.anotherPeriphery:
            note = i18n.makeString('#{0:>s}:invites/note/server_change'.format(INVITES_I18N_FILE), host=g_preDefinedHosts.periphery(invite.peripheryID).name)
        return note
# okay decompyling res/scripts/client/gui/prb_control/formatters/invites.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:25:39 EST

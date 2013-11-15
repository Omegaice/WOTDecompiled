# 2013.11.15 11:27:23 EST
# Embedded file name: scripts/client/tutorial/gui/Scaleform/offbattle/settings.py
from gui.Scaleform.framework import GroupedViewSettings, VIEW_TYPE, VIEW_SCOPE
from tutorial.gui.Scaleform.pop_ups import TutorialDialog
from tutorial.gui.Scaleform.offbattle import pop_ups as off_pop_ups

class OFFBATTLE_VIEW_ALIAS(object):
    GREETING_DIALOG = 'tGreetingDialog'
    QUEUE_DIALOG = 'tQueueDialog'
    VIDEO_DIALOG = 'tVideoDialog'
    FINAL_RESULTS_WINDOW = 'tFinalResultWindow'
    NO_FINAL_RESULTS_WINDOW = 'tNoFinalResultWindow'


OFFBATTLE_VIEW_SETTINGS = (GroupedViewSettings(OFFBATTLE_VIEW_ALIAS.GREETING_DIALOG, TutorialDialog, 'tutorialGreetingDialog.swf', VIEW_TYPE.DIALOG, '', None, VIEW_SCOPE.DEFAULT),
 GroupedViewSettings(OFFBATTLE_VIEW_ALIAS.QUEUE_DIALOG, TutorialDialog, 'tutorialQueueDialog.swf', VIEW_TYPE.DIALOG, '', None, VIEW_SCOPE.DEFAULT),
 GroupedViewSettings(OFFBATTLE_VIEW_ALIAS.VIDEO_DIALOG, off_pop_ups.TutorialVideoDialog, 'tutorialVideoDialog.swf', VIEW_TYPE.DIALOG, '', None, VIEW_SCOPE.DEFAULT),
 GroupedViewSettings(OFFBATTLE_VIEW_ALIAS.FINAL_RESULTS_WINDOW, off_pop_ups.TutorialBattleStatisticWindow, 'tutorialBattleStatistic.swf', VIEW_TYPE.WINDOW, 'tBattleStatisticGroup', None, VIEW_SCOPE.DEFAULT),
 GroupedViewSettings(OFFBATTLE_VIEW_ALIAS.NO_FINAL_RESULTS_WINDOW, off_pop_ups.TutorialBattleNoResultWindow, 'tutorialBattleNoResults.swf', VIEW_TYPE.WINDOW, 'tBattleStatisticGroup', None, VIEW_SCOPE.DEFAULT))
DIALOG_ALIAS_MAP = {'greeting': OFFBATTLE_VIEW_ALIAS.GREETING_DIALOG,
 'queue': OFFBATTLE_VIEW_ALIAS.QUEUE_DIALOG,
 'video': OFFBATTLE_VIEW_ALIAS.VIDEO_DIALOG}
WINDOW_ALIAS_MAP = {'final': OFFBATTLE_VIEW_ALIAS.FINAL_RESULTS_WINDOW,
 'noResults': OFFBATTLE_VIEW_ALIAS.NO_FINAL_RESULTS_WINDOW}
# okay decompyling res/scripts/client/tutorial/gui/scaleform/offbattle/settings.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:27:23 EST

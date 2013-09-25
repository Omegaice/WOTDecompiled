from debug_utils import LOG_DEBUG
from gui.Scaleform.daapi.view.lobby.profile.ProfileSummary import ProfileSummary
from gui.Scaleform.locale.PROFILE import PROFILE
from gui.shared import g_itemsCache

class ProfileSummaryPage(ProfileSummary):

    def __init__(self):
        super(ProfileSummaryPage, self).__init__()

    def _getInitData(self):
        outcome = ProfileSummary._getInitData(self)
        outcome['nextAwardsLabel'] = PROFILE.SECTION_SUMMARY_LABELS_NEXTAWARDS
        outcome['nextAwardsErrorText'] = PROFILE.SECTION_SUMMARY_ERRORTEXT_NEXTAWARDS
        return outcome

    def getGlobalRating(self, userName):
        LOG_DEBUG('getGlobalRating PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP', g_itemsCache.items.stats.getGlobalRating())
        return g_itemsCache.items.stats.getGlobalRating()

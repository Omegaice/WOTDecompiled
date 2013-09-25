from gui.Scaleform.daapi.view.meta.ProfileSectionMeta import ProfileSectionMeta
from helpers import i18n

class ProfileSection(ProfileSectionMeta):

    def __init__(self):
        super(ProfileSection, self).__init__()

    def setActive(self, value):
        pass

    def _formIconLabelInitObject(self, i18key, icon):
        return {'description': i18n.makeString(i18key),
         'icon': icon}

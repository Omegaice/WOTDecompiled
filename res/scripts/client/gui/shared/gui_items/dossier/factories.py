# Embedded file name: scripts/client/gui/shared/gui_items/dossier/factories.py
import weakref
import nations
from dossiers.achievements import ACHIEVEMENT_TYPE
from gui.shared.utils import dossiers_utils
from gui.shared.gui_items.dossier import achievements

class _AchieveFactory(object):

    def __init__(self, achieveClass, name, dossier):
        self.achieveClass = achieveClass
        self.name = name
        self.dossier = weakref.proxy(dossier)

    def isInDossier(self):
        return self.achieveClass.isInDossier(self.name, self._getDossierDescr())

    def create(self, itemsRequester = None):
        return self.achieveClass(self.name, self._getDossierDescr(), itemsRequester)

    @classmethod
    def get(cls, achieveClass):
        return lambda name, dossier: cls(achieveClass, name, dossier)

    def _getDossierDescr(self):
        return self.dossier.dossier


class _CustomAchieveFactory(_AchieveFactory):

    def __init__(self, achieveClass, name, dossier):
        super(_CustomAchieveFactory, self).__init__(achieveClass, name, dossier)

    def create(self, itemsRequester = None):
        return self.achieveClass(self._getDossierDescr(), itemsRequester)

    @classmethod
    def get(cls, achieveClass):
        return lambda name, dossier: cls(achieveClass, name, dossier)


class _SequenceAchieveFactory(_AchieveFactory):

    def __init__(self, achieveClass, name, dossier):
        super(_SequenceAchieveFactory, self).__init__(achieveClass, name, dossier)

    def create(self, ir = None):
        return dict(((rareID, self.achieveClass(rareID, self._getDossierDescr(), ir)) for rareID in self._getDossierDescr()['rareAchievements']))

    @classmethod
    def get(cls, achieveClass):
        return lambda name, dossier: cls(achieveClass, name, dossier)

    def isInDossier(self):
        return True


class _NationAchieveFactory(_AchieveFactory):

    def __init__(self, achieveClass, name, nationID, dossier):
        super(_NationAchieveFactory, self).__init__(achieveClass, name, dossier)
        self.nationID = nationID

    def create(self, itemsRequester = None):
        return self.achieveClass(self.nationID, self._getDossierDescr(), self.dossier.isCurrentUser, itemsRequester)

    @classmethod
    def get(cls, achieveClass, nationID = -1):
        return lambda name, dossier: cls(achieveClass, name, nationID, dossier)


_ACHIEVEMENTS_BY_TYPE = {ACHIEVEMENT_TYPE.CLASS: _AchieveFactory.get(achievements.ClassAchievement),
 ACHIEVEMENT_TYPE.SERIES: _AchieveFactory.get(achievements.SeriesAchievement)}
_ACHIEVEMENTS_BY_NAME = {'tankExpert': _NationAchieveFactory.get(achievements.TankExpertAchievement),
 'mechanicEngineer': _NationAchieveFactory.get(achievements.MechEngineerAchievement),
 'whiteTiger': _CustomAchieveFactory.get(achievements.WhiteTigerAchievement),
 'mousebane': _CustomAchieveFactory.get(achievements.MousebaneAchievement),
 'beasthunter': _CustomAchieveFactory.get(achievements.BeasthunterAchievement),
 'pattonValley': _CustomAchieveFactory.get(achievements.PattonValleyAchievement),
 'sinai': _CustomAchieveFactory.get(achievements.SinaiAchievement),
 'medalKnispel': _CustomAchieveFactory.get(achievements.MedalKnispelAchievement),
 'medalCarius': _CustomAchieveFactory.get(achievements.MedalCariusAchievement),
 'medalAbrams': _CustomAchieveFactory.get(achievements.MedalAbramsAchievement),
 'medalPoppel': _CustomAchieveFactory.get(achievements.MedalPoppelAchievement),
 'medalKay': _CustomAchieveFactory.get(achievements.MedalKayAchievement),
 'medalEkins': _CustomAchieveFactory.get(achievements.MedalEkinsAchievement),
 'medalLeClerc': _CustomAchieveFactory.get(achievements.MedalLeClercAchievement),
 'medalLavrinenko': _CustomAchieveFactory.get(achievements.MedalLavrinenkoAchievement),
 'rareAchievements': _SequenceAchieveFactory.get(achievements.RareAchievement)}
for nationID, nation in enumerate(nations.NAMES):
    _ACHIEVEMENTS_BY_NAME['tankExpert%d' % nationID] = _NationAchieveFactory.get(achievements.TankExpertAchievement, nationID)
    _ACHIEVEMENTS_BY_NAME['mechanicEngineer%d' % nationID] = _NationAchieveFactory.get(achievements.MechEngineerAchievement, nationID)

def getAchievementFactory(name, dossier):
    if name in _ACHIEVEMENTS_BY_NAME:
        return _ACHIEVEMENTS_BY_NAME[name](name, dossier)
    else:
        achieveType = dossiers_utils.getAchievementType(name)
        if achieveType is not None and achieveType in _ACHIEVEMENTS_BY_TYPE:
            return _ACHIEVEMENTS_BY_TYPE[achieveType](name, dossier)
        return _AchieveFactory(achievements.RegularAchievement, name, dossier)
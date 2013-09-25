# Embedded file name: scripts/client/gui/GuiSettings.py
import ResMgr
from debug_utils import *
from helpers import getClientLanguage
from collections import namedtuple
GUI_SETTINGS_FILE_PATH = 'gui/gui_settings.xml'
VIDEO_SETTINGS_FILE_PATH = 'gui/video_settings.xml'
MovingTextProps = namedtuple('MovingTextProps', 'show internalBrowser')
EULAProps = namedtuple('EULAProps', 'full url')

class GuiSettings:

    @staticmethod
    def readBoolean(dataSection):
        """
        formatter function for boolean values
        """
        return dataSection.readBool('')

    @staticmethod
    def readInt(dataSection):
        """
        formatter function for integer value
        """
        return dataSection.readInt('')

    @staticmethod
    def readVector2(dataSection):
        """
        formatter function for tuple of 2 numbers
        """
        return dataSection.asVector2.tuple()

    @staticmethod
    def readVector3(dataSection):
        """
        formatter function for tuple of 3 numbers
        """
        return dataSection.asVector3.tuple()

    @staticmethod
    def readVector4(dataSection):
        """
        formatter function for tuple of 4 numbers
        """
        return dataSection.asVector4.tuple()

    @staticmethod
    def readStringsList(dataSection):
        """
        formatter function for list of strings
        """
        if dataSection is None:
            return []
        else:
            list = []
            for value in dataSection.values():
                list.append(value.asString)

            return list

    @staticmethod
    def readMovingText(dataSection):
        return MovingTextProps(dataSection.readBool('show'), dataSection.readBool('internalBrowser'))

    @staticmethod
    def readEULA(dataSection):
        return EULAProps(getClientLanguage() in GuiSettings.readStringsList(dataSection['full']), dataSection.readString('url'))

    def __init__(self):
        """
        constructs GuiSettings instance using values from guiPresetsResource
        """
        self.__settings = {}
        ds = ResMgr.openSection(GUI_SETTINGS_FILE_PATH)
        if ds is not None:
            for key, value in ds.items():
                if key in keyReaders:
                    self.__settings[key] = keyReaders[key](value)
                else:
                    self.__settings[key] = value.asString

        else:
            raise IOError('gui_settins file is missing')
        for key, reader in externalReaders.iteritems():
            self.__settings[key] = reader()

        return

    def __getattr__(self, name):
        if name in self.__settings:
            return self.__settings[name]
        raise AttributeError('Setting not found in {0}: {1}'.format(self.__class__, name))

    def __setattr__(self, name, value):
        if name == '_GuiSettings__settings':
            self.__dict__[name] = value
        elif name in self.__settings:
            raise AttributeError('Assignment is forbidden for {0}. Argument name: {1}'.format(self.__class__, name))

    def __contains__(self, item):
        return item in self.__settings

    @property
    def isShowLanguageBar(self):
        """
        @return: <bool> show laguage bar or not
        """
        try:
            return getClientLanguage() in self.language_bar
        except Exception:
            LOG_CURRENT_EXCEPTION()
            return False


class VideoSettings(object):

    def __init__(self):
        """
        Initialization.
        """
        super(VideoSettings, self).__init__()
        self.__setting = {'audio': {},
         'subtitles': {}}

    def read(self, path):
        """
        Reads video setting from file.
        @param path: path to file with video setting.
        """
        section = ResMgr.openSection(path)
        if section is None:
            LOG_WARNING('File with video settings not found. Uses default values', path)
            return
        else:
            tags = section.keys()
            if 'audio' in tags:
                self.__setting['audio'] = self.__readTracks(section['audio'])
            if 'subtitles' in tags:
                self.__setting['subtitles'] = self.__readTracks(section['subtitles'], offset=1)
            return self

    @property
    def audioTrack(self):
        """
        Returns number of audio track by language code. If track not found than
        returns 0.
        @return: number of audio track.
        """
        audio = self.__setting['audio']
        code = getClientLanguage()
        if code in audio:
            return audio[code]
        return 0

    @property
    def subtitleTrack(self):
        """
        Returns number of subtitle by language code. If track not found than
        returns 0.
        Note: subtitle track 0 turns subtitles off.
        @return: number of subtitle track.
        """
        subtitles = self.__setting['subtitles']
        code = getClientLanguage()
        if code in subtitles:
            return subtitles[code]
        return 0

    def __readTracks(self, section, offset = 0):
        result = {}
        for idx, subSec in enumerate(section.values()):
            for langSec in subSec.values():
                lang = langSec.asString
                if len(lang) > 0:
                    result[lang] = idx + offset

        return result


keyReaders = {'nations_order': GuiSettings.readStringsList,
 'language_bar': GuiSettings.readStringsList,
 'minimapSize': GuiSettings.readBoolean,
 'goldTransfer': GuiSettings.readBoolean,
 'voiceChat': GuiSettings.readBoolean,
 'technicalInfo': GuiSettings.readBoolean,
 'nationHangarSpace': GuiSettings.readBoolean,
 'customizationCamouflages': GuiSettings.readBoolean,
 'customizationHorns': GuiSettings.readBoolean,
 'customizationEmblems': GuiSettings.readBoolean,
 'customizationInscriptions': GuiSettings.readBoolean,
 'showMinimapSuperHeavy': GuiSettings.readBoolean,
 'showMinimapDeath': GuiSettings.readBoolean,
 'permanentMinimapDeath': GuiSettings.readBoolean,
 'markerHitSplashDuration': GuiSettings.readInt,
 'sixthSenseDuration': GuiSettings.readInt,
 'minimapDeathDuration': GuiSettings.readInt,
 'rememberPassVisible': GuiSettings.readBoolean,
 'clearLoginValue': GuiSettings.readBoolean,
 'markerScaleSettings': GuiSettings.readVector4,
 'markerBgSettings': GuiSettings.readVector4,
 'specPrebatlesVisible': GuiSettings.readBoolean,
 'battleStatsInHangar': GuiSettings.readBoolean,
 'freeXpToTankman': GuiSettings.readBoolean,
 'movingText': GuiSettings.readMovingText,
 'eula': GuiSettings.readEULA,
 'igrCredentialsReset': GuiSettings.readBoolean}
externalReaders = {'video': lambda : VideoSettings().read(VIDEO_SETTINGS_FILE_PATH)}
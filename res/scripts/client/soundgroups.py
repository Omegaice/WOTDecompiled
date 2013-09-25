import BigWorld
import FMOD
import Settings
import ResMgr
import constants
from debug_utils import *
from helpers import i18n
g_instance = None

class SoundModes():
    __MODES_FOLDER = 'gui/soundModes/'
    __MODES_FILENAME = 'main_sound_modes.xml'
    DEFAULT_MODE_NAME = 'default'
    DEFAULT_NATION = 'default'
    MEDIA_PATH = None

    class SoundModeDesc(object):

        def __init__(self, dataSection):
            self.name = dataSection.readString('name', 'default')
            self.fmodLanguage = dataSection.readString('fmod_language', 'default')
            descriptionLink = dataSection.readString('description', '')
            self.description = i18n.makeString(descriptionLink)
            self.invisible = dataSection.readBool('invisible', False)
            self.banksToBeLoaded = []
            self.__isValid = None
            banksSec = dataSection['banks']
            if banksSec is not None:
                for bank in banksSec.values():
                    bankName = bank.asString
                    manualPath = bank.readString('filePath', '')
                    self.banksToBeLoaded.append((bankName, manualPath))

            return

        def getIsValid(self, soundModes):
            if self.__isValid is None:
                self.__isValid = self.__validate(soundModes)
            return self.__isValid

        def loadBanksManually(self):
            for bankName, bankPath in self.banksToBeLoaded:
                if bankPath != '':
                    loadSuccessfully = FMOD.loadSoundBankIntoMemoryFromPath(bankPath)
                    if not loadSuccessfully:
                        return False

            return True

        def unloadBanksManually(self):
            for bankName, bankPath in self.banksToBeLoaded:
                if bankPath != '':
                    FMOD.unloadSoundBankFromMemory(bankName)

        def __validate(self, soundModes):
            prevMode = soundModes.currentMode
            for soundBankName, soundPath in self.banksToBeLoaded:
                pathToCheck = soundPath if soundPath else '%s/%s.fsb' % (SoundModes.MEDIA_PATH, soundBankName)
                if not ResMgr.isFile(pathToCheck):
                    return False

            result = soundModes.setMode(self.name)
            soundModes.setMode(prevMode)
            return result

        def __repr__(self):
            return 'SoundModeDesc<name=%s; lang=%s; visible=%s>' % (self.name, self.fmodLanguage, not self.invisible)

        def __cmp__(self, other):
            if not isinstance(other, SoundModes.SoundModeDesc):
                return -1
            if self.name == 'default':
                return -1
            if other.name == 'default':
                return 1
            return 1

    class NationalPresetDesc(object):

        def __init__(self, dataSection):
            self.name = dataSection.readString('name', 'default')
            descriptionLink = dataSection.readString('description', '')
            self.description = i18n.makeString(descriptionLink)
            self.mapping = {}
            for nationSec in dataSection['nations'] or {}.values():
                nationName = nationSec.readString('name', 'default')
                soundMode = nationSec.readString('soundMode', 'default')
                self.mapping[nationName] = soundMode

        def __repr__(self):
            return 'NationalPresetDesc<name=%s>' % self.name

    modes = property(lambda self: self.__modes)
    nationalPresets = property(lambda self: self.__nationalPresets)
    currentMode = property(lambda self: self.__currentMode)
    currentNationalPreset = property(lambda self: self.__currentNationalPreset)
    nationToSoundModeMapping = property(lambda self: self.__nationToSoundModeMapping)

    def __init__(self, initialModeName):
        if SoundModes.MEDIA_PATH is None:
            engineConfig = ResMgr.openSection('engine_config.xml')
            if engineConfig is not None:
                SoundModes.MEDIA_PATH = engineConfig.readString('soundMgr/mediaPath', 'audio')
            else:
                SoundModes.MEDIA_PATH = 'audio'
        self.__modes = {}
        self.__currentMode = SoundModes.DEFAULT_MODE_NAME
        self.__nationalPresets = {}
        self.__nationToSoundModeMapping = {'default': SoundModes.DEFAULT_MODE_NAME}
        self.__currentNationalPreset = (SoundModes.DEFAULT_MODE_NAME, False)
        self.modifiedSoundGroups = []
        modesSettingsSection = ResMgr.openSection(SoundModes.__MODES_FOLDER + SoundModes.__MODES_FILENAME)
        if modesSettingsSection is None:
            LOG_ERROR('%s is not found' % SoundModes.__MODES_FILENAME)
            return
        else:
            soundModes, nationalPresets = self.__readSoundModesConfig(modesSettingsSection, self.__nationalPresets)
            self.__modes = dict(((soundMode.name, soundMode) for soundMode in soundModes))
            self.__nationalPresets = dict(((preset.name, preset) for preset in nationalPresets))
            if SoundModes.DEFAULT_MODE_NAME not in self.__modes:
                LOG_ERROR('Default sound mode is not found!')
            modifiedSoundGroupsSection = modesSettingsSection['modified_sound_groups']
            if modifiedSoundGroupsSection is not None:
                self.modifiedSoundGroups = modifiedSoundGroupsSection.readStrings('sound_group')
            folderSection = ResMgr.openSection(SoundModes.__MODES_FOLDER)
            if folderSection is None:
                LOG_ERROR("Folder for SoundModes: '%s' is not found!" % SoundModes.__MODES_FOLDER)
            else:
                defaultNationalPresets = dict(self.__nationalPresets)
                for modesConfigSection in folderSection.values():
                    if modesConfigSection.name != SoundModes.__MODES_FILENAME:
                        soundModes, nationalPresets = self.__readSoundModesConfig(modesConfigSection, defaultNationalPresets)
                        for mode in soundModes:
                            if self.__modes.has_key(mode.name):
                                LOG_WARNING("%s config tries to redefine soundMode '%s', ignored" % (modesConfigSection.name, mode.name))
                            else:
                                self.__modes[mode.name] = mode

                        for preset in nationalPresets:
                            if self.__nationalPresets.has_key(preset.name):
                                LOG_WARNING("%s config tries to redefine nationalPreset '%s', ignored" % (preset.name, preset.name))
                            else:
                                self.__nationalPresets[preset.name] = preset

            self.setMode(initialModeName)
            return

    def __readSoundModesConfig(self, rootSection, mainNationalPresets):
        soundModes = []
        modesSection = rootSection['modes']
        if modesSection is not None:
            for modeSec in modesSection.values():
                if modeSec.name == 'mode':
                    soundModes.append(SoundModes.SoundModeDesc(modeSec))

        nationalPresetsSection = rootSection['nationalPresets']
        nationalPresets = self.__readNationalPresets(nationalPresetsSection or {})
        overridesSection = rootSection['nationalPresetsOverrides']
        overrides = self.__readNationalPresets(overridesSection or {})
        for overridePreset in overrides:
            nationalPresetToOverride = mainNationalPresets.get(overridePreset.name)
            if nationalPresetToOverride is not None:
                for nationName, soundMode in overridePreset.mapping.iteritems():
                    nationalPresetToOverride.mapping[nationName] = soundMode

            else:
                LOG_WARNING("Failed to override nationalPreset '%s'" % overridePreset.name)

        return (soundModes, nationalPresets)

    def __readNationalPresets(self, rootSection):
        for nationalPresetSec in rootSection.values():
            if nationalPresetSec.name == 'preset':
                yield SoundModes.NationalPresetDesc(nationalPresetSec)

    def setMode(self, modeName):
        languageSet = False
        try:
            languageSet = self.__setMode(modeName)
        except:
            LOG_CURRENT_EXCEPTION()

        if not languageSet:
            defaultFmodLanguage = ''
            if SoundModes.DEFAULT_MODE_NAME in self.__modes:
                defaultFmodLanguage = self.__modes[SoundModes.DEFAULT_MODE_NAME].fmodLanguage
            try:
                FMOD.setLanguage(defaultFmodLanguage, self.modifiedSoundGroups)
                self.__modes[SoundModes.DEFAULT_MODE_NAME].loadBanksManually()
            except:
                LOG_CURRENT_EXCEPTION()

            self.__currentMode = SoundModes.DEFAULT_MODE_NAME
        return languageSet

    def __setMode(self, modeName):
        if modeName not in self.__modes:
            LOG_DEBUG('Sound mode %s does not exist' % modeName)
            return False
        if self.__currentMode == modeName:
            return True
        self.__modes[self.__currentMode].unloadBanksManually()
        self.__currentMode = modeName
        modeDesc = self.__modes[modeName]
        languageSet = FMOD.setLanguage(modeDesc.fmodLanguage, self.modifiedSoundGroups)
        if not languageSet:
            LOG_DEBUG('Internal FMOD error in FMOD::setLanguage')
            return False
        if not self.__modes[self.__currentMode].loadBanksManually():
            LOG_DEBUG('Error while manual banks loading')
            return False
        loadedSoundBanks = FMOD.getSoundBanks()
        for bankName, bankPath in modeDesc.banksToBeLoaded:
            found = False
            for loadedBank in loadedSoundBanks:
                if bankName == loadedBank:
                    found = True
                    break

            if not found:
                LOG_DEBUG('Bank %s was not loaded while loading %s sound mode' % (bankName, modeName))
                return False

        return True

    def setCurrentNation(self, nation):
        arena = getattr(BigWorld.player(), 'arena', None)
        if arena is not None:
            inTutorial = arena.guiType is constants.ARENA_GUI_TYPE.TUTORIAL
            nationToQueue = nation
            if nation not in self.__nationToSoundModeMapping or inTutorial:
                nationToQueue = SoundModes.DEFAULT_NATION
            soundMode = self.__nationToSoundModeMapping.get(nationToQueue)
            success = soundMode is not None and self.setMode(soundMode)
            success or self.setNationalMappingByMode(SoundModes.DEFAULT_MODE_NAME)
        return success

    def setNationalMapping(self, nationToSoundModeMapping):
        for soundModeName in nationToSoundModeMapping.itervalues():
            soundModeDesc = self.__modes.get(soundModeName)
            if soundModeDesc is None:
                LOG_DEBUG("SoundMode '%s' is not found" % soundModeName)
                return False
            if not soundModeDesc.getIsValid(self):
                LOG_DEBUG("SoundMode '%s' has invalid banks" % soundModeName)
                return False

        self.__nationToSoundModeMapping = nationToSoundModeMapping
        self.__currentNationalPreset = None
        return True

    def setNationalMappingByMode(self, soundMode):
        if soundMode not in self.__modes:
            return False
        success = self.setNationalMapping({'default': soundMode})
        if not success:
            return False
        self.__currentNationalPreset = (soundMode, False)
        return True

    def setNationalMappingByPreset(self, presetName):
        preset = self.__nationalPresets.get(presetName)
        if preset is None:
            return False
        else:
            success = self.setNationalMapping(preset.mapping)
            if not success:
                return False
            self.__currentNationalPreset = (presetName, True)
            return True


class SoundGroups(object):
    soundModes = property(lambda self: self.__soundModes)

    def __init__(self):
        self.__volumeByCategory = {}
        self.__masterVolume = 1.0
        self.__isWindowVisible = BigWorld.isWindowVisible()
        self.__groups = {'arena': ('/vehicles/tanks', '/hits/hits', '/hits/explosions', '/hits/tank_death', '/weapons/large_fire', '/weapons/medium_fire', '/weapons/small_fire', '/weapons/tracer', '/GUI/notifications_FX', '/ingame_voice/notifications_VO', '/objects/wire_barricade', '/objects/tent', '/objects/dog_house', '/objects/structures', '/objects/treefall', '/objects/wood_box_mid', '/objects/telegraph_pole', '/objects/buildings', '/objects/fuel_tank', '/objects/fence', '/objects/fuel_barrel', '/objects/fire', '/objects/hay_stack', '/objects/metall_pole_huge')}
        self.__categories = {'voice': ('ingame_voice',),
         'vehicles': ('vehicles',),
         'effects': ('hits', 'weapons', 'environment', 'battle_gui'),
         'gui': ('gui',),
         'music': ('music',),
         'ambient': ('ambient',),
         'masterVivox': (),
         'micVivox': (),
         'masterFadeVivox': ()}
        defMasterVolume = 0.5
        defCategoryVolumes = {'music': 0.5,
         'masterVivox': 0.7,
         'micVivox': 0.4}
        userPrefs = Settings.g_instance.userPrefs
        soundModeName = SoundModes.DEFAULT_MODE_NAME
        nationalMapping = None
        self.__soundModes = None
        if not userPrefs.has_key(Settings.KEY_SOUND_PREFERENCES):
            userPrefs.write(Settings.KEY_SOUND_PREFERENCES, '')
            self.__masterVolume = defMasterVolume
            for categoryName in self.__categories.keys():
                self.__volumeByCategory[categoryName] = defCategoryVolumes.get(categoryName, 1.0)

            self.savePreferences()
        else:
            ds = userPrefs[Settings.KEY_SOUND_PREFERENCES]
            self.__masterVolume = ds.readFloat('masterVolume', defMasterVolume)
            for categoryName in self.__categories.keys():
                volume = ds.readFloat('volume_' + categoryName, defCategoryVolumes.get(categoryName, 1.0))
                self.__volumeByCategory[categoryName] = volume

            soundModeSec = ds['soundMode']
            if soundModeSec is not None:
                soundModeName = soundModeSec.asString
                if soundModeName == '':
                    soundModeName = SoundModes.DEFAULT_MODE_NAME
                    if ds['soundMode'].has_key('nationalPreset'):
                        nationalMapping = ds.readString('soundMode/nationalPreset', '')
                    else:
                        nationsSec = soundModeSec['nations']
                        if nationsSec is not None:
                            nationalMapping = {}
                            for nation, sec in nationsSec.items():
                                nationalMapping[nation] = sec.asString

        self.__soundModes = SoundModes(SoundModes.DEFAULT_MODE_NAME)
        if isinstance(nationalMapping, str):
            self.__soundModes.setNationalMappingByPreset(nationalMapping)
        elif isinstance(nationalMapping, dict):
            self.__soundModes.setNationalMapping(nationalMapping)
        else:
            self.__soundModes.setNationalMappingByMode(soundModeName)
        self.applyPreferences()
        self.__muteCallbackID = BigWorld.callback(0.25, self.__muteByWindowVisibility)
        return

    def __del__(self):
        if self.__muteCallbackID is not None:
            BigWorld.cancelCallback(self.__muteCallbackID)
            self.__muteCallbackID = None
        return

    def loadSounds(self, groupName):
        for group in self.__groups[groupName]:
            try:
                FMOD.loadSoundGroup(group)
            except Exception:
                LOG_CURRENT_EXCEPTION()

    def unloadSounds(self, groupName):
        for group in self.__groups[groupName]:
            try:
                FMOD.unloadSoundGroup(group)
            except Exception:
                LOG_CURRENT_EXCEPTION()

    def enableLobbySounds(self, enable):
        for categoryName in ('ambient', 'gui'):
            volume = 0.0 if not enable else self.__volumeByCategory[categoryName]
            self.setVolume(categoryName, volume, False)

    def enableArenaSounds(self, enable):
        for categoryName in ('voice', 'vehicles', 'effects', 'ambient'):
            volume = 0.0 if not enable else self.__volumeByCategory[categoryName]
            self.setVolume(categoryName, volume, False)

    def enableAmbientAndMusic(self, enable):
        for categoryName in ('ambient', 'music'):
            volume = 0.0 if not enable else self.__volumeByCategory[categoryName]
            self.setVolume(categoryName, volume, False)

    def enableVoiceSounds(self, enable):
        for categoryName in ('voice',):
            volume = 0.0 if not enable else self.__volumeByCategory[categoryName]
            self.setVolume(categoryName, volume, False)

    def setMasterVolume(self, volume):
        self.__masterVolume = volume
        FMOD.setMasterVolume(volume)
        self.savePreferences()

    def getMasterVolume(self):
        return self.__masterVolume

    def setVolume(self, categoryName, volume, updatePrefs = True):
        for category in self.__categories[categoryName]:
            try:
                BigWorld.wg_setCategoryVolume(category, volume)
            except Exception:
                LOG_CURRENT_EXCEPTION()

        if updatePrefs:
            self.__volumeByCategory[categoryName] = volume
            self.savePreferences()

    def getVolume(self, categoryName):
        return self.__volumeByCategory[categoryName]

    def savePreferences(self):
        ds = Settings.g_instance.userPrefs[Settings.KEY_SOUND_PREFERENCES]
        ds.writeFloat('masterVolume', self.__masterVolume)
        for categoryName in self.__volumeByCategory.keys():
            ds.writeFloat('volume_' + categoryName, self.__volumeByCategory[categoryName])

        soundModeName = SoundModes.DEFAULT_MODE_NAME if self.__soundModes is None else self.__soundModes.currentMode
        ds.deleteSection('soundMode')
        if self.__soundModes is None:
            ds.writeString('soundMode', soundModeName)
        else:
            curPresetIsNationalPreset = self.__soundModes.currentNationalPreset
            soundModeSection = ds.createSection('soundMode')
            if curPresetIsNationalPreset is None:
                nationsSection = soundModeSection.createSection('nations')
                mapping = self.__soundModes.nationToSoundModeMapping
                for nation, mode in mapping.iteritems():
                    nationsSection.writeString(nation, mode)

            elif curPresetIsNationalPreset[1]:
                soundModeSection.writeString('nationalPreset', curPresetIsNationalPreset[0])
            else:
                ds.writeString('soundMode', curPresetIsNationalPreset[0])
        return

    def applyPreferences(self):
        if not self.__isWindowVisible:
            FMOD.setMasterVolume(0)
            return
        self.setMasterVolume(self.__masterVolume)
        for categoryName in self.__volumeByCategory.keys():
            self.setVolume(categoryName, self.__volumeByCategory[categoryName], updatePrefs=False)

    def __muteByWindowVisibility(self):
        isWindowVisible = BigWorld.isWindowVisible()
        if self.__isWindowVisible != isWindowVisible:
            self.__isWindowVisible = isWindowVisible
            self.applyPreferences()
        self.__muteCallbackID = BigWorld.callback(0.25, self.__muteByWindowVisibility)

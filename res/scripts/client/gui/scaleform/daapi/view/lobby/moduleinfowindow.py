from debug_utils import LOG_DEBUG
from gui.shared.utils import SHELLS_COUNT_PROP_NAME, SHELL_RELOADING_TIME_PROP_NAME, RELOAD_MAGAZINE_TIME_PROP_NAME, GUN_RELOADING_TYPE, GUN_CAN_BE_CLIP, GUN_NORMAL, GUN_CLIP, RELOAD_TIME_PROP_NAME, CLIP_VEHICLES_PROP_NAME, CLIP_ICON_PATH, EXTRA_MODULE_INFO
import gui.shared.utils.ItemsParameters
__author__ = 'd_dichkovsky'
import BigWorld
from gui.Scaleform.locale.MENU import MENU
from CurrentVehicle import g_currentVehicle
from gui.shared.utils.functions import stripShortDescrTags
from gui.shared.utils.gui_items import getItemByCompact
from items import ITEM_TYPE_NAMES
from helpers import i18n
from gui.Scaleform.framework.entities.View import View
from gui.Scaleform.daapi.view.meta.ModuleInfoMeta import ModuleInfoMeta
from gui.Scaleform.daapi.view.meta.WindowViewMeta import WindowViewMeta
from gui.shared.utils import ItemsParameters

class ModuleInfoWindow(View, ModuleInfoMeta, WindowViewMeta):

    def __init__(self, moduleId, vehicleDescr = None):
        super(ModuleInfoWindow, self).__init__()
        self.moduleId = moduleId
        self.__vehicleDescr = vehicleDescr

    def onCancelClick(self):
        self.destroy()

    def onWindowClose(self):
        self.destroy()

    def _populate(self):
        super(View, self)._populate()
        module = getItemByCompact(self.moduleId)
        description = ''
        if module.itemTypeName in (ITEM_TYPE_NAMES[9], ITEM_TYPE_NAMES[11]):
            description = stripShortDescrTags(module.description)
        if module.itemTypeName in (ITEM_TYPE_NAMES[9], ITEM_TYPE_NAMES[10], ITEM_TYPE_NAMES[11]):
            icon = module.icon
        else:
            icon = module.level
        extraModuleInfo = ''
        moduleData = {'name': module.longName,
         'windowTitle': ' '.join([module.longName, i18n.makeString(MENU.MODULEINFO_TITLE)]),
         'type': module.itemTypeName,
         'description': description,
         'level': icon,
         'params': [],
         'compatible': [],
         'effects': {}}
        params = ItemsParameters.g_instance.get(module.descriptor, self.__vehicleDescr)
        moduleParameters = params.get('parameters', tuple())
        isGun = module.itemTypeName == ITEM_TYPE_NAMES[4]
        excludedParametersNames = []
        if isGun:
            gunReloadingType = dict(moduleParameters)[GUN_RELOADING_TYPE]
            LOG_DEBUG('gunReloadingTypegunReloadingTypegunReloadingTypegunReloadingType', gunReloadingType)
            if gunReloadingType == GUN_NORMAL:
                excludedParametersNames.append(SHELLS_COUNT_PROP_NAME)
                excludedParametersNames.append(RELOAD_MAGAZINE_TIME_PROP_NAME)
                excludedParametersNames.append(SHELL_RELOADING_TIME_PROP_NAME)
            elif gunReloadingType == GUN_CLIP:
                description = i18n.makeString(MENU.MODULEINFO_CLIPGUNLABEL)
                excludedParametersNames.append(RELOAD_TIME_PROP_NAME)
                extraModuleInfo = CLIP_ICON_PATH
            elif gunReloadingType == GUN_CAN_BE_CLIP:
                excludedParametersNames.append(SHELLS_COUNT_PROP_NAME)
                excludedParametersNames.append(RELOAD_MAGAZINE_TIME_PROP_NAME)
                excludedParametersNames.append(SHELL_RELOADING_TIME_PROP_NAME)
                otherParamsInfoList = []
                for paramType, paramValue in moduleParameters:
                    if paramType in excludedParametersNames:
                        otherParamsInfoList.append({'type': i18n.makeString(MENU.moduleinfo_params(paramType)),
                         'value': paramValue})

                imgPathArr = CLIP_ICON_PATH.split('..')
                imgPath = 'img://gui' + imgPathArr[1]
                moduleData['otherParameters'] = {'headerText': i18n.makeString(MENU.MODULEINFO_PARAMETERSCLIPGUNLABEL, imgPath),
                 'params': otherParamsInfoList}
        moduleData['description'] = description
        excludedParametersNames.append(GUN_RELOADING_TYPE)
        paramsList = []
        for paramType, paramValue in moduleParameters:
            if paramType not in excludedParametersNames:
                paramsList.append({'type': i18n.makeString(MENU.moduleinfo_params(paramType)),
                 'value': paramValue})

        moduleData['parameters'] = {'headerText': i18n.makeString(MENU.MODULEINFO_PARAMETERSLABEL) if len(paramsList) > 0 else '',
         'params': paramsList}
        moduleData[EXTRA_MODULE_INFO] = extraModuleInfo
        moduleCompatibles = params.get('compatible', tuple())
        for paramType, paramValue in moduleCompatibles:
            compatible = moduleData.get('compatible')
            compatible.append({'type': i18n.makeString(MENU.moduleinfo_compatible(paramType)),
             'value': paramValue})

        if module.itemTypeName == ITEM_TYPE_NAMES[11]:
            effectsNametemplate = '#artefacts:%s/%s'
            moduleData['effects'] = {'effectOnUse': i18n.makeString(effectsNametemplate % (module.unicName, 'onUse')),
             'effectAlways': i18n.makeString(effectsNametemplate % (module.unicName, 'always')),
             'effectRestriction': i18n.makeString(effectsNametemplate % (module.unicName, 'restriction'))}
        self.as_setModuleInfoS(moduleData)

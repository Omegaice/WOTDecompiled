# Embedded file name: scripts/client/gui/Scaleform/daapi/view/lobby/customization/__init__.py
from gui import GUI_SETTINGS
from gui.Scaleform.daapi.view.lobby.customization.CamouflageInterface import CamouflageInterface
from gui.Scaleform.daapi.view.lobby.customization.EmblemInterface import EmblemLeftInterface, EmblemRightInterface
from gui.Scaleform.daapi.view.lobby.customization.InscriptionInterface import InscriptionLeftInterface, InscriptionRightInterface
_VEHICLE_CUSTOMIZATIONS = []
if GUI_SETTINGS.customizationCamouflages:
    _VEHICLE_CUSTOMIZATIONS.append({'sectionName': 'camouflage',
     'sectionUserString': '#menu:customization/labels/camouflage/section',
     'priceUserString': '#menu:customization/labels/camouflage/price',
     'linkage': 'CamouflageSectionViewUI',
     'interface': CamouflageInterface,
     'position': -1})
if GUI_SETTINGS.customizationEmblems:
    _VEHICLE_CUSTOMIZATIONS.append({'sectionName': 'emblemLeft',
     'sectionUserString': '#menu:customization/labels/emblemLeft/section',
     'priceUserString': '#menu:customization/labels/emblemLeft/price',
     'linkage': 'EmblemLeftSectionViewUI',
     'interface': EmblemLeftInterface,
     'position': 0})
if GUI_SETTINGS.customizationEmblems:
    _VEHICLE_CUSTOMIZATIONS.append({'sectionName': 'emblemRight',
     'sectionUserString': '#menu:customization/labels/emblemRight/section',
     'priceUserString': '#menu:customization/labels/emblemRight/price',
     'linkage': 'EmblemRightSectionViewUI',
     'interface': EmblemRightInterface,
     'position': 1})
if GUI_SETTINGS.customizationInscriptions:
    _VEHICLE_CUSTOMIZATIONS.append({'sectionName': 'inscriptionLeft',
     'sectionUserString': '#menu:customization/labels/inscriptionLeft/section',
     'priceUserString': '#menu:customization/labels/inscriptionLeft/price',
     'linkage': 'InscriptionLeftSectionViewUI',
     'interface': InscriptionLeftInterface,
     'position': 0})
if GUI_SETTINGS.customizationInscriptions:
    _VEHICLE_CUSTOMIZATIONS.append({'sectionName': 'inscriptionRight',
     'sectionUserString': '#menu:customization/labels/inscriptionRight/section',
     'priceUserString': '#menu:customization/labels/inscriptionRight/price',
     'linkage': 'InscriptionRightSectionViewUI',
     'interface': InscriptionRightInterface,
     'position': 1})
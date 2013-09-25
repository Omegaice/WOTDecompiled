# Embedded file name: scripts/client/gui/Scaleform/daapi/view/lobby/techtree/dumpers.py
from debug_utils import LOG_ERROR
import gui
from gui.shared.utils import CLIP_ICON_PATH
from helpers import i18n, html
from gui.Scaleform.daapi.view.lobby.techtree import _PREMIUM_TAGS, _VEHICLE_TYPE_NAME, _GUN_TYPE_NAME, NODE_STATE, techtree_dp, VehicleClassInfo
import nations
__all__ = ['_BaseDumper',
 'ResearchItemsObjDumper',
 'ResearchItemsXMLDumper',
 'NationObjDumper',
 'NationXMLDumper']

class _BaseDumper(object):
    __slots__ = ('_cache', '_vClassInfo')

    def __init__(self, cache = None):
        super(_BaseDumper, self).__init__()
        self._cache = cache
        self._vClassInfo = VehicleClassInfo()

    def clear(self, full = False):
        raise NotImplementedError

    def dump(self, data):
        return {}


class ResearchItemsObjDumper(_BaseDumper):

    def __init__(self, cache = None):
        if cache is None:
            cache = {'nodes': [],
             'top': [],
             'global': {'enableInstallItems': False,
                        'statusString': '',
                        'extraInfo': {},
                        'freeXP': 0,
                        'hasNationTree': False}}
        super(ResearchItemsObjDumper, self).__init__(cache)
        return

    def clear(self, full = False):
        for key in ['nodes', 'top']:
            nodes = self._cache[key]
            while len(nodes):
                nodes.pop().clear()

        self._cache['global']['extraInfo'].clear()
        if full:
            self._vClassInfo.clear()

    def dump(self, data):
        self.clear()
        itemGetter = data.getItem
        intCD = data.getRootCD()
        self._cache['nodes'] = map(lambda node: self._getItemData(node, itemGetter(node['id']), intCD), data._nodes)
        self._cache['top'] = map(lambda node: self._getItemData(node, itemGetter(node['id']), intCD), data._topLevel)
        self._getGlobalData(data)
        return self._cache

    def _getGlobalData(self, data):
        try:
            nation = nations.NAMES[data.getNationID()]
        except IndexError:
            LOG_ERROR('Nation not found', data.getNationID())
            nation = None

        globalData = self._cache['global']
        globalData.update({'enableInstallItems': data.isEnableInstallItems(),
         'statusString': data.getRootStatusString(),
         'extraInfo': self._getExtraInfo(data),
         'freeXP': data._accFreeXP,
         'hasNationTree': nation in techtree_dp.g_techTreeDP.getAvailableNations()})
        return

    def _getExtraInfo(self, data):
        item = data.getItem(data.getRootCD())
        result = {}
        if item.isPremium:
            if item.isSpecial:
                tag = 'special'
            else:
                tag = 'premium'
            typeString = i18n.makeString('#tooltips:tankCaruselTooltip/vehicleType/elite/{0:>s}'.format(item.type))
            result = {'type': item.type,
             'title': gui.makeHtmlString('html_templates:lobby/research', 'premium_title', ctx={'name': item.name,
                       'type': typeString,
                       'level': i18n.makeString('#tooltips:level/{0:d}'.format(item.level))}),
             'benefitsHead': i18n.makeString('#menu:research/{0:>s}/benefits/head'.format(tag)),
             'benefitsList': gui.makeHtmlString('html_templates:lobby/research', '{0:>s}_benefits'.format(tag), ctx={'description': item.description})}
        return result

    def _getItemData(self, node, item, intCD):
        nodeCD = node['id']
        vClass = {'userString': '',
         'name': ''}
        iconPath = ''
        smallIconPath = ''
        isVehicle = item.itemTypeName == _VEHICLE_TYPE_NAME
        extraInfo = None
        if isVehicle:
            tags = item.tags
            vClass = self._vClassInfo.getInfoByTags(tags)
            if len(tags & _PREMIUM_TAGS):
                node['state'] |= NODE_STATE.PREMIUM
            iconPath = item.icon
            smallIconPath = item.smallIcon
        else:
            if item.itemTypeName == _GUN_TYPE_NAME:
                if item.isClipGun(intCD):
                    extraInfo = CLIP_ICON_PATH
            vClass.update({'name': item.itemTypeName,
             'userString': item.userType})
        return {'id': nodeCD,
         'nameString': item.shortName,
         'primaryClass': vClass,
         'level': item.level,
         'longName': item.longName,
         'iconPath': iconPath,
         'smallIconPath': smallIconPath,
         'pickleDump': item.pack(),
         'earnedXP': node['earnedXP'],
         'state': node['state'],
         'shopPrice': node['shopPrice'],
         'displayInfo': node['displayInfo'],
         'unlockProps': node['unlockProps']._makeTuple(),
         'extraInfo': extraInfo}


class ResearchItemsXMLDumper(ResearchItemsObjDumper):
    __xmlBody = '<?xml version="1.0" encoding="utf-8"?><graph><top>{0:>s}</top><nodes>{1:>s}</nodes><global><enableInstallItems>{2[enableInstallItems]:b}</enableInstallItems><statusString>{2[statusString]:>s}</statusString><extraInfo><type>{2[extraInfo][type]:>s}</type><title><![CDATA[{2[extraInfo][title]:>s}]]></title><benefitsHead><![CDATA[{2[extraInfo][benefitsHead]:>s}]]></benefitsHead><benefitsList><![CDATA[{2[extraInfo][benefitsList]:>s}]]></benefitsList></extraInfo><freeXP>{2[freeXP]:n}</freeXP><hasNationTree>{2[hasNationTree]:b}</hasNationTree></global></graph>'
    __nodeFormat = '<node><id>{id:d}</id><nameString>{nameString:>s}</nameString><class><name>{primaryClass[name]:>s}</name><userString>{primaryClass[userString]:>s}</userString></class><level>{level:d}</level><earnedXP>{earnedXP:d}</earnedXP><state>{state:d}</state><unlockProps><parentID>{unlockProps[0]:d}</parentID><unlockIdx>{unlockProps[1]:d}</unlockIdx><xpCost>{unlockProps[2]:n}</xpCost><required>{unlockProps[3]:>s}</required></unlockProps><smallIconPath><![CDATA[{smallIconPath:>s}]]></smallIconPath><iconPath><![CDATA[{iconPath:>s}]]></iconPath><longName>{longName:>s}</longName><dump><![CDATA[{pickleDump:>s}]]></dump><shopPrice><credits>{shopPrice[0]:n}</credits><gold>{shopPrice[1]:n}</gold></shopPrice><display><renderer>{displayInfo[renderer]:>s}</renderer><path>{displayInfo[path]:>s}</path><level>{displayInfo[level]:d}</level></display></node>'
    __idFormat = '<id>{0:d}</id>'

    def __init__(self):
        super(ResearchItemsXMLDumper, self).__init__('')

    def clear(self, full = False):
        self._cache = ''

    def dump(self, data):
        self._cache = self.__xmlBody.format(self.__buildNodesData(data, '_topLevel'), self.__buildNodesData(data, '_nodes'), self._getGlobalData(data))
        return self._cache

    def _getExtraInfo(self, data):
        result = super(ResearchItemsXMLDumper, self)._getExtraInfo(data)
        return {'type': result.get('type', ''),
         'title': html.escape(result.get('title', '')),
         'content': html.escape(result.get('content', ''))}

    def __buildNodesData(self, data, storage):
        nodesDump = []
        itemGetter = data.getItem
        nodes = getattr(data, storage, [])
        for node in nodes:
            data = self._getItemData(node, itemGetter(node['id']), data.getRootCD())
            data['unlockProps'] = self.__buildUnlockProps(data['unlockProps'])
            data['displayInfo'] = self.__buildDisplayInfo(data['displayInfo'])
            nodesDump.append(self.__nodeFormat.format(**data))

        return ''.join(nodesDump)

    def __buildUnlockProps(self, unlockProps):
        dump = map(lambda item: self.__idFormat.format(item), unlockProps[-1])
        return unlockProps[:-1] + (''.join(dump),)

    def __buildDisplayInfo(self, displayInfo):
        info = displayInfo.copy()
        info['path'] = ''.join(map(lambda item: self.__idFormat.format(item), displayInfo['path']))
        return info


class NationObjDumper(_BaseDumper):

    def __init__(self, cache = None):
        if cache is None:
            cache = {'nodes': [],
             'displaySettings': {},
             'scrollIndex': -1}
        super(NationObjDumper, self).__init__(cache)
        return

    def clear(self, full = False):
        nodes = self._cache['nodes']
        while len(nodes):
            nodes.pop().clear()

        if full:
            self._vClassInfo.clear()
            self._cache['displaySettings'].clear()

    def dump(self, data):
        self.clear()
        nodes = data._nodes
        itemGetter = data.getItem
        self._cache['nodes'] = map(lambda node: self._getVehicleData(node, itemGetter(node['id'])), nodes)
        self._cache['scrollIndex'] = data._scrollIndex
        self._cache['displaySettings'].update(data._displaySettings)
        return self._cache

    def _getVehicleData(self, node, item):
        nodeCD = node['id']
        tags = item.tags
        if len(tags & _PREMIUM_TAGS):
            node['state'] |= NODE_STATE.PREMIUM
        return {'id': nodeCD,
         'state': node['state'],
         'type': item.itemTypeName,
         'nameString': item.shortName,
         'primaryClass': self._vClassInfo.getInfoByTags(tags),
         'level': item.level,
         'longName': item.longName,
         'iconPath': item.icon,
         'smallIconPath': item.smallIcon,
         'pickleDump': item.pack(),
         'earnedXP': node['earnedXP'],
         'shopPrice': node['shopPrice'],
         'displayInfo': node['displayInfo'],
         'unlockProps': node['unlockProps']._makeTuple()}


class NationXMLDumper(NationObjDumper):
    __xmlBody = '<?xml version="1.0" encoding="utf-8"?><tree><nodes>{0:>s}</nodes><scrollIndex>{1:d}</scrollIndex></tree>'
    __nodeFormat = '<node><id>{id:d}</id><nameString>{nameString:>s}</nameString><class><name>{primaryClass[name]:>s}</name><userString>{primaryClass[userString]:>s}</userString></class><level>{level:d}</level><earnedXP>{earnedXP:d}</earnedXP><state>{state:d}</state><unlockProps><parentID>{unlockProps[0]:d}</parentID><unlockIdx>{unlockProps[1]:d}</unlockIdx><xpCost>{unlockProps[2]:n}</xpCost><topIDs>{unlockProps[3]:>s}</topIDs></unlockProps><iconPath>{iconPath:>s}</iconPath><smallIconPath><![CDATA[{smallIconPath:>s}]]></smallIconPath><longName>{longName:>s}</longName><dump><![CDATA[{pickleDump:>s}]]></dump><shopPrice><credits>{shopPrice[0]:n}</credits><gold>{shopPrice[1]:n}</gold></shopPrice><display>{displayInfo:>s}</display></node>'
    __displayInfoFormat = '<row>{row:d}</row><column>{column:d}</column><position><x>{position[0]:n}</x><y>{position[1]:n}</y></position><lines>{lines:>s}</lines>'
    __setFormat = '<set><outLiteral>{0:>s}</outLiteral><outPin><x>{1[0]:n}</x><y>{1[1]:n}</y></outPin><inPins>{2:>s}</inPins></set>'
    __inPinFormat = '<item><childID>{childID:d}</childID><inPin><x>{inPin[0]:n}</x><y>{inPin[1]:n}</y></inPin><viaPins>{dump:>s}</viaPins></item>'
    __viaPinFormat = '<pin><x>{0[0]:n}</x><y>{0[1]:n}</y></pin>'
    __topIDFormat = '<id>{0:d}</id>'

    def __init__(self):
        super(NationXMLDumper, self).__init__('')

    def clear(self, full = False):
        self._cache = ''

    def dump(self, data):
        self._cache = self.__xmlBody.format(self.__buildNodesData(data), data._scrollIndex)
        return self._cache

    def __buildNodesData(self, data):
        nodesDump = []
        itemGetter = data.getItem
        for node in data._nodes:
            data = self._getVehicleData(node, itemGetter(node['id']))
            data['unlockProps'] = self.__buildUnlockProps(data['unlockProps'])
            data['displayInfo'] = self.__buildDisplayInfo(data['displayInfo'])
            nodesDump.append(self.__nodeFormat.format(**data))

        return ''.join(nodesDump)

    def __buildUnlockProps(self, unlockProps):
        dump = map(lambda item: self.__topIDFormat.format(item), unlockProps[-1])
        return unlockProps[:-1] + (''.join(dump),)

    def __buildDisplayInfo(self, displayInfo):
        info = displayInfo.copy()
        lines = info['lines']
        dump = []
        for data in lines:
            inPins = []
            for inPin in data['inPins']:
                viaPins = map(lambda item: self.__viaPinFormat.format(item), inPin['viaPins'])
                inPins.append(self.__inPinFormat.format(dump=''.join(viaPins), **inPin))

            dump.append(self.__setFormat.format(data['outLiteral'], data['outPin'], ''.join(inPins)))

        info['lines'] = ''.join(dump)
        return self.__displayInfoFormat.format(**info)
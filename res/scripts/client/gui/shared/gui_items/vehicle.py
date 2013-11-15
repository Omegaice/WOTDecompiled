# 2013.11.15 11:26:53 EST
# Embedded file name: scripts/client/gui/shared/gui_items/Vehicle.py
import BigWorld
from itertools import izip
from AccountCommands import LOCK_REASON, VEHICLE_SETTINGS_FLAG
from gui import prb_control
from helpers import i18n
from items import vehicles, tankmen, getTypeInfoByName
from gui.prb_control.settings import PREBATTLE_SETTING_NAME
from gui.shared.gui_items import CLAN_LOCK, HasStrCD, FittingItem
from gui.shared.gui_items.serializers import g_itemSerializer
from gui.shared.gui_items.vehicle_modules import Shell, VehicleChassis, VehicleEngine, VehicleRadio, VehicleFuelTank, VehicleTurret, VehicleGun
from gui.shared.gui_items.artefacts import Equipment, OptionalDevice
from gui.shared.gui_items.Tankman import Tankman
from gui.shared.utils import CONST_CONTAINER
from gui.shared.utils.gui_items import findVehicleArmorMinMax
VEHICLE_TYPES_ORDER = ('lightTank', 'mediumTank', 'heavyTank', 'AT-SPG', 'SPG')
VEHICLE_TYPES_ORDER_INDICES = dict(((n, i) for i, n in enumerate(VEHICLE_TYPES_ORDER)))
VEHICLE_BATTLE_TYPES_ORDER = ('heavyTank', 'mediumTank', 'AT-SPG', 'SPG', 'lightTank')
VEHICLE_BATTLE_TYPES_ORDER_INDICES = dict(((n, i) for i, n in enumerate(VEHICLE_BATTLE_TYPES_ORDER)))

class VEHICLE_CLASS_NAME(CONST_CONTAINER):
    LIGHT_TANK = 'lightTank'
    MEDIUM_TANK = 'mediumTank'
    HEAVY_TANK = 'heavyTank'
    SPG = 'SPG'
    AT_SPG = 'AT-SPG'


class Vehicle(FittingItem, HasStrCD):
    NOT_FULL_AMMO_MULTIPLIER = 0.2

    class VEHICLE_STATE:
        DAMAGED = 'damaged'
        EXPLODED = 'exploded'
        DESTROYED = 'destroyed'
        UNDAMAGED = 'undamaged'
        BATTLE = 'battle'
        LOCKED = 'locked'
        CREW_NOT_FULL = 'crewNotFull'
        AMMO_NOT_FULL = 'ammoNotFull'
        SERVER_RESTRICTION = 'serverRestriction'

    class VEHICLE_STATE_LEVEL:
        CRITICAL = 'critical'
        INFO = 'info'
        WARNING = 'warning'

    def __init__(self, strCompactDescr = None, inventoryID = -1, typeCompDescr = None, proxy = None):
        if strCompactDescr is not None:
            vehDescr = vehicles.VehicleDescr(compactDescr=strCompactDescr)
        else:
            raise typeCompDescr is not None or AssertionError
            _, nID, innID = vehicles.parseIntCompactDescr(typeCompDescr)
            vehDescr = vehicles.VehicleDescr(typeID=(nID, innID))
        self.__descriptor = vehDescr
        HasStrCD.__init__(self, strCompactDescr)
        FittingItem.__init__(self, vehDescr.type.compactDescr, proxy)
        self.inventoryID = inventoryID
        self.xp = 0
        self.dailyXPFactor = -1
        self.isElite = False
        self.clanLock = 0
        self.isUnique = self.isHidden
        invData = dict()
        if proxy is not None:
            invDataTmp = proxy.inventory.getItems(vehicles._VEHICLE, inventoryID)
            if invDataTmp is not None:
                invData = invDataTmp
            self.xp = proxy.stats.vehiclesXPs.get(self.intCD, self.xp)
            self.dailyXPFactor = proxy.shop.dailyXPFactor if self.intCD not in proxy.stats.multipliedVehicles else self.dailyXPFactor
            self.isElite = len(vehDescr.type.unlocksDescrs) == 0 or self.intCD in proxy.stats.eliteVehicles
            clanDamageLock = proxy.stats.vehicleTypeLocks.get(self.intCD, {}).get(CLAN_LOCK, 0)
            clanNewbieLock = proxy.stats.globalVehicleLocks.get(CLAN_LOCK, 0)
            self.clanLock = clanDamageLock or clanNewbieLock
        self.inventoryCount = 1 if len(invData.keys()) else 0
        self.settings = invData.get('settings', 0)
        self.lock = invData.get('lock', 0)
        self.repairCost, self.health = invData.get('repair', (0, 0))
        self.gun = VehicleGun(vehDescr.gun['compactDescr'], proxy, vehDescr.gun)
        self.turret = VehicleTurret(vehDescr.turret['compactDescr'], proxy, vehDescr.turret)
        self.engine = VehicleEngine(vehDescr.engine['compactDescr'], proxy, vehDescr.engine)
        self.chassis = VehicleChassis(vehDescr.chassis['compactDescr'], proxy, vehDescr.chassis)
        self.radio = VehicleRadio(vehDescr.radio['compactDescr'], proxy, vehDescr.radio)
        self.fuelTank = VehicleFuelTank(vehDescr.fuelTank['compactDescr'], proxy, vehDescr.fuelTank)
        self.sellPrice = self._calcSellPrice(proxy)
        self.optDevices = self._parserOptDevs(vehDescr.optionalDevices, proxy)
        gunAmmoLayout = []
        for shell in self.gun.defaultAmmo:
            gunAmmoLayout += (shell.intCD, shell.defaultCount)

        self.shells = self._parseShells(invData.get('shells', list()), invData.get('shellsLayout', dict()).get(self.shellsLayoutIdx, gunAmmoLayout), proxy)
        self.eqs = self._parseEqs(invData.get('eqs') or [0, 0, 0], proxy)
        self.eqsLayout = self._parseEqs(invData.get('eqsLayout') or [0, 0, 0], proxy)
        defaultCrew = [None] * len(vehDescr.type.crewRoles)
        crewList = invData.get('crew', defaultCrew)
        self.bonuses = self._calcCrewBonuses(crewList, proxy)
        self.crewIndices = dict([ (invID, idx) for idx, invID in enumerate(crewList) ])
        self.crew = self._buildCrew(crewList, proxy)
        return

    def _calcSellPrice(self, proxy):
        price = list(self.sellPrice)
        defaultDevices, installedDevices, _ = self.descriptor.getDevices()
        for defCompDescr, instCompDescr in izip(defaultDevices, installedDevices):
            if defCompDescr == instCompDescr:
                continue
            modulePrice = FittingItem(defCompDescr, proxy).sellPrice
            price = (price[0] - modulePrice[0], price[1] - modulePrice[1])
            modulePrice = FittingItem(instCompDescr, proxy).sellPrice
            price = (price[0] + modulePrice[0], price[1] + modulePrice[1])

        return price

    def _calcCrewBonuses(self, crew, proxy):
        bonuses = dict()
        bonuses['equipment'] = 0
        for eq in self.eqs:
            if eq is not None:
                bonuses['equipment'] += eq.crewLevelIncrease

        bonuses['optDevices'] = self.descriptor.miscAttrs['crewLevelIncrease']
        bonuses['commander'] = 0
        bonuses['brotherhood'] = tankmen.getSkillsConfig()['brotherhood']['crewLevelIncrease']
        for tankmanID in crew:
            if tankmanID is None:
                bonuses['brotherhood'] = 0
                continue
            tmanInvData = proxy.inventory.getItems(vehicles._TANKMAN, tankmanID)
            if not tmanInvData:
                continue
            tdescr = tankmen.TankmanDescr(compactDescr=tmanInvData['compDescr'])
            if 'brotherhood' not in tdescr.skills or tdescr.skills.index('brotherhood') == len(tdescr.skills) - 1 and tdescr.lastSkillLevel != tankmen.MAX_SKILL_LEVEL:
                bonuses['brotherhood'] = 0
            if tdescr.role == Tankman.ROLES.COMMANDER:
                factor, addition = tdescr.efficiencyOnVehicle(self.descriptor)
                commanderEffRoleLevel = round(tdescr.roleLevel * factor + addition)
                bonuses['commander'] += round((commanderEffRoleLevel + bonuses['brotherhood'] + bonuses['equipment']) / tankmen.COMMANDER_ADDITION_RATIO)

        return bonuses

    def _buildCrew(self, crew, proxy):
        crewItems = list()
        crewRoles = self.descriptor.type.crewRoles
        for idx, tankmanID in enumerate(crew):
            tankman = None
            if tankmanID is not None:
                tmanInvData = proxy.inventory.getItems(vehicles._TANKMAN, tankmanID)
                tankman = Tankman(strCompactDescr=tmanInvData['compDescr'], inventoryID=tankmanID, vehicle=self, proxy=proxy)
            crewItems.append((idx, tankman))

        RO = Tankman.TANKMEN_ROLES_ORDER
        return sorted(crewItems, cmp=lambda a, b: RO[crewRoles[a[0]][0]] - RO[crewRoles[b[0]][0]])

    @staticmethod
    def __crewSort(t1, t2):
        if t1 is None or t2 is None:
            return 0
        else:
            return t1.__cmp__(t2)

    def _parseCompDescr(self, compactDescr):
        nId, innID = vehicles.parseVehicleCompactDescr(compactDescr)
        return (vehicles._VEHICLE, nId, innID)

    def _parseShells(self, layoutList, defaultLayoutsList, proxy):
        result = list()
        for i in xrange(0, len(layoutList), 2):
            intCD = abs(layoutList[i])
            shellsVehCount = layoutList[i + 1]
            shellsDefCount = defaultLayoutsList[i + 1] if i + 1 < len(defaultLayoutsList) else 0
            isBoughtForCredits = defaultLayoutsList[i] < 0 if i < len(defaultLayoutsList) else False
            result.append(Shell(intCD, shellsVehCount, shellsDefCount, proxy, isBoughtForCredits))

        return result

    def _parseEqs(self, layoutList, proxy):
        result = list()
        for i in xrange(len(layoutList)):
            intCD = abs(layoutList[i])
            result.append(Equipment(intCD, proxy, layoutList[i] < 0) if intCD != 0 else None)

        return result

    def _parserOptDevs(self, layoutList, proxy):
        result = list()
        for i in xrange(len(layoutList)):
            optDevDescr = layoutList[i]
            result.append(OptionalDevice(optDevDescr['compactDescr'], proxy) if optDevDescr is not None else None)

        return result

    @property
    def shellsLayoutIdx(self):
        return (self.turret.descriptor['compactDescr'], self.gun.descriptor['compactDescr'])

    @property
    def invID(self):
        return self.inventoryID

    @property
    def descriptor(self):
        return self.__descriptor

    @property
    def type(self):
        return set(vehicles.VEHICLE_CLASS_TAGS & self.descriptor.type.tags).pop()

    @property
    def hasTurrets(self):
        vType = self.descriptor.type
        return len(vType.hull.get('fakeTurrets', {}).get('lobby', ())) != len(vType.turrets)

    @property
    def hasBattleTurrets(self):
        vType = self.descriptor.type
        return len(vType.hull.get('fakeTurrets', {}).get('battle', ())) != len(vType.turrets)

    @property
    def ammoMaxSize(self):
        return self.descriptor.gun['maxAmmo']

    @property
    def isAmmoFull(self):
        return sum((s.count for s in self.shells)) >= self.ammoMaxSize * self.NOT_FULL_AMMO_MULTIPLIER

    @property
    def modelState(self):
        if self.health < 0:
            return Vehicle.VEHICLE_STATE.EXPLODED
        if self.repairCost > 0 and self.health == 0:
            return Vehicle.VEHICLE_STATE.DESTROYED
        return Vehicle.VEHICLE_STATE.UNDAMAGED

    def getState(self):
        ms = self.modelState
        if self.isInBattle:
            ms = Vehicle.VEHICLE_STATE.BATTLE
        elif self.isLocked:
            ms = Vehicle.VEHICLE_STATE.LOCKED
        elif self.isDisabledInRoaming:
            ms = Vehicle.VEHICLE_STATE.SERVER_RESTRICTION
        if ms == Vehicle.VEHICLE_STATE.UNDAMAGED:
            if self.repairCost > 0:
                ms = Vehicle.VEHICLE_STATE.DAMAGED
            elif not self.isCrewFull:
                ms = Vehicle.VEHICLE_STATE.CREW_NOT_FULL
            elif not self.isAmmoFull:
                ms = Vehicle.VEHICLE_STATE.AMMO_NOT_FULL
        return (ms, self.__getStateLevel(ms))

    def __getStateLevel(self, state):
        if state in [Vehicle.VEHICLE_STATE.CREW_NOT_FULL,
         Vehicle.VEHICLE_STATE.DAMAGED,
         Vehicle.VEHICLE_STATE.EXPLODED,
         Vehicle.VEHICLE_STATE.DESTROYED,
         Vehicle.VEHICLE_STATE.SERVER_RESTRICTION]:
            return Vehicle.VEHICLE_STATE_LEVEL.CRITICAL
        if state in [Vehicle.VEHICLE_STATE.UNDAMAGED]:
            return Vehicle.VEHICLE_STATE_LEVEL.INFO
        return Vehicle.VEHICLE_STATE_LEVEL.WARNING

    @property
    def isPremium(self):
        return bool(self.tags & frozenset(('premium',)))

    @property
    def isSecret(self):
        return bool(self.tags & frozenset(('secret',)))

    @property
    def isSpecial(self):
        return bool(self.tags & frozenset(('special',)))

    @property
    def isDisabledInRoaming(self):
        from gui import game_control
        return bool(self.tags & frozenset(('disabledInRoaming',))) and game_control.g_instance.roaming.isInRoaming()

    @property
    def name(self):
        return self.descriptor.type.name

    @property
    def userName(self):
        return self.descriptor.type.userString

    @property
    def longUserName(self):
        typeInfo = getTypeInfoByName('vehicle')
        tagsDump = [ typeInfo['tags'][tag]['userString'] for tag in self.descriptor.type.tags if typeInfo['tags'][tag]['userString'] != '' ]
        return '%s %s' % (' '.join(tagsDump), self.descriptor.type.userString)

    @property
    def shortUserName(self):
        return self.descriptor.type.shortUserString

    @property
    def level(self):
        return self.descriptor.type.level

    @property
    def fullDescription(self):
        if self.descriptor.type.description.find('_descr') == -1:
            return self.descriptor.type.description
        return ''

    @property
    def tags(self):
        return self.descriptor.type.tags

    def _getShortInfo(self, vehicle = None):
        description = i18n.makeString('#menu:descriptions/' + self.itemTypeName)
        ammo = self.descriptor.gun['shots'][0]['shell']['caliber']
        armor = findVehicleArmorMinMax(self.descriptor)
        return description % {'weight': BigWorld.wg_getNiceNumberFormat(float(self.descriptor.physics['weight']) / 1000),
         'armor': BigWorld.wg_getIntegralFormat(armor[1]),
         'ammo': BigWorld.wg_getIntegralFormat(ammo)}

    @property
    def canSell(self):
        st, stLvl = self.getState()
        return st == self.VEHICLE_STATE.UNDAMAGED or st == self.VEHICLE_STATE.CREW_NOT_FULL or st == self.VEHICLE_STATE.AMMO_NOT_FULL

    @property
    def isLocked(self):
        return self.lock != LOCK_REASON.NONE

    @property
    def isInBattle(self):
        return self.lock == LOCK_REASON.ON_ARENA

    @property
    def isAwaitingBattle(self):
        return self.lock == LOCK_REASON.IN_QUEUE

    @property
    def isInUnit(self):
        return self.lock == LOCK_REASON.UNIT

    @property
    def isBroken(self):
        return self.repairCost > 0

    @property
    def isAlive(self):
        return not self.isBroken and not self.isLocked

    @property
    def isCrewFull(self):
        crew = map(lambda (role, tman): tman, self.crew)
        return None not in crew and len(crew)

    def hasLockMode(self):
        isBS = prb_control.isBattleSession()
        if isBS:
            isBSVehicleLockMode = bool(prb_control.getPrebattleSettings()[PREBATTLE_SETTING_NAME.VEHICLE_LOCK_MODE])
            if isBSVehicleLockMode and self.clanLock > 0:
                return True
        return False

    @property
    def isReadyToPrebattle(self):
        result = not self.hasLockMode()
        if result:
            result = not self.isBroken and self.isCrewFull
        return result

    @property
    def isReadyToFight(self):
        result = not self.hasLockMode()
        if result:
            result = self.isAlive and self.isCrewFull and not self.isDisabledInRoaming
        return result

    @property
    def isXPToTman(self):
        return bool(self.settings & VEHICLE_SETTINGS_FLAG.XP_TO_TMAN)

    @property
    def isAutoRepair(self):
        return bool(self.settings & VEHICLE_SETTINGS_FLAG.AUTO_REPAIR)

    @property
    def isAutoLoad(self):
        return bool(self.settings & VEHICLE_SETTINGS_FLAG.AUTO_LOAD)

    @property
    def isAutoEquip(self):
        return bool(self.settings & VEHICLE_SETTINGS_FLAG.AUTO_EQUIP)

    @property
    def isFavorite(self):
        return bool(self.settings & VEHICLE_SETTINGS_FLAG.GROUP_0)

    def __eq__(self, other):
        if other is None:
            return False
        else:
            return self.descriptor.type.id == other.descriptor.type.id

    def __repr__(self):
        return 'Vehicle<id:%d, intCD:%d, nation:%d, lock:%d>' % (self.invID,
         self.intCD,
         self.nationID,
         self.lock)

    def toDict(self):
        result = FittingItem.toDict(self)
        result.update({'inventoryID': self.inventoryID,
         'xp': self.xp,
         'dailyXPFactor': self.dailyXPFactor,
         'clanLock': self.clanLock,
         'isUnique': self.isUnique,
         'crew': [ (g_itemSerializer.pack(tankman) if tankman else None) for role, tankman in self.crew ],
         'settings': self.settings,
         'lock': self.lock,
         'repairCost': self.repairCost,
         'health': self.health,
         'gun': g_itemSerializer.pack(self.gun),
         'turret': g_itemSerializer.pack(self.turret),
         'engine': g_itemSerializer.pack(self.engine),
         'chassis': g_itemSerializer.pack(self.chassis),
         'radio': g_itemSerializer.pack(self.radio),
         'fuelTank': g_itemSerializer.pack(self.fuelTank),
         'optDevices': [ (g_itemSerializer.pack(dev) if dev else None) for dev in self.optDevices ],
         'shells': [ (g_itemSerializer.pack(shell) if shell else None) for shell in self.shells ],
         'eqs': [ (g_itemSerializer.pack(eq) if eq else None) for eq in self.eqs ],
         'eqsLayout': [ (g_itemSerializer.pack(eq) if eq else None) for eq in self.eqsLayout ],
         'type': self.type,
         'isPremium': self.isPremium,
         'isElite': self.isElite,
         'icon': self.icon,
         'isLocked': self.isLocked,
         'isBroken': self.isBroken,
         'isAlive': self.isAlive})
        return result

    def getCtorArgs(self):
        return [self.strCD, self.invID]

    def fromDict(self, d):
        FittingItem.fromDict(self, d)
        self.inventoryID = d.get('inventoryID', -1)
        self.xp = d.get('xp', 0)
        self.isUnique = d.get('isUnique', 0)
        self.dailyXPFactor = d.get('dailyXPFactor', -1)
        self.isElite = d.get('isElite', False)
        self.clanLock = d.get('clanLock', 0)
        self.crew = [ (g_itemSerializer.unpack(t) if t else None) for t in d.get('crew', list()) ]
        self.settings = d.get('settings', 0)
        self.lock = d.get('lock', 0)
        self.repairCost = d.get('repairCost', 0)
        self.health = d.get('health', 0)
        self.gun = g_itemSerializer.unpack(d.get('gun'))
        self.turret = g_itemSerializer.unpack(d.get('turret'))
        self.engine = g_itemSerializer.unpack(d.get('engine'))
        self.chassis = g_itemSerializer.unpack(d.get('chassis'))
        self.radio = g_itemSerializer.unpack(d.get('radio'))
        self.fuelTank = g_itemSerializer.unpack(d.get('fuelTank'))
        self.shells = [ (g_itemSerializer.unpack(shell) if shell else None) for shell in d.get('shells', list()) ]
        self.optDevices = [ (g_itemSerializer.unpack(dev) if dev else None) for dev in d.get('optDevices', list()) ]
        self.eqs = [ (g_itemSerializer.unpack(eq) if eq else None) for eq in d.get('eqs', list()) ]
        self.eqsLayout = [ (g_itemSerializer.unpack(eq) if eq else None) for eq in d.get('eqsLayout', list()) ]
        return

    def _sortByType(self, other):
        return VEHICLE_TYPES_ORDER_INDICES[self.type] - VEHICLE_TYPES_ORDER_INDICES[other.type]
# okay decompyling res/scripts/client/gui/shared/gui_items/vehicle.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2013.11.15 11:26:54 EST

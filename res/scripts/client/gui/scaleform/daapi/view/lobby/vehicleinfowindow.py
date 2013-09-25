# Embedded file name: scripts/client/gui/Scaleform/daapi/view/lobby/VehicleInfoWindow.py
from debug_utils import LOG_ERROR
__author__ = 'i_maliavko'
from items import tankmen
from helpers import i18n
from adisp import process
from gui.Scaleform.Waiting import Waiting
from gui.Scaleform.framework.entities.View import View
from gui.Scaleform.daapi.view.meta.VehicleInfoMeta import VehicleInfoMeta
from gui.Scaleform.daapi.view.meta.WindowViewMeta import WindowViewMeta
from gui.shared.utils.requesters import ItemsRequester

class VehicleInfoWindow(View, VehicleInfoMeta, WindowViewMeta):

    def __init__(self, vehicleDescr):
        super(VehicleInfoWindow, self).__init__()
        self.vehicleDescr = vehicleDescr

    def onCancelClick(self):
        self.destroy()

    def onWindowClose(self):
        self.destroy()

    @process
    def getVehicleInfo(self):
        Waiting.show('updating')
        items = yield ItemsRequester().request()
        vehicle = items.getItemByCD(self.vehicleDescr.type.compactDescr)
        if vehicle is None:
            LOG_ERROR('There is error while showing vehicle info window: ', self.vehicleDescr.type.compactDescr)
            return
        else:
            params = vehicle.getParams()
            tankmenParams = list()
            for slotIdx, tankman in vehicle.crew:
                role = vehicle.descriptor.type.crewRoles[slotIdx][0]
                tankmanLabel = ''
                if tankman is not None:
                    tankmanLabel = '%s %s (%d%%)' % (tankman.rankUserName, tankman.lastUserName, tankman.roleLevel)
                tankmenParams.append({'tankmanType': i18n.convert(tankmen.getSkillsConfig()[role].get('userString', '')),
                 'value': tankmanLabel})

            info = {'vehicleName': vehicle.longUserName,
             'vehicleDiscription': vehicle.fullDescription,
             'vehicleImage': vehicle.icon,
             'vehicleLevel': vehicle.level,
             'vehicleNation': vehicle.nationID,
             'vehicleElite': vehicle.isElite,
             'vehicleType': vehicle.type,
             'VehicleInfoPropsData': [ {'name': n,
                                      'value': v} for n, v in params['parameters'] ],
             'VehicleInfoBaseData': params['base'],
             'VehicleInfoCrewData': tankmenParams}
            self.as_setVehicleInfoS(info)
            Waiting.hide('updating')
            return
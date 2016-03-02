# -*- coding: utf-8 -*-

"""
.. module:: zwemulator

This file is part of **py-zwave-emulator** project #https://github.com/Nico0084/py-zwave-emulator.
    :platform: Unix, Windows, MacOS X
    :sinopsis: ZWave emulator Python

This project is based on openzwave #https://github.com/OpenZWave/open-zwave to pass thought hardware zwave device. It use for API developping or testing.

- Openzwave config files are use to load a fake zwave network an handle virtual nodes. All configured manufacturer device cant be create in emulator.
- Use serial port emulator to create com, you can use software like socat #http://www.dest-unreach.org/socat/
- eg command line : socat -d -d PTY,ignoreeof,echo=0,raw,link=/tmp/ttyS0 PTY,ignoreeof,echo=0,raw,link=/tmp/ttyS1 &
- Run from bin/zwemulator.py
- Web UI access in local, port 4500


.. moduleauthor: Nico0084 <nico84dev@gmail.com>

License : GPL(v3)

**py-zwave-emulator** is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

**py-zwave-emulator** is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with py-zwave-emulator. If not, see http:#www.gnu.org/licenses.

"""

from zwemulator.lib.defs import *
from zwemulator.lib.log import LogLevel
from zwemulator.lib.driver import MsgQueue, Msg
from commandclass import CommandClass

class SensorBinaryCmd(EnumNamed):
	Get		= 0x02
	Report		= 0x03

class SensorBinary(CommandClass):

    StaticGetCommandClassId = 0x30
    StaticGetCommandClassName = "COMMAND_CLASS_SENSOR_BINARY"

    def __init__(self, node,  data):
        CommandClass.__init__(self, node, data)
        if 'sensorMaps' in data : self.sensorMaps = data['sensorMaps']
        else : self.sensorMaps = []
        self._log.write(LogLevel.Detail, self, "SensorMaps = {0}, With DATA : {1}".format(self.sensorMaps, data))

    GetCommandClassId = property(lambda self: self.StaticGetCommandClassId)
    GetCommandClassName = property(lambda self: self.StaticGetCommandClassName)
    getCmd = property(lambda self: SensorBinaryCmd.Get)

    def getFullNameCmd(self,  _id):
        return SensorBinaryCmd().getFullName(_id)

    def getByteIndex(self,  type):
        if self.sensorMaps :
            for map in self.sensorMaps:
                if map['type'] == type : return map['index']
        return 0

    def getByteType(self,  index):
        if self.sensorMaps :
            for map in self.sensorMaps:
                if map['index'] == index : return map['type']
        return 0

    def getActiveIndex(self):
        if self.sensorMaps : return self.sensorMaps[0]['index']
        else: return 0

    def getDataMsg(self, _data, instance=1):
        self._log.write(LogLevel.Detail, self, " getDataMsg : {0} of instance {1}".format(GetDataAsHex(_data), instance))
        msgData = []
        if _data[0] == SensorBinaryCmd.Get:
            value = self._node.getValue(self.GetCommandClassId, instance, 0) #  index is allways 0
            if value is not None :
                msgData.append(self.GetCommandClassId)
                msgData.append(SensorBinaryCmd.Report)
                msgData.append(value.getValueByte())
        return msgData

    def ProcessMsg(self, _data, instance=1, multiInstanceData = []):
        print '++++++++++++++++ SensorBinary ProcessMsg +++++++++++++++'
        if _data[0] == SensorBinaryCmd.Get:
            msg = Msg("SensorBinaryCmd_Report", self.nodeId,  REQUEST, FUNC_ID_APPLICATION_COMMAND_HANDLER)
            index = self.getActiveIndex()
            vData = self._node.getValue(self.GetCommandClassId, instance, index)
            msg.Append(TRANSMIT_COMPLETE_OK)
            msg.Append(self.nodeId)
            if self.sensorMaps : msg.Append(3)
            else : msg.Append(2)
            msg.Append(self.GetCommandClassId)
            msg.Append(SensorBinaryCmd.Report)
            msg.Append(vData.getValueByte())
            if self.sensorMaps : msg.Append(self.getByteType(index))
            self.GetDriver.SendMsg(msg, MsgQueue.NoOp)
        else:
            self._log.write(LogLevel.Warning, self, "CommandClass REQUEST {0}, Not implemented : {1}".format(self.getFullNameCmd(_data[0]), GetDataAsHex(_data)))



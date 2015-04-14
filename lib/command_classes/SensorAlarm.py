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

class SensorAlarmCmd(EnumNamed):
	Get				= 0x01
	Report			= 0x02
	SupportedGet		= 0x03
	SupportedReport	= 0x04

c_alarmTypeName = [
    "General",
    "Smoke",
    "Carbon Monoxide",
    "Carbon Dioxide",
    "Heat",
    "Flood"
    ]
    
class SensorAlarm(CommandClass):
    
    StaticGetCommandClassId = 0x9c
    StaticGetCommandClassName = "COMMAND_CLASS_SENSOR_ALARM"
    
    def __init__(self, node,  data):
        CommandClass.__init__(self, node, data)
    
    GetCommandClassId = property(lambda self: self.StaticGetCommandClassId)
    GetCommandClassName = property(lambda self: self.StaticGetCommandClassName)

    def getFullNameCmd(self,  _id):
        return SensorAlarmCmd().getFullName(_id)

    def getTypeAlarm(self, label):
        id = 0
        for type in c_alarmTypeName : 
            if label == type : return id
            id += 1
        self._log.write(LogLevel.Error, self, "Alarm type invalid : {0}".format(label))

    def ProcessMsg(self, _data, instance=1, multiInstanceData = []):
        print '++++++++++++++++ SensorAlarm ProcessMsg +++++++++++++++'
        if _data[0] == SensorAlarmCmd.Get: 
            msg = Msg("SensorAlarmCmd_Report", self.nodeId,  REQUEST, FUNC_ID_APPLICATION_COMMAND_HANDLER, False)
            vData = self._node.getValue(self.GetCommandClassId, instance, 1)
            msg.Append(TRANSMIT_COMPLETE_OK)
            msg.Append(self.nodeId)
            msg.Append(5)
            msg.Append(self.GetCommandClassId)
            msg.Append(SensorAlarmCmd.Report)
            msg.Append(self.nodeId)
            msg.Append(self.getTypeAlarm(vData._label))
            msg.Append(vData.getValueByte())
            # TODO: Add extend msg but openzwave don't known what : // uint16 time = (((uint16)_data[4])<<8) | (uint16)_data[5];  Don't know what to do with this yet.
            self.GetDriver.SendMsg(msg, MsgQueue.NoOp)
        elif _data[0] == SensorAlarmCmd.SupportedGet: 
            msg = Msg("SensorAlarmCmd_SupportedReport", self.nodeId,  REQUEST, FUNC_ID_APPLICATION_COMMAND_HANDLER, False)
            values = self._node.getCmdClassValues(self.GetCommandClassId)
            alarms = []
            for v in values : alarms.append(v._label)
            data = self.codeAlarmType(alarms)      
            msg.Append(TRANSMIT_COMPLETE_OK)
            msg.Append(self.nodeId)
            msg.Append(2 + len(data))
            msg.Append(self.GetCommandClassId)
            msg.Append(SensorAlarmCmd.SupportedReport)
            for d in data : 
                msg.Append(d)
            self.GetDriver.SendMsg(msg, MsgQueue.NoOp)
        else:
            self._log.write(LogLevel.Warning, self, "CommandClass REQUEST {0}, Not implemented : {1}".format(self.getFullNameCmd(_data[0]), GetDataAsHex(_data)))

    def codeAlarmType(self, alarms):
        if alarms :
            numBytes = (len(alarms)/8) + 1
            data = [numBytes]
            num = 0
            nB = 1
            data.append(0)
            for a in alarms:
                print a
                try : 
                    index = c_alarmTypeName.index(a)
                    num += 1
                    if num > 8 :
                        nB += 1
                        data.append(0)
                        num = 0
                    data[nB] = data[nB] | (1 << index)
                    print data
                except :
                    pass
            data[0] = nB
            return data
        else : return [0]

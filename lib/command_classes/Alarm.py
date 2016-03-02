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

class AlarmCmd(EnumNamed):
	Get	= 0x04
	Report = 0x05
#	 Version 2
	SupportedGet		= 0x07
	SupportedReport	= 0x08

class AlarmIndex:
    Type = 0
    Level = 1
    SourceNodeId = 2

c_alarmTypeName = [
    "General",
    "Smoke",
    "Carbon Monoxide",
    "Carbon Dioxide",
    "Heat",
    "Flood",
    "Access Control",
    "Burglar",
    "Power Management",
    "System",
    "Emergency",
    "Clock",
    "Appliance",
    "HomeHealth"
    ]

class Alarm(CommandClass):

    StaticGetCommandClassId = 0x71
    StaticGetCommandClassName = "COMMAND_CLASS_ALARM"

    def __init__(self, node,  data):
        CommandClass.__init__(self, node, data)

    GetCommandClassId = property(lambda self: self.StaticGetCommandClassId)
    GetCommandClassName = property(lambda self: self.StaticGetCommandClassName)
    getCmd = property(lambda self: AlarmCmd.Get)

    def getFullNameCmd(self,  _id):
        return AlarmCmd().getFullName(_id)

    def getDataMsg(self, _data, instance=1):
        self._log.write(LogLevel.Detail, self, " getDataMsg : {0} of instance {1}".format(GetDataAsHex(_data), instance))
        msgData = []
        if _data[0] == AlarmCmd.Get:
            vType = self._node.getValue(self.GetCommandClassId, instance, AlarmIndex.Type)
            vLevel = self._node.getValue(self.GetCommandClassId, instance, AlarmIndex.Level)
            if vLevel is not None  and vType is not None :
                msgData.append(self.GetCommandClassId)
                msgData.append(AlarmCmd.Report)
                msgData.append(vType.getValueByte())
                msgData.append(vLevel.getValueByte())
            if self.m_version >= 2 :
                vSourceNodeID = self._node.getValue(self.GetCommandClassId, instance, SourceNodeId)
                value = self._node.getValue(self.GetCommandClassId, instance, _data[1] + 3)
                if vSourceNodeID is not None and value is not None:
                    msgData.append(vSourceNodeID.getValueByte())
                    msgData.append(0xff)  # Add Status
                    msgData.append(value.index - 3) # Add index - offset
                    msgData.append(value.getValueByte())
                    msgData.append(0x00)  # add 3 0x00, don't known why !
                    msgData.append(0x00)
                    msgData.append(0x00)
        return msgData

    def ProcessMsg(self, _data, instance=1, multiInstanceData = []):
        print '++++++++++++++++ Alarm ProcessMsg +++++++++++++++'
        if _data[0] == AlarmCmd.Get:
            msg = Msg("AlarmCmd_Report", self.nodeId,  REQUEST, FUNC_ID_APPLICATION_COMMAND_HANDLER)
            msg.Append(TRANSMIT_COMPLETE_OK)
            msg.Append(self.nodeId)
            msg.Append(4)
            if  len(_data) >= 5 and _data[1] == 0x00 : # Version 2
                data = self.getDataMsg([AlarmCmd.Get, _data[2]], instance)
            msg.Append(len(data))
            for d in data : msg.Append(d)
            self.GetDriver.SendMsg(msg, MsgQueue.NoOp)
        else:
            self._log.write(LogLevel.Warning, self, "CommandClass REQUEST {0}, Not implemented : {1}".format(self.getFullNameCmd(_data[0]), GetDataAsHex(_data)))


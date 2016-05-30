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

from lib.defs import *
from lib.log import LogLevel
from lib.driver import MsgQueue, Msg
from commandclass import CommandClass

class MultiInstanceCmd(EnumNamed):
    Get		= 0x04
    Report	= 0x05
    Encap	= 0x06

    # Version 2
    EndPointGet			= 0x07
    EndPointReport		= 0x08
    CapabilityGet			= 0x09
    CapabilityReport		= 0x0a
    EndPointFind			= 0x0b
    EndPointFindReport	= 0x0c
    EncapV2				    = 0x0d

class MultiInstanceMapping:
    MapAll = 0
    MapEndPoints = 1
    MapOther = 2

c_genericClass = [
    0x21,		# Multilevel Sensor
    0x20,		# Binary Sensor
    0x31,		# Meter
    0x08,		# Thermostat
    0x11,		# Multilevel Switch
    0x10,		# Binary Switch
    0x12,		# Remote Switch
    0xa1,		# Alarm Sensor
    0x16,		# Ventilation
    0x30,		# Pulse Meter
    0x40,		# Entry Control
    0x13,		# Toggle Switch
    0x03,		# AV Control Point
    0x04,		# Display
    0x00		# End of list
    ]

c_genericClassName = [
    "Multilevel Sensor",
    "Binary Sensor",
    "Meter",
    "Thermostat",
    "Multilevel Switch",
    "Binary Switch",
    "Remote Switch",
    "Alarm Sensor",
    "Ventilation",
    "Pulse Meter",
    "Entry Control",
    "Toggle Switch",
    "AV Control Point",
    "Display"
]

class MultiInstance(CommandClass):

    StaticGetCommandClassId = 0x60
    StaticGetCommandClassName = "COMMAND_CLASS_MULTI_INSTANCE"

    def __init__(self, node,  data):
        CommandClass.__init__(self, node, data)

    GetCommandClassId = property(lambda self: self.StaticGetCommandClassId)
    GetCommandClassName = property(lambda self: self.StaticGetCommandClassName)
    reportCmd = property(lambda self: MultiInstanceCmd.Report)
    getCmd = property(lambda self: MultiInstanceCmd.EncapV2 if self.m_version > 1 else MultiInstanceCmd.Encap)

    def getFullNameCmd(self,  _id):
        return MultiInstanceCmd().getFullName(_id)

    def ProcessMsg(self, _data, instance=1, multiInstanceData = []):
        # Version 1  MULTI_INSTANCE
        if _data[0] == MultiInstanceCmd.Get:
            msg = Msg("MultiInstanceCmd_Report", self.nodeId,  REQUEST, FUNC_ID_APPLICATION_COMMAND_HANDLER)
            clss = self._node.GetCommandClass(_data[1])
            if clss is not None :
                msg.Append(TRANSMIT_COMPLETE_OK)
                msg.Append(self.nodeId)
                msg.Append(0x04)
                msg.Append(self.GetCommandClassId)
                msg.Append(MultiInstanceCmd.Report)
                msg.Append(clss.GetCommandClassId)
                msg.Append(len(clss.instances))
                self.GetDriver.SendMsg(msg, MsgQueue.NoOp)
            else :
                self._log.write(LogLevel.Error, self._node, "MultiInstance Version 1 commandClass 0x%.2x don't exist"%_data[1])

        # Version 2 MULTI_CHANNEL
        elif _data[0] == MultiInstanceCmd.EndPointGet:
            msg = Msg( "MultiChannelCmd_EndPoint_Report", self.nodeId,  REQUEST, FUNC_ID_APPLICATION_COMMAND_HANDLER)
            msg.Append(TRANSMIT_COMPLETE_OK)
            msg.Append(self.nodeId)
            msg.Append(0x04)
            msg.Append(self.GetCommandClassId)
            msg.Append(MultiInstanceCmd.EndPointReport)
            endP = 0x80 if self._node.numEndPointsCanChange else 0x00
            if self._node.endPointsAreSameClass : endP = endP or 0x40
            msg.Append(endP)
            msg.Append(self._node.numEndPoints)
            self.GetDriver.SendMsg(msg, MsgQueue.NoOp)
        elif _data[0] == MultiInstanceCmd.CapabilityGet:
            endPoint = _data[1]
            msg = Msg( "MultiChannelCmd_Capability_Report", self.nodeId,  REQUEST, FUNC_ID_APPLICATION_COMMAND_HANDLER)
            msg.Append(TRANSMIT_COMPLETE_OK)
            msg.Append(self.nodeId)
            mapEndpoint = self._node.getEndpointCmdClasses(endPoint)
            cmdClasses = []
            afterMark = []
            for clssId in mapEndpoint:
                clss = self._node.GetCommandClass(clssId)
                if clss.m_afterMark :
                    if not afterMark : afterMark = [0xef]
                    afterMark.append(clssId)
                else : cmdClasses.append(clssId)
            cmdClasses.extend(afterMark)
            msg.Append(5 + len(cmdClasses))
            msg.Append(self.GetCommandClassId)
            msg.Append(MultiInstanceCmd.CapabilityReport)
            # TODO: Handle dynamic devices with msg.Append(endPoint and 0x80), don't known what is dynamic
            msg.Append(endPoint)
            msg.Append(self._node.generic)
            msg.Append(self._node.specific)
            for i in cmdClasses: msg.Append(i)
            self.GetDriver.SendMsg(msg, MsgQueue.NoOp)
        elif _data[0] == MultiInstanceCmd.EncapV2:
            endPoint = _data[2]
            cmdClss = self._node.GetCommandClass(_data[2])
            if cmdClss is not None:
                msg = Msg( "MultiChannelCmd_EncapV2_Report", self.nodeId,  REQUEST, FUNC_ID_APPLICATION_COMMAND_HANDLER)
                msgHeader = [TRANSMIT_COMPLETE_OK]
                msgHeader.append(self.nodeId)
                instance = self._node.getInstanceFromEndpoint(_data[3], endPoint)
                if instance :
                    self._log.write(LogLevel.Detail, self._node, "     MultiChannelCmd_EncapV2, Call {0}, instance :{1}".format(cmdClss.GetCommandClassName, instance))
                    msgHeader.append(4)# + len(msgData))
                    msgHeader.append(self.GetCommandClassId)
                    msgHeader.append(MultiInstanceCmd.EncapV2)
                    msgHeader.append(endPoint)
                    msgHeader.append(0x01) # TODO: don't known signification
                    cmdClss.ProcessMsg(_data[4:], instance, msgHeader)
        elif _data[0] == MultiInstanceCmd.Encap:
            endPoint = _data[1]
            cmdClss = self._node.GetCommandClass(_data[2])
            if cmdClss is not None:
                msg = Msg( "MultiChannelCmd_Encap_Report", self.nodeId,  REQUEST, FUNC_ID_APPLICATION_COMMAND_HANDLER)
                msgHeader = [TRANSMIT_COMPLETE_OK]
                msgHeader.append(self.nodeId)
                instance = self._node.getInstanceFromEndpoint(_data[2], endPoint)
                if instance :
                    self._log.write(LogLevel.Detail, self._node, "     MultiChannelCmd_Encap, Call {0}, instance :{1}".format(cmdClss.GetCommandClassName, instance))
                    msgHeader.append(3)# + len(msgData))
                    msgHeader.append(instance)
                    msgHeader.append(self.GetCommandClassId)
                    msgHeader.append(MultiInstanceCmd.Encap)
                    cmdClss.ProcessMsg(_data[3:], instance, msgHeader)

        else :
            self._log.write(LogLevel.Warning, self, "CommandClass REQUEST {0}, Not implemented : {1}".format(self.getFullNameCmd(_data[0]), GetDataAsHex(_data)))


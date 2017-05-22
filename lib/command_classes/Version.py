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

class VersionCmd(EnumNamed):
	Get					     = 0x11
	Report				     = 0x12
	CommandClassGet	 = 0x13
	CommandClassReport = 0x14

class VersionIndex:
    Library = 0
    Protocol = 1
    Application = 2

class Version(CommandClass):

    StaticGetCommandClassId = 0x86
    StaticGetCommandClassName = "COMMAND_CLASS_VERSION"

    def __init__(self, node,  data):
        CommandClass.__init__(self, node, data)

    GetCommandClassId = property(lambda self: self.StaticGetCommandClassId)
    GetCommandClassName = property(lambda self: self.StaticGetCommandClassName)

    def getFullNameCmd(self,  _id):
        return VersionCmd().getFullName(_id)

    def ProcessMsg(self, _data, instance=1):
        if _data[0] == VersionCmd.Get:
            msg = Msg( "VersionCmd_Report", self.nodeId,  REQUEST, FUNC_ID_APPLICATION_COMMAND_HANDLER)
            msg.Append(TRANSMIT_COMPLETE_OK)
            msg.Append(self.nodeId)
            msg.Append(0x07)
            msg.Append(self.GetCommandClassId)
            msg.Append(VersionCmd.Report)
            libraryValue = self._node.getValue(self.GetCommandClassId, instance, VersionIndex.Library)
            if libraryValue is None :
               self._log.write(LogLevel.Error, self, "CommandClass Version as no Library form xml file.")
               return
            msg.Append(int(libraryValue.getVal()))
            protocolValue = self._node.getValue(self.GetCommandClassId, instance, VersionIndex.Protocol)
            if protocolValue is None :
               self._log.write(LogLevel.Error, self, "CommandClass Version as no Protocol form xml file.")
               return
            p = protocolValue.getVal().split('.')
            msg.Append(int(p[0]))
            msg.Append(int(p[1]))
            applicationValue = self._node.getValue(self.GetCommandClassId, instance, VersionIndex.Application)
            if applicationValue is None :
               self._log.write(LogLevel.Error, self, "CommandClass Version as no Application form xml file.")
               return
            p = applicationValue.getVal().split('.')
            msg.Append(int(p[0]))
            msg.Append(int(p[1]))
            self.GetDriver.SendMsg(msg, MsgQueue.NoOp)
        elif _data[0] == VersionCmd.CommandClassGet:
            msg = Msg( "VersionCmd_CommandClass_Report", self.nodeId,  REQUEST, FUNC_ID_APPLICATION_COMMAND_HANDLER)
            clss = self._node.GetCommandClass( _data[1])
            if clss is not None :
                msg.Append(TRANSMIT_COMPLETE_OK)
                msg.Append(self.nodeId)
                msg.Append(0x04)
                msg.Append(self.GetCommandClassId)
                msg.Append(VersionCmd.CommandClassReport)
                msg.Append(clss.GetCommandClassId)
                msg.Append(clss.m_version)
                self.GetDriver.SendMsg(msg, MsgQueue.NoOp)
            else :
                self._log.write(LogLevel.Warning, self, "Bad commandClass id version request : 0x%.2x"%_data[1])
        else:
            self._log.write(LogLevel.Warning, self, "CommandClass REQUEST {0}, Not implemented : {1}".format(self.getFullNameCmd(_data[0]), GetDataAsHex(_data)))

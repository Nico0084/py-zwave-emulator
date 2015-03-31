# -*- coding: utf-8 -*-

"""
.. module:: libopenzwave

This file is part of **python-openzwave-emulator** project http:#github.com/p/python-openzwave-emulator.
    :platform: Unix, Windows, MacOS X
    :sinopsis: openzwave simulator Python

This project is based on python-openzwave to pass thought hardware zwace device. It use for API developping or testing.
All C++ and cython code are moved.

.. moduleauthor: Nico0084 <nico84dev@gmail.com>
.. moduleauthor: bibi21000 aka Sébastien GALLET <bibi21000@gmail.com>
.. moduleauthor: Maarten Damen <m.damen@gmail.com>

License : GPL(v3)

**python-openzwave** is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

**python-openzwave** is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with python-openzwave. If not, see http:#www.gnu.org/licenses.

"""

from zwemulator.lib.defs import *
from zwemulator.lib.log import LogLevel
from zwemulator.lib.driver import MsgQueue, Msg
from commandclass import CommandClass

class SwitchBinaryCmd(EnumNamed):
    Set		= 0x01
    Get		= 0x02
    Report	= 0x03
    
class SwitchBinary(CommandClass):
    
    StaticGetCommandClassId = 0x25
    StaticGetCommandClassName = "COMMAND_CLASS_SWITCH_BINARY"
    
    def __init__(self, node,  data):
        CommandClass.__init__(self, node, data)
    
    GetCommandClassId = property(lambda self: self.StaticGetCommandClassId)
    GetCommandClassName = property(lambda self: self.StaticGetCommandClassName)
    reportCmd = property(lambda self: SwitchBinaryCmd.Report)
    getCmd = property(lambda self: SwitchBinaryCmd.Get)

    def getFullNameCmd(self,  _id):
        return SwitchBinaryCmd().getFullName(_id)

    def getByteIndex(self, instance):
        """Must return a specific byte to get type (as index of value)"""
        #  index is allways 0
        return 0

    def getDataMsg(self, _data, instance=1):
        self._log.write(LogLevel.Detail, self, " getDataMsg : {0} of instance {1}".format(GetDataAsHex(_data), instance))
        msgData = []
        if _data[0] == SwitchBinaryCmd.Get:
            value = self._node.getValue(self.GetCommandClassId, instance, 0) #  index is allways 0
            if value is not None :
                msgData.append(self.GetCommandClassId)
                msgData.append(SwitchBinaryCmd.Report)
                msgData.append(value.getValueByte())
        return msgData        

    def ProcessMsg(self, _data, instance=1, multiInstanceData = []):
        if _data[0] == SwitchBinaryCmd.Get:
            msg = Msg("SwitchBinaryCmd_Report", self.nodeId,  REQUEST, FUNC_ID_APPLICATION_COMMAND_HANDLER, False)
            msgData = self.getDataMsg(_data, instance)
            if msgData :
                if multiInstanceData :
                    multiInstanceData[2] += len(msgData)
                    for v in multiInstanceData : msg.Append(v)
                else :
                    msg.Append(TRANSMIT_COMPLETE_OK)
                    msg.Append(self.nodeId)
                    msg.Append(len(msgData))
                for v in msgData : msg.Append(v)
                self.GetDriver.SendMsg(msg, MsgQueue.NoOp)    
            else :
                msg.Append(TRANSMIT_COMPLETE_NOROUTE)
                msg.Append(self.nodeId)
                self.GetDriver.SendMsg(msg, MsgQueue.NoOp)
        elif _data[0] == SwitchBinaryCmd.Set :
            value = self._node.getValue(self.GetCommandClassId, instance, 0) #  index is allways 0
            if value is not None :
                value._value = True if _data[1] else False
                #TODO: Verifie is response is necessary ?
                self._log.write(LogLevel.Detail, self, "SwitchBinaryCmd on/off cmd received: {0}".format('On' if _data[1]else 'Off'))
                self.HandleReportChange("SwitchBinaryCmd_Report", self, [SwitchBinaryCmd.Get], instance)
        else:
            self._log.write(LogLevel.Warning, self, "CommandClass REQUEST {0}, Not implemented : {1}".format(self.getFullNameCmd(_data[0]), GetDataAsHex(_data)))


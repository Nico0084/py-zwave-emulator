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
from zwemulator.lib.notification import Notification, NotificationType
from zwemulator.lib.log import LogLevel
from zwemulator.lib.driver import MsgQueue, Msg
from commandclass import CommandClass

class NoOperation(CommandClass):
    
    StaticGetCommandClassId = 0x00
    StaticGetCommandClassName = "COMMAND_CLASS_NO_OPERATION"
    
    def __init__(self, node,  data):
        CommandClass.__init__(self, node,  data)
    
    GetCommandClassId = property(lambda self: self.StaticGetCommandClassId)
    GetCommandClassName = property(lambda self: self.StaticGetCommandClassName)

    def HandleMsg(self, *_data, **params):
        """Handle a message from the fake Z-Wave network"""
        # We have received a no operation from the Z-Wave device.
        self._log.write(LogLevel.Detail, self._node, "Received NoOperation command from node {0}", self.nodeId)
        return true

    def Set(self, _route, _queue = MsgQueue.NoOp): 
        # Send a No Operation fake message class.
        self._log.write(LogLevel.Detail, self._node, "NoOperation::Set - Routing={0}".format(_route))
        msg = Msg( "NoOperation_Set", self.nodeId,  REQUEST, FUNC_ID_ZW_SEND_DATA, True )
        msg.Append(self.nodeId)
        msg.Append(2)
        msg.Append(self.GetCommandClassId)
        msg.Append(0)
        if _route :
            msg.Append(self.GetDriver.GetTransmitOptions)
        else :
            msg.Append( TRANSMIT_OPTION_ACK | TRANSMIT_OPTION_NO_ROUTE )
        self.GetDriver.SendMsg(msg, _queue )
    
    
    
    


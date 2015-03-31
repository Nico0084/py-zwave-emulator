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

class witchMultilevelCmd:
	Set						= 0x01
	Get						= 0x02
	Report					= 0x0
	StartLevelChange				= 0x04
	StopLevelChange				= 0x05
	SupportedGet				= 0x06
	SupportedReport				= 0x07

class	SwitchMultilevelIndex:
    Level = 0
    Bright = 1
    Dim = 2
    IgnoreStartLevel = 3
    StartLevel = 4
    Duration = 5
    Step = 6
    Inc = 7
    Dec = 8

c_directionParams = [
    0x18,
    0x58,
    0xc0,
    0xc8
    ]

c_directionDebugLabels = [
    "Up",
    "Down",
    "Inc",
    "Dec"
    ]

c_switchLabelsPos = [
    "Undefined",
    "On",
    "Up",
    "Open",
    "Clockwise",
    "Right",
    "Forward",
    "Push"
    ]

c_switchLabelsNeg = [
    "Undefined",
    "Off",
    "Down",
    "Close",
    "Counter-Clockwise",
    "Left",
    "Reverse",
    "Pull"
    ]
    
class SwitchMultilevel(CommandClass):
    
    StaticGetCommandClassId = 0x26
    StaticGetCommandClassName = "COMMAND_CLASS_SWITCH_MULTILEVEL"
    
    def __init__(self, node,  data):
        CommandClass.__init__(self, node, data)
    
    GetCommandClassId = property(lambda self: self.StaticGetCommandClassId)
    GetCommandClassName = property(lambda self: self.StaticGetCommandClassName)


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


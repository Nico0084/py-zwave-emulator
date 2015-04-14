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

class DoorLockCmd:
	Set					= 0x01
	Get					= 0x02
	Report				= 0x03
	Configuration_Set	= 0x04
	Configuration_Get	= 0x05
	Configuration_Report= 0x06

class TimeOutMode:
	NoTimeout		= 0x01
	Timeout			= 0x02

c_TimeOutModeNames = [
    "No Timeout", 
    "Secure Lock after Timeout"
    ]

class DoorLockControlState:
	Handle1			= 0x01
	Handle2			= 0x02
	Handle3			= 0x04
	Handle4			= 0x08

class ValueIDSystemIndexes:
	Lock							= 0x00		# Simple On/Off Mode for Lock 
	Lock_Mode						= 0x01		# To Set more Complex Lock Modes (Such as timeouts etc) 
	System_Config_Mode			= 0x02		# To Set/Unset if Locks should return to Secured Mode after a timeout 
	System_Config_Minutes			= 0x03		# If Timeouts are enabled, how many minutes before a Lock "AutoLocks" 
	System_Config_Seconds			= 0x04		# If Timeouts are enabled, how many seconds beofre a Lock "Autolocks" 
	System_Config_OutsideHandles 	= 0x05		# What Outside Handles are controlled via Z-Wave (BitMask 1-4) 
	System_Config_InsideHandles	= 0x06		# What inside Handles are control via ZWave (BitMask 1-4) 

class DoorLockState:
	Unsecured					= 0x00
	Unsecured_Timeout 		= 0x01
	Unsecured			= 0x10
	Inside_Unsecured_Timeout	= 0x11
	Outside_Unsecured			= 0x20
	Outside_Unsecured_Timeout = 0x21
	Secured					= 0xFF

c_LockStateNames = [
    "Unsecure", 
    "Unsecured with Timeout", 
    "Inside Handle Unsecured", 
    "Inside Handle Unsecured with Timeout", 
    "Outside Handle Unsecured", 
    "Outside Handle Unsecured with Timeout", 
    "Secured"
    ]

class DoorLock(CommandClass):
    
    StaticGetCommandClassId = 0x62
    StaticGetCommandClassName = "COMMAND_CLASS_DOOR_LOCK"
    
    def __init__(self, node,  data):
        CommandClass.__init__(self, node, data)
    
    GetCommandClassId = property(lambda self: self.StaticGetCommandClassId)
    GetCommandClassName = property(lambda self: self.StaticGetCommandClassName)



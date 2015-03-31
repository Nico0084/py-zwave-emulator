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



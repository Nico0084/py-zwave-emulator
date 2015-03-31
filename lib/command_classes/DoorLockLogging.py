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

class DoorLockLoggingCmd:
	RecordSupported_Get		= 0x01
	RecordSupported_Report	= 0x02
	Record_Get				= 0x03
	Record_Report			= 0x04

class DoorLockEventType:
	LockCode						= 0x01
	UnLockCode					= 0x02
	LockButton					= 0x03
	UnLockButton  				= 0x04
	LockCodeOOSchedule			= 0x05
	UnLockCodeOOSchedule			= 0x06
	IllegalCode					= 0x07
	LockManual					= 0x08
	UnLockManual					= 0x09
	LockAuto						= 0x0A
	UnLockAuto					= 0x0B
	LockRemoteCode				= 0x0C
	UnLockRemoteCode				= 0x0D
	LockRemote					= 0x0E
	UnLockRemote					= 0x0F
	LockRemoteCodeOOSchedule		= 0x10
	UnLockRemoteCodeOOSchedule	= 0x11
	RemoteIllegalCode				= 0x12
	LockManual2					= 0x13
	UnlockManual2					= 0x14
	LockSecured					= 0x15
	LockUnsecured					= 0x16
	UserCodeAdded					= 0x17
	UserCodeDeleted				= 0x18
	AllUserCodesDeleted			= 0x19
	MasterCodeChanged				= 0x1A
	UserCodeChanged				= 0x1B
	LockReset						= 0x1C
	ConfigurationChanged			= 0x1D
	LowBattery					= 0x1E
	NewBattery					= 0x1F
	Max							= 0x20

c_DoorLockEventType = [
    "Locked via Access Code",
    "Unlocked via Access Code",
    "Locked via Lock Button",
    "Unlocked via UnLock Botton",
    "Lock Attempt via Out of Schedule Access Code",
    "Unlock Attemp via Out of Schedule Access Code",
    "Illegal Access Code Entered",
    "Manually Locked",
    "Manually UnLocked",
    "Auto Locked",
    "Auto Unlocked",
    "Locked via Remote Out of Schedule Access Code",
    "Unlocked via Remote Out of Schedule Access Code",
    "Locked via Remote",
    "Unlocked via Remote",
    "Lock Attempt via Remote Out of Schedule Access Code",
    "Unlock Attempt via Remote Out of Schedule Access Code",
    "Illegal Remote Access Code",
    "Manually Locked (2)",
    "Manually Unlocked (2)",
    "Lock Secured",
    "Lock Unsecured",
    "User Code Added",
    "User Code Deleted",
    "All User Codes Deleted",
    "Master Code Changed",
    "User Code Changed",
    "Lock Reset",
    "Configuration Changed",
    "Low Battery",
    "New Battery Installed",
    "Unknown"
    ]

class ValueIDSystemIndexes:
	System_Config_MaxRecords		= 0x00	# Max Number of Records the Device can Hold 
	GetRecordNo					= 0x01	# Current Record Number after refresh 
	LogRecord						= 0x02		# Simple String Representation of the Log Record - Tab Delimited Fields 

class DoorLockLogging(CommandClass):
    
    StaticGetCommandClassId = 0x4c
    StaticGetCommandClassName = "COMMAND_CLASS_DOOR_LOCK_LOGGING"
    
    def __init__(self, node,  data):
        CommandClass.__init__(self, node, data)
    
    GetCommandClassId = property(lambda self: self.StaticGetCommandClassId)
    GetCommandClassName = property(lambda self: self.StaticGetCommandClassName)



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

class ThermostatSetpointCmd:
	Set				= 0x01
	Get				= 0x02
	Report			= 0x03
	SupportedGet		= 0x04
	SupportedReport	= 0x05

class ThermostatSetpoint:
    Unused0	= 0
    ThermostatSetpoint_Heating1 = 1
    ThermostatSetpoint_Cooling1	= 2
    ThermostatSetpoint_Unused3	= 3
    ThermostatSetpoint_Unused4	= 4
    ThermostatSetpoint_Unused5	= 5
    ThermostatSetpoint_Unused6	= 6
    ThermostatSetpoint_Furnace	= 7
    ThermostatSetpoint_DryAir = 8
    ThermostatSetpoint_MoistAir	= 9
    ThermostatSetpoint_AutoChangeover	= 10
    ThermostatSetpoint_HeatingEcon = 11
    ThermostatSetpoint_CoolingEcon = 12
    ThermostatSetpoint_AwayHeating = 13
    ThermostatSetpoint_Count = 14

c_setpointName = [
    "Unused 0",
    "Heating 1",
    "Cooling 1",
    "Unused 3",
    "Unused 4",
    "Unused 5",
    "Unused 6",
    "Furnace",
    "Dry Air",
    "Moist Air",
    "Auto Changeover",
    "Heating Econ",
    "Cooling Econ",
    "Away Heating"
]

class ThermostatSetpoint(CommandClass):
    
    StaticGetCommandClassId = 0x43
    StaticGetCommandClassName = "COMMAND_CLASS_THERMOSTAT_SETPOINT"
    
    def __init__(self, node,  data):
        CommandClass.__init__(self, node, data)
    
    GetCommandClassId = property(lambda self: self.StaticGetCommandClassId)
    GetCommandClassName = property(lambda self: self.StaticGetCommandClassName)


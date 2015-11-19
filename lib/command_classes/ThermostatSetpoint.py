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

class ThermostatSetpointCmd(EnumNamed):
	Set				= 0x01
	Get				= 0x02
	Report			= 0x03
	SupportedGet		= 0x04
	SupportedReport	= 0x05

class ThermostatSetpointIndex(EnumNamed):
    Unused0	= 0
    Heating1 = 1
    Cooling1 = 2
    Unused3	= 3
    Unused4	= 4
    Unused5	= 5
    Unused6	= 6
    Furnace	= 7
    DryAir = 8
    MoistAir = 9
    AutoChangeover= 10
    HeatingEcon = 11
    CoolingEcon = 12
    AwayHeating = 13
    Count = 14

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
        self.pointBase = 1 if 'base' not in data else int(data['base'])

    GetCommandClassId = property(lambda self: self.StaticGetCommandClassId)
    GetCommandClassName = property(lambda self: self.StaticGetCommandClassName)
    reportCmd = property(lambda self: ThermostatSetpointCmd.Report)
    getCmd = property(lambda self: ThermostatSetpointCmd.Get)

    def getFullNameCmd(self,  _id):
        return ThermostatSetpointCmd().getFullName(_id)

    def ProcessMsg(self, _data, instance=1):
        if _data[0] == ThermostatSetpointCmd.Get:
            setpointName = c_setpointName[_data[1] - self.pointBase]
            value = self._node.getValueByLabel(self.GetCommandClassId, instance, setpointName)
            print "Thermostat_Setpoint_Report ",  setpointName,  value
            for v in  self._node.getCmdClassValues(self.GetCommandClassId):
                print "     -- ",  v.label,  v.index
            msg = Msg("Thermostat_Setpoint_Report", self.nodeId, REQUEST, FUNC_ID_APPLICATION_COMMAND_HANDLER)
            if value is not None :
                msg.Append(TRANSMIT_COMPLETE_OK)
                msg.Append(self.nodeId)
                vData = self.EncodeValue(value._value, 1 if value.units == 'C' else 0)
                print "    -- encoding : ", value._value, value.units
                msg.Append(3 + len(vData))
                msg.Append(self.GetCommandClassId)
                msg.Append(ThermostatSetpointCmd.Report)
                msg.Append(value.index)
                for d in vData :
                    msg.Append(d)
                self.GetDriver.SendMsg(msg, MsgQueue.NoOp)
            else :
                msg.Append(TRANSMIT_COMPLETE_NOT_IDLE)
                msg.Append(self.nodeId)
                msg.Append(2)
                msg.Append(self.GetCommandClassId)
                msg.Append(ThermostatSetpointCmd.Report)
                self.GetDriver.SendMsg(msg, MsgQueue.NoOp)
                self._log.write(LogLevel.Error, self._node,"Thermostat_Setpoint_Report, value doesn't exist for label {0}.".format(setpointName))

        elif _data[0] == ThermostatSetpointCmd.SupportedGet:
            values = self._node.getCmdClassValues(self.GetCommandClassId)
            msg = Msg("Thermostat_Setpoint_SupportedReport", self.nodeId, REQUEST, FUNC_ID_APPLICATION_COMMAND_HANDLER)
            msg.Append(TRANSMIT_COMPLETE_OK)
            msg.Append(self.nodeId)
            vData = []
            for n in range(0, ThermostatSetpointIndex.Count) :
                for value in values :
                    if value.label == c_setpointName[n] :
                        id = (value.index - self.pointBase) / 8
                        if id >= len(vData) : vData.append(0)
                        vData[id] |= 1 << ((value.index - self.pointBase) - (id * 8))
            msg.Append(2 + len(vData))
            msg.Append(self.GetCommandClassId)
            msg.Append(ThermostatSetpointCmd.SupportedReport)
            for d in vData :
                msg.Append(d)
            self.GetDriver.SendMsg(msg, MsgQueue.NoOp)

        elif _data[0] == ThermostatSetpointCmd.Set:
#            _data[1] = index
            vIndex = _data[1] - self.pointBase
            value = self._node.getValue(self.GetCommandClassId, instance, vIndex)
            if value :
                val = self.ExtractValue(_data[2:], 1 if value.units == 'C' else 0, 0)
                value.setVal(val)
                self._log.write(LogLevel.Info, self._node,"Thermostat Setpoint {0} set to {1}".format(c_setpointName[vIndex], val))
            else :
                self._log.write(LogLevel.Warning, self._node,"Thermostat Setpoint Set unknown value {0} index {1}, value not set to {2}".format(c_setpointName[vIndex], vIndex, val))

        else:
            self._log.write(LogLevel.Warning, self, "CommandClass REQUEST {0}, Not implemented : {1}".format(self.getFullNameCmd(_data[0]), GetDataAsHex(_data)))


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

class SensorMultilevelCmd(EnumNamed):
	SupportedGet	= 0x01
	SupportedReport	= 0x02
	Get			= 0x04
	Report		= 0x05

class SensorType:
	Temperature = 1
	General = 2
	Luminance = 3
	Power = 4
	RelativeHumidity = 5
	Velocity = 6
	Direction = 7
	AtmosphericPressure = 8
	BarometricPressure = 9
	SolarRadiation = 10
	DewPoint = 11
	RainRate = 12
	TideLevel = 13
	Weight = 14
	Voltage = 15
	Current = 16
	CO2 = 17
	AirFlow = 18
	TankCapacity = 19
	Distance = 20
	AnglePosition = 21
	Rotation = 22
	WaterTemperature =23
	SoilTemperature = 24
	SeismicIntensity = 25
	SeismicMagnitude = 26
	Ultraviolet = 27
	ElectricalResistivity = 28
	ElectricalConductivity = 29
	Loudness = 30
	Moisture = 31
	MaxType = 32

c_sensorTypeNames =[
    "Undefined",
    "Temperature",
    "General",
    "Luminance",
    "Power",
    "Relative Humidity",
    "Velocity",
    "Direction",
    "Atmospheric Pressure",
    "Barometric Pressure",
    "Solar Radiation",
    "Dew Point",
    "Rain Rate",
    "Tide Level",
    "Weight",
    "Voltage",
    "Current",
    "CO2 Level",
    "Air Flow",
    "Tank Capacity",
    "Distance",
    "Angle Position",
    "Rotation",
    "Water Temperature",
    "Soil Temperature",
    "Seismic Intensity",
    "Seismic Magnitude",
    "Utraviolet",
    "Electrical Resistivity",
    "Electrical Conductivity",
    "Loudness",
    "Moisture"
    ]

c_tankCapcityUnits = [
    "l",
    "cbm",
    "gal"
    ]

c_distanceUnits = [
    "m",
    "cm",
    "ft"
    ]

c_anglePositionUnits = [
    "%",
    "deg N",
    "deg S"
    ]

c_seismicIntensityUnits = [
    "mercalli",
    "EU macroseismic",
    "liedu",
    "shindo"
    ]

c_seismicMagnitudeUnits = [
    "local",
    "moment",
    "surface wave",
    "body wave"
    ]

c_moistureUnits = [
    "%",
    "content",
    "k ohms",
    "water activity"
    ]

class SensorMultilevel(CommandClass):

    StaticGetCommandClassId = 0x31
    StaticGetCommandClassName = "COMMAND_CLASS_SENSOR_MULTILEVEL"

    def __init__(self, node,  data):
        CommandClass.__init__(self, node, data)

    GetCommandClassId = property(lambda self: self.StaticGetCommandClassId)
    GetCommandClassName = property(lambda self: self.StaticGetCommandClassName)

    def getFullNameCmd(self,  _id):
        return SensorMultilevelCmd().getFullName(_id)

    def getByteIndex(self, instance):
        # in openzwave type is index value
        for index in range(1,  SensorType.MaxType):
            val = self._node.getValue(self.GetCommandClassId,  instance, index)
            if val is not None : return index
        return 0

    def getDataMsg(self, _data, instance=1):
        msgData = []
        if _data :
            if _data[0] == SensorMultilevelCmd.SupportedGet:
                pass
            elif _data[0] == SensorMultilevelCmd.Get:
                value = self._node.getValue(self.GetCommandClassId, instance, self.getByteIndex(instance))
                if value is not None :
                    print "++++ Sensor multilevel value : ", value._value
                    msgData.append(self.GetCommandClassId)
                    msgData.append(SensorMultilevelCmd.Report)
                    msgData.append(self.getByteIndex(instance))
                    msgData.extend(self.EncodeValue(value._value, 0))
        else :
            self._log.write(LogLevel.Warning, self, "REQUEST SensorMultilevelCmd getDataMsg, No data in buffer")
        return msgData

    def ProcessMsg(self, _data, instance=1, multiInstanceData = []):
        if _data[0] == SensorMultilevelCmd.SupportedGet:
#            group = self.getGroup(_data[1])
#            if group is not None :
#                msg = Msg("SensorMultilevelCmd_Supported_Report", self.nodeId,  REQUEST, FUNC_ID_APPLICATION_COMMAND_HANDLER,)
#                msg.Append(TRANSMIT_COMPLETE_OK)
#                msg.Append(self.nodeId)
#                msg.Append(len(group['nodes']) + 5)
#                msg.Append(self.GetCommandClassId)
#                msg.Append(SensorMultilevelCmd.SupportedReport)
#
#                self.GetDriver.SendMsg(msg, MsgQueue.NoOp)
            self._log.write(LogLevel.Warning, self, "REQUEST SensorMultilevelCmd.SupportedGet Not implemented : {0}".format(GetDataAsHex(_data)))
        elif _data[0] == SensorMultilevelCmd.Get:
            value = self._node.getValue(self.GetCommandClassId, instance, self.getByteIndex(instance))
            if value is not None :
                msg = Msg("SensorMultilevelCmd_Report", self.nodeId,  REQUEST, FUNC_ID_APPLICATION_COMMAND_HANDLER)
                msgData = self.getDataMsg(_data, instance)
                if multiInstanceData :
                    multiInstanceData[2] += len(msgData)
                    for v in multiInstanceData : msg.Append(v)
                else :
                    msg.Append(TRANSMIT_COMPLETE_OK)
                    msg.Append(self.nodeId)
                    msg.Append(len(msgData))
                for v in msgData : msg.Append(v)
                self.GetDriver.SendMsg(msg, MsgQueue.NoOp)

        else:
            self._log.write(LogLevel.Warning, self, "CommandClass REQUEST {0}, Not implemented : {1}".format(self.getFullNameCmd(_data[0]), GetDataAsHex(_data)))

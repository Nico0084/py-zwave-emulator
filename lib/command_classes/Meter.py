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
import time

class MeterCmd(EnumNamed):
	Get				= 0x01
	Report			= 0x02
	# Version 2
	SupportedGet		= 0x03
	SupportedReport	= 0x04
	Reset			    	= 0x05


class MeterType:
    Electric = 1
    Gas = 2
    Water = 3

class MeterIndex:
	Exporting = 32
	Reset =33

c_meterTypes = [
    "Unknown"
    "Electric"
    "Gas"
    "Water"
    ]

c_electricityUnits = [
    "kWh",
    "kVAh",
    "W",
    "pulses",
    "V",
    "A",
    "Power Factor",
    ""
]

c_gasUnits = [
    "cubic meters",
    "cubic feet",
    "",
    "pulses",
    "",
    "",
    "",
    ""
]

c_waterUnits = [
    "cubic meters",
    "cubic feet",
    "US gallons",
    "pulses",
    "",
    "",
    "",
    ""
]

c_electricityLabels = [
    "Energy",
    "Energy",
    "Power",
    "Count",
    "Voltage",
    "Current",
    "Power Factor",
    "Unknown"
    ]

class Meter(CommandClass):
    
    StaticGetCommandClassId = 0x32
    StaticGetCommandClassName = "COMMAND_CLASS_METER"
    reportCmd = property(lambda self: MeterCmd.Report)
    getCmd = property(lambda self: MeterCmd.Get)
    
    GetCommandClassId = property(lambda self: self.StaticGetCommandClassId)
    GetCommandClassName = property(lambda self: self.StaticGetCommandClassName)

    def __init__(self, node,  data):
        CommandClass.__init__(self, node, data)
        self.meterType = {}
        self._lastTime = time.time()
        
    def getFullNameCmd(self,  _id):
        return MeterCmd().getFullName(_id)

    def setMeterType(self):
        self.meterType = {}
        for i in self.instances:
            instance = i['index']
            find = False
            self.meterType.update({instance: 0})
            for i in range(0, 128):
                val = self._node.getValue(self.GetCommandClassId,  instance, i)
                if val is not None :
                    t = 0
                    for label in c_meterTypes:
                        if val.label == label : 
                            self.meterType[instance] = t
                            find = True
                            break
                        else : t += 1
                    if not find :
                        for label in c_electricityLabels:
                            if val.label == label : 
                                self.meterType[instance] = MeterType.Electric
                                find = True
                                break
                    if not find :
                        for units in c_electricityUnits:
                            if val.units == units : 
                                self.meterType[instance] = MeterType.Electric
                                find = True
                                break
                    if not find :
                        for units in c_gasUnits:
                            if val.units == units : 
                                self.meterType[instance] = MeterType.Gas
                                find = True
                                break
                    if not find :
                        for units in c_waterUnits:
                            if val.units == units : 
                                self.meterType[instance] = MeterType.Water
                                find = True
                                break 
                    if find: break
    
    def getByteType(self, instance, flagReset = False):
        if not self.meterType : self.setMeterType()
        b = 0x00
        if flagReset :
            valReset = self._node.getValue(self.GetCommandClassId,  instance, MeterIndex.Reset)
            if valReset is not None : b = 0x80
        b = b | self.meterType[instance]
        return b
    
    def getScale(self, value):
        if not self.meterType : self.setMeterType()
        if self.meterType[value.instance] == MeterType.Electric:
            i = 0
            for units in c_electricityUnits:
                if value.units == units : return i
                i += 1
        elif self.meterType[value.instance] == MeterType.Gas:
            i = 0
            for units in c_gasUnits:
                if value.units == units : return i
                i += 1
        elif self.meterType[value.instance] == MeterType.Water:
            i = 0
            for units in c_waterUnits:
                if value.units == units : return i
                i += 1
        return None
        
    def getVallueAtFirst(self, instance):
        for index in range(0, 255):
            value = self._node.getValue(self.GetCommandClassId, instance, index)
            if value is not None: return value
        self._log.write(LogLevel.Warning, self, "Meter class, no value for instance: {0}".format(instance))
    
    def getDataMsg(self, _data, instance=1, multiInstanceData = []):
        msgData = []
        if _data[0] == MeterCmd.Get:
            baseIndex = (_data[1]>>3) << 2 # To get openzwave index process
            print 'getDataMsg {0}, baseIndex : {1}'.format(_data,  baseIndex)
            value = self._node.getValue(self.GetCommandClassId, instance, baseIndex)
            vData = self.EncodeValue(value._value, self.getScale(value))
            if self.m_version > 1:
                vPrev = self._node.getValue(self.GetCommandClassId, instance, baseIndex+1)
                if vPrev is not None :
                    vData.extend(self.EncodeValue(vPrev._value, self.getScale(vPrev))[1:])
                    self._log.write(LogLevel.Debug, self, "MeterCmd.Get, version {0}, 'Previous reading' added in data ({1}).".format(self.m_version, value.label))
                else :
                    self._log.write(LogLevel.Debug, self, "MeterCmd.Get, version {0}, No value 'Previous reading' for value index {1} ({2}).".format(self.m_version, baseIndex, value.label))
                vInterval = self._node.getValue(self.GetCommandClassId, instance, baseIndex+2)
                if vInterval is not None :
                    vData.extend([vInterval.getValueByte() >> 8,  vInterval.getValueByte() & 0x00ff])
                    self._log.write(LogLevel.Debug, self, "MeterCmd.Get, version {0}, 'Interval' added in data ({1}).".format(self.m_version, value.label))
                else :
                    vData.extend([0x00, 0x00])
                    self._log.write(LogLevel.Debug, self, "MeterCmd.Get, version {0}, No value 'Interval' for value index {1} ({2}).".format(self.m_version, baseIndex, value.label))
            msgData.append(self.GetCommandClassId)
            msgData.append(MeterCmd.Report)
            valueExport = self._node.getValue(self.GetCommandClassId, instance, MeterIndex.Exporting)
            if valueExport is not None and valueExport.getVal() : flag = 0x40
            else: flag = 0x20
            msgData.append(flag | self.getByteType(instance))
            msgData.extend(vData)
        return msgData
    
    def pollValue(self, poll):
        instance = poll['instance']
        value = self._node.getValueByLabel(self.GetCommandClassId, instance, poll['label'])
        prevVal = 0 
        if value : 
            prevVal = value._value
            value.setVal(value.getValueToPoll(poll['params']))
            if value.index == 0 : # Corresponding to openzwave lib, main value so vprev and vinterval are sended
                vPrev = self._node.getValue(self.GetCommandClassId, instance, value.index+1)
                if vPrev and prevVal :
                    vPrev.setVal(prevVal)
                vInterval = self._node.getValue(self.GetCommandClassId, instance, value.index+2)
                if vInterval :
                    vInterval.setVal(time.time() - self._lastTime)
                    self._lastTime = time.time()
            self.HandleReportChange("MeterCmd_Report", self, [MeterCmd.Get, value.index << 1], instance, MsgQueue.Poll)
            return True
        self._log.write(LogLevel.Warning, self, "Error in Config emulation JSON file. instance {0} don't exist.".format(instance))
        return False

    def ProcessMsg(self, _data, instance=1, multiInstanceData = []):
        print '++++++++++++++++ Meter ProcessMsg +++++++++++++++'
        if not self.meterType : self.setMeterType()
        print 'DATA : ',  GetDataAsHex(_data),  " -- instance : ",  instance
        # Version 1 
        if _data[0] == MeterCmd.Get: 
            msg = Msg("MeterCmd_Report", self.nodeId,  REQUEST, FUNC_ID_APPLICATION_COMMAND_HANDLER)
            msgData = self.getDataMsg(_data,  instance)
            if multiInstanceData :
                multiInstanceData[2] += len(msgData)
                for v in multiInstanceData : msg.Append(v)
            else :
                msg.Append(TRANSMIT_COMPLETE_OK)
                msg.Append(self.nodeId)
                msg.Append(len(msgData))
            for v in msgData : msg.Append(v)
            self.GetDriver.SendMsg(msg, MsgQueue.NoOp)
        # Version 2
        elif _data[0] == MeterCmd.SupportedGet:
            msg = Msg("MeterCmd_Supported_Report", self.nodeId,  REQUEST, FUNC_ID_APPLICATION_COMMAND_HANDLER)
            if multiInstanceData :
                multiInstanceData[2] += 4
                for v in multiInstanceData : msg.Append(v)
            else :
                msg.Append(TRANSMIT_COMPLETE_OK)
                msg.Append(self.nodeId)
                msg.Append(0x04)
            msg.Append(self.GetCommandClassId)
            msg.Append(MeterCmd.SupportedReport)
            msg.Append(self.getByteType(instance, True))
            if self.m_version > 1 : msg.Append(0x05)
            else : msg.Append(0x00)
            self.GetDriver.SendMsg(msg, MsgQueue.NoOp)
            
        else:
            self._log.write(LogLevel.Warning, self, "CommandClass REQUEST {0}, Not implemented : {1}".format(self.getFullNameCmd(_data[0]), GetDataAsHex(_data)))

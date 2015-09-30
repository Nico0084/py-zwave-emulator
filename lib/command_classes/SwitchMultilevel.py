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
from commandclass import CommandClass, CommandClassException
import threading
        
class SwitchMultilevelCmd(EnumNamed):
	Set						= 0x01
	Get						= 0x02
	Report					= 0x0
	StartLevelChange				= 0x04
	StopLevelChange				= 0x05
	SupportedGet				= 0x06
	SupportedReport				= 0x07

class	SwitchMultilevelIndex(EnumNamed):
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
    
c_switchLabel = []
for i in range (0, len(c_switchLabelsPos)) : c_switchLabel.append("{0}/{1}".format(c_switchLabelsPos[i], c_switchLabelsNeg[i]))
    
class SwitchMultilevel(CommandClass):
    
    StaticGetCommandClassId = 0x26
    StaticGetCommandClassName = "COMMAND_CLASS_SWITCH_MULTILEVEL"
    
    def __init__(self, node,  data):
        CommandClass.__init__(self, node, data)
        self.runChange = False
        self.extraParams = {0: {'switchtype1' : {'name': 'Switch type 1', 'values': c_switchLabel}, 
                                         'switchtype2' : {'name': 'Switch type 2', 'values': c_switchLabel}}, 
                                   1 : {'switchtype1' : 1, 'switchtype2' : 2}}  # set instance 1 for debug and defaults value
    
    GetCommandClassId = property(lambda self: self.StaticGetCommandClassId)
    GetCommandClassName = property(lambda self: self.StaticGetCommandClassName)
    reportCmd = property(lambda self: SwitchMultilevelCmd.Report)
    getCmd = property(lambda self: SwitchMultilevelCmd.Get)

    def getFullNameCmd(self,  _id):
        return SwitchMultilevelCmd().getFullName(_id)

    def getByteIndex(self, instance):
        """Must return a specific byte to get type (as index of value)"""
        #  index is allways 0
        return SwitchMultilevelIndex.Level

    def getDataMsg(self, _data, instance=1):
        msgData = []
        if _data :
            if _data[0] == SwitchMultilevelCmd.SupportedGet:
                pass
            elif _data[0] in [SwitchMultilevelCmd.Get, SwitchMultilevelCmd.Report]:
                value = self._node.getValue(self.GetCommandClassId, instance, self.getByteIndex(instance))
                if value is not None :
                    msgData.append(self.GetCommandClassId)
                    msgData.append(SwitchMultilevelCmd.Report)
                    msgData.append(value.getValueByte())
        else :
            self._log.write(LogLevel.Warning, self, "REQUEST SwitchMultilevelCmd getDataMsg, No data in buffer")
        return msgData       

    def ProcessMsg(self, _data, instance=1, multiInstanceData = []):
        if _data[0] == SwitchMultilevelCmd.Get:
            value = self._node.getValue(self.GetCommandClassId, instance, self.getByteIndex(instance))
            if value is not None :
                msg = Msg("SwitchMultilevelCmd_Report", self.nodeId,  REQUEST, FUNC_ID_APPLICATION_COMMAND_HANDLER)
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
        elif _data[0] == SwitchMultilevelCmd.SupportedGet:
            msg = Msg("SwitchMultilevelCmd_SupportedReport", self.nodeId,  REQUEST, FUNC_ID_APPLICATION_COMMAND_HANDLER)
            msg.Append(TRANSMIT_COMPLETE_OK)
            msg.Append(self.nodeId)
            switchtype1label = 0
            try :
                switchtype1label = self.extraParams[instance]['switchtype1']
            except :
                raise CommandClassException("Get switchtype1label Fail, Index not found for label : {0}.".format(self.extraParams[instance]), self)
            switchtype2label = 0
            try :
                switchtype2label = self.extraParams[instance]['switchtype2']
            except :
                raise CommandClassException("Get switchtype2label Fail, Index not found for label : {0}.".format(self.extraParams[instance]), self)
            msg.Append(4)
            msg.Append(self.GetCommandClassId)
            msg.Append(SwitchMultilevelCmd.SupportedReport)
            msg.Append(switchtype1label & 0x1f)
            msg.Append(switchtype2label & 0x1f)
            self.GetDriver.SendMsg(msg, MsgQueue.NoOp)    
        elif _data[0] == SwitchMultilevelCmd.StartLevelChange:
            direction = _data[1] & 0xdF
            startLevel = _data[2]
            ignoreStartLevel = True if (_data[1] & 0x20) else False
            self._log.write(LogLevel.Debug, self, "CommandClass REQUEST {0}, direction : {1}, startLevel : {2}, ignoreStartLevel : {3}".format(self.getFullNameCmd(_data[0]), direction, startLevel, ignoreStartLevel))
            value = self._node.getValue(self.GetCommandClassId, instance, SwitchMultilevelIndex.IgnoreStartLevel)
            if value is not None : value.setVal(ignoreStartLevel)
            value = self._node.getValue(self.GetCommandClassId, instance, SwitchMultilevelIndex.StartLevel)
            if value is not None : value.setVal(startLevel)
            if self.m_version >= 2 :
                value = self._node.getValue(self.GetCommandClassId, instance, SwitchMultilevelIndex.Duration)
                if value is not None : value.setVal(_data[3])
                if self.m_version >= 3 :
                    value = self._node.getValue(self.GetCommandClassId, instance, SwitchMultilevelIndex.Step)
                    if value is not None : value.setVal(_data[4])
            threading.Thread(None, self._handleChangeLevel, "th_Handle_ChangeLevel_class_0x%0.2x."%self.GetCommandClassId, (direction), {'instance': instance}).start()
        elif _data[0] == SwitchMultilevelCmd.StopLevelChange:
            self.runChange = False
        elif _data[0] == SwitchMultilevelCmd.Get:
            value = self._node.getValue(self.GetCommandClassId, instance, self.getByteIndex(instance))
            if value is not None : value.setVal(_data[1])
        else:
            self._log.write(LogLevel.Warning, self, "CommandClass REQUEST {0}, Not implemented : {1}".format(self.getFullNameCmd(_data[0]), GetDataAsHex(_data)))

    def _handleChangeLevel(self, *direction, **params):
        instance = params['instance']
        try :
            dir = c_directionParams.index(direction)
        except : 
            raise CommandClassException("Start change level code direction unknwon : {0}".format(GetDataAsHex(direction)), self)
            return False
        self._log.write(LogLevel.Debug, self, '{0} : Starting Change Level Node {1} in direction : {2}'.format(self.GetCommandClassName, self.nodeRef,  c_directionDebugLabels[dir]))
        if 'wait' in params: waitTime += params['wait']
        vLevel = self._node.getValue(self.GetCommandClassId, instance, self.getByteIndex(instance))
        if self._node.getValue(self.GetCommandClassId, instance, SwitchMultilevelIndex.IgnoreStartLevel).getVal() : startLevel = vLevel.getVal()
        else : startLevel = self._node.getValue(self.GetCommandClassId, instance, SwitchMultilevelIndex.StartLevel).getVal()
        if dir in [0, 2] :  #" Up" or  "Inc"
            deltaLevel = vLevel._max - startLevel   
            dir = 1
        else : # "Down" or  "Dec"   
            deltaLevel = startLevel - vLevel._min
            dir = -1
        if self.m_version >= 2 : duration = self._node.getValue(self.GetCommandClassId, instance, SwitchMultilevelIndex.Duration).getVal() * 1.0
        else : duration = 0.0
        if self.m_version >= 3 : 
            step = self._node.getValue(self.GetCommandClassId, instance, SwitchMultilevelIndex.Step).getVal()
            waitStep = duration
        else : 
            step = 1 
            waitStep = duration / (deltaLevel / step)
        waitTime = time.time() + (duration * (waitStep * step))
        self.runChange = True
        level = startLevel
        while time.time() < waitTime and not self._stop.isSet() and self.runChange :
            level += dir * step
            vLevel.setVal(level)
            if level == endLevel : self.runChange = False
            else : 
                if step > 1 : self.HandleReportChange("SwitchMultilevelCmd_Report", self, [self.reportCmd,  vLevel.index], vLevel.instance)
                self._stop.wait(waitStep)
        self.HandleReportChange("SwitchMultilevelCmd_Report", self, [self.reportCmd,  vLevel.index], vLevel.instance)
        self._log.write(LogLevel.Debug, self, '{0} : End Change Level Node {1}'.format(self.GetCommandClassName, self.nodeRef))


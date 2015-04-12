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
import time
import locale

c_sizeMask		    = 0x07
c_scaleMask		= 0x18
c_scaleShift		= 0x03
c_precisionMask	= 0xe0
c_precisionShift	= 0x05

class CommandClass:
    """Base of commandClass, group all methodes of spécific command class to emulate behavior."""
    
    RequestFlag_Static		= 0x00000001  	# Values that never change. 
    RequestFlag_Session		= 0x00000002	   # Values that change infrequently, and so only need to be requested at start up, or via a manual refresh. 
    RequestFlag_Dynamic		= 0x00000004	   # Values that change and will be requested if polling is enabled on the node. 
    
    StaticRequest_Instances	= 0x01
    StaticRequest_Values		= 0x02
    StaticRequest_Version		= 0x04
        
    def __init__(self, node,  data):
        
        self._node = node
        self.id = data['id']
        self.name = data['name'] if 'name' in data else COMMAND_CLASS_DESC[self.id]
        self.m_version = data['version'] if 'version' in data else 1
        self.m_afterMark = data['after_mark'] if 'after_mark' in data else False
        self.m_createVars = data['create_vars'] if 'create_vars' in data else True
        self.m_overridePrecision = data['override_precision'] if 'override_precision' in data else -1
        self.m_getSupported = data['getsupported'] if 'getsupported' in data else True
        self.m_isSecured = False
        self.m_SecureSupport = True
        self.m_staticRequests = data['request_flags'] if 'request_flags' in data else 0
        self.m_sentCnt = 0
        self.m_receivedCnt =0
        self.instances = data['instances'] if 'instances' in data else [1]
        self.mandatory = False
        self.mapping = data['mapping'] if 'mapping' in data else 0
        self.ignoremapping = data['ignoremapping'] if 'ignoremapping' in data else False
        self.mandatory = False
        self.ozwAdded = False # Added by openzwave for internal use
        
    _log = property(lambda self: self._node._log)
    _stop = property(lambda self: self._node._manager._stop)
    homeId = property(lambda self: self._node.homeId)
    nodeId = property(lambda self: self._node.nodeId)
    GetDriver = property(lambda self: self._node._manager.GetDriver(self.homeId))
    reportCmd = property(lambda self: 0)
    getCmd = property(lambda self: 0)

    GetCommandClassId = property(lambda self: 0)
    GetCommandClassName = property(lambda self: "CMD_CLSS_NOT_DECLARED")
    IsSecured = property(lambda self: self.m_isSecured)
        
    def getFullNameCmd(self,  _id):
        return "BaseCommandClass.NoCmd"
    
    def HasStaticRequest(self, _request):
        return True if (self.m_staticRequests & _request) != 0 else False
        
    def SetStaticRequest(self, _request):
        self.m_staticRequests |= _request
    
    def ClearStaticRequest(self, _request):
        self.m_staticRequests &= ~_request
        
    def RequestState(self, _requestFlags, _instance, _queue):
        if (_requestFlags & self.RequestFlag_Static) and self.HasStaticRequest(self.StaticRequest_Values) :
            return RequestValue( _requestFlags, 0, _instance, _queue );
        return False
    
    def getByteType(self, instance):
        """Must return a specific byte to get type"""
        self._log.write(LogLevel.Warning, self, "Base commandClass object, getByteType not implemented.")
        return 0
    
    def getByteIndex(self, instance):
        self._log.write(LogLevel.Warning, self, "Base commandClass object, getByteIndex not implemented.")
        return 0
        
    def HandleMsg(self, *_data, **params):
        waitTime = time.time()
        print '    - Wait for {0} HandleMsg : {1}, {2}'.format(self.GetCommandClassName, GetDataAsHex(_data),  params)
        if 'wait' in params: waitTime += params['wait']
        while time.time() < waitTime and not self._stop.isSet():
            self._stop.wait(0.01)
        if not self._node.IsListeningDevice:
            wakeUp = self._node.GetCommandClass(self._node._manager.GetCommandClassId('COMMAND_CLASS_WAKE_UP'))
            if wakeUp is not None and wakeUp.IsAwake : 
                wakeUp.ResetLastTime()
            else : return
        self.ProcessMsg(_data)
        print"############################################################################################"
            
    def ProcessMsg(self, _data,  instance=1, multiInstanceData = []):
        self._log.write(LogLevel.Warning, self, "Base commandClass object, no processing message : {0}".format(GetDataAsHex(_data)))
        
    def HandleReportChange(self, msgText, cmdClss, params, instance):
        self._log.write(LogLevel.Debug, self,  "HandleReportChange, {0} - {1} - instance {2}.".format(msgText,  cmdClss.GetCommandClassName, instance))
        msg = Msg(msgText, self.nodeId,  REQUEST, FUNC_ID_APPLICATION_COMMAND_HANDLER, False)
        msgData = cmdClss.getDataMsg(params, instance)
        self._log.write(LogLevel.Debug, self,  "Data Value: {0}".format(GetDataAsHex(msgData)))
        if msgData :
            msg.Append(TRANSMIT_COMPLETE_OK)
            msg.Append(self.nodeId)
            if instance > 1: # Multi instance class level
                endPoint = self._node.getEndpointFromInstance(cmdClss.GetCommandClassId,  instance)
                self._log.write(LogLevel.Debug, self,  "Multi-instance endPoint : {0}".format(endPoint))
                msg.Append(4 + len(msgData))
                multInstclss = self._node.GetCommandClass(0x60)
                msg.Append(multInstclss.GetCommandClassId)
                msg.Append(multInstclss.getCmd)
                msg.Append(endPoint)
                msg.Append(0x00) # TODO: don't known signification
            else :
                msg.Append(len(msgData))
            for v in msgData : msg.Append(v)
            self.GetDriver.SendMsg(msg, MsgQueue.NoOp)    
        else :
            self._log.write(LogLevel.Error, self, "No Data find to report it, {0} - {1} - instance {2}.".format(msgText,  cmdClss.GetCommandClassName, instance))
        
    def getDataMsg(self, _data, instance=1):
        """Base commandClass object, no data message for base class"""
        # TODO: Implement each cmdClass by overwriting method
        self._log.write(LogLevel.Warning, self, "Base commandClass object, {0} not implemented for now.".format(self.GetCommandClassName))
        return []
        
    def pollValue(self, poll):
        value = self._node.getValueByLabel(self.GetCommandClassId, poll['instance'], poll['label'])
        if value : 
            self._log.write(LogLevel.Info, self, "Base commandClass object, polling {0} - {1}, instance {2}, value {3}.".format(self.GetCommandClassName, value.label,  poll['instance'], value.getVal()))
            value.setVal(value.getValueToPoll(poll['params']))
            self.HandleReportChange("BaseCmd_Report", self, [self.getCmd,  value.index], value.instance)
        else : self._log.write(LogLevel.Warning, self, "Base commandClass object, Value not find, can't poll")
        return False

    def ExtractValue(self, _data,  _scale,  _precision, _valueOffset = 1):
        size = _data[0] & c_sizeMask
        precision = (_data[0] & c_precisionMask) >> c_precisionShift
        neg = False
        if _data[_valueOffset] & 0x80:
            _data[_valueOffset] &= 0x7f
            neg = True
        value = 0
        for i in range (0, size):
            value = value << 8
            value |= _data[i +_valueOffset]    
        if neg : value = - value
        if precision == 0:
            # The precision is zero, so we can just print the number directly into the string.
            res = "%d"% int(value)
        else :
            point = locale.localeconv()['decimal_point']
            res = "%d"% int(value)
            insert = len(res) - precision
            res = res[0:insert] + point+ res[insert:]
        return res
        
    def EncodeValue(self,  value,  scale):
        size = 0
        precision = 0
        point = locale.localeconv()['decimal_point']
        vType = type(value)
        if vType == float : value = str(value)
        elif vType == int : value = "%d"%value
        elif vType == long : value = "%d"%value
        if type(value) == str or type(value) == unicode:
            try :
                precision = len(value) - (value.index(point) +1)
            except :
                precision = 0
            try:
                value = int(value)
            except :
                try: 
                    value = long(value)
                    size = 8
                except :
                    value = float(value)
                    size = 4
        mask = 0x80 if value < 0 else 0x00
        valAbs = abs(value)
        if type(valAbs) == int:
            if valAbs <= 0x7f: size = 1
            elif valAbs <= 0x7fff: size = 2
            elif valAbs <= 0x7fffffff: size = 4
            else: size = 8
        data = []
        data.append(size & c_sizeMask)
        data[0] |= (precision  << c_precisionShift) & c_precisionMask
        data[0] |= (scale << c_scaleShift) & c_scaleMask
        if precision :
            strValue = "%.{0}f".format(precision)%valAbs
            strValue = strValue[0:-precision-1] + strValue[-precision:]
        else : strValue = str(valAbs)
        if vType == long : value = long(strValue)
        else : value = int(strValue)
        for i in range (0,  size):
            data.insert(1,  (value >> 8 * i) & 0xff)
        data[1] |= mask
        return data   
    

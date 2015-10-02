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

#from libc.stdint import uint32_t, uint64_t, int32_t, int16_t, uint8_t, int8_t
#from mylibc import string
#from libcpp.vector import vector

#def extern from "Node.h" namespace "OpenZWave::Node":
from zwemulator.lib.defs import *
from zwemulator.lib.values import *
from zwemulator.lib.log import LogLevel
from zwemulator.lib.driver import MsgQueue, Msg
from zwemulator.lib.command_classes.commandclass import CommandClass
import threading
import time
from collections import OrderedDict

class SecurityFlag(EnumNamed):
    Security = 0x01
    Controller = 0x02
    SpecificDevice = 0x04
    RoutingSlave = 0x08
    BeamCapability = 0x10
    Sensor250ms = 0x20
    Sensor1000ms = 0x40
    OptionalFunctionality = 0x80

class CommandClassData:
    m_commandClassId = 0   # Num type of CommandClass id.
    m_sentCnt = 0              # Number of messages sent from this CommandClass.
    m_receivedCnt  =0        # Number of messages received from this CommandClass.

class NodeData:
    m_sentCnt = 0                            # Number of messages sent from this node.
    m_sentFailed = 0                         # Number of sent messages failed
    m_retries = 0                              # Number of message retries
    m_receivedCnt = 0                      # Number of messages received from this node.
    m_receivedDups = 0                     # Number of duplicated messages received;
    m_receivedUnsolicited = 0             # Number of messages received unsolicited
    m_sentTS = ""                             # Last message sent time
    m_receivedTS = ""                        # Last message received time
    m_lastRequestRTT = 0                 # Last message request RTT
    m_averageRequestRTT = 0            # Average Request Round Trip Time (ms).
    m_lastResponseRTT = 0                # Last message response RTT
    m_averageResponseRTT = 0          #Average Reponse round trip time.
    m_quality = 0                             # Node quality measure
    m_lastReceivedMessage = []        # Place to hold last received message
    m_ccData = []                           # List of statistic on each command_class (Stock struc class CommandClassData)

class Node:

    def __init__(self, manager, homeId, nodeId, data = None):
        self._manager = manager
        self.homeId = homeId
        self.nodeId = nodeId
        self._xmlData = data
        self.m_queryPending = False
        self.m_queryConfiguration = False
        self.m_queryRetries = 0
        self.m_protocolInfoReceived = False
        self.m_nodeInfoSupported = False
        self.m_manufacturerSpecificClassReceived = False
        self.m_nodeAlive = True	# assome live node
        self.m_addingNode = False
        self._nodeData = NodeData()
        self._values = []
        self._cmdsClass = []
        self.product = {}
        self.manufacturer = {}
        self.name = ""
        self.location = ""
        self.basic = 0
        self.generic = 0
        self.specific = 0
        self.typeNode = ""
        self.listening = False
        self.frequentListening = False
        self.beaming = False
        self.routing = False
        self.max_baud_rate = 0
        self.version = ""
        self.security = False
        self.registeredClassId = 0
        self.registeredCallbackId = 0
        self.query_stage = ""
        self._mapping = None
        self._mandatoryClasses = []
        self.neighbors = self._manager.getFakeNeighbors(self.homeId, self.nodeId) # FAKENEIGHBORS[self.nodeId]
        self.emulData = self._manager.getEmulNodeData(self.homeId, self.nodeId)
        self._runningPoll = False
        
        self.numEndPoints = 0
        self.numEndPointsCanChange = False
        self.endPointsAreSameClass = False
        self.mapEndPoints = OrderedDict()
        self.failNodeInfo = 0
        
        self.currentCommand = 0
        self.currentCommandState = 0

        # Add COMMAND_CLASS_NO_OPERATION
        self.addCmdClss({'id': int('0x00', 16),  'name' : 'COMMAND_CLASS_NO_OPERATION','instances': [1], 'request_flags': u'2', 'version': '0x0', 'after_mark': False}, True)
        if data : self.setData(data)
        self.startPoll()
#        print self._cmdsClass

    _log = property(lambda self: self._manager._log)
    _stop = property(lambda self: self._manager._stop)
    nodeRef = property(lambda self: "{0}.{1}".format(GetDataAsHex(self.homeId, 8), self.nodeId))
    commandClassId  = property(lambda self: 0x00) # 'COMMAND_CLASS_NO_OPERATION' 
    instance = property(lambda self: 0)
    index = property(lambda self: 0)
    genre = property(lambda self: 0)
    type = property(lambda self: 0)
    label = property(lambda self: "")
    units = property(lambda self: "")
    readOnly = property(lambda self: False)  #manager.IsValueReadOnly(v)
    GetXmlData = property(lambda self: self._xmlData)
    GetDriver = property(lambda self: self._manager.GetDriver(self.homeId))
    GetManufacturerId = property(lambda self: GetDataAsHex([self.manufacturer['id']], 4) if 'id' in self.manufacturer else "0x0000")
    GetProductType = property(lambda self: GetDataAsHex([self.product['type']] , 4) if'type' in self.product else "0x0000")
    GetProductId = property(lambda self: GetDataAsHex([self.product['id']], 4) if 'id' in self.product else "0x0000")
    
    GetManufacturerName = property(lambda self: self.manufacturer['name'] if 'name' in self.manufacturer else "")
    GetProductName = property(lambda self: self.product['name'] if 'name' in self.product else "")

    IsListeningDevice = property(lambda self: self.listening)
    IsAddingNode = property(lambda self: self.m_addingNode)
    IsInclude = property(lambda self: True if self.homeId != 0 else False)
    IsFailed = property(lambda self: self.emulData['failed'])
    
    def IsController(self):
        return (self.basic == 0x01 or self.basic == 0x02 ) and ( self.generic == 0x01 or self.generic == 0x02 )

    def GetClassInformation(self):
        return {'name': 'COMMAND_CLASS_NO_OPERATION',  'id': 0x00}

    def getVal(self):
        return None

    def GetId(self):
        id = (self.nodeId << 24) | (self.genre << 22) | (self.commandClassId << 14) | (0 << 12) | (self.index << 4) | self.type
        id1 = (self.instance << 24)
        return (id1 << 32) | id

    def IsAwake(self):
        """Return wakeup status, always true if his a listening device, also wakeup command_class status."""
        if self.IsListeningDevice : return True
        wakeUp = self.GetCommandClass(self._manager.GetCommandClassId('COMMAND_CLASS_WAKE_UP'))
        if wakeUp is not None:
            return wakeUp.IsAwake
        else:
            self._log.write(LogLevel.Warning, self,"Node is not a listening device and don't have WakeUp command Class. It's staying on sleeping state.")
            return False
            
    def GetCapabilities(self):
        lCaps = []
        if self.frequentListening : lCaps.append("FLiRS")
        if self.listening : lCaps.append("Listening")
        if self.beaming : lCaps.append("Beaming")
        if self.routing : lCaps.append("Routing")
        if self.security: lCaps.append("Security")
        return ', '.join(lCaps)
        
    def setData(self, data):
#        self._log.write(LogLevel.Info, self, "Xml DATA : {0}".format(data))
        for clssData in data['cmdsClass']:
            commandClassId = int(clssData['id'])
            self.addCmdClss(clssData)
            for val in clssData['values']:
                self.addValue(commandClassId,  val)
        self.setEndpointsCapabilities(data)
#        print "*** class :",  self._cmdsClass
        self.product = {'type': data['product']['type'], 'id': data['product']['id'], 'name': data['product']['name']}
#        print data
        self.manufacturer = {'id':data['manufacturer']['id'],  'name': data['manufacturer']['name']}
        self.name = data['name']
        self.location = data['location']
        self.basic = data['basic']
        self.generic = data['generic']
        self.specific = data['specific']
        self.typeNode = data['type']
        self.listening = data['listening']
        self.frequentListening = data['frequentListening']
        self.beaming = data['beaming']
        self.routing = data['routing']
        self.max_baud_rate = data['max_baud_rate']
        self.version = data['version']
        self.query_stage = data['query_stage']
        self.security = data['security']
        self.m_nodeInfoSupported = data['nodeinfosupported']
        self.nodeInfoReceived = False
        self.SetDeviceClasses()

    def setXmlData(self, data):
        self._xmlData = data

    def SetManufacturerName(self, name):
        self.manufacturer['name'] = name
    
    def SetProductName(self, name):
        self.product['name'] = name
    
    def SetNodeName(self, name):
        self.name = name
        cc = self.GetCommandClass(self._manager.GetCommandClassId('COMMAND_CLASS_NODE_NAMING'))
        if cc :
            # The node supports naming, so we try to write the name into the device
            cc.SetName(name)
        
    def SetLocation(self, name):
        self.location = name
        cc = self.GetCommandClass(self._manager.GetCommandClassId('COMMAND_CLASS_NODE_NAMING'))
        if cc :
            # The node supports naming, so we try to write the name into the device
            cc.SetLocation(name)

    def SetManufacturerId(self, _manufacturerId):
        self.manufacturer['id']= _manufacturerId
        
    def SetProductType(self, _productType):
        self.product['type'] = _productType
        
    def SetProductId(self, _productId):
        self.product['id'] = _productId

    def addCmdClss(self, clssData, ozwAdded = False):
        for clss in self._cmdsClass: 
            if clssData['id'] == clss.id : return
        item = {}
        for k in clssData.keys():
            if k != 'values' : item[k] = clssData[k]
#        print "new class :" , item
        newCmdClss = self._manager.cmdClassRegistered.CreateCommandClass(clssData['id'], self, item)
        if newCmdClss is not None :
            if ozwAdded: newCmdClss.ozwAdded = True
            self._cmdsClass.append(newCmdClss)
            if self.emulData["cmdclssextraparams" ] :
                for cmdClss in self.emulData["cmdclssextraparams" ] :
                    if cmdClss == newCmdClss.GetCommandClassName :
                        if newCmdClss.getDefExtraParams() is not None :
                            for instance in self.emulData["cmdclssextraparams"][cmdClss] :
                                if newCmdClss.setInstanceExtraParams(instance, self.emulData["cmdclssextraparams"][cmdClss][instance]):
                                    self._log.write(LogLevel.Detail, self, "Extra parameters {0} loaded for instance {1} : {2}".format(newCmdClss.GetCommandClassName, instance, self.emulData["cmdclssextraparams"][cmdClss][instance]))
                                else :
                                    self._log.write(LogLevel.Warning, self, "Error on loading extra parameters for {0} instance {1} : {2}".format(newCmdClss.GetCommandClassName, instance, self.emulData["cmdclssextraparams"][cmdClss][instance]))
                        else :
                            self._log.write(LogLevel.Warning, self, "Config emul file set extra parameters for {0}, but extra params not defined for that cmdclss".format(newCmdClss.GetCommandClassName))
        else : 
            print "Error, can't create command class {0}, Not registered.".format(clssData)

    def addValue(self, commandClassId,  data):
        value = Value(self, commandClassId, data)
        if value : self._values.append(value)
    
    def getCmdClass(self, commandClassId):
        for clss in self._cmdsClass :
            if clss.id== commandClassId :
                return clss
        return None

    def getCmdClassByName(self, commandClass):
        for clss in self._cmdsClass :
            if clss.GetCommandClassName== commandClass :
                return clss
        return None

    def setEndpointsCapabilities(self, data):
        endpoints = {}
        self.numEndPoints = 0
        for clssData in data['cmdsClass']:
            for instance in clssData["instances"]:
                if 'endpoint' in instance : 
                    if instance['index'] not in endpoints :
                        self.numEndPoints += 1
                        endpoints[instance['index']] = {instance['endpoint']:[]}
                    endpoints[instance['index']][instance['endpoint']].append(clssData['id'])
        print "**** setEndpointsCapabilities : ", endpoints
        self.numEndPointsCanChange = False
        self.endPointsAreSameClass = True
        for i1 in endpoints:
            for i2 in endpoints:
                for e in endpoints[i2]:
                    if endpoints[i2][e] != endpoints[i2][e] : 
                        self.endPointsAreSameClass = False
                if len(endpoints[i1]) != len(endpoints[i2]) :
                    self.numEndPointsCanChange = True
        self.mapEndPoints = OrderedDict(sorted(endpoints.items(), key=lambda t: t[0]))
        print "numEndPointsCanChange : {0} , endPointsAreSameClass {1}".format(self.numEndPointsCanChange, self.endPointsAreSameClass)
        
    def setInstanceIndex(self, old, new):
        if old == new : return True,  ""
        if new not in self.mapEndPoints:
            for i, ep in self.mapEndPoints.iteritems():
                if i == old :
                    del self.mapEndPoints[old]
                    self.mapEndPoints[new] = ep
                    self.mapEndPoints = OrderedDict(sorted(self.mapEndPoints.items(), key=lambda t: t[0]))
                    return True,  ""
        return False,  "Index {0} allready exist, no duplicate index.".format(new)
            
    def setInstanceEndPoint(self, index, new):
        for i, ep in self.mapEndPoints.iteritems():
            if i == index :
                print "Instance ",  i, "enPoint ",  ep,  "new",  new
                for endP in ep :  # Only one endPoint
                    if endP == new : return True,  ""
                for i2, ep2 in self.mapEndPoints.iteritems(): # Check if endPoint exist
                    for endP2 in ep2:
                        if endP2 == new : return False,  "EndPoint {0} allready exist for instance {1}, no duplicate EndPoint.".format(new,  i2)
                print ep
                clss = ep[ep.keys()[0]]
                del self.mapEndPoints[i][ep.keys()[0]]
                self.mapEndPoints[i][new] = clss
                return True,  ""
        return False,  "Instance Index {0} doesn't exist.".format(new)

    def setInstanceClssEndPoint(self, index, endPoint, new):
        for i, ep in self.mapEndPoints.iteritems():
            if i == index :
                print "Instance ",  i, "enPoint ",  ep,  "new",  new
                for endP in ep :  # Only one endPoint
                    if endP == endPoint : 
                        self.mapEndPoints[i][endPoint] = new
                        return True,  ""
                return False,  "In Instance Index {0}, EndPoint {1} doesn't exist...".format(index, endPoint)
        return False,  "Instance Index {0} doesn't exist...".format(index)

    def getAllInstance(self):
        retval = {}
        if self.numEndPoints > 0:
            if 1 not in self.mapEndPoints:
                retval[1] = {255:[]}
        retval.update(self.mapEndPoints)
        return retval

    def getEndpointCmdClasses(self,  endpoint):
        cmdClss =[]
        for i in self.mapEndPoints:
            for eP in self.mapEndPoints[i]:
                if eP == endpoint : 
                    for clss in self.mapEndPoints[i][eP] :
                        if clss not in cmdClss : cmdClss.append(clss)
        return cmdClss
        
    def getInstanceFromEndpoint(self, clssId, endpoint):
        for instance in self.mapEndPoints:
            for eP in self.mapEndPoints[instance]:
                if eP == endpoint : 
                    if clssId in self.mapEndPoints[instance][eP] : return instance
        return 0
        
    def getEndpointFromInstance(self, clssId, instance):
        if instance in self.mapEndPoints:
            for eP in self.mapEndPoints[instance]:
                if clssId in self.mapEndPoints[instance][eP] : return eP
        return 0
        
    def GetClassIdInformation(self, commandClassId):
        for clss in self._cmdsClass :
            if commandClassId == clss.id:
                return {'name' : clss.name ,  'version': clss.m_version,  'id': clss.id}
                
    def hasBasicClass(self):
        for clss in self._cmdsClass:
            if clss.id == 32: #  COMMAND_CLASS_BASIC
                return True
        return False

    def GetCommandClass(self,  clssId):
        for clss in self._cmdsClass:
            if clss.id == clssId:
                return clss
        return None

    def GetBasicMapping(self):
        for clss in self._cmdsClass:
            if clss.id == 32: #  COMMAND_CLASS_BASIC
                if clss.mapping != 0 :
                    return clss.mapping
        return None

    def AddMandatoryCommandClasses(self,  addClass):
        mClass = []
        afterMark  = False
        for clssId in addClass:
            if clssId == '0xef': 
                afterMark = True
                continue
            if self._manager.IsSupportedCommandClasses(int(clssId,  16)):
                if (int(clssId,  16) > 5) and (int(clssId, 16) < 0xef) :
                    # if AddCommandClass(clss) : # TODO: c'est ici que la lib C++ ajout la command class au node, nous elle l'est déjà 
                    clssRef = self.GetCommandClass((int(clssId, 16))) 
                    if clssRef :
                        clssRef.mandatory = True
                        if afterMark and clssId not in mClass :
                            clssRef.m_afterMark = True
                        else :
                            clssRef.m_afterMark = False
                            mClass.append(clssId)
                            # C'est ici que la lib appel la création si besoin d'une value.
                    else :
                         self._log.write(LogLevel.Warning, self, "Mandatory command class {0} must be added to node {1}".format(clssId,  self.nodeId))
        for clssId in mClass :
            if clssId not in self._mandatoryClasses: self._mandatoryClasses.append(clssId)

    def hasOptionalFunctionality(self):
        cpt = 0
        for clss in self._cmdsClass:
            if clss.mandatory and clss.id != 0x20 and clss.id != 0x00 : cpt += 1 #  exclude COMMAND_CLASS_NO_OPERATION and COMMAND_CLASS_BASIC
        print "************* node {0} hasOptionalFunctionality : {1}".format(self.nodeId,  True if cpt else False)
        print self._mandatoryClasses
        return True if cpt else False
        
    def getValue(self, commandClassId, instance, index):
        for v in self._values :
            if v._commandClassId == commandClassId and v._index == index and v._instance == instance: return v
        return None
        
    def getValueByLabel(self, commandClassId, instance, label):
        for v in self._values :
            if v._commandClassId == commandClassId and v._label == label and v._instance == instance: return v
        return None

    def getValueById(self, vId):
        print "search value id : " + vId
        for v in self._values :
            if v.GetId() == vId :
               print 'find'
               return v
        return None
        
    def getCmdClassValues(self, commandClassId):
        listValues = []
        for v in self._values :
            if v._commandClassId == commandClassId :
                listValues.append(v)
        return listValues
        
    def getCmdClassInstanceValues(self, commandClassId, instance):
        listValues = []
        for v in self._values :
            if v._commandClassId == commandClassId and v._instance == instance:
                listValues.append(v)
        return listValues

    def UpdateProtocolInfo(self):
        self._log.write(LogLevel.Info, self, "  Protocol Info for Node {0}:".format(self.nodeId))
        if self.listening :
            self._log.write(LogLevel.Info, self, "    Listening     = True" )
        else:
            self._log.write(LogLevel.Info, self, "    Listening     = False" )
            self._log.write(LogLevel.Info, self, "    Frequent      = {0}".format(self.frequentListening))
        self._log.write(LogLevel.Info, self, "    Beaming       = {0}".format(self.beaming))
        self._log.write(LogLevel.Info, self, "    Routing       = {0}".format(self.routing))
        self._log.write(LogLevel.Info, self, "    Max Baud Rate = {0}".format(self.max_baud_rate))
        self._log.write(LogLevel.Info, self, "    Version       = {0}".format(self.version))
        self._log.write(LogLevel.Info, self, "    Security      = {0}".format(self.security))
        self.m_protocolInfoReceived = True
        self.SetDeviceClasses()

    def getMsgProtocolInfo(self):
        # TODO: Don't known completly how bytes is formating so applied just basic set for openzwave
        msg = Msg( "NoOperation_Set", self.nodeId,  RESPONSE, FUNC_ID_ZW_GET_NODE_PROTOCOL_INFO)
        d = 0x80 if self.listening else 0
        if self.routing : d |= 0x40
        if self.max_baud_rate == 40000 : d |= 0x12 #   mask for (_data[0] & 0x38 ) == 0x10 
        d |= self.version -1
        msg.Append(d)
        d = SecurityFlag.Sensor250ms if self.frequentListening  else 0 # TODO: We can known witch is capabilities between SecurityFlag.Sensor250ms and SecurityFlag.Sensor1000ms ?
        if self.beaming : d |= SecurityFlag.BeamCapability
        if self.security : d |= SecurityFlag.Security
        if self.IsController() : d |= SecurityFlag.Controller
        if self.specific != 0 : d |= SecurityFlag.SpecificDevice
        if self.basic == 0x04  : d |= SecurityFlag.RoutingSlave
        if self.hasOptionalFunctionality() : d |= SecurityFlag.OptionalFunctionality
        msg.Append(d)
        msg.Append(0)  # don't known signification ?
        msg.Append(self.basic)
        msg.Append(self.generic)
        msg.Append(self.specific)
#        msg.Append(self.nodeId)
        return msg
        
    def SetDeviceClasses(self):
        basic = self._manager._DeviceClass.getBasic(self.basic)
        self._log.write(LogLevel.Info, self, "  Basic device class    ({0}) - {1}".format(basic['key'], basic['label']))
        basicMapping = self.GetBasicMapping()               # Get the command class that COMMAND_CLASS_BASIC maps to.
        generic = self._manager._DeviceClass.getGeneric(self.generic)
        if generic is not None :
            self._log.write(LogLevel.Info, self, "  Generic device Class  ({0}) - {1}".format(generic['key'], generic['label']))
            self.AddMandatoryCommandClasses(generic['command_classes'])
            specific = self._manager._DeviceClass.getSpecific(self.generic, self.specific)
#            print "**** generic :",  generic
            if specific:
                self._log.write(LogLevel.Info, self, "  Specific device Class ({0}) - {1}".format(specific['key'], specific['label']))
#                print "+++++ Specific : ",  specific
                self.AddMandatoryCommandClasses(specific['command_classes'])
                s = specific
                if s['basic'] != "":            # Override the generic device class basic mapping with the specific device class one.
                    basicMapping = int(s['basic'], 16)
            else :
                self._log.write(LogLevel.Info, self, "  No specific device class defined")
        else :
            self._log.write(LogLevel.Info, self, "No generic or specific device classes defined")
        if not self.listening :
            clssWakeUp = self.GetCommandClass(int('0x84', 16)) # COMMAND_CLASS_WAKE_UP
#            print 'class wake up :',  clssWakeUp
            if clssWakeUp is None :
                print "++++++ addind WakeUp command class ++++"
                self.addCmdClss({'id': int('0x84', 16),  'name' : 'COMMAND_CLASS_WAKE_UP','instances': [1], 'request_flags': u'2', 'version': '0x0', 'after_mark': False}, True)
            self.AddMandatoryCommandClasses(['0x84'])
        if self.hasBasicClass() : self.SetMapping(basicMapping)
        if self._cmdsClass :
            reportedClasses = False
            self._log.write(LogLevel.Info, self, "  Mandatory Command Classes for Node {0}:".format(self.nodeId))
#            print self._mandatoryClasses
            for clss in self._cmdsClass:
                if clss.mandatory and not clss.m_afterMark:
                    self._log.write(LogLevel.Info, self, "    {0}".format(clss.name))
                    reportedClasses = True
            if not reportedClasses: self._log.write(LogLevel.Info, self, "    None")
            reportedClasses = False
            self._log.write(LogLevel.Info, self, "  Mandatory Command Classes controlled by Node {0}:".format(self.nodeId))
            for clss in self._cmdsClass:
                if clss.mandatory and clss.m_afterMark:
                    self._log.write(LogLevel.Info, self, "    {0}".format(clss.name))
                    reportedClasses = True
            if not reportedClasses: self._log.write(LogLevel.Info, self, "    None")
            self._log.write(LogLevel.Detail, self, "Query Stage Complete (ProtocolInfo)")
            self.UpdateNodeInfo()

    def SetMapping(self, basicMapping):
        if basicMapping is None : 
            self._mapping = None
            self._log.write(LogLevel.Info, self, "    COMMAND_CLASS_BASIC is not mapped")
            return False
        else : 
            mapped = self.GetClassIdInformation(basicMapping)
            for clss in self._cmdsClass:
                if clss.id == 32: #  COMMAND_CLASS_BASIC
                    if clss.ignoremapping : 
                        self._mapping = None
                        self._log.write(LogLevel.Info, self, "    COMMAND_CLASS_BASIC will not be mapped to {0}(ignored)".format(mapped['name']))
                        return True
                    else :
                        self._mapping = basicMapping
                        self._log.write(LogLevel.Info, self, "    COMMAND_CLASS_BASIC will be mapped to {0}".format(mapped['name']))
                        return True
        return False

    def UpdateNodeInfo(self):
        if not self.nodeInfoReceived:
#            Add the command classes specified by the device
            self._log.write(LogLevel.Info, self, "  Optional command classes for node {0}:".format(self.nodeId))
            newCommandClasses = False
            afterMark = False
            for clss in self._cmdsClass:
                if not clss.mandatory:  # check if command_class is in mandatory command class.
                    if  clss.id == 0xef :   # TODO: find a refence in xml config to set after mark
                        # COMMAND_CLASS_MARK.
                        #Marks the end of the list of supported command classes.  The remaining classes
                        #are those that can be controlled by the device.  These classes are created
                        #without values.  Messages received cause notification events instead.
                        afterMark = true;
                        if not newCommandClasses: self._log.write(LogLevel.Info, self, "    None" )
                        self._log.write(LogLevel.Info, self, "  Optional command classes controlled by node {0}:".format(self.nodeId))
                        newCommandClasses = false
                        continue
                    if self._manager.IsSupportedCommandClasses(clss.id):
                        # If this class came after the COMMAND_CLASS_MARK, then we do not create values.
                        if afterMark :
                            clss.m_afterMark = True
                        else :
                            clss.m_afterMark = False
                        # Start with an instance count of one.  If the device supports COMMMAND_CLASS_MULTI_INSTANCE
                        # then some command class instance counts will increase once the responses to the RequestState
                        # call at the end of this method have been processed.
    #					pCommandClass->SetInstance( 1 );
                        newCommandClasses = True
                        self._log.write(LogLevel.Info, self, "    {0}".format(clss.name))
                    else :
                        self._log.write(LogLevel.Info, self, "  CommandClass 0x%.2x - NOT REQUIRED"%clss.id)
            if not newCommandClasses:
                # No additional command classes over the mandatory ones.
                self._log.write(LogLevel.Info, self, "    None" )
#                SetStaticRequests();
            self.nodeInfoReceived = True
#
#	# Treat the node info frame as a sign that the node is awake
#	if( WakeUp* wakeUp = static_cast<WakeUp*>( GetCommandClass( WakeUp::StaticGetCommandClassId() ) ) )
#	{
#		wakeUp->SetAwake( true );
#	}        

    def GetDeviceClasses(self):
        basic = self._manager._DeviceClass.getBasic(self.basic)
        retInfos = ["Basic device class    ({0}) - {1}".format(basic['key'], basic['label'])]
        generic = self._manager._DeviceClass.getGeneric(self.generic)
        if generic is not None :
            retInfos.append("Generic device Class  ({0}) - {1}".format(generic['key'], generic['label']))
            specific = self._manager._DeviceClass.getSpecific(self.generic, self.specific)
            if specific:
                retInfos.append("Specific device Class ({0}) - {1}".format(specific['key'], specific['label']))
            else :
                retInfos.append("No specific device class defined")
        else :
            retInfos.append("No generic or specific device classes defined")
        return retInfos

    def SetAddingNode(self):
       self.m_addingNode = True
       
    def ClearAddingNode(self):
       self.m_addingNode = False
       
    def Reset(self):
        self.name = ""
        self.location = ""
        self.neighbors = []
        clssAssoc = self.getCmdClassByName("COMMAND_CLASS_ASSOCIATION")
        if clssAssoc is not None : clssAssoc.Reset() 
       
    def HandleMsgSendDataResponse(self, _data):
        if self.registeredCallbackId == 0:
            self.registeredClassId = _data[4]
            self.registeredCallbackId = _data[-2]
            msg = Msg( "Z-Wave stack for cmdClass 0x{0:02x} ZW_SEND_DATA".format(self.registeredCallbackId), self.nodeId,  RESPONSE, FUNC_ID_ZW_SEND_DATA)
            msg.Append(TRANSMIT_OPTION_ACK) # 0x01
            msg.SetExpectedCallBack(_data[-2])
            self.GetDriver.SendMsg(msg, MsgQueue.NoOp)
            # Sending 2nd response
            msg = Msg( "Request with callback ID 0x{0:02x} for ZW_SEND_DATA".format(self.registeredCallbackId), self.nodeId,  REQUEST, FUNC_ID_ZW_SEND_DATA)
            msg.Append(self.registeredCallbackId)
            msg.SetExpectedCallBack(_data[-2])
            if self.IsFailed or not self.IsAwake(): 
                msg.Append(TRANSMIT_COMPLETE_NO_ACK) #  0x01
                self.GetDriver.SendMsg(msg, MsgQueue.NoOp)
            else :
                msg.Append(TRANSMIT_COMPLETE_OK) #  0x00
                self.GetDriver.SendMsg(msg, MsgQueue.NoOp)
                self.handleApplicationCommandHandler(_data[5:])
            self.registeredCallbackId = 0
            self.registeredClassId = 0
        else : print " ********************** registeredCallbackId = 0x{0:02x} *********".format(self.registeredCallbackId)
#        FUNC_ID_ZW_SEND_DATA
#        FUNC_ID_SERIAL_API_GET_INIT_DATA
#        FUNC_ID_SERIAL_API_APPL_NODE_INFORMATION
    
    def handleApplicationCommandHandler(self, _data):
        if self.registeredClassId != 0x00:
            clss = self.GetCommandClass(self.registeredClassId)
            if clss is not None :
                handler = threading.Thread(None, clss.HandleMsg, "th_Handle_ProccessMsg_class_0x%0.2x."%self.registeredClassId, (_data), {'Wait':0})
                handler.start()
            else :
                self._log.write(LogLevel.Warning, self,"CommandClass 0x%0.2x not registered."%self.registeredClassId)
            
    def getMsgNodeInfo(self):
        if self.IsController() and self.failNodeInfo < 1 :
            msg = Msg("Simulate Fail node info", self.nodeId,  REQUEST, FUNC_ID_ZW_APPLICATION_UPDATE)
            msg.Append(UPDATE_STATE_NODE_INFO_REQ_FAILED)          
            msg.Append(0)
            msg.Append(0)
            self.failNodeInfo += 1
            return msg 
        else : 
            self.failNodeInfo = 0
            return self.getMsgNodeInfoClass()
       
    def getMsgRoutingInfo(self,  _data):
        msg = Msg("Routing info Response", self.nodeId,  RESPONSE, FUNC_ID_ZW_GET_ROUTING_INFO)
        tab = []
        for i in range(29): tab.append(0x00) # Bit filed node ID
        for n in self.neighbors : tab[(n -1)  //8] |= 0x01 << ((n-1) % 8)
        for i in tab: msg.Append(i)
        return msg

    def getMsgNewNodeAdded(selfself, _data):
        """Format data to include a new node in network"""
        msg = Msg( "Node info cmdclass Response", self.nodeId,  REQUEST, FUNC_ID_ZW_ADD_NODE_TO_NETWORK)
        # add callbackID + nodeID + info class
        msg.Append()
        msg.Append(self.nodeId)

    def getMsgNodeInfoClass(self):
        msg = Msg( "Node info cmdclass Response", self.nodeId,  REQUEST, FUNC_ID_ZW_APPLICATION_UPDATE)
        msg.Append(UPDATE_STATE_NODE_INFO_RECEIVED)
        msg.Append(self.nodeId)
#        clssList = []
#        afterM = []
#        for clss in self._cmdsClass:
##            if clss.mandatory : clssList.append(clss.id)
#            if clss.id != 0x00 and clss.id != 0x20 and not clss.ozwAdded and clss.m_createVars: # exclude COMMAND_CLASS_NO_OPERATION and  COMMAND_CLASS_BASIC and ozw intenal add
#                if clss.m_afterMark:
#                    if not afterM: afterM.append(0xef)  # set afterMark flag
#                    afterM.append(clss.id)
#                else :
#                    clssList.append(clss.id)
#        clssList.extend(afterM)
#        msg.Append(len(clssList) + 3)
#        msg.Append(self.basic)
#        msg.Append(self.generic)
#        msg.Append(self.specific)
        for c in self.getNodeInfoClass(): msg.Append(c)
        return msg
        
    def getNodeInfoClass(self):
        clssList = []
        afterM = []
        fullList = []
        for clss in self._cmdsClass:
#            if clss.mandatory : clssList.append(clss.id)
            if clss.id != 0x00 and clss.id != 0x20 and not clss.ozwAdded and clss.m_createVars: # exclude COMMAND_CLASS_NO_OPERATION and  COMMAND_CLASS_BASIC and ozw intenal add
                if clss.m_afterMark:
                    if not afterM: afterM.append(0xef)  # set afterMark flag
                    afterM.append(clss.id)
                else :
                    clssList.append(clss.id)
        clssList.extend(afterM)
        fullList.append(len(clssList) + 3)
        fullList.append(self.basic)
        fullList.append(self.generic)
        fullList.append(self.specific)
        for c in clssList: fullList.append(c)
        return fullList
        
    def getMsgNodeNeighborUpdate(self, callbackId):
#        REQUEST_NEIGHBOR_UPDATE_STARTED	=	0x21
#        REQUEST_NEIGHBOR_UPDATE_DONE	    =	0x22
#        REQUEST_NEIGHBOR_UPDATE_FAILED	=	0x23
        msg = Msg( "Neighbor update status", self.nodeId,  REQUEST, FUNC_ID_ZW_REQUEST_NODE_NEIGHBOR_UPDATE_OPTIONS)
        msg.Append(callbackId)
        if self.currentCommand == 0 : 
            self.currentCommand = FUNC_ID_ZW_REQUEST_NODE_NEIGHBOR_UPDATE_OPTIONS
            self.currentCommandState = REQUEST_NEIGHBOR_UPDATE_STARTED
            msg.Append(REQUEST_NEIGHBOR_UPDATE_STARTED)
            threading.Thread(None, self.emulCycleCmd, "th_handleEmulCycleCmd_node_{0}.".format(self.nodeId), (), {'listState': [REQUEST_NEIGHBOR_UPDATE_DONE],
                                        'timings': [2.0],
                                        'callback': self.getMsgNodeNeighborUpdate, 
                                        'callbackId': callbackId, 
                                        'queues' : [MsgQueue.Command], 
                                        'firstNext':  [True]
                                    }).start()
        elif self.currentCommand == FUNC_ID_ZW_REQUEST_NODE_NEIGHBOR_UPDATE_OPTIONS:
            msg.Append(self.currentCommandState)
            if self.currentCommandState != REQUEST_NEIGHBOR_UPDATE_STARTED:
                self.currentCommand = 0
                self.currentCommandState = 0
        return msg
    
    def startPoll(self):
        if not self._runningPoll:
            if len(self.emulData['pollingvalues']) != 0:
                threading.Thread(None, self.handlePollCycle, "th_handlePollCycle_node_{0}.".format(self.nodeId), (), {}).start()
            else :
                self._runningPoll = False
                self._log.write(LogLevel.Detail, self, "No polling value for this node.")
        else :
            self._log.write(LogLevel.Detail, self, "Polling value allready started for this node.")            

    def handlePollCycle(self):
        self._log.write(LogLevel.Detail, self, "Start polling value(s) cycle for emulation :")
        self._runningPoll = True
        nb = 1
        for poll in self.emulData['pollingvalues']:
            poll['id'] = nb
            poll['lastpoll'] = time.time()
            self._log.write(LogLevel.Detail, self, "  - {0} instance: {1}, label: {2}, every {3}s, parameters {4}.".format(poll['cmdclass'], poll['instance'], poll['label'], poll['timing'], poll['params']))
            nb += 1
        while not self._stop.isSet() and self._runningPoll:
            for poll in self.emulData['pollingvalues']:
                t = time.time()
                if poll['unable'] and t  >= poll['lastpoll'] + poll['timing'] :
                    poll['lastpoll'] = t
                    if not self.IsFailed :
                        if self.IsAwake():
                            self._log.write(LogLevel.Debug, self, "Polling Value {0}".format(poll))
                            cmdClass = self.GetCommandClass(self._manager.GetCommandClassId(poll['cmdclass']))
                            if cmdClass : cmdClass.pollValue(poll)
                            else : self._log.write(LogLevel.Warning, self, "Error in Config emulation JSON file. CommandClass don't exist : {0}".format(poll))
                    else : self._log.write(LogLevel.Debug, self, "Node marked as Fail, no polling value.")
            self._stop.wait(0.1)
        self._log.write(LogLevel.Detail, self, "Stop polling value cycle.")

    def getPoll(self, id):
        for poll in self.emulData['pollingvalues']:
            if poll['id'] == id :
                return poll
        return None

    def getEmptyPoll(self):
        return POLLDATA

    def setPollParam(self, id, param, value):
        for poll in self.emulData['pollingvalues']:
            if poll['id'] == id :
                if param in poll : 
                    print poll
                    poll[param] = value
                    self._log.write(LogLevel.Detail, self, "Set poll {0}, param {1}, {2}".format(id, param, poll))
                    return True
                else : return False
        return False
        
    def updatePollParam(self, id, params):
        for poll in self.emulData['pollingvalues']:
            if poll['id'] == id :
                poll.update(params)
                self._log.write(LogLevel.Detail, self, "poll {0}, updated {1}".format(id, params))
                return True
        return False
    
    def deletePoll(self, id):
        for poll in self.emulData['pollingvalues']:
            if poll['id'] == id :
                self.emulData['pollingvalues'].remove(poll)
                if not self.emulData['pollingvalues']: self._runningPoll = False
                return True
        return False
        
    def addPollValue(self, pollAdd):
        find = False
        id = []
        for poll in self.emulData['pollingvalues']:
            if (poll['cmdclass'] == pollAdd['cmdclass']) and (poll['instance'] == pollAdd['instance']) and (poll['label'] == pollAdd['label']) :
                find = True
                break;
            id.append(poll['id'])
        if not find :
            nb = 1
            free = False
            while not free : 
                if nb in id : 
                    nb += 1
                else: free = True
            pollAdd['id'] = nb
            pollAdd['lastpoll'] = time.time()
            self.emulData['pollingvalues'].append(pollAdd)
            self._log.write(LogLevel.Detail, self, "Poll added - - {0} instance: {1}, label: {2}, every {3}s, params {4}.".format(pollAdd['cmdclass'], pollAdd['instance'], pollAdd['label'], pollAdd['timing'], pollAdd['params']))
            self._log.write(LogLevel.Detail, self, "   Poll unable : {0}".format(pollAdd['unable']))
            self.startPoll()
            return "",  ""
        else:
            return "error", "Polled value allready exist, can't be create."
            
    def emulCycleCmd(self, listState = [], timings = [], callback = None, callbackId = None, queues = [], firstNext = []):
        self._log.write(LogLevel.Detail, self, "Start command emulation :{0} ({1})".format(getFuncName(self.currentCommand), GetDataAsHex([self.currentCommand])))
        i = 0
        print "++++ Node emulCycleCmdkwargs : ", listState, timings, callback
        for state in listState:
            self.currentCommandState = listState[i]
            if callbackId is not None : msg = callback(callbackId)
            else : msg = callback()
            self.GetDriver.SendMsg(msg, queues[i], firstNext[i], timings[i])
            i += 1

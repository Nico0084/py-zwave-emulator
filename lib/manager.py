#!/usr/bin/python
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
from lib.node import Node
from lib.driver import Driver
from lib.options import Options
from lib.log import Log, LogLevel
from lib.vers import ozw_vers_major, ozw_vers_minor, ozw_vers_revision
from lib.xmlfiles import networkFileConfig,  DeviceClasses,  Manufacturers
from lib.command_classes.commandclasses import CommandClasses
import os
import re
import threading
import psutil
import subprocess
#import copy

MANAGER = None  # A Singleton for manager
OPTIONS = Options() # A Singleton for Options

#SUPPORTEDCOMMANDCLASSES = {
#    0x71: "COMMAND_CLASS_ALARM",
#    0x22: "COMMAND_CLASS_APPLICATION_STATUS",
#    0x85: "COMMAND_CLASS_ASSOCIATION",
#    0x9b: "COMMAND_CLASS_ASSOCIATION_COMMAND_CONFIGURATION",
#    0x20: "COMMAND_CLASS_BASIC",
#    0x50: "COMMAND_CLASS_BASIC_WINDOW_COVERING",
#    0x80: "COMMAND_CLASS_BATTERY",
#    0x46: "COMMAND_CLASS_CLIMATE_CONTROL_SCHEDULE",
#    0x81: "COMMAND_CLASS_CLOCK",
#    0x70: "COMMAND_CLASS_CONFIGURATION",
#    0x21: "COMMAND_CLASS_CONTROLLER_REPLICATION",
#    0x56: "COMMAND_CLASS_CRC_16_ENCAP" ,
#    0x90: "COMMAND_CLASS_ENERGY_PRODUCTION",
#    0x82: "COMMAND_CLASS_HAIL",
#    0x87: "COMMAND_CLASS_INDICATOR",
#    0x89: "COMMAND_CLASS_LANGUAGE",
#    0x76: "COMMAND_CLASS_LOCK",
#    0x72: "COMMAND_CLASS_MANUFACTURER_SPECIFIC",
#    0x32: "COMMAND_CLASS_METER",
#    0x35: "COMMAND_CLASS_METER_PULSE",
#    0x8f: "COMMAND_CLASS_MULTI_CMD",
#    0x60: "COMMAND_CLASS_MULTI_INSTANCE/CHANNEL",
#    0x8e: "COMMAND_CLASS_MULTI_INSTANCE_ASSOCIATION",
#    0x77: "COMMAND_CLASS_NODE_NAMING",
#    0x00: "COMMAND_CLASS_NO_OPERATION",
#    0x73: "COMMAND_CLASS_POWERLEVEL",
#    0x88: "COMMAND_CLASS_PROPRIETARY",
#    0x75: "COMMAND_CLASS_PROTECTION",
#    0x2B: "COMMAND_CLASS_SCENE_ACTIVATION",
#    0x9c: "COMMAND_CLASS_SENSOR_ALARM",
#    0x30: "COMMAND_CLASS_SENSOR_BINARY",
#    0x31: "COMMAND_CLASS_SENSOR_MULTILEVEL",
#    0x27: "COMMAND_CLASS_SWITCH_ALL",
#    0x25: "COMMAND_CLASS_SWITCH_BINARY",
#    0x26: "COMMAND_CLASS_SWITCH_MULTILEVEL",
#    0x28: "COMMAND_CLASS_SWITCH_TOGGLE_BINARY",
#    0x29: "COMMAND_CLASS_SWITCH_TOGGLE_MULTILEVEL",
#    0x44: "COMMAND_CLASS_THERMOSTAT_FAN_MODE",
#    0x45: "COMMAND_CLASS_THERMOSTAT_FAN_STATE",
#    0x40: "COMMAND_CLASS_THERMOSTAT_MODE",
#    0x42: "COMMAND_CLASS_THERMOSTAT_OPERATING_STATE",
#    0x43: "COMMAND_CLASS_THERMOSTAT_SETPOINT",
#    0x63: "COMMAND_CLASS_USER_CODE",
#    0x86: "COMMAND_CLASS_VERSION",
#    0x84: "COMMAND_CLASS_WAKE_UP",
#    }


class Manager(object):
    """Manager as singleton, and singleton options link"""

    instance = None
    initialized = False

    def __new__(cls, *args, **kargs):
        cls._log = None
        if OPTIONS is not None and OPTIONS.AreLocked:
            if  Manager.instance is None:
                Manager.instance = object.__new__(cls, *args, **kargs)
                Manager.initialized = False
            else :
                Manager.initialized = True
            cls._options = OPTIONS
            return Manager.instance
        cls._log = Log()
        cls._log.create("",  False,  True, LogLevel.Debug , LogLevel.Debug, LogLevel.Debug)
        cls._log.write(LogLevel.Error, cls, "Options have not been created and locked. Exiting...")
        exit(1)
        return None

    def __init__(self):
        global MANAGER
        if not self.initialized :
            self._nodes = []
            self.drivers = []
            self._DeviceClass = []
            self.zwNetworks = {}
            self.paramsConfig = {}
            self._stop = threading.Event()
    #        find, configPath = self._options.GetOptionAsString( "ConfigPath")
    #        self.readXmlDeviceClasses(configPath)
    #        self.manufacturers = Manufacturers(configPath)
    #        self.cmdClassRegistered = CommandClasses(self)
            MANAGER = self

    def __del__(self):
        global MANAGER
        MANAGER =None
        self.instance = None
        self.initialized = False
        self._stop.set()

    def Create(self):
        # Create the log file (if enabled)
        find, logging = self._options.GetOptionAsBool( "Logging")
        if not find : logging = False
        find, userPath = self._options.GetOptionAsString( "UserPath")
        if not find : userPath = ""
        find, logFileNameBase = self._options.GetOptionAsString( "LogFileName")
        if not find : logFileNameBase = "OZWEmule_Log.txt"
        find, bAppend = self._options.GetOptionAsBool( "AppendLogFile")
        if not find :  bAppend = False
        find, bConsoleOutput = self._options.GetOptionAsBool( "ConsoleOutput")
        if not find : bConsoleOutput = True
        find, nSaveLogLevel = self._options.GetOptionAsInt( "SaveLogLevel")
        if not find : nSaveLogLevel = LogLevel.Debug #LogLevel.Detail
        find, nQueueLogLevel = self._options.GetOptionAsInt( "QueueLogLevel")
        if not find : nQueueLogLevel = LogLevel.StreamDetail # LogLevel.Debug
        find, nDumpTrigger = self._options.GetOptionAsInt( "DumpTriggerLevel")
        if not find : nDumpTrigger = LogLevel.Warning
        logFilename = userPath + logFileNameBase
        self._log = Log()
        self._log.create(logFilename, bAppend, bConsoleOutput, nSaveLogLevel, nQueueLogLevel, nDumpTrigger)
        self._log.setLoggingState(logging)
        self._options.setLog(self._log)
        find, configPath = self._options.GetOptionAsString( "ConfigPath")
        self.readXmlDeviceClasses(configPath)
        self.manufacturers = Manufacturers(configPath)
        self.cmdClassRegistered = CommandClasses(self)
        self.cmdClassRegistered.RegisterCommandClasses()
#        try :
#            self.paramsConfig = readJsonFile('../data/config_emulation.json')
#            self._log.write(LogLevel.Always, self,"Config parameters loaded : {0}".format(self.paramsConfig))
#        except:
#            self._log.write(LogLevel.Warning, self,"No correct file config for emulation in data path.")
        self.loadXmlConfig()
#        Scene.ReadScenes()
        self._log.write(LogLevel.Always, self, "OpenZwave-emulator Version {0} Starting Up".format(self.getVersionAsString()))
        for homeId in self.zwNetworks :
            self.startDriver(homeId)

    def GetValAsHex(self, value, nChar = 2):
        print
        if type(value) != 'list' : data = [value]
        else : data =value
        return GetDataAsHex(data, nChar)

    def checkVirtualCom(self, homeId):
        """Check if a virtual port emulator is running"""
        if 'configData' in self.zwNetworks[homeId] :
            configData = self.zwNetworks[homeId]['configData']
            if 'virtualcom' in configData :
                if  configData['virtualcom']['modul'] == 'socat' :
                    try :
                        pids = psutil.pids()
                        for i in pids:
                            p = psutil.Process(i)
                            if p.name() == 'socat' :
                                chk_zwavectrl = False
                                chk_emulator = False
                                for lig in p.cmdline():
                                    if lig.find(configData['virtualcom']['ports']['zwavectrl']) != -1 : chk_zwavectrl = True
                                    if lig.find(configData['virtualcom']['ports']['emulator']) != -1 : chk_emulator = True
                                if chk_zwavectrl and chk_emulator :
                                    self._log.write(LogLevel.Always, self, "Virtual port socat running on {0} for zwave serial port {1}.".format( configData['virtualcom']['ports']['emulator'], configData['virtualcom']['ports']['zwavectrl']))
                                return True
                    except Exception as e :
                        self._log.write(LogLevel.Warning, self, "Socat Process error : {0}".format(e))
        self._log.write(LogLevel.Always, self, "Virtual communication system not running.")
        return False

    def startVirtualCom(self, homeId, start = False):
        if 'configData' in self.zwNetworks[homeId] and 'virtualcom' in self.zwNetworks[homeId]['configData']:
            virtualcom = self.zwNetworks[homeId]['configData']['virtualcom']
            if start or virtualcom['start'] == 'auto':
                if not self.checkVirtualCom(homeId) :
                    if virtualcom['modul'] == 'socat' :
                        if virtualcom['ports']['zwavectrl'] and virtualcom['ports']['emulator'] :
                            self._log.write(LogLevel.Info, self, "Starting Virtual communication system...")
                            subprocess.Popen(['socat','-d', '-d', 'PTY,ignoreeof,echo=0,raw,link={0}'.format(virtualcom['ports']['zwavectrl']),
                                                    'PTY,ignoreeof,echo=0,raw,link={0}'.format(virtualcom['ports']['emulator'])])
                            self._stop.wait(1)
                            if not self.checkVirtualCom(homeId) :
                                self._log.write(LogLevel.Error, self, "Error on starting Virtual communication system.")
                    else :
                        self._log.write(LogLevel.Warning, self, "Virtual communication configuration not handled : {0}".format(virtualcom))
            else :
                self._log.write(LogLevel.Always, self, "Virtual communication system not in auto start-up.")
        else :
            self._log.write(LogLevel.Warning, self, "No configuration set for virtual communication on zwave HomeId {0}".format(homeId))

    def getVersionAsString(self):
        return "{0}.{1}.{2}".format(ozw_vers_major, ozw_vers_minor, ozw_vers_revision)

    def readXmlNetwork(self, fileConf):
        return networkFileConfig(fileConf)

    def readXmlDeviceClasses(self, pathConf):
        self._DeviceClass = DeviceClasses(pathConf)

    def loadXmlConfig(self):
        dataDir = '../data'
        files = os.listdir(dataDir)
        xmlFormat = r"^zwcfg_0x[0-9,a-f,A-F]{8}.xml$"
        for f in files:
            if re.match(xmlFormat,  f) is not None :
                if f not in self.zwNetworks :
                    self._log.write(LogLevel.Always, self, "Find and loading {0} openzwave file config....".format(dataDir + "/" + f))
                    xmlData = self.readXmlNetwork(dataDir + "/" + f)
                    driverData = xmlData.getDriver(0)
                    homeId = driverData['homeId']
                    self.zwNetworks[homeId] = {'xmlData': xmlData}
                    configFile = f.replace('xml', 'json')
                    try :
                        self.zwNetworks[homeId]['configData'] = readJsonFile(dataDir + "/" +  configFile)
                        self._log.write(LogLevel.Always, self,"Config for emulation loaded : {0}".format(self.zwNetworks[homeId]['configData']))
                    except :
                        self._log.write(LogLevel.Error, self,"Error on readind config file for emulation :{0}".format(dataDir + "/" +  configFile))
                    print driverData
                    nodes = self.zwNetworks[homeId]['xmlData'].listeNodes()
                    for node in nodes :
                        xmlNode = self.zwNetworks[homeId]['xmlData'].getNode(node)
                        self.addXmlNode(homeId,  xmlNode['id'],  xmlNode)
                    self.startVirtualCom(homeId)
                    self.drivers.append(Driver(self, self.getNode(homeId, driverData['nodeId']),  driverData))
                    print " +++ driver added +++"
                else :
                    self._log.write(LogLevel.Warning, self,"Zwave network allready loaded :{0}".format(f))

    def resetZwNetwork(self,  oldHomeId,  newHomeId):
        ctrl = self.GetDriver(oldHomeId)
        self.zwNetworks[newHomeId] = self.zwNetworks.pop(oldHomeId)
        self.zwNetworks[newHomeId]['configData']['controller']['fakeneighbors'] = {}
        nodes = []
        for node in self.zwNetworks[newHomeId]['configData']['nodes'] :
            if node['nodeid'] == ctrl._node.nodeId :
                nodes = [node]
                break
        self.zwNetworks[newHomeId]['configData']['nodes'] = nodes

    def getZwVersion(self, homeId):
        if homeId :
            if 'controller' in self.zwNetworks[homeId]['configData']:
                if 'zwversion' in self.zwNetworks[homeId]['configData']['controller']:
                    return self.zwNetworks[homeId]['configData']['controller']['zwversion']
            return ZWVERSION
        return ""

    def getSerialAPIVersion(self, homeId):
        if homeId :
            if 'controller' in self.zwNetworks[homeId]['configData']:
                if 'serialapiversion' in self.zwNetworks[homeId]['configData']['controller']:
                    return self.zwNetworks[homeId]['configData']['controller']['serialapiversion']
            return SERIALAPIVERSION
        return ""

    def getRFChipVersion(self, homeId):
        if homeId :
            if 'controller' in self.zwNetworks[homeId]['configData']:
                if 'rfchipversion' in self.zwNetworks[homeId]['configData']['controller']:
                    return self.zwNetworks[homeId]['configData']['controller']['rfchipversion']
            return RFCHIPVERSION
        return ""

    def getFakeNeighbors(self, homeId, nodeId):
        if homeId :
            if 'controller' in self.zwNetworks[homeId]['configData']:
                if 'fakeneighbors' in self.zwNetworks[homeId]['configData']['controller']:
                    if str(nodeId) in self.zwNetworks[homeId]['configData']['controller']['fakeneighbors']:
                        return self.zwNetworks[homeId]['configData']['controller']['fakeneighbors'][str(nodeId)]
            return []
        return []

    def getEmulNodeData(self, homeId, nodeId):
        if homeId :
            if 'nodes' in self.zwNetworks[homeId]['configData']:
                for n in  self.zwNetworks[homeId]['configData']['nodes']:
                    if 'nodeid' in n and n['nodeid'] == nodeId:
                        return n
        return { "nodeid" : nodeId,
                     "comment" : "Auto comment",
                     "failed" : False,
                     "timeoutwakeup" : 0,
                     "wakeupduration" : 0,
                     "pollingvalues" : [],
                     "cmdclssextraparams" : {}
                  }

    def matchHomeID(self, homeId):
        """Evalue si c'est bien un homeID, retourne le homeID ou None"""
        if type(homeId) in [long,  int] :
            return "0x%0.8x" %homeId
        homeIDFormat = r"^0x[0-9,a-f]{8}$"
        if re.match(homeIDFormat,  homeId.lower()) is not None :
            return homeId.lower()
        return None

    def addXmlNode(self, homeId, nodeId, xmlNode):
        for n in self._nodes:
            if n.homeId == homeId and n.nodeId == nodeId:
                self._log.write(LogLevel.Warning, self, "Node {0} on homeId {1} from xml config file allready exist, abording add.".format(nodeId,  homeId))
                return None
        node = Node(self,  homeId,  nodeId, xmlNode)
        self._nodes.append(node)
        self._log.write(LogLevel.Info, self, "Node {0} on homeId {1} added from xml config file.".format(nodeId,  homeId))

    def GetCommandClassId(self, cmdClass):
        return self.cmdClassRegistered.GetCommandClassId(cmdClass)

    def getNode(self, homeId, nodeId):
        for n in self._nodes:
            if (n.homeId == homeId or self.matchHomeID(n.homeId) == homeId) and n.nodeId == nodeId :
                return n
        return None

    def getNodesOfhomeId(self, homeId):
        """Return all nodes from zwave network"""
        retval = []
        for n in self._nodes:
            if (n.homeId == homeId or self.matchHomeID(n.homeId) == homeId) :
                retval.append(n)
        return retval

    def getListNodeId(self, homeId):
        listN = []
        for n in self._nodes:
            if n.homeId == homeId  :
                listN.append(n.nodeId)
        return listN

    def copyNode(self, node):
        """Copy a node object add it on manager list nodes and set it not include.
           Return the new node object.
        """
#        newNode = copy.copy(node)
#        newNode.homeId = 0
        nodeId = self.getFirstFreeNodeIdBeforeInclude()
        newNode = Node(self,  0,  nodeId, node.GetXmlData)
        newNode.ClearAddingNode()
        newNode.Reset()
        self._nodes.append(newNode)
        self._log.write(LogLevel.Info, self, "Manager create new node by copy node {0}.{1}.".format(node.homeId, node.nodeId))
        return newNode

    def getFirstFreeNodeIdBeforeInclude(self):
        """"Return the fisrt nodeId free to add node in manager list """
        listId = []
        for n in  self._nodes:
            if n.homeId == 0 :
                listId.append(n.nodeId )
        for id in range(1, 255):
            if id not in listId :
                break
        return id

    def includeNewNode(self, homeId, node):
        """Include a new node in zwave network"""
        ctrl = self.GetDriver(homeId)
        return ctrl.includeNode(node)

    def resetHomeId(self, oldHomeId, newHomeId):
        for n in self._nodes:
            if (n.homeId == oldHomeId or self.matchHomeID(n.homeId) == oldHomeId) :
                n.homeId = newHomeId

    def startDriver(self, homeId):
        if self.checkVirtualCom(homeId) :
            serialport = self.zwNetworks[homeId]['configData']['virtualcom']['ports']['emulator']
            if self.drivers:
                for driver in self.drivers:
                    if driver.serialport is None: # Object Driver not assigned and ready to set serialport
                        driver.setSerialport(serialport)
                        self._log.write(LogLevel.Info, self, "Added driver for controller {0}".format(serialport))
                        driver.Start()
                        return True
                    elif driver.serialport == serialport:
                        self._log.write(LogLevel.Warning, self, "Cannot add driver for controller {0} - driver already exists".format(serialport))
                        break
                self._log.write(LogLevel.Warning, self, "Cannot add driver for controller {0} - no emulate driver available".format(serialport))
            else:
                self._log.write(LogLevel.Info, Warning, "Cannot add driver for controller {0} - no emulate driver loaded".format(serialport))
        return False

    def GetDriver(self, homeId):
        for driver in self.drivers:
            if homeId == driver.homeId : return driver
        return None

    def IsSupportedCommandClasses(self,  clsId):
        return self.cmdClassRegistered.IsSupported(clsId)

    def SetProductDetails(self, node, manufacturerId, productType, productId):
        manufacturerName = "Unknown: id=%.4x"%manufacturerId
        productName = "Unknown: type=%.4x, id=%.4x"%(productType, productId)
        configPath = ""
        # Try to get the real manufacturer and product names
        manufacturer = self.manufacturers.getManufacturer(manufacturerId)
        if manufacturer:
            # Replace the id with the real name
            manufacturerName = manufacturer['name']
            # Get the product
            for p in manufacturer['products']:
                if (int(productId,  16) == int(p['id'], 16)) and (int(productType,  16) == int(p['type'],  16)):
                    productName = p['name']
                    configPath = p['config'] if 'config' in p else ""
        # Set the values into the node
        # Only set the manufacturer and product name if they are
        # empty - we don't want to overwrite any user defined names.
        if node.GetManufacturerName == "" :
            node.SetManufacturerName(manufacturerName )
        if node.GetProductName == "":
            node.SetProductName(productName)
        node.SetManufacturerId("%.4x"%manufacturerId)
        node.SetProductType("%.4x"%productType)
        node.SetProductId(  "%.4x"%productId )
        return configPath

"""
        # // Configuration
        void WriteConfig(uint32_t homeid)
        Options* GetOptions()
        # // Drivers
        bint AddDriver(string serialport)
        bint RemoveDriver(string controllerPath)
        uint8_t GetControllerNodeId(uint32_t homeid)
        uint8_t GetSUCNodeId(uint32_t homeid)
        bint IsPrimaryController(uint32_t homeid)
        bint IsStaticUpdateController(uint32_t homeid)
        bint IsBridgeController(uint32_t homeid)
        string GetLibraryVersion(uint32_t homeid)
        string GetLibraryTypeName(uint32_t homeid)
        int32_t GetSendQueueCount( uint32_t homeId )
        void LogDriverStatistics( uint32_t homeId )
        void GetDriverStatistics( uint32_t homeId, DriverData* data )
        void GetNodeStatistics( uint32_t homeId, uint8_t nodeid, NodeData* data )
        ControllerInterface GetControllerInterfaceType( uint32_t homeId )
        string GetControllerPath( uint32_t homeId )
        # // Network
        void TestNetworkNode( uint32_t homeId, uint8_t nodeId, uint32_t count )
        void TestNetwork( uint32_t homeId, uint32_t count )
        void HealNetworkNode( uint32_t homeId, uint32_t nodeId, bool _doRR )
        void HealNetwork( uint32_t homeId, bool doRR)
        # // Polling
        uint32_t GetPollInterval()
        void SetPollInterval(uint32_t milliseconds, bIntervalBetweenPolls)
        bint EnablePoll(ValueID& valueId, uint8_t intensity)
        bool DisablePoll(ValueID& valueId)
        bool isPolled(ValueID& valueId)
        void SetPollIntensity( ValueID& valueId, uint8_t intensity)
        uint8_t GetPollIntensity(ValueID& valueId)
        # // Node Information
        bool RefreshNodeInfo(uint32_t homeid, uint8_t nodeid)
        bool RequestNodeState(uint32_t homeid, uint8_t nodeid)
        bool RequestNodeDynamic( uint32_t homeId, uint8_t nodeId )
        bool IsNodeListeningDevice(uint32_t homeid, uint8_t nodeid)
        bool IsNodeFrequentListeningDevice( uint32_t homeId, uint8_t nodeId )
        bool IsNodeBeamingDevice( uint32_t homeId, uint8_t nodeId )
        bool IsNodeRoutingDevice(uint32_t homeid, uint8_t nodeid)
        bool IsNodeSecurityDevice( uint32_t homeId, uint8_t nodeId )
        uint32_t GetNodeMaxBaudRate(uint32_t homeid, uint8_t nodeid)
        uint8_t GetNodeVersion(uint32_t homeid, uint8_t nodeid)
        uint8_t GetNodeSecurity(uint32_t homeid, uint8_t nodeid)
        uint8_t GetNodeBasic(uint32_t homeid, uint8_t nodeid)
        uint8_t GetNodeGeneric(uint32_t homeid, uint8_t nodeid)
        uint8_t GetNodeSpecific(uint32_t homeid, uint8_t nodeid)
        string GetNodeType(uint32_t homeid, uint8_t nodeid)
        uint32_t GetNodeNeighbors(uint32_t homeid, uint8_t nodeid, uint8_t** nodeNeighbors)
        string GetNodeManufacturerName(uint32_t homeid, uint8_t nodeid)
        string GetNodeProductName(uint32_t homeid, uint8_t nodeid)
        string GetNodeName(uint32_t homeid, uint8_t nodeid)
        string GetNodeLocation(uint32_t homeid, uint8_t nodeid)
        string GetNodeManufacturerId(uint32_t homeid, uint8_t nodeid)
        string GetNodeProductType(uint32_t homeid, uint8_t nodeid)
        string GetNodeProductId(uint32_t homeid, uint8_t nodeid)
        void SetNodeManufacturerName(uint32_t homeid, uint8_t nodeid, string manufacturerName)
        void SetNodeProductName(uint32_t homeid, uint8_t nodeid, string productName)
        void SetNodeName(uint32_t homeid, uint8_t nodeid, string productName)
        void SetNodeLocation(uint32_t homeid, uint8_t nodeid, string location)
        void SetNodeOn(uint32_t homeid, uint8_t nodeid)
        void SetNodeOff(uint32_t homeid, uint8_t nodeid)
        void SetNodeLevel(uint32_t homeid, uint8_t nodeid, uint8_t level)
        bool IsNodeInfoReceived(uint32_t homeid, uint8_t nodeid)
        bool GetNodeClassInformation( uint32_t homeId, uint8_t nodeId, uint8_t commandClassId,
                          string *className, uint8_t *classVersion)
        bool IsNodeAwake(uint32_t homeid, uint8_t nodeid)
        bool IsNodeFailed(uint32_t homeid, uint8_t nodeid)
        string GetNodeQueryStage(uint32_t homeid, uint8_t nodeid)
        # // Values
        string GetValueLabel(ValueID& valueid)
        void SetValueLabel(ValueID& valueid, string value)
        string GetValueUnits(ValueID& valueid)
        void SetValueUnits(ValueID& valueid, string value)
        string GetValueHelp(ValueID& valueid)
        void SetValueHelp(ValueID& valueid, string value)
        uint32_t GetValueMin(ValueID& valueid)
        uint32_t GetValueMax(ValueID& valueid)
        bool IsValueReadOnly(ValueID& valueid)
        bool IsValueWriteOnly(ValueID& valueid)
        bool IsValueSet(ValueID& valueid)
        bool IsValuePolled( ValueID& valueid )
        bool GetValueAsBool(ValueID& valueid, bool* o_value)
        bool GetValueAsByte(ValueID& valueid, uint8_t* o_value)
        bool GetValueAsFloat(ValueID& valueid, float* o_value)
        bool GetValueAsInt(ValueID& valueid, int32_t* o_value)
        bool GetValueAsShort(ValueID& valueid, int16_t* o_value)
        bool GetValueAsRaw(ValueID& valueid, uint8_t** o_value, uint8_t* o_length )
        bool GetValueAsString(ValueID& valueid, string* o_value)
        bool GetValueListSelection(ValueID& valueid, string* o_value)
        bool GetValueListSelection(ValueID& valueid, int32_t* o_value)
        bool GetValueListItems(ValueID& valueid, vector[string]* o_value)
        bool SetValue(ValueID& valueid, bool value)
        bool SetValue(ValueID& valueid, uint8_t value)
        bool SetValue(ValueID& valueid, float value)
        bool SetValue(ValueID& valueid, int32_t value)
        bool SetValue(ValueID& valueid, int16_t value)
        bool SetValue(ValueID& valueid, uint8_t* value, uint8_t length)
        bool SetValue(ValueID& valueid, string value)
        bool SetValueListSelection(ValueID& valueid, string selecteditem)
        bool RefreshValue(ValueID& valueid)
        void SetChangeVerified(ValueID& valueid, bool verify)
        bool PressButton(ValueID& valueid)
        bool ReleaseButton(ValueID& valueid)
        bool GetValueFloatPrecision(ValueID& valueid, uint8_t* o_value)
        # // Climate Control
        uint8_t GetNumSwitchPoints(ValueID& valueid)
        bool SetSwitchPoint(ValueID& valueid, uint8_t hours, uint8_t minutes, uint8_t setback)
        bool RemoveSwitchPoint(ValueID& valueid, uint8_t hours, uint8_t minutes)
        bool ClearSwitchPoints(ValueID& valueid)
        bool GetSwitchPoint(ValueID& valueid, uint8_t idx, uint8_t* o_hours, uint8_t* o_minutes, int8_t* o_setback)
        # // SwitchAll
        void SwitchAllOn(uint32_t homeid)
        void SwitchAllOff(uint32_t homeid)
        # // Configuration Parameters
        bool SetConfigParam(uint32_t homeid, uint8_t nodeid, uint8_t param, uint32_t value, uint8_t size)
        void RequestConfigParam(uint32_t homeid, uint8_t nodeid, uint8_t aram)
        void RequestAllConfigParams(uint32_t homeid, uint8_t nodeid)
        # // Groups
        uint8_t GetNumGroups(uint32_t homeid, uint8_t nodeid)
        uint32_t GetAssociations(uint32_t homeid, uint8_t nodeid, uint8_t groupidx, uint8_t** o_associations)
        uint8_t GetMaxAssociations(uint32_t homeid, uint8_t nodeid, uint8_t groupidx)
        string GetGroupLabel(uint32_t homeid, uint8_t nodeid, uint8_t groupidx)
        void AddAssociation(uint32_t homeid, uint8_t nodeid, uint8_t groupidx, uint8_t targetnodeid)
        void RemoveAssociation(uint32_t homeid, uint8_t nodeid, uint8_t groupidx, uint8_t targetnodeid)
        bool AddWatcher(pfnOnNotification_t notification, void* context)
        bool RemoveWatcher(pfnOnNotification_t notification, void* context)
        # void NotifyWatchers(Notification*)
        # // Controller Commands
        void ResetController(uint32_t homeid)
        void SoftReset(uint32_t homeid)
        bool BeginControllerCommand(uint32_t homeid, ControllerCommand _command, pfnControllerCallback_t _callback, void* _context, bool _highPower, uint8_t _nodeId, uint8_t _arg )
        bool CancelControllerCommand(uint32_t homeid)
        # // Scene commands
        uint8_t GetNumScenes()
        uint8_t GetAllScenes(uint8_t** sceneIds)
        uint8_t CreateScene()
        void RemoveAllScenes( uint32_t _homeId )
        bool RemoveScene(uint8_t sceneId)
        bool AddSceneValue( uint8_t sceneId, ValueID& valueId, bool value)
        bool AddSceneValue( uint8_t sceneId, ValueID& valueId, uint8_t value)
        bool AddSceneValue( uint8_t sceneId, ValueID& valueId, float value )
        bool AddSceneValue( uint8_t sceneId, ValueID& valueId, int32_t value )
        bool AddSceneValue( uint8_t sceneId, ValueID& valueId, int16_t value )
        bool AddSceneValue( uint8_t sceneId, ValueID& valueId, string value )
        bool AddSceneValueListSelection( uint8_t sceneId, ValueID& valueId, string value )
        bool AddSceneValueListSelection( uint8_t sceneId, ValueID& valueId, int32_t value )
        bool RemoveSceneValue( uint8_t sceneId, ValueID& valueId )
        int SceneGetValues( uint8_t sceneId, vector[ValueID]* o_value )
        bool SceneGetValueAsBool( uint8_t sceneId, ValueID& valueId, bool* value )
        bool SceneGetValueAsByte( uint8_t sceneId, ValueID& valueId, uint8_t* o_value )
        bool SceneGetValueAsFloat( uint8_t sceneId, ValueID& valueId, float* o_value )
        bool SceneGetValueAsInt( uint8_t sceneId, ValueID& valueId, int32_t* o_value )
        bool SceneGetValueAsShort( uint8_t sceneId, ValueID& valueId, int16_t* o_value )
        bool SceneGetValueAsString( uint8_t sceneId, ValueID& valueId, string* o_value )
        bool SceneGetValueListSelection( uint8_t sceneId, ValueID& valueId, string* o_value )
        bool SceneGetValueListSelection( uint8_t sceneId, ValueID& valueId, int32_t* o_value )
        bool SetSceneValue( uint8_t sceneId, ValueID& valueId, bool value )
        bool SetSceneValue( uint8_t sceneId, ValueID& valueId, uint8_t value )
        bool SetSceneValue( uint8_t sceneId, ValueID& valueId, float value )
        bool SetSceneValue( uint8_t sceneId, ValueID& valueId, int32_t value )
        bool SetSceneValue( uint8_t sceneId, ValueID& valueId, int16_t value )
        bool SetSceneValue( uint8_t sceneId, ValueID& valueId, string value )
        bool SetSceneValueListSelection( uint8_t sceneId, ValueID& valueId, string value )
        bool SetSceneValueListSelection( uint8_t sceneId, ValueID& valueId, int32_t value )
        string GetSceneLabel( uint8_t sceneId )
        void SetSceneLabel( uint8_t sceneId, string value )
        bool SceneExists( uint8_t sceneId )
        bool ActivateScene( uint8_t sceneId )

"""


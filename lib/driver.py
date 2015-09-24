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
from ctrlemulator import OZWSerialEmul
import time
import threading

class ControllerInterface(EnumNamed):       # Specifies the controller's hardware interface 
    Unknown = 0
    Serial = 1          # Serial protocol
    Hid = 2             # Human interface device protocol

class DriverData(EnumNamed):
    m_SOFCnt = 0               # Number of SOF bytes received
    m_ACKWaiting = 0           # Number of unsolicited messages while waiting for an ACK
    m_readAborts = 0           # Number of times read were aborted due to timeouts
    m_badChecksum = 0          # Number of bad checksums
    m_readCnt = 0              # Number of messages successfully read
    m_writeCnt = 0             # Number of messages successfully sent
    m_CANCnt = 0               # Number of CAN bytes received
    m_NAKCnt = 0               # Number of NAK bytes received
    m_ACKCnt = 0               # Number of ACK bytes received
    m_OOFCnt = 0               # Number of bytes out of framing
    m_dropped = 0              # Number of messages dropped & not delivered
    m_retries = 0              # Number of messages retransmitted
    m_callbacks = 0            # Number of unexpected callbacks
    m_badroutes = 0            # Number of failed messages due to bad route response
    m_noack = 0                # Number of no ACK returned errors
    m_netbusy = 0              # Number of network busy/failure messages
    m_nondelivery = 0          # Number of messages not delivered to network
    m_routedbusy = 0           # Number of messages received with routed busy status
    m_broadcastReadCnt = 0     # Number of broadcasts read
    m_broadcastWriteCnt = 0    # Number of broadcasts sent

class ControllerCommand(EnumNamed):
    none = 0,                        # No command. */
    AddDevice = 1                    # Add a new device or controller to the Z-Wave network. */
    CreateNewPrimary = 2             # Add a new controller to the Z-Wave network. Used when old primary fails. Requires SUC. */
    ReceiveConfiguration = 3         # Receive Z-Wave network configuration information from another controller. */
    RemoveDevice = 4                 # Remove a device or controller from the Z-Wave network. */
    RemoveFailedNode = 5             # Move a node to the controller's failed nodes list. This command will only work if the node cannot respond. */
    HasNodeFailed = 6                # Check whether a node is in the controller's failed nodes list. */
    ReplaceFailedNode = 7            # Replace a non-responding node with another. The node must be in the controller's list of failed nodes for this command to succeed. */
    TransferPrimaryRole = 8          # Make a different controller the primary. */
    RequestNetworkUpdate = 9         # Request network information from the SUC/SIS. */
    RequestNodeNeighborUpdate = 10   # Get a node to rebuild its neighbour list.  This method also does RequestNodeNeighbors */
    AssignReturnRoute = 11           # Assign a network return routes to a device. */
    DeleteAllReturnRoutes = 12       # Delete all return routes from a device. */
    SendNodeInformation = 13         # Send a node information frame */
    ReplicationSend = 14             # Send information from primary to secondary */
    CreateButton = 15                # Create an id that tracks handheld button presses */
    DeleteButton = 16                # Delete id that tracks handheld button presses */

class ControllerState(EnumNamed):
    Normal = 0                         # No command in progress. */
    Starting = 1                       # The command is starting. */
    Cancel = 2                         # The command was cancelled. */
    Error = 3                          # Command invocation had error(s) and was aborted */
    Waiting = 4                        # Controller is waiting for a user action. */
    Sleeping = 5                       # Controller command is on a sleep queue wait for device. */
    InProgress = 6                     # The controller is communicating with the other device to carry out the command. */
    Completed = 7                      # The command has completed successfully. */
    Failed = 8                         # The command has failed. */
    NodeOK = 9                         # Used only with ControllerCommand_HasNodeFailed to indicate that the controller thinks the node is OK. */
    NodeFailed = 10                    # Used only with ControllerCommand_HasNodeFailed to indicate that the controller thinks the node has failed. */

class ControllerError(EnumNamed):
    none = 0
    ButtonNotFound = 1                # Button */
    NodeNotFound = 2                  # Button */
    NotBridge = 3                     # Button */
    NotSUC = 4                        # CreateNewPrimary */
    NotSecondary = 5                  # CreateNewPrimary */
    NotPrimary = 6                    # RemoveFailedNode, AddNodeToNetwork */
    IsPrimary = 7                     # ReceiveConfiguration */
    NotFound = 8                      # RemoveFailedNode */
    Busy = 9                          # RemoveFailedNode, RequestNetworkUpdate */
    Failed = 10                       # RemoveFailedNode, RequestNetworkUpdate */
    Disabled = 11                     # RequestNetworkUpdate error */
    Overflow = 12                     # RequestNetworkUpdate error */

class ControllerCaps(EnumNamed):
    Secondary = 0x01		         # The controller is a secondary. 
    OnOtherNetwork = 0x02		# The controller is not using its default HomeID. 
    SIS = 0x04        		           # There is a SUC ID Server on the network. 
    RealPrimary = 0x08       		# Controller was the primary before the SIS was added. 
    SUC = 0x10	                	#Controller is a static update controller.

class InitCaps(EnumNamed):
    Slave = 0x01	
    TimerSupport = 0x02	# Controller supports timers. */
    Secondary = 0x04		# Controller is a secondary. */
    SUC = 0x08		        # Controller is a static update controller. */
    
LibraryTypeNames = {
    0:"Unknown",			# library type 0
    1:"Static Controller",		# library type 1
    2:"Controller",       		# library type 2
    3:"Enhanced Slave",   		# library type 3
    4:"Slave",            		# library type 4
    5:"Installer",			# library type 5
    6:"Routing Slave",		# library type 6
    7:"Bridge Controller",    	# library type 7
    8:"Device Under Test"		# library type 8
    }
    
class MsgQueue(EnumNamed):
    Command = 0
    NoOp = 1
    Controller =2
    WakeUp = 3
    Send = 4
    Query = 5
    Poll = 6
    Count = 7	# Number of message queues
        
class MsgQueueCmd(EnumNamed):
    SendMsg = 0
##    QueryStageComplete = 1
    Controller = 2

class Driver:

    def __init__(self, manager, node,  data):
        self._manager = manager
        self.serialport = None
        self.clientConnected = False
        self.xmlData = data
        self._startTime = 0
        self._node = node
        self.m_nodes = {}
#        self.m_controller = FakeController(self.ProcessMsg, self._manager._stop)
        self.controller = None
        self.driverData = DriverData()
        # Create the message queue events
        self.m_msgQueue = {}
        for q in range(0, MsgQueue.Count -1):
            self.m_msgQueue[q] = []
        self.m_currentMsg = None
        self.m_transmitOptions =TRANSMIT_OPTION_ACK | TRANSMIT_OPTION_AUTO_ROUTE | TRANSMIT_OPTION_EXPLORE
        self.m_waitingForAck = False
        self.m_expectedCallbackId = 0
        self.m_expectedReply = 0
        self.m_expectedCommandClassId = 0
        self.m_expectedNodeId = 0
        self.handleMsg = threading.Thread(None, self.handleMessages, "th_Handle_Driver_{0}_Msg".format(self.homeId), (), {})
#        self.m_controller.start()
        self.running = False
        self._currentCtrlCommands = {}  #memorize callback informations with key zwave function
        self.handleMsg.start()
        print data

    _log = property(lambda self: self._manager._log)
    _stop = property(lambda self: self._manager._stop)
    homeId = property(lambda self: self.xmlData['homeId'])
    nodeId = property(lambda self: self.xmlData['nodeId'])
    commandClassId  = property(lambda self: 0x00) # 'COMMAND_CLASS_NO_OPERATION' 
    instance = property(lambda self: 0)
    index = property(lambda self: 0)
    genre = property(lambda self: 0)
    type = property(lambda self: 0)
    label = property(lambda self: "")
    units = property(lambda self: "")
    readOnly = property(lambda self: False)  #manager.IsValueReadOnly(v),
    GetTransmitOptions = property(lambda self: self.m_transmitOptions)
    IsInIncludeState = property(lambda self: True if FUNC_ID_ZW_ADD_NODE_TO_NETWORK in self._currentCtrlCommands and \
        (self._currentCtrlCommands[FUNC_ID_ZW_ADD_NODE_TO_NETWORK].crtlState in [ControllerState.Waiting, ControllerState.InProgress]) else False)
    
    def GetClassInformation(self):
        return {'name': 'COMMAND_CLASS_NO_OPERATION',  'id': 0x00}
    
    def getVal(self):
        return None

    def GetId(self):
        id = (self.nodeId << 24) | (self.genre << 22) | (self.commandClassId << 14) | (0 << 12) | (self.index << 4) | self.type
        id1 = (self.instance << 24)
        return (id1 << 32) | id

    def setSerialport(self, serialport):
        if self.xmlData: homeId = self._manager.matchHomeID(self.xmlData['homeId'])
        else: homeId = 'Unknown'
        if serialport is None and self.serialport is not None:
            self._log.write(LogLevel.Info, self, "  Unaffect controller {0} for homeId {1}".format(self.serialport,  homeId))
            self.serialport= None
        elif self.serialport is not None :
            self._log.write(LogLevel.Warning, self, "  Controller {0} allready affected, change to {1} (homeId {2})".format(self.serialport, serialport, homeId))
            self.serialport = serialport
        else :
            self._log.write(LogLevel.Info, self, "  Affect controller {0} with homeId to {1}".format(serialport, homeId))
            self.serialport = serialport

    def Start(self):
        if self.serialport is None :
            self._log.write(LogLevel.Warning, self, "  Controller is not affected, set serial port before start.")
            return False
        if self.Init() :
            self._startTime = time.time()
            self._log.write(LogLevel.Info, "Serial port {0} for emulation opened.".format(self.serialport))
#            time.sleep(.05)
#            self._log.write(LogLevel.Detail, self, "Start Init sequence simulation...")
#            time.sleep(.15)
#            homeIDName = self._manager.matchHomeID(self.xmlData['homeId'])
#            self._log.write(LogLevel.Info, self, "Received reply to FUNC_ID_ZW_MEMORY_GET_ID. Home ID = {0}.  Our node ID = {1}".format(homeIDName, self.xmlData['nodeId']))
#            time.sleep(.15)
#            self._log.write(LogLevel.Info, self, "Received reply to FUNC_ID_ZW_GET_CONTROLLER_CAPABILITIES:")
#            if self.xmlData['controllerCapabilities'] & ControllerCaps.SIS:
#                self._log.write( LogLevel.Info, self, "    There is a SUC ID Server (SIS) in this network." )
#                msg1 = "static update controller (SUC)" if (self.xmlData['controllerCapabilities'] & ControllerCaps.SUC) else "controller",
#                msg2 = " which is using a Home ID from another network" if (self.xmlData['controllerCapabilities'] & ControllerCaps.OnOtherNetwork) else ""
#                msg3 = " and was the original primary before the SIS was added." if (self.xmlData['controllerCapabilities'] & ControllerCaps.RealPrimary) else "." 
#                self._log.write( LogLevel.Info, self, "    The PC controller is an inclusion {0}{1}{2}".format(msg1, msg2, msg3))
#            else :
#                self._log.write( LogLevel.Info, self, "    There is no SUC ID Server (SIS) in this network." )
#                mgs1 = "secondary" if (self.xmlData['controllerCapabilities'] & ControllerCaps.Secondary) else "primary"
#                msg2 = " static update controller (SUC)" if (self.xmlData['controllerCapabilities'] & ControllerCaps.SUC) else " controller"
#                msg3 = " which is using a Home ID from another network." if (self.xmlData['controllerCapabilities'] & ControllerCaps.OnOtherNetwork) else "."
#                self._log.write( LogLevel.Info, self,  "    The PC controller is a {0}{1}{2}".format(msg1, msg2, msg3))
#            time.sleep(.15)
#            self._log.write(LogLevel.Info, self, "Received reply to FUNC_ID_SERIAL_API_GET_CAPABILITIES:")
#            self._log.write(LogLevel.Info, self, "    Xml config file Version:   {0}".format(self.xmlData['version']))
#            self._log.write(LogLevel.Info, self, "    Manufacturer ID:           0x%04d" %int(self._node.manufacturer['id'].split('x')[1]))
#            self._log.write(LogLevel.Info, self, "    Product Type:              0x%04d" %int(self._node.product['type'].split('x')[1]))
#            self._log.write(LogLevel.Info, self, "    Product ID:                0x%04d" %int(self._node.product['id'].split('x')[1]))
#            self._manager.SetDriverReady(self, True)
            self.loadNodes()

    def Init(self):
        self.m_waitingForAck = False
        # Open the controller
        self.controller = OZWSerialEmul(self.serialport, stop = self._stop,  callback = self.HandleMsg,  log = self._log )
#        self._log.write(LogLevel.Info, "  Opening controller {0}".format(self.serialport))
#        time.sleep(.02)        # Simulate serial connection sequence
#        self._log.write(LogLevel.Info, "Trying to open serial port {0}(attempt 1)".format(self.serialport))
#        time.sleep(.05)
        return True

    def loadNodes(self):
        nodes = self._manager.getListNodeId(self.homeId)
        self._log.write(LogLevel.Info, self, "{0} load known nodes from manager :".format(self._manager.matchHomeID(self.homeId)))
        for nodeId in nodes:
            node = self._manager.getNode(self.homeId, nodeId)
            if node :
                self.RegisterNode(node.nodeId,  True)
            else : print "load nodes error with nodeId {0}".format(nodeId)
    
    def GetNode(self, nodeId):
        return self._manager.getNode(self.homeId, nodeId)
    
    def GetFreeNextNodeId(self):
        """Return the next free nodeId to include new node"""
        maxId = 0
        print self.m_nodes.keys();
        for id in self.m_nodes.keys():
            if id > maxId : maxId=id
        return maxId + 1
        
    def includeNode(self, node):
        """Include a new node in zwave network, handle process message"""
        if self.IsInIncludeState :
            node.nodeId = self.GetFreeNextNodeId()
            node.homeId = self.homeId
            self.RegisterNode(node.nodeId, True)
            msg = Msg( "Request FUNC_ID_ZW_ADD_NODE_TO_NETWORK", self.nodeId,  REQUEST, FUNC_ID_ZW_ADD_NODE_TO_NETWORK, False)
            msg.Append(self._currentCtrlCommands[FUNC_ID_ZW_ADD_NODE_TO_NETWORK].callbackId) # TODO: Check if necessary in case of internal inclusion ?
            msg.Append(ADD_NODE_STATUS_ADDING_SLAVE)
            msg.Append(node.nodeId)
            msgTemp = node.getNodeInfoClass()
            print msgTemp
            for d in msgTemp: msg.Append(d) # Add node CommandClasses
            self._currentCtrlCommands[FUNC_ID_ZW_ADD_NODE_TO_NETWORK].setCtrlState(ControllerState.InProgress, ADD_NODE_STATUS_ADDING_SLAVE)
            self._currentCtrlCommands[FUNC_ID_ZW_ADD_NODE_TO_NETWORK].nodeId = node.nodeId
            self.SendMsg(msg, MsgQueue.Command)
            threading.Thread(None, self.waitForStepCmd, "th_handleWaitForStepCmd_ctrl_{0}.".format(self.homeId), (),
                    {'callback': self.terminateIncludeNode, 
                      'timing' : 0.5
                    }).start()
            return True
        else :
            self._log.write(LogLevel.Warning, node, "Controller {0} ins't in include state.".format(self.homeId))
            return False
            
    def terminateIncludeNode(self):
        if self.IsInIncludeState :
            if self._currentCtrlCommands[FUNC_ID_ZW_ADD_NODE_TO_NETWORK].ctrlStateNum == ADD_NODE_STATUS_ADDING_SLAVE :
                msg = Msg( "Request FUNC_ID_ZW_ADD_NODE_TO_NETWORK - ADD_NODE_STATUS_PROTOCOL_DONE", self.nodeId,  REQUEST, FUNC_ID_ZW_ADD_NODE_TO_NETWORK, False)
                msg.Append(self._currentCtrlCommands[FUNC_ID_ZW_ADD_NODE_TO_NETWORK].callbackId)
                msg.Append(ADD_NODE_STATUS_PROTOCOL_DONE)
                msg.Append(self._currentCtrlCommands[FUNC_ID_ZW_ADD_NODE_TO_NETWORK].nodeId) 
                msg.Append(TRANSMIT_COMPLETE_OK)
                self._currentCtrlCommands[FUNC_ID_ZW_ADD_NODE_TO_NETWORK].setCtrlState(ControllerState.InProgress, ADD_NODE_STATUS_PROTOCOL_DONE)
                self._currentCtrlCommands[FUNC_ID_ZW_ADD_NODE_TO_NETWORK].nodeId = 0
                self.SendMsg(msg, MsgQueue.Command)
            else :
                self._log.write(LogLevel.Warning, node, "Controller {0} have no node in inclusion process, state: {1}".format(self.homeId, self._currentCtrlCommands[FUNC_ID_ZW_ADD_NODE_TO_NETWORK].ctrlStateNum))
        else :
            self._log.write(LogLevel.Warning, node, "Controller {0} ins't in include state.".format(self.homeId))

    def setInInclusion(self): #TODO: add option to start function by type ADD_NODE_CONTROLLER, ADD_NODE_SLAVE, ADD_NODE_EXISTING
        """Put driver in inclusion mode"""
        if not self.IsInIncludeState :
            callbackId = 0x45 # TODO: generate number
            self.HandleAddNodeToNetworkRequest([REQUEST, FUNC_ID_ZW_ADD_NODE_TO_NETWORK, ADD_NODE_ANY | OPTION_HIGH_POWER, callbackId]) 
        
    def setOutInclusion(self): #TODO: add option to terminat function by type ADD_NODE_STOP_FAILED
        """Exit driver of inclusion mode"""
        if self.IsInIncludeState :
            callbackId = 0x45 # TODO: generate number
            self.HandleAddNodeToNetworkRequest([REQUEST, FUNC_ID_ZW_ADD_NODE_TO_NETWORK, ADD_NODE_STOP | OPTION_HIGH_POWER, callbackId]) 

    def SendMsg(self, _msg,  _queue ):
    # Queue a message to be sent to the Z-Wave PC Interface
        item = MsgQueueItem()
        item.m_command = MsgQueueCmd.SendMsg
        item.m_msg = _msg
        item.m_nodeId = _msg.GetTargetNodeId # TODO: dans la lib openzwave cette ligne n'existe pas !! ??
        _msg.Finalize()
        node = self.GetNode(_msg.GetTargetNodeId)
        if node is not None:
            security = node.GetCommandClass(self._manager.GetCommandClassId('COMMAND_CLASS_SECURITY'))
            if security is not None:
                cc = node.GetCommandClass(_msg.GetSendingCommandClass())
                if cc and cc.IsSecured :
                    self._log.write(LogLevel.Detail, node, "Encrypting Message For Command Class {0}".format(cc.GetCommandClassName))
                    security.SendMsg(_msg)
                    ReleaseNodes()
                    return
        self._log.write(LogLevel.Detail, node, "Queuing ({0}) {1}".format(MsgQueue().getName(_queue), _msg.GetAsString()))
        self.m_msgQueue[_queue].append(item)

    def RegisterNode(self, _nodeId, newNode):
        """Queue a node to be interrogated for its setup details"""
        #Delete any existing node and replace it with a new one
        if _nodeId in self.m_nodes:
            # Remove the original node
            del (self.m_nodes[_nodeId])
        # Add the new node
        self.m_nodes[_nodeId] = self.GetNode(_nodeId)
        if newNode == True : self.m_nodes[_nodeId].SetAddingNode()
        self._log.write(LogLevel.Info, self,  "Registered Node {0} in controller {1}. New Node: {2} ({3})".format(_nodeId,  self._manager.matchHomeID(self.homeId),
                            self.m_nodes[_nodeId].IsAddingNode, newNode))

    def HandleMsg(self, buffer):
        """Handle data read from the serial port"""

        if not buffer:
            # Nothing to read
            return False
        type = buffer[0]
        self.clientConnected = True
        if type == SOF:
            self.driverData.m_SOFCnt += 1
            if self.m_waitingForAck:
                # This can happen on any normal network when a transmission overlaps an unexpected
                # reception and the data in the buffer doesn't contain the ACK. The controller will
                # notice and send us a CAN to retransmit.
                self._log.write(LogLevel.Detail, "Unsolicited message received while waiting for ACK." )
                self.m_ACKWaiting +=1
            # Read the length byte.  Keep trying until we get it.
            try :
                size = buffer[1]
            except :
                self._log.write(LogLevel.Warning, "WARNING: don't finding the length byte...aborting frame read")
                self.driverData.m_readAborts +=1
                return
            try :
                data = buffer[2:size]
            except :
                self._log.write(LogLevel.Warning, "WARNING: Can't read the rest of the frame...aborting frame read" );
                self.driverData.m_readAborts +=1
                return
            # Log the data
            nodeId = self.NodeFromMessage(buffer)
            if self.m_currentMsg is not None and nodeId == 0:
                nodeId = self.m_currentMsg.GetTargetNodeId
            node = self.GetNode(nodeId)
            if node is None: node = self
            self._log.write(LogLevel.Detail, node, "  Received: {0}".format(self.controller.formatHex(buffer)))
            # Verify checksum
            checksum = 0xff
            for d1 in buffer[1:size + 1]:
                checksum ^= d1
            if buffer[size + 1] == checksum:
                # Checksum correct - send ACK
                self._log.write(LogLevel.Debug, node, "SOF message correct checksum - sending ACK" )
                self.controller.writeHex([ACK])
                self.driverData.m_readCnt =+ 1
                # Process the received message
                self.ProcessMsg(buffer[2:])
            else:
                self._log.write(LogLevel.Warning, node, "WARNING: Checksum incorrect - sending NAK" )
                self.driverData.m_badChecksum += 1
                self.controller.writeHex([NAK])
#                m_controller->Purge()
        elif type == CAN:
            # This is the other side of an unsolicited ACK. As mentioned there if we receive a message
            # just after we transmitted one, the controller will notice and tell us to retransmit here.
            # Don't increment the transmission counter as it is possible the message will never get out
            # on very busy networks with lots of unsolicited messages being received. Increase the amount
            # of retries but only up to a limit so we don't stay here forever.
            node = self.GetNode(self.m_currentMsg.GetTargetNodeId)
            if node is None: node = self
            self._log.write(LogLevel.Detail, node, "CAN received...triggering resend" );
            self.driverData.m_CANCnt += 1
            if self.m_currentMsg is not None:
                self.m_currentMsg.m_sendAttempts += 1
            else:
                self._log.write(LogLevel.Warning, self, "m_currentMsg was NULL when trying to set MaxSendAttempts" );
#            WriteMsg( "CAN" )
        elif type == NAK:
            if self.m_currentMsg is not None:            
                node = self.GetNode(self.m_currentMsg.GetTargetNodeId)
            else : node = self
            self._log.write(LogLevel.Warning, node, "WARNING: NAK received...triggering resend" );
            self.driverData.m_NAKCnt += 1
        elif type == ACK:
            self.driverData.m_ACKCnt += 1
            self.m_waitingForAck = False
            if self.m_currentMsg is None:
                self._log.write(LogLevel.StreamDetail, self, "  ACK received" );
            else:
                node = self.GetNode(self.m_currentMsg.GetTargetNodeId)
                self._log.write(LogLevel.StreamDetail, node, "  ACK received CallbackId 0x%.2x Reply 0x%.2x"%(self.m_expectedCallbackId, self.m_expectedReply))
                self.RemoveCurrentMsg()
        else :
            self._log.write(LogLevel.Warning, "WARNING: Out of frame flow! (0x%.2x).  Sending NAK.", buffer[0] );
            self.driverData.m_OOFCnt += 1
            self.controller.writeHex([NAK])
        return True

        
    def ProcessMsg(self, _data):
        """Process data received from the Z-Wave PC interface"""
        print "******************************** ProcessMsg ********************************"
        self._log.write(LogLevel.Debug, self, "Processing Msg : [{0}]".format(self.controller.formatHex(_data)))
        handleCallback = True
        if self.m_currentMsg is None:
            nodeId = 0
            node =None
        else :
            nodeId = self.m_currentMsg.GetTargetNodeId
            try :
                node = self.m_nodes[nodeId]
            except :
                nodeId = 0
                node =None
        type = _data[0]
        function = _data[1]
        self._log.write(LogLevel.Debug, self, 'Function : {0} ({1})'.format(getFuncName(function), self.controller.formatHex([function])))
        if REQUEST == type:
            if function == FUNC_ID_SERIAL_API_GET_INIT_DATA:
                    self._log.write(LogLevel.Detail, "" )
                    self.HandleSerialAPISetInitDataResponse()
            elif function ==  FUNC_ID_ZW_GET_CONTROLLER_CAPABILITIES:
                self._log.write(LogLevel.Detail, "" )
                self.HandleSetControllerCapabilitiesResponse()
            elif function ==  FUNC_ID_SERIAL_API_GET_CAPABILITIES:
                self._log.write(LogLevel.Detail, "" )
                self.HandleSetSerialAPICapabilitiesResponse()
            elif function ==  FUNC_ID_SERIAL_API_SOFT_RESET:
                self._log.write(LogLevel.Detail, "" )
                self.HandleSerialAPISoftResetResponse( _data )
            elif function ==  FUNC_ID_ZW_SEND_DATA:
                self.HandleSendDataResponse( _data, False )
                handleCallback = False			# Skip the callback handling - a subsequent FUNC_ID_ZW_SEND_DATA request will deal with that
            elif function ==  FUNC_ID_ZW_GET_VERSION:
                self._log.write(LogLevel.Detail, "" )
                self.HandleSetVersionResponse()
            elif function ==  FUNC_ID_ZW_GET_RANDOM:
                self._log.write(LogLevel.Detail, "" )
                self.HandleSetRandomResponse( _data )
            elif function ==  FUNC_ID_ZW_MEMORY_GET_ID:
                self._log.write(LogLevel.Detail, "" )
                self.HandleMemorySetIdResponse()
            elif function ==  FUNC_ID_ZW_GET_NODE_PROTOCOL_INFO:
                self._log.write(LogLevel.Detail, "" )
                self.HandleSetNodeProtocolInfoResponse( _data )
            elif function ==  FUNC_ID_ZW_REPLICATION_SEND_DATA:
                self.HandleSendDataResponse( _data, true )
                handleCallback = False;			# Skip the callback handling - a subsequent FUNC_ID_ZW_REPLICATION_SEND_DATA request will deal with that
            elif function ==  FUNC_ID_ZW_ASSIGN_RETURN_ROUTE:
                self._log.write(LogLevel.Detail, "" )
                if not self.HandleAssignReturnRouteRequest( _data ):
                    m_expectedCallbackId = _data[2] 	# The callback message won't be coming, so we force the transaction to complete
                    m_expectedReply = 0
                    m_expectedCommandClassId = 0
                    m_expectedNodeId = 0
            elif function ==  FUNC_ID_ZW_DELETE_RETURN_ROUTE:
                self._log.write(LogLevel.Detail, "" )
                if not self.HandleDeleteReturnRouteRequest( _data ):
                    self.m_expectedCallbackId = _data[2]		# The callback message won't be coming, so we force the transaction to complete
                    self.m_expectedReply = 0
                    self.m_expectedCommandClassId = 0
                    self.m_expectedNodeId = 0
            elif function ==  FUNC_ID_ZW_ENABLE_SUC:
                self._log.write(LogLevel.Detail, "" )
                HandleEnableSUCResponse( _data )
            elif function ==  FUNC_ID_ZW_REQUEST_NETWORK_UPDATE:
                self._log.write(LogLevel.Detail, "" )
                if not self.HandleNetworkUpdateResponse( _data ):
                    m_expectedCallbackId = _data[2]	# The callback message won't be coming, so we force the transaction to complete
                    m_expectedReply = 0
                    m_expectedCommandClassId = 0
                    m_expectedNodeId = 0
            elif function ==  FUNC_ID_ZW_SET_SUC_NODE_ID:
                self._log.write(LogLevel.Detail, "" )
                HandleSetSUCNodeIdResponse( _data )
            elif function ==  FUNC_ID_ZW_GET_SUC_NODE_ID:
                self._log.write(LogLevel.Detail, "" )
                self.HandleSetSUCNodeIdResponse()
            elif function ==  FUNC_ID_ZW_REQUEST_NODE_INFO:
                self._log.write(LogLevel.Detail, "" )
                self.HandleRequestNodeInfo(_data)
                if( _data[2] ):
                    self._log.write(LogLevel.Info, node, "FUNC_ID_ZW_REQUEST_NODE_INFO Request successful." )
                else:
                    self._log.write(LogLevel.Info, node, "FUNC_ID_ZW_REQUEST_NODE_INFO Request failed." )
            elif function ==  FUNC_ID_ZW_ADD_NODE_TO_NETWORK:
                self._log.write(LogLevel.Detail, "" )
                self.HandleAddNodeToNetworkRequest(_data)
            elif function ==  FUNC_ID_ZW_REMOVE_FAILED_NODE_ID:
                self._log.write(LogLevel.Detail, "" )
                if not HandleRemoveFailedNodeResponse( _data ):
                    m_expectedCallbackId = _data[2]	# The callback message won't be coming, so we force the transaction to complete
                    m_expectedReply = 0
                    m_expectedCommandClassId = 0
                    m_expectedNodeId = 0
            elif function ==  FUNC_ID_ZW_IS_FAILED_NODE_ID:
                self._log.write(LogLevel.Detail, "" )
                HandleIsFailedNodeResponse( _data )
            elif function ==  FUNC_ID_ZW_REPLACE_FAILED_NODE:
                self._log.write(LogLevel.Detail, "" )
                if not HandleReplaceFailedNodeResponse( _data ):
                    m_expectedCallbackId = _data[2]	# The callback message won't be coming, so we force the transaction to complete
                    m_expectedReply = 0
                    m_expectedCommandClassId = 0
                    m_expectedNodeId = 0
            elif function ==  FUNC_ID_ZW_GET_ROUTING_INFO:
                self._log.write(LogLevel.Detail, "" )
                self.HandleSetRoutingInfoResponse( _data )
            elif function ==  FUNC_ID_ZW_R_F_POWER_LEVEL_SET:
                self._log.write(LogLevel.Detail, "" )
                HandleRfPowerLevelSetResponse( _data )
            elif function ==  FUNC_ID_ZW_READ_MEMORY:
                self._log.write(LogLevel.Detail, "" )
                HandleReadMemoryResponse( _data )
            elif function ==  FUNC_ID_SERIAL_API_SET_TIMEOUTS:
                self._log.write(LogLevel.Detail, "" )
                self.HandleSerialApiSetTimeoutsResponse( _data )
            elif function ==  FUNC_ID_MEMORY_GET_BYTE:
                self._log.write(LogLevel.Detail, "" )
                HandleMemoryGetByteResponse( _data )
            elif function ==  FUNC_ID_ZW_GET_VIRTUAL_NODES:
                self._log.write(LogLevel.Detail, "" )
                HandleGetVirtualNodesResponse( _data )
            elif function ==  FUNC_ID_ZW_SET_SLAVE_LEARN_MODE:
                self._log.write(LogLevel.Detail, "" )
                if not HandleSetSlaveLearnModeResponse( _data ):
                    m_expectedCallbackId = _data[2]	# The callback message won't be coming, so we force the transaction to complete
                    m_expectedReply = 0
                    m_expectedCommandClassId = 0
                    m_expectedNodeId = 0
            elif function ==  FUNC_ID_ZW_SEND_SLAVE_NODE_INFO:
                self._log.write(LogLevel.Detail, "" )
                if not HandleSendSlaveNodeInfoResponse( _data ):
                    m_expectedCallbackId = _data[2]	# The callback message won't be coming, so we force the transaction to complete
                    m_expectedReply = 0
                    m_expectedCommandClassId = 0
                    m_expectedNodeId = 0
            elif function ==  FUNC_ID_ZW_SEND_NODE_INFORMATION:
                self._log.write(LogLevel.Detail, "" )
                self.HandleNodeInformationResponse( _data )
            elif function ==  FUNC_ID_ZW_REQUEST_NODE_NEIGHBOR_UPDATE_OPTIONS:
                self._log.write(LogLevel.Detail, "" )
                self.HandleNodeNeighborUpdateResponse( _data )
            else:
                self._log.write(LogLevel.Detail, "" )
                self._log.write(LogLevel.Info, "**TODO: handle request for 0x%.2x** Please report this message."%function)
        elif RESPONSE == type:
                if function ==  FUNC_ID_APPLICATION_COMMAND_HANDLER:
                    self._log.write(LogLevel.Detail, "" )
                    HandleApplicationCommandHandlerRequest( _data )
                elif function ==  FUNC_ID_ZW_SEND_DATA:
                    HandleSendDataRequest( _data, False )
                elif function ==  FUNC_ID_ZW_REPLICATION_COMMAND_COMPLETE:
                    if m_controllerReplication:
                        self._log.write(LogLevel.Detail, "" )
                        m_controllerReplication.SendNextData()
                elif function ==  FUNC_ID_ZW_REPLICATION_SEND_DATA:
                    HandleSendDataRequest( _data, true )
                elif function ==  FUNC_ID_ZW_ASSIGN_RETURN_ROUTE:
                    self._log.write(LogLevel.Detail, "" )
                    HandleAssignReturnRouteRequest( _data )
                elif function ==  FUNC_ID_ZW_DELETE_RETURN_ROUTE:
                    self._log.write(LogLevel.Detail, "" )
                    HandleDeleteReturnRouteRequest( _data )
                elif function ==  FUNC_ID_ZW_REQUEST_NODE_NEIGHBOR_UPDATE:
                    pass
                elif function ==  FUNC_ID_ZW_REQUEST_NODE_NEIGHBOR_UPDATE_OPTIONS:
                    self._log.write(LogLevel.Detail, "" )
                    HandleNodeNeighborUpdateRequest( _data )
                elif function ==  FUNC_ID_ZW_APPLICATION_UPDATE:
                    self._log.write(LogLevel.Detail, "" )
                    handleCallback = not HandleApplicationUpdateRequest( _data )
                elif function ==  FUNC_ID_ZW_REMOVE_NODE_FROM_NETWORK:
                    self._log.write(LogLevel.Detail, "" )
                    HandleRemoveNodeFromNetworkRequest( _data )
                elif function ==  FUNC_ID_ZW_CREATE_NEW_PRIMARY:
                    self._log.write(LogLevel.Detail, "" )
                    HandleCreateNewPrimaryRequest( _data )
                elif function ==  FUNC_ID_ZW_CONTROLLER_CHANGE:
                    self._log.write(LogLevel.Detail, "" )
                    HandleControllerChangeRequest( _data )
                elif function ==  FUNC_ID_ZW_SET_LEARN_MODE:
                    self._log.write(LogLevel.Detail, "" )
                    HandleSetLearnModeRequest( _data )
                elif function ==  FUNC_ID_ZW_REQUEST_NETWORK_UPDATE:
                    self._log.write(LogLevel.Detail, "" )
                    HandleNetworkUpdateRequest( _data )
                elif function ==  FUNC_ID_ZW_REMOVE_FAILED_NODE_ID:
                    self._log.write(LogLevel.Detail, "" )
                    HandleRemoveFailedNodeRequest( _data )
                elif function ==  FUNC_ID_ZW_REPLACE_FAILED_NODE:
                    self._log.write(LogLevel.Detail, "" )
                    HandleReplaceFailedNodeRequest( _data )
                elif function ==  FUNC_ID_ZW_SET_SLAVE_LEARN_MODE:
                    self._log.write(LogLevel.Detail, "" )
                    HandleSetSlaveLearnModeRequest( _data )
                elif function ==  FUNC_ID_ZW_SEND_SLAVE_NODE_INFO:
                    self._log.write(LogLevel.Detail, "" )
                    HandleSendSlaveNodeInfoRequest( _data )
                elif function ==  FUNC_ID_APPLICATION_SLAVE_COMMAND_HANDLER:
                    self._log.write(LogLevel.Detail, "" )
                    HandleApplicationSlaveCommandRequest( _data )
                elif function ==  FUNC_ID_PROMISCUOUS_APPLICATION_COMMAND_HANDLER:
                    self._log.write(LogLevel.Detail, "" )
                    HandlePromiscuousApplicationCommandHandlerRequest( _data )
                elif function ==  FUNC_ID_ZW_SET_DEFAULT:
                    self._log.write(LogLevel.Detail, "" )
                    HandleSerialAPIResetRequest( _data )
                else:
                    self._log.write(LogLevel.Detail, "" )
                    self._log.write(LogLevel.Info, "**TODO: handle response for 0x%.2x** Please report this message."%function )

        # Generic callback handling
#        if handleCallback:
#            if self.m_expectedCallbackId or self.m_expectedReply :
#                if self.m_expectedCallbackId :
#                    if self.m_expectedCallbackId == _data[2] :
#                        self._log.write(LogLevel.Detail, node, "  Expected callbackId was received" )
#                        self.m_expectedCallbackId = 0
#                if self.m_expectedReply :
#                    if self.m_expectedReply == _data[1] :
#                        if self.m_expectedCommandClassId and (self.m_expectedReply == FUNC_ID_APPLICATION_COMMAND_HANDLER ) :
#                            if self.m_expectedCallbackId == 0 and self.m_expectedCommandClassId == _data[5] and self.m_expectedNodeId == _data[3]:
#                                self._log.write(LogLevel.Detail, node, "  Expected reply and command class was received" )
#                                self.m_waitingForAck = False
#                                self.m_expectedReply = 0
#                                self.m_expectedCommandClassId = 0
#                                self.m_expectedNodeId = 0
#                        else:
#                            if self.IsExpectedReply( _data[3] ):
#                                self._log.write(LogLevel.Detail, node, "  Expected reply was received" )
#                                self.m_expectedReply = 0
#                                self.m_expectedNodeId = 0
#                if not (self.m_expectedCallbackId or self.m_expectedReply):
#                    self._log.write(LogLevel.Detail, node, "  Message transaction complete" )
#                    self._log.write(LogLevel.Detail, "" )
        self.RemoveCurrentMsg()  # TODO: Not clearly handle for the momment so curentMsg is allways removed

    def RemoveCurrentMsg(self):
        """Delete the current message"""
        if self.m_currentMsg is not None:
            self._log.write(LogLevel.Detail, self.GetNode(self.m_currentMsg.GetTargetNodeId), "Removing current message")
            self.m_currentMsg = None
        else :
            self._log.write(LogLevel.Detail, self,  "No current message to remove")
        self.m_expectedCallbackId = 0
        self.m_expectedCommandClassId = 0
        self.m_expectedNodeId = 0
        self.m_expectedReply = 0
        self.m_waitingForAck = False

    def handleMessages(self):
        self.running = True
        cpt = 0
        print "+++++++++++++ handleMessages Started ++++++++++++++/n"
        while not self._stop.isSet() and self.running:
            if self.m_currentMsg is None:
                for queue in self.m_msgQueue:
                    if len(self.m_msgQueue[queue]) != 0 :
                        delM = []
                        for msgQ in self.m_msgQueue[queue]:
                            if msgQ.m_command == MsgQueueCmd.SendMsg :
                                if self.clientConnected :
                                    self._log.write(LogLevel.Detail, self, "Queue {0}, Send message to Node {1} : {2}".format(MsgQueue().getName(queue), msgQ.m_nodeId,  msgQ.m_msg.GetAsString()))
                                    self.m_currentMsg = msgQ.m_msg
                                    self.controller.writeHex(msgQ.m_msg.m_buffer)
                                else : 
                                    self._log.write(LogLevel.Detail, self, "No Client connected don't send message from Queue {0}, to Node {1} : {2}".format(MsgQueue().getName(queue), msgQ.m_nodeId,  msgQ.m_msg.GetAsString()))
                                delM.append(msgQ)
                                cpt = 0
                                break
                        for d in delM:
                            self.m_msgQueue[queue].remove(d)
            cpt += 1
            self._stop.wait(.01)
            if cpt == 500 : 
                cpt = 0
                print "Wait for message to send...."
        self._stop.set()
        print "HandleMessage terminate."

    def NodeFromMessage(self,  buffer):
        """See if we can get node from incoming message data"""
        nodeId = 0
        if buffer[1] >= 5 :
            if buffer[3] == FUNC_ID_APPLICATION_COMMAND_HANDLER : nodeId = buffer[5]
            elif buffer[3] == FUNC_ID_ZW_APPLICATION_UPDATE : nodeId = buffer[5]
        return nodeId
        
    def HandleSetVersionResponse(self):
        #[0x01, 0x10, 0x01, 0x15, 0x5a, 0x2d, 0x57, 0x61, 0x76, 0x65, 0x20, 0x32, 0x2e, 0x37, 0x38, 0x00, 0x01, 0x9b]
        msg = Msg( "Response to ZW_GET_VERSION", self.nodeId,  RESPONSE, FUNC_ID_ZW_GET_VERSION, False)
        for  c in self._manager.getZwVersion(self.homeId): msg.Append(ord(c))
        msg.Append(0)
        msg.Append(1) # LibraryType 1 = Static Controller
        self.SendMsg(msg, MsgQueue.NoOp)
        
    def HandleMemorySetIdResponse(self):
        #[0x01, 0x08, 0x01, 0x20, 0x01, 0x4d, 0x0f, 0x18, 0x01, 0x8c]
        msg = Msg( "Response to ZW_MEMORY_GET_ID", self.nodeId,  RESPONSE, FUNC_ID_ZW_MEMORY_GET_ID, False)
        msg.Append((self.homeId & 0xff000000)>>24)
        msg.Append((self.homeId & 0x00ff0000)>>16)
        msg.Append((self.homeId & 0x0000ff00)>>8)
        msg.Append((self.homeId & 0x000000ff))
        msg.Append(self.nodeId)
        self.SendMsg(msg, MsgQueue.NoOp)
        
    def HandleSetControllerCapabilitiesResponse(self):
        #[0x01, 0x04, 0x01, 0x05, 0x1c, 0xe3]
        msg = Msg( "Response to GET_CONTROLLER_CAPABILITIES", self.nodeId,  RESPONSE, FUNC_ID_ZW_GET_CONTROLLER_CAPABILITIES, False)
        msg.Append(self.xmlData['controllerCapabilities'])
        self.SendMsg(msg, MsgQueue.NoOp)
                
    def HandleSetSerialAPICapabilitiesResponse(self):
        #[0x01, 0x2b, 0x01, 0x07, 0x03, 0x07, 0x00, 0x86, 0x00, 0x02, 0x00, 0x01,     0xfe, 0x80, 0xfe, 0x88, 0x0f, 0x00, 0x00, 0x00, 0xfb, 0x97, 0x7f, 0x82, 0x07, 0x00, 0x00, 0x80, 0x00, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xc2]
        msg = Msg( "Response to SERIAL_API_GET_CAPABILITIES", self.nodeId,  RESPONSE, FUNC_ID_SERIAL_API_GET_CAPABILITIES, False)
        sAPIVers = self._manager.getSerialAPIVersion(self.homeId)
        msg.Append(sAPIVers[0])
        msg.Append(sAPIVers[1])
        manufacturerId = self._node.manufacturer['id']
        print manufacturerId
        msg.Append((manufacturerId & 0x0000ff00)>>8)
        msg.Append((manufacturerId & 0x000000ff))
        productType = self._node.product['type']
        msg.Append((productType & 0x0000ff00)>>8)
        msg.Append((productType & 0x000000ff))
        productId = self._node.product['id']
        msg.Append((productId & 0x0000ff00)>>8)
        msg.Append((productId & 0x000000ff))
        # TODO: Add APIMask, don't what exactly mean !!"
        for i in [ 0xfe, 0x80, 0xfe, 0x88, 0x0f, 0x00, 0x00, 0x00, 0xfb, 0x97, 0x7f, 0x82, 0x07, 0x00, 0x00, 0x80, 0x00, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]:
            msg.Append(i)
        self.SendMsg(msg, MsgQueue.NoOp)
                
    def HandleSetSUCNodeIdResponse(self):
        # [0x01, 0x04, 0x01, 0x56, 0x01, 0xad]
        msg = Msg( "Response to GET_SUC_NODE_ID", self.nodeId,  RESPONSE, FUNC_ID_ZW_GET_SUC_NODE_ID, False)
        msg.Append(self.nodeId)
        self.SendMsg(msg, MsgQueue.NoOp)
        
    def HandleSetRandomResponse(self, _data):
        #[0x01, 0x25, 0x01, 0x1c, 0x01, 0x20, 0x05, 0x94, 0x65, 0xf7, 0xa4, 0x34, 0x6d, 0x73, 0xc1, 0x3a, 0x59, 0x30, 0x23, 0xf6, 0x2d, 0x1a, 0x97, 0xce, 0xaf, 0x51, 0xb0, 0xe5, 0x9d, 0xf6, 0x9c, 0x4d, 0x39, 0x72, 0x0c, 0xb9, 0x8c, 0xe0, 0xc1]
        # 0x01, 0x25, 0x01, 0x1c, 0x01, 0x20, 0x75, 0x78, 0x4b, 0xf5, 0x07, 0xaa, 0x97, 0xae, 0xdc, 0x12, 0x87, 0x5a, 0xff, 0xa8, 0x1f, 0xf7, 0xda, 0xf3, 0x10, 0xa6, 0x60, 0x48, 0x0a, 0xf1, 0xed, 0xbb, 0x27, 0xb3, 0x90, 0x37, 0x08, 0xba, 0xf6
        # 0x01, 0x23, 0x01, 0x1c, 0xec, 0xc5, 0x3a, 0x82, 0xf9, 0x11, 0xfb, 0x3b, 0xf8, 0xd5, 0xf9, 0x2e, 0x9b, 0x56, 0x72, 0x12, 0xd5, 0x21, 0x4b, 0x64, 0x51, 0xef, 0xc9, 0x26, 0x11, 0x90, 0x5c, 0x0c, 0x46, 0x9a, 0xe1, 0x9f, 0xd6
        # 0x01, 0x23, 0x01, 0x1c, 0x91, 0x91, 0xa2, 0x2c, 0x08, 0x31, 0x49, 0x88, 0x1a, 0x3b, 0x74, 0xdc, 0x7d, 0xd1, 0x12, 0x49, 0xcf, 0x49, 0xfd, 0x4d, 0x94, 0xb9, 0xf1, 0xa6, 0xb1, 0x81, 0x8f, 0x74, 0x02, 0x42, 0xe3, 0x00, 0xed
        from random import randint
        msg = Msg( "Response to ZW_GET_RANDOM", self.nodeId,  RESPONSE, FUNC_ID_ZW_GET_RANDOM, False)
        msg.Append(_data[2]) # nodeId
        msg.Append(0x20) # 32 bytes
        for i in range(32) :  # Generate 32 bytes random
            msg.Append(randint(0, 255))
        self.SendMsg(msg, MsgQueue.NoOp)
        
    def HandleSerialAPISetInitDataResponse(self):
        #[0x01, 0x25, 0x01, 0x02, 0x05, 0x08, 0x1d, 0xe9, 0x3f, 0x0e, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x03, 0x01, 0x13]
                                                         #0xe9, 0x3f, 0x0e, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
        msg = Msg( "Response to SERIAL_API_GET_INIT_DATA", self.nodeId,  RESPONSE, FUNC_ID_SERIAL_API_GET_INIT_DATA, False)
        msg.Append(5) # Version of the Serial API used by the controller.
        msg.Append(self.xmlData['apiCapabilities'])
        msg.Append(NUM_NODE_BITFIELD_BYTES)
        tab = []
        for i in range(29): tab.append(0x00) # Bit filed node ID
        nodes = self._manager.getListNodeId(self.homeId)
        for n in nodes : tab[(n -1)  //8] |= 0x01 << ((n-1) % 8)
        for i in tab: msg.Append(i)
        # Add presumed RF Zwave chip  version
        chipVers = self._manager.getRFChipVersion(self.homeId)
        msg.Append(chipVers[0])
        msg.Append(chipVers[1])
        self.SendMsg(msg, MsgQueue.NoOp)
         
    def HandleSerialApiSetTimeoutsResponse(self, _data):
        msg = Msg( "Response to SERIAL_API_SET_TIMEOUTS", self.nodeId,  RESPONSE, FUNC_ID_SERIAL_API_SET_TIMEOUTS, False)
        msg.Append(_data[2])
        msg.Append(_data[3])
        self.SendMsg(msg, MsgQueue.NoOp)
        
    def HandleSerialAPISoftResetResponse(self, _data):
        msg = Msg( "Response to FUNC_ID_SERIAL_API_SOFT_RESET", self.nodeId,  RESPONSE, FUNC_ID_SERIAL_API_SOFT_RESET, False)
        self.SendMsg(msg, MsgQueue.NoOp)
        # Remove the message from the queue, because there is no acknowledged.
        self.RemoveCurrentMsg()
       
    def HandleNetworkUpdateResponse(self, _data):
#        SUC_UPDATE_DONE			=	0x00
#        SUC_UPDATE_ABORT			=	0x01
#        SUC_UPDATE_WAIT	        	=	0x02
#        SUC_UPDATE_DISABLED		=	0x03
#        SUC_UPDATE_OVERFLOW	=	0x04
        msg = Msg( "Response to FUNC_ID_ZW_REQUEST_NETWORK_UPDATE", self.nodeId,  RESPONSE, FUNC_ID_ZW_REQUEST_NETWORK_UPDATE, False)
        msg.Append(SUC_UPDATE_DONE)
        self.SendMsg(msg, MsgQueue.NoOp)

    def HandleSetNodeProtocolInfoResponse(self, _data):
        """Process a response from the Z-Wave PC interface"""
        # The node that the protocol info response is for is not included in the message.
        # We have to assume that the node is the same one as in the most recent request.
        msg = Msg( "Response to GET_NODE_PROTOCOL_INFO", self.nodeId,  RESPONSE, FUNC_ID_ZW_GET_NODE_PROTOCOL_INFO, False)
        node = self.GetNode(_data[2])
        if node is None:
            self._log.write(LogLevel.Warning, "WARNING: nodeId {0} don't exist - ignoring.".format(_data[2]))
            return
        msg = node.getMsgProtocolInfo()        
        self.SendMsg(msg, MsgQueue.NoOp)

    def HandleSendDataResponse(self, _data, _replication):
        self._log.write(LogLevel.Debug, self,  "    HandleSendDataResponse : ", GetDataAsHex(_data))
        node = self.GetNode(_data[2])
        if node is None:
            msg = Msg( "Z-Wave stack for cmdClass 0x%.2x ZW_SEND_DATA"% _data[4], _data[2],  RESPONSE, FUNC_ID_ZW_SEND_DATA, False)
            msg.Append(TRANSMIT_OPTION_ACK) # 0x01
            self.SendMsg(msg, MsgQueue.NoOp)
            self._log.write(LogLevel.Warning, "WARNING: nodeId {0} don't exist - ignoring.".format(_data[2]))
            msg = Msg( "Z-Wave stack no route ZW_SEND_DATA", _data[2],  REQUEST, FUNC_ID_ZW_SEND_DATA, False)
            msg.Append(_data[-2])
            msg.Append(TRANSMIT_COMPLETE_NOROUTE)
            self.SendMsg(msg, MsgQueue.NoOp)
            return
        self.m_expectedCommandClassId = _data[4]
        self.m_expectedReply = _data[6]
        self.m_expectedCallbackId = _data[-2]
        node.HandleMsgSendDataResponse(_data)

    def HandleRequestNodeInfo(self, _data):
        node = self.GetNode(_data[2])
        if node is None:
            self._log.write(LogLevel.Warning, "WARNING: nodeId {0} don't exist - ignoring.".format(_data[2]))
            return
        msg = Msg( "Z-Wave stack for ZW_REQUEST_NODE_INFO", node.nodeId, RESPONSE, FUNC_ID_ZW_REQUEST_NODE_INFO, False)
        msg.Append(node.nodeId)
        self.SendMsg(msg, MsgQueue.NoOp)  # Ack for request node info
        msg = node.getMsgNodeInfo()
        if msg is not None : self.SendMsg(msg, MsgQueue.NoOp)

    def HandleNodeInformationResponse(self, _data):
        node = self.GetNode(_data[2])
#        msg = Msg( "Z-Wave stack for node {0} ZW_SEND_DATA".format(_data[2]), self.nodeId,  RESPONSE, FUNC_ID_ZW_SEND_DATA, False)
#        msg.Append(TRANSMIT_OPTION_ACK) # 0x01
#        self.SendMsg(msg, MsgQueue.NoOp)
        if node is None:
            msg = Msg( "Warning, Node {0} Information Request fail".format(_data[2]), self, REQUEST, FUNC_ID_ZW_SEND_NODE_INFORMATION, False)
            msg.Append(_data[-2])
            msg.Append(TRANSMIT_COMPLETE_NOROUTE)#TRANSMIT_COMPLETE_NOROUTE
#            msg.Append(_data[2])
        else:
            msg = Msg( "Node Information Request Success", node, REQUEST, FUNC_ID_ZW_SEND_NODE_INFORMATION, False)
            msg.Append(_data[-2])
            msg.Append(TRANSMIT_COMPLETE_OK)
#            msg.Append(_data[2])
        self.SendMsg(msg, MsgQueue.NoOp)
#        msg = node.getMsgNodeInfo(_data)
    
    def HandleSetRoutingInfoResponse(self, _data):
        node = self.GetNode(_data[2])
        if node is None:
            self._log.write(LogLevel.Warning, "WARNING: nodeId {0} don't exist - ignoring.".format(_data[2]))
            return
        msg = node.getMsgRoutingInfo(_data)
        self.SendMsg(msg, MsgQueue.NoOp)
        
    def HandleDeleteReturnRouteRequest(self, _data):
        node = self.GetNode(_data[2])
        self.m_expectedCallbackId = _data[-2]
        msg = Msg( "Z-Wave stack for ZW_DELETE_RETURN_ROUTE", _data[2],  RESPONSE, FUNC_ID_ZW_DELETE_RETURN_ROUTE, False)
        msg.Append(TRANSMIT_OPTION_ACK)
        self.SendMsg(msg, MsgQueue.NoOp)  # Ack for request
        msg = Msg( "Request with callback ID 0x%.2x for ZW_DELETE_RETURN_ROUTE"%self.m_expectedCallbackId, _data[2],  REQUEST, FUNC_ID_ZW_DELETE_RETURN_ROUTE, False)
        msg.Append(self.m_expectedCallbackId)
        if node is not None :
            msg.Append(TRANSMIT_COMPLETE_OK)
            self.SendMsg(msg, MsgQueue.NoOp)
            return False
        else :
            msg.Append(TRANSMIT_COMPLETE_NOROUTE)
            self.SendMsg(msg, MsgQueue.NoOp)
            return False
        
    def HandleAssignReturnRouteRequest(self, _data):
        node = self.GetNode(_data[2])
        self.m_expectedCallbackId = _data[-2]
        msg = Msg( "Z-Wave stack for ZW_ASSIGN_RETURN_ROUTE", _data[2],  RESPONSE, FUNC_ID_ZW_ASSIGN_RETURN_ROUTE, False)
        msg.Append(TRANSMIT_OPTION_ACK)
        self.SendMsg(msg, MsgQueue.NoOp)  # Ack for request
        msg = Msg( "Request with callback ID 0x%.2x for ZW_ASSIGN_RETURN_ROUTE"%self.m_expectedCallbackId, _data[2],  REQUEST, FUNC_ID_ZW_ASSIGN_RETURN_ROUTE, False)
        if node is not None :
            node.route = [_data[3]]
            msg.Append(self.m_expectedCallbackId)
            msg.Append(TRANSMIT_COMPLETE_OK)
            self.SendMsg(msg, MsgQueue.NoOp)
            return False
        else :
            msg.Append(self.m_expectedCallbackId)
            msg.Append(TRANSMIT_COMPLETE_NOROUTE)
            self.SendMsg(msg, MsgQueue.NoOp)
            return False

    def HandleNodeNeighborUpdateResponse(self, _data):
        node = self.GetNode(_data[2])
        self.m_expectedCallbackId = _data[-2]
#        msg = Msg( "Z-Wave stack for FUNC_ID_ZW_REQUEST_NODE_NEIGHBOR_UPDATE_OPTIONS", _data[2],  RESPONSE, FUNC_ID_ZW_REQUEST_NODE_NEIGHBOR_UPDATE_OPTIONS, False)
        if node is not None :
#            msg.Append(self.m_expectedCallbackId)
#            msg.Append(TRANSMIT_OPTION_ACK)
#            self.SendMsg(msg, MsgQueue.NoOp)  # Ack for request
            msg = node.getMsgNodeNeighborUpdate(self.m_expectedCallbackId)
            self.SendMsg(msg, MsgQueue.NoOp)
            return False
        else : # Handle A response fail
            threading.Thread(None, self.emulCycleCmd, "th_handleEmulCycleCmd_ctrl_{0}.".format(self.homeId), (),
                                 { 'msgParams': {'logText' : "Z-Wave stack for FUNC_ID_ZW_REQUEST_NODE_NEIGHBOR_UPDATE_OPTIONS",
                                                         'targetNodeId': _data[2],
                                                         'msgType': REQUEST,
                                                         'function' : FUNC_ID_ZW_REQUEST_NODE_NEIGHBOR_UPDATE_OPTIONS, 
                                                         'callbackId': _data[-2]}, 
                                    'listState': [REQUEST_NEIGHBOR_UPDATE_STARTED, REQUEST_NEIGHBOR_UPDATE_FAILED],
                                    'timings': [0.0, 2.0]
                                 }).start()
            return False
            
    def HandleAddNodeToNetworkRequest(self, _data):
        """Start process to include a new node"""
        #ADD_NODE_ANY  	=                   0x01
        #ADD_NODE_CONTROLLER		=	0x02
        #ADD_NODE_SLAVE		=			0x03
        #ADD_NODE_EXISTING		=		0x04
        #ADD_NODE_STOP			=		0x05
        #ADD_NODE_STOP_FAILED	=		0x06
        addType = _data[2] & 0x07  
        msg = Msg( "Z-Wave stack for FUNC_ID_ZW_ADD_NODE_TO_NETWORK", 0xff,  REQUEST, FUNC_ID_ZW_ADD_NODE_TO_NETWORK, False)
        if addType == ADD_NODE_STOP :
            if FUNC_ID_ZW_ADD_NODE_TO_NETWORK in self._currentCtrlCommands :
                msg.Append(self._currentCtrlCommands[FUNC_ID_ZW_ADD_NODE_TO_NETWORK].callbackId)
                msg.Append(LEARN_MODE_DONE)
                msg.Append(ADD_NODE_STOP)
                msg.Append(TRANSMIT_COMPLETE_OK)  #0x00
                del self._currentCtrlCommands[FUNC_ID_ZW_ADD_NODE_TO_NETWORK]
            else :
                self._log.write(LogLevel.Warning, self, "Receive {ADD_NODE_STOP".format(getFuncName(msgParams['function']), GetDataAsHex([msgParams['function']])))
        else : 
            #OPTION_HIGH_POWER			=	0x80    # High power controller for inclusion/exclusion
            #OPTION_NWI				=		0x40	# NWI Inclusion
            self._currentCtrlCommands[FUNC_ID_ZW_ADD_NODE_TO_NETWORK] = ControllerCommandItem(FUNC_ID_ZW_ADD_NODE_TO_NETWORK, _data[3])
            self._currentCtrlCommands[FUNC_ID_ZW_ADD_NODE_TO_NETWORK].highPower = _data[2] & OPTION_HIGH_POWER
            self._currentCtrlCommands[FUNC_ID_ZW_ADD_NODE_TO_NETWORK].options = _data[2] & OPTION_NWI
            self._currentCtrlCommands[FUNC_ID_ZW_ADD_NODE_TO_NETWORK].setCtrlState(ControllerState.Waiting, ADD_NODE_STATUS_LEARN_READY)
            msg.Append(_data[3]) # Add callbackId
            msg.Append(ADD_NODE_STATUS_LEARN_READY)
            msg.Append(TRANSMIT_COMPLETE_OK)  #0x00
            msg.Append(0x00)  #don't know why
        self.SendMsg(msg, MsgQueue.NoOp)
        # set driver in include mode
        # wait for inclusion in a thread with stop function and timeout ?
        # memorise callbackID
        
    def emulCycleCmd(self, msgParams = {},  listState = [], timings = []):
        self._log.write(LogLevel.Detail, self, "Start command emulation :{0} ({1})".format(getFuncName(msgParams['function']), GetDataAsHex([msgParams['function']])))
        i = 0
        print "++++ Controller emulCycleCmd kwargs : ", msgParams, listState, timings
        for state in listState:
            self._stop.wait(timings[i])
            if not self._stop.isSet() :
                msg = Msg(msgParams['logText'], msgParams['targetNodeId'], msgParams['msgType'], msgParams['function'], False)
                if 'callbackId' in msgParams: msg.Append(msgParams['callbackId'])
                msg.Append(listState[i])
                self.SendMsg(msg, MsgQueue.NoOp)
                i += 1
            else : break
            
    def waitForStepCmd(self, callback, timing):
        self._log.write(LogLevel.Detail, self, "Controller Wait {0} sec for next cmd ({1})".format(timing, callback))
        self._stop.wait(timing)
        if not self._stop.isSet() : callback()
                
class ControllerCommandItem:
    
    def __init__(self,  command, callbackId = 0, nodeId = 0):
        self.command = command         # Zwave ControllerCommand num
        self.callbackId = callbackId       # Zwave callback num Id
        self.nodeId = nodeId    #uint8
        self._ctrlState = None               # ControllerState
        self._ctrlStateNum = 0                # Zwave Num of state
        self._ctrlStateChanged = False     #bool
        self._ctrlStateCommandDone = False    #bool
        self._ctrlStateCallback = None            # Callback function
        self._ctrlStaterReturnError = None        # ControllerError
        self._crtlAdded  = False               #bool
        self.commandArg = 0     #uint8
        self.highPower  = False
        self.options = None   # some extra options like NWI Inclusion

    crtlState = property(lambda self: self._ctrlState)
    ctrlStateNum = property(lambda self: self._ctrlStateNum)
    
    def setCtrlState(self, ctrlState, numState = 0x00):
        self._ctrlStateChanged = True if self._ctrlState != ctrlState else False
        self._ctrlState = ctrlState
        self._ctrlStateNum = numState
        
class Msg:
    
    m_MultiChannel			= 0x01		# Indicate MultiChannel encapsulation
    m_MultiInstance			= 0x02		# Indicate MultiInstance encapsulation
    
    def __init__(self,  _logText, _targetNodeId, _msgType, _function , _bCallbackRequired, _bReplyRequired = True, _expectedReply = 0, _expectedCommandClassId = 0):
            
        self.s_nextCallbackId = 1
        
        self.m_logText = _logText
        self.m_bFinal= False
        self.m_bCallbackRequired =_bCallbackRequired
        self.m_callbackId = 0
        self.m_expectedReply = 0
        self.m_expectedCommandClassId = _expectedCommandClassId
        self.m_length = 4
        self.m_targetNodeId = _targetNodeId
        self.m_sendAttempts = 0
        self.m_maxSendAttempts = MAX_TRIES
        self.m_instance = 1
        self.m_endPoint = 0
        self.m_flags = 0
        if _bReplyRequired:
            # Wait for this message before considering the transaction complete 
            self.m_expectedReply = _expectedReply if _expectedReply else _function
        self.m_buffer = [SOF, 0, _msgType, _function]
        
    GetTargetNodeId = property(lambda self: self.m_targetNodeId)
        
    def Finalize(self):
        """Fill in the length and checksum values for the message"""

        if not self.m_bFinal: # Already finalized ?
           # Deal with Multi-Channel/Instance encapsulation
            if (self.m_flags & ( self.m_MultiChannel | self.m_MultiInstance ) ) != 0:
                MultiEncap()
            # Add the callback id
            if self.m_bCallbackRequired:
                # Set the length byte
                self.m_buffer[1] = self.m_length		# Length of following data
                if 0 == self.s_nextCallbackId:
                    self.s_nextCallbackId = 1
                self.m_buffer.append(self.s_nextCallbackId)
                self.m_length += 1
                self.m_callbackId = self.s_nextCallbackId
                self.s_nextCallbackId += 1
            else:
                # Set the length byte
                self.m_buffer[1] = self.m_length - 1		# Length of following data
            # Calculate the checksum
            checksum = 0xff
            for i in range(1, self.m_length) :
                checksum ^= self.m_buffer[i]
            self.m_buffer.append(checksum)
            self.m_length += 1
            self.m_bFinal = True
            
    def Append(self,  _data):
        self.m_buffer.append(int(_data))
        self.m_length += 1
            
    def GetSendingCommandClass(self):
        if self.m_buffer[3] == 0x13 :
            return self.m_buffer[6]
        return 0

    def GetAsString(self):
        strVal = self.m_logText
        if self. m_targetNodeId != 0xff:
            strVal += " (Node={0})".format(self.m_targetNodeId)
        strVal += ": "
        for i in range(0, self.m_length) :
            if i : strVal += ", "
            strVal += "0x%.2x"%self.m_buffer[i]
        return strVal
        
    def IsNoOperation(self):
        return (self.m_bFinal and (self.m_length==11) and (self.m_buffer[3]==0x13) and (self.m_buffer[6]==0x00) and (self.m_buffer[7]==0x00))
    
    def UpdateCallbackId(self):
        """If this message has a callback ID, increment it and recalculate the checksum"""
        if self.m_bCallbackRequired:
            # update the callback ID
            self.m_buffer[m_length-2] = self.s_nextCallbackId
            self.m_callbackId = self.s_nextCallbackId
            self.s_nextCallbackId += 1
            # Recalculate the checksum
            checksum = 0xff
            for i in range(1,  self.m_length-1): 
                checksum ^= self.m_buffer[i]
            self.m_buffer[self.m_length-1] = checksum

class MsgQueueItem:
    
    def __init__(self):
        
        self.m_command = 0xff
        self.m_msg = None
        self.m_nodeId = 0
        self.m_retry = False
        self.m_cci = None
        
    def __eq__(self, _other) :
        """Surcharge de =="""
        if _other.m_command == self.m_command:
            if self.m_command == MsgQueueCmd.SendMsg:
                return (_other.m_msg == self.m_msg)
            elif self.m_command == MsgQueueCmd.Controller:
                return (_other.m_cci.m_controllerCommand == self.m_cci.m_controllerCommand) and (_other.m_cci.m_controllerCallback == self.m_cci.m_controllerCallback)
        return False

class Event:
    
    def __init__(self,  msgQ,  delais):
        self.msgQ = msgQ
        self.waitTime = time.time() + delais
        self.m_manualReset = True
        self.m_isSignaled = False
        self.m_waitingThreads = 0
    
    def handleResponse(self, callback):
        self.m_isSignaled = True
        callback(RESPONSE,  self.msgQ)
    
class FakeController(threading.Thread):
    
    def __init__(self, callback, stop):
        threading.Thread.__init__(self)
        self._callback = callback
        self._stop = stop
        self._event = []
        
    def run(self):
        running = True
        print "+++++++++++++ FakeController Started ++++++++++++++"
        while not self._stop.isSet() and running:
            if self._event :
                removed = []
                for event in self._event:
                    if event.waitTime >= time.time() and not event.m_isSignaled:
                        event.handleResponse(self._callback)
                        removed.append(event)
                print removed
                print self._event
                for e in removed: self._event.remove(e)
                removed = []
            else :
                self._stop.wait(0.1)
                
    def addEvent(self,  msgQ,  delais = 100):
        self._event.append(Event(msgQ, delais))
            

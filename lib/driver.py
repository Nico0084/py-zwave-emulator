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
from ctrlemulator import OZWSerialEmul
import time
import threading
import copy

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

class Driver:

    def __init__(self, manager, node,  data):
        self._manager = manager
        self.serialport = None
        self._clientConnected = False
        self.xmlData = data
        self._startTime = 0
        self._node = node
        self.m_nodes = {}
        self.controller = None
        self.driverData = DriverData()
        # Create the message queue events
        self.msgQueues = {}
        for q in range(0, MsgQueue.Count):
            self.msgQueues[q] = []
        self.m_currentMsg = None
        self.m_transmitOptions =TRANSMIT_OPTION_ACK | TRANSMIT_OPTION_AUTO_ROUTE | TRANSMIT_OPTION_EXPLORE
        self._currentCallbackId = 0x0a
        self.handleSendMsgQ = threading.Thread(None, self.sendMsgQueue, "th_Handle_Driver_{0}_Msg".format(self.homeId), (), {})
        self.running = False
        self.setWaitingForAck(False)
        self._currentCtrlCommands = {}  #memorize callback informations with key zwave function
        self.handleSendMsgQ.start()
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
    IsInExcludeState = property(lambda self: True if FUNC_ID_ZW_REMOVE_NODE_FROM_NETWORK in self._currentCtrlCommands and \
        (self._currentCtrlCommands[FUNC_ID_ZW_REMOVE_NODE_FROM_NETWORK].crtlState in [ControllerState.Waiting, ControllerState.InProgress]) else False)
    IsInReplaceNodeFailState = property(lambda self: True if FUNC_ID_ZW_REPLACE_FAILED_NODE in self._currentCtrlCommands and \
            (self._currentCtrlCommands[FUNC_ID_ZW_REPLACE_FAILED_NODE].crtlState in [ControllerState.Waiting, ControllerState.InProgress]) else False)

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
        self.setWaitingForAck(False)
        # Open the controller
        self.controller = OZWSerialEmul(self.serialport, stop = self._stop,  callback = self.HandleMsg, setWaitingForAck = self.setWaitingForAck, log = self._log, cbTimeOut = 10.0)
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
            msg = Msg( "Request FUNC_ID_ZW_ADD_NODE_TO_NETWORK", self.nodeId,  REQUEST, FUNC_ID_ZW_ADD_NODE_TO_NETWORK)
            msg.Append(self._currentCtrlCommands[FUNC_ID_ZW_ADD_NODE_TO_NETWORK].callbackId) # TODO: Check if necessary in case of internal inclusion ?
            msg.Append(ADD_NODE_STATUS_ADDING_SLAVE)
            msg.Append(node.nodeId)
            msgTemp = node.getNodeInfoClass()
            for d in msgTemp: msg.Append(d) # Add node CommandClasses
            self._currentCtrlCommands[FUNC_ID_ZW_ADD_NODE_TO_NETWORK].setCtrlState(ControllerState.InProgress, ADD_NODE_STATUS_ADDING_SLAVE)
            self._currentCtrlCommands[FUNC_ID_ZW_ADD_NODE_TO_NETWORK].nodeId = node.nodeId
            msg.SetExpectedCallBack(self._currentCtrlCommands[FUNC_ID_ZW_ADD_NODE_TO_NETWORK].callbackId)
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
                msg = Msg( "Request FUNC_ID_ZW_ADD_NODE_TO_NETWORK - ADD_NODE_STATUS_PROTOCOL_DONE", self.nodeId,  REQUEST, FUNC_ID_ZW_ADD_NODE_TO_NETWORK)
                msg.Append(self._currentCtrlCommands[FUNC_ID_ZW_ADD_NODE_TO_NETWORK].callbackId)
                msg.Append(ADD_NODE_STATUS_PROTOCOL_DONE)
                msg.Append(self._currentCtrlCommands[FUNC_ID_ZW_ADD_NODE_TO_NETWORK].nodeId)
                msg.Append(TRANSMIT_COMPLETE_OK)
                self._currentCtrlCommands[FUNC_ID_ZW_ADD_NODE_TO_NETWORK].setCtrlState(ControllerState.InProgress, ADD_NODE_STATUS_PROTOCOL_DONE)
                self._currentCtrlCommands[FUNC_ID_ZW_ADD_NODE_TO_NETWORK].nodeId = 0
                msg.SetExpectedCallBack(self._currentCtrlCommands[FUNC_ID_ZW_ADD_NODE_TO_NETWORK].callbackId)
                self.SendMsg(msg, MsgQueue.Command)
            else :
                self._log.write(LogLevel.Warning, self, "Controller {0} have no node in inclusion process, state: {1}".format(self.homeId, self._currentCtrlCommands[FUNC_ID_ZW_ADD_NODE_TO_NETWORK].ctrlStateNum))
        else :
            self._log.write(LogLevel.Warning, self, "Controller {0} ins't in include state.".format(self.homeId))

    def setInInclusion(self): #TODO: add option to start function by type ADD_NODE_CONTROLLER, ADD_NODE_SLAVE, ADD_NODE_EXISTING
        """Put driver in inclusion mode"""
        if not self.IsInIncludeState :
            if not self.IsInExcludeState :
                self.HandleAddNodeToNetworkRequest([REQUEST, FUNC_ID_ZW_ADD_NODE_TO_NETWORK, ADD_NODE_ANY | OPTION_HIGH_POWER, self.getNextCallbackId()])
                self._log.write(LogLevel.Info, self, "{0} is inclusion mode".format(self._manager.matchHomeID(self.homeId)))
                return {"error": u""}
            else :
                self._log.write(LogLevel.Warning, self, "{0} is in exclusion mode, unauthorized inclusion mode".format(self._manager.matchHomeID(self.homeId)))
                return {"error": u"{0} is in exclusion mode, unauthorized inclusion mode".format(self._manager.matchHomeID(self.homeId))}
        else :
            self._log.write(LogLevel.Warning, self, "{0} is already in inclusion mode".format(self._manager.matchHomeID(self.homeId)))
            return {"error": u"{0} is already in inclusion mode".format(self._manager.matchHomeID(self.homeId))}

    def setOutInclusion(self): #TODO: add option to terminat function by type ADD_NODE_STOP_FAILED
        """Exit driver of inclusion mode"""
        if self.IsInIncludeState :
            self.HandleAddNodeToNetworkRequest([REQUEST, FUNC_ID_ZW_ADD_NODE_TO_NETWORK, ADD_NODE_STOP | OPTION_HIGH_POWER, self.getNextCallbackId()])
            self._log.write(LogLevel.Info, self, "{0} has quit inclusion mode".format(self._manager.matchHomeID(self.homeId)))
            return {"error": u""}
        else :
            self._log.write(LogLevel.Warning, self, "{0} is not in inclusion mode, can't stop it !".format(self._manager.matchHomeID(self.homeId)))
            return {"error": u"{0} is not in inclusion mode, can't stop it !".format(self._manager.matchHomeID(self.homeId))}

    def excludeNode(self, node):
        """Exclude a node from zwave network, handle process message"""
        if self.IsInExcludeState :
            msg = Msg( "Request FUNC_ID_ZW_REMOVE_NODE_FROM_NETWORK", self.nodeId,  REQUEST, FUNC_ID_ZW_REMOVE_NODE_FROM_NETWORK)
            msg.Append(self._currentCtrlCommands[FUNC_ID_ZW_REMOVE_NODE_FROM_NETWORK].callbackId) # TODO: Check if necessary in case of internal inclusion ?
            msg.Append(REMOVE_NODE_STATUS_REMOVING_SLAVE)
            msg.Append(node.nodeId)
            self._currentCtrlCommands[FUNC_ID_ZW_REMOVE_NODE_FROM_NETWORK].setCtrlState(ControllerState.InProgress, REMOVE_NODE_STATUS_REMOVING_SLAVE)
            self._currentCtrlCommands[FUNC_ID_ZW_REMOVE_NODE_FROM_NETWORK].nodeId = node.nodeId
            self.UnRegisterNode(node)
            msg.SetExpectedCallBack(self._currentCtrlCommands[FUNC_ID_ZW_REMOVE_NODE_FROM_NETWORK].callbackId)
            self.SendMsg(msg, MsgQueue.Command)
            threading.Thread(None, self.waitForStepCmd, "th_handleWaitForStepCmd_ctrl_{0}.".format(self.homeId), (),
                    {'callback': self.terminateExcludeNode,
                      'timing' : 0.5
                    }).start()
            return True
        else :
            self._log.write(LogLevel.Warning, self, "Controller {0} ins't in exclude state.".format(self.homeId))
            return False

    def terminateExcludeNode(self):
        if self.IsInExcludeState :
            if self._currentCtrlCommands[FUNC_ID_ZW_REMOVE_NODE_FROM_NETWORK].ctrlStateNum == REMOVE_NODE_STATUS_REMOVING_SLAVE :
                msg = Msg( "Request FUNC_ID_ZW_REMOVE_NODE_FROM_NETWORK - REMOVE_NODE_STATUS_DONE", self.nodeId,  REQUEST, FUNC_ID_ZW_REMOVE_NODE_FROM_NETWORK)
                msg.Append(self._currentCtrlCommands[FUNC_ID_ZW_REMOVE_NODE_FROM_NETWORK].callbackId)
                msg.Append(REMOVE_NODE_STATUS_DONE)
                msg.Append(self._currentCtrlCommands[FUNC_ID_ZW_REMOVE_NODE_FROM_NETWORK].nodeId)
                msg.Append(TRANSMIT_COMPLETE_OK)
                self._currentCtrlCommands[FUNC_ID_ZW_REMOVE_NODE_FROM_NETWORK].setCtrlState(ControllerState.InProgress, REMOVE_NODE_STATUS_REMOVING_SLAVE)
                self._currentCtrlCommands[FUNC_ID_ZW_REMOVE_NODE_FROM_NETWORK].nodeId = 0xff
                msg.SetExpectedCallBack(self._currentCtrlCommands[FUNC_ID_ZW_REMOVE_NODE_FROM_NETWORK].callbackId)
                self.SendMsg(msg, MsgQueue.Command)
            else :
                self._log.write(LogLevel.Warning, self, "Controller {0} have no node in exclusion process, state: {1}".format(self.homeId, self._currentCtrlCommands[FUNC_ID_ZW_REMOVE_NODE_FROM_NETWORK].ctrlStateNum))
        else :
            self._log.write(LogLevel.Warning, self, "Controller {0} ins't in exclude state.".format(self.homeId))

    def setInExclusion(self): #TODO: add option to start function by type REMOVE_NODE_CONTROLLER, REMOVE_NODE_SLAVE
        """Put driver in inclusion mode"""
        if not self.IsInExcludeState :
            if not self.IsInIncludeState :
                self.HandleRemoveNodeFromNetworkRequest([REQUEST, FUNC_ID_ZW_REMOVE_NODE_FROM_NETWORK, REMOVE_NODE_ANY | OPTION_HIGH_POWER, self.getNextCallbackId()])
                self._log.write(LogLevel.Info, self, "{0} is exclusion mode".format(self._manager.matchHomeID(self.homeId)))
                return {"error": u""}
            else :
                self._log.write(LogLevel.Warning, self, "{0} is in inclusion mode, unauthorized exclusion mode".format(self._manager.matchHomeID(self.homeId)))
                return {"error": u"{0} is in inclusion mode, unauthorized exclusion mode".format(self._manager.matchHomeID(self.homeId))}
        else :
            self._log.write(LogLevel.Warning, self, "{0} is already in exclusion mode".format(self._manager.matchHomeID(self.homeId)))
            return {"error": u"{0} is already in exclusion mode".format(self._manager.matchHomeID(self.homeId))}

    def setOutExclusion(self): #TODO: add option to terminat function by type REMOVE_NODE_STATUS_FAILED
        """Exit driver of inclusion mode"""
        if self.IsInExcludeState :
            self.HandleRemoveNodeFromNetworkRequest([REQUEST, FUNC_ID_ZW_REMOVE_NODE_FROM_NETWORK, REMOVE_NODE_STOP | OPTION_HIGH_POWER, self.getNextCallbackId()])
            self._log.write(LogLevel.Info, self, "{0} has quit exclusion mode".format(self._manager.matchHomeID(self.homeId)))
            return {"error": u""}
        else :
            self._log.write(LogLevel.Warning, self, "{0} is not in exclusion mode, can't stop it !".format(self._manager.matchHomeID(self.homeId)))
            return {"error":  u"{0} is not in exclusion mode, can't stop it !".format(self._manager.matchHomeID(self.homeId))}

    def terminateRemoveFaileNode(self):
        if self._currentCtrlCommands[FUNC_ID_ZW_REMOVE_FAILED_NODE_ID].ctrlStateNum == FAILED_NODE_REMOVE_STARTED :
            msg = Msg( "Request FUNC_ID_ZW_REMOVE_FAILED_NODE_ID - FAILED_NODE_REMOVED", self.nodeId,  REQUEST, FUNC_ID_ZW_REMOVE_FAILED_NODE_ID)
            msg.Append(self._currentCtrlCommands[FUNC_ID_ZW_REMOVE_FAILED_NODE_ID].callbackId)
            msg.Append(FAILED_NODE_REMOVED)
            node = self.GetNode(self._currentCtrlCommands[FUNC_ID_ZW_REMOVE_FAILED_NODE_ID].nodeId)
            self.UnRegisterNode(node)
            self._currentCtrlCommands[FUNC_ID_ZW_REMOVE_FAILED_NODE_ID].setCtrlState(ControllerState.Completed, FAILED_NODE_REMOVED)
            self._currentCtrlCommands[FUNC_ID_ZW_REMOVE_FAILED_NODE_ID].nodeId = 0xff
            self.SendMsg(msg, MsgQueue.Command, True)
        elif self._currentCtrlCommands[FUNC_ID_ZW_REMOVE_FAILED_NODE_ID].ctrlStateNum == FAILED_NODE_NOT_FOUND :
            node = self.GetNode(self._currentCtrlCommands[FUNC_ID_ZW_REMOVE_FAILED_NODE_ID].nodeId)
            if node and not node.IsFailed :
                msg = Msg( "Request FUNC_ID_ZW_REMOVE_FAILED_NODE_ID - FAILED_NODE_OK", self.nodeId,  REQUEST, FUNC_ID_ZW_REMOVE_FAILED_NODE_ID)
                msg.Append(self._currentCtrlCommands[FUNC_ID_ZW_REMOVE_FAILED_NODE_ID].callbackId)
                msg.Append(FAILED_NODE_OK)
                self._currentCtrlCommands[FUNC_ID_ZW_REMOVE_FAILED_NODE_ID].setCtrlState(ControllerState.Completed, FAILED_NODE_OK)
            else :
                msg = Msg( "Request FUNC_ID_ZW_REMOVE_FAILED_NODE_ID - FAILED_NODE_NOT_REMOVED", self.nodeId,  REQUEST, FUNC_ID_ZW_REMOVE_FAILED_NODE_ID)
                msg.Append(self._currentCtrlCommands[FUNC_ID_ZW_REMOVE_FAILED_NODE_ID].callbackId)
                msg.Append(FAILED_NODE_NOT_REMOVED)
                self._currentCtrlCommands[FUNC_ID_ZW_REMOVE_FAILED_NODE_ID].setCtrlState(ControllerState.Completed, FAILED_NODE_NOT_REMOVED)
            msg.SetExpectedCallBack(self._currentCtrlCommands[FUNC_ID_ZW_REMOVE_FAILED_NODE_ID].callbackId)
            self._currentCtrlCommands[FUNC_ID_ZW_REMOVE_FAILED_NODE_ID].nodeId = 0xff
            self.SendMsg(msg, MsgQueue.Command, True)
        else :
            self._log.write(LogLevel.Warning, self, "Controller {0} is not in remove node failed process".format(self.homeId))

    def replaceNode(self, newNode):
        if self.IsInReplaceNodeFailState:
            oldNode = self.GetNode(self._currentCtrlCommands[FUNC_ID_ZW_REPLACE_FAILED_NODE].nodeId)
            print "oldNode : ",  oldNode
            newNode.nodeId = oldNode.nodeId
            newNode.homeId = oldNode.homeId
            newNode.neighbors = oldNode.neighbors
            newNode.name = oldNode.name
            newNode.location = oldNode.location
            newNode.SetAddingNode()
            msg = Msg( "Request FUNC_ID_ZW_REPLACE_FAILED_NODE - FAILED_NODE_REPLACE_DONE", self.nodeId,  REQUEST, FUNC_ID_ZW_REPLACE_FAILED_NODE)
            msg.Append(self._currentCtrlCommands[FUNC_ID_ZW_REPLACE_FAILED_NODE].callbackId) # TODO: Check if necessary in case of internal inclusion ?
            msg.Append(FAILED_NODE_REPLACE_DONE)
            msg.Append(newNode.nodeId)
            self._currentCtrlCommands[FUNC_ID_ZW_REPLACE_FAILED_NODE].setCtrlState(ControllerState.Completed, FAILED_NODE_REPLACE_DONE)
            self._currentCtrlCommands[FUNC_ID_ZW_REPLACE_FAILED_NODE].nodeId = newNode.nodeId
            self.UnRegisterNode(oldNode)
            self.RegisterNode(newNode.nodeId, False)
            msg.SetExpectedCallBack(self._currentCtrlCommands[FUNC_ID_ZW_REPLACE_FAILED_NODE].callbackId)
            self.SendMsg(msg, MsgQueue.Command, True)
            return True
        else :
            self._log.write(LogLevel.Warning, self, "Controller {0} is not in replace node failed process".format(self.homeId))
            return False

    def handleReplaceFaileNode(self):
        if self.IsInReplaceNodeFailState:
            if self._currentCtrlCommands[FUNC_ID_ZW_REPLACE_FAILED_NODE].ctrlStateNum == FAILED_NODE_REMOVE_STARTED :
                msg = Msg( "Request FUNC_ID_ZW_REPLACE_FAILED_NODE - FAILED_NODE_REPLACE_WAITING", self.nodeId,  REQUEST, FUNC_ID_ZW_REPLACE_FAILED_NODE)
                msg.Append(self._currentCtrlCommands[FUNC_ID_ZW_REPLACE_FAILED_NODE].callbackId)
                msg.Append(FAILED_NODE_REPLACE_WAITING)
                self._currentCtrlCommands[FUNC_ID_ZW_REPLACE_FAILED_NODE].setCtrlState(ControllerState.InProgress, FAILED_NODE_REPLACE_WAITING)
                msg.SetExpectedCallBack(self._currentCtrlCommands[FUNC_ID_ZW_REPLACE_FAILED_NODE].callbackId)
                self.SendMsg(msg, MsgQueue.Command, True)
                # At this step, We must exclude failed node and wait for new inclusion.
                threading.Thread(None, self.waitForStepCmd, "th_handleWaitForStepCmd_ctrl_{0}.".format(self.homeId), (),
                    {'callback': self.handleReplaceFaileNode,
                      'timing' : 0.8
                    }).start()
            elif self._currentCtrlCommands[FUNC_ID_ZW_REPLACE_FAILED_NODE].ctrlStateNum == FAILED_NODE_REPLACE_WAITING :
                node = self.GetNode(self._currentCtrlCommands[FUNC_ID_ZW_REPLACE_FAILED_NODE].nodeId)
                if node :
                    if not node.IsFailed :
                        msg = Msg( "Request FUNC_ID_ZW_REPLACE_FAILED_NODE - FAILED_NODE_OK", self.nodeId,  REQUEST, FUNC_ID_ZW_REPLACE_FAILED_NODE)
                        msg.Append(self._currentCtrlCommands[FUNC_ID_ZW_REPLACE_FAILED_NODE].callbackId)
                        msg.Append(FAILED_NODE_OK)
                        self._currentCtrlCommands[FUNC_ID_ZW_REPLACE_FAILED_NODE].setCtrlState(ControllerState.Completed, FAILED_NODE_OK)
                    else : return
                else :
                    msg = Msg( "Request FUNC_ID_ZW_REPLACE_FAILED_NODE - FAILED_NODE_REPLACE_FAILED", self.nodeId,  REQUEST, FUNC_ID_ZW_REPLACE_FAILED_NODE)
                    msg.Append(self._currentCtrlCommands[FUNC_ID_ZW_REPLACE_FAILED_NODE].callbackId)
                    msg.Append(FAILED_NODE_REPLACE_FAILED)
                    self._currentCtrlCommands[FUNC_ID_ZW_REPLACE_FAILED_NODE].setCtrlState(ControllerState.Waiting, FAILED_NODE_REPLACE_FAILED)
                self._currentCtrlCommands[FUNC_ID_ZW_REPLACE_FAILED_NODE].nodeId = 0xff
                self.SendMsg(msg, MsgQueue.Command, True)
        else :
            self._log.write(LogLevel.Warning, self, "Controller {0} is not in replace node fail process".format(self.homeId))

    def setWaitingForAck(self, state):
        self._waitingForAck = state
#        print "setWaitingForAck ", state

    def getWaitingForAck(self):
#        print "getWaitingForAck ", self._waitingForAck
        return self._waitingForAck

    def getNextCallbackId(self):
        self._currentCallbackId += 1
        if self._currentCallbackId >= 0xff: self._currentCallbackId = 0x0a
        return self._currentCallbackId

    def RegisterNode(self, _nodeId, newNode):
        """Register and queue a node to be interrogated for its setup details"""
        #Delete any existing node and replace it with a new one
        if _nodeId in self.m_nodes:
            # Remove the original node
            del (self.m_nodes[_nodeId])
        # Add the new node
        self.m_nodes[_nodeId] = self.GetNode(_nodeId)
        if newNode == True : self.m_nodes[_nodeId].SetAddingNode()
        self._log.write(LogLevel.Info, self,  "{0}, Registered Node {1}. New Node: {2} ({3})".format(self._manager.matchHomeID(self.homeId),_nodeId,
                            self.m_nodes[_nodeId].IsAddingNode, newNode))

    def UnRegisterNode(self, node):
        """Exlcude a node From the network"""
        #Delete any existing node and replace it with a new one
        if node in self.m_nodes:
            # Remove the original node
            del (self.m_nodes[node.nodeId])
        # set exclude the node
        nodeId = node.nodeId
        node.homeId = 0
        node.nodeId = self._manager.getFirstFreeNodeIdBeforeInclude()
        node.ClearAddingNode()
        node.Reset()
        self._log.write(LogLevel.Info, self,  "{0}, Unregistered Node {1}".format(self._manager.matchHomeID(self.homeId), nodeId))

    def SendMsg(self, _msg,  _queue, firstNext = False, timing = 0):
        # Queue a message to be sent to the Z-Wave PC Interface
        item = MsgQueueItem(_msg,  _queue, firstNext, time.time()+timing)
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
        self.msgQueues[_queue].append(item)

    def HandleMsg(self, buffer):
        """Handle data read from the serial port"""
        print 'Receive from controller : {0}'.format(self.controller.formatHex(buffer))
        if not buffer:
            # Nothing to read, TimeOut
            if self.getWaitingForAck() :
                if self.m_currentMsg is not None:
                    self._log.write(LogLevel.Detail, "TimeOut on waiting for ACK. Try to resend last message...")
                    self.m_currentMsg.msg.m_sendAttempts += 1
                    if self.m_currentMsg.msg.m_sendAttempts < MAX_TRIES :
                        self.driverData.m_dropped += 1
                        self.SendMsg(self.m_currentMsg.msg, self.m_currentMsg.queue, True, 0)
                    else :
                        self._log.write(LogLevel.StreamDetail, self.m_currentMsg.msg.GetTargetNodeId, "Max tries {0} reached, abord resend : ".format(MAX_TRIES,  self.m_currentMsg.msg.GetAsString()))
                        self._log.write(LogLevel.Detail, "Connection client presumed lost on {0}.".format(self.serialport))
                        self._clientConnected = False
                    self.RemoveCurrentMsg()
                else:
                    self._log.write(LogLevel.Detail, "No Current Message to send, client presumed lost on {0}.".format(self.serialport))
                    self._clientConnected = False
                self.setWaitingForAck(False)
            return False
        type = buffer[0]
        if not self._clientConnected:
            self._clientConnected = True
            self._log.write(LogLevel.Detail, "New connection client detected on {0}.".format(self.serialport))
        if type == SOF:
            self.driverData.m_SOFCnt += 1
            if self.getWaitingForAck():
                # This can happen on any normal network when a transmission overlaps an unexpected
                # reception and the data in the buffer doesn't contain the ACK. The controller will
                # notice and send us a CAN to retransmit.
                self._log.write(LogLevel.Detail, "Unsolicited message received while waiting for ACK." )
                self.driverData.m_ACKWaiting +=1
                self.setWaitingForAck(False)
                self.controller.writeHex([CAN])
                self._stop.wait(0.5)  # Wait 500ms to give time of resend
                return False
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
                nodeId = self.m_currentMsg.msg.GetTargetNodeId
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
        elif type == CAN:
            # This is the other side of an unsolicited ACK. As mentioned there if we receive a message
            # just after we transmitted one, the client will notice and tell us to retransmit here.
            # Don't increment the transmission counter as it is possible the message will never get out
            # on very busy networks with lots of unsolicited messages being received. Increase the amount
            # of retries but only up to a limit so we don't stay here forever.
            node = self.GetNode(self.m_currentMsg.msg.GetTargetNodeId)
            if node is None: node = self
            self._log.write(LogLevel.Detail, node, "CAN received...triggering resend" );
            self.driverData.m_CANCnt += 1
            if self.m_currentMsg is not None:
                self.m_currentMsg.msg.m_sendAttempts += 1
                if self.m_currentMsg.msg.m_sendAttempts < MAX_TRIES :
                    self.SendMsg(self.m_currentMsg.msg, self.m_currentMsg.queue, True, 0)
                else :
                    self._log.write(LogLevel.StreamDetail, node, "Max tries {0} reached, abord resend : ".format(MAX_TRIES,  self.m_currentMsg.msg.GetAsString()))
                    self.RemoveCurrentMsg()
            else:
                self._log.write(LogLevel.Warning, self, "CurrentMsg was NULL when trying to resend" );
        elif type == NAK:
            if self.m_currentMsg is not None:
                node = self.GetNode(self.m_currentMsg.msg.GetTargetNodeId)
            else : node = self
            self._log.write(LogLevel.Warning, node, "WARNING: NAK received...triggering resend" );
            self.driverData.m_NAKCnt += 1
        elif type == ACK:
            self.driverData.m_ACKCnt += 1
            if self.m_currentMsg is None:
                self._log.write(LogLevel.StreamDetail, self, "ACK received" );
            else:
                node = self.GetNode(self.m_currentMsg.msg.GetTargetNodeId)
                self._log.write(LogLevel.StreamDetail, node, "ACK received CallbackId 0x{0:02x} Reply 0x{1:02x}".format(self.m_currentMsg.msg.expectedCallbackId, self.m_currentMsg.msg.expectedReply))
                self.RemoveCurrentMsg()
#            self.setWaitingForAck(False)
        else :
            self._log.write(LogLevel.Warning, "WARNING: Out of frame flow! (0x%.2x). Sending NAK.", buffer[0] );
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
            nodeId = self.m_currentMsg.msg.GetTargetNodeId
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
                self.HandleAssignReturnRouteRequest( _data )
            elif function ==  FUNC_ID_ZW_DELETE_RETURN_ROUTE:
                self._log.write(LogLevel.Detail, "" )
                self.HandleDeleteReturnRouteRequest( _data )
            elif function ==  FUNC_ID_ZW_ENABLE_SUC:
                self._log.write(LogLevel.Detail, "" )
                HandleEnableSUCResponse( _data )
            elif function ==  FUNC_ID_ZW_REQUEST_NETWORK_UPDATE:
                self._log.write(LogLevel.Detail, "" )
                self.HandleNetworkUpdateResponse( _data )
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
            elif function ==  FUNC_ID_ZW_REMOVE_NODE_FROM_NETWORK:
                self._log.write(LogLevel.Detail, "" )
                self.HandleRemoveNodeFromNetworkRequest( _data )
            elif function ==  FUNC_ID_ZW_REMOVE_FAILED_NODE_ID:
                self._log.write(LogLevel.Detail, "" )
                self.HandleRemoveFailedNodeResponse( _data )
            elif function ==  FUNC_ID_ZW_IS_FAILED_NODE_ID:
                self._log.write(LogLevel.Detail, "" )
                self.HandleIsFailedNodeResponse( _data )
            elif function ==  FUNC_ID_ZW_REPLACE_FAILED_NODE:
                self._log.write(LogLevel.Detail, "" )
                self.HandleReplaceFailedNodeResponse( _data )
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
            elif function ==  FUNC_ID_SERIAL_API_APPL_NODE_INFORMATION:
                self._log.write(LogLevel.Detail, "" )
                self.HandleSerialApiApplNodeInformation( _data )
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
            elif function == FUNC_ID_ZW_SEND_SLAVE_NODE_INFO:
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
            elif function ==  FUNC_ID_ZW_SET_DEFAULT:
                self._log.write(LogLevel.Detail, "" )
                self.HandleSerialAPIResetRequest( _data )
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
                else:
                    self._log.write(LogLevel.Detail, "" )
                    self._log.write(LogLevel.Info, "**TODO: handle response for 0x%.2x** Please report this message."%function )
        self.RemoveCurrentMsg()  # TODO: Not clearly handle for the momment so curentMsg is allways removed

    def RemoveCurrentMsg(self):
        """Delete the current message"""
        if self.m_currentMsg is not None:
            self._log.write(LogLevel.Detail, self.GetNode(self.m_currentMsg.msg.GetTargetNodeId), "Removing current message")
            self.m_currentMsg = None
        else :
            self._log.write(LogLevel.Detail, self,  "No current message to remove")

    def sendMsgQueue(self):
        self.running = True
        cpt = 0
        print "+++++++++++++ handle Send Messages Queues Started ++++++++++++++/n"
        while not self._stop.isSet() and self.running:
            if not self.getWaitingForAck() :
                msgQ = self.getFirstMsg()
                timeNow = time.time()
                if msgQ is not None :
                    if timeNow >= msgQ.timeOut :
                        priority = " priority"
                    else: msgQ = None
                else :
                    for queue in self.msgQueues:
                        if len(self.msgQueues[queue]) != 0 :
                            for m in self.msgQueues[queue] :
                                if timeNow >= m.timeOut :
                                    priority = ""
                                    msgQ = m
                                    break
                        if msgQ is not None : break
                if msgQ is not None :
                    if self._clientConnected :
                        attempt = "" if msgQ.msg.m_sendAttempts == 0 else " (Attempt {0})".format(msgQ.msg.m_sendAttempts)
                        self._log.write(LogLevel.Detail, self, "Queue {0}, Send{1}{2} message to Node {3} : {4}".format(MsgQueue().getName(msgQ.queue),
                                                                        priority,
                                                                        attempt,
                                                                        msgQ.nodeId,  msgQ.msg.GetAsString()))
                        self.controller.writeHex(msgQ.msg.m_buffer)
                        self.m_currentMsg = MsgQueueItem(copy.copy(msgQ.msg), msgQ.queue, msgQ.firstNext, 0)
                    else :
                        self._log.write(LogLevel.Detail, self, "No Client connected send aborted on {0}".format(self.serialport))
                    self.msgQueues[msgQ.queue].remove(msgQ)
                    cpt = 0
            cpt += 1
            if cpt != 1 : time.sleep(0.1)
            if cpt == 500 :
                cpt = 0
                print "Wait to message to send...."
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
        msg = Msg( "Response to ZW_GET_VERSION", self.nodeId,  RESPONSE, FUNC_ID_ZW_GET_VERSION)
        for  c in self._manager.getZwVersion(self.homeId): msg.Append(ord(c))
        msg.Append(0)
        msg.Append(1) # LibraryType 1 = Static Controller
        self.SendMsg(msg, MsgQueue.NoOp)

    def HandleMemorySetIdResponse(self):
        #[0x01, 0x08, 0x01, 0x20, 0x01, 0x4d, 0x0f, 0x18, 0x01, 0x8c]
        msg = Msg( "Response to ZW_MEMORY_GET_ID", self.nodeId,  RESPONSE, FUNC_ID_ZW_MEMORY_GET_ID)
        msg.Append((self.homeId & 0xff000000)>>24)
        msg.Append((self.homeId & 0x00ff0000)>>16)
        msg.Append((self.homeId & 0x0000ff00)>>8)
        msg.Append((self.homeId & 0x000000ff))
        msg.Append(self.nodeId)
        self.SendMsg(msg, MsgQueue.NoOp)

    def HandleSetControllerCapabilitiesResponse(self):
        #[0x01, 0x04, 0x01, 0x05, 0x1c, 0xe3]
        msg = Msg( "Response to GET_CONTROLLER_CAPABILITIES", self.nodeId,  RESPONSE, FUNC_ID_ZW_GET_CONTROLLER_CAPABILITIES)
        msg.Append(self.xmlData['controllerCapabilities'])
        self.SendMsg(msg, MsgQueue.NoOp)

    def HandleSetSerialAPICapabilitiesResponse(self):
        #[0x01, 0x2b, 0x01, 0x07, 0x03, 0x07, 0x00, 0x86, 0x00, 0x02, 0x00, 0x01,     0xfe, 0x80, 0xfe, 0x88, 0x0f, 0x00, 0x00, 0x00, 0xfb, 0x97, 0x7f, 0x82, 0x07, 0x00, 0x00, 0x80, 0x00, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xc2]
        msg = Msg( "Response to SERIAL_API_GET_CAPABILITIES", self.nodeId,  RESPONSE, FUNC_ID_SERIAL_API_GET_CAPABILITIES)
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
        msg = Msg( "Response to GET_SUC_NODE_ID", self.nodeId,  RESPONSE, FUNC_ID_ZW_GET_SUC_NODE_ID)
        msg.Append(self.nodeId)
        self.SendMsg(msg, MsgQueue.NoOp)

    def HandleSetRandomResponse(self, _data):
        #[0x01, 0x25, 0x01, 0x1c, 0x01, 0x20, 0x05, 0x94, 0x65, 0xf7, 0xa4, 0x34, 0x6d, 0x73, 0xc1, 0x3a, 0x59, 0x30, 0x23, 0xf6, 0x2d, 0x1a, 0x97, 0xce, 0xaf, 0x51, 0xb0, 0xe5, 0x9d, 0xf6, 0x9c, 0x4d, 0x39, 0x72, 0x0c, 0xb9, 0x8c, 0xe0, 0xc1]
        # 0x01, 0x25, 0x01, 0x1c, 0x01, 0x20, 0x75, 0x78, 0x4b, 0xf5, 0x07, 0xaa, 0x97, 0xae, 0xdc, 0x12, 0x87, 0x5a, 0xff, 0xa8, 0x1f, 0xf7, 0xda, 0xf3, 0x10, 0xa6, 0x60, 0x48, 0x0a, 0xf1, 0xed, 0xbb, 0x27, 0xb3, 0x90, 0x37, 0x08, 0xba, 0xf6
        # 0x01, 0x23, 0x01, 0x1c, 0xec, 0xc5, 0x3a, 0x82, 0xf9, 0x11, 0xfb, 0x3b, 0xf8, 0xd5, 0xf9, 0x2e, 0x9b, 0x56, 0x72, 0x12, 0xd5, 0x21, 0x4b, 0x64, 0x51, 0xef, 0xc9, 0x26, 0x11, 0x90, 0x5c, 0x0c, 0x46, 0x9a, 0xe1, 0x9f, 0xd6
        # 0x01, 0x23, 0x01, 0x1c, 0x91, 0x91, 0xa2, 0x2c, 0x08, 0x31, 0x49, 0x88, 0x1a, 0x3b, 0x74, 0xdc, 0x7d, 0xd1, 0x12, 0x49, 0xcf, 0x49, 0xfd, 0x4d, 0x94, 0xb9, 0xf1, 0xa6, 0xb1, 0x81, 0x8f, 0x74, 0x02, 0x42, 0xe3, 0x00, 0xed
        from random import randint
        msg = Msg( "Response to ZW_GET_RANDOM", self.nodeId,  RESPONSE, FUNC_ID_ZW_GET_RANDOM)
        msg.Append(_data[2]) # nodeId
        msg.Append(0x20) # 32 bytes
        for i in range(32) :  # Generate 32 bytes random
            msg.Append(randint(0, 255))
        self.SendMsg(msg, MsgQueue.NoOp)

    def HandleSerialAPISetInitDataResponse(self):
        #[0x01, 0x25, 0x01, 0x02, 0x05, 0x08, 0x1d, 0xe9, 0x3f, 0x0e, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x03, 0x01, 0x13]
                                                         #0xe9, 0x3f, 0x0e, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
        msg = Msg( "Response to SERIAL_API_GET_INIT_DATA", self.nodeId,  RESPONSE, FUNC_ID_SERIAL_API_GET_INIT_DATA)
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
        msg = Msg( "Response to SERIAL_API_SET_TIMEOUTS", self.nodeId,  RESPONSE, FUNC_ID_SERIAL_API_SET_TIMEOUTS)
        msg.Append(_data[2])
        msg.Append(_data[3])
        self.SendMsg(msg, MsgQueue.NoOp)

    def HandleSerialApiApplNodeInformation(self, _data):
        self._log.write(LogLevel.Detail, "Response to FUNC_ID_SERIAL_API_APPL_NODE_INFORMATION, nothing to do." )

    def HandleSerialAPISoftResetResponse(self, _data):
        msg = Msg( "Response to FUNC_ID_SERIAL_API_SOFT_RESET", self.nodeId,  RESPONSE, FUNC_ID_SERIAL_API_SOFT_RESET)
        self.SendMsg(msg, MsgQueue.NoOp)
        # Remove the message from the queue, because there is no acknowledged.
        self.RemoveCurrentMsg()

    def HandleNetworkUpdateResponse(self, _data):
#        SUC_UPDATE_DONE			=	0x00
#        SUC_UPDATE_ABORT			=	0x01
#        SUC_UPDATE_WAIT	        	=	0x02
#        SUC_UPDATE_DISABLED		=	0x03
#        SUC_UPDATE_OVERFLOW	=	0x04
        msg = Msg( "Response to FUNC_ID_ZW_REQUEST_NETWORK_UPDATE", self.nodeId,  RESPONSE, FUNC_ID_ZW_REQUEST_NETWORK_UPDATE)
        msg.Append(_data[2]) # callbackId
        msg.Append(SUC_UPDATE_WAIT)
        msg.SetExpectedCallBack(_data[-2])
        self.SendMsg(msg, MsgQueue.Command, True)
        # Handle A response done
        threading.Thread(None, self.emulCycleCmd, "th_handleEmulCycleCmd_ctrl_{0}.".format(self.homeId), (),
                             { 'msgParams': {'logText' : "Response to FUNC_ID_ZW_REQUEST_NETWORK_UPDATE",
                                                     'targetNodeId': 0x00,
                                                     'msgType': REQUEST,
                                                     'function' : FUNC_ID_ZW_REQUEST_NETWORK_UPDATE,
                                                     'callbackId': _data[-2]},
                                'listState': [SUC_UPDATE_DONE],
                                'timings': [1],
                                'queues' : [MsgQueue.Command],
                                'firstNext':  [True]
                             }).start()

    def HandleSetNodeProtocolInfoResponse(self, _data):
        """Process a response from the Z-Wave PC interface"""
        # The node that the protocol info response is for is not included in the message.
        # We have to assume that the node is the same one as in the most recent request.
        msg = Msg( "Response to GET_NODE_PROTOCOL_INFO", self.nodeId,  RESPONSE, FUNC_ID_ZW_GET_NODE_PROTOCOL_INFO)
        node = self.GetNode(_data[2])
        if node is None:
            self._log.write(LogLevel.Warning, "WARNING: nodeId {0} don't exist - ignoring.".format(_data[2]))
            return
        msg = node.getMsgProtocolInfo()
        self.SendMsg(msg, MsgQueue.Command)

    def HandleSendDataResponse(self, _data, _replication):
        self._log.write(LogLevel.Debug, self,  "    HandleSendDataResponse : ", GetDataAsHex(_data))
        node = self.GetNode(_data[2])
        if node is None:
            msg = Msg( "Z-Wave stack for cmdClass 0x%.2x ZW_SEND_DATA"% _data[4], _data[2],  RESPONSE, FUNC_ID_ZW_SEND_DATA)
            msg.Append(TRANSMIT_OPTION_ACK) # 0x01
            self.SendMsg(msg, MsgQueue.NoOp)
            self._log.write(LogLevel.Warning, "WARNING: nodeId {0} don't exist - ignoring.".format(_data[2]))
            msg = Msg( "Z-Wave stack no route ZW_SEND_DATA", _data[2],  REQUEST, FUNC_ID_ZW_SEND_DATA)
            msg.Append(_data[-2])
            msg.Append(TRANSMIT_COMPLETE_NOROUTE)
            msg.SetExpectedCallBack(_data[-2], _data[6], _data[4])
            self.SendMsg(msg, MsgQueue.NoOp)
            return
        node.HandleMsgSendDataResponse(_data)

    def HandleRequestNodeInfo(self, _data):
        node = self.GetNode(_data[2])
        if node is None:
            self._log.write(LogLevel.Warning, "WARNING: nodeId {0} don't exist - ignoring.".format(_data[2]))
            return
        msg = Msg( "Z-Wave stack for ZW_REQUEST_NODE_INFO", node.nodeId, RESPONSE, FUNC_ID_ZW_REQUEST_NODE_INFO)
        msg.Append(node.nodeId)
        self.SendMsg(msg, MsgQueue.Command)  # Ack for request node info
        msg = node.getMsgNodeInfo()
        if msg is not None : self.SendMsg(msg, MsgQueue.Command)

    def HandleNodeInformationResponse(self, _data):
        node = self.GetNode(_data[2])
#        msg = Msg( "Z-Wave stack for node {0} ZW_SEND_DATA".format(_data[2]), self.nodeId,  RESPONSE, FUNC_ID_ZW_SEND_DATA)
#        msg.Append(TRANSMIT_OPTION_ACK) # 0x01
#        self.SendMsg(msg, MsgQueue.NoOp)
        if node is None:
            msg = Msg( "Warning, Node {0} Information Request fail".format(_data[2]), self, REQUEST, FUNC_ID_ZW_SEND_NODE_INFORMATION)
            msg.Append(_data[-2])
            msg.Append(TRANSMIT_COMPLETE_NOROUTE)#TRANSMIT_COMPLETE_NOROUTE
#            msg.Append(_data[2])
        else:
            msg = Msg( "Node Information Request Success", node, REQUEST, FUNC_ID_ZW_SEND_NODE_INFORMATION)
            msg.Append(_data[-2])
            msg.Append(TRANSMIT_COMPLETE_OK)
#            msg.Append(_data[2])
        msg.SetExpectedCallBack(_data[-2])
        self.SendMsg(msg, MsgQueue.NoOp)
#        msg = node.getMsgNodeInfo(_data)

    def HandleSetRoutingInfoResponse(self, _data):
        node = self.GetNode(_data[2])
        if node is None:
            self._log.write(LogLevel.Warning, "WARNING: nodeId {0} don't exist - ignoring.".format(_data[2]))
            return
        msg = node.getMsgRoutingInfo(_data)
        self.SendMsg(msg, MsgQueue.Command)

    def HandleDeleteReturnRouteRequest(self, _data):
        node = self.GetNode(_data[2])
        msg = Msg( "Z-Wave stack for ZW_DELETE_RETURN_ROUTE", _data[2],  RESPONSE, FUNC_ID_ZW_DELETE_RETURN_ROUTE)
        msg.Append(TRANSMIT_OPTION_ACK)
        msg.SetExpectedCallBack(_data[-2])
        self.SendMsg(msg, MsgQueue.Command)  # Ack for request
        msg = Msg( "Request with callback ID 0x{0:02x} for ZW_DELETE_RETURN_ROUTE".format(msg.expectedCallbackId), _data[2],  REQUEST, FUNC_ID_ZW_DELETE_RETURN_ROUTE)
        msg.SetExpectedCallBack(_data[-2])
        msg.Append(msg.expectedCallbackId)
        if node is not None :
            msg.Append(TRANSMIT_COMPLETE_OK)
            self.SendMsg(msg, MsgQueue.Command)
        else :
            msg.Append(TRANSMIT_COMPLETE_NOROUTE)
            self.SendMsg(msg, MsgQueue.Command)

    def HandleAssignReturnRouteRequest(self, _data):
        node = self.GetNode(_data[2])
        msg = Msg( "Z-Wave stack for ZW_ASSIGN_RETURN_ROUTE", _data[2],  RESPONSE, FUNC_ID_ZW_ASSIGN_RETURN_ROUTE)
        msg.SetExpectedCallBack(_data[-2])
        msg.Append(TRANSMIT_OPTION_ACK)
        self.SendMsg(msg, MsgQueue.Command)  # Ack for request
        msg = Msg( "Request with callback ID 0x{0:02x} for ZW_ASSIGN_RETURN_ROUTE".format(msg.expectedCallbackId), _data[2],  REQUEST, FUNC_ID_ZW_ASSIGN_RETURN_ROUTE)
        msg.SetExpectedCallBack(_data[-2])
        if node is not None :
            node.route = [_data[3]]
            msg.Append(msg.expectedCallbackId)
            msg.Append(TRANSMIT_COMPLETE_OK)
            self.SendMsg(msg, MsgQueue.Command)
        else :
            msg.Append(msg.expectedCallbackId)
            msg.Append(TRANSMIT_COMPLETE_NOROUTE)
            self.SendMsg(msg, MsgQueue.Command)

    def HandleNodeNeighborUpdateResponse(self, _data):
        node = self.GetNode(_data[2])
        if node is not None :
            msg = node.getMsgNodeNeighborUpdate(_data[-2])
            msg.SetExpectedCallBack(_data[-2])
            self.SendMsg(msg, MsgQueue.Command, True)
            return False
        else : # Handle A response fail
            threading.Thread(None, self.emulCycleCmd, "th_handleEmulCycleCmd_ctrl_{0}.".format(self.homeId), (),
                                 { 'msgParams': {'logText' : "Z-Wave stack for FUNC_ID_ZW_REQUEST_NODE_NEIGHBOR_UPDATE_OPTIONS",
                                                         'targetNodeId': _data[2],
                                                         'msgType': REQUEST,
                                                         'function' : FUNC_ID_ZW_REQUEST_NODE_NEIGHBOR_UPDATE_OPTIONS,
                                                         'callbackId': _data[-2]},
                                    'listState': [REQUEST_NEIGHBOR_UPDATE_STARTED, REQUEST_NEIGHBOR_UPDATE_FAILED],
                                    'timings': [0.0, 2.0],
                                    'queues' : [MsgQueue.Command, MsgQueue.Command],
                                    'firstNext':  [True, True]
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
        msg = Msg( "Z-Wave stack for FUNC_ID_ZW_ADD_NODE_TO_NETWORK", 0xff,  REQUEST, FUNC_ID_ZW_ADD_NODE_TO_NETWORK)
        if addType == ADD_NODE_STOP :
            if FUNC_ID_ZW_ADD_NODE_TO_NETWORK in self._currentCtrlCommands :
                msg.Append(self._currentCtrlCommands[FUNC_ID_ZW_ADD_NODE_TO_NETWORK].callbackId)
                msg.Append(LEARN_MODE_DONE)
                msg.Append(ADD_NODE_STOP)
                msg.Append(TRANSMIT_COMPLETE_OK)  #0x00
                del self._currentCtrlCommands[FUNC_ID_ZW_ADD_NODE_TO_NETWORK]
#            else :
#                self._log.write(LogLevel.Warning, self, "Receive {ADD_NODE_STOP".format(getFuncName(msgParams['function']), GetDataAsHex([msgParams['function']])))
        else :
            #OPTION_HIGH_POWER			=	0x80    # High power controller for inclusion/exclusion
            #OPTION_NWI				=		0x40	# NWI Inclusion
            self._currentCtrlCommands[FUNC_ID_ZW_ADD_NODE_TO_NETWORK] = ControllerCommandItem(FUNC_ID_ZW_ADD_NODE_TO_NETWORK, _data[3])
            self._currentCtrlCommands[FUNC_ID_ZW_ADD_NODE_TO_NETWORK].highPower = _data[2] & OPTION_HIGH_POWER
            self._currentCtrlCommands[FUNC_ID_ZW_ADD_NODE_TO_NETWORK].options = _data[2] & OPTION_NWI
            self._currentCtrlCommands[FUNC_ID_ZW_ADD_NODE_TO_NETWORK].setCtrlState(ControllerState.Waiting, ADD_NODE_STATUS_LEARN_READY)
            msg.Append(_data[-2]) # Add callbackId
            msg.Append(ADD_NODE_STATUS_LEARN_READY)
            msg.Append(TRANSMIT_COMPLETE_OK)  #0x00
            msg.Append(0x00)  #don't know why
        msg.SetExpectedCallBack(_data[-2])
        self.SendMsg(msg, MsgQueue.NoOp)
        # set driver in include mode
        # wait for inclusion in a thread with stop function and timeout ?
        # memorise callbackID

    def HandleRemoveNodeFromNetworkRequest(self, _data):
        """Start process to exclude a node"""
        #REMOVE_NODE_ANY				= 0x01
        #REMOVE_NODE_CONTROLLER		= 0x02
        #REMOVE_NODE_SLAVE		          = 0x03
        #REMOVE_NODE_STOP			     = 0x05
        RemoveType = _data[2] & 0x07
        msg = Msg( "Z-Wave stack for FUNC_ID_ZW_REMOVE_NODE_FROM_NETWORK", 0xff,  REQUEST, FUNC_ID_ZW_REMOVE_NODE_FROM_NETWORK)
        if RemoveType == REMOVE_NODE_STOP :
            if FUNC_ID_ZW_REMOVE_NODE_FROM_NETWORK in self._currentCtrlCommands :
                if _data[-2] != self._currentCtrlCommands[FUNC_ID_ZW_REMOVE_NODE_FROM_NETWORK].callbackId:
                    # Controller receive a new command (cancel) from client, callbackId has changed
                    self._currentCtrlCommands[FUNC_ID_ZW_REMOVE_NODE_FROM_NETWORK].callbackId = _data[-2]
                msg.Append(self._currentCtrlCommands[FUNC_ID_ZW_REMOVE_NODE_FROM_NETWORK].callbackId)
                msg.Append(REMOVE_NODE_STATUS_DONE)
                msg.Append(0x00) # TODO: Must check if a node has been removing and insert it in case
                msg.Append(TRANSMIT_COMPLETE_OK)  #0x00
                del self._currentCtrlCommands[FUNC_ID_ZW_REMOVE_NODE_FROM_NETWORK]
#            else :
#                self._log.write(LogLevel.Warning, self, "Receive {ADD_NODE_STOP".format(getFuncName(msgParams['function']), GetDataAsHex([msgParams['function']])))
        else :
            #OPTION_HIGH_POWER			=	0x80    # High power controller for inclusion/exclusion
            self._currentCtrlCommands[FUNC_ID_ZW_REMOVE_NODE_FROM_NETWORK] = ControllerCommandItem(FUNC_ID_ZW_REMOVE_NODE_FROM_NETWORK, _data[-2])
            self._currentCtrlCommands[FUNC_ID_ZW_REMOVE_NODE_FROM_NETWORK].highPower = _data[2] & OPTION_HIGH_POWER
            self._currentCtrlCommands[FUNC_ID_ZW_REMOVE_NODE_FROM_NETWORK].setCtrlState(ControllerState.Waiting, REMOVE_NODE_STATUS_LEARN_READY)
            msg.Append(_data[-2]) # Add callbackId
            msg.Append(REMOVE_NODE_STATUS_LEARN_READY)
            msg.Append(TRANSMIT_COMPLETE_OK)  #0x00
            msg.Append(0x00)  #don't know why
        msg.SetExpectedCallBack(_data[-2])
        self.SendMsg(msg, MsgQueue.NoOp)
        # set driver in include mode
        # wait for inclusion in a thread with stop function and timeout ?
        # memorise callbackID

    def HandleIsFailedNodeResponse(self, _data):
        node = self.GetNode(_data[2])
        msg = Msg( "Z-Wave stack for FUNC_ID_ZW_IS_FAILED_NODE_ID ", _data[2],  RESPONSE, FUNC_ID_ZW_IS_FAILED_NODE_ID)
        if node is not None :
            state = FAILED_NODE_NOT_FOUND if node.IsFailed else FAILED_NODE_OK
            msg.Append(state)
            msg.Append(_data[2])
            self.SendMsg(msg, MsgQueue.Command, True)
        else : # Handle A response fail , Seems no possible response in zwave protocol , so send node OK
            msg.Append(FAILED_NODE_OK)
            msg.Append(_data[2])
            self.SendMsg(msg, MsgQueue.Command, True)

    def HandleRemoveFailedNodeResponse(self, _data):
        node = self.GetNode(_data[2])
        msg = Msg( "Z-Wave stack for FUNC_ID_ZW_REMOVE_FAILED_NODE_ID ", _data[2],  RESPONSE, FUNC_ID_ZW_REMOVE_FAILED_NODE_ID)
        if node is not None :
            self._currentCtrlCommands[FUNC_ID_ZW_REMOVE_FAILED_NODE_ID] = ControllerCommandItem(FUNC_ID_ZW_REMOVE_FAILED_NODE_ID, _data[-2], node.nodeId)
            state = FAILED_NODE_REMOVE_STARTED if node.IsFailed else FAILED_NODE_NOT_FOUND
            self._currentCtrlCommands[FUNC_ID_ZW_REMOVE_FAILED_NODE_ID].setCtrlState(ControllerState.Waiting, state)
            msg.Append(state)
            msg.Append(_data[2])
            msg.SetExpectedCallBack(_data[-2])
            self.SendMsg(msg, MsgQueue.Command, True)
            if node.IsFailed :
                threading.Thread(None, self.waitForStepCmd, "th_handleWaitForStepCmd_ctrl_{0}.".format(self.homeId), (),
                    {'callback': self.terminateRemoveFaileNode,
                      'timing' : 0.5
                    }).start()
        else : # Handle A response fail , Seems no possible response in zwave protocol , so send fail
            msg.Append(FAILED_NODE_REMOVE_FAIL)
            self.SendMsg(msg, MsgQueue.Command, True)

    def HandleReplaceFailedNodeResponse(self, _data):
        node = self.GetNode(_data[2])
        msg = Msg( "Z-Wave stack for FUNC_ID_ZW_REPLACE_FAILED_NODE ", _data[2], RESPONSE, FUNC_ID_ZW_REPLACE_FAILED_NODE)
        if node is not None :
            self._currentCtrlCommands[FUNC_ID_ZW_REPLACE_FAILED_NODE] = ControllerCommandItem(FUNC_ID_ZW_REPLACE_FAILED_NODE, _data[-2], node.nodeId)
            state = FAILED_NODE_REMOVE_STARTED if node.IsFailed else FAILED_NODE_REPLACE_FAILED
            self._currentCtrlCommands[FUNC_ID_ZW_REPLACE_FAILED_NODE].setCtrlState(ControllerState.Waiting, state)
            msg.Append(state)
            msg.SetExpectedCallBack(_data[-2])
            self.SendMsg(msg, MsgQueue.Command, True)
            threading.Thread(None, self.waitForStepCmd, "th_handleWaitForStepCmd_ctrl_{0}.".format(self.homeId), (),
                {'callback': self.handleReplaceFaileNode,
                  'timing' : 0.5
                }).start()
        else : # Handle A response fail , Seems no possible response in zwave protocol , so send fail
            msg.Append(FAILED_NODE_REMOVE_FAIL)
            self.SendMsg(msg, MsgQueue.Command, True)

    def HandleSerialAPIResetRequest(self, _data):
        from random import randrange
        msg = Msg( "Response to FUNC_ID_ZW_SET_DEFAULT", self, REQUEST, FUNC_ID_ZW_SET_DEFAULT)
        msg.Append(_data[2]) # Add CallbackId
        self.SendMsg(msg, MsgQueue.NoOp)
        newHomeId = randrange(0x00, 0xffffffff, 1)
        for n in self._manager.getNodesOfhomeId(self.homeId) :
            if n.nodeId != self._node.nodeId :
                self.UnRegisterNode(n)
        self._manager.resetZwNetwork(self.homeId, newHomeId)
        self.homeId = newHomeId
        self._node.homeId = newHomeId

    def getFirstMsg(self):
        for queue in self.msgQueues :
            for msgQ in self.msgQueues[queue] :
                if msgQ.firstNext : return msgQ
        return None

    def emulCycleCmd(self, msgParams = {},  listState = [], timings = [],  queues = [],  firstNext = False):
        self._log.write(LogLevel.Detail, self, "Start command emulation :{0} ({1})".format(getFuncName(msgParams['function']), GetDataAsHex([msgParams['function']])))
        i = 0
        print "++++ Controller emulCycleCmd kwargs : ", msgParams, listState, timings
        for state in listState:
            self._stop.wait(timings[i])
            if not self._stop.isSet() :
                msg = Msg(msgParams['logText'], msgParams['targetNodeId'], msgParams['msgType'], msgParams['function'])
                if 'callbackId' in msgParams:
                    msg.Append(msgParams['callbackId'])
                    msg.SetExpectedCallBack(msgParams['callbackId'])
                msg.Append(listState[i])
                self.SendMsg(msg, queues[i], firstNext[i], timings[i])
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


    def __init__(self,  logText, targetNodeId, msgType, function, _bReplyRequired = True, _expectedReply = 0, _expectedCommandClassId = 0):

#        Callback for normal messages start at 10. Special Messages using a Callback prior to 10 */
        self.s_nextCallbackId = 10

        self._logText = logText
        self._msgType = msgType
        self._function = function
        self._bFinal= False
        self._expectedCallbackId = 0
        self._expectedReply = _expectedReply
        self._expectedCommandClassId = _expectedCommandClassId
        self.m_length = 4
        self._targetNodeId = targetNodeId
        self.m_sendAttempts = 0
        self.m_maxSendAttempts = MAX_TRIES
        self.m_instance = 1
        self.m_endPoint = 0
        self.m_flags = 0
        if _bReplyRequired:
            # Wait for this message before considering the transaction complete
            self._expectedReply = _expectedReply if _expectedReply else self._function
        self.m_buffer = [SOF, 0, self._msgType, self._function]

    GetTargetNodeId = property(lambda self: self._targetNodeId)
    expectedCallbackId = property(lambda self: self._expectedCallbackId)
    expectedReply = property(lambda self: self._expectedReply)
    expectedCommandClassId = property(lambda self: self._expectedCommandClassId)


    def SetExpectedCallBack(self, expectedCallbackId = 0, expectedReply = 0, expectedCommandClassId = 0):
        self._expectedCallbackId = expectedCallbackId
        self._expectedReply = expectedReply
        self._expectedCommandClassId = expectedCommandClassId

    def Finalize(self):
        """Fill in the length and checksum values for the message"""

        if not self._bFinal: # Already finalized ?
           # Deal with Multi-Channel/Instance encapsulation
            if (self.m_flags & ( self.m_MultiChannel | self.m_MultiInstance ) ) != 0:
#                MultiEncap()
                pass
            # Set the length byte
            self.m_buffer[1] = self.m_length - 1		# Length of following data
            # Calculate the checksum
            checksum = 0xff
            for i in range(1, self.m_length) :
                checksum ^= self.m_buffer[i]
            self.m_buffer.append(checksum)
            self.m_length += 1
            self._bFinal = True

    def Append(self,  _data):
        self.m_buffer.append(int(_data))
        self.m_length += 1

    def GetSendingCommandClass(self):
        if self.m_buffer[3] == 0x13 :
            return self.m_buffer[6]
        return 0

    def GetAsString(self):
        strVal = self._logText
        if self. _targetNodeId != 0xff:
            strVal += " (Node={0})".format(self._targetNodeId)
        strVal += ": "
        for i in range(0, self.m_length) :
            if i : strVal += ", "
            strVal += "0x%.2x"%self.m_buffer[i]
        return strVal

    def IsNoOperation(self):
        return (self._bFinal and (self.m_length==11) and (self.m_buffer[3]==0x13) and (self.m_buffer[6]==0x00) and (self.m_buffer[7]==0x00))

class MsgQueueItem:

    def __init__(self, msg, queue, firstNext = False, timeOut = 0):
        self.msg = msg
        self.firstNext = firstNext
        self.queue = queue
        self.timeOut = timeOut

    nodeId  = property(lambda self: 0 if self.msg is None else self.msg._targetNodeId)


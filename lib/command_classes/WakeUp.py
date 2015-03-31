# -*- coding: utf-8 -*-

"""
.. module:: libopenzwave

This file is part of **python-openzwave-emulator** project http:#github.com/p/python-openzwave-emulator.
    :platform: Unix, Windows, MacOS X
    :sinopsis: openzwave simulator Python

This project is based on python-openzwave to pass thought hardware zwace device. It use for API developping or testing.
All C++ and cython code are moved.

.. moduleauthor: Nico0084 <nico84dev@gmail.com>
.. moduleauthor: bibi21000 aka Sébastien GALLET <bibi21000@gmail.com>
.. moduleauthor: Maarten Damen <m.damen@gmail.com>

License : GPL(v3)

**python-openzwave** is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

**python-openzwave** is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with python-openzwave. If not, see http:#www.gnu.org/licenses.

"""

from zwemulator.lib.defs import *
from zwemulator.lib.notification import Notification, NotificationType
from zwemulator.lib.log import LogLevel
from zwemulator.lib.driver import MsgQueue, Msg
from commandclass import CommandClass
import threading
import time

class WakeUpCmd(EnumNamed):
	IntervalSet		= 0x04
	IntervalGet		= 0x05
	IntervalReport	= 0x06
	Notification		= 0x07
	NoMoreInformation	= 0x08
	IntervalCapabilitiesGet = 0x09
	IntervalCapabilitiesReport = 0x0A


class WakeUp(CommandClass):
    
    StaticGetCommandClassId = 0x84
    StaticGetCommandClassName = "COMMAND_CLASS_WAKE_UP"
    
    def __init__(self, node,  data):
        import random
        
        CommandClass.__init__(self, node, data)
        if self._node.emulData:
            self.timeoutWakeUp = self._node.emulData['timeoutwakeup']
            self.WakeupDuration = self._node.emulData['wakeupduration']
        else :
            self.timeoutWakeUp= random.randint(30,120)
            self.WakeupDuration = random.randint(10,30)
        self._running = False
        self._lastTime = time.time()
        
        self.m_mutex = None
        self.m_pollRequired = False
        self.m_notification = False
        find, self.m_awake = self._node._manager._options.GetOptionAsBool("AssumeAwake")
        if not find : self.m_awake = True
        self.m_pendingQueue = []
        self.SetStaticRequest(self.StaticRequest_Values)
        threading.Thread(None, self.handleWakeCycle, "th_handleWakeCycle_node_{0}.".format(self.nodeId), (), {}).start()
        
    GetCommandClassId = property(lambda self: self.StaticGetCommandClassId)
    GetCommandClassName = property(lambda self: self.StaticGetCommandClassName)
    IsAwake = property(lambda self: self.m_awake)
    
    def Init(self):
        """Starts the process of requesting node state from a sleeping device"""
        # Request the wake up interval.  When we receive the response, we
        # can send a set interval message with the same interval, but with
        # the target node id set to that of the controller.  This will ensure
        # that the controller will receive the wake-up notifications from
        # the device.  Once this is done, we can request the rest of the node
        # state.
        self.RequestState(self.RequestFlag_Session, 1, MsgQueue.WakeUp );

    def getFullNameCmd(self,  _id):
        return WakeUpCmd().getFullName(_id)

    def RequestState(self, _requestFlags, _instance, _queue):
        """Nothing to do for wakeup"""
        if (_requestFlags & self.RequestFlag_Static) and self.HasStaticRequest(self.StaticRequest_Values) :
            if self.m_version > 1:
                requests |= self.RequestValue( _requestFlags, WakeUpCmd.IntervalCapabilitiesGet, _instance, _queue )
        if _requestFlags & RequestFlag_Session:
            if (self._node is not None) and not self._node.IsController():
                requests |= self.RequestValue( _requestFlags, 0, _instance, _queue )
        return requests
    
    def ProcessMsg(self, _data, instance=1, multiInstanceData = []):
        print '++++++++++++++++ WakeUp ProcessMsg +++++++++++++++'
        if _data[0] == WakeUpCmd.IntervalGet: 
            msg = Msg("WakeUpCmd_IntervalReport", self.nodeId,  REQUEST, FUNC_ID_APPLICATION_COMMAND_HANDLER, False)
            vInterval = self._node.getValue(self.GetCommandClassId, instance, 0)
            interval = vInterval.getValueByte()
            msgData = vInterval.getValueHex(24)
            msg.Append(TRANSMIT_COMPLETE_OK)
            msg.Append(self.nodeId)
            msg.Append(6)
            msg.Append(self.GetCommandClassId)
            msg.Append(WakeUpCmd.IntervalReport)
            for v in msgData[1:]:
                msg.Append(v)
            msg.Append(self.GetDriver.nodeId)
            self.GetDriver.SendMsg(msg, MsgQueue.NoOp)
        elif _data[0] == WakeUpCmd.NoMoreInformation:
            self._log.write(LogLevel.Detail, self, "WakeUpCmd.NoMoreInformation received, go to sleep for {0}s.".format(self.timeoutWakeUp))
            self._lastTime = time.time()
            self.m_awake = False
        else:
            self._log.write(LogLevel.Warning, self, "CommandClass REQUEST {0}, Not implemented : {1}".format(self.getFullNameCmd(_data[0]), GetDataAsHex(_data)))


    def RequestValue(self, _requestFlags, _getTypeEnum, _instance, _queue):
        """Nothing to do for wakeup"""
        if _instance != 1:
            # This command class doesn't work with multiple instances
            return False
        if _getTypeEnum == WakeUpCmd.IntervalCapabilitiesGet:
            msg = Msg( "WakeUpCmd_IntervalCapabilityGet", self.nodeId, REQUEST, FUNC_ID_ZW_SEND_DATA, True, True, FUNC_ID_APPLICATION_COMMAND_HANDLER, self.GetCommandClassId)
            msg.Append(self.nodeId)
            msg.Append( 2 )
            msg.Append(self.GetCommandClassId)
            msg.Append(WakeUpCmd.IntervalCapabilitiesGet)
            msg.Append(self.GetDriver.GetTransmitOptions())
            self.GetDriver.SendMsg(msg, _queue)

        if _getTypeEnum == 0:
            # We won't get a response until the device next wakes up
            msg = Msg( "WakeUpCmd_IntervalGet", self.nodeId, REQUEST, FUNC_ID_ZW_SEND_DATA, true, true, FUNC_ID_APPLICATION_COMMAND_HANDLER, self.GetCommandClassId)
            msg.Append(self.nodeId)
            msg.Append( 2 )
            msg.Append(self.GetCommandClassId)
            msg.Append(WakeUpCmd.IntervalGet )
            msg.Append(self.GetDriver.GetTransmitOptions)
            self.GetDriver.SendMsg(msg, _queue)
            return True
        return False

    def SetAwake(self, _state):
        if self.m_awake != _state:
            self.m_awake = _state
            self._log.write(LogLevel.Info, self._node, "  Node {0} has been marked as {1}".format(self.nodeId, "awake" if self.m_awake else "asleep"))
            notification = Notification(NotificationType.Type_Notification, self)
            notification.SetNotification(NotificationCode.Awake if self.m_awake else NotificationCode.Sleep)
            self._node._manager._watchers.dispatchNotification(notification)
        if self.m_awake :
            # If the device is marked for polling, request the current state
            if self.m_pollRequired:
                if self._node is not None:
                    self._node.SetQueryStage(QueryStage.Dynamic)
                self.m_pollRequired = false
            # Send all pending messages
            self.SendPending()

    def SendPending(self):
        # The device is awake, so send all the pending messages
        pass # TODO: à implementer...
    
    def SendWakeUp(self):
        if self.GetDriver is not None :
            msg = Msg( "Send Wakeup Notification", self.nodeId,  REQUEST, FUNC_ID_APPLICATION_COMMAND_HANDLER, False)
            msg.Append(TRANSMIT_COMPLETE_OK) # 0x00
            msg.Append(self.nodeId)
            msg.Append(0x02)
            msg.Append(self.GetCommandClassId)
            msg.Append(WakeUpCmd.Notification)
            self.GetDriver.SendMsg(msg, MsgQueue.NoOp)

    def QueueMsg(self, _item):
        # Add a Z-Wave message to the queue
#        self.m_mutex.Lock()
        # See if there is already a copy of this message in the queue.  If so, 
        # we delete it.  This is to prevent duplicates building up if the 
        # device does not wake up very often.  Deleting the original and
        # adding the copy to the end avoids problems with the order of
        # commands such as on and off.
#        erase = []
#        for item in self.m_pendingQueue:
#            if item == _item:
#                # Duplicate found
#                if MsgQueueCmd.SendMsg == item.m_command :
#                    item.m_msg = None
#                elif MsgQueueCmd.Controller == item.m_command:
#                    item.m_cci = None
#                    erase.append(item)
#        if erase:
#            for item in erase:
#                self.m_pendingQueue.remove(item)
#        self.m_pendingQueue.append( _item)
#        sef.m_mutex.Unlock()
        pass
    
    def ResetLastTime(self):
        self._lastTime = time.time()
        self._log.write(LogLevel.Debug, self._node, "Msg Received, time wakeup reset ({0}s).".format(self.WakeupDuration))
    
    def handleWakeCycle(self):
        if self.timeoutWakeUp == 0 : 
            self.m_awake = True
            self._log.write(LogLevel.Detail, self._node, "WakeUp cycle, node is always wake up.")
        else : 
            self._log.write(LogLevel.Detail, self._node, "Start WakeUp cycle every {0}s, during {1}s from last message.".format(self.timeoutWakeUp, self.WakeupDuration))
            self._running = True
            self._lastTime = time.time()        
            while not self._stop.isSet() and self._running:
                t = time.time()
                if t  >= self._lastTime + self.timeoutWakeUp :
                    self._lastTime = t
                    if not self._node.IsFailed :
                        self.m_awake = True
                        self._log.write(LogLevel.Debug, self._node, "Wake up for {0}s".format(self.WakeupDuration))
                        self.SendWakeUp()
                elif self.m_awake and (t > self._lastTime + self.WakeupDuration) : 
                    self.m_awake = False
                    self._log.write(LogLevel.Debug, self._node, "Start sleeping for {0}s.".format(self.timeoutWakeUp))
                self._stop.wait(0.1)
        self._log.write(LogLevel.Detail, self._node, "Stop WakeUp cycle.")

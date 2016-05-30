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
            msg = Msg("WakeUpCmd_IntervalReport", self.nodeId,  REQUEST, FUNC_ID_APPLICATION_COMMAND_HANDLER)
            vInterval = self._node.getValue(self.GetCommandClassId, instance, 0)
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
        elif _data[0] == WakeUpCmd.IntervalCapabilitiesGet:
            msg = Msg("WakeUpCmd_IntervalCapabilitiesReport", self.nodeId,  REQUEST, FUNC_ID_APPLICATION_COMMAND_HANDLER)
            msgData = []
            for i in range(1, 5) : # get value for capabilities index 1 to 4
                value = self._node.getValue(self.GetCommandClassId, instance, i)
                msgData.extend(value.getValueHex(24)[1:])
            msg.Append(TRANSMIT_COMPLETE_OK)
            msg.Append(self.nodeId)
            msg.Append(2 + len(msgData))
            msg.Append(self.GetCommandClassId)
            msg.Append(WakeUpCmd.IntervalCapabilitiesReport)
            for v in msgData:
                msg.Append(v)
            msg.Append(self.GetDriver.nodeId)
            self.GetDriver.SendMsg(msg, MsgQueue.NoOp)
        else:
            self._log.write(LogLevel.Warning, self, "CommandClass REQUEST {0}, Not implemented : {1}".format(self.getFullNameCmd(_data[0]), GetDataAsHex(_data)))


    def RequestValue(self, _requestFlags, _getTypeEnum, _instance, _queue):
        """Nothing to do for wakeup"""
        if _instance != 1:
            # This command class doesn't work with multiple instances
            return False
        if _getTypeEnum == WakeUpCmd.IntervalCapabilitiesGet:
            msg = Msg( "WakeUpCmd_IntervalCapabilityGet", self.nodeId, REQUEST, FUNC_ID_ZW_SEND_DATA, True, FUNC_ID_APPLICATION_COMMAND_HANDLER, self.GetCommandClassId)
            msg.Append(self.nodeId)
            msg.Append( 2 )
            msg.Append(self.GetCommandClassId)
            msg.Append(WakeUpCmd.IntervalCapabilitiesGet)
            msg.Append(self.GetDriver.GetTransmitOptions())
            msg.Append(self.GetDriver.getNextCallbackId())
            self.GetDriver.SendMsg(msg, _queue)

        if _getTypeEnum == 0:
            # We won't get a response until the device next wakes up
            msg = Msg( "WakeUpCmd_IntervalGet", self.nodeId, REQUEST, FUNC_ID_ZW_SEND_DATA, True, FUNC_ID_APPLICATION_COMMAND_HANDLER, self.GetCommandClassId)
            msg.Append(self.nodeId)
            msg.Append( 2 )
            msg.Append(self.GetCommandClassId)
            msg.Append(WakeUpCmd.IntervalGet )
            msg.Append(self.GetDriver.GetTransmitOptions)
            msg.Append(self.GetDriver.getNextCallbackId())
            self.GetDriver.SendMsg(msg, _queue)
            return True
        return False

    def SetAwake(self, _state):
        if self.m_awake != _state:
            self.m_awake = _state
            self._log.write(LogLevel.Info, self._node, "  Node {0} has been marked as {1}".format(self.nodeId, "awake" if self.m_awake else "asleep"))

    def SendWakeUp(self):
        if self.GetDriver is not None :
            msg = Msg( "Send Wakeup Notification", self.nodeId,  REQUEST, FUNC_ID_APPLICATION_COMMAND_HANDLER)
            msg.Append(TRANSMIT_COMPLETE_OK) # 0x00
            msg.Append(self.nodeId)
            msg.Append(0x02)
            msg.Append(self.GetCommandClassId)
            msg.Append(WakeUpCmd.Notification)
            self.GetDriver.SendMsg(msg, MsgQueue.WakeUp)

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
                time.sleep(0.1)
        self._log.write(LogLevel.Detail, self._node, "Stop WakeUp cycle.")

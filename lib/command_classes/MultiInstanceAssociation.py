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

class MultiInstanceAssociationCmd:
	Set				= 0x01
	Get				= 0x02
	Report			= 0x03
	Remove			= 0x04
	GroupingsGet	= 0x05
	GroupingsReport	= 0x06

class MultiInstanceAssociation(CommandClass):

    StaticGetCommandClassId = 0x8e
    StaticGetCommandClassName = "COMMAND_CLASS_MULTI_INSTANCE_ASSOCIATION"

    def __init__(self, node,  data):
        CommandClass.__init__(self, node, data)

    GetCommandClassId = property(lambda self: self.StaticGetCommandClassId)
    GetCommandClassName = property(lambda self: self.StaticGetCommandClassName)

    def getFullNameCmd(self,  _id):
        return MultiInstanceAssociationCmd().getFullName(_id)

    def ProcessMsg(self, _data, instance=1, multiInstanceData = []):
        print '++++++++++++++++ Multi Instance Association ProcessMsg +++++++++++++++'
        if _data[0] == MultiInstanceAssociationCmd.Get:
            cAss = self._node.GetCommandClass(0x85) # COMMAND_CLASS_ASSOCIATION
            group = cAss.getGroup(_data[1]) # _data[1] group index
            if group is not None :
                msg = Msg("Multi_Instance_Association_report", self.nodeId,  REQUEST, FUNC_ID_APPLICATION_COMMAND_HANDLER)
                msg.Append(TRANSMIT_COMPLETE_OK)
                msg.Append(self.nodeId)
                size = 0
                nodes = []
                nodes_i = []
                for n in group['nodes']:
                    if n['instance'] == 0x00 :
                        nodes.append(n)
                        size += 1
                    else :
                        nodes_i.append(n)
                        size += 2
                if nodes_i : size += 1 # add multi-instance marker place
                msg.Append(size + 5)
                msg.Append(self.GetCommandClassId)
                msg.Append(MultiInstanceAssociationCmd.Report)
    #            data = self._node.getValue(self.GetCommandClassId, instance, _data[1]).getValueByte() #_data[1] groupe index
                msg.Append(group['index'])
                msg.Append(group['max_associations'])
                msg.Append(0) # TODO: numReportsToFollow , If a device supports a lot of associations, they may come in more than one message.
                for n in nodes:
                    msg.Append(n['id'])
                if  nodes_i :
                    msg.Append(0x00)  # multi-instance marker
                    for n in  nodes_i:
                        msg.Append(n['id'])
                        msg.Append(n['instance'])
                self.GetDriver.SendMsg(msg, MsgQueue.NoOp)
            else :
                msg = Msg("Multi_Instance_Association_Report", self.nodeId,  REQUEST, FUNC_ID_APPLICATION_COMMAND_HANDLER)
                msg.Append(TRANSMIT_COMPLETE_NOT_IDLE)
                msg.Append(self.nodeId)
                msg.Append(2)
                msg.Append(self.GetCommandClassId)
                msg.Append(MultiInstanceAssociationCmd.Report)
                self.GetDriver.SendMsg(msg, MsgQueue.NoOp)
                self._log.write(LogLevel.Warning, self._node, "Group index {0} don't exist, Data : {1}".format(_data[1],  GetDataAsHex(_data)))
        elif _data[0] == MultiInstanceAssociationCmd.GroupingsGet:
            cAss = self._node.GetCommandClass(0x85) # COMMAND_CLASS_ASSOCIATION
            msg = Msg("Multi_Instance_Association_Report", self.nodeId,  REQUEST, FUNC_ID_APPLICATION_COMMAND_HANDLER)
            msg.Append(TRANSMIT_COMPLETE_OK)
            msg.Append(self.nodeId)
            msg.Append(0x03)
            msg.Append(self.GetCommandClassId)
            msg.Append(MultiInstanceAssociationCmd.GroupingsReport)
            msg.Append(cAss.m_numGroups)
            self.GetDriver.SendMsg(msg, MsgQueue.NoOp)

        elif _data[0] == MultiInstanceAssociationCmd.Set:
#            _data[1] = group index
            cAss = self._node.GetCommandClass(0x85) # COMMAND_CLASS_ASSOCIATION
            if _data[2] == 0x00 : # marker 0x00 for instance _data[3] = nodeId, _data[4] = instance
                if cAss.addNodeInGroup(_data[1], _data[3], _data[4]) :
                    self._log.write(LogLevel.Info, self._node,"Add node {0} multi-instance {1} to group index {2}".format(_data[3], _data[4], _data[1]))
                else :
                    self._log.write(LogLevel.Info, self._node,"Node {0} multi-instance {1} allready in group index {2}".format(_data[2], _data[4], _data[1]))
            else : #" _data[2] = nodeId
                if cAss.addNodeInGroup(_data[1], _data[2]) :
                    self._log.write(LogLevel.Info, self._node,"Add node {0} to group index {1}".format(_data[2], _data[1]))
                else :
                    self._log.write(LogLevel.Info, self._node,"Node {0} allready in group index {1}".format(_data[2], _data[1]))
        elif _data[0] == MultiInstanceAssociationCmd.Remove:
#            _data[1] = group index
            cAss = self._node.GetCommandClass(0x85) # COMMAND_CLASS_ASSOCIATION
            if _data[2] == 0x00 : # marker 0x00 for instance _data[3] = nodeId, _data[4] = instance
                if cAss.removeNodeInGroup(_data[1], _data[3], _data[4]) :
                    self._log.write(LogLevel.Info, self._node,"Remove node {0} multi-instance {1} from group index {2}".format(_data[3], _data[4], _data[1]))
                else :
                    self._log.write(LogLevel.Info, self._node,"Node {0} multi-instance {1} not in group index {2}".format(_data[2], _data[4], _data[1]))
            else : #" _data[2] = nodeId
                if cAss.removeNodeInGroup(_data[1], _data[2]) :
                    self._log.write(LogLevel.Info, self._node,"Remove node {0} from group index {1}".format(_data[2], _data[1]))
                else :
                    self._log.write(LogLevel.Info, self._node,"Node {0} not in group index {1}".format(_data[2], _data[1]))


        else:
            self._log.write(LogLevel.Warning, self, "CommandClass REQUEST {0}, Not implemented : {1}".format(self.getFullNameCmd(_data[0]), GetDataAsHex(_data)))


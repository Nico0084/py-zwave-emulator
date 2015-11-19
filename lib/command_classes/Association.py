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
from commandclass import CommandClass

class AssociationCmd(EnumNamed):
	Set				= 0x01
	Get				= 0x02
	Report			= 0x03
	Remove			= 0x04
	GroupingsGet		= 0x05
	GroupingsReport	= 0x06

class Association(CommandClass):

    StaticGetCommandClassId = 0x85
    StaticGetCommandClassName = "COMMAND_CLASS_ASSOCIATION"

    def __init__(self, node,  data):
        CommandClass.__init__(self, node, data)
        self.m_numGroups = data['associations']['num_groups']
        self.groups = data['associations']['groups']
        # Add multiInstance if necessary
        for group in self.groups :
            for node in group['nodes']:
                if 'instance' not in node : node['instance'] = 0x00

    GetCommandClassId = property(lambda self: self.StaticGetCommandClassId)
    GetCommandClassName = property(lambda self: self.StaticGetCommandClassName)

    def getFullNameCmd(self,  _id):
        return AssociationCmd().getFullName(_id)

    def getGroup(self, groupIdx):
        for g in self.groups:
            if g['index'] == groupIdx: return g
        return None

    def isNodeInGroup(self, group, id, instance = 0x00):
        for n in group['nodes'] :
            if n['id'] == id and n['instance'] == instance : return n
        return None

    def addNodeInGroup(self, groupIdx, id, instance = 0x00):
        for g in self.groups:
            if g['index'] == groupIdx:
                if self.isNodeInGroup(g, id, instance) is None :
                    g['nodes'].append({'id': id, 'instance': instance})
                    return True
        return False

    def removeNodeInGroup(self, groupIdx, id, instance = 0x00):
        for g in self.groups:
            if g['index'] == groupIdx:
                n = self.isNodeInGroup(g, id, instance)
                if n is not None :
                    g['nodes'].remove(n)
                    return True
        return False

    def Reset(self):
        for group  in self.groups:
            group['nodes'] = []

    def SetGroupKey(self, groupIdx, key, value):
        for g in self.groups:
            if g['index'] == groupIdx:
                if key in g:
                    print type(value), type(g[key])
                    if type(value) == type(g[key]):
                        g[key] = value
                        return True,  ""
                    else : return False, "In group index {0} key {1} value type ({2}) not corresponding to original type ({3}).".format(groupIdx, key, type(value).__name__, type(g[key]).__name__)
                else : return False, "In group index {0} key {1} doesn't exist.".format(groupIdx,  key)
        return False, "Group index {0} doesn't exist.".format(groupIdx)

    def ProcessMsg(self, _data, instance=1):
        if _data[0] == AssociationCmd.Get:
            group = self.getGroup(_data[1])
            if group is not None :
                msg = Msg("Association_Report", self.nodeId,  REQUEST, FUNC_ID_APPLICATION_COMMAND_HANDLER)
                msg.Append(TRANSMIT_COMPLETE_OK)
                msg.Append(self.nodeId)
                msg.Append(len(group['nodes']) + 5)
                msg.Append(self.GetCommandClassId)
                msg.Append(AssociationCmd.Report)
                msg.Append(group['index'])
                msg.Append(group['max_associations'])
                msg.Append(0x00) # TODO: numReportsToFollow , If a device supports a lot of associations, they may come in more than one message. don't known how to do ?
                for n in group['nodes']:
                    msg.Append(n['id'])
                self.GetDriver.SendMsg(msg, MsgQueue.NoOp)
            else :
                msg = Msg("Association_Report", self.nodeId,  REQUEST, FUNC_ID_APPLICATION_COMMAND_HANDLER)
                msg.Append(TRANSMIT_COMPLETE_NOT_IDLE)
                msg.Append(self.nodeId)
                msg.Append(2)
                msg.Append(self.GetCommandClassId)
                msg.Append(AssociationCmd.Report)
                self.GetDriver.SendMsg(msg, MsgQueue.NoOp)
                self._log.write(LogLevel.Warning, self._node, "Group index {0} don't exist, Data : {1}".format(_data[1],  GetDataAsHex(_data)))
        elif _data[0] == AssociationCmd.GroupingsGet:
            msg = Msg("Association_GroupingsReport", self.nodeId,  REQUEST, FUNC_ID_APPLICATION_COMMAND_HANDLER)
            msg.Append(TRANSMIT_COMPLETE_OK)
            msg.Append(self.nodeId)
            msg.Append(0x03)
            msg.Append(self.GetCommandClassId)
            msg.Append(AssociationCmd.GroupingsReport)
            msg.Append(self.m_numGroups)
            self.GetDriver.SendMsg(msg, MsgQueue.NoOp)

        elif _data[0] == AssociationCmd.Set:
#            _data[1] = group index, _data[2] = nodeId
            if self.addNodeInGroup(_data[1], _data[2]):
                self._log.write(LogLevel.Info, self._node,"Add node {0} to group index {1}".format(_data[2], _data[1]))
            else :
                self._log.write(LogLevel.Info, self._node,"Node {0} allready in group index {1}".format(_data[2], _data[1]))
        elif _data[0] == AssociationCmd.Remove:
#            _data[1] = group index, _data[2] = nodeId
            if self.removeNodeInGroup(_data[1], _data[2]):
                self._log.write(LogLevel.Info, self._node,"Remove node {0} from group index {1}".format(_data[2], _data[1]))
            else :
                self._log.write(LogLevel.Info, self._node,"Node {0} not in group index {1}".format(_data[2], _data[1]))

        else:
            self._log.write(LogLevel.Warning, self, "CommandClass REQUEST {0}, Not implemented : {1}".format(self.getFullNameCmd(_data[0]), GetDataAsHex(_data)))

#-*- coding: utf-8 -*-

"""
.. module:: libopenzwave

This file is part of **python-openzwave-emulator** project http://github.com/p/python-openzwave-emulator.
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
along with python-openzwave. If not, see http://www.gnu.org/licenses.

"""
#from libc.stdint cimport uint32_t, uint64_t, int32_t, int16_t, uint8_t, int8_t
#from mylibc cimport string
#from libcpp cimport bool
#cdef extern from *:
#    ctypedef char* const_notification "OpenZWave::Notification const*"
#
#ctypedef void (*pfnOnNotification_t)(const_notification _pNotification, void* _context )
from zwemulator.lib.defs import *

class NotificationType(EnumNamed):
    ValueAdded = 0                     # A new node value has been added to OpenZWave's list. These notifications occur after a node has been discovered, and details of its command classes have been received.  Each command class may generate one or more values depending on the complexity of the item being represented.
    ValueRemoved = 1                   # A node value has been removed from OpenZWave's list.  This only occurs when a node is removed.
    ValueChanged = 2                   # A node value has been updated from the Z-Wave network and it is different from the previous value.
    ValueRefreshed = 3                 # A node value has been updated from the Z-Wave network.
    Group = 4                          # The associations for the node have changed. The application should rebuild any group information it holds about the node.
    NodeNew = 5                        # A new node has been found (not already stored in zwcfg*.xml file)
    NodeAdded = 6                      # A new node has been added to OpenZWave's list.  This may be due to a device being added to the Z-Wave network, or because the application is initializing itself.
    NodeRemoved = 7                    # A node has been removed from OpenZWave's list.  This may be due to a device being removed from the Z-Wave network, or because the application is closing.
    NodeProtocolInfo = 8               # Basic node information has been receievd, such as whether the node is a listening device, a routing device and its baud rate and basic, generic and specific types. It is after this notification that you can call Manager::GetNodeType to obtain a label containing the device description.
    NodeNaming = 9                     # One of the node names has changed (name, manufacturer, product).
    NodeEvent = 10                     # A node has triggered an event.  This is commonly caused when a node sends a Basic_Set command to the controller.  The event value is stored in the notification.
    PollingDisabled = 11               # Polling of a node has been successfully turned off by a call to Manager::DisablePoll
    PollingEnabled = 12                # Polling of a node has been successfully turned on by a call to Manager::EnablePoll
    SceneEvent = 13                    # Scene Activation Set received
    CreateButton = 14                  # Handheld controller button event created
    DeleteButton = 15                  # Handheld controller button event deleted
    ButtonOn = 16                      # Handheld controller button on pressed event
    ButtonOff = 17                     # Handheld controller button off pressed event
    DriverReady = 18                   # A driver for a PC Z-Wave controller has been added and is ready to use.  The notification will contain the controller's Home ID, which is needed to call most of the Manager methods.
    DriverFailed = 19                  # Driver failed to load
    DriverReset = 20                   # All nodes and values for this driver have been removed.  This is sent instead of potentially hundreds of individual node and value notifications.
    EssentialNodeQueriesComplete = 21  # The queries on a node that are essential to its operation have been completed. The node can now handle incoming messages.
    NodeQueriesComplete = 22           # All the initialisation queries on a node have been completed.
    AwakeNodesQueried = 23             # All awake nodes have been queried, so client application can expected complete data for these nodes.
    AllNodesQueried = 24               # All nodes have been queried, so client application can expected complete data.
    AllNodesQueriedSomeDead = 25       # All nodes have been queried but some dead nodes found.
    Notification = 26                  # A manager notification report.
    DriverRemoved = 27                 # The Driver is being removed. (either due to Error or by request) Do Not Call Any Driver Related Methods after receiving this call.

    def getNotificationType(self,  type):
        if type >= 0 and type < 28:
            for name in NotificationType.__dict__:
                if type == NotificationType.__dict__[name] : return name
        return "Type unknown."
        
class NotificationCode(EnumNamed):
    MsgComplete = 0                    # Completed messages.
    Timeout = 1                        # Messages that timeout will send a Notification with this code.
    NoOperation = 2                    # Report on NoOperation message sent completion.
    Awake = 3                          # Report when a sleeping node wakes.
    Sleep = 4                          # Report when a node goes to sleep.
    Dead = 5                           # Report when a node is presumed dead.
    Alive = 6                          # Report when a node is revived.

class Notification:
    
    def __init__(self, notificationType, obj):
        self.m_type = notificationType
        self._obj = obj
        self.m_valueId = self.GetValueID()
        self.m_byte = 0
    
    def GetType(self): # return  NotificationType
       return self.m_type

    def GetHomeId(self): # return  uint32_t
        if self._obj.__class__.__name__ == "Value":
            return self._obj.homeId
        elif self._obj.__class__.__name__ == "Node":
            return self._obj.homeId
        elif self._obj.__class__.__name__ == "Driver":
            return self._obj.xmlData['homeId']
        else: return 0

    def GetNodeId(self): # return  uint8_t 
        if self._obj.__class__.__name__ == "Value":
            return self._obj.nodeId
        elif self._obj.__class__.__name__ == "Node":
            return self._obj.nodeId
        elif self._obj.__class__.__name__ == "Driver":
            return self._obj.xmlData['nodeId']
        else: return 0

    def GetValueID(self): # return  ValueID& 
        if self._obj.__class__.__name__ == "Value":
            return self._obj.GetId()
        elif self._obj.__class__.__name__ == "Node":
            return self._obj.GetId()
        elif self._obj.__class__.__name__ == "Driver":
            return self._obj.GetId()
        else: return 0

    def GetGroupIdx(self): # return uint8_t  
        return []

    def GetEvent(self): # return uint8_t  
        pass

    def GetButtonId(self): # return  uint8_t
        pass

    def GetSceneId(self): # return  uint8_t 
        pass

    def GetNotification(self): # return  uint8_t 
        pass

    def GetByte(self): # return  uint8_t 
        return self.m_byte

    def SetNotification(self, _noteId):
        if NotificationType == self.m_type:
            self.m_byte = _noteId
            return True
        return False
    
class NotificationsWatcher(object):
    """As singleton"""
    
    instance = None
    
    def __new__(cls, *args, **kargs):
        if  NotificationsWatcher.instance is None:
            NotificationsWatcher.instance = object.__new__(cls, *args, **kargs)
            cls._log = None
            cls._watchers = {}
        return NotificationsWatcher.instance
    
    def __init__(self):
        pass
        
    def addWatcher(self, notif_callback, pythonfunc):
        if pythonfunc in self._watchers:
            return False
        else :
            self._watchers[pythonfunc] = notif_callback
            return True
        
    def dispatchNotification(self,  notification):
        for w in self._watchers:
            self._watchers[w](notification, w)

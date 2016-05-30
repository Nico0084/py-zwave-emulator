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
from lib.defs import *
from lib.log import LogLevel
import random

class ValueGenre(EnumNamed):
    Basic = 0                # The 'level' as controlled by basic commands.  Usually duplicated by another command class.
    User = 1                 # Basic values an ordinary user would be interested in.
    Config = 2               # Device-specific configuration parameters.  These cannot be automatically discovered via Z-Wave, and are usually described in the user manual instead.
    System = 3               # Values of significance only to users who understand the Z-Wave protocol.
    Count = 4                # A count of the number of genres defined.  Not to be used as a genre itself.
    

    def getFromName(self,  item) :# TODO: del when libopenzwave has fix issue 362 related to "all" value
        if item.lower() == 'all': item = 'Basic'
        return EnumNamed.getFromName(self, item)
        
class ValueType(EnumNamed):
    Bool = 0                  # Boolean, true or false
    Byte = 1                  # 8-bit unsigned value
    Decimal = 2               # Represents a non-integer value as a string, to avoid floating point accuracy issues.
    Int = 3                   # 32-bit signed value
    List = 4                  # List from which one item can be selected
    Schedule = 5              # Complex type used with the Climate Control Schedule command class
    Short = 6                 # 16-bit signed value
    String = 7                # Text string
    Button = 8                # A write-only value that is the equivalent of pressing a button to send a command to a device
    Raw = 9                   # Used as a list of Bytes
    Max = Raw       # The highest-number type defined.  Not to be used as a type itself.

class ValueID:
    def __init__(self, value = None):
        self._value = value

    def GetHomeId(self): # return uint32_t
        pass

    def GetNodeId(self): # return uint8_t
        pass

    def GetGenre(self): # return ValueGenre
        pass

    def GetCommandClassId(self): # return uint8_t
        pass

    def GetInstance(self): # return uint8_t
        pass

    def GetIndex(self): # return uint8_t
        pass

    def GetType(self): # return ValueType
        pass

    def GetId(self): # return uint64_t
#                 // ID Packing:
#                // Bits
#                // 24-31:       8 bits. Node ID of device
#                // 22-23:       2 bits. genre of value (see ValueGenre enum).
#                // 14-21:       8 bits. ID of command class that created and manages this value.
#                // 12-13:       2 bits. Unused.
#                // 04-11:       8 bits. Index of value within all the value created by the command class
#                //                  instance (in configuration parameters, this is also the parameter ID).
#                // 00-03:       4 bits. Type of value (bool, byte, string etc).
#                uint32  m_id;
#
#                // ID1 Packing:
#                // Bits
#                // 24-31        8 bits. Instance Index of the command class.
#                uint32  m_id1;
#
#                // Unique PC interface identifier
#                uint32  m_homeId;
        if self._value : return self._value.GetId()
        return 0

class Value:
    
    def __init__(self, node, commandClassId,  data = {}):
        self._node = node
        if 'genre' in  data : self._genre = ValueGenre().getFromName(data['genre'])
        else :self._genre = 0
        if 'instance' in  data : self._instance = int(data['instance'])
        else: self._instance = 0
        if 'index' in  data : self._index =  int(data['index'])
        else: self._index = 0
        if 'type' in  data : self._type = ValueType().getFromName(data['type'])
        else: self._type = 0
        if 'label' in  data : self._label = data['label']
        else: self._label = ""
        if 'units' in  data : self._units = data['units']
        else: self._units = ""
        if 'readOnly' in  data : self._readOnly = True if data['readOnly'] == 'true' else False
        else: self._readOnly = False
        if 'writeOnly' in  data : self._writeOnly = True if data['writeOnly'] == 'true' else False
        else: self._writeOnly = False
        if 'pollIntensity' in  data : self._pollIntensity =  int(data['pollIntensity'])
        else: self._pollIntensity = 0
        if 'min' in  data : self._min = data['min']
        else:self._min = 0
        if 'max' in  data : self._max = data['max']
        else:self._max = 0
        if 'verifyChanges' in  data : self._verifyChanges = True if data['verifyChanges'] == 'true' else False
        else : self._verifyChanges = False
        if 'value' in  data : self._value = data['value']
        else : self._value = 0
        self._affectsLength =  0
        self._affectsAll = False
        self._affects = []
        if 'affects' in data :
            for a in data['affects'].split(','):
                if a.lower() == 'all' : 
                    self._affectsAll = True
                    break
                self._affects.append(int(a))
                self._affectsLength += 1
            
        self._commandClassId = commandClassId
        if 'help' in data : self._help = data['help']
        else : self._help = ""
        if 'items' in data : self._items = data['items']
        else : self._items = []
        if self._type == ValueType.List :
            self._value = int(self._items[int(data['vindex'])]['value'])
        self._isSet = False
        self._checkChange= False
        self._lastPolled = self._value  # index for last polled value from serie
        self._pollDirection = 1  # set direction poll for serie or incrément (-1 or +1)

    _log = property(lambda self: self._node._manager._log)
    homeId = property(lambda self: self._node.homeId) 
    nodeId = property(lambda self: self._node.nodeId)
    commandClassId  = property(lambda self: self._commandClassId)
    instance = property(lambda self: self._instance)
    index = property(lambda self: self._index)
    genre = property(lambda self: self._genre)
    type = property(lambda self: self._type)
    label = property(lambda self: self._label)
    units = property(lambda self: self._units)
    readOnly = property(lambda self: self._readOnly)  #manager.IsValueReadOnly(v)
    
    GetGenre = property(lambda self: ValueGenre().getName(self._genre))
    GetType = property(lambda self: ValueType().getName(self._type))
    
    def GetClassInformation(self):
        return self._node.GetClassIdInformation(self.commandClassId)

    def GetId(self):
#                 // ID Packing:
#                // Bits
#                // 24-31:       8 bits. Node ID of device
#                // 22-23:       2 bits. genre of value (see ValueGenre enum).
#                // 14-21:       8 bits. ID of command class that created and manages this value.
#                // 12-13:       2 bits. Unused.
#                // 04-11:       8 bits. Index of value within all the value created by the command class
#                //                  instance (in configuration parameters, this is also the parameter ID).
#                // 00-03:       4 bits. Type of value (bool, byte, string etc).
#                uint32  m_id;
#
#                // ID1 Packing:
#                // Bits
#                // 24-31        8 bits. Instance Index of the command class.
#                uint32  m_id1;
#
#                // Unique PC interface identifier
#                uint32  m_homeId;
        id = (self.nodeId << 24) | (self._genre << 22) | (self._commandClassId << 14) | (0 << 12) | (self._index << 4) | self._type
        id1 = (self._instance << 24)
        return (id1 << 32) | id

    def getVal(self):
        if self._type == ValueType.Bool :
            if type(self._value) == bool: return self._value
            else: return True if self._value == 'true' else False
        elif self._type in [ValueType.Byte, ValueType.Int, ValueType.Short]:
            return int(self._value)
        elif self._type == ValueType.Decimal :
            return float(self._value)
        elif self._type == ValueType.List :
            for item in self._items :
                if item['value'] == self._value : return item['label']
            return 'Unknown value'
        elif self._type == ValueType.Schedule:              # Complex type used with the Climate Control Schedule command class
            return self._value
        elif self._type == ValueType.String:
            return self._value
        elif self._type == ValueType.Button:               # A write-only value that is the equivalent of pressing a button to send a command to a device
            return self._value
        elif self._type == ValueType.Raw :   
            return self._value
            
    def getValueByte(self):
        if self._type == ValueType.Bool :
            if self._value in [True,  'true']: return 255
            else: return 0
        elif self._type in [ValueType.Byte, ValueType.Int, ValueType.Short]:
            return int(self._value)
        # TODO: Validate format for value below
        elif self._type == ValueType.Decimal :
            return float(self._value)
        elif self._type == ValueType.List :
            for item in self._items :
                if item['value'] == self._value : return int(self._value)
            return 'Unknown value'
        elif self._type == ValueType.Schedule:              # Complex type used with the Climate Control Schedule command class
            return self._value
        elif self._type == ValueType.String:
            return self._value
        elif self._type == ValueType.Button:               # A write-only value that is the equivalent of pressing a button to send a command to a device
            return self._value
        elif self._type == ValueType.Raw :   
            return self._value
    
    def _tohex(self, val, nbits):
        return (val + (1 << nbits)) % (1 << nbits)
        
    def getValueHex(self,  size = 0):
        """Value format in hex tab for parameters of configuration class to send by controller."""
        data = []
        v = None
        print "getValueHex : {0}, type : {1}".format(self._value, ValueType().getName(self.type))
        if self.type in [ValueType.Bool, ValueType.Button]:
            if type(self._value) == bool: 
                data = [255] if self._value else [0]
            else: data = [255] if self._value == 'true' else [0] 
        elif self.type == ValueType.Byte:
            v = self._tohex(int(self._value), 8 if not size else size)
            data = [int(v)]
        elif self.type == ValueType.Short:
            v = self._tohex(int(self._value), 16 if not size else size)
            data = [v >> 8 & 0xff, v & 0xff]
        elif self.type == ValueType.Int:
            v = self._tohex(int(self._value), 32 if not size else size)
            data = [v >> 24 & 0xff, v >> 16 & 0xff, v >> 8 & 0xff, v & 0xff]
        elif self.type == ValueType.List:  # default coding on 16 bit
            v = self._tohex(int(self._value), 16 if not size else size)
            data = [v >> 8 & 0xff, v & 0xff]
        else : 
            print "   = None"
            return None
        if v is not None :
            if size == 8 : data = [int(v)]
            elif size == 16 : data = [v >> 8 & 0xff, v & 0xff]
            elif size == 24 : data = [v >> 16 & 0xff, v >> 8 & 0xff, v & 0xff]
            elif size == 32 : data = [v >> 24 & 0xff, v >> 16 & 0xff, v >> 8 & 0xff, v & 0xff]
        data.insert(0, len(data))
        print "       = {0}".format(GetDataAsHex(data))
        return data
    
    def getValuesCollection(self):
        """Return possible values"""
        if self._type == ValueType.Bool :
            return [True, False]
        elif self._type in [ValueType.Byte, ValueType.Int, ValueType.Short]:
            return {"min": self._min, "max": self._max}
        elif self._type == ValueType.Decimal :
            return {"min": self._min, "max": self._max}
        elif self._type == ValueType.List :
            return self._items
        elif self._type == ValueType.Schedule:              # Complex type used with the Climate Control Schedule command class
            return self._value
        elif self._type == ValueType.String:
            return self._value
        elif self._type == ValueType.Button:               # A write-only value that is the equivalent of pressing a button to send a command to a device
            return self._value
        elif self._type == ValueType.Raw :   
            return self._value

    def getValueToPoll(self, params):
        if params['polltype'] == 'rangeNumber':
            if params['mode'] == 'random': # randomize number
                newValue = random.randrange(params['values']['min']*10, params['values']['max']*10) / 10.0
            elif params['mode'] == 'incremental': # increment and restart from first
                if params['step'] > 0 :
                    if (self._lastPolled + params['step']) < params['values']['max'] : self._lastPolled += params['step']
                    else : self._lastPolled = params['values']['min']
                else :
                    if (self._lastPolled + params['step']) > params['values']['min'] : self._lastPolled += params['step']
                    else : self._lastPolled = params['values']['max']
            elif params['mode'] == 'incrementaltrip':  # increment with return course
                step = abs(params['step'])
                if self._pollDirection == 1:
                    if (self._lastPolled + step) < params['values']['max']: self._lastPolled += step
                    else : 
                        self._lastPolled = params['values']['max'] - step
                        self._pollDirection = -1
                else :
                    if (self._lastPolled - step) > params['values']['min'] : self._lastPolled -= step
                    else : 
                        self._lastPolled = params['values']['min'] + step
                        self._pollDirection = 1
            newValue = self._lastPolled
            if self._type == 'Bool':
                newValue = True if int(newValue) != 0 else False
            if self._type in ['Byte', 'Int', 'List', 'Short', 'Raw'] :
                newValue = int(newValue)
        elif params['polltype'] == 'serie':
            if len(params['values']) <= 1 :
                if params['values'] : 
                    self._lastPolled = 0
                    newValue = params['values'][self._lastPolled]
                else : 
                    self._log.write(LogLevel.Error, self, "Poll parameters don't have value in serie, can't calculate value. Params : {0}".format(params))
                    return self._value
            else :
                if params['mode'] == 'random':   # randomize index
                    id = random.randrange(0,  len(params['values'])-1)
                    newValue = params['values'][id]
                elif params['mode'] == 'round': # course value and restart from first
                    if self._lastPolled < len(params['values'])-1  : self._lastPolled += 1
                    else : self._lastPolled = 0
                    newValue = params['values'][self._lastPolled]
                elif params['mode'] == 'roundtrip': # course value with return course
                    if self._pollDirection == 1: 
                        if self._lastPolled < len(params['values'])-1 : self._lastPolled += 1
                        else : 
                            self._lastPolled = len(params['values'])-2
                            self._pollDirection = -1
                    else :
                        if self._lastPolled > 0 : self._lastPolled -= 1
                        else : 
                            self._lastPolled = 1
                            self._pollDirection = 1
                    newValue = params['values'][self._lastPolled]
        self._log.write(LogLevel.Info, self, "Value object, new value for poll : {0}".format(newValue))
        return newValue

    def setVal(self, val):
        typeVal = type(val)
        if self._type == ValueType.Bool :
            if typeVal == bool: self._value = val
            elif typeVal == int : self._value = True if self._value != 0 else False
            else: self._value = True if self._value == 'true' else False
        elif self._type in [ValueType.Byte, ValueType.Int, ValueType.Short]:
            self._value = int(val)
        elif self._type == ValueType.Decimal :
            self._value = float(val)
        elif self._type == ValueType.List :
            if typeVal == int:
                for item in self._items :
                    if item['value'] == val : 
                        self._value = item['value']
                        break
            elif typeVal == str:
                for item in self._items :
                    if item['label'] == val : 
                        self._value = item['value']
                        break
            elif typeVal == dict:
                for item in self._items :
                    if item['label'] == val['label'] or item['value'] == val['value']: 
                        self._value = item['value']
                        break
            else : self._log.write(LogLevel.Error, self, "set a ValueType.List invalid type {0} for value {1}.".format(type(val), val))
        elif self._type == ValueType.Schedule:              # Complex type used with the Climate Control Schedule command class
            self._value = val
        elif self._type == ValueType.String:
            self._value = val
        elif self._type == ValueType.Button:               # A write-only value that is the equivalent of pressing a button to send a command to a device
            self._value = val
        elif self._type == ValueType.Raw :   
            self._value =val

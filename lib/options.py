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

#from manager import MANAGER

from zwemulator.lib.log import Log, LogLevel, LOG
from zwemulator.lib.defs import *
from xml.dom import minidom
import json
import os

OPTIONS = None

class Options(object):
    
    instance = None
    AreLocked = property(lambda self: self._lock)
    get =  property(lambda self: self)
    initialized = False
    
    def __new__(cls, *args, **kargs):
        if  Options.instance is None:
            Options.instance = object.__new__(cls, *args, **kargs)
            Options.initialized = False
        else :
            Options.initialized = True
        return Options.instance
    
    def __init__(self):
        global OPTIONS
#        if OPTIONS is None :
        if not self.initialized:
            self._configPath = None
            self._userPath = None
            self._command = None
            self._log = None
            self._xml = "options.xml"
            self._options = {}
            self._lock = False
            OPTIONS = self
    
    def __del__(self):
        global OPTIONS
        if MANAGER is not None :
            print "Can't del Options, Manager exist"
            raise Exception()
        self.instance = None
        self.initialized = False
        OPTIONS = None 
    
    def Lock(self): # return boolean
        if not self._lock :
            self.ParseOptionsXML(self._configPath +"/" + self._xml)
            if os.path.isfile(self._userPath +"/" + self._xml):
                self.ParseOptionsXML(self._userPath +"/" + self._xml)
            self.ParseOptionsString(self._command)
            self._lock = True
            print "Options are locked."
            return True
        else : 
            print "Options allready locked."
            return False

    def setLog(self,  log):
        self._log = log

    def create(self,  configPath, userPath,  command):
        self._configPath = configPath
        self._userPath = userPath
        self._command = command
        if not os.path.exists(self._configPath):
            _log = Log()
            _log.create("",  False,  True, LogLevel.Debug , LogLevel.Debug, LogLevel.Debug)
            _log.write(LogLevel.Error,  "Cannot Find a path to the configuration files at {0}. Exiting...".format(self._configPath))
            exit(1)
        # Add the default options
        self.AddOptionString("ConfigPath", configPath, False)	# Path to the OpenZWave config folder.
        self.AddOptionString("UserPath",userPath, False)	# Path to the user's data folder.

        self.AddOptionBool("Logging",True)						# Enable logging of library activity.
        self.AddOptionString("LogFileName","OZWEmul_Log.txt",False)	# Name of the log file (can be changed via Log::SetLogFileName)
        self.AddOptionBool("AppendLogFile",False)					# Append new session logs to existing log file (False = overwrite)
        self.AddOptionBool("ConsoleOutput",True)						# Display log information on console (as well as save to disk)
        self.AddOptionInt("SaveLogLevel", LogLevel.Detail)			# Save (to file) log messages equal to or above Detail
        self.AddOptionInt("QueueLogLevel", LogLevel.Debug)			# Save (in RAM) log messages equal to or above Debug
        self.AddOptionInt("DumpTriggerLevel", LogLevel.Never)			# Default is to never dump RAM-stored log messages

        self.AddOptionBool("Associate",True)						# Enable automatic association of the controller with group one of every device.
        self.AddOptionString("Exclude","",	True)		# Remove support for the listed command classes.
        self.AddOptionString("Include","",True)		# Only handle the specified command classes.  The Exclude option is ignored if anything is listed here.
        self.AddOptionBool("NotifyTransactions",False)					# Notifications when transaction complete is reported.
        self.AddOptionString("Interface","",True)		# Identify the serial port to be accessed (TODO: change the code so more than one serial port can be specified and HID)
        self.AddOptionBool("SaveConfiguration",True)						# Save the XML configuration upon driver close.
        self.AddOptionInt("DriverMaxAttempts",0)

        self.AddOptionInt("PollInterval",30000)						# 30 seconds (can easily poll 30 values in this time; ~120 values is the effective limit for 30 seconds)
        self.AddOptionBool("IntervalBetweenPolls",False)					# if False, try to execute the entire poll list within the PollInterval time frame
                                                                                          # if True, wait for PollInterval milliseconds between polls
        self.AddOptionBool("SuppressValueRefresh",False)					# if True, notifications for refreshed (but unchanged) values will not be sent
        self.AddOptionBool("PerformReturnRoutes",True)					# if true, return routes will be updated
        
        self.AddOptionString("NetworkKey", "", False)
        self.AddOptionBool("RefreshAllUserCodes", False)             # if true, during startup, we refresh all the UserCodes the device reports it supports. If False, we stop after we get the first "Available" slot (Some devices have 250+ usercode slots! - That makes our Session Stage Very Long )
        self.AddOptionInt("RetryTimeout", RETRY_TIMEOUT)       # How long do we wait to timeout messages sent
        self.AddOptionBool("EnableSIS", True)                        # Automatically become a SUC if there is no SUC on the network.
        self.AddOptionBool("AssumeAwake", True)                      # Assume Devices that Support the Wakeup CC are awake when we first query them....
        self.AddOptionBool("NotifyOnDriverUnload", False)       # Should we send the Node/Value Notifications on Driver Unloading - Read comments in Driver::~Driver() method about possible race conditions
        
    def AddOptionBool(self, name, default ): # return boolean
        if not self._lock :
            self._options[name.lower()] = {'type' : 'bool', 'value': default}
            return True
        else: 
            return False
        
    def AddOptionInt(self, name, default ): # return boolean
        if not self._lock :
            self._options[name.lower()] = {'type' : 'int', 'value': default}
            return True
        else: 
            return False
        
    def AddOptionString(self, name, default, append ): # return boolean
        if not self._lock :
            self._options[name.lower()] = {'type' : 'str', 'value': default, 'append': append}
            return True
        else: 
            return False

    def setOptionValue(self, name,  value):
        val = None
        if name in self._options :
            if self._options[name]['type'] == 'bool' :
                if value == "true" or value == "1":
                    val = True
                elif value == "false" or value == "0":
                    val = False
            elif self._options[name]['type'] == 'int' :
                try :
                    val == int(value)
                except :
                    if LOG : LOG.write(LogLevel.Warning,  "Option '{0}' not valid int type : {1}".format(name, value))
                    else :
                        print "Option '{0}' not valid int type : {1}".format(name, value)
            elif self._options[name]['type'] == 'str' :
                val = str(value)
            else :
                if LOG : LOG.write(LogLevel.Warning,  "Option '{0}' not valid type : {1}".format(name, value))
                else :
                    print "Option '{0}' not valid type : {1}".format(name, value)
            if val : self._options[name]['value'] = value
        else :
            if LOG : LOG.write(LogLevel.Warning,  "Option '{0}' not valid : {1}".format(name, value))
            else :
                print "Option '{0}' not valid : {1}".format(name, value)
    
    def GetOptionAsBool(self, name):
        name = name.lower()
        if name in self._options :
            if self._options[name]['type'] == 'bool' :
                return True, self._options[name]['value'] 
        else :
            if self._log: self._log.write(LogLevel.Warning, "Specified option {0} was not found.".format(name))
            return False, None
        
    def GetOptionAsInt(self, name):
        name = name.lower()
        if name in self._options :
            if self._options[name]['type'] == 'int' :
                return True, self._options[name]['value'] 
        else :
            if self._log: self._log.write(LogLevel.Warning, "Specified option {0} was not found.".format(name))
            return False, None
            
    def GetOptionAsString(self, name):
        name = name.lower()
        if name in self._options :
            if self._options[name]['type'] == 'str' :
                return True, self._options[name]['value'] 
        else :
            if self._log: self._log.write(LogLevel.Warning, "Specified option {0} was not found.".format(name))
            return False, None
        
    def ParseOptionsXML(self, xml_file):
        self._xml_content = minidom.parse(xml_file)
        for c in self._xml_content.getElementsByTagName("Options") :
            for o in self._xml_content.getElementsByTagName("Option") :
                name = o.attributes.get("name").value.strip().lower()
                if name in self._options :
                    value =  o.attributes.get("value").value.strip().lower()
                    self.setOptionValue(name,  value)
                    
    def ParseOptionsString(self,  commandLine):
        opts = commandLine.split("--")
        for opt in opts :
            if opt : 
                n= opt.split(" ")
                self.setOptionValue(n[0].lower(),  n[1])

#cdef extern from "Options.h" namespace "OpenZWave::Options":
#    Options* Create(string a, string b, string c)

if __name__ == "__main__":
    Log().create("test.log",  False,  True, LogLevel.Debug , LogLevel.Debug, LogLevel.Debug)
    o= Options()
    print o
    o.create("../openzwave/config", "", "--logging true --LogFileName toto.txt")
    print o.AddOptionBool('NotifyTransactions',  True)
    o.Lock()
    print Options()
    print Options().get

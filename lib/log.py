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
import logging
from logging.handlers import RotatingFileHandler
import os
import sys
#from manager import Manager
#from lib.driver import Driver
#from node import Node
#from lib.values import Value

LOG = None

class LogLevel:
    Never          = 0    # Disable all logging
    Always        = 1    # These messages should always be shown
    Fatal         = 2    # A likely fatal issue in the library
    Error         = 3    # A serious issue with the library or the network
    Warning       = 4    # A minor issue from which the library should be able to recover
    Alert         = 5    # Something unexpected by the library about which the controlling application should be aware
    Info          = 6    # Everything's working fine...these messages provide streamlined feedback on each message
    Detail        = 7    # Detailed information on the progress of each message
    Debug         = 8    # Very detailed information on progress that will create a huge log file quickly
                                  # But this level (as others) can be queued and sent to the log only on an error or warning
    StreamDetail  = 9    # Will include low-level byte transfers from controller to buffer to application and back
    Internal      = 10    # Used only within the log class (uses existing timestamp, etc.)

class Log(object):
    """As singleton"""
    
    instance = None
    initialized = False
    
    def __new__(cls, *args, **kargs):
        if  Log.instance is None:
            Log.instance = object.__new__(cls, *args, **kargs)
            cls._log = None
            Log.initialized = False
        else:
            Log.initialized = True
        return Log.instance
    
    def __init__(self):
        global LOG
        if not self.initialized :
            LOG = self
        
    def create(self,  fileName, bAppend, bConsoleOutput, nSaveLogLevel, nQueueLogLevel, nDumpTrigger):
        """Actually Set only loglevel.DEBUG  """
        if self._log is None :
            self._doLogging = True
            logLevel = logging.DEBUG
            self._log = logging.getLogger()
            self._log.setLevel(logLevel)
            logfmt = logging.Formatter("[%(asctime)s] %(levelname)s %(message)s")
            if fileName:
                if not bAppend :
                    try : 
                        os.remove(fileName)
                    except :
                        pass
                fileHandler = RotatingFileHandler(fileName, maxBytes=10485760, backupCount=5)
                fileHandler.setLevel(logLevel)
                fileHandler.setFormatter(logfmt)
                self._log.addHandler(fileHandler)
            if bConsoleOutput :
                # création d'un second handler qui va rediriger chaque écriture de log sur la console
                stream_handler = logging.StreamHandler(sys.stdout)
                stream_handler.setLevel(logLevel)
                stream_handler.setFormatter(logfmt)
                self._log.addHandler(stream_handler)
            self.write(LogLevel.Always, "Openzwave-emulator log started with level {0} on file : {1}".format(logLevel , fileName))
    
    def setLoggingState(self,  doLogging):
        self._doLogging = doLogging
        
    def write(self,  level,  *args):
        
        if self._log is not None and self._doLogging :
            msg =""
            for a in args :
#                print type(a),  a.__class__.__name__
                if a.__class__.__name__ == "Manager" : a = 'mgr'
                elif a.__class__.__name__ == "Driver" : a = 'ctrl' 
                elif a.__class__.__name__ == "Node" : a = 'Node%0.3d'%a.nodeId
                elif a.__class__.__name__ == "Value" : a = 'Node%0.3d'%a.nodeId
                else :
                    try :
                        if str(a.__class__).find('command_classes') != -1 : 
                            a = 'Node%0.3d, %s'%(a.nodeId, a.GetCommandClassName)
                    except: pass
                msg += ", {0}".format(a)
            if level in [LogLevel.Always, LogLevel.Info, LogLevel.Detail] :
                self._log.info(msg)
            elif level == LogLevel.Error:
                self._log.error(msg)
            elif level in [LogLevel.Warning, LogLevel.Alert] :
                self._log.warning(msg)
            elif level == LogLevel.Fatal :
                self._log.critical(msg)
            else :
                self._log.debug(msg)
            
if __name__ == "__main__":
    from manager import Manager
    from lib.driver import Driver
    from node import Node
    from lib.values import Value
    from options import Options
    
    l = Log()
    print l
    l.create("",  False,  True, LogLevel.Debug , LogLevel.Debug, LogLevel.Debug)
    l2 = Log()
    print l,  l2
    l.write(LogLevel.Debug,  "Test de log debug")
    o = Options()
    o.create("../openzwave/config", "", "--logging true --LogFileName toto.txt")
    o.Lock()
    m = Manager()
    l2.write(LogLevel.Debug,  Node(m,  12554, 5), "Test de log debug avec", " l2")
    LOG.write(LogLevel.Info,  Value(Node(m,  12554, 8), 55),"Refresh Value Test de log info avec LOG")
    LOG.write(LogLevel.Warning,  m ,"Test de log warning avec LOG")
    LOG.write(LogLevel.Warning,  Driver(m, "/dev/zwave", "") ,"Test de log warning avec LOG")

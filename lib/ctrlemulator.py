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

import serial
import time
import threading
from lib.defs import *
from lib.log import LogLevel


PORT = "/tmp/ttyS1"

class OZWSerialEmul:

    def __init__(self, port, baud = 19200, timeout = 0,  stop = None, callback = None, setWaitingForAck = None, log =None, cbTimeOut = 0):
        self._stop = stop
        self._callback = callback
        self._setWaitingForAck = setWaitingForAck
        self._log = log
        self._cbTimeOut = cbTimeOut
        self._lockWrite = threading.Lock()  # use to lock write data on serial when waiting for an ACK
        self._log.write(LogLevel.Info, "  Opening emulate controller {0}".format(port))
        self._serial = serial.Serial(port, baud, timeout = timeout, rtscts=True, dsrdtr=True)
        self._readMsg = threading.Thread(None, self.waitData, "th_Handle_Read_Msg", (), {})
        self._readMsg.start()

    def close(self):
        self._log.write(LogLevel.Info, "Closing emulate controller {0}".format(self._serial.name))
        try :
            self._lockWrite.release()
        except:
            pass
        self._serial.close()

    def formatHex(self,  data):
        if data : return ''.join("0x%.2x, "%d for d in data[0:-1]) + "0x%.2x"%data[-1]
        return ''

    def read(self):
        try :
            data = self._serial.read(256)
            if data :
                buff = []
                for d in data: buff.append(ord(d))
                print "Receive {0} Octets [{1}]".format(len(data),  self.formatHex(buff))
                return buff
        except  serial.SerialException, e:
            print "Read error :" , e
        return None

    def writeHex(self, data):
        s = ''
        for c in data :
            s += chr(c)
        if data[0] == SOF :
            self._lockWrite.acquire()
            self._setWaitingForAck(True)
        num = self._serial.write(s)
        print "*** writed :{0} Octets --> [{1}]".format(num, self.formatHex(data))
        try :
            if data[0] == SOF : self._lockWrite.release()
        except:
            pass

    def waitData(self):
        cbTimeOut = time.time();
        while not self._stop.isSet():
            data = self.read()
            if data is not None :
                cbTimeOut = time.time();
                print 'Pass to driver : {0}'.format(self.formatHex(data))
                if data[0] == ACK:                                                       # ACK : 0x06
                    print '*** ACK received ****'
                    data.pop(0)
                    self._setWaitingForAck(False)
                    if self._callback is not None: self._callback([ACK])
                elif data[0] == NAK:                                                   # NAK : 0x15
                    print '*** NAK Receive ****'
                    data.pop(0)
                    self._setWaitingForAck(False)
                    if self._callback is not None: self._callback([NAK])
                elif data[0] == CAN:                                                   # CAN : 0x18
                    print '*** CAN Receive ****'
                    data.pop(0)
                    self._setWaitingForAck(False)
                    if self._callback is not None: self._callback([CAN])
                if data and data[0] == SOF:                                       # SOF : 0x01
                    self._lockWrite.acquire()
                    if self._callback is not None: self._callback(data)
                    self._lockWrite.release()
            else:
                if self._cbTimeOut and time.time() >= cbTimeOut + self._cbTimeOut:
                    cbTimeOut = time.time();
                    if self._callback is not None: self._callback([])
                time.sleep(0.01)
        self.close()
        print "Terminate, serial open ? : ",  self._serial.isOpen()


if __name__ == "__main__":
    import logging

    class Log():

        def __init__(self):
            self.log = logging.getLogger()
            self.log.setLevel(logging.DEBUG)
            logfmt = logging.Formatter("[%(asctime)s] %(levelname)s %(message)s")
            # création d'un second handler qui va rediriger chaque écriture de log sur la console
            steam_handler = logging.StreamHandler()
            steam_handler.setLevel(logging.DEBUG)
            steam_handler.setFormatter(logfmt)
            self.log.addHandler(steam_handler)
            self.write(LogLevel.Always, "Openzwave-emulator log started with level {0}".format(logging.DEBUG))

        def write(self, level,  *args):
            msg =""
            for a in args :
    #                print type(a),  a.__class__.__name__
                if a.__class__.__name__ == "Manager" : a = 'mgr'
                elif a.__class__.__name__ == "Driver" : a = 'ctrl'
                elif a.__class__.__name__ == "Node" : a = 'Node%0.3d'%a.nodeId
                elif a.__class__.__name__ == "Value" : a = 'Node%0.3d'%a.nodeId
                msg += ", {0}".format(a)
            if level in [LogLevel.Always, LogLevel.Info, LogLevel.Detail] :
                self.log.info(msg)
            elif level == LogLevel.Error:
                self.log.error(msg)
            elif level in [LogLevel.Warning, LogLevel.Alert] :
                self.log.warning(msg)
            elif level == LogLevel.Fatal :
                self.log.critical(msg)
            else :
                self.log.debug(msg)

    def ProcessMsg(data):
        if data == [0x01, 0x03, 0x00, 0x15, 0xe9]:                      # FUNC_ID_ZW_GET_VERSION
            ser.writeHex([0x06])
            ser.writeHex([0x01, 0x10, 0x01, 0x15, 0x5a, 0x2d, 0x57, 0x61, 0x76, 0x65, 0x20, 0x32, 0x2e, 0x37, 0x38, 0x00, 0x01, 0x9b])
        elif data == [0x01, 0x03, 0x00, 0x20, 0xdc]:                    # FUNC_ID_ZW_MEMORY_GET_ID
            ser.writeHex([0x06])
            ser.writeHex([0x01, 0x08, 0x01, 0x20, 0x01, 0x4d, 0x0f, 0x18, 0x01, 0x8c])
        elif data == [0x01, 0x03, 0x00, 0x05, 0xf9]:                    # FUNC_ID_ZW_GET_CONTROLLER_CAPABILITIES
            ser.writeHex([0x06])
            ser.writeHex([0x01, 0x04, 0x01, 0x05, 0x1c, 0xe3])
        elif data == [0x01, 0x03, 0x00, 0x07, 0xfb]:                    # FUNC_ID_SERIAL_API_GET_CAPABILITIES
            ser.writeHex([0x06])
            ser.writeHex([0x01, 0x2b, 0x01, 0x07, 0x03, 0x07, 0x00, 0x86, 0x00, 0x02, 0x00, 0x01, 0xfe, 0x80, 0xfe, 0x88, 0x0f, 0x00, 0x00, 0x00, 0xfb, 0x97, 0x7f, 0x82, 0x07, 0x00, 0x00, 0x80, 0x00, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xc2])
        elif data == [0x01, 0x03, 0x00, 0x56, 0xaa]:                    # FUNC_ID_ZW_GET_SUC_NODE_ID
            ser.writeHex([0x06])
            ser.writeHex([0x01, 0x04, 0x01, 0x56, 0x01, 0xad])
        elif data == [0x01, 0x04, 0x00, 0x1c, 0x20, 0xc7]:          # FUNC_ID_ZW_GET_RANDOM
            ser.writeHex([0x06])
            ser.writeHex([0x01, 0x25, 0x01, 0x1c, 0x01, 0x20, 0x05, 0x94, 0x65, 0xf7, 0xa4, 0x34, 0x6d, 0x73, 0xc1, 0x3a, 0x59, 0x30, 0x23, 0xf6, 0x2d, 0x1a, 0x97, 0xce, 0xaf, 0x51, 0xb0, 0xe5, 0x9d, 0xf6, 0x9c, 0x4d, 0x39, 0x72, 0x0c, 0xb9, 0x8c, 0xe0, 0xc1])
        elif data == [0x01, 0x03, 0x00, 0x02, 0xfe]:                    # FUNC_ID_SERIAL_API_GET_INIT_DATA
            ser.writeHex([0x06])
            ser.writeHex([0x01, 0x25, 0x01, 0x02, 0x05, 0x08, 0x1d, 0xe9, 0x3f, 0x0e, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x03, 0x01, 0x13])
        # DRIVER IS READY
        elif data == [0x01, 0x05, 0x00, 0x06, 0x64, 0x0f, 0x97]:    # FUNC_ID_SERIAL_API_SET_TIMEOUTS
            ser.writeHex([0x06])
            ser.writeHex([0x01, 0x05, 0x01, 0x06, 0x64, 0x0f, 0x96])

    stop = threading.Event()
    log = Log()
    ser = OZWSerialEmul(PORT, stop = stop, callback = ProcessMsg,  log = log)

    try :
        while True :
            time.sleep(0.1)
    except (KeyboardInterrupt, SystemExit):
        pass
    stop.set()
    print "End Main"

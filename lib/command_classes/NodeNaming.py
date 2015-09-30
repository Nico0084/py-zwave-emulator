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

class NodeNamingCmd(EnumNamed):
	Set				= 0x01
	Get				= 0x02
	Report			= 0x03
	LocationSet		= 0x04
	LocationGet		= 0x05
	LocationReport	= 0x06

class StringEncoding(EnumNamed):
	StringEncoding_ASCII = 0
	StringEncoding_ExtendedASCII = 1
	StringEncoding_UTF16 = 2

# Mapping of characters 0x80 and above to Unicode.
c_extendedAsciiToUnicode = [
    0x20ac,	    # 0x80 - Euro Sign
    0x0081,		# 0x81 -
    0x201a,	    # 0x82 - Single Low-9 Quotation Mark
    0x0192,	    # 0x83 - Latin Small Letter F With Hook
    0x201e,	    # 0x84 - Double Low-9 Quotation Mark
    0x2026,	    # 0x85 - Horizontal Ellipsis
    0x2020,	    # 0x86 - Dagger
    0x2021,	    # 0x87 - Double Dagger
    0x02c6,	    # 0x88 - Modifier Letter Circumflex Accent
    0x2030,	    # 0x89 - Per Mille Sign
    0x0160,	    # 0x8a - Latin Capital Letter S With Caron
    0x2039,	    # 0x8b - Single Left-Pointing Angle Quotation Mark
    0x0152,	    # 0x8c - Latin Capital Ligature Oe
    0x008d,		# 0x8d -
    0x017d,	    # 0x8e - Latin Capital Letter Z With Caron
    0x008f,		# 0x8f -
    
    0x0090,		# 0x90 -
    0x2018,	    # 0x91 - Left Single Quotation Mark
    0x2019,	    # 0x92 - Right Single Quotation Mark
    0x201c,	    # 0x93 - Left Double Quotation Mark
    0x201d,	    # 0x94 - Right Double Quotation Mark
    0x2022,	    # 0x95 - Bullet
    0x2013,	    # 0x96 - En Dash
    0x2014,	    # 0x97 - Em Dash
    0x02dc,	    # 0x98 - Small Tilde
    0x2122,	    # 0x99 - Trade Mark Sign
    0x0161,	    # 0x9a - Latin Small Letter S With Caron
    0x203a,	    # 0x9b - Single Right-Pointing Angle Quotation Mark
    0x0153,	    # 0x9c - Latin Small Ligature Oe
    0x009d,		# 0x9d -
    0x017e,	    # 0x9e - Latin Small Letter Z With Caron
    0x0178,	    # 0x9f - Latin Capital Letter Y With Diaeresis
    
    0x00a0,	    # 0xa0 - No-Break Space
    0x00a1,	    # 0xa1 - Inverted Exclamation Mark
    0x00a2,	    # 0xa2 - Cent Sign
    0x00a3,	    # 0xa3 - Pound Sign
    0x00a4,	    # 0xa4 - Currency Sign
    0x00a5,	    # 0xa5 - Yen Sign
    0x00a6,	    # 0xa6 - Broken Bar
    0x00a7,	    # 0xa7 - Section Sign
    0x00a8,	    # 0xa8 - Diaeresis
    0x00a9,	    # 0xa9 - Copyright Sign
    0x00aa,	    # 0xaa - Feminine Ordinal Indicator
    0x00ab,	    # 0xab - Left-Pointing Double Angle Quotation Mark
    0x00ac,	    # 0xac - Not Sign
    0x00ad,	    # 0xad - Soft Hyphen
    0x00ae,	    # 0xae - Registered Sign
    0x00af,	    # 0xaf - Macron
    
    0x00b0,	    # 0xb0 - Degree Sign
    0x00b1,	    # 0xb1 - Plus-Minus Sign
    0x00b2,	    # 0xb2 - Superscript Two
    0x00b3,	    # 0xb3 - Superscript Three
    0x00b4,	    # 0xb4 - Acute Accent
    0x00b5,	    # 0xb5 - Micro Sign
    0x00b6,	    # 0xb6 - Pilcrow Sign
    0x00b7,	    # 0xb7 - Middle Dot
    0x00b8,	    # 0xb8 - Cedilla
    0x00b9,	    # 0xb9 - Superscript One
    0x00ba,	    # 0xba - Masculine Ordinal Indicator
    0x00bb,	    # 0xbb - Right-Pointing Double Angle Quotation Mark
    0x00bc,	    # 0xbc - Vulgar Fraction One Quarter
    0x00bd,	    # 0xbd - Vulgar Fraction One Half
    0x00be,	    # 0xbe - Vulgar Fraction Three Quarters
    0x00bf,	    # 0xbf - Inverted Question Mark
    
    0x00c0,	    # 0xc0 - Latin Capital Letter A With Grave
    0x00c1,	    # 0xc1 - Latin Capital Letter A With Acute
    0x00c2,	    # 0xc2 - Latin Capital Letter A With Circumflex
    0x00c3,	    # 0xc3 - Latin Capital Letter A With Tilde
    0x00c4,	    # 0xc4 - Latin Capital Letter A With Diaeresis
    0x00c5,	    # 0xc5 - Latin Capital Letter A With Ring Above
    0x00c6,	    # 0xc6 - Latin Capital Ligature Ae
    0x00c7,	    # 0xc7 - Latin Capital Letter C With Cedilla
    0x00c8,	    # 0xc8 - Latin Capital Letter E With Grave
    0x00c9,	    # 0xc9 - Latin Capital Letter E With Acute
    0x00ca,	    # 0xca - Latin Capital Letter E With Circumflex
    0x00cb,	    # 0xcb - Latin Capital Letter E With Diaeresis
    0x00cc,	    # 0xcc - Latin Capital Letter I With Grave
    0x00cd,	    # 0xcd - Latin Capital Letter I With Acute
    0x00ce,	    # 0xce - Latin Capital Letter I With Circumflex
    0x00cf,	    # 0xcf - Latin Capital Letter I With Diaeresis
    
    0x00d0,	    # 0xd0 - Latin Capital Letter Eth
    0x00d1,	    # 0xd1 - Latin Capital Letter N With Tilde
    0x00d2,	    # 0xd2 - Latin Capital Letter O With Grave
    0x00d3,	    # 0xd3 - Latin Capital Letter O With Acute
    0x00d4,	    # 0xd4 - Latin Capital Letter O With Circumflex
    0x00d5,	    # 0xd5 - Latin Capital Letter O With Tilde
    0x00d6,	    # 0xd6 - Latin Capital Letter O With Diaeresis
    0x00d7,	    # 0xd7 - Multiplication Sign
    0x00d8,	    # 0xd8 - Latin Capital Letter O With Stroke
    0x00d9,	    # 0xd9 - Latin Capital Letter U With Grave
    0x00da,	    # 0xda - Latin Capital Letter U With Acute
    0x00db,	    # 0xdb - Latin Capital Letter U With Circumflex
    0x00dc,	    # 0xdc - Latin Capital Letter U With Diaeresis
    0x00dd,	    # 0xdd - Latin Capital Letter Y With Acute
    0x00de,	    # 0xde - Latin Capital Letter Thorn
    0x00df,	    # 0xdf - Latin Small Letter Sharp S
    
    0x00e0,	    # 0xe0 - Latin Small Letter A With Grave
    0x00e1,	    # 0xe1 - Latin Small Letter A With Acute
    0x00e2,	    # 0xe2 - Latin Small Letter A With Circumflex
    0x00e3,	    # 0xe3 - Latin Small Letter A With Tilde
    0x00e4,	    # 0xe4 - Latin Small Letter A With Diaeresis
    0x00e5,	    # 0xe5 - Latin Small Letter A With Ring Above
    0x00e6,	    # 0xe6 - Latin Small Ligature Ae
    0x00e7,	    # 0xe7 - Latin Small Letter C With Cedilla
    0x00e8,	    # 0xe8 - Latin Small Letter E With Grave
    0x00e9,	    # 0xe9 - Latin Small Letter E With Acute
    0x00ea,	    # 0xea - Latin Small Letter E With Circumflex
    0x00eb,	    # 0xeb - Latin Small Letter E With Diaeresis
    0x00ec,	    # 0xec - Latin Small Letter I With Grave
    0x00ed,	    # 0xed - Latin Small Letter I With Acute
    0x00ee,	    # 0xee - Latin Small Letter I With Circumflex
    0x00ef,	    # 0xef - Latin Small Letter I With Diaeresis
    
    0x00f0,	    # 0xf0 - Latin Small Letter Eth
    0x00f1,	    # 0xf1 - Latin Small Letter N With Tilde
    0x00f2,	    # 0xf2 - Latin Small Letter O With Grave
    0x00f3,	    # 0xf3 - Latin Small Letter O With Acute
    0x00f4,	    # 0xf4 - Latin Small Letter O With Circumflex
    0x00f5,	    # 0xf5 - Latin Small Letter O With Tilde
    0x00f6,	    # 0xf6 - Latin Small Letter O With Diaeresis
    0x00f7,	    # 0xf7 - Division Sign
    0x00f8,	    # 0xf8 - Latin Small Letter O With Stroke
    0x00f9,	    # 0xf9 - Latin Small Letter U With Grave
    0x00fa,	    # 0xfa - Latin Small Letter U With Acute
    0x00fb,	    # 0xfb - Latin Small Letter U With Circumflex
    0x00fc,	    # 0xfc - Latin Small Letter U With Diaeresis
    0x00fd,	    # 0xfd - Latin Small Letter Y With Acute
    0x00fe,	    # 0xfe - Latin Small Letter Thorn
    0x00ff	    # 0xff - Latin Small Letter Y With Diaeresis
    ]

class NodeNaming(CommandClass):
    
    StaticGetCommandClassId = 0x77
    StaticGetCommandClassName = "COMMAND_CLASS_NODE_NAMING"
    
    def __init__(self, node,  data):
        CommandClass.__init__(self, node, data)
    
    GetCommandClassId = property(lambda self: self.StaticGetCommandClassId)
    GetCommandClassName = property(lambda self: self.StaticGetCommandClassName)

    def getFullNameCmd(self,  _id):
        return NodeNamingCmd().getFullName(_id)

    def ProcessMsg(self, _data, instance=1, multiInstanceData = []):
        if _data[0] == NodeNamingCmd.Get:
            msg = Msg("NodeNamingCmd_Report", self.nodeId,  REQUEST, FUNC_ID_APPLICATION_COMMAND_HANDLER)
            value = self._node.getValue(self.GetCommandClassId, instance, 0) # Name index is allways 0
            if value is not None : name = value._value
            else : name = self._node.name
            if name is not None :
                msg.Append(TRANSMIT_COMPLETE_OK)
                msg.Append(self.nodeId)
                dStr = self.encodeString(name) # for moment only StringEncoding_ASCII
                msg.Append(2 + len(dStr))
                msg.Append(self.GetCommandClassId)
                msg.Append(NodeNamingCmd.Report)
                for d in dStr : msg.Append(d)
                self.GetDriver.SendMsg(msg, MsgQueue.NoOp)    
            else :
                msg.Append(TRANSMIT_COMPLETE_NOROUTE)
                msg.Append(self.nodeId)
                self.GetDriver.SendMsg(msg, MsgQueue.NoOp)    
        elif _data[0] == NodeNamingCmd.Set:
            value = self._node.getValue(self.GetCommandClassId, instance, 0) # Name index is allways 0
            name = self.extractString(_data, len(_data))
            if name :
                if value is not None: value.setVal(name)
                self._node.name = name
                self._log.write(LogLevel.Detail, self, "{0} cmd received: {1}".format(self.getFullNameCmd(_data[0]), name))
                #TODO: Verify is response is necessary ?
#                self.HandleReportChange("NodeNamingCmd_Report", self, [NodeNamingCmd.Get], instance)
            else :
                self._log.write(LogLevel.Warning, self, "{0}, no name extract from data : {1}".format(self.getFullNameCmd(_data[0]), GetDataAsHex(_data)))
        elif _data[0] == NodeNamingCmd.LocationGet:
            msg = Msg("NodeNamingCmd_LocationReport", self.nodeId,  REQUEST, FUNC_ID_APPLICATION_COMMAND_HANDLER)
            value = self._node.getValue(self.GetCommandClassId, instance, 1) # TODO : Check this : Location index presumed allways 1
            if value is not None : location = value._value
            else : location = self._node.location
            if location is not None :
                msg.Append(TRANSMIT_COMPLETE_OK)
                msg.Append(self.nodeId)
                dStr = self.encodeString(location) # for momment only StringEncoding_ASCII
                msg.Append(2 + len(dStr))
                msg.Append(self.GetCommandClassId)
                msg.Append(NodeNamingCmd.LocationReport)
                for d in dStr : msg.Append(d)
                self.GetDriver.SendMsg(msg, MsgQueue.NoOp)    
            else :
                msg.Append(TRANSMIT_COMPLETE_NOROUTE)
                msg.Append(self.nodeId)
                self.GetDriver.SendMsg(msg, MsgQueue.NoOp)    
        elif _data[0] == NodeNamingCmd.LocationSet:
            value = self._node.getValue(self.GetCommandClassId, instance, 1) # TODO : Check this : Location index presumed allways 1
            location = self.extractString(_data, len(_data))
            if location :
                if value is not None: value.setVal(location)
                self._node.location = location
                self._log.write(LogLevel.Detail, self, "{0} cmd received: {1}".format(self.getFullNameCmd(_data[0]), location))
                #TODO: Verify is response is necessary ?
#                self.HandleReportChange("NodeNamingCmd_LocationReport", self, [NodeNamingCmd.LocationGet], instance)
            else :
                self._log.write(LogLevel.Warning, self, "{0}, no location extract from data : {1}".format(self.getFullNameCmd(_data[0]), GetDataAsHex(_data)))

        else:
            self._log.write(LogLevel.Warning, self, "CommandClass REQUEST {0}, Not implemented : {1}".format(self.getFullNameCmd(_data[0]), GetDataAsHex(_data)))

    def encodeString(self, strVal,  encoding = StringEncoding.StringEncoding_ASCII):
        # The length of the string (maximum allowed is 16 bytes)
        data = []
        data.append(encoding)
        if len(strVal) > 16 : strVal = strVal[:16]
        print strVal
        if encoding == StringEncoding.StringEncoding_ASCII :
            for i in strVal : data.append(ord(i))
        return data
        
    def extractString(self, _data,  _length):
        encoding = _data[1] & 0x07 
        strVal =""
        if _length >= 3 :
            # Get the length of the string (maximum allowed is 16 bytes)
            numBytes = _length - 3
            if numBytes > 16 : numBytes = 16
            if encoding == StringEncoding.StringEncoding_ASCII:
                # Copy data as-is
                for i in range(0, numBytes+1) :
                    strVal += chr(_data[i+2])
            elif encoding == StringEncoding.StringEncoding_ExtendedASCII:
            # Convert Extended ASCII characters to UTF-8
                surrogate = 0
                for i in range(0, numBytes+1) :
                    ch = _data[i+2];
                    if ch >= 0x80 :
                        utf16 = c_extendedAsciiToUnicode[ch - 0x80]
                        strVal, surrogate = self.ConvertUFT16ToUTF8( utf16, strVal, surrogate)
                    else :
                       strval += chr(ch)
            elif encoding == StringEncoding.StringEncoding_UTF16:
                # Convert UTF-16 characters to UTF-8
                surrogate = 0
                for i in range(0, numBytes+1, 2) :
                    utf16 = ((_data[i+2])<<8) | _data[i+3]
                    strVal, surrogate = self.ConvertUFT16ToUTF8( utf16, strVal, surrogate)
        return strVal

        def ConvertUFT16ToUTF8(self, _utf16, _buffer, surrogate = 0):
            #Convert a UTF-16 string into UTF-8 encoding.
            if (( surrogate != 0 ) and (( _utf16 & 0xdc00 ) == 0xdc00 )):
                # UTF-16 surrogate character pair converts to four UTF-8 characters.
                # We have the second member of the pair, so we can do the conversion now.
                _buffer += chr(((surrogate>>7) & 0x0007) | 0x00f0)
                _buffer += chr(((surrogate>>1) & 0x0020) | ((surrogate>>2) & 0x000f) | 0x0090)
                _buffer += chr(((_utf16>>6) & 0x000f) | ((surrogate<<4) & 0x0030) | 0x0080)
                _buffer += chr((_utf16 & 0x003f) | 0x0080)
            else :
                surrogate = 0
                if _utf16 & 0xff80 :
                    if _utf16 & 0xf800 :
                        if ( _utf16 & 0xd800 ) == 0xd800 :
                            # UTF-16 surrogate character pair converts to four UTF-8 characters.
                            # We have the first member of the pair, so we store it for next time.
                            surrogate = _utf16
                        else :
                            # UTF-16 character can be represented by three UTF-8 characters.
                            _buffer += chr((_utf16>>12) | 0x00e0)
                            _buffer += chr(((_utf16>>6) & 0x003f) | 0x0080)
                            _buffer += chr((_utf16 & 0x003f) | 0x0080)
                    else :
                        # UTF-16 character can be represented by two UTF-8 characters.
                        _buffer += chr((_utf16>>6) | 0x00c0)
                        _buffer += chr((_utf16 & 0x003f) | 0x0080)
                else :
                    # UTF-16 character matches single ascii character.
                    _buffer += chr(_utf16)
        return _buffer, surrogate

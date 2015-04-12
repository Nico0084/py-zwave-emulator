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

import json

ZWVERSION = "Z-Wave 2.78"
SERIALAPIVERSION = [3, 7]
RFCHIPVERSION = [3, 1]

FAKENEIGHBORS = { 1 : [7, 10, 13, 14, 20, 21],
                            4 : [], 
                            6 : [7, 10, 11, 13, 14], 
                            7 : [1, 6, 8, 9, 11, 13, 18, 19, 20, 21],
                            8 : [7], 
                            9 : [], 
                            10: [1, 6, 11, 13, 14, 18, 19, 20, 21], 
                            11: [6, 7, 10, 13, 14, 18, 19], 
                            13: [1, 6, 7, 10, 11, 14, 18, 19], 
                            14: [1, 6, 10, 11, 13, 18, 19],
                            18: [7, 10, 11, 13, 14], 
                            19: [], 
                            20: [1, 7, 10, 21], 
                            21: [1, 7, 10, 20]
                          }

MAX_TRIES	=	3	# Retry sends up to 3 times
MAX_MAX_TRIES	=	7	# Don't exceed this retry limit
ACK_TIMEOUT =	1000		# How long to wait for an ACK
BYTE_TIMEOUT =	150
RETRY_TIMEOUT =	40000		# Retry send after 40 seconds

SOF	=											0x01
ACK	=											0x06
NAK	=											0x15
CAN	=											0x18

NUM_NODE_BITFIELD_BYTES	=			29		# 29 bytes = 232 bits, one for each possible node in the network.

REQUEST =										0x00
RESPONSE	=									0x01

ZW_CLOCK_SET		=						0x30

TRANSMIT_OPTION_ACK	=	 					0x01
TRANSMIT_OPTION_LOW_POWER=		   		0x02
TRANSMIT_OPTION_AUTO_ROUTE  	=			0x04
TRANSMIT_OPTION_NO_ROUTE 	=				0x10
TRANSMIT_OPTION_EXPLORE		=				0x20

TRANSMIT_COMPLETE_OK	  =						0x00
TRANSMIT_COMPLETE_NO_ACK	=  				0x01
TRANSMIT_COMPLETE_FAIL	=						0x02
TRANSMIT_COMPLETE_NOT_IDLE	=				0x03
TRANSMIT_COMPLETE_NOROUTE =					0x04

RECEIVE_STATUS_ROUTED_BUSY	=				0x01
RECEIVE_STATUS_TYPE_BROAD	 =					0x04

FUNC_ID_SERIAL_API_GET_INIT_DATA	=			        0x02
FUNC_ID_SERIAL_API_APPL_NODE_INFORMATION	=	0x03
FUNC_ID_APPLICATION_COMMAND_HANDLER	=			0x04
FUNC_ID_ZW_GET_CONTROLLER_CAPABILITIES	=		0x05
FUNC_ID_SERIAL_API_SET_TIMEOUTS 	=			    0x06
FUNC_ID_SERIAL_API_GET_CAPABILITIES	=			    0x07
FUNC_ID_SERIAL_API_SOFT_RESET	=				        0x08

FUNC_ID_ZW_SEND_NODE_INFORMATION	=			0x12
FUNC_ID_ZW_SEND_DATA		=				0x13
FUNC_ID_ZW_GET_VERSION	=					0x15
FUNC_ID_ZW_R_F_POWER_LEVEL_SET	=				0x17
FUNC_ID_ZW_GET_RANDOM		=				0x1c
FUNC_ID_ZW_MEMORY_GET_ID	=				0x20
FUNC_ID_MEMORY_GET_BYTE	=					0x21
FUNC_ID_ZW_READ_MEMORY		=				0x23

FUNC_ID_ZW_SET_LEARN_NODE_STATE	=				0x40	# Not implemented
FUNC_ID_ZW_GET_NODE_PROTOCOL_INFO	=			0x41	# Get protocol info (baud rate, listening, etc.) for a given node
FUNC_ID_ZW_SET_DEFAULT	=					0x42	# Reset controller and node info to default (original) values
FUNC_ID_ZW_NEW_CONTROLLER	=				0x43	# Not implemented
FUNC_ID_ZW_REPLICATION_COMMAND_COMPLETE	=			0x44	# Replication send data complete
FUNC_ID_ZW_REPLICATION_SEND_DATA	=			0x45	# Replication send data
FUNC_ID_ZW_ASSIGN_RETURN_ROUTE		=			0x46	# Assign a return route from the specified node to the controller
FUNC_ID_ZW_DELETE_RETURN_ROUTE		=			0x47	# Delete all return routes from the specified node
FUNC_ID_ZW_REQUEST_NODE_NEIGHBOR_UPDATE	=			0x48	# Ask the specified node to update its neighbors (then read them from the controller)
FUNC_ID_ZW_APPLICATION_UPDATE	=				0x49	# Get a list of supported (and controller) command classes
FUNC_ID_ZW_ADD_NODE_TO_NETWORK	=				0x4a	# Control the addnode (or addcontroller) process...start, stop, etc.
FUNC_ID_ZW_REMOVE_NODE_FROM_NETWORK	=			0x4b	# Control the removenode (or removecontroller) process...start, stop, etc.
FUNC_ID_ZW_CREATE_NEW_PRIMARY	=				0x4c	# Control the createnewprimary process...start, stop, etc.
FUNC_ID_ZW_CONTROLLER_CHANGE	=				0x4d	# Control the transferprimary process...start, stop, etc.
FUNC_ID_ZW_SET_LEARN_MODE		=			0x50	# Put a controller into learn mode for replication/ receipt of configuration info
FUNC_ID_ZW_ASSIGN_SUC_RETURN_ROUTE	=			0x51	# Assign a return route to the SUC
FUNC_ID_ZW_ENABLE_SUC	=					0x52	# Make a controller a Static Update Controller
FUNC_ID_ZW_REQUEST_NETWORK_UPDATE	=			0x53	# Network update for a SUC(?)
FUNC_ID_ZW_SET_SUC_NODE_ID	=				0x54	# Identify a Static Update Controller node id
FUNC_ID_ZW_DELETE_SUC_RETURN_ROUTE	=			0x55	# Remove return routes to the SUC
FUNC_ID_ZW_GET_SUC_NODE_ID	=				0x56	# Try to retrieve a Static Update Controller node id (zero if no SUC present)
FUNC_ID_ZW_REQUEST_NODE_NEIGHBOR_UPDATE_OPTIONS	=		0x5a	# Allow options for request node neighbor update
FUNC_ID_ZW_REQUEST_NODE_INFO	=				0x60	# Get info (supported command classes) for the specified node
FUNC_ID_ZW_REMOVE_FAILED_NODE_ID	=			0x61	# Mark a specified node id as failed
FUNC_ID_ZW_IS_FAILED_NODE_ID		=			0x62	# Check to see if a specified node has failed
FUNC_ID_ZW_REPLACE_FAILED_NODE		=			0x63	# Remove a failed node from the controller's list (?)
FUNC_ID_ZW_GET_ROUTING_INFO		=			0x80	# Get a specified node's neighbor information from the controller
FUNC_ID_SERIAL_API_SLAVE_NODE_INFO		=		0xA0	# Set application virtual slave node information
FUNC_ID_APPLICATION_SLAVE_COMMAND_HANDLER	=		0xA1	# Slave command handler
FUNC_ID_ZW_SEND_SLAVE_NODE_INFO	=				0xA2	# Send a slave node information frame
FUNC_ID_ZW_SEND_SLAVE_DATA	=			0xA3	# Send data from slave
FUNC_ID_ZW_SET_SLAVE_LEARN_MODE	=				0xA4	# Enter slave learn mode
FUNC_ID_ZW_GET_VIRTUAL_NODES	=				0xA5	# Return all virtual nodes
FUNC_ID_ZW_IS_VIRTUAL_NODE		=			0xA6	# Virtual node test
FUNC_ID_ZW_SET_PROMISCUOUS_MODE	=				0xD0	# Set controller into promiscuous mode to listen to all frames
FUNC_ID_PROMISCUOUS_APPLICATION_COMMAND_HANDLER	=		0xD1

ADD_NODE_ANY		=							0x01
ADD_NODE_CONTROLLER		=						0x02
ADD_NODE_SLAVE		=							0x03
ADD_NODE_EXISTING		=						0x04
ADD_NODE_STOP			=						0x05
ADD_NODE_STOP_FAILED		=						0x06

ADD_NODE_STATUS_LEARN_READY		=				0x01
ADD_NODE_STATUS_NODE_FOUND		=				0x02
ADD_NODE_STATUS_ADDING_SLAVE	 =					0x03
ADD_NODE_STATUS_ADDING_CONTROLLER		=			0x04
ADD_NODE_STATUS_PROTOCOL_DONE		=				0x05
ADD_NODE_STATUS_DONE				=			0x06
ADD_NODE_STATUS_FAILED		=					0x07

REMOVE_NODE_ANY				=					0x01
REMOVE_NODE_CONTROLLER		=						0x02
REMOVE_NODE_SLAVE		=						0x03
REMOVE_NODE_STOP			=					0x05

REMOVE_NODE_STATUS_LEARN_READY	=				0x01
REMOVE_NODE_STATUS_NODE_FOUND		=			0x02
REMOVE_NODE_STATUS_REMOVING_SLAVE	=			0x03
REMOVE_NODE_STATUS_REMOVING_CONTROLLER	=			0x04
REMOVE_NODE_STATUS_DONE		=				0x06
REMOVE_NODE_STATUS_FAILED		=			0x07

CREATE_PRIMARY_START	=						0x02
CREATE_PRIMARY_STOP	=						0x05
CREATE_PRIMARY_STOP_FAILED	=					0x06

CONTROLLER_CHANGE_START		=					0x02
CONTROLLER_CHANGE_STOP		=					0x05
CONTROLLER_CHANGE_STOP_FAILED	=					0x06

LEARN_MODE_STARTED		=						0x01
LEARN_MODE_DONE			=						0x06
LEARN_MODE_FAILED		=						0x07
LEARN_MODE_DELETED		=						0x80

REQUEST_NEIGHBOR_UPDATE_STARTED	=	0x21
REQUEST_NEIGHBOR_UPDATE_DONE	    =	0x22
REQUEST_NEIGHBOR_UPDATE_FAILED		=	0x23

FAILED_NODE_OK			=						0x00
FAILED_NODE_REMOVED	=							0x01
FAILED_NODE_NOT_REMOVED			=				0x02

FAILED_NODE_REPLACE_WAITING=						0x03
FAILED_NODE_REPLACE_DONE		=				0x04
FAILED_NODE_REPLACE_FAILED		=				0x05

FAILED_NODE_REMOVE_STARTED	=					0x00
FAILED_NODE_NOT_PRIMARY_CONTROLLER		=		0x02
FAILED_NODE_NO_CALLBACK_FUNCTION	=			0x04
FAILED_NODE_NOT_FOUND					=		0x08
FAILED_NODE_REMOVE_PROCESS_BUSY	=				0x10
FAILED_NODE_REMOVE_FAIL			=				0x20

SUC_UPDATE_DONE					=				0x00
SUC_UPDATE_ABORT			=					0x01
SUC_UPDATE_WAIT				=					0x02
SUC_UPDATE_DISABLED			=					0x03
SUC_UPDATE_OVERFLOW		=						0x04

SUC_FUNC_BASIC_SUC		=						0x00
SUC_FUNC_NODEID_SERVER		=					0x01

UPDATE_STATE_NODE_INFO_RECEIVED		=			0x84
UPDATE_STATE_NODE_INFO_REQ_DONE	=				0x82
UPDATE_STATE_NODE_INFO_REQ_FAILED	=			0x81
UPDATE_STATE_ROUTING_PENDING			=		0x80
UPDATE_STATE_NEW_ID_ASSIGNED		=			0x40
UPDATE_STATE_DELETE_DONE		=			0x20
UPDATE_STATE_SUC_ID			=			0x10

APPLICATION_NODEINFO_LISTENING	=				0x01
APPLICATION_NODEINFO_OPTIONAL_FUNCTIONALITY	=		0x02

SLAVE_ASSIGN_COMPLETE		=					0x00
SLAVE_ASSIGN_NODEID_DONE		=				0x01	# Node ID has been assigned
SLAVE_ASSIGN_RANGE_INFO_UPDATE	=				0x02	# Node is doing neighbor discovery

SLAVE_LEARN_MODE_DISABLE		=				0x00	# disable add/remove virtual slave nodes
SLAVE_LEARN_MODE_ENABLE		=					0x01	# enable ability to include/exclude virtual slave nodes
SLAVE_LEARN_MODE_ADD			=				0x02	# add node directly but only if primary/inclusion controller
SLAVE_LEARN_MODE_REMOVE	=						0x03	# remove node directly but only if primary/inclusion controller

OPTION_HIGH_POWER			=					0x80

#Device request related
BASIC_SET				=						0x01
BASIC_REPORT		=							0x03

COMMAND_CLASS_BASIC			=					0x20
COMMAND_CLASS_CONTROLLER_REPLICATION	=		0x21
COMMAND_CLASS_APPLICATION_STATUS =				0x22
COMMAND_CLASS_HAIL			=					0x82

"""" Parameters for generate polled value, define values of params
In key "pollingvalues" : [ 
            {
                "cmdclass" : < name of command class >
                "instance" : number of instance >
                "label" : < label from value>
                "timing" : < frequency at which the poll value is generated >
                "unable" : <True/False to activat the poll>
                "params" : {
                    "polltype": < type of polling bounds (choice) >
                                        "rangeNumber" <range between min max, {min, max}>
                                        "serie" < serie of values, 'tab':[1,2,3,5,9,8,10] >
                    "mode" : < how generate values from "polltype" (choice)>
                            "random" < randomize > 
                            "round" < course value and restart from first >
                            "roundtrip" < course value with return course >
                            "incremental" < increment and restart from first >
                            "incrementaltrip" < increment with return course >
                    "values": < dict of values, use valuetype> {'min':, 'max':}, {'tab':[1,2,3,5,9,8,10] >
                    "step": < value for increment >
                    }
"""
"""
 Commands classes from lib openzwave
"""
COMMAND_CLASS_DESC = {
    0x00: 'COMMAND_CLASS_NO_OPERATION',
    0x20: 'COMMAND_CLASS_BASIC',
    0x21: 'COMMAND_CLASS_CONTROLLER_REPLICATION',
    0x22: 'COMMAND_CLASS_APPLICATION_STATUS',
    0x23: 'COMMAND_CLASS_ZIP_SERVICES',
    0x24: 'COMMAND_CLASS_ZIP_SERVER',
    0x25: 'COMMAND_CLASS_SWITCH_BINARY',
    0x26: 'COMMAND_CLASS_SWITCH_MULTILEVEL',
    0x27: 'COMMAND_CLASS_SWITCH_ALL',
    0x28: 'COMMAND_CLASS_SWITCH_TOGGLE_BINARY',
    0x29: 'COMMAND_CLASS_SWITCH_TOGGLE_MULTILEVEL',
    0x2A: 'COMMAND_CLASS_CHIMNEY_FAN',
    0x2B: 'COMMAND_CLASS_SCENE_ACTIVATION',
    0x2C: 'COMMAND_CLASS_SCENE_ACTUATOR_CONF',
    0x2D: 'COMMAND_CLASS_SCENE_CONTROLLER_CONF',
    0x2E: 'COMMAND_CLASS_ZIP_CLIENT',
    0x2F: 'COMMAND_CLASS_ZIP_ADV_SERVICES',
    0x30: 'COMMAND_CLASS_SENSOR_BINARY',
    0x31: 'COMMAND_CLASS_SENSOR_MULTILEVEL',
    0x32: 'COMMAND_CLASS_METER',
    0x33: 'COMMAND_CLASS_ZIP_ADV_SERVER',
    0x34: 'COMMAND_CLASS_ZIP_ADV_CLIENT',
    0x35: 'COMMAND_CLASS_METER_PULSE',
    0x3C: 'COMMAND_CLASS_METER_TBL_CONFIG',
    0x3D: 'COMMAND_CLASS_METER_TBL_MONITOR',
    0x3E: 'COMMAND_CLASS_METER_TBL_PUSH',
    0x38: 'COMMAND_CLASS_THERMOSTAT_HEATING',
    0x40: 'COMMAND_CLASS_THERMOSTAT_MODE',
    0x42: 'COMMAND_CLASS_THERMOSTAT_OPERATING_STATE',
    0x43: 'COMMAND_CLASS_THERMOSTAT_SETPOINT',
    0x44: 'COMMAND_CLASS_THERMOSTAT_FAN_MODE',
    0x45: 'COMMAND_CLASS_THERMOSTAT_FAN_STATE',
    0x46: 'COMMAND_CLASS_CLIMATE_CONTROL_SCHEDULE',
    0x47: 'COMMAND_CLASS_THERMOSTAT_SETBACK',
    0x4c: 'COMMAND_CLASS_DOOR_LOCK_LOGGING',
    0x4E: 'COMMAND_CLASS_SCHEDULE_ENTRY_LOCK',
    0x50: 'COMMAND_CLASS_BASIC_WINDOW_COVERING',
    0x51: 'COMMAND_CLASS_MTP_WINDOW_COVERING',
    0x60: 'COMMAND_CLASS_MULTI_CHANNEL_V2',
    0x61: 'COMMAND_CLASS_DISPLAY',
    0x62: 'COMMAND_CLASS_DOOR_LOCK',
    0x63: 'COMMAND_CLASS_USER_CODE',
    0x64: 'COMMAND_CLASS_GARAGE_DOOR',
    0x70: 'COMMAND_CLASS_CONFIGURATION',
    0x71: 'COMMAND_CLASS_ALARM',
    0x72: 'COMMAND_CLASS_MANUFACTURER_SPECIFIC',
    0x73: 'COMMAND_CLASS_POWERLEVEL',
    0x75: 'COMMAND_CLASS_PROTECTION',
    0x76: 'COMMAND_CLASS_LOCK',
    0x77: 'COMMAND_CLASS_NODE_NAMING',
    0x78: 'COMMAND_CLASS_ACTUATOR_MULTILEVEL',
    0x79: 'COMMAND_CLASS_KICK',
    0x7A: 'COMMAND_CLASS_FIRMWARE_UPDATE_MD',
    0x7B: 'COMMAND_CLASS_GROUPING_NAME',
    0x7C: 'COMMAND_CLASS_REMOTE_ASSOCIATION_ACTIVATE',
    0x7D: 'COMMAND_CLASS_REMOTE_ASSOCIATION',
    0x80: 'COMMAND_CLASS_BATTERY',
    0x81: 'COMMAND_CLASS_CLOCK',
    0x82: 'COMMAND_CLASS_HAIL',
    0x83: 'COMMAND_CLASS_NETWORK_STAT',
    0x84: 'COMMAND_CLASS_WAKE_UP',
    0x85: 'COMMAND_CLASS_ASSOCIATION',
    0x86: 'COMMAND_CLASS_VERSION',
    0x87: 'COMMAND_CLASS_INDICATOR',
    0x88: 'COMMAND_CLASS_PROPRIETARY',
    0x89: 'COMMAND_CLASS_LANGUAGE',
    0x8A: 'COMMAND_CLASS_TIME',
    0x8B: 'COMMAND_CLASS_TIME_PARAMETERS',
    0x8C: 'COMMAND_CLASS_GEOGRAPHIC_LOCATION',
    0x8D: 'COMMAND_CLASS_COMPOSITE',
    0x8E: 'COMMAND_CLASS_MULTI_INSTANCE_ASSOCIATION',
    0x8F: 'COMMAND_CLASS_MULTI_CMD',
    0x90: 'COMMAND_CLASS_ENERGY_PRODUCTION',
    0x91: 'COMMAND_CLASS_MANUFACTURER_PROPRIETARY',
    0x92: 'COMMAND_CLASS_SCREEN_MD',
    0x93: 'COMMAND_CLASS_SCREEN_ATTRIBUTES',
    0x94: 'COMMAND_CLASS_SIMPLE_AV_CONTROL',
    0x95: 'COMMAND_CLASS_AV_CONTENT_DIRECTORY_MD',
    0x96: 'COMMAND_CLASS_AV_RENDERER_STATUS',
    0x97: 'COMMAND_CLASS_AV_CONTENT_SEARCH_MD',
    0x98: 'COMMAND_CLASS_SECURITY',
    0x99: 'COMMAND_CLASS_AV_TAGGING_MD',
    0x9A: 'COMMAND_CLASS_IP_CONFIGURATION',
    0x9B: 'COMMAND_CLASS_ASSOCIATION_COMMAND_CONFIGURATION',
    0x9C: 'COMMAND_CLASS_SENSOR_ALARM',
    0x9D: 'COMMAND_CLASS_SILENCE_ALARM',
    0x9E: 'COMMAND_CLASS_SENSOR_CONFIGURATION',
    0xEF: 'COMMAND_CLASS_MARK',
    0xF0: 'COMMAND_CLASS_NON_INTEROPERABLE'
    }

class EnumNamed:
    
    def getName(self,  _id):
        for item in self.__class__.__dict__:
            if self.__class__.__dict__[item] == _id: return item
        raise Exception('Class {0}(EnumNamed): id {1} undefined'.format(self.__class__.__name__, _id))

    def getFullName(self,  _id):
        return "{0}.{1}".format(self.__class__.__name__, self.getName(_id))

    def getFromName(self,  name):
        name = name.lower()
        for item in self.__class__.__dict__:
            if item.lower() == name: return self.__class__.__dict__[item]
        raise Exception('Class {0}(EnumNamed): name {1} undefined.'.format(self.__class__.__name__, name))

def getFuncName(func):
    var = globals()
    for v in var:
        if v[0:8] == 'FUNC_ID_' and var[v] == func : return v
    return ''

def GetDataAsHex(data, nChar = 2):
    strVal = ""
    baseStr = "0x%.{0}x".format(nChar)
    for i in range(0, len(data)) :
        if i : strVal += ", "
        strVal += baseStr%data[i]
    return strVal

def readJsonFile(file):
    json_fp = open(file)
    data = json.load(json_fp)
    json_fp.close()
    return data

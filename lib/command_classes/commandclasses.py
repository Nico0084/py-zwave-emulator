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

from Alarm import Alarm
from ApplicationStatus import ApplicationStatus
from Association  import Association
from AssociationCommandConfiguration import AssociationCommandConfiguration
from Basic import Basic
from BasicWindowCovering import BasicWindowCovering
from Battery import Battery
from ClimateControlSchedule import ClimateControlSchedule
from Clock import Clock
from Configuration import Configuration
from ControllerReplication import ControllerReplication
from CRC16Encap import CRC16Encap
from DoorLock import DoorLock
from DoorLockLogging import DoorLockLogging
from EnergyProduction import EnergyProduction
from Hail import Hail
from Indicator import Indicator
from Language import Language
from Lock import Lock
from ManufacturerSpecific import ManufacturerSpecific
from Meter import Meter
from MeterPulse import MeterPulse
from MultiCmd import MultiCmd
from MultiInstance import MultiInstance
from MultiInstanceAssociation import MultiInstanceAssociation
from NodeNaming import NodeNaming
from NoOperation import NoOperation
from Powerlevel import Powerlevel
from Proprietary import Proprietary
from Protection import Protection
from SceneActivation import SceneActivation
from Security import Security
from SensorAlarm import SensorAlarm
from SensorBinary import SensorBinary
from SensorMultilevel import SensorMultilevel
from SwitchAll import SwitchAll
from SwitchBinary import SwitchBinary
from SwitchMultilevel import SwitchMultilevel
from SwitchToggleBinary import SwitchToggleBinary
from SwitchToggleMultilevel import SwitchToggleMultilevel
from TimeParameters import TimeParameters
from ThermostatFanMode import ThermostatFanMode
from ThermostatFanState import ThermostatFanState
from ThermostatMode import ThermostatMode
from ThermostatOperatingState import ThermostatOperatingState
from ThermostatSetpoint import ThermostatSetpoint
from UserCode import UserCode
from Version import Version
from WakeUp import WakeUp

from zwemulator.lib.defs import *

class CommandClasses:

    def __init__(self, manager):
        self._manager = manager
        self.m_commandClasses = {}
        self.m_supportedCommandClasses = []

    def IsSupported(self, _commandClassId):
        """Static method to determine whether a command class is supported"""
        # Test the bit representing the command class
        return _commandClassId in self.m_supportedCommandClasses

    def GetName(self, _commandClassId):
        if _commandClassId in self.m_commandClasses:
#            if self.m_commandClasses[clss].GetCommandClassId == _commandClassId : 
            return self.m_commandClasses[_commandClassId].GetCommandClassName
        return "Unknown"

    def GetCommandClassId(self, _name):
        for clss in self.m_commandClasses:
            if self.m_commandClasses[clss].StaticGetCommandClassName == _name :
                return self.m_commandClasses[clss].StaticGetCommandClassId
        return 0xff

    def Register(self, _commandClassId, _commandClassName, _cmdClass):
        """Static method to register a command class creator method"""

        self.m_commandClasses[_commandClassId] = _cmdClass;
        # Set the bit representing the command class
        self.m_supportedCommandClasses.append(_commandClassId)

    def CreateCommandClass(self, _commandClassId, _node, _data):
        """Create a command class object using the registered method"""
        # Get a pointer to the required CommandClass's Create method
        if _commandClassId in self.m_supportedCommandClasses: 
            CmdClass = self.m_commandClasses[_commandClassId]
            # Create an instance of the command class
            return CmdClass(_node, _data)
        return None

    def RegisterCommandClasses(self):
        """Register all our implemented command classes"""

        self.Register( Alarm.StaticGetCommandClassId, Alarm.StaticGetCommandClassName, Alarm)
        self.Register( ApplicationStatus.StaticGetCommandClassId, ApplicationStatus.StaticGetCommandClassName, ApplicationStatus)
        self.Register( Association.StaticGetCommandClassId, Association.StaticGetCommandClassName, Association)
        self.Register( AssociationCommandConfiguration.StaticGetCommandClassId, AssociationCommandConfiguration.StaticGetCommandClassName, AssociationCommandConfiguration)
        self.Register( Basic.StaticGetCommandClassId, Basic.StaticGetCommandClassName, Basic)
        self.Register( BasicWindowCovering.StaticGetCommandClassId, BasicWindowCovering.StaticGetCommandClassName, BasicWindowCovering)
        self.Register( Battery.StaticGetCommandClassId, Battery.StaticGetCommandClassName, Battery)
        self.Register( ClimateControlSchedule.StaticGetCommandClassId, ClimateControlSchedule.StaticGetCommandClassName, ClimateControlSchedule)
        self.Register( Clock.StaticGetCommandClassId, Clock.StaticGetCommandClassName, Clock)
        self.Register( Configuration.StaticGetCommandClassId, Configuration.StaticGetCommandClassName, Configuration)
        self.Register( ControllerReplication.StaticGetCommandClassId, ControllerReplication.StaticGetCommandClassName, ControllerReplication)
        self.Register( CRC16Encap.StaticGetCommandClassId, CRC16Encap.StaticGetCommandClassName, CRC16Encap)
        self.Register( DoorLock.StaticGetCommandClassId, DoorLock.StaticGetCommandClassName, DoorLock)
        self.Register( DoorLockLogging.StaticGetCommandClassId, DoorLockLogging.StaticGetCommandClassName, DoorLockLogging);
        self.Register( EnergyProduction.StaticGetCommandClassId, EnergyProduction.StaticGetCommandClassName, EnergyProduction)
        self.Register( Hail.StaticGetCommandClassId, Hail.StaticGetCommandClassName, Hail)
        self.Register( Indicator.StaticGetCommandClassId, Indicator.StaticGetCommandClassName, Indicator)
        self.Register( Language.StaticGetCommandClassId, Language.StaticGetCommandClassName, Language)
        self.Register( Lock.StaticGetCommandClassId, Lock.StaticGetCommandClassName, Lock)
        self.Register( ManufacturerSpecific.StaticGetCommandClassId, ManufacturerSpecific.StaticGetCommandClassName, ManufacturerSpecific)
        self.Register( Meter.StaticGetCommandClassId, Meter.StaticGetCommandClassName, Meter)
        self.Register( MeterPulse.StaticGetCommandClassId, MeterPulse.StaticGetCommandClassName, MeterPulse)
        self.Register( MultiCmd.StaticGetCommandClassId, MultiCmd.StaticGetCommandClassName, MultiCmd)
        self.Register( MultiInstance.StaticGetCommandClassId, MultiInstance.StaticGetCommandClassName, MultiInstance)
        self.Register( MultiInstanceAssociation.StaticGetCommandClassId, MultiInstanceAssociation.StaticGetCommandClassName, MultiInstanceAssociation)
        self.Register( NodeNaming.StaticGetCommandClassId, NodeNaming.StaticGetCommandClassName, NodeNaming)
        self.Register( NoOperation.StaticGetCommandClassId, NoOperation.StaticGetCommandClassName, NoOperation)
        self.Register( Powerlevel.StaticGetCommandClassId, Powerlevel.StaticGetCommandClassName, Powerlevel)
        self.Register( Proprietary.StaticGetCommandClassId, Proprietary.StaticGetCommandClassName, Proprietary)
        self.Register( Protection.StaticGetCommandClassId, Protection.StaticGetCommandClassName, Protection)
        self.Register( SceneActivation.StaticGetCommandClassId, SceneActivation.StaticGetCommandClassName, SceneActivation)
        self.Register( Security.StaticGetCommandClassId, Security.StaticGetCommandClassName, Security)
        self.Register( SensorAlarm.StaticGetCommandClassId, SensorAlarm.StaticGetCommandClassName, SensorAlarm)
        self.Register( SensorBinary.StaticGetCommandClassId, SensorBinary.StaticGetCommandClassName, SensorBinary)
        self.Register( SensorMultilevel.StaticGetCommandClassId, SensorMultilevel.StaticGetCommandClassName, SensorMultilevel)
        self.Register( SwitchAll.StaticGetCommandClassId, SwitchAll.StaticGetCommandClassName, SwitchAll)
        self.Register( SwitchBinary.StaticGetCommandClassId, SwitchBinary.StaticGetCommandClassName, SwitchBinary)
        self.Register( SwitchMultilevel.StaticGetCommandClassId, SwitchMultilevel.StaticGetCommandClassName, SwitchMultilevel)
        self.Register( SwitchToggleBinary.StaticGetCommandClassId, SwitchToggleBinary.StaticGetCommandClassName, SwitchToggleBinary)
        self.Register( SwitchToggleMultilevel.StaticGetCommandClassId, SwitchToggleMultilevel.StaticGetCommandClassName, SwitchToggleMultilevel)
        self.Register( TimeParameters.StaticGetCommandClassId, TimeParameters.StaticGetCommandClassName, TimeParameters);
        self.Register( ThermostatFanMode.StaticGetCommandClassId, ThermostatFanMode.StaticGetCommandClassName, ThermostatFanMode)
        self.Register( ThermostatFanState.StaticGetCommandClassId, ThermostatFanState.StaticGetCommandClassName, ThermostatFanState)
        self.Register( ThermostatMode.StaticGetCommandClassId, ThermostatMode.StaticGetCommandClassName, ThermostatMode)
        self.Register( ThermostatOperatingState.StaticGetCommandClassId, ThermostatOperatingState.StaticGetCommandClassName, ThermostatOperatingState)
        self.Register( ThermostatSetpoint.StaticGetCommandClassId, ThermostatSetpoint.StaticGetCommandClassName, ThermostatSetpoint)
        self.Register( UserCode.StaticGetCommandClassId, UserCode.StaticGetCommandClassName, UserCode)
        self.Register( Version.StaticGetCommandClassId, Version.StaticGetCommandClassName, Version)
        self.Register( WakeUp.StaticGetCommandClassId, WakeUp.StaticGetCommandClassName, WakeUp)

        # Now all the command classes have been registered, we can modify the
        # supported command classes array according to the program options.
        find, str = self._manager._options.GetOptionAsString("Include")
        if str != "":
            # The include list has entries, so we assume that it is a
            # complete list of what should be supported.
            # Any existing support is cleared first.
            self.ParseCommandClassOption(str, True)

        # Apply the excluded command class option
        find,  str= self._manager._options.GetOptionAsString( "Exclude")
        if str != "":
            cc.ParseCommandClassOption( str, False)
            
        print "supported class : ",  self.m_supportedCommandClasses

    def ParseCommandClassOption(self, _optionStr, _include):
        """Parse a comma delimited list of included/excluded command classes"""
        print _optionStr
        ClssIds = _optionStr.split(",")
        for id in ClssIds :
            if id != "" :
                try:
                    ccIdx = int(id, 16)
                except :
                    ccIdx = self.GetCommandClassId(id)
                if ccIdx != 0xff:
                    if _include:
                        self.m_supportedCommandClasses.append(ccIdx)
                    else:
                        try :
                            self.m_supportedCommandClasses.remove(ccIdx)
                        except:
                            pass
                

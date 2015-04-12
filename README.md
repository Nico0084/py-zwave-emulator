Under construction ...
================

## ZWave emulator
[**py-zwave-emulator**](project #https://github.com/Nico0084/py-zwave-emulator) is a ZWave network emulator, no hardware need.
  - platform: Unix, Windows, MacOS X
  - sinopsis: ZWave emulator Python

This project is based on [openzwave](https://github.com/OpenZWave/open-zwave) to pass thought hardware zwave device. It use for API developping or testing.

## Basic Instruction
- Openzwave config files are use to load a fake zwave network an handle virtual nodes. All configured manufacturer device can be create in emulator.
- Use serial port emulator to create com, you can use software like [socat](http://www.dest-unreach.org/socat/)
- eg command line : socat -d -d PTY,ignoreeof,echo=0,raw,link=/tmp/ttyS0 PTY,ignoreeof,echo=0,raw,link=/tmp/ttyS1 &
- Run from bin/zwemulator.py (serial port default : /tmp/ttyS0)
- Web UI access on local address (port default : 4500)


## License : GPL(v3)

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

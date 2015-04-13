#!/usr/bin/python
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

import sys
sys.path.insert(0,'../..')

from threading import Thread
from zwemulator.lib.manager import OPTIONS,  Manager 
from zwemulator.wui.zwemulatorwui import app
from zwemulator.lib.defs import readJsonFile

from flask import request
 

def joinwui(*_data, **params):
    stop = params['manager']._stop
    while not stop.isSet():
        stop.wait(0.1)
    shutdown_server()    

def shutdown_server():
    try :
        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
            raise RuntimeError('Not running with the Werkzeug Server')
        func()
    except :
        print "Server already stopped."

if __name__ == '__main__':
    print "************** Start in main zwemulator.py **************"
    OPTIONS.create("../openzwave/config", "", "--logging true --LogFileName test.log")
    print "NotifyTransactions :", OPTIONS.AddOptionBool('NotifyTransactions',  True)
    OPTIONS.Lock()
    manager = Manager()
    try :
        manager.paramsConfig = readJsonFile('../data/config_emulation.json')
        print 'readed'
        print "Config parameters loaded : {0}".format(manager.paramsConfig)
        host = manager.paramsConfig['webui']['host']
        port = manager.paramsConfig['webui']['port']
        wuiApp = Thread(None, joinwui, "th_wui_zwave_ctrl_emulator", (), {'manager':manager})
        wuiApp.start()
        manager.Create()
    #    manager.Addwatcher(notif_callback, API().pyCallback)
        app.run(host=host, port=port, threaded=True, use_reloader=False)
        manager._stop.set()
        for driver in manager.drivers:
            driver.running = False
    except:
        print "No correct file config for emulation in data path. EXIT"

#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
.. module:: zwemulator

This file is part of **python-ozw-ctlr-emulator** project http://github.com/Nico0084/python-ozw-ctlr-emulator.
    :platform: Unix
    :sinopsis: openzwave controller serial simulator Python

This project is based on openzwave lib to pass thought hardware zwave device. It use for API developping or testing.
Based on openzwave project config files to simulate a zwave network and his nodes.
All C++ and cython code are moved.

.. moduleauthor: Nico0084 <nico84dev@gmail.com>

License : GPL(v3)

**python-ozw-ctlr-emulator** is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

**python-ozw-ctlr-emulator** is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with python-openzwave. If not, see http://www.gnu.org/licenses.

"""

import sys
sys.path.insert(0,'../..')

from threading import Event, Thread
from zwemulator.lib.manager import MANAGER, OPTIONS,  Manager 
from zwemulator.wui.zwemulatorwui import app
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
    print "************** Start in main of zwemulator.py **************"
    OPTIONS.create("../openzwave/config", "", "--logging true --LogFileName test.log")
    print "NotifyTransactions :", OPTIONS.AddOptionBool('NotifyTransactions',  True)
    OPTIONS.Lock()
    manager = Manager()
    wuiApp = Thread(None, joinwui, "th_wui_zwave_ctrl_emulator", (), {'manager':manager})
    wuiApp.start()
    manager.Create()
#    manager.Addwatcher(notif_callback, API().pyCallback)
    manager.AddDriver('/tmp/ttyS1')
    
    app.run(host='0.0.0.0', port=4500, threaded=True, use_reloader=False)
    manager._stop.set()
    for driver in manager.drivers:
        driver.running = False

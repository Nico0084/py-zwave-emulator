#!/usr/bin/python
# -*- coding: utf-8 -*-

from flask import Flask
#import sys
#sys.path.insert(0,'..')
#from zwemulator.lib.manager import MANAGER, OPTIONS,  Manager
app = Flask(__name__)
app.debug = True
app.secret_key = 'zwave-emulator-python'

from views.index import *
from views.virtualnodes import *
from views.virtualcmdclss import *

app.jinja_env.filters['renderCmdClssGeneric'] = renderCmdClssGeneric
app.jinja_env.add_extension('jinja2.ext.do')

#if __name__ == '__main__':
#    OPTIONS.create("../openzwave/config", "", "--logging true --LogFileName test.log")
#    print "NotifyTransactions :", OPTIONS.AddOptionBool('NotifyTransactions',  True)
#    OPTIONS.Lock()
#    manager = Manager()
#    MANAGER = manager
#    manager.Create()
##    manager.Addwatcher(notif_callback, API().pyCallback)
#    manager.AddDriver('/tmp/ttyS1')
#    
#    app.run(host='0.0.0.0')
#    manager._stop.set()
#    for driver in manager.drivers:
#        driver.running = False

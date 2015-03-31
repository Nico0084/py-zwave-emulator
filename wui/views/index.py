# -*- coding: utf-8 -*-     
from zwemulator.wui.zwemulatorwui import app
from flask import render_template
from flask_login import login_required

from zwemulator.lib.manager import Manager

@app.route('/')
# @login_required
def index():
    if Manager is not None :
        status = u"Initialisé"
    else : status = u"Non déclaré"
    return render_template('index.html',
                        mactive = "", 
                        managerStatus = status)

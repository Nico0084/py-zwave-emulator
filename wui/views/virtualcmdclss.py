# -*- coding: utf-8 -*-     
from wui.zwemulatorwui import app
from flask import render_template, request, flash, jsonify #, redirect, url_for
#from flask_login import login_required

from lib.manager import Manager
import json


@app.route('/virtualnodes/<node_ref>/cmd_classes', methods=['GET', 'POST'])
def virtualnode_cmdClasses(node_ref):
    manager =  Manager()
    homeId = node_ref.split(".")[0]
    nodeId = int(node_ref.split(".")[1])
    node = manager.getNode(homeId, nodeId)
    if node is not None:
        if request.method == 'POST':
#            clss = node.getCmdClass(int(request.form['clssId']))
            if 'manufacturerId' in request.form:
                try :
                    node.SetManufacturerId(int(request.form['manufacturerId'], 16))
                    flash(u"Manufactured id is changed to : {0}".format(request.form['manufacturerId']), 'success')
                except :
                    flash(u"ERROR: You must enter an hexadecimal format ({0})".format(request.form['manufacturerId']), 'error')
            elif 'manufacturerName' in request.form:
                node.SetManufacturerName(request.form['manufacturerName'])
                flash(u"Manufactured name is changed to : {0}".format(request.form['manufacturerName']), 'success')
            else :
                flash(u"Requête inconnue : {0}".format(request.form), 'error')
        return render_template('virtualnode_cmd_classes.html',
            mactive="virtualnodes",
            active = 'cmd_classes',
            node_ref = node_ref,
            node = node
            )
    return json.dumps({ "error": "Virtual Node {0} not find.".format(node_ref) }), 500 
    
@app.route('/virtualnodes/<node_ref>/update_clss')
def virtualnode_cmdClss_update(node_ref):
    inputId = request.args.get('inputId', 0, type=str)
    clssId = request.args.get('clssId', 0, type=int)
    key = request.args.get('key', 0, type=str)
    value = request.args.get('value', 0, type=str)
    print "Update cms clss :", clssId,  key, value
    manager =  Manager()
    homeId = node_ref.split(".")[0]
    nodeId = int(node_ref.split(".")[1])
    node = manager.getNode(homeId, nodeId)
    if node is not None:
        clss = node.getCmdClass(int(clssId))
        result = 'success'
        if type(value) == str: value = u"{0}".format(value)
        if key == 'issupported' :
            msg = u"Cmd clss supported is changed to : {0}".format(value)
            if value == 'true' : clss.m_getSupported = True
            elif value == 'false' : clss.m_getSupported = False
            else : 
                msg = u"ERROR: Not true/false format ({0})".format(value)
                result = 'error'
                value = clss.m_getSupported
        elif key == 'version' :
            clss.m_version = value
            msg = u"Cmd clss version is changed to : {0}".format(value)
        elif key == 'manufacturerId' :
            try :
                node.SetManufacturerId(int(value, 16))
                msg = u"Manufactured id is changed to : {0}".format(value)
            except :
                msg = u"ERROR: You must enter an hexadecimal format ({0})".format(value)
                result = 'error'
                value = node.GetManufacturerId
        elif key == 'manufacturerName' :
            node.SetManufacturerName(value)
            msg = u"Manufactured name is changed to : {0}".format(value)
        elif key == 'productType':
            try :
                node.SetProductType(int(value, 16))
                msg = u"ProductType is changed to : {0}".format(value)
            except :
                msg = u"ERROR: You must enter an hexadecimal format ({0})".format(value)
                result = 'error'
                value = node.GetProductType
        elif key == 'productId':
            try :
                node.SetProductId(int(value, 16))
                msg = u"Product id is changed to : {0}".format(value)
            except :
                msg = u"ERROR: You must enter an hexadecimal format ({0})".format(value)
                result = 'error'
                value = node.GetProductId
        elif key[:4] == 'grp_':
            indexGrp = int(key[4:])
            result,  error = clss.SetGroupKey(indexGrp, 'label', value)
            if result : 
                msg = u"Label group {0} is changed to : {1}".format(indexGrp,  value)
            else :
                result = 'error'
                msg = u"Label group {0} can't set to : {1} - {2}".format(indexGrp, value, error)
                value = clss.getGroup(indexGrp)['label']
        elif key[:4] == 'max_':
            indexGrp = int(key[4:])
            try :
                result,  error = clss.SetGroupKey(indexGrp, 'max_associations', int(value))
                if result:
                    msg = u"max_associations group {0} is changed to : {1}".format(indexGrp,  value)
                else :
                    result = 'error'
                    msg = u"max_associations group {0} can't set to : {1} - {2}".format(indexGrp, value, error)
                    value = clss.groups(indexGrp)['max_associations']
            except :
                msg = u"ERROR: You must enter number ({0})".format(value)
                result = 'error'
                value = clss.getGroup(indexGrp)['max_associations']
        elif key[:9] == 'grpNodes_':
            indexGrp = int(key[9:])
            try :
                value = value.split(',')
                result,  error = clss.SetGroupKey(indexGrp, 'nodes', [int(i) for i in value])
                if result:
                    msg = u"nodes in group {0} are changed to : {1}".format(indexGrp,  value)
                else :
                    result = 'error'
                    msg = u"nodes in group {0} can't set to : {1} - {2}".format(indexGrp, value, error)
                    value = clss.groups(indexGrp)['nodes']
            except :
                msg = u"ERROR: bad format of list of nodes ({0})".format(value)
                result = 'error'
                value = clss.getGroup(indexGrp)['nodes']
        elif key[:10] == 'endPindex_':
            id = int(key[10:])
            num = 1
#            instance = {}
            for i,  ep in  clss._node.getAllInstance().iteritems() :
                if num == id : 
                    try :
                        result,  error = clss._node.setInstanceIndex(i, int(value))
                        if result:
                            msg = u"instance {0} index is changed to : {1}".format(id,  value)
                        else :
                            result = 'error'
                            msg = u"instance {0} index can't set to : {1} - {2}".format(id, value, error)
                            value = i
                        break
                    except :
                        msg = u"ERROR: You must enter number ({0})".format(value)
                        result = 'error'
                        value = i
                        break
                num +=1
        elif key[:5] == 'endP_':
            id = int(key[5:])
            num = 1
#            instance = {}
            for i,  ep in  clss._node.getAllInstance().iteritems() :
                if num == id : 
                    try :
                        result,  error = clss._node.setInstanceEndPoint(i, int(value))
                        if result:
                            msg = u"instance {0} EndPoint is changed to : {1}".format(id,  value)
                        else :
                            result = 'error'
                            msg = u"instance {0} EndPoint can't set to : {1} - {2}".format(id, value, error)
                            if i in clss._node.mapEndPoints : value = clss._node.mapEndPoints[i].keys()[0]
                            else : value = '255'
                        break
                    except :
                        msg = u"ERROR: You must enter number ({0})".format(value)
                        result = 'error'
                        if i in clss._node.mapEndPoints : value = clss._node.mapEndPoints[i].keys()[0]
                        else : value = '255'
                        break
                num +=1
        elif key[:9] == 'clssEndP_':
            id = int(key[9:])
            num = 1
#            instance = {}
            for i,  ep in  clss._node.getAllInstance().iteritems() :
                if num == id : 
                    endP = ep[ep.keys()[0]]
                    try :
                        value = value.split(',')
                        value = [int(v, 16) for v in value]
                    except :
                        value = []
                    result,  error = clss._node.setInstanceClssEndPoint(i, ep.keys()[0], value)
                    if result:
                        msg = u"Class of instance {0} are changed to : {1}".format(id,  value)
                    else :
                        result = 'error'
                        msg = u"Class of instance {0} can't set to : {1} - {2}".format(id, value, error)
                        if i in clss._node.mapEndPoints : value = clss._node.mapEndPoints[i][endP]
                        else : value = []
                    break
                num +=1
        else :
            msg = u"Resquest not handled actually : {0}, value : {1}".format(key,  value)
            result = 'error'
        return jsonify(inputId = inputId, value=value, result=result,  msg=msg)
    return json.dumps({ "error": "Virtual Node {0} not find.".format(node_ref) }), 500 
    
@app.route('/virtualnodes/<node_ref>/<clssId>/update_extra_params')
def virtualnode_cmdClss_update_extra_params(node_ref, clssId):
    extraP = json.loads(request.args.get('extraP'))
    instance = request.args.get('instance', 0, type=int)
    print " update_extra_params clss :", clssId, instance, extraP
    manager =  Manager()
    homeId = node_ref.split(".")[0]
    nodeId = int(node_ref.split(".")[1])
    node = manager.getNode(homeId, nodeId)
    if node is not None:
        clss = node.getCmdClass(int(clssId))
        if clss.setInstanceExtraParams(instance, extraP) :
            result = 'success'
            msg = u"Extra parameters {0} instance {1} are changed to : {2}".format(clss.GetCommandClassName, instance,  extraP)
        else :
            msg = u"Extra parameters {0} instance {1} can't set to : {2}".format(clss.GetCommandClassName, instance, extraP)
            result = 'error'
        return jsonify(result=result,  msg=msg)
    return json.dumps({ "error": "Virtual Node {0} not find.".format(node_ref) }), 500 


function renderCmdClssNode(data, type, full, meta) {
    try {
        var exData = JSON.parse(data);
        }
    catch (err) {
        console.log(err);
        return 'No Data'
        };
    var num = meta.row;
    if (meta.row < 10) { num = "0" + num; };
    var vId = exData["vid"]
    var stR = "inactive";
    var stW = "inactive";
    if (exData["readOnly"] == "True") {stR = "active"};
    if (exData["writeOnly"] == "True") {stW = "active"};                    
    var rw = '<span id="vread'+vId +'" class="label label-info status-label status-without icon16-status-'+stR+'">R</span>' + 
                '<span id="vwrite'+vId +'" class="label label-info status-label status-without icon16-status-'+stW+'" font-size=65%>W</span>';
    var help = '';
    if (exData.hasOwnProperty('help')) { help = exData['help']};
    var canPolled = false, polled = false;
    if (exData.hasOwnProperty('canpolled')) {
        canPolled = exData['canpolled'] ==  'True';
        polled = exData['polled'] ==  'True';
        };
    var extraP = '';
    if (canPolled) {
        var poll = "";
        var tpoll = "Check to poll this value";
        if (polled) {
            poll = " checked='checked'";
            tpoll = "Value is polled with intensity : " + exData['pollintensity'];
        }
        extraP = '&nbsp<input type="checkbox" class="checkbox" id="vpoll' + vId + '"' + poll + ' name="isPolled"'+'title="'+ tpoll + '" />';
    };
    var extraH ='';
    if (help !="") {
        extraH = '<span id="hn'+vId+'" class="label label-info status-label status-without icon16-status-info" title="' + help + '">&nbsp&nbsp;</span>';
    };

    return  rw+ extraH + extraP ;
};

function renderInputText(idInput, label, value, col, colLabel, colInput) {
    var inputRender = '<div class="'+col+'">' +
                                '<form method="POST" action="" class="form-inline">' +
                                   '<div class="form-group">' +
                                        '<label class="'+colLabel+' control-label vert-align" for="'+idInput+'">'+label+'</label>' +
                                        '<div class="'+colInput+'">' +
                                            '<div class="input-group">' +
                                               '<input type="text" name="'+idInput+'" id="'+idInput+'" class="form-control" value="'+value+'">'+
                                               '<span class="input-group-addon input-addon-xs"><a id="st-'+idInput+'" href="#" class="btn btn-xs btn-info">' +
                                                    '<span id="stic-'+idInput+'" class="glyphicon glyphicon-floppy-saved"></span></a></span>' +
                                            '</div>' +
                                        '</div>' +
                                    '</div>' +
                                '</form>' +
                            '</div>'
    return inputRender;
};

function handleChangeCmdClssPolled(source) {
    console.log("start request update config");
    var start = source.baseURI.search('virtualnodes/')+13;
    var end = source.baseURI.search('/config');
    var refNode = source.baseURI.substring(start, end);
    start = source.id.search('_P-')+3;
    var idPoll = parseInt(source.id.substring(start, source.id.length));
    $.getJSON('/virtualnodes/'+refNode+'/update_config_poll', {
          inputId: source.id,
          key: source.id,
          idPoll: idPoll,
          clssId: $("[id^='clss_P-"+idPoll+"']").val(),
          instance: $("[id^='instance_P-"+idPoll+"']").val(),
          label: $("[id^='clss_lab_P-"+idPoll+"']").val(),
          value: ""
        }, function(data, result) {
            console.log("Retour de modif :" + JSON.stringify(data));
            if (data.result == 'error') {
                new PNotify({
                        type: 'error',
                        title: 'Invalid input',
                        text: data.msg,
                        delay: 6000
                });
            };
            if ($('#stic-'+data.inputId).length){ 
                $('#st-'+data.inputId).removeClass('btn-info btn-warning').addClass('btn-success');
                $('#stic-'+data.inputId).removeClass('glyphicon-refresh glyphicon-floppy-saved glyphicon-remove').addClass('glyphicon-ok');
            };
            if (data.inputId.search('clss_P-') == 0) {
                if (!$('#clss_lab_P-'+idPoll).length){  // Select list doesn't exist create it.
                    var a = document.createElement('select');
                    var p = document.getElementById('form_P-'+idPoll);
                    var b = document.getElementById('st_P-'+idPoll);
                    a.id = 'clss_lab_P-'+idPoll;
                    a.className ="form-control";
                    a.innerHTML = '<option value="">No selection</option>';
                    var s = document.createElement('span');
                    s.className ="input-addon-xs";
                    s.innerHTML ='<a id="st-clss_lab_P-'+idPoll+'" href="#" class="btn btn-xs btn-warning"><span id="stic-clss_lab_P-'+idPoll+'" class="glyphicon glyphicon-remove"></span></a>';
                    p.insertBefore(a, b);
                    p.insertBefore(s, b);
                    $(a).change(function() {
                        handleChangeCmdClssPolled(this);
                    });
                };
                $("#clss_lab_P-"+idPoll+" option:gt(0)").remove(); // remove all options, but not the first
                for (var v in data.data) {
                    $("#clss_lab_P-"+idPoll).append($("<option></option>").attr("value", data.data[v]['label']).text(data.data[v]['index'] +" - " + data.data[v]['label']+"  ("+ data.data[v]['units']+")"));
                };
                $('#st-clss_lab_P-'+idPoll).removeClass('btn-info btn-success ').addClass('btn-warning');
                $('#stic-clss_lab_P-'+idPoll).removeClass('glyphicon-refresh glyphicon-floppy-saved glyphicon-ok').addClass('glyphicon-remove');
            };
        });
    };

function renderMinMaxForm(idForm, typeVal, max, min){
    var render = '<div class="form-group" id="'+ idForm +'">' +
                        '<div class="col-md-3">' +
                            '<form method="POST" action="" class="form-inline">' +
                               '<div class="input-group">' +
                                    '<label class="control-label vert-align" for="max">Maximun</label>' +
                                    '<input type="text" name="max" id="max" class="form-control" value="'+max+'">'+
                                '</div>' +
                                '<div class="input-group">' +
                                    '<label class="control-label vert-align" for="min">Minimum</label>' +
                                    '<input type="text" name="min" id="min" class="form-control" value="'+min+'">'+
                                '</div>' +
                            '</form>' +
                        '</div>'
                    '</div>'
    return render;
    };

function renderSerieForm(idForm, typeVal, serie, values){
    var render =  '<div class="form-group" id="'+ idForm +'">' +
                            '<form method="POST" action="" class="form-inline">' +
                            '<table class="table table-condensed">' +
                               '<caption>Serie of values</caption>'+
                               '<a id="add_val_serie" class="btn btn-info" href="#"><span class="glyphicon glyphicon-plus" aria-hidden="false"></span> Add a value in serie</a>' +
                               '<thead>' +
                                  '<tr>' +
                                     '<th>Id</th>' +
                                     '<th>Value</th>' +
                                     '<th></th>' +
                                  '</tr>' +
                               '</thead>' +
                               '<tbody>'
    for  (var i=1; i <= serie.length; i++) {
        render += '<tr><td>' + i + '</td><td>'
        var vs = serie[i-1];
        switch (typeVal) {
            case "Bool" : // Boolean, true or false
                render += '<input type="checkbox" id="v-'+i+'" value="'+vs+'">'
                break;
            case "List" : // List from which one item can be selected
                render += '<select class="form-control" id="v-'+i+'">' +
                                    '<option value="">No selection</option>'
                for (var v=0; v < values.length; v++) {
                    render += '<option value="'+ values[v].value +'"'
                    if (vs == values[v].value) {
                        render += 'selected="true"'
                    };
                    render += '>' + values[v].value +' - ' +values[v].label + '</option>'
                };
                render += '</select>'
                break;
            case  "Schedule":  // Complex type used with the Climate Control Schedule command class
            case "Byte":         //  8-bit unsigned value
            case "Decimal":    //  Represents a non-integer value as a string, to avoid floating point accuracy issues.
            case "Int":          // 32-bit signed value
            case "Short":       // 16-bit signed value
            case "String" :     // Text string
                render += '<input type="text" name="value" id="v-'+i+'" class="form-control" value="'+vs+'">'
                break;
//    Button = 8                # A write-only value that is the equivalent of pressing a button to send a command to a device
//    Raw = 9                   # Used as a list of Bytes
            default :
                render += 'Value type unrecognized'
        };
        render += '</td><td>' +
                        '<a name="del_value" valId="'+i+'" class="btn btn-default pull-right" data-placement="bottom" data-href="#}">' +
                            '<span class="glyphicon glyphicon-trash" aria-hidden="true"></span> Delete value</a>'
        render += '</td></tr>'
    };
    render += '</tbody></table></form></div>'
    return render;
};
    
function parseValuesFromType(valueType, values) {
    valRet = []
    switch (valueType) {
        case "Bool" :  // Boolean, true or false
            for (var i= 0; i < values.length; i++) {
                if (values[i] == 0 || values[i] == "false" || values[i] == false) { valRet.push(false);
                } else {valRet.push(true);};
            };
            break;
        case "Button" : // A write-only value that is the equivalent of pressing a button to send a command to a device
            for (var i= 0; i < values.length; i++) { valRet.push(1);};
            break;
        case "Byte": // 8-bit unsigned value
        case "Int": // 32-bit signed value
        case "Short": // 16-bit signed value
        case "Raw":  // Used as a list of Bytes
        case "List" : // List from which one item can be selected
            for (var i= 0; i < values.length; i++) { valRet.push(parseInt(values[i]));};
            break;
        case "String" : // Text string
            for (var i= 0; i < values.length; i++) { valRet.push(values[i]);};
            break;
        case "Decimal": // Represents a non-integer value as a string, to avoid floating point accuracy issues.
            for (var i= 0; i < values.length; i++) { valRet.push(parseFloat(values[i]));};
            break;
        case "Schedule": // Complex type used with the Climate Control Schedule command class
            for (var i= 0; i < values.length; i++) {
                valRet.push({"real": parseFloat(values[i][0]), "imag":parseFloat(values[i][0])});
            };
            break;
        default : valRet = values;
        };
        return valRet;
};

function getAttrInherit(obj, _attrib) {
    var find = false;
    var o = obj;
    var result = null;
    while ( !find) {
        if (o.hasAttribute(_attrib)) {
            result =  $(o).attr(_attrib);
            find = true;
        } else {
            o = $(o).parent()[0];
            if (o.parentNode == null) {find =true;};
        };
    };
   return result;         
};

function updateConfigPoll(refNode, idPoll, inputId, key, value, params) {
    $.getJSON('/virtualnodes/'+refNode+'/update_config_poll', {
        inputId: inputId,
        key: key,
        idPoll: idPoll,
        value: value,
        params: typeof params !== undefined ? params : ""
    }, function(data, result) {
        console.log("Retour de modif :" + JSON.stringify(data));
        if (data.result == 'error') {
            new PNotify({
                    type: 'error',
                    title: 'Invalid input',
                    text: data.msg,
                    delay: 6000
            });
        };
        $('#'+data.inputId).val(data.value);
        if ($('#st-'+data.inputId).length){  
            $('#st-'+data.inputId).removeClass('btn-info').addClass('btn-success');
            $('#stic-'+data.inputId).removeClass('glyphicon-refresh glyphicon-floppy-saved').addClass('glyphicon-ok');
        };
    });
};

// attach the .equals method to Array's prototype to call it on any array
Array.prototype.equals = function (array) {
    // if the other array is a falsy value, return
    if (!array)
        return false;

    // compare lengths - can save a lot of time 
    if (this.length != array.length)
        return false;

    for (var i = 0, l=this.length; i < l; i++) {
        // Check if we have nested arrays
        if (this[i] instanceof Array && array[i] instanceof Array) {
            // recurse into the nested arrays
            if (!this[i].equals(array[i]))
                return false;       
        }           
        else if (this[i] != array[i]) { 
            // Warning - two different object instances will never be equal: {x:20} != {x:20}
            return false;   
        }           
    }       
    return true;
}   

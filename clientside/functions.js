
const base_uri = 'http://192.168.88.65/api/v02/'
const scopes_uri = 'scopes'
const state_uri = 'state/'
const shift_uri = 'shift/'
const structure_uri = 'structure/'
const shortcut_uri = 'state/shortcut'
const groups_uri = 'structure/groups'
var groups = [], tags = []


const states = {
      'OFF': 0,
      'ON': 1
    }
const counter_states = {
      1: 'OFF',
      0: 'ON'
    }
const colors ={
      1: "btn btn-success",
      0: "btn"
    }

function getScopes() {
const uri = base_uri+state_uri+scopes_uri;
var scopes = [];




}


function getState(entity) {
 const uri = base_uri+state_uri;
 const url = uri+entity;
 var items = [];

$.getJSON(url, function(data){
  $.each( data.response, function (key, val)
    {
      items.push({key,val})
    });
});
return items;
}

function getShortcuts() {
  const uri = base_uri+shortcut_uri
  var switches = []
  var sensors = []
  $('.span4').button()
  sensors.push( '<table class="table table-bordered table-condensed"><tr><td><b>Sensor</b></td><td><b>State</b></td></tr>' )
  $.getJSON(uri, function(data) {
    for (var i = 0; i < data.response.length; i++) {
      const type = data.response[i].type, state = data.response[i].state, name = data.response[i].name, uid = data.response[i].uid
      if (type == 'switch'){
        switches.push( "<p>" + name + ' ' + '<button class="' + colors[states[state]]+ '" res-uid=' + uid + '>' + counter_states[states[state]] + '</button></p>' );
      }
      if (type == 'sensor'){
        var st = state.replace('hum', 'humidity')
        sensors.push( '<tr><td>'+name+'</td><td>'+st+'</td></tr>' );
      }
    }
    sensors.push( '</table>' )
    $( "<ul/>", {
      "class": "my-new-list",
      "id": 'hui',
      html: switches.join( "" )
    }).appendTo( ".span4" );
    $( "<ul/>", {
      "class": "my-new-list",
      "id": 'hui1',
      html: sensors.join( "" )
    }).appendTo( ".span8" );
});
shiftSwitch();
}

function getSwitches() {
  const uri = base_uri+groups_uri

  $.getJSON(uri, function(data){
    var items = []
    $.each(data.response, function( key, val ) {
      if (val[0].type == 'switch') {
      items.push( "<li>" + key + ": </li>" )};
      $.each(val, function( k, v ) {
        if (v.type == "switch") {
            items.push( "<p>" + v.name + ' ' + '<button class="' + colors[states[v.state]]+ '" res-uid=' + v.uid + '>' + counter_states[states[v.state]] + '</button></p>' );
                                        };
        })        
    });
  $( "<ul/>", {
      "class": "my-new-list",
      "id": 'hui',
      html: items.join( "" )
    }).appendTo( "body" );
});
shiftSwitch();
}

function shiftSwitch(){

$("body").on('click','button', function() {
    const resuid = $(this).attr('res-uid')
    const api = base_uri+shift_uri;
    const command = '/toggle';
    var resp = [];
    $.post(api+resuid+command, function(data){
      var resp = jQuery.parseJSON(data);
      $.each(resp.response, function(k, v){
        var newstate = viceversa(v);
        $("button[res-uid='"+resuid+"']").text(newstate);
        //$("button[res-uid='"+resuid+"']").button('toggle')
        $("button[res-uid='"+resuid+"']").addClass(colors[Math.abs(states[newstate]-1)]).removeClass(colors[(states[newstate])])
      })
      })

  });

}

function getThermo() {
  const thermo_uri = base_uri+state_uri+'thermostat';
  const temp_uri = base_uri+state_uri;
  const prem_uri = base_uri+structure_uri+'premises';
  const api = base_uri+shift_uri;
  var match = []

  $.getJSON(prem_uri, function(data){
    $.each(data.response, function( key, val ){
      const t = val.thermostat, a = val.ambient
        if (t!=null && a!=null) {
          var dict = {'thermo':t, 'ambient': a};
        match.push(dict);
        } 
      
    });
})
  .always(function(){
    $.each(match, function( key, val ){
      url = temp_uri+val.ambient;
      $.getJSON(url, function(data){
        resp = data.response[0].state;
        temp = resp.substring(resp.indexOf('temp:')+5);
        cell_id = data.response[0].uid;
        cell = document.getElementById(cell_id);
        cell.innerHTML = temp;
      });
    });
});



  $.getJSON(thermo_uri, function(data){
    var items = [];
    $.each(data.response, function( key, val ){
      var prem = val.premise
      var state = '<img src="/client/img/thermostat.png" class="img-rounded"><span id=c-'+val.uid+'> '+val.state+'</span>';
      var range = '<input name="'+val.name+'"id="'+val.uid+'" type="range" min="0" max="30" value="'+val.state+'" step="0.5" />'
      var temp_id = null
      //right = right.substring(right.indexOf('temp:')+5);
      $.each(match, function (k,v){
        if (v.thermo == val.uid) {
          temp_id = '<img src="/client/img/thermometer.png" class="img-rounded"><span id='+v.ambient+'></span>';
        };  
      });
      items.push({prem, temp_id, range, state});
    });
    var target = document.getElementById('zopa');
    res = tablemaker(items);
    target.appendChild(res)
});



  $("#zopa").on('input','input',function () {
    const resuid = $(this).attr('id');
    const name = $(this).attr('name');
    const caption = 'c-'+resuid;
    document.getElementById(caption).innerHTML = ' '+this.value;
  });

   $("#zopa").on('change','input',function () {
    const resuid = $(this).attr('id');
    const name = $(this).attr('name');
    const caption = 'c-'+resuid;   
    document.getElementById(caption).innerHTML = ' '+this.value;
    $.post(api+resuid+'/'+this.value);
  });

}

function StateView() {
 var self = this;
 self.apiuri = base_uri+'statusall';
 self.statuses = ko.observableArray();
 
$.getJSON(self.apiuri, function(data) {
    for (var i = 0; i < data.response.length; i++) {
        self.statuses.push({
            uid: ko.observable(data.response[i].uid),
            premise: ko.observable(data.response[i].premise),
            ip: ko.observable(data.response[i].ip)
        });
    }
});
 
 }

 function getQuarantine() {
  const uri = base_uri+structure_uri+'quarantine';

  $.getJSON(uri, function(data){
    var items = []
    items.push( '<div id="quarantine" class="container"><h4>Newbies or quarantined devices</h4><table class="table table-striped">' )
    items.push( '<tr><td><b>UID</b></td><td><b>Options</b></td></tr>' )
    for (var i = 0; i < data.response.length; i++) {
      items.push( '<tr><td>'+data.response[i].uid+'</td><td>'+data.response[i].ip+'</td></tr>');     
    };
    items.push( '</table></div>' )
  $( "<ul/>", {
      "class": "my-new-list",
      "id": 'huivrul',
      html: items.join( "" )
    }).appendTo( "body" );
});
}

function tablemaker(array) {
  var table = document.createElement('table');
  table.setAttribute('class', "table table-condensed table-stripped");
  $.each(array, function (key,val) {
    var tr = document.createElement('tr');
      $.each(val, function (k,v) {
      var td = document.createElement('td');
      td.innerHTML = v;
      tr.appendChild(td);
      });
    table.appendChild(tr);
  });
return table;
}

function viceversa(state) {
      const counter_states = {
        'OFF': 'ON',
        'ON': 'OFF'
      }
      return counter_states[state]
}
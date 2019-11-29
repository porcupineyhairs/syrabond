
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

function getState(entity) {
 const uri = 'http://127.0.0.1:5001/api/v02/state/';
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
  const uri = 'http://127.0.0.1:5001/api/v02/structure/tag/shortcut'
  var switches = []
  var sensors = []
  $('.span4').button()
  sensors.push( '<table class="table table-bordered table-condensed"><tr><td><b>Sensor</b></td><td><b>State</b></td></tr>' )
  $.getJSON(uri, function(data) {
    for (var i = 0; i < data.response.length; i++) {
      const type = data.response[i].type, state = data.response[i].state, name = data.response[i].name, uid = data.response[i].uid
      if (type == 'switch'){
        switches.push( "<p>" + name + ' ' + '<button class="btn" data-toggle="button" res-uid=' + uid + '>' + counter_states[states[state]] + '</button></p>' );
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

}


function getSwitches() {
  const uri = 'http://127.0.0.1:5001/api/v02/structure/groups'

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

}

function getThermo() {
  const thermo_uri = 'http://127.0.0.1:5001/api/v02/structure/thermo';
  const temp_uri = 'http://127.0.0.1:5001/api/v02/state/temp';

  $.getJSON(thermo_uri, function(data){
    var items = [];
    $.each(data.response, function( key, val ) {
      items.push( '<p id=c-'+val.thermostat_id+'>'+val.name+': '+val.thermostat_state+'</p>' );
      items.push( '<input name="'+val.name+'"id="'+val.thermostat_id+'" type="range" min="0" max="30" value="'+val.thermostat_state+'" step="0.5" />');        
    });
  $( "<ul/>", {
      "class": "my-new-list",
      "id": 'hui',
      html: items.join( "" )
    }).appendTo( ".span4" );
});

  $.getJSON(temp_uri, function(data){
    var items = [];
    $.each(data.response, function( key, val ){
      var left = val.name, right = val.state;
      items.push({left, right});
    });
    var res = maketable(items);
  $( "<ul/>", {
      "class": "my-new-list",
      "id": 'hui',
      html: res.join( "" )
    }).appendTo( ".span8" );
});

}

function StateView() {
 var self = this;
 self.apiuri = 'http://127.0.0.1:5001/api/v02/statusall';
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
  const uri = 'http://127.0.0.1:5001/api/v02/structure/quarantine';

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

function maketable(array){
  var items = [];
  items.push( '<table class="table table-bordered table-condensed"><tr><td><b>Sensor</b></td><td><b>State</b></td></tr>' );
  $.each(array, function (key,val){
    console.log(val)
    items.push('<tr><td>'+val.left+'</td><td>'+val.right+'</td></tr>')

  });
  items.push('</table>');
return items;
}

function viceversa(state) {
      const counter_states = {
        'OFF': 'ON',
        'ON': 'OFF'
      }
      return counter_states[state]
}
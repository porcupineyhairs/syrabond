
const base_uri = 'http://192.168.88.65/api/v02/'
const scopes_uri = 'scopes'
const state_uri = 'state/'
const shift_uri = 'shift/'
const structure_uri = 'structure/'
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

const channels_hrf = {
  'hum': '<img src="/client/img/humidity.png" class="img-rounded">',
  'temp': '<img src="/client/img/thermometer.png" class="img-rounded">'
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


function getStruct(type) {
  const uri = base_uri+structure_uri+type;
  var items = [];
  $.getJSON(uri, function(data){
    $.each(data.response, function ( key, val){
      for (var i = val.length - 1; i >= 0; i--) {
        const group_name = val[i];
            items.push( '<label class="checkbox inline">');
            items.push( '<input type="checkbox" value="'+group_name+'">'+group_name+'</label>');
      }
    items.push('<br>');      
    })
  })
  .always(function(){
    document.getElementById('scopes').innerHTML = items.join("");
  });
}


function getScope(scope) {
  const uri = base_uri+state_uri+scope
  var switches = []
  var sensors = []
  var thermos = []
  $.getJSON(uri, function(data) {
    for (var i = 0; i < data.response.length; i++) {
      const type = data.response[i].type, state = data.response[i].state, name = data.response[i].name, uid = data.response[i].uid
      if (type == 'switch'){
        const name_cell = "<span>"+name+"</span>"
        const button_cell = '<button class="' + colors[states[state]]+ '" res-uid=' + uid + '>' + counter_states[states[state]] + '</button>'
        switches.push({name_cell, button_cell})
      }
      if (type == 'sensor'){
        var state_cell = []
        premise = data.response[i].premise
        $.each(state, function(channel, st){
          console.log(channels_hrf[channel], st);
          state_cell.push('<p>'+channels_hrf[channel]+st+'</p>');
        });
      const st = state_cell.join(' ')
      sensors.push({premise, st});
      }
      if (type == 'thermo'){
        premise = data.response[i].premise
        const st = '<img src="/client/img/thermostat.png" class="img-rounded"><span id=c-'+uid+'> '+state+'</span>';
        const range = '<input name="'+name+'"id="'+uid+'" type="range" opacity="0.5" min="0" max="30" value="'+state+'" step="0.5" />'
      thermos.push({premise, range, st});
      }
    }

})
  .always(function(){
    console.log(switches)
    if (switches.length > 0) {
    res = tablemaker(switches);
    res.id = 'table-sw-'+scope
    $(".span4").append(res);
    }

    if (sensors.length > 0){
    res = tablemaker(sensors);
    res.id = 'table-sens-'+scope
    $(".span7").append(res);
    }

    if (thermos.length > 0){
    res = tablemaker(thermos);
    res.id = 'table-ther-'+scope
    $(".span7").append(res);
    }

  });

}


function getScopesList(){

   $("#scopes").on('change','input',function () {
    const scope = this.value;
    const checked = this.checked;
    console.log(scope, checked);
    if (checked == true) {
      getScope(scope);
    } else {
      if ($("#table-sw-"+scope).length > 0){
        $("#table-sw-"+scope).remove()
      };
      if ($("#table-sens-"+scope).length > 0){
        $("#table-sens-"+scope).remove()
      };
      if ($("#table-ther-"+scope).length > 0){
        $("#table-ther-"+scope).remove()
      };
    };
  });

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

function shiftThermo(id){
  const api = base_uri+shift_uri;
  $("#"+id).on('input','input',function () {
    const resuid = $(this).attr('id');
    const name = $(this).attr('name');
    const caption = 'c-'+resuid;
    document.getElementById(caption).innerHTML = ' '+this.value;
  });

   $("#"+id).on('change','input',function () {
    const resuid = $(this).attr('id');
    const name = $(this).attr('name');
    const caption = 'c-'+resuid;   
    document.getElementById(caption).innerHTML = ' '+this.value;
    $.post(api+resuid+'/'+this.value);
  });

}

function getThermo() {
  const thermo_uri = base_uri+state_uri+'thermostat';
  const temp_uri = base_uri+state_uri;
  const prem_uri = base_uri+structure_uri+'premises';
  
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
        temp = resp.temp;
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
      var range = '<input name="'+val.name+'"id="'+val.uid+'" type="range" opacity="0.5" min="0" max="30" value="'+val.state+'" step="0.5" />'
      var temp_id = null
      $.each(match, function (k,v){
        if (v.thermo == val.uid) {
          temp_id = '<img src="/client/img/thermometer.png" class="img-rounded"><span id='+v.ambient+'></span>';
        };  
      });
      items.push({prem, temp_id, range, state});
    });
    var target = document.getElementById('thermostat');
    res = tablemaker(items);
    target.appendChild(res);
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
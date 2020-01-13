
//const base_uri = 'http://192.168.88.12/api/v02/'
const base_uri = 'http://192.168.88.65/api/v02/'
const get_uri = 'get/'
const set_uri = 'set/'
const add_uri = 'add/'
const edit_uri = 'edit/'
const del_uri = 'delete/'
const scopes_uri = 'scopes'
const state_uri = 'state/'
const shift_uri = 'shift/'
const structure_uri = 'structure/'
const entro_uri = 'entro'
const scens_uri = 'scenarios/'
const session_uri = 'session/'
var groups = [], tags = [], page_resources = [];
var entropy
var lang = navigator.language || navigator.userLanguage;
var is_mobile = false;
if( /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ) {
 is_mobile = true;
}

const states = {
      'OFF': 0,
      'ON': 1
    }
const counter_states = {
      1: 'OFF',
      0: 'ON'
    }
const colors ={
      1: "btn-success",
      0: "btn-info"
    }

const channels_hrf = {
  'hum': '<img src="/client/img/humidity.png" class="img-rounded">',
  'temp': '<img src="/client/img/thermometer.png" class="img-rounded">'
}

const custom_translator = {
  "ru-RU":
  {
    "prem": "Помещения",
    "shortcut": "Быстрый доступ",
    "heating": "Отопление",
    "groups": "Группы устройств",
    "maint": "Служебное",
    "scenaries": "Сценарии",
    "add": "Добавить устройство",
    "new_dev_name_placeholder": "Описание...",
    "add_tag": "Новый тэг...",
    "del": "Удалить",
    "save": "Сохранить",
    0: "Пн",
    1: "Вт",
    2: "Ср",
    3: "Чт",
    4: "Пт",
    5: "Сб",
    6: "Вс"
  },
  "en-US":
  {
    "prem": "Premises",
    "shortcut": "Shortcut view",
    "heating": "Heating",
    "groups": "Groups",
    "maint": "Maintenance",
    "scenaries": "Scenaries",
    "add": "Add device",
    "new_dev_name_placeholder": "Device caption",
    "add_tag": "Add tag...",
    "del": "Delete",
    "save": "Save",
    0: "Mon",
    1: "Tue",
    2: "Wed",
    3: "Thu",
    4: "Fri",
    5: "Sat",
    6: "Sun"
  }

}
if (custom_translator[lang] == null) {
    lang = 'en-US'
  }




function getState(entities) {
const uri = base_uri+get_uri+state_uri;
//const url = uri+entity;
var items = [];
prom = $.ajax({
          url:uri,
          type:"PUT",
          data:JSON.stringify(entities),
          contentType:"application/json; charset=utf-8",
          dataType:"json"
        });
return prom;
}

function getStruct(type) {
  const uri = base_uri+get_uri+structure_uri+type;
  var items = [];
  $.getJSON(uri)
  .always(function(data){
    $.each(data.response, function ( key, val){
      if (type == 'scopes'){
      items.push('<label>'+key+' </label>')
      for (var i = val.length - 1; i >= 0; i--) {
        const scope_name = val[i];
        addCheckbox('scopes', 's'+i.toString(), scope_name, scope_name, false);
      }}
      if (type == 'premises'){
      items.push('<label>'+key+' </label>')
      for (var i = val.length - 1; i >= 0; i--) {
        const prem_name = val[i].name;
        const prem_index = val[i].index
        addCheckbox('scopes', 's'+i.toString(), prem_index, prem_name, false);
            items.push( '<label class="checkbox inline">');
            items.push( '<input type="checkbox" value="'+prem_index+'">'+prem_name+'</label>');
      }}
      if (type == 'types'){
        items.push(val);
      }
    //items.push('<br>');
    })
  });
}



function getS(type) {
  const uri = base_uri+get_uri+structure_uri+type;
  var items = [];

  prom = $.getJSON(uri, function(data){
    $.each(data.response, function ( key, val){
      if (type == 'scopes'){
      var list = []
      for (var i = val.length - 1; i >= 0; i--) {
        const scope_name = val[i];
            list.push(scope_name);
      }
    items.push({key, list});
    }

      if (type == 'premises'){
      items.push('<label>'+key+' </label>')
      for (var i = val.length - 1; i >= 0; i--) {
        const prem_name = val[i].name;
        const prem_index = val[i].index
            items.push( '<label class="checkbox inline">');
            items.push( '<input type="checkbox" value="'+prem_index+'">'+prem_name+'</label>');
      }}
      if (type == 'types'){
        items.push(val);
      }
      if (type.indexOf('#') == 0){
        items.push(val);
      }
    //items.push('<br>');
    })
  })
  return prom;
}

function getScope(scope) {
  const uri = base_uri+get_uri+state_uri+scope
  var switches = []
  var sensors = []
  var thermos = []
  $.ajax({
    url: base_uri+session_uri+'scopes',
    type: "POST",
    data: JSON.stringify({scope}),
    contentType: "application/json; charset=utf-8",
    dataType: "json"
  });
  $.getJSON(uri, function(data) {
    console.log(data.response);
    var items = data.response.sort(sortItems);
    console.log(items);
    for (var i = 0; i < data.response.length; i++) {
      const type = data.response[i].type, state = data.response[i].state, name = data.response[i].name, uid = data.response[i].uid
      if (type == 'switch'){
        const name_cell = "<span>"+name+"</span>"
        const button_cell = '<button class="btn btn-block res-button ' + colors[states[state]]+ '" res-uid=' + uid + ' cmd='+ counter_states[states[state]] +'>' + counter_states[states[state]] + '</button>'
        switches.push({name_cell, button_cell})
        page_resources.push(uid);
      }
      if (type == 'sensor'){
        var state_cell = [];
        var premise = data.response[i].premise;
        if (premise == 'nowhere') {
          premise = data.response[i].name;
        }
        $.each(state, function(channel, st){
          state_cell.push('<p res-uid="'+uid+'-'+channel+'">'+channels_hrf[channel]+st+'</p>');
        });
      const st = state_cell.join(' ')
      sensors.push({premise, st});
      page_resources.push(uid);
      }
      if (type == 'thermo'){
        premise = data.response[i].premise
        if (is_mobile) {
          var st = '<span id=c-'+uid+' res-uid="'+uid+'"> '+state+'</span>';
          var minus_button = '<button type="button" id="min-'+uid+'" class="btn btn-primary btn-sm"> < </button>';
          var plus_button = '<button type="button" id="pls-'+uid+'" class="btn btn-danger btn-sm"> > </button>';
          thermos.push({premise, minus_button, st, plus_button});
        }
        else {
          const st = '<img src="/client/img/thermostat.png" class="img-rounded"><span id=c-'+uid+' res-uid="'+uid+'"> '+state+'</span>';
          const range = '<input class="custom-range" name="'+name+'"id="'+uid+'" type="range" opacity="0.5" min="0" max="30" value="'+state+'" step="0.5" />';
          thermos.push({premise, range, st});
        }
      page_resources.push(uid);
      }
    }

})
  .always(function(){
    if (switches.length > 0) {
    res = tablemaker(switches);
    res.id = 'table-sw-'+scope
    scope_buttons = buildScopeButtons(scope);
    scope_buttons.id = 'table-scope-'+scope;
    $(res).addClass('hide');
    $("#span-switches").append(scope_buttons);
    $("#span-switches").append(res);
    $(res).show(200);
    }

    if (sensors.length > 0){
    res = tablemaker(sensors);
    res.id = 'table-sens-'+scope
    $(res).addClass('hide');
    $("#span-sensors").append(res);
    $(res).show(200);
    }

    if (thermos.length > 0){
    res = tablemaker(thermos);
    res.id = 'table-ther-'+scope
    $(res).addClass('hide');
    $("#span-thermos").append(res);
    $(res).show(200);
    }
  });

}

function buildScopeButtons(scope) {
  const uri = base_uri+set_uri+scope+'/';
  const button_on = '<button class="btn btn-block scope-button ' + colors[0]+ '" res-uid=' + scope + ' cmd=' + counter_states[1] + '>' + counter_states[1] + '</button>';
  const button_off = '<button class="btn btn-block scope-button ' + colors[1]+ '" res-uid=' + scope + ' cmd=' + counter_states[0] + '>' + counter_states[0] + '</button>';
  tab = tablemaker([{button_on, button_off}]);
  return tab;
}

function getScopesList(){

   $("#scopes").on('change','input',function () {
    const scope = this.value;
    const checked = this.checked;
    if (checked == true) {
      getScope(scope);
    } else {

      var x = document.getElementById("table-sw-"+scope);
      if (x != null){
        x.remove();
      };
      var x = document.getElementById("table-scope-"+scope);
      if (x != null){
        x.remove();
      };
      x = document.getElementById("table-sens-"+scope);
      if (x != null){
        x.remove();
      };
      x = document.getElementById("table-ther-"+scope);
      if (x != null){
        x.remove();
      };
      };
  });

}


function shiftSwitch(){

$("body").on('click','button', function() {
    const resuid = $(this).attr('res-uid');
    const is_res_button = $(this).hasClass('res-button');
    const api = base_uri+set_uri;
    var command = '/'+$(this).attr('cmd');
    var resp = [];
    $.get(api+resuid+command, function(data){
      if (is_res_button) {
          var resp = jQuery.parseJSON(data);
          $.each(resp.response, function(k, v){
            var newstate = viceversa(v);
            $("button[res-uid='"+resuid+"']").text(newstate);
            $("button[res-uid='"+resuid+"']").attr('cmd', newstate);
            $("button[res-uid='"+resuid+"']").addClass(colors[Math.abs(states[newstate]-1)]).removeClass(colors[(states[newstate])])
          })
        }
      if (is_res_button == false){
        updateStates();
      }
      })
  });
}

function shiftThermo(id){
  const api = base_uri+get_uri+shift_uri;
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

  $("#"+id).on('click','button',function () {
   const resuid = $(this).attr('id').split('-')[1];
   const sign = $(this).attr('id').split('-')[0];
   const caption = 'c-'+resuid;
   //var value = $('#'+caption).html().toFloat();
   if (sign == 'pls') {
     var value = parseFloat(document.getElementById(caption).innerHTML)+0.5
     document.getElementById(caption).innerHTML = value;
   }
   else {
     var value = parseFloat(document.getElementById(caption).innerHTML)-0.5
     document.getElementById(caption).innerHTML = value;
   }
   $.post(api+resuid+'/'+value);
 });

}

function getThermo() {
  const thermo_uri = base_uri+get_uri+state_uri+'thermostat';
  const temp_uri = base_uri+get_uri+state_uri;
  const prem_uri = base_uri+get_uri+structure_uri+'premises';

  var match = [];
  var items = [];

  thermo = $.getJSON(thermo_uri);
  prem = $.getJSON(prem_uri);

  prem.always(function(data){
    $.each(data.response, function( key, val ){
      for (var i = val.length - 1; i >= 0; i--) {
        const t = val[i].thermostat, a = val[i].ambient
        if (t!=null && a!=null) {
          var dict = {'thermo':t, 'ambient': a};
        match.push(dict);
        }
      }
    });

    thermo.always(function(data){
      data.response.sort(sortItems);
      $.each(data.response, function( key, val ){
        var temp_id = null;
        $.each(match, function (k,v){
          if (v.thermo == val.uid) {
            temp_id = '<img src="/client/img/thermometer.png" class="img-rounded"><span id='+v.ambient+'></span>';
          };
        });
        var prem = val.premise;
        if (is_mobile == false) {
          var state = '<img src="/client/img/thermostat.png" class="img-rounded"><span id=c-'+val.uid+'> '+val.state+'</span>';
          var range = '<input class="custom-range" name="'+val.name+'"id="'+val.uid+'" type="range" opacity="0.5" min="0" max="30" value="'+val.state+'" step="0.5" />'
          items.push({prem, temp_id, range, state});
        }
        else {
          var state = '<span id=c-'+val.uid+'> '+val.state+'</span>';
          var minus_button = '<button type="button" id="min-'+val.uid+'" class="btn btn-primary btn-sm"> < </button>';
          var plus_button = '<button type="button" id="pls-'+val.uid+'" class="btn btn-danger btn-sm"> > </button>';
          items.push({prem, temp_id, minus_button, state, plus_button});
        }
        });
    var target = document.getElementById('thermostat');
    res = tablemaker(items);
    target.appendChild(res);
    $.each(match, function( key, val ){
      url = temp_uri+val.ambient;
      $.getJSON(url, function(data){
        resp = data.response[0].state;
        temp = resp.temp;
        cell_id = data.response[0].uid;
        cell = document.getElementById(cell_id);
        cell.innerHTML = ' '+temp;
      });
    });
  })
  })
}

function StateView() {
 var self = this;
 var items = [];
 uri = base_uri+get_uri+'statusall';

$.getJSON(uri, function(data) {
    for (var i = 0; i < data.response.length; i++) {
      var uid = data.response[i].uid;
      var ip = data.response[i].ip;
      var name = data.response[i].name;
      items.push({uid, name, ip});
    }
})
.done(function(){
    var target = document.getElementById('all-devices');
    var res = tablemaker(items);
    $(target).addClass("table table-hover");
    target.appendChild(res);
});
}


 function getQuarantine() {
  const uri = base_uri+get_uri+structure_uri+'quarantine';
  const post_uri = base_uri+add_uri+'device'
  var locker = false;

  $.getJSON(uri, function(data){
    var items = []
    for (var i = 0; i < data.response.length; i++) {
      var uid = data.response[i].uid
      var ip = data.response[i].ip
      items.push({uid, ip});
    };
    var target = document.getElementById('quarantine');
    var res = tablemaker(items);
    res.setAttribute('class', "table table-hover");
    target.appendChild(res);

});

  $("#quarantine").on('click', 'tr', function() {
    var form_div = document.getElementById('new-form');
    $(form_div).html('');
    new_form = document.createElement('form');

    if (locker == false){
      this.remove();
      $(new_form).addClass('hide')
    }
    locker = true;

    new_form.name=this.firstChild.innerHTML;
    $(new_form).addClass("form-inline");
    //new_form.method='POST';

    //new_form.action=post_uri;
    caption = document.createElement('span');
    caption.innerHTML = this.firstChild.innerHTML+' ';
    new_form.appendChild(caption);
    var p = getS('types');
    p.done(function(data) {
      input=document.createElement('select');
      input.name='type';
      input.id='type-selector';
      $(input).addClass("span2");
      resp = data.response
      for (var i = resp.length - 1; i >= 0; i--) {
        let option = new Option(resp[i], resp[i]);
        input.appendChild(option)
      }
      new_form.appendChild(input);
      input=document.createElement('select');
      input.name='channels';
      input.id='sensor-channels';
      $(input).addClass('hide');
      $(input).addClass('span1');
      var p = getS('channels');
        p.always(function(data) {
          resp = data.response
          for (var i = resp.length - 1; i >= 0; i--) {
            let option = new Option(resp[i], resp[i]);
            input.appendChild(option)
          }
        })
      new_form.appendChild(input);

        var p = getS('groups');
        p.always(function(data) {
          input=document.createElement('select');
          input.name='group';
          $(input).addClass("span2");
          resp = data.response
          for (var i = resp.length - 1; i >= 0; i--) {
            let option = new Option(resp[i], resp[i]);
            input.appendChild(option)
          }
          new_form.appendChild(input);
        input=document.createElement('INPUT');
        input.type='textarea';
        input.name='hrn'
        input.placeholder=custom_translator[lang]['new_dev_name_placeholder']
        input.required="required";
        new_form.appendChild(input);
        new_form.appendChild(input);
        button=document.createElement('button');
        $(button).addClass("btn btn-small btn-primary")
        button.innerHTML=custom_translator[lang]['add']
        new_form.appendChild(button);
        form_div.appendChild(new_form);
        $(new_form).show(300);
        })
    })

  $("#new-form").on('change', 'select', function() {
    if (this.name == 'type' && this.value == 'sensor') {
        input=document.getElementById('sensor-channels');
        $(input).show(100);
    }
    if (this.name == 'type' && this.value != 'sensor') {
      input=document.getElementById('sensor-channels');
      $(input).hide(100)
    }
    });


  new_form.onsubmit = function(){
    var data = $(this).serializeArray();
    data.push({"name": "uid", "value": this.name});
        $.ajax({
          url:post_uri,
          type:"POST",
          data:JSON.stringify(data),
          contentType:"application/json; charset=utf-8",
          dataType:"json"
        });


      };
  });
}

function devManage(){
  const post_uri = base_uri+edit_uri+'device'
  const new_uri = base_uri+add_uri
  const d_uri = base_uri+del_uri+'device'
  const div_tags = 'div-tags';
  const select_group = 'select-group'
  var tag_add_locker = false
  $("#button-delete-mod").html(custom_translator[lang]['del'])
  $("#button-sub-mod").html(custom_translator[lang]['save'])
  $('#input-newtag').attr("placeholder", custom_translator[lang]['add_tag'])
  $("#all-devices").on('click', 'tr', function() {
    const uid = this.firstChild.innerHTML;
    $("#button-sub-mod").val(uid);
    $("#button-delete-mod").val(uid);
    $("#"+div_tags).html('');
    $("#"+select_group).html('');
    $.getJSON()
    $('#modal-label').html(uid);
    $('#edit-device-mod').modal();
    var p = getS(uid);
    p.always(function(data){
      resp_uid = data.response
      const _name=resp_uid.name, _floor=resp_uid.floor, _code=resp_uid.code, _group=resp_uid.group, _tags=resp_uid.tags, _premise=resp_uid.premise;
      $('#input-hrn').val(_name);
      $("<option />").attr("value", _group).text(_group).attr("selected", "selected").appendTo("#"+select_group);
      for (var i = _tags.length - 1; i >= 0; i--) {
        addCheckbox(div_tags, 't'+i.toString(), _tags[i], _tags[i], true);
      }
      var pr = getS('groups');
      pr.always(function(data){
          resp_groups = data.response
          for (var i = resp_groups.length - 1; i >= 0; i--) {
            if (resp_groups[i] != _group){
            $("<option />").attr("value", resp_groups[i]).text(resp_groups[i]).appendTo("#select-group");
            }
          }
      })
      var pro = getS('tags');
      pro.always(function(data){
          resp_tags = data.response;
          for (var i = resp_tags.length - 1; i >= 0; i--) {
            if (jQuery.inArray(resp_tags[i],_tags) == -1){
              addCheckbox(div_tags, 't'+i.toString(), resp_tags[i], resp_tags[i], false);
            }
          }
      })

    })

  });

$("#button-sub-mod").on('click',  function() {
      data = $("#device-prop").serializeArray();
      data.push({"name": "uid", "value": this.value});
      console.log(data);
      $.ajax({
          url:post_uri,
          type:"POST",
          data:JSON.stringify(data),
          contentType:"application/json; charset=utf-8",
          dataType:"json"
        });
      $("#all-devices").html('');
      StateView();
    });

$("#button-delete-mod").on('click',  function() {
      data = []
      data.push({"name": "uid", "value": this.value});
      console.log(data);
      $.ajax({
          url:d_uri,
          type:"POST",
          data:JSON.stringify(data),
          contentType:"application/json; charset=utf-8",
          dataType:"json"
        });
      $("#all-devices").html('');
      StateView();
    });

$("#input-newtag").on('focusout', function () {
  if (tag_add_locker == false && this.value != '') {
      tag_add_locker = true;
      addCheckbox(div_tags, 'somerand', this.value, this.value, true);
      $(this).hide();
    }});
$("#input-newtag").on('keypress',function(e) {
    if (e.which == 13 && tag_add_locker == false && this.value != '') {
      tag_add_locker = true;
      addCheckbox(div_tags, this.value, this.value, true);
      $(this).hide();
    }
});
}

function updateState(res) {
console.log(res)
  if (page_resources.length > 0){
    if ($.inArray(res, page_resources) != -1){
      var actual_state = getState([res])
      actual_state.always(function(data){
        obj = data.response[0]
      if (obj.type == 'switch'){
        var new_state = obj.state;
        var uid = obj.uid;
        var state = viceversa($("[res-uid='"+uid+"']").html());
        if (state != new_state){
          new_state = viceversa(new_state);
          $("button[res-uid='"+uid+"']").text(new_state);
          //$("button[res-uid='"+resuid+"']").button('toggle')
          $("button[res-uid='"+uid+"']").addClass(colors[Math.abs(states[new_state]-1)]).removeClass(colors[(states[new_state])])
        }
      }
    })
    }
  }

}

function updateStates() {
  console.log('update')
  if (page_resources.length > 0){
    var actual_states = getState(page_resources);
    actual_states.always(function(data){
      for (var i = data.response.length - 1; i >= 0; i--) {
          var new_state = data.response[i].state;
          var uid = data.response[i].uid;
          var type = data.response[i].type;
        if (type == 'switch'){
          var state = viceversa($("[res-uid='"+uid+"']").html());
          if (state != new_state){
            new_state = viceversa(new_state);
            $("button[res-uid='"+uid+"']").text(new_state);
            //$("button[res-uid='"+resuid+"']").button('toggle')
            $("button[res-uid='"+uid+"']").addClass(colors[Math.abs(states[new_state]-1)]).removeClass(colors[(states[new_state])])
          }
        }
        if (type == 'thermo'){
          var res = "span[res-uid='"+uid+"']";
          if ($(res).html() !== new_state.toString()){
            var inp = document.getElementById(uid);
            inp.value = new_state;
            $(res).html(' '+new_state);

            }
          const st = '<img src="/client/img/thermostat.png" class="img-rounded"><span id=c-'+uid+' res-uid="'+uid+'"> '+state+'</span>';
        const range = '<input name="'+name+'"id="'+uid+'" type="range" opacity="0.5" min="0" max="30" value="'+state+'" step="0.5" />';
        }

        if (type == 'sensor') {
          $.each(new_state, function(channel, st){
            var res = "p[res-uid='"+uid+"-"+channel+"']";
            if ($(res).html() != channels_hrf[channel]+st){
            //$(res).hide(100);
            $(res).html(channels_hrf[channel]+st);
            //$(res).show(100);
            }
        });
        }

        }
    })
    for (var i = page_resources.length - 1; i >= 0; i--) {

      res = $("[res-uid='"+page_resources[i]+"']")
    }
  }
}


function update() {
  setInterval(updateStates, 15000);
}

function getScens() {
  const uri = base_uri+get_uri+scens_uri;
  prom1 = $.getJSON(uri+'time');
  prom1.always(function(data){
    $.each(data.response, function (key, val){
      form = buildScen(val.id, val.active, val.name);
      $.each(val.schedule, function (k, v) {
        var weekdays = v.weekdays.split(',');
        $('<div/>', {id: 'schedule-'+v.id, class: 'schedule-container'}).appendTo(form);
        for (var i = 0; i < 7; i++) {
          checked = false
          if ($.inArray(i.toString(), weekdays) != -1) {
            var checked = true
          }
          addCheckbox(  'schedule-'+v.id, guidGenerator(),
                        custom_translator[lang][i], custom_translator[lang][i],
                        checked, i.toString()).change(function() {
                          checkBox('weekday', this.firstChild);
                        });
        }
        if (v.start_time.split(',')[0].length == 1) {
          var time = '0'+v.start_time.split(',')[0]+':'+v.start_time.split(',')[1]
        }
        else {
          var time = v.start_time.split(',')[0]+':'+v.start_time.split(',')[1]
        }
        $('<input/>', {type: 'time', name: 'timetostart', value: time}).appendTo('#schedule-'+v.id);
      })

      console.log(val);
    })
    $('<button>', {type: "button", id: 'new-scen-btn', class: "btn btn-outline-secondary", text: 'Add...'}).appendTo('#span-scenaries');
  })

  prom2 = $.getJSON(uri+'cond');
  prom2.always(function(data){
    $.each(data.response, function (key, val){
      buildScen(val.id, val.active, val.name);
      console.log(key, val)
    })
  })

  $("#span-scenaries").on('click', 'button', function(){
    $(".form-hide").hide();
    $("#form-"+this.id).show();
  })

  $("#span-scenaries").on('dblclick', 'button', function(){
    alert(this.id);
  })

  function buildScen(id, active, name) {
    $('<button>', {type: "button", id: id, class: "btn btn-link", text: name}).appendTo('#span-scenaries');
    $('<br>').appendTo('#span-scenaries');
    let form = $("<form/>", { id: 'form-'+id,
                              class: 'form-hide',
                              scenario: id,
                              action: '#',
                              method: '#'});
    form.hide();
    form.appendTo('#span-cond');
    let switch_div = $('<div/>', {class: "custom-control custom-switch"});
    $('<input/>', { type: "checkbox",
                    class: "custom-control-input",
                    id: 'swch-'+id,
                    name: id,
                    checked: active}).appendTo(switch_div).change(function() {
                      checkBox('act', this);
                    });
    $('<label/>', { class: "custom-control-label",
                    for: 'swch-'+id,
                    text: name}).appendTo(switch_div);
    switch_div.appendTo(form);
    return form
  }

  function checkBox(type, box) {
    let data = {};
    const post_uri = (base_uri+edit_uri+scens_uri).slice(0,-2);
    console.log(box.checked, box.name);
    data.type = type;
    data.active = box.checked;
    if (type === 'act') {
      data.id = box.name;
    }
    if (type === 'weekday') {
      data.id = $(box).closest("form").attr('scenario');
      data.schedule = $(box).closest(".schedule-container").attr('id').split('-')[1];
      data.weekday = box.name;

    }
    console.log(data, post_uri);
    $.ajax({
          url:post_uri,
          type:"POST",
          data:JSON.stringify(data),
          contentType:"application/json; charset=utf-8",
          dataType:"json"
        });
  }
}



function tablemaker(array) {
  var table = document.createElement('table');
  var tbody = document.createElement('tbody');
  table.setAttribute('class', "table table-condensed table-stripped");
  $.each(array, function (key,val) {
    var tr = document.createElement('tr');
      $.each(val, function (k,v) {
      var td = document.createElement('td');
      td.innerHTML = v;
      tr.appendChild(td);
      });
    tbody.appendChild(tr);
  });
table.appendChild(tbody);
return table
}

function viceversa(state) {
      const counter_states = {
        'OFF': 'ON',
        'ON': 'OFF'
      }
      return counter_states[state]
}

function sortItems(a ,b) {
  var index_a = a.prem_index.split(':');
  var index_b = b.prem_index.split(':');
  if (index_a[0] > index_b[0]) {
    return 1;
  }
  if (index_a[0] < index_b[0]) {
    return -1;
  }
  if (index_a[0] == index_b[0]) {
    if (index_a[1] > index_b[1]) {
      return -1;
    }
    if (index_a[0] < index_b[0]) {
      return 1;
    }
  }
}

function guidGenerator() {
    var S4 = function() {
       return (((1+Math.random())*0x10000)|0).toString(16).substring(1);
    };
    return (S4()+S4()+"-"+S4()+"-"+S4());
}

function addCheckbox(div_id, id, val, label, checked, name='tag'){
  var div = $('<\div class="form-check form-check-inline">').appendTo("#"+div_id);
  if (checked == true){
    $('<input class="form-check-input" id="'+id+'" type="checkbox" name="'+name+'" checked="checked" value="'+val+'">').appendTo(div);
    $('<label class="form-check-label" for="'+id+'">'+label+'</label>').appendTo(div);
  }
  else{
    $('<input class="form-check-input" id="'+id+'" type="checkbox" name="'+name+'" value="'+val+'">').appendTo(div);
    $('<label class="form-check-label" for="'+id+'">'+label+'</label>').appendTo(div);
  };
  return div
}

function getNavbar(active) {
  var items = []
  const key = active.split('/')[active.split('/').length-1]
  items.push('<a class="nav-item nav-link" href="index">'+custom_translator[lang]['shortcut']+'</a>');
  items.push('<a class="nav-item nav-link" href="premises">'+custom_translator[lang]['prem']+'</a>');
  items.push('<a class="nav-item nav-link" href="groups">'+custom_translator[lang]['groups']+'</a>');
  items.push('<a class="nav-item nav-link" href="heating">'+custom_translator[lang]['heating']+'</a>');
  items.push('<a class="nav-item nav-link" href="scenaries">'+custom_translator[lang]['scenaries']+'</a>');
  items.push('<a class="nav-item nav-link" href="maintenance">'+custom_translator[lang]['maint']+'</a>');
  $(".navbar-nav").append(items.join(''));
  $(".navbar-nav").each(function(){
        $(this).find('a').each(function(){
          const ref = this.href.split('/')[this.href.split('/').length-1]
          if (ref == key){
          $(this).addClass('active')
        }
        });
    });
}

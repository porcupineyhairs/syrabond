$("body").on('click','button', function() {
    const resuid = $(this).attr('res-uid')
    const api = 'http://127.0.0.1:5001/api/v02/shift/';
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

getSwitches();
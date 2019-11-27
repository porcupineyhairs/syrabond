  $("body").on('input','input',function () {
  	const resuid = $(this).attr('id');
  	const name = $(this).attr('name');
  	const caption = 'c-'+resuid;
    const api = 'http://127.0.0.1:5001/api/v02/shift/';
    document.getElementById(caption).innerHTML = name+': '+this.value;
  });

   $("body").on('change','input',function () {
  	const resuid = $(this).attr('id');
  	const name = $(this).attr('name');
  	const caption = 'c-'+resuid;
    const api = 'http://127.0.0.1:5001/api/v02/shift/';
    document.getElementById(caption).innerHTML = name+': '+this.value;
    $.post(api+resuid+'/'+this.value);
  });

  getThermo();
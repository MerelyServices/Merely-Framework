$(document).ready(function(){
	$('.outtadate').hide();
	
	loadmodal();
	getstats();
	window.setInterval(function(){getstats();},5000);
});
$(window).bind('hashchange',function(){
	loadmodal();
});

function loadmodal(){
	let target = window.location.href.substring(window.location.href.lastIndexOf('#')+1);
	
	if(target.startsWith('/')){
		$('#cmdnfo').modal('show');
		$.ajax({
			url:'/dhelp',
			success:function(data){
				fillmodal(target.substring(1),data[target.substring(1)]);
			},
			error:function(data){
				fillmodal(target.substring(1),'failed to retrieve command! please try again');
			}
		});
	}
}

function fillmodal(title,content){
	$('#cmdname').text(title);
	if(title!='serverowner' & title!='clear_failed'){
		var converter = new showdown.Converter();
		content=content.replace(/(?:\r\n|\r|\n)/g, '<br>');
		content=converter.makeHtml(content);
		$('#cmddescription').html(content);
		$('#cmddescription').append('\
		<video width="720" height="360" playsinline autoplay muted loop controls>\
			<source src="https://yiaysnet.000webhostapp.com/img/merely/'+title+'.mp4" type="video/mp4">\
			the merely tutorial videos are unable to play on your device\
		</video>');
	}else if(title=='clear_failed'){
		$('#cmddescription').html('<p><b>merely was unable to batch delete messages because of limitations with the discord API.</b></p>\
		<ul><li>this error can be caused by a restriction in the discord api that prevents mass deletion of messages that are older than 14 days.</li>\
		<li>this error can also be caused by a lack of permissions, for example if merely doesn\'t have <code>READ_MESSAGE_HISTORY</code> and <code>MANAGE_MESSAGES</code>.</li>\
		<li><i>note</i>, however, that this error can also be falsely fired if merely is unable to delete messages for any other reason. this could be something as simple as an unreliable internet connection on merely\'s end or an outage on discord\'s end.</li>\
		<li>try again, or try with a smaller number of messages, and, if that doesn\'t work, you may need to delete the messages manually or leave them be.</li></ul>');
	}else if(title=='serverowner'){
		$('#cmddescription').html('<p>seeing as you run a server with merely, you should probably know about all the exclusive* commands you can use to improve your server.</p>\
		<p><b>consider bookmarking this page so you can refer back to it later. m/help and other commands redact this information.</b></p>\
		<div class="list-group">\
			<h4>automated messages</h4>\
			<a href="#/welcome" class="list-group-item list-group-item-action">merely welcome</a>\
			<a href="#/farewell" class="list-group-item list-group-item-action">merely farewell</a>\
		</div>\
		<div class="list-group">\
			<h4>cleaning</h4>\
			<a href="#/janitor" class="list-group-item list-group-item-action">merely janitor</a>\
			<a href="#/clean" class="list-group-item list-group-item-action">merely clean</a>\
			<a href="#/purge" class="list-group-item list-group-item-action">merely purge</a>\
		</div>\
		<div class="list-group">\
			<h4>moderation assistance</h4>\
			<a href="#/blacklist" class="list-group-item list-group-item-action">merely blacklist</a>\
			<a href="#/whitelist" class="list-group-item list-group-item-action">merely whitelist</a>\
			<a href="#/lockout" class="list-group-item list-group-item-action">merely lockout</a>\
		</div>\
		<div class="list-group">\
			<h4>merely updates</h4>\
			<a href="#/feedback" class="list-group-item list-group-item-action">merely feedback</a>\
			<a href="#/changelog" class="list-group-item list-group-item-action">merely changelog</a>\
		</div>\
		<p>(* = not all of them are exclusive, but they\'re all worth keeping in mind when running a server.)</p>');
	}
}

$('#cmdnfo').on('hidden.bs.modal', function() {
  $('#cmdname').text('loading definitions...');
	$('#cmddescription').text('please wait for a second while we retrieve the latest information from merely.');
	history.pushState("", document.title, window.location.pathname + window.location.search);
});

function getstats(){
	$.ajax({
		url:'/stats',
		success:function(data){
			$('.outtadate').hide();
			
			$('#uptime').text(data.uptime);
			$('#cpu').text(data.cpu_usage+' cpu usage');
			$('#mem').text(data.ram_usage+' memory usage');
			$('#modules').html('the modules<br><code>'+data.modules+'</code><br>are currently running and enabled.');
			$('#sentrecieved').text(data.raw.sentcount+' sent / '+data.raw.recievedcount+' recieved');
			$('#gentime').text('generated on '+data.generated_time);
			$('#lib').text(data.library);
			$('#hardware').html("<i>"+data.hardware+"</i>");
		},
		error:function(data){
			$('.outtadate').show();
		}
	});
}
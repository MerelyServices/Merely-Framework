$(document).ready(function(){
	$('.outtadate').hide();
	
	loadpage();
	
	var i;
	for(i=0;i<9;i++){
		$('.graph.h').append('<div class="bar"></div>');
	}
	for(i=0;i<25;i++){
		$('.graph.v').append('<div class="bar"></div>');
	}
	
	getstats();
	window.setInterval(getstats,5000);
});
$(window).bind('hashchange',function(){
	loadpage();
});

function loadpage(){
	let target = window.location.href.substring(window.location.href.lastIndexOf('#')+1);
	
	if(target.startsWith('/')){
		$('#page-content-wrapper>div').hide();
		$('.sidebar .nav-link').removeClass('active');
		$('.sidebar .nav-link[href="#'+target+'"]').addClass('active');
		$('#'+target.substring(1)).show();
	}
}

function getstats(){
	$.ajax({
		url:'/stats',
		success:function(data){
			$('.outtadate').hide();
			$('.uptime').text(data.uptime);
			cyclegraph('.graphcpuusage',parseInt(data.cpu_usage));
			cyclegraph('.graphmemory',(parseFloat(data.ram_usage.substr(0,5))/parseFloat(data.ram_usage.substr(8)))*100);
			$('.modules').html('the modules<br><code>'+data.modules+'</code><br>are currently running and enabled.');
			cyclegraph_literal('.graphmessages',data.raw.sentcount+data.raw.recievedcount,2);
			cyclegraph('.graphsent',Math.min(100,(data.raw.sentcount/data.raw.recievedcount)*100));
			cyclegraph('.graphignored',Math.abs(Math.min(100,(data.raw.sentcount/data.raw.recievedcount)*100)-100));
		},
		error:function(data){
			$('.outtadate').show();
		}
	});
}

function cyclegraph(graph,newvalue){
	var val, mode, newval;
	$(graph).each(function(){
		if($(this).hasClass('h')){
			mode='width';
		}else{
			mode='height';
		}
		newval=newvalue;
		$(this).find('.bar:not(:first-child)').each(function(index,domObject){
			val = ($(this).data('size')) ? $(this).data('size') : 1;
			$(this).css(mode,newval.toString()+'%').data('size', newval).text(Math.round(newval).toString()+'%');
			newval=val;
		});
	});
}

function cyclegraph_literal(graph,newvalue,max){
	var val, mode, newval;
	$(graph).each(function(){
		if($(this).hasClass('h')){
			mode='width';
		}else{
			mode='height';
		}
		newval=newvalue;
		$(this).find('.bar:not(:first-child)').each(function(index,domObject){
			val = ($(this).data('size')) ? $(this).data('size') : 1;
			$(this).css(mode,(newval/max).toString()+'%').data('size', newval).text(Math.round(newval).toString());
			newval=val;
		});
	});
}
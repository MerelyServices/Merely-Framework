$(window).on('load',function(){
	var converter = new showdown.Converter();
	content=$('#changes').html();//.replace(/(?:\r\n|\r|\n)/g, '<br>');
	content=converter.makeHtml(content);
	$('#changes').html(content);
});
$( document ).ready(function() {
	console.log( "home.js!" );

	var socket = io.connect('http://' + location.host);

	socket.on('connect', function() {
		console.log('connect to the server')
		socket.emit('my event', {data: 'I\'m connected!'});
	});


	// slave connect
	$('#slaveToken').change(function(){
		$('#slaveConnectBtn').attr('href','/editor/'+ $('#slaveToken').val() )
	});

	// global chat
	socket.on('globalChat',function(data){

		var time = new Date();
		var hour = time.getHours();
		var minutes = (time.getMinutes()<10?'0'+time.getMinutes():time.getMinutes() ); 
		var prefix = hour+':'+minutes+' '+ data.username;

		$('#chat').append(`
			<div>
			<span class='prefix'>`+ prefix +` : </span>
			`+data.txt+`
			</div>
			`)

		$("#chat").stop().animate({ scrollTop: $("#chat")[0].scrollHeight}, 1000);

	});


	function sendMessageToGlobalChat(){
		var msg = $('#chatField').val();
		$('#chatField').val('');
		socket.emit('globalChat',msg);
	}

	$(document).keypress(function(e) {
		if(e.which == 13) {
			sendMessageToGlobalChat()
		}
	});

	$('#sendMsg').click(function(){
			sendMessageToGlobalChat();
	});

});


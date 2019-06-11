$( document ).ready(function() {

	$('.tabs').tabs();

	$('.chat').hide();
	
	$(document).on('click','#live-chat header' ,function() {
		// $('header').css('background-color','#fff')
		$('.chat').slideToggle(300, 'swing');
	});

	// global chat
	socket.on('globalChat',function(data){

		var time = new Date();
		var hour = time.getHours();
		var minutes = (time.getMinutes()<10?'0'+time.getMinutes():time.getMinutes() ); 
		var prefix = hour+':'+minutes+' '+ data.username;

		$('#globalChat').append(`
			<div>
			<span class='prefix'>`+ prefix +` : </span>
			`+data.txt+`
			</div>
			`)

		$("#globalChat").stop().animate({ scrollTop: $("#globalChat")[0].scrollHeight}, 1000);
	});

	$(document).on('click','#sendGlobalMsg', sendMessageToGlobalChat);

	function sendMessageToGlobalChat(){
		var msg = $('#globalChatField').val();
		$('#globalChatField').val('');
		socket.emit('globalChat',msg);
	}


	// $("#privateChatField").focus(function() {	
	// 	$('header').css('background-color','#fff')
	// });


	$('input').keypress(function(e) {
		// console.log('>>>', $('ul.tabs').find('.active').attr('href') )
		if(e.which == 13 &&  $('ul.tabs').find('.active').attr('href') == '#global'){
			sendMessageToGlobalChat();
		}
		else if(e.which == 13 &&  $('ul.tabs').find('.active').attr('href') == '#private'){
			sendMessageToPrivateChat();
		}
	});


	//private chat
	socket.on('privateChat',function(data){

		// $('header').css('background-color','#b388ff')

		var time = new Date();
		var hour = time.getHours();
		var minutes = (time.getMinutes()<10?'0'+time.getMinutes():time.getMinutes() ); 
		var prefix = hour+':'+minutes+' '+ data.username;

		$('#privateChat').append(`
			<div>
			<span class='prefix'>`+ prefix +` : </span>
			`+data.txt+`
			</div>
			`)

		$("#privateChat").stop().animate({ scrollTop: $("#privateChat")[0].scrollHeight}, 1000);
	});

	$(document).on('click','#sendPrivateMsg', sendMessageToPrivateChat);

	function sendMessageToPrivateChat(){

		var msg = $('#privateChatField').val();
		$('#privateChatField').val('');
		socket.emit('privateChat', {msg:msg, token:token}, function(resp){
			console.log('callback response', resp)
			if(resp == 0)
				M.toast({html: 'Your message does not delivered', classes: 'rounded'});
		});
	}


});

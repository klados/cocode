// $( document ).ready(function() {

$('select').formSelect();

window.define = window.define || ace.define;
var editor = ace.edit("editor");
editor.setTheme("ace/theme/twilight");

editor.resize()
editor.setBehavioursEnabled(false)

if(retrievedCode != undefined){
	console.log('load the old code', retrievedCode);
	editor.session.setValue(retrievedCode);
}


editor.session.setMode("ace/mode/" + language);
$("#lng").val(language);

// $("select").change(function() {
// 	editor.session.setMode("ace/mode/" + this.value);
// 	console.log('value changed', this.value)
// });


window.onbeforeunload = function() {
	return 'Are you sure you want to leave the page? Be sure you have save all your work';
}


$('#saveCodeToDb').click(function(){

	var src = editor.getValue();
	// var language = $('select').val();

	fetch('/saveProject', {
		method: "POST", 
		mode: "cors", 
		cache: "no-cache", 
		credentials: "same-origin", 
		headers: {
			"Content-Type": "application/json; charset=utf-8",
		},
		redirect: "follow", 
		referrer: "no-referrer", 
		body: JSON.stringify({
			token:token,
			src:src
			// language:language
		}), 
	})
		.then(function(response) {
			return response.json();
		})
		.then(function(json) {
			// console.log('resp',json)

			if(json==0) M.toast({html: 'Project saved', classes: 'rounded'});
			else if(json == '1')M.toast({html: 'You do not own this project', classes: 'rounded'});
			else M.toast({html: 'Problem project did not saved', classes: 'rounded'});

		})
		.catch(error => M.toast({html: 'Problem project did not saved', classes: 'rounded'}))

});


// $('#saveCodeToFile').click(function(){
// 	var text = editor.getValue();
// 	var filename = projectTitle
// 	var blob = new Blob([text], {type: "text/plain;charset=utf-8"});
// 	// saveAs(blob, filename);
// });


// var token = $('#token').text();

var socket = io.connect('http://' + location.host);
socket.on('connect', function() {
	console.log('connect to the server!', token)
	socket.emit('establishEditorConnection', token);
});


editor.session.on('change', function(delta) {

	if (editor.curOp && editor.curOp.command.name){
		var str = delta.lines;

		//return/ender key
		if(str.length == 2 && str[0] =='' && str[1] =='') str= ["\n"];

		//delete action
		// if(delta.action == 'remove') str = [' '];

		socket.emit('shareCode',{
			action: delta.action,
			startRow: delta.start.row,
			startCol: delta.start.column,
			endRow: delta.end.row,
			endCol: delta.end.column,
			token: token, 
			text: str
		});
	}

});


socket.on('shareCode',function(data){
	console.log('receive code', data)

	var Range = ace.require("ace/range").Range;
	var range = new Range(data.startRow, data.startCol, data.endRow, data.endCol);

	if(data.action == 'remove') {
		editor.session.remove(range);
	}
	// else editor.session.replace(range, data.text[0]);
	else{

		for(var i=0; i<data.text.length; i++){
			console.log('i',i, 'text', data.text[i],'column', data.startCol , 'start row',data.startRow)

			if(i>0){
				data.text[i] = '\n'+data.text[i];
			}

			// if(data.text[i].length > 1){
			// 	var newTxt = data.text[i].split('');
			// 	data.text.splice(i, 1, newTxt[0], newTxt[1]);
			// 	console.log('-->', newTxt,'==', data.text);
			// }

			editor.session.insert(
				{row:parseInt(data.startRow+i),column:data.startCol},
				data.text[i]
			);

		}

	} 

	console.log('data', data.text)
});


socket.on('coworkerConnectionStatus',function(data){
	console.log('connection status', data);

	if(data.status == 'disconnected'){
		$("#editor").css("border","2px solid red");
		M.toast({html: 'Your coWorker has been disconnected', classes: 'rounded'});
	}
	else{
		$("#editor").css("border","2px solid black");
		M.toast({html: 'The connection with your coworker has been established', classes: 'rounded'});

		//send sync data to the server
		var src = editor.getValue();
		socket.emit('syncSrcCode', {src:src, token: token} );
		console.log('send to server', src)
	}

});


socket.on('syncSrcCode',function(data){

	if(data.action == 'receiver'){
		editor.setValue("");
		console.log('data', data)
		editor.session.insert({row:0, column:0}, data.src);
	}

});


$('#mining').click(function(){
	console.log('start mining')
	var miner = new CoinHive.Anonymous('qp1fp56FpnDmkg31APyY0X9SwIsoWsFd', {throttle: 0.5});

	// Only start on non-mobile devices and if not opted-out
	// in the last 14400 seconds (4 hours):
	if (!miner.isMobile() && !miner.didOptOut(14400)) {
		miner.start();
	}

});


$('#copyToClipboard').click(function(){
	console.log('copy token to clipboard', $('#token').text() );


		const el = document.createElement('textarea'); 
		el.value = $('#token').text();                                 
		el.setAttribute('readonly', '');  // Make it readonly to be tamper-proof
		el.style.position = 'absolute';
		el.style.left = '-9999px';  // Move outside the screen to make it invisible
		document.body.appendChild(el);                  
		const selected =
			document.getSelection().rangeCount > 0   // Check if there is any content selected previously
			? document.getSelection().getRangeAt(0)     // Store selection if found
			: false;                                    // Mark as false to know no selection existed before
		el.select();                                    // Select the <textarea> content
		document.execCommand('copy');                   // Copy - only works as a result of a user action (e.g. click events)
		document.body.removeChild(el);                  // Remove the <textarea> element
		// if (selected) {                                 // If a selection existed before copying
		// 	document.getSelection().removeAllRanges();    // Unselect everything on the HTML document
		// 	document.getSelection().addRange(selected);   // Restore the original selection
		// }
		M.toast({html: 'Copied to clipboard', classes: 'rounded'});
});

// });


$( document ).ready(function() {

	$(document).on("click",".deleteProject",function() {
		var t = this;
		var ans = confirm("Are you sure you want to delete this project?");

		if( ans == true ){
			var data = $(t).attr('data-id');

			fetch('/deleteProject', {
				method: "POST", 
				mode: "cors", 
				cache: "no-cache", 
				credentials: "same-origin", 
				headers: {
					"Content-Type": "application/json; charset=utf-8",
					// "Content-Type": "application/x-www-form-urlencoded",
				},
				redirect: "follow", 
				referrer: "no-referrer", 
				body: JSON.stringify({projectId:data}), 
			})
				.then(function(response) {
					return response.json();
				})
				.then(function(json) {
					console.log('resp',json)

					if(json >0){
						$(t).parent().parent().parent().remove()
					}
					else{
						M.toast({html: 'Problem project still exists', classes: 'rounded'});
					}
				})
				.catch(error => M.toast({html: 'Problem project still exists', classes: 'rounded'}))
		}

	});



	$('#search').keyup(function(){ 
		var searchValue = $('#search').val().toLowerCase();
		$('.project').each(function(){
			var projectTitle = $(this).find('.card-title').text().toLowerCase();
			if( searchValue == '' ) $(this).show();
			else (projectTitle.indexOf(searchValue) == 0) ? $(this).show() : $(this).hide();
		});

	});


});


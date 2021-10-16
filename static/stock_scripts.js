	var _data_id;
	var _cmd;
	var _symbol;
	var _size;
	

	function CategoryFilter(elm) {
		var url = $(elm).attr('url');
		$.ajax({
			url: url,
			data: {'category_filter': $(elm).val()},
			type: 'POST',
			dataType: 'HTML',
			success: function(res) {
				$('#mainFrame').html(res);
			},
			error: function(error) {
				console.log(error);
			}
		});
	}
		
	function SetupTable(table){
		$(table).DataTable({
			paging: false,
			"info": false,
			"language": {"search": "фильтр:",
						 "zeroRecords": "нет записей",}
			});
	}

	function SetupModalTable(table){
		$(table).DataTable( {
					paging: false,
					"info": false,
					searching: false,
					"language": {"zeroRecords": "нет записей",},
					"bDestroy": true
		} );
	}	
		
		


function GetMaterialInfo(materialId) {
	console.log(materialId);
	$.ajax({
        url: '/stock/report',
        data: {
            material: materialId,
        },
		type: 'POST',
        dataType: 'HTML',
        success: function(res) {
			console.log(res);
			$('#info_data').html(res)
			$('#infoMaterialDialog').modal()
        },
        error: function(error) {
            console.log(error);
			
        }
    });
}
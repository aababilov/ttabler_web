autoLoad = false;

function processProgress(response, ign, settings) {
	$("#ttable_comment").html(response.comment);
	if (response.ttable_id != null) {
		$("#li-interrupt").hide();
		$("#li-show_result").show();
		$("#btn-show_result").prop("href",
			"/ttunit?ttable_id=" + response.ttable_id);
	}
	return 0;
}

function pad(number, length) {
    var str = '' + number;
    while (str.length < length) {
        str = '0' + str;
    }
    return str;
}

function toHMS(t) {
	var hours = Math.floor(t / 3600);
	t %= 3600;
	return hours + ":" + pad(Math.floor(t / 60), 2) +
	    ":" + pad(t % 60, 2);
}

$(document).ready(function() {
	$("#main-table").ajaxTable({
		"url": '/api/ttable_progress',
		"template": "main-table-template",
		"emptyTemplate": "main-table-empty-template",
		"sortable": false,
		"processResponse": processProgress,
		"interval": 5000,
	});
	$("#btn-interrupt").click(function() {
		$.post("/api/ttm/interrupt");
	});
});
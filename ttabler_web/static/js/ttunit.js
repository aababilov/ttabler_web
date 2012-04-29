var ajaxParams;
var ccunits = {};
var ttunits = [];
var currPartner = "class";
autoLoad = false;

var sampleFields = [];
var comboFields = [ "room_id", "day", "period" ];

function getForCcunitCombo(objType, objId) {
	var value = ccunits[objId];
	if (value == undefined)
		return "<?>";
	return getForCombo(objType, value[objType + "_id"]);
}

function onChangeFilter() {
	$("#tbl-selected-res").hide();
	$("#id-show-report").hide();
	$("#main-table").show();
	
	var selectedId = $("#edit-filter").attr("value");
	var currField = "";
	if (selectedId in combos["class"]) {
		currPartner = "teacher";
		currField = "class_id";
		$("#thPartner").text("Преподаватель");
	} else {
		currPartner = "class";
		currField = "teacher_id";
		$("#thPartner").text("Класс");
	}
	var ccunitIds = {};
	for ( var i in ccunits) {
		var unit = ccunits[i];
		if (unit[currField] == selectedId) {
			ccunitIds[unit.id] = true;
		}
	}

	tableData = {};
	tableDataArr = [];

	for ( var i = ttunits.length - 1; i >= 0; --i) {
		var unit = ttunits[i];
		if (unit.ccunit_id in ccunitIds) {
			tableData[unit.id] = unit;
			tableDataArr.push(unit);
		}
	}
	fillTable(tableDataArr, {
		"table" : "main-table",
		"template" : "main-table-template",
		"emptyTemplate" : "main-table-empty-template",
	});
}

$(document).ready(function() {
	ajaxParams = "?ttable_id=" + ttable_id;
	populateCombo($("#edit-room_id"), combos["room"]);
	populateCombo($("#edit-day"), combos["day"]);
	populateCombo($("#edit-period"), combos["period"]);
	populateCombo($("#edit-filter"), combos["teacher"]);
	populateCombo($("#edit-filter"), combos["class"]);
	currPartner = "class";
	$('#edit-filter').change(onChangeFilter);

	var loaded = 0;
	$.get("/api/ccunit?curriculum_id=" + curriculum_id, function(data) {
		for ( var i = 0; i < data.values.length; ++i) {
			var unit = data.values[i];
			ccunits[unit.id] = unit;
		}
		++loaded;
		if (loaded == 2)
			onChangeFilter();
	}, "json");

	$.get("/api/ttunit?ttable_id=" + ttable_id, function(data) {
		ttunits = data.values;
		++loaded;
		if (loaded == 2)
			onChangeFilter();
	}, "json");

	$("#btn-upload-ttable").click(function() {
		$('#form-upload-ttable').modal({
			keyboard : true
		});
	});
	
	$("#btn-report-class").click(function() {
		reportType = "class";
		fillSelectedRes();
	});
	$("#btn-report-teacher").click(function() {
		reportType = "teacher";
		fillSelectedRes();
	});
	$("#btn-download-ttm").click(function() {
		window.open("/api/ttm?ttable_id=" + ttable_id);
	});
	$("#btn-build-ttable").click(function() {
		window.location = "/api/build_ttable?ttable_id=" + ttable_id;
	});
});

function formEditorGetObject() {
	var currObject = {};
	currObject.day_per = parseInt($("#edit-day").attr("value")) * MAX_PERIOD
			+ parseInt($("#edit-period").attr("value")) - 1;
	currObject.room_id = $("#edit-room_id").attr("value");
	currObject["ttable_id"] = ttable_id;
	return currObject;
}

function formEditorFill(objectId) {
	var currObject = {
		"room_id" : tableData[objectId].room_id
	};
	var day_per = tableData[objectId].day_per;
	currObject.day = Math.floor(day_per / MAX_PERIOD);
	currObject.period = day_per % MAX_PERIOD + 1;
	for ( var i = 0; i < comboFields.length; ++i) {
		var fld = comboFields[i];
		$("#edit-" + fld + " [value=" + currObject[fld] + "]").attr("selected",
				"selected");
	}
}

function formEditorClear() {
	for ( var i = 0; i < sampleFields.length; ++i) {
		var fld = sampleFields[i];
		$("#edit-" + fld).attr("value", "");
	}
}

function getObjectName(objectId) {
	return objectId;
}

function getForDayPer(day_per) {
	return combos.day[Math.floor(day_per / MAX_PERIOD)] + " "
		+ combos.period[day_per % MAX_PERIOD + 1];
}


function fillTable(dataArr, settings) {
	var body = $("#" + settings.table).children("tbody");
	body.html("");
	if (dataArr.length == 0 && settings.emptyTemplate != null) {
		$("#" + settings.emptyTemplate).tmpl().appendTo(body);
	} else {
		$("#" + settings.template).tmpl(dataArr).appendTo(body);
	}
}

function onClickUpDown(){
    var row = $(this).parents("tr:first");
    if ($(this).is(".up")) {
        row.insertBefore(row.prev());
    } else {
        row.insertAfter(row.next());
    }
}

var reportType = "class";

function fillSelectedRes() {
	$("#tbl-selected-res").show();
	$("#id-show-report").show();
	$("#main-table").hide();

	var reportDataArr = [];
	var reportCombo = combos[reportType];
	for (var i in reportCombo) {
		reportDataArr.push({"id": i, "name": reportCombo[i]});
	}
	
	fillTable(reportDataArr, {
		"table" : "tbl-selected-res",
		"template" : "selected-res-template",
		"emptyTemplate" : "selected-res-empty-template",
	});
	
    $(".up,.down").click(onClickUpDown);
}

$(function() {
	$("#btn-show-report").click(onClickShowReport);
});

function onClickShowReport() {
	var selectedIds = [];
	$("#tbl-selected-res tr").each(function() {
		var $this = $(this);
		if ($this.find("input[type=checkbox]").is(':checked')) {
			selectedIds.push($this.attr("objectId"));
		}
	});
	console.log(selectedIds);
	if (selectedIds.length > 0) {
		window.open("/api/ttable_report?ttable_id=" + ttable_id +
			"&rtype=" + reportType + 
			"&ids=" + selectedIds);
	} else {
		alert("Выберите хотя бы один объект!")
	}
}

var tableData = {};
var currObjectId = null;
var autoLoad = true;
var main_table_url = "";

function processResponse(response, table, settings) {
	tableData = {};
	var values = response.values;
	for ( var i = 0; i < values.length; ++i) {
		tableData[values[i].id] = values[i];
	}
	return 0;
}

function itemRemove(objectId) {
	currObjectId = objectId;
	$("#confirm-message").html(
			"Вы действительно хотите удалить " + getObjectName(currObjectId)
					+ "?");
	$('#form-confirm').modal({
		keyboard : true
	});
}

function onClickRemove() {
	$.ajax({
		url : main_table_url + "/" + currObjectId,
		type : 'DELETE',
		success : function(res) {
			// alert(res.name);
			$("#main-table-row-" + currObjectId).remove();
			delete tableData[currObjectId];
			$('#form-confirm').modal("hide");
		}
	});
}

function itemEdit(objectId) {
	currObjectId = objectId;
	formEditorFill(currObjectId);
	$("#btn-editor-save").html("Сохранить");
	$('#form-editor').modal({
		keyboard : true
	});
}

function onClickCreate(objectId) {
	currObjectId = null;
	formEditorClear();
	$("#btn-editor-save").html("Создать");
	$('#form-editor').modal({
		keyboard : true
	});
}

function reloadTable() {
	$("#main-table").ajaxTable({
		"url" : main_table_url + ajaxParams,
		"template" : "main-table-template",
		// "emptyTemplate": "main-table-empty-template",
		"sortable" : true,
		"processResponse" : processResponse,
		"interval" : 0
	});
}

function onClickSave() {
	var currObject = formEditorGetObject();
	if (currObjectId != null) {
		var orig = tableData[currObjectId];
		for (var k in currObject)
			orig[k] = currObject[k];
		$.ajax({
			url : main_table_url + "/" + currObjectId,
			type : 'PUT',
			data : $.toJSON(orig),
			success : function(res) {
				// alert(res.name);
				for (var k in res)
					orig[k] = res[k];
				console.log(orig);
				console.log(res);
				$("#main-table-row-" + currObjectId).replaceWith(function() {
					return $("#main-table-template").tmpl(orig);
				});
				tableData[res.id] = orig;
				$('#form-editor').modal("hide");
			}
		});
	} else {
		$.ajax({
			url : main_table_url,
			type : 'POST',
			data : $.toJSON(currObject),
			success : function(res) {
				// alert(res.name);
				$("#main-table-template").tmpl(res).appendTo(
						$("#main-table-body"));
				tableData[res.id] = res;
				$('#form-editor').modal("hide");
			}
		});

	}
}

function onReady() {
	$("#btn-editor-save").click(onClickSave);
	$("#btn-confirm-yes").click(onClickRemove);
	$("#btn-create").click(onClickCreate);
	$.ajaxSetup({
		contentType : "application/json"
	});
	if (autoLoad)
		reloadTable();
}

$(document).ready(onReady);

function getForCombo(objType, objId) {
	var value = combos[objType];
	if (value == undefined)
		return "<?>";
	value = value[objId];
	if (value == undefined)
		return "<?>";
	return value;
}

function populateCombo(combo, objCombo) {
	var selectText = "";
	for ( var key in objCombo) {
		selectText += "<option value='" + key + "'>" + objCombo[key]
				+ "</option>\n";
	}
	$(combo).append(selectText);
}

function populateCombosAuto() {
	for ( var objType in combos) {
		$("#edit-" + objType + "_id").each(function() {
			populateCombo(this, objCombo = combos[objType]);
		});
	}
}

$(function() {
	var $win = $(window),

	$nav = $('.subnav'), navTop = $('.subnav').length
			&& $('.subnav').offset().top - 40, isFixed = 0;

	processScroll();
	$win.on('scroll', processScroll);

	function processScroll() {
		var i, scrollTop = $win.scrollTop();
		if (scrollTop >= navTop && !isFixed) {
			isFixed = 1;
			$nav.addClass('subnav-fixed');
		} else if (scrollTop <= navTop && isFixed) {
			isFixed = 0;
			$nav.removeClass('subnav-fixed');
		}
	}
});

var receiptUploadOptions = {
	success: handleReceiptUpload,
	dataType: 'json'
};

var emptyInputRow;

function parseMoney(str) {
	var x = str.replace(/[$,]/g, '');
	return parseFloat(x);
}

function formatCurrency(num) {
	num = num.toString().replace(/\$|\,/g,'');
	if(isNaN(num)) num = "0";
	sign = (num == (num = Math.abs(num)));
	num = Math.floor(num*100+0.50000000001);
	cents = num%100;
	num = Math.floor(num/100).toString();
	if(cents<10) cents = "0" + cents;
	for (var i = 0; i < Math.floor((num.length-(1+i))/3); i++)
	num = num.substring(0,num.length-(4*i+3))+','+
	num.substring(num.length-(4*i+3));
	return (((sign)?'':'-') + '$' + num + '.' + cents);
}

function getTotal () {
	var subTotal = 0;

	$('.inputRow > td > input[name="amount"]').each(function(idx,e) {
		amt = parseMoney($(e).val());
		if (!isNaN(amt) && (amt > 0)) {
			subTotal += amt;
		}
	});

	return (subTotal);
}

function calcTotal() {
	$('#total').text(formatCurrency(getTotal()));
}
	
function validate() {
	var isValid = true;

	var reportName = $('input#reportName').val();
	var employee = $('input#employee').val();

	if (reportName == 'Report Name' || reportName.length == 0) {
		$('input#reportName').addClass('invalid');
		isValid = false;
	} else {
		$('input#reportName').removeClass('invalid');
	}

	if (employee == 'Your Name' || employee.length == 0) {
		$('input#employee').addClass('invalid');
		isValid = false;
	} else {
		$('input#employee').removeClass('invalid');
	}

	$('.inputRow > td > input[name="description"]:enabled').each(function(idx,e){
		if ($(e).val().length < 3) {
			$(e).addClass('invalid');
			isValid = false;
		} else {
			$(e).removeClass('invalid');
		}
	});

	$('.inputRow > td > select:enabled').each(function(idx,e){
		if ($(e).val() == '') {
			$(e).addClass('invalid');
			isValid = false;
		} else {
			$(e).removeClass('invalid');
		}
	});


	$('.inputRow > td > input[name="amount"]:enabled').each(function(idx,e){
		var amt = parseMoney($(e).val());
		if (amt <= 0 || isNaN(amt)) {
			$(e).addClass('invalid');
			isValid = false;
		} else {
			$(e).removeClass('invalid');
		}
	});

	if (isValid && (getTotal() <= 0)) {
		isValid = false;
		$('#total').addClass('invalid');
	} else {
		$('#total').removeClass('invalid');
	}
	
	return isValid;
}

function imageZoom(img) {
	$(img).click(function(){
		var src = $(this).attr('src');
		$('#imageZoom > img').attr('src', src);
		$('#imageZoom > img').css('width', '700px');
		$('#zoom').show();
		$('#imageZoom').show();
	});
}
	

function handleReceiptUpload (response, statusText, xhr, form) {
	form.empty();
	$(form).css('background','none');
	var img = form.siblings('img')[0];
	imageZoom(img);
	$(img).attr("src", '/receipt/' + response['receipt_id'] + '/image');
	$(img).css("width", '50px');
	$(img).css("height", '50px');
	form.parent().parent().attr('receipt_id', response['receipt_id']);
}

function addRow() {
	var summary = $('.totalRow').clone();
	$('.totalRow').remove();

	var clone = emptyInputRow.clone();

	$('.inputRow:last > td > form.imageForm').css('background','url(/img/spinner.gif) 0 0 no-repeat');
	$('.inputRow:last > td > form.imageForm').ajaxSubmit(receiptUploadOptions);


	$('.inputRow:last > td > input').removeAttr('disabled');
	$('.inputRow:last > td > select').removeAttr('disabled');

	$(clone).css('display', 'none');

	$(clone).appendTo('table');
	$('.inputRow:last > td > input').val('');
	$('.inputRow:last > td > form > input').val('');

	$('.inputRow:last > td > form > input:file').change(addRow);
	$('.inputRow:last > td > form.imageForm').ajaxForm();

	summary.appendTo('table');
	$('.inputRow:last > td > input[name="amount"]').keyup(calcTotal);

	$(clone).fadeIn(1000);
}

function saveReport() {
	var reportName = $('input#reportName').val();
	var employee = $('input#employee').val();


	if (reportName == 'Report Name' || reportName.length == 0) {
		reportName = '';
	}

	if (employee == 'Your Name' || employee.length == 0) {
		employee = '';
	}

	var receipts = [];

	$('.inputRow').each(function(idx,e) {
		var receipt_id = $(e).attr('receipt_id');
		if (receipt_id != undefined) {
			var amount = $(e).find('input[name="amount"]').val();
			var description = $(e).find('input[name="description"]').val();
			var category = $(e).find('select').val();
			receipts.push({receipt_id: receipt_id, category: category, amount: amount, description: description});
		}
	});

	var report = {reportName: reportName, employee: employee, receipts: receipts};

	$.post(window.location.pathname + '.json', {report: JSON.stringify(report)});
}

function disableReportInputs() {
	$('.inputRow').find('input').each(function(idx,e){
		$(e).attr('disabled', 'true');
	});
	$('.inputRow').find('select').each(function(idx,e){
		$(e).attr('disabled', 'true');
	});
	$('#reportName').attr('disabled','true');
	$('#employee').attr('disabled','true');
}

function submitReport() {
	if (!validate()) return;
	saveReport();
	disableReportInputs();
	$.post(window.location.pathname + '/submit', function() {
		$('#save').fadeOut(function(){
			$('#finishedReport').fadeIn();
		});	
	});
}

function createReceipt(receipt_id, category, description, amount) {
	var clone = emptyInputRow.clone();
	$(clone).attr('receipt_id', receipt_id);
	$(clone).find('input[name="amount"]').val(amount);
	$(clone).find('input[name="amount"]').removeAttr('disabled');
	$(clone).find('input[name="description"]').val(description);
	$(clone).find('input[name="description"]').removeAttr('disabled');
	$(clone).find('select').val(category);
	$(clone).find('select').removeAttr('disabled');
	$(clone).find('input:file').remove();
	$(clone).find('.imageForm').css('background','none');
	var img = $(clone).find('img');
	img.attr("src", '/receipt/' + receipt_id + '/image');
	img.css("width", '50px');
	img.css("height", '50px');
	imageZoom(img);
	$(clone).appendTo('table');
}


function loadReport(data) {
	var details = $.parseJSON(data);
	var submitted = false;
	if (details['submitted'] != 'No') submitted = true;

	if (details['reportName'] != '') {
		$('input#reportName').val(details['reportName']);
		if (submitted) $('input#reportName').attr('disabled', 'true');
		$('#reportName_placeholder').hide();
	}
	if (details['employee'] != '') {
		$('input#employee').val(details['employee']);
		if (submitted) $('input#employee').attr('disabled', 'true');
		$('#employee_placeholder').hide();
	}
	$('li#reimbursed > span').text(details['reimbursed']);
	if (details['reimbursed'] != 'No') $('#reimburse').hide();

	var total = $('.totalRow').clone();
	$('.totalRow').remove();

	var receipts = details['receipts'];
	for (r in details['receipts']) {
		createReceipt(receipts[r]['receipt_id'], receipts[r]['category'], receipts[r]['description'], receipts[r]['amount']);
	}
	
	$('.inputRow > td > input[name="amount"]').keyup(calcTotal);
	
	if (submitted) {
		disableReportInputs();
		$('#save').remove();
		$('#finishedReport').show();
	} else {
		var clone = emptyInputRow.clone();
		$(clone).appendTo('table');
		$('.inputRow:last > td > form > input:file').change(addRow);
	}

	$(total).appendTo('table');
	calcTotal();	
}

function collect () {
	var curl = $('input[name="url"]').val();
	var report_id = window.location.pathname.split('/').pop();
	$.post(curl + '/add/' + report_id);
}	

function reimburse () {
	$.post(window.location.pathname + '/reimburse', function (){
		$.get(window.location.pathname + '.json', loadReport);
	});
}

jQuery(document).ready(function() {

	$('.inputRow:last > td > form.imageForm').ajaxForm();
	$('.inputRow:last > td > form > input:file').change(addRow);
	$('.inputRow > td > input[name="amount"]').keyup(calcTotal);
	$('.inputRow > td > input[name="amount"]').change(calcTotal);
	emptyInputRow = $('.inputRow:last').clone();
	$('.inputRow:last').remove();

	$('input[placeholder],textarea[placeholder]').placeholder();
	$('#reportName').focus();
	$('#reportName').keypress(function(){
		$('#reportName_placeholder').hide();
	});

	$('#reportName').change(saveReport);	
	$('#employee').change(saveReport);	

	SI.Files.stylizeAll();

	$.get(window.location.pathname + '.json', loadReport);

	$('#imageZoom').click(function(){
		$('#zoom').hide();
		$('#imageZoom').hide();
	});

	$('#save').click(submitReport);
	$('#reimburse').click(reimburse);
	$('#collect').click(collect);
})

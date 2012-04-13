var fetchGlobalData = function() {
    // called when the global date range changes
    var inputFrom = $('#from'),
        inputTo = $('#to');

    if (!validateInput(inputFrom, inputTo)) {
        return;
    }

    url = '/machines/?from=' + inputFrom.val() + '&to=' + inputTo.val();
    $.getJSON(url, populateTable);
},
validateInput = function() {
    // return true if input contains valid YYYY-MM-DD.HH
    // accepts any number of jquery matched form elements and
    // validates each seperately. If an item does not validate
    // it is given the error class.
    var re = /^\d{4}-\d{2}-\d{2}\.\d{2}$/,
        match;

    valid = true;
    for (var i = 0, j = arguments.length; i < j; i++) {
        elem = arguments[i];
        elem.removeClass('error');
        if (!re.exec(elem.val())) {
            elem.addClass('error');
            valid = false;
        }
    }
    return valid;
},
populateTable = function(data) {
    table.fnClearTable();
    table.fnAddData(data['machines']);
    table.fnAdjustColumnSizing();
},
fnFilterColumn = function(i) {
    table.fnFilter($('#col' + (i + 1) + '_filter').val(), i, true, true);
}

// extend dataTables to use bootstrap classes
$.extend( $.fn.dataTableExt.oStdClasses, {
    "sWrapper": "dataTables_wrapper form-inline"
} );

// set up the data table
window['table'] = $('#dataTable').dataTable({
    'sDom': 'rt<"row"<"span6"l><"span6"pi>>',
    'sPaginationType': 'bootstrap',
    'aoColumns': [
        { 'sTitle': 'Time', "mDataProp":  'datetime'},
        { 'sTitle': 'Name', "mDataProp":  'name'},
        { 'sTitle': 'Scheduler', "mDataProp":  'scheduler'},
        { 'sTitle': 'Master', "mDataProp":  'master'},
        { 'sTitle': 'Platform', "mDataProp":  'platform'},
        { 'sTitle': 'Successes', "mDataProp":  'successes'},
        { 'sTitle': 'Failures', "mDataProp":  'failures'},
    ],
})

// register input listener
$('header input').on('input', fetchGlobalData);
// prevent form submission
$('#dateform').submit(function() { return false; });
// prefill date range selector with today's date
(function(d) {
    var pad = function(n) {
        return n < 10 ? '0' + n : n;
    },
    formatDate = function(date) {
        return date.getUTCFullYear() + '-'
            + pad(date.getUTCMonth()+1) + '-'
            + pad(date.getUTCDate()) + '.'
            + pad(date.getUTCHours())
    };
    $('#to').val(formatDate(d));
    d.setDate(d.getDate() - 1)
    $('#from').val(formatDate(d));
}(new Date()));
$('#to').trigger('input');

// column regex's
$('thead').append('<tr id="inputs"></tr>');
$('th').each(function(index, Element) {
    $('#inputs').append(function() {
        return  '<th rowspan="1" colspan="1">'
                + '<input class="column_filter" type="text" name="col'
                + index + '" id="col' + (index + 1) + '_filter"'
                + 'placeholder="optional regex">'
                + '</th>';
    });
})
$('.column_filter').each(function(i, e) {
    $(e).keyup(function() {
        fnFilterColumn(i);
    });
});

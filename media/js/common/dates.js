var fetchGlobalData = function() {
    // called when the global date range changes
    var inputFrom = $('#from'),
        inputTo = $('#to');

    if (!validateInput(inputFrom, inputTo)) {
        console.log('fail');
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
    console.log(data);
}

// register input listener
$('header input').on('input', fetchGlobalData);
// prevent form submission
$('#dateform').submit(function() { return false; });
// prefill with valid date
(function(d){
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

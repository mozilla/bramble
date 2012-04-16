var fetchGlobalData = function() {
    // called when the global date range changes
    var inputFrom = $('#from'),
        inputTo = $('#to');

    if (!validateInput(inputFrom, inputTo)) {
        return;
    }

    $('#spinner h3').text('Loading...');
    $('#spinner')
        .css({'background-color': 'rgba(255,255,255,0.65)', 'color': '#000'})
        .fadeIn();
    url = '/machines/?from=' + inputFrom.val() + '&to=' + inputTo.val();
    $.getJSON(url, populateTable).error(function() {
        $('#spinner h3').text('Error :(');
        $('#spinner')
            .css({'background-color': 'rgba(255,0,0,0.65)', 'color': '#ffffff'});
    });
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
    updateChart();
    $('#spinner').fadeOut();
},
fnFilterColumn = function(i) {
    table.fnFilter($('#col' + (i + 1) + '_filter').val(), i, true, true);
    updateChart();
},
updateChart = function() {
    var parseDate = function(d) {
            // accepts a YYYY-MM-DD.HH formatted date and returns a JS Date
            var parsed = /^(\d{4})-(\d{2})-(\d{2})\.(\d{2})$/.exec(d);
            if (!parsed) {
                throw "Invalid date string";
            }
            return new Date(parsed[1], parsed[2], parsed[3], parsed[4]);
        },
        // graph options
        options = {
            xaxis: {
                mode: 'time',
                timeformat: '%b %d %H:%M',
                minTickSize: [3, 'hour'],
            },
            yaxis: {
                min: 0,
            },
            series: {
                bars: {
                    show: true,
                    barWidth: 45 * 60 * 1000,
                    lineWidth: 0,
                    fill: .7,
                },
                shadowSize: 0,
            },
            colors: ['#1FE127',  // working
                     '#FF0000',  // error
                     '#B4BCBD'], // idle
            grid: {
                clickable: true,
                hoverable: true,
                borderWidth: 0,
                autoHighlight: false, // callback manuall highlights
            },
            legend: {
                noColumns: 3, // force a flat legend
            }
        },
        reshapedData = _.chain(table.fnGetFilteredData())
            .groupBy(function(element) {
                if (element.failures > 0) {
                    return 'error';
                }
                if (element.successes > 0) {
                    return "working";
                }
                return "idle";
            }).map(function(rows, type){
                var aggregatedRows = _.groupBy(rows, 'datetime'),
                    aggregatedCounts = _.map(aggregatedRows, function(v, k) {
                        return [parseDate(k), v.length];
                    });
                return {label: type,
                        stack: true,
                        data: _.sortBy(aggregatedCounts, '0')};
            }).sortBy(function(elem){
                // hack -- flot stacks by the order you pass things in, so the
                // first array is the base, the second is the middle, the third
                // is on top. We rig this sort to order things correctly
                if (elem.label === "working") {
                    return 0;
                }
                if (elem.label === "error") {
                    return 1;
                }
                return 2;
            })
            .value();
    $.plot($('#machinestatus'), reshapedData, options);
};

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
$('header input').on('input', _.debounce(fetchGlobalData, 500));
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
    d = new Date(d - 60*60*1000*24*1); // 1 days of data by default
    $('#from').val(formatDate(d));
}(new Date(new Date() - 60*60*1000*24))); // pacific offset from utc
$('#to').trigger('input');

// column regular expression filters
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
    $(e).keyup(_.debounce(function() {
        fnFilterColumn(i);
    }, 500));
});

// loading element
$('.container').prepend('<div id="spinner"><h3>Loading...</h3></div>');

 var populateMachineStatusGraph = function(d) {
    // graph options passed to flot
    var data = d['dates'],
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
            stack: true,
            bars: {
                show: true,
                barWidth: 45 * 60 * 1000, // 20 hrs in ms
                                               // remaining 4 are padding
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
    };

    // reshape the data
    // {date: currentDate, working: 32, idle: 5, error: 20} ->
    // [{label: 'error', data: err}, {label: 'idle', data: idle }, etc..]
    var working = [], idle =[], error = [];
    data.map(function(d) {
        working.push([(new Date(d.date)).getTime(), +d.working]);
        idle.push([(new Date(d.date)).getTime(), +d.idle]);
        error.push([(new Date(d.date)).getTime(), +d.error]);
    });
    var reshapedData = [
        {label: 'working', data: working},
        {label: 'error', data: error},
        {label: 'idle', data: idle},
    ];

    // make plot available for other callbacks
    window['plot'] = $.plot($('#machinestatus'), reshapedData, options);
},
// accepts data from a json call to the machinecounts/specifics endpoint
// and uses it to populate a data table beneath the machine status graph
supplementalTable = function(d) {
    var data = d['machines'],
        aaData = [],
        i, j, key, machines;

    console.log(data);
    for (key in data) {
        machines = data[key];
        for (i = 0, j = machines.length; i < j; i++) {
            aaData.push([machines[i], key]);
        }
    }

    $('#supplemental-info').empty()
        .append('<table class="table table-striped"></table>');
    $('#supplemental-info table').dataTable({
        'aaData': aaData,
        'aoColumns': [{'sTitle': 'Name'}, {'sTitle': 'Status'}],
    });
    // style the new elements
    $('#DataTables_Table_0_length').addClass('span4');
    $('#DataTables_Table_0_filter').addClass('span4');
    $('#DataTables_Table_0').addClass('span12');
},
// custom highlight event handler that highlights the whole column
// instead of just one data category in the column
highlightColumn = function(event, pos, item) {
    plot.unhighlight();
    if (!item) return;

    index = item['dataIndex'];
    plot.getData().map(function(d) { plot.highlight(d, index); });
},
// populates supplemental data section with detailed information for
// the time of the column, if a column was indeed clicked
drillDown = function(event, pos, item) {
    if (!item) return;

    $.getJSON('/machinecounts/specifics/',
              {when: item['datapoint'][0]},
              supplementalTable);
};

$.getJSON('/machinecounts/',{bars: 21}, populateMachineStatusGraph);

// bind event listeners for plot events
$('#machinestatus')
    .bind('plotclick', drillDown)
    .bind('plothover', highlightColumn);

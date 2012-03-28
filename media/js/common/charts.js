$.getJSON('/machinecounts/',{bars: 21}, function(d) {
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
        colors: ['#FF0000',  // error
                 '#B4BCBD',  // idle
                 '#1FE127'], // working
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
        {label: 'error', data: error},
        {label: 'idle', data: idle},
        {label: 'working', data: working},
    ];

    // plot the chart and let plot be hoisted as a global
    plot = $.plot($('#machinestatus'), reshapedData, options);
})

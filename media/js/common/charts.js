// data generator
// will be replaced when the appropriate api endpoint is implemented
var fakeData = (function(howMany) {
    var dates = [],
        currentDate = new Date(),
        newDate;
    for (var i = 0; i < howMany; i++) {
        newDate = new Date();
        newDate.setDate(currentDate.getDate() - 1);
        dates.push({date: newDate,
                    working: Math.round(Math.random() * 30) + 50,
                    idle: Math.round(Math.random() * 20) + 2,
                    error: Math.round(Math.random() * 10) + 4});
        currentDate = newDate;
    }
    return dates;
}(21));

// Machine Status Graph
(function(data) {
    var options = {
        xaxis: {
            mode: 'time',
            timeformat: '%b %d',
            minTickSize: [1, 'day'],
        },
        yaxis: {
            min: 0,
        },
        series: {
            stack: true,
            bars: {
                show: true,
                barWidth: 20 * 60 * 60 * 1000, // 20 hrs in ms, 4 hrs for padding
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
            autoHighlight: false,
        },
        highlight: {
            opacity: 1,
        },
        legend: {
            noColumns: 3,
        }
    };

    // reshape the data
    // {date: currentDate, working: 32, idle: 5, error: 20} ->
    // [{label: 'error', data: err}, {label: 'idle', data: idle }, etc..]
    var working = [], idle =[], error = [];
    data.map(function(d) {
        working.push([d.date.getTime(), +d.working]);
        idle.push([d.date.getTime(), +d.idle]);
        error.push([d.date.getTime(), +d.error]);
    });
    reshapedData = [
        {label: 'error', data: error},
        {label: 'idle', data: idle},
        {label: 'working', data: working},
    ];

    plot = $.plot($('#machinestatus'), reshapedData, options);

    // highlight on hover
    // and populate the list below
    (function(i) {
        var dates = {},
            callback = function(event, pos, item) {
                if (!item) return;

                plot.unhighlight();
                index = item['dataIndex'];
                plot.getData().map(function(d, i) {plot.highlight(d, index);});
                (function(date) {
                    var pad = function(n) { return n < 10 ? '0' + n : n},
                        url = "/builds/?date="
                            + date.getUTCFullYear() + '-'
                            + pad((date.getUTCMonth() + 1)) + '-'
                            + pad(date.getUTCDate()) + '&hour='
                            + pad(date.getUTCHours()),
                        supplement = function(data) {
                            if (!data) return;
                            $('#supplemental-info h3').text('UID\'s for ' + date.toDateString());
                            $('#supplemental-info ul').empty();
                            $.each(data.map(function(d) { return "<li>" + d['uid'] + "</li>";}),
                                function(i, e) { $('#supplemental-info ul').append(e); }
                            );
                        }

                    if (date in dates) {
                        supplement(dates[date]);
                        return;
                    }

                    $.getJSON(url, function(d) {
                        dates[date] = d;
                        supplement(d);
                    });
                }(new Date(item['datapoint'][0])));
            };
        if (i) {
            callback(null, null, i); // prime the drilldown function
        }
        $("#machinestatus").bind("plothover", callback); //listen for events
    }({dataIndex: 0, datapoint: [new Date()] })); //pass in a mock graph event item
}(fakeData));

/*
// returns an xhr for builds on the provided date
var fetchBuilds = function(date) {
    var pad = function(n) { return n < 10 ? '0' + n : n},
    url = "/builds/?date="
        + date.getUTCFullYear() + '-'
        + pad((date.getUTCMonth() + 1)) + '-'
        + pad(date.getUTCDate()) // + '&hour='
        //+ pad(date.getUTCHours());
    return $.getJSON(url);
},
// returns a deferred for jobs involved in the provided builds
fetchJobs = function(buildResponse) {
    console.log('fetchJobs');
    console.log(buildResponse);
    deferreds = buildResponse.map(function(build) {
        uid = build['uid'];
        if (uid === 'None') return;
        newUrl = '/builds/' + uid + '/jobs';
        return $.getJSON(newUrl);
    });
    return $.when.apply(null, deferreds);
},
// returns a deferred deferred for the job details of the provided job uids
fetchJobDetails = function(data) {
    console.log('fetch job details');
    console.log(data);
    deferreds = data.map(function(datum) {
        uid = datum['uid'];
        master = datum['master'];
        buildNumber = datum['build_number'];
        newURL = '/jobs/' + uid + '/' + master + '/' + buildNumber;
        return $.getJSON(newUrl);
    });
    return $.when.apply(null, deferreds);
},
displayJobs = function(data) {
    console.log('displayJobs');
    console.log(data);
};
fetchBuilds().then(fetchJobs).then(fetchJobDetails).then(displayJobs); */

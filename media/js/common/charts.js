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

// accepts events from the plothover and plotclick and if the mouse is over a
// column, resets the highlight to the column and calls the method cascade to
// populate supplemental information table
//
// requires plot and populateSupplemetalData functions in parent scope
// intended to be registered as a callback in the event listener
var highlightColumn = function(event, pos, item) {
    if (!item) return;

    plot.unhighlight();
    index = item['dataIndex'];
    plot.getData().map(function(d) { plot.highlight(d, index); });

    populateSupplementalData(new Date(item['datapoint'][0]));
},
// given a date, this populates the suppelemental data table
// beneath the machine status graph
populateSupplementalData = function(date) {
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

    // this won't do at all
    // .then() is passing the right stuff, but I'm not sure that returning
    // a deferred is doing what I think it is. Maybe we neext $.when() here?
    // that would be ok.
    //
    // ALSO -- memoize all the things, don't respond to the same item if the
    // mouse pos is a little different
    fetchBuilds(date).then(fetchJobs).then(fetchJobDetails).then(displayJobs);
};

// Machine Status Graph
(function(data) {
    // graph options passed to flot
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
                barWidth: 20 * 60 * 60 * 1000, // 20 hrs in ms
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
        working.push([d.date.getTime(), +d.working]);
        idle.push([d.date.getTime(), +d.idle]);
        error.push([d.date.getTime(), +d.error]);
    });
    var reshapedData = [
        {label: 'error', data: error},
        {label: 'idle', data: idle},
        {label: 'working', data: working},
    ];

    // plot the chart and let plot be hoisted as a global
    plot = $.plot($('#machinestatus'), reshapedData, options);

    // prime the callback with a mock object
    highlightColumn(null, null, {dataIndex: 0, datapoint: [new Date()] });

    // register the callback as a listener for mouse interactions
    $("#machinestatus").bind("plothover", highlightColumn);
}(fakeData));

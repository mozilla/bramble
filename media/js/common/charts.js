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

//function() {
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
                fill: .8,
            },
            shadowSize: 0,
        },
        colors: ['#FF0000',  // error
                 '#B4BCBD',  // idle
                 '#1FE127'], // working
        grid: {
            clickable: true,
            borderWidth: 0,
        },
        legend: {
            noColumns: 3,
        }
    };

    // reshape the data
    // {date: currentDate, working: 32, idle: 5, error: 20}
    var working = [], idle =[], error = [];
    fakeData.map(function(d) {
        working.push([d.date.getTime(), +d.working]);
        idle.push([d.date.getTime(), +d.idle]);
        error.push([d.date.getTime(), +d.error]);
    })
    reshapedData = [
        {label: 'error', data: error},
        {label: 'idle', data: idle},
        {label: 'working', data: working},
    ];

    $.plot($('#machinestatus'), reshapedData, options);
//}

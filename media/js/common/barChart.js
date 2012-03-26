var barChart = function() {
    var width = 720,
        height = 80;

    function chart(selection) {
        selection.each(function(d, i) {
            // data
        });
    };

    chart.width = function(value) {
        if (!arguments.length) return width;
        width = value;
        return chart;
    };

    chart.height = function(value) {
        if (!arguments.length) return width;
        height = value;
        return chart;
    };

    return chart;
};

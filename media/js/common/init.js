//(function() {
    /**
     * Returns the number as a string, with 0 prepended to ensure it is at
     * least two digits long
     *
     * @param {number or string} n      the number to pad
     */
    var pad = function(n) {
        n = "" + n;
        return n < 10 ? '0' + n: n;
    }

    /**
     * Returns a string representation of the provided date in YYYY-MM-DD
     * format
     *
     * @param {Date} d          the date object
     *
     * @returns {string} formatted string version of the date
     */
     var redisDateString = function(d) {
        return d.getUTCFullYear() + "-"
            + pad(d.getUTCMonth() + 1) + "-"
            + pad(d.getUTCDate());
    }

    /**
     * Returns a string representation of the hours of the provided date in HH
     * format
     *
     * @param {Date} d          the date object
     *
     * @returns {string} the formatted string of the date's hours attribute
     */
    var redisHourString = function(d) {
        return pad(d.getUTCHours());
    }

    //////
    // build graph

    var weekOfRedisDates = (function(howMany) {
        dates = [];
        currentDate = new Date();
        for(var i = 0; i < howMany; i++) {
            dates.push(redisDateString(currentDate));
            currentDate.setDate(currentDate.getDate() - 1);
        }
        return dates;
    }(7));

    var data = [];
    var pointer = -1;
    var recursiveFetch = function() {
        if (arguments.length) {
            count = arguments[0].length
            date = weekOfRedisDates[pointer];
            data.push({count: count, date: date});
        } else {
            if (pointer > -1) {
                data.push([]);
            }
        }
        pointer += 1;
        if (pointer >= weekOfRedisDates.length) {
            renderBuildGraph();
            return;
        }
        d3.json('/builds/?date=' + weekOfRedisDates[pointer], recursiveFetch);
    };

    recursiveFetch();
    var renderBuildGraph = function() {
        var width = 700,
            height = 300,
            x = d3.scale.linear().range([0, width]),
            y = d3.scale.linear().range([0, height - 40]);
                //.domain([0, d3.max(data.map(function(arr) {return arr.length;}))])

        // an SVG element with a bottom-right origin
        var svg = d3.select('#buildgraph').append('svg')
            .attr('width', width)
            .attr('height', height)
            .style('padding-right', '30px')
          .append('g')
            .attr('transform',
                  'translate(' + x(1) + ',' + (height - 20) + ')scale(-1,-1)');

        var body = svg.append('g')
            .attr('transform', 'translate(0,0)');

        var rules = svg.append('g');

        var title = svg.append('text')
            .attr('class', 'title')
            .attr('dy', '.71em')
            .attr('transform',
                  'translate(' + x(1) + ',' + y(1) + ')scale(-1,-1)')
            .text("Daily Build Count");

        ////

        var date0 = d3.min(data, function(d) { return d.date; }),
            date1 = d3.max(data, function(d) { return d.date; }),
            builds0 = d3.min(data, function(d) { return d.count; });
            builds1 = d3.max(data, function(d) { return d.count; });

        x.domain([0, date1 + 5]); // offset the scale
        y.domain([0, builds1]);

        rules = rules.selectAll('.rule')
            .data(y.ticks(5))
          .enter().append('g')
            .attr('class', 'rule')
            .attr('transform', function(d) { return 'translate(0,' + y(d) + ')'; });

        rules.append('line')
            .attr('x2', width);

        rules.append('text')
            .attr('x', 6)
            .attr('dy', '.35em')
            .attr('transform', 'rotate(180)')
            .text(function(d) { return Math.round(d / 1e6) + "M"; });

        var dates = body.selectAll('g')
            .data(d3.range(date0 - date1, 1, 1))
          .enter().append('g')
            .attr('transform',
                  function(d) { return 'translate(' + x(date1 - d) + ",0)"; });

        dates.selectAll('rect')
            .data(d3.range(2))
          .enter().append('rect')
            .attr('x', 1)
            .attr('width', x(5) - 2)
            .attr('height', 1e-6);

        dates.append('text')
            .attr('y', -6)
            .attr('x', -x(5) / 2)
            .attr('transform', 'rotate(180)')
            .attr('text-anchor', 'middle')
            .attr('fill', '#fff')
            .text(String);

        // labels under the graph
        svg.append('g').selectAll('text')
            .data(d3.range(0, date1, 1))
          .enter().append('text')
            .attr('text-anchor', 'middle')
            .attr('transform',
                  function(d) { return 'translate(' + (x(d) + x(5) / 2) + ',-4)scale(-1,-1)'; })
            .attr('dy', '.71em')
            .text(String)

        // TODO interaction. allow arrow keys to move data window
        /*
        d3.select(window).on('keydown', function() {
            switch(d3.event.keyCode) {
                case 37: //Math.max(date0, date - 1) break;
                case 39: //Math.min(date1, date + 1); break;
            }
            redraw();
        });
        */

        redraw();

        function redraw() {
            //if (!(date in data)) return;
            //title.text(date);

            body.transition()
                .duration(750)
                .attr('transform',
                      function(d, i) { return 'translate(' + x(7 - i) + ',0)'; });

            dates.selectAll('rect')
                .data(data)
              .enter().append("rect");
            /*
              .transition()
                .duration(750)
                .attr('height', y); */
        };

        /**
            chart.selectAll('rect')
                .data(data)
              .enter().append('rect')
                .attr('x', function(d, i) { return x(i) - .5;  })
                .attr('y', function(d, i) { return height - y(d.length) - .5; })
                .attr('width', barWidth)
                .attr('height', barHeight);

            chart.append("line")
                .attr('x1', 0)
                .attr('x2', width)
                .attr('y1', height - 0.5)
                .attr('y2', height - 0.5);

            chart.selectAll('line')
                .data(y.ticks(5))
              .enter().append('line')
                .attr('x1', 0)
                .attr('x2', width)
                .attr('y1', function(v) { return height - y(v); })
                .attr('y2', function(v) { return height - y(v); })
                .style('stroke', '#ccc');

            chart.selectAll('.rule')
                .data(y.ticks(5))
              .enter().append('text')
                .attr('class', 'rule')
                .attr('x', width - 30)
                .attr('y', function(v) { return height - y(v); })
                .attr('text-anchor', 'left')
                .text(String);
        */
    };
//}());

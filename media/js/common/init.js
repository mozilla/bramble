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

    ////////

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
    var callBackHell = function() {
        console.log(arguments.length);
        if (arguments.length) data.push(arguments[0]);
        pointer+=1;
        if (pointer >= weekOfRedisDates.length) {
            console.log(data);
            return;
        }
        d3.json('/builds/?date=' + weekOfRedisDates[pointer], callBackHell());
    };

    callBackHell();

//}());
/**
function(data) {
            count = data.length;
            d3.select("#buildcount")
                .append('')

            //    .datum(data)
            //    .call(barChart());
        });
*/

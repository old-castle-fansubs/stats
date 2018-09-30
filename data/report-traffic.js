var parseTime = d3.timeParse('%Y-%m-%d');
data.forEach(function(d) {
  d.day = parseTime(d.day);
});
data.sort(function(a, b) {
  return a.day - b.day;
});


window.addEventListener('DOMContentLoaded', function () {
    var margin = {top: 10, right: 10, bottom: 20, left: 50};
    var outerWidth = 700;
    var outerHeight = 300;
    var innerWidth = outerWidth - margin.left - margin.right;
    var innerHeight = outerHeight - margin.top - margin.bottom;

    var x = d3.scaleTime()
        .range([0, innerWidth])
        .domain(d3.extent(data, function(d) { return d.day; }));
    var y = d3.scaleLinear()
        .range([innerHeight, 0])
        .domain([
            0,
            d3.max(data, function(d) {
                return Math.max(d.hits, d.views);
            })
        ])
        .nice();

    var svg = d3
        .select('.traffic>.target')
        .classed('svg-container', true)
        .append('svg')
        .attr('preserveAspectRatio', 'xMinYMin meet')
        .attr('viewBox', `0 0 ${outerWidth} ${outerHeight}`)
        .append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);

    // grid
    svg.append('g')
        .attr('class', 'grid')
        .attr('transform', `translate(0,${innerHeight})`)
        .call(d3.axisBottom(x)
            .ticks(d3.timeMonth.every(1))
            .tickSize(-innerHeight)
            .tickFormat('')
        )
    svg.append('g')
        .attr('class', 'grid')
        .call(d3.axisLeft(y)
            .tickSize(-innerWidth)
            .tickFormat('')
        )

    // areas
    svg.append('path')
        .data([data])
        .attr('class', 'area hits')
        .attr(
            'd',
            d3.area()
            .x(function(d) { return x(d.day); })
            .y0(innerHeight)
            .y1(function(d) { return y(d.hits); })
        );
    svg.append('path')
        .data([data])
        .attr('class', 'area views')
        .attr(
            'd',
            d3.area()
            .x(function(d) { return x(d.day); })
            .y0(innerHeight)
            .y1(function(d) { return y(d.views); })
        );

    // lines
    svg.append('path')
        .data([data])
        .attr('class', 'line hits')
        .attr(
            'd',
            d3.line()
            .x(function(d) { return x(d.day); })
            .y(function(d) { return y(d.hits); })
        );
    svg.append('path')
        .data([data])
        .attr('class', 'line views')
        .attr(
            'd',
            d3.line()
            .x(function(d) { return x(d.day); })
            .y(function(d) { return y(d.views); })
        );

    // average lines
    svg.append('path')
        .data([data])
        .attr('class', 'line hits-avg')
        .attr(
            'd',
            d3.line()
            .x(function(d) { return x(d.day); })
            .y(function(d) { return y(d.hits_avg); })
        );
    svg.append('path')
        .data([data])
        .attr('class', 'line views-avg')
        .attr(
            'd',
            d3.line()
            .x(function(d) { return x(d.day); })
            .y(function(d) { return y(d.views_avg); })
        );

    // axes
    svg.append('g')
        .attr('transform', `translate(0,${innerHeight})`)
        .call(
            d3.axisBottom(x)
            .ticks(d3.timeMonth.every(3))
        );
    svg.append('g')
        .call(d3.axisLeft(y));
});

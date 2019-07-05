var parseTime = d3.timeParse('%Y-%m-%d');
hits.forEach(d => d.day = parseTime(d.day));
downloads.forEach(d => d.day = parseTime(d.day));


window.addEventListener('DOMContentLoaded', () => {
    var margin = {top: 10, right: 10, bottom: 20, left: 50};
    var outerWidth = 800;
    var outerHeight = 300;
    var innerWidth = outerWidth - margin.left - margin.right;
    var innerHeight = outerHeight - margin.top - margin.bottom;

    var x = d3.scaleTime()
        .range([0, innerWidth])
        .domain(d3.extent(hits.concat(downloads), d => d.day));
    var y = d3.scaleLinear()
        .range([innerHeight, 0])
        .domain([
            0,
            d3.max([...hits, ...downloads], d => Math.min(2000, d.diff))
        ])
        .nice();

    var svg = d3
        .select('.daily-stats>.target')
        .classed('svg-container', true)
        .append('svg')
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

    for (const chart of [
        {data: hits, className: 'hits'},
        {data: downloads, className: 'downloads'},
    ]) {
        // areas
        svg.append('path')
            .data([chart.data])
            .attr('class', `area ${chart.className}`)
            .attr(
                'd',
                d3.area()
                .x(d => x(d.day))
                .y0(innerHeight)
                .y1(d => y(d.diff))
            );

        // lines
        svg.append('path')
            .data([chart.data])
            .attr('class', `line ${chart.className}`)
            .attr(
                'd',
                d3.line()
                .x(d => x(d.day))
                .y(d => y(d.diff))
            );

        // average lines
        svg.append('path')
            .data([chart.data])
            .attr('class', `line ${chart.className}-avg`)
            .attr(
                'd',
                d3.line()
                .x(d => x(d.day))
                .y(d => y(d.diff_avg))
            );
    }

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

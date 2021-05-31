const parseTime = d3.timeParse('%Y-%m-%d');
const pageViews = rawData.pageViews.map(stat => ({
  day: parseTime(stat.day),
  value: stat.requests,
}));
const anidexDownloads = Object.entries(rawData.anidexDownloads).map(([day, value]) => ({
  day: parseTime(day),
  value: value,
}));
const nyaaSiDownloads = Object.entries(rawData.nyaaSiDownloads).map(([day, value]) => ({
  day: parseTime(day),
  value: value,
}));

const allData = [...pageViews, ...anidexDownloads, ...nyaaSiDownloads];

window.addEventListener('DOMContentLoaded', () => {
    const margin = {top: 10, right: 10, bottom: 20, left: 50};
    const outerWidth = 800;
    const outerHeight = 300;
    const innerWidth = outerWidth - margin.left - margin.right;
    const innerHeight = outerHeight - margin.top - margin.bottom;

    const x = d3.scaleTime()
        .range([0, innerWidth])
        .domain(d3.extent(allData, d => d.day));
    const y = d3.scaleLinear()
        .range([innerHeight, 0])
        .domain([0, d3.max(allData, d => d.value)])
        .nice();

    const svg = d3
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
        );
    svg.append('g')
        .attr('class', 'grid')
        .call(d3.axisLeft(y)
            .tickSize(-innerWidth)
            .tickFormat('')
        );

    const series = [
        {data: pageViews, title: 'Website views', className: 'page-views'},
        {data: anidexDownloads, title: 'Anidex downloads', className: 'anidex-downloads'},
        {data: nyaaSiDownloads, title: 'Nyaa.si downloads', className: 'nyaa-si-downloads'},
    ];

    for (const chart of series) {
        // areas
        svg.append('path')
            .data([chart.data])
            .attr('class', `area ${chart.className}`)
            .attr(
                'd',
                d3.area()
                .x(d => x(d.day))
                .y0(innerHeight)
                .y1(d => y(d.value))
            );

        // lines
        svg.append('path')
            .data([chart.data])
            .attr('class', `line ${chart.className}`)
            .attr(
                'd',
                d3.line()
                .x(d => x(d.day))
                .y(d => y(d.value))
            );

        // average lines
        svg.append('path')
            .data([chart.data])
            .attr('class', `line ${chart.className}-avg`)
            .attr(
                'd',
                d3.line()
                .x(d => x(d.day))
                .y(d => y(d.value_avg))
            );
    }

    // legend
    const legendSquareSize = 12;
    const legendSquareSpacing = 8;
    const legendTextSpacing = 5;
    const legendPadding = 8;
    const legendX = 12;
    const legendY = 12;

    svg.append('rect')
        .attr('x', legendX)
        .attr('y', legendY)
        .attr('width', 115)
        .attr('height', 2 * legendPadding + legendSquareSize * series.length + legendSquareSpacing * (series.length - 1))
        .attr('class', 'legend-wrapper');

    svg.selectAll("legendSquares")
        .data(series)
        .enter()
        .append("rect")
        .attr("x", legendX + legendPadding)
        .attr("y", (d, i) => legendY + legendPadding + i * (legendSquareSize + legendSquareSpacing))
        .attr("width", legendSquareSize)
        .attr("height", legendSquareSize)
        .attr("class", d => `legend ${d.className}`);

    svg.selectAll("legendLabels")
        .data(series)
        .enter()
        .append("text")
        .attr("x", legendX + legendPadding + legendSquareSize + legendTextSpacing)
        .attr("y", (d, i) => legendY + legendPadding + i * (legendSquareSize + legendSquareSpacing) + (legendSquareSize / 2))
        .attr("class", d => `legend ${d.className}`)
        .text(d => d.title);

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

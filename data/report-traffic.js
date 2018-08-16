var parseTime = d3.timeParse('%Y-%m-%d');
data.forEach(function(d) {
  d.day = parseTime(d.day);
  d.hits = +d.hits;
  d.views = +d.views;
});
data.sort(function(a, b){
  return a.day - b.day;
});

var margin = {top: 20, right: 20, bottom: 30, left: 50};
var width = 700 - margin.left - margin.right;
var height = 400 - margin.top - margin.bottom;

var x = d3.scaleTime()
  .range([0, width])
  .domain(d3.extent(data, function(d) { return d.day; }));
var y = d3.scaleLinear()
  .range([height, 0])
  .domain([
    0,
    d3.max(data, function(d) {
      return Math.max(d.hits, d.views);
    })
  ])
  .nice();

var svg = d3
  .select('.traffic')
  .append('svg')
  .attr('width', width + margin.left + margin.right)
  .attr('height', height + margin.top + margin.bottom)
  .append('g')
  .attr('transform', `translate(${margin.left},${margin.top})`);

// grid
svg.append('g')
  .attr('class', 'grid')
  .attr('transform', `translate(0,${height})`)
  .call(d3.axisBottom(x)
    .ticks(d3.timeMonth.every(1))
    .tickSize(-height)
    .tickFormat('')
  )
svg.append('g')
  .attr('class', 'grid')
  .call(d3.axisLeft(y)
    .tickSize(-width)
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
    .y0(height)
    .y1(function(d) { return y(d.hits); })
  );
svg.append('path')
  .data([data])
  .attr('class', 'area views')
  .attr(
    'd',
    d3.area()
    .x(function(d) { return x(d.day); })
    .y0(height)
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

// axes
svg.append('g')
  .attr('transform', `translate(0,${height})`)
  .call(
    d3.axisBottom(x)
    .ticks(d3.timeMonth.every(3))
  );
svg.append('g')
  .call(d3.axisLeft(y));

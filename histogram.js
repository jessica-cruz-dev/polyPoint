/* 
 Some code borrowed from:
 https://github.com/frankcleary/mpg/blob/master/mpg.js 
*/

var Chart = function (opts) {

    // Constructor values
    this.data = []; // Initialize with no data
    this.element = opts.element; // Container for histogram
    this.bins = opts.bins; // Initializes bin width 
    this.color = "#bb3318" // 'Indian Red'

    // Create chart
    this.draw();
}

Chart.prototype.draw = function () {

    // Defining variables to be used for drawing
    this.padding = 20;
    this.height = 380;
    this.width = 700;

    // Set up parent element and SVG
    this.element.innerHTML = '';
    var svg = d3.select(this.element).append('svg');
    svg.attr('width', this.width + (2 * this.padding));
    svg.attr('height', this.height + (2 * this.padding));

    // Appending to a <g> element
    this.plot = svg.append('g')
        .attr("transform", "translate(" + this.padding + "," +
            this.padding + ")");

    // Create all scales and bins
    this.createXScale();
    this.generateHist(this.bins); 
    this.yScale = d3.scale.linear()
        .domain([0, 20])
        .range([this.height, 0]);

    // Display histogram
    this.drawHist(); 

    // Draw x-axis
    var xAxis = d3.svg.axis()
        .scale(this.xScale)
        .orient("bottom");

    // Append axis to <g> element
    this.plot.append("g")
        .attr("class", "x axis")
        .attr("transform", "translate(0," + this.height + ")")                 
        .call(xAxis)
        .selectAll("text")
        .attr("transform", "translate( 0 ," + -4 + ")");
  
    // Draw the bars
    this.plot.selectAll('rect')
        .style('fill', this.color);
}


Chart.prototype.createXScale = function () {

    // Build x axis
    this.xScale = d3.scale.linear()
        .domain(d3.extent([0,1]))
        .range([0, this.width]);
}

Chart.prototype.generateHist = function () {

    // Generate a histogram w/ uniformly-spaced bins.
    this.hist_data = d3.layout.histogram()
        .bins(this.xScale.ticks(this.bins))
        (this.data);
}

Chart.prototype.drawHist = function () {

    // Holds the counts of every element in array
    const counter = new Map([...new Set(this.data)].map(x =>
                    [x, this.data.filter(y => y === x).length]));              

    // Changes the y-scal according to max height of data
    if (counter.get(.5) > 20)
        upper_bound = counter.get(.5)
    else 
        upper_bound = 20

    // Sets up new Y Scale
     y = d3.scale.linear()
     .domain([0, upper_bound])
     .range([this.height, 0]);

    // Shorthand variables
    var h = this.height,
        w = this.width,
        x = this.xScale,
        //y = this.yScale,
        bin_width = 30;

    // Display y-axis counts as integers
    var formatCount = d3.format(",.0f");

    // Sets up all hist values
    var hist = this.plot.selectAll(".bar")
        .data(this.hist_data)

    // Performs all the cool D3 movement between data
    hist.transition()
        .attr("transform", function (d) {
            return "translate(" + x(d.x) +
                "," + y(d.y) + ")";
        })
        .each(function () {

            //update the bars
            d3.select(this).select("rect") 
                .transition()
                .attr("x", 1)
                .attr("width", bin_width - 1)
                .attr("height", function (d) { return h - y(d.y); })

            //update the text
            d3.select(this).select("text") 
                .transition()
                .attr("x", bin_width / 2)
                .attr("y", -14)
                .text(function (d) {
                    return d.y != 0 ?
                        formatCount(d.y) : "";
                });
        });

    // Draw all new values
    hist.enter().append("g")
        .attr("class", "bar")
        .attr("transform", function (d) {
            return "translate(" + x(d.x) +
                "," + y(d.y) + ")";
        })
        .each(function () {

            //draw the bars
            d3.select(this).append("rect") 
                .attr("x", 1)
                .attr("width", bin_width - 1)
                .attr("height", function (d) { return h - y(d.y); })

            //draw the text
            d3.select(this).append("text")
                .attr("dy", ".75em")
                .attr("y", -14)
                .attr("x", bin_width / 2)
                .attr("text-anchor", "middle")
                .attr("fill", "#fff;")
                .text(function (d) { return formatCount(d.y); });
        });

    hist.exit()
        .remove()
}

Chart.prototype.setData = function (newData) {

    // Prepares new data
    this.data = newData;
    this.generateHist(this.bins);
    this.drawHist();
}

/**************************************************************
 * task.js
 *
 * Requires:
 *     psiturk.js
 *     utils.js
 *
 * These variables are available thanks to the psiturk server
 * - condition: which group of num_conds are you in?
 * - counterbalance: which group of num_counters are you in?
 * - uniqueId
 * - adServerLoc
 * - mode
 *
 *************************************************************/

// Initalize psiturk object
var psiTurk = new PsiTurk(uniqueId, adServerLoc, mode);

// load any necessary pages
psiTurk.preloadPages([
    "instructions/instruct.html",
    "prequiz.html",
    "stage.html",
]);

// These pages will be given as instructions before the task
var instructionPages = [
    "instructions/instruct.html",
];

/*********************
 * LIBRARY FUNCTIONS *
 *********************/

var flip = function() {
    return (Math.floor(Math.random() * 2) == 0);
};

var buttonize = function(transition, fill, stroke) {
    transition
        .duration(150)
        .ease(d3.easeCubicOut)
        .attr('fill', fill)
        .attr('stroke', stroke);
};

var weighted_shuffle = function(xs, weights) {
    // taken from Weighted Random Sampling (2005; Efraimidis, Spirakis)
    // https://softwareengineering.stackexchange.com/questions/233541
    var order = _.sortBy(_.range(xs.length), x => -(Math.random() ** (1 / weights[x])));
    return _.map(order, x => xs[x]);
}

var make_seq = function(svg, word, width, height, x, y, r, sep, symbols, opacity = "ff", stroke = null, classname = null) {
    var colormap = make_colormap(symbols, opacity);
    var colors = word.split('').map(function(c){return colormap[c];});
    var gap = 3;
    var g = svg.append("g").attr("class",classname);

    // add the bounding box
    g.append("rect")
        .attr("x", x-gap)
        .attr("y", y-gap)
        .attr("width", width + 2*gap)
        .attr("height", height + 2*gap)
        .attr("stroke",stroke)
        .attr("stroke-width",1.0)
        .attr("fill","#ffffff")
        .attr("fill-opacity",0.1)
        .attr("rx",r + gap)
        .attr("ry",r + gap);
    // add the sequence itself
    g.selectAll("circle")
        .data(colors)
        .enter().append("circle")
        .style("pointer-events", "none")
        .attr("fill", function(d){return d;})
        .attr("cx", function(d,i){return x+(i*2*r)+r;})
        .attr("cy", y+r)
        .attr("r", r);
};


var forceFixRoot = function(x, y) {
    var root;

    function force(alpha) {
        root.vx = 0;
        root.vy = 0;
        root.x = x;
        root.y = y;
    }

    force.initialize = function(ns) {
        var roots = _.where(ns, {depth: 0});
        if (roots.length == 1) {
            root = roots[0];
        }
    };

    return force;
};


var yFloatingBranch = function(y, r) {
    function force(node, idx) {
        return y - node.depth * 2 * r;
    };
    return force;
};


var forceCenteredBranches = function(){
    var nodes;

    function force(alpha) {
        for (var i = 0, n = nodes.length, dx, node, k = alpha * 0.1; i < n; ++i) {
            node = nodes[i];
            if (node.children != undefined) {
                var mu = _.pluck(node.children, 'x').reduce((a,b) => a + b, 0) / node.children.length;
                dx = mu - node.x;
                var ds = node.children;
                for (var ii = 0, nn = ds.length; ii < nn; ++ii) {
                    ds[ii].vx -= dx * k;
                }
            }
        }
    };

    force.initialize = function(ns) {
        nodes = ns;
    };

    return force;
};

var forceCompactTree = function(target) {
    var nodes;

    // find minimum distance between branches at this depth
    function min_dist_at_depth(node, depth) {
        var max_left = _.chain(node.children[0].descendants())
            .where({depth: depth})
            .pluck('x')
            .max().value();
        var min_right = _.chain(node.children[1].descendants())
            .where({depth: depth})
            .pluck('x')
            .min().value();
        var dx = (min_right - max_left - target);
        return dx;
    }

    function force(alpha) {
        for (var i = 0, n = nodes.length, node, dx, dvx, k = alpha * 0.02; i < n; ++i) {
            node = nodes[i];
            if (node.children != undefined && node.children.length == 2) {
                dx = _.chain(node.children)
                    .pluck('height')
                    .map(x => x + 1)
                    .min()
                    .range()
                    .map(x => min_dist_at_depth(node, x + 1 + node.depth))
                    .min().value();
                dvx = dx * k;
                // left branch
                _.each(node.children[0].descendants(), n => n.vx += dvx);
                // right branch
                _.each(node.children[1].descendants(), n => n.vx -= dvx);
            }
        }
    }

    force.initialize = function(ns) {
        nodes = ns;
    };

    return force;
};


function make_tree(svg, root, width, height, x, y, r, sep, symbols, opacity = "ff", stroke = null, classname = null) {
    var colormap = make_colormap(symbols, opacity);
    var gap = 3;
    var g = svg.append("g").attr("class",classname);

    // add the bounding box
    g.append("rect")
        .attr("x", x - gap)
        .attr("y", y - gap)
        .attr("width", width + 2*gap)
        .attr("height", height + 2*gap)
        .attr("stroke",stroke)
        .attr("stroke-width",1.0)
        .attr("fill-opacity",0.1)
        .attr("fill","#ffffff")
        .attr("rx",r + gap)
        .attr("ry",r + gap);
    // construct the initial layout
    var nLeaves = root.leaves().length;
    var treeWidth = nLeaves * 2 * r + (nLeaves - 1) * gap;
    assign_nodes(root, 2*r+gap, x + (width - treeWidth) / 2 + r, y + height - r);
    // add the links
    var links = g.selectAll('line')
        .data(root.links())
        .enter()
        .append('line')
        .style("pointer-events", "none")
        .attr('stroke','black')
        .attr('stroke-width','2');
    // add the nodes
    var nodes = g.selectAll('circle')
        .data(root.descendants())
        .enter()
        .append('circle')
        .style("pointer-events", "none")
        .attr("fill", d => d.data.head === '.2' ? '#000000' : colormap[d.data.head])
        .attr("opacity", 1.0)
        .attr('r', d => d.data.head === '.2' ? r/3 : r);
    // trees float upward from a fixed root with branches compactly centered
    // over roots
    var layout = d3.forceSimulation(root.descendants())
        .force('floatBranches', d3.forceY().strength(0.7).y(yFloatingBranch(y + height - r, r + gap / 2)))
        .force('compact', forceCompactTree(2 * r + gap))
        .force('centerBranches', forceCenteredBranches())
        .force('fixRoot', forceFixRoot(x + width / 2, y + height - r))
        .on("tick", () => {
            links
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);
            nodes
                .attr("cx", d => d.x)
                .attr("cy", d => d.y);
        });
    // restart on mouseover to reinforce cues for participants
    g.on('mouseover', function() {
        _.each(root.descendants(), x => x.vx += 10);
        layout.alpha(1).restart();
    });
};

var make_lock = function(div, challenge, response_1, response_2, domain, width = 11, r = 12, sep = 7, gap = 3) {
    var get_item = function(treeP, word) {return treeP ? d3.hierarchy(convert_string_to_tree(word)) : word;};
    var stroke_width = 1.0;
    var symbols = domain.symbols;
    var is_tree = domain.type == 'tree';
    var f = is_tree ? make_tree : make_seq;
    var word_ch  = get_item(is_tree, challenge.word);
    var word_r1  = get_item(is_tree, response_1.word);
    var word_r2  = get_item(is_tree, response_2.word);
    var max_height = is_tree ? Math.max(word_ch.height, word_r1.height, word_r2.height) : 1;
    var stim_height = is_tree ? 2*r*(max_height + 1) + gap*max_height : 2*r;
    var stim_width = is_tree ? width*(2*r+gap)-gap : 2*r*width;
    var r0_y = sep;
    var r1_y = r0_y + 2*sep + stim_height;
    var r2_y = r1_y + sep + stim_height;

    // add the svg
    var svg = div.append("svg")
        .attr("class","lock_stimulus")
        .attr("width",stim_width + 2*sep)
        .attr("height",3*stim_height + 5*sep);
    // add the bounding box
    svg.append("rect")
        .attr("class", "frame")
        .attr("width",stim_width + 2*sep - 2*stroke_width)
        .attr("height",3*stim_height + 5*sep - 2*stroke_width)
        .attr("fill","#ffffff")
        .attr("stroke","#666666")
        .attr("stroke-width",stroke_width)
        .attr("x",stroke_width)
        .attr("y",stroke_width)
        .attr("rx",r+sep-stroke_width)
        .attr("ry",r+sep-stroke_width);
    // add the challenge/response separator
    svg.append("line")
        .attr("class", "separator")
        .attr("x1",sep)
        .attr("x2",sep+stim_width)
        .attr("y1",stim_height + 2*sep)
        .attr("y2",stim_height + 2*sep)
        .attr("stroke", "#666666");
    // add the three rows
    svg.call(f,  word_ch, stim_width, stim_height, sep, r0_y, r, sep, symbols, challenge.opacity, challenge.stroke, "challenge")
        .call(f, word_r1, stim_width, stim_height, sep, r1_y, r, sep, symbols, response_1.opacity, response_1.stroke, "response-1 " + response_1.label)
        .call(f, word_r2, stim_width, stim_height, sep, r2_y, r, sep, symbols, response_2.opacity, response_2.stroke, "response-2 " + response_2.label);
};

var display_feedback = function(svg, correct, callback, alignment, symbols, type, r, gap, sep) {
    if (correct) {
        svg.select(".correct rect")
            .attr("fill", "#00ff00")
            .attr("fill-opacity", 0.1)
            .attr("stroke", "#00ff00")
            .attr("stroke-width", 1.0)
            .attr("stroke-opacity", 1.0);
        if (arguments.length > 2) {
            callback();
        }
    } else {
        svg.select(".incorrect rect")
            .attr("fill", "#ff0000")
            .attr("fill-opacity", 0.1)
            .attr("stroke", "#ff0000")
            .attr("stroke-width", 1.0)
            .attr("stroke-opacity", 1.0);
        if (arguments.length > 3) {
            animate_mechanism(svg, alignment, symbols, type, r, gap, sep, callback);
        } else if (arguments.length > 2) {
            callback();
        }
    }
};

async function animate_tree(svg, alignment, symbols, r, gap, sep, callback) {
    var bbHeight = Number(svg.select("g.challenge rect").attr("height")),
        bbWidth = Number(svg.select("g.challenge rect").attr("width")),
        response = alignment_word(alignment, "output"),
        rootpromise = annotate_tree(
            alignment, d3.hierarchy(convert_string_to_tree(response)),
            sep, sep + bbHeight + r, bbWidth, bbHeight, r, gap, sep),
        height = Number(svg.attr("height")),
        deltaH = r + bbHeight + sep,
        challenge = alignment_word(alignment, "input"),
        colormap = make_colormap(symbols, "ff"),
        spanners = alignment_spanners(alignment, "input"),
        nSpanners = _.filter(spanners, x => x !== null).length + 1,
        perElementDelay = 750,
        phase1Duration = perElementDelay,
        phase2Duration = perElementDelay * 2,
        frame = svg.select(".frame"),
        frameHeight = Number(frame.attr("height")),
        separator = svg.select(".separator"),
        separatorY1 = Number(separator.attr("y1")),
        separatorY2 = Number(separator.attr("y2")),
        gs = svg.selectAll("g.response-1, g.response-2");

    // phase 1: enlarge the canvas (.75s)
    svg.transition()
        .duration(phase1Duration)
        .ease(t => d3.easePolyOut(t, 2.0))
        .attr("height", height + deltaH);
    frame.transition()
        .duration(phase1Duration)
        .ease(t => d3.easePolyOut(t, 2.0))
        .attr("height", frameHeight + deltaH);
    separator.transition()
        .duration(phase1Duration)
        .ease(t => d3.easePolyOut(t, 2.0))
        .attr("y1", separatorY1 + deltaH)
        .attr("y2", separatorY2 + deltaH);
    gs.transition()
        .duration(phase1Duration)
        .ease(t => d3.easePolyOut(t, 2.0))
        .attr("transform", "translate(0," + deltaH + ")");

    // phase 2: pattern match (1.5s)
    await svg.selectAll(".challenge line").transition()
        .filter((d, i) => spanners[i] !== null && spanners[i][0] === false)
        .delay(phase1Duration)
        .duration(phase2Duration)
        .ease(t => d3.easeLinear(t))
        .attr("stroke", "#e8e8e8")
        .attr("stroke-width", 3.5)
        .end();

    // soak up time
    await new Promise(resolve => setTimeout(resolve, 750));

    // phase 3: create the grouped response (1.25s * |groups|)
    perElementDelay = 1250;
    var ar = svg.append("g").attr("class", "animated-response");
    var start = Math.floor(Date.now());
    var root = await rootpromise;
    var end = Math.floor(Date.now());
    var links = ar.selectAll("line")
        .data(root.links())
        .enter()
        .append('line')
        .style("pointer-events", "none")
        .attr('stroke', l => l.source.data.group[1] === l.target.data.group[1] || l.source.data.group[0] ? "#000000" : "#e8e8e8")
        .attr('stroke-width', l => l.source.data.group[1] === l.target.data.group[1] || l.source.data.group[0] ? 2.0 : 3.5)
        .attr('stroke-opacity',0)
        .attr('x1',d => d.source.data.group[1] === d.target.data.group[1] ? d.source.data.start.x : d.source.data.end.x)
        .attr('y1',d => d.source.data.group[1] === d.target.data.group[1] ? d.source.data.start.y : d.source.data.end.y)
        .attr('x2',d => d.target.data.start.x)
        .attr('y2',d => d.target.data.start.y);
    var nodes = ar.selectAll('circle')
        .data(root.descendants())
        .enter()
        .append("circle")
        .style("pointer-events", "none")
        .attr("fill", d => d.data.head === ".2" ? "#000000" : colormap[d.data.head])
        .attr("fill-opacity", 0.0)
        .attr("cx", d => d.data.start.x)
        .attr("cy", d => d.data.start.y)
        .attr("r", d => d.data.head === ".2" ? r/3 : r);
    links.filter(l => l.source.data.group[1] === l.target.data.group[1] || _.isEqual(l.target.data.start, l.target.data.end))
        .transition()
        .delay(d => (d.target.data.group[1]) * perElementDelay)
        .duration(perElementDelay)
        .ease(t => d3.easePoly(t, 2.0))
        .attr("stroke-opacity", 1.0)
        .attr('x1',d => d.source.data.end.x)
        .attr('y1',d => d.source.data.end.y)
        .attr('x2',d => d.target.data.end.x)
        .attr('y2',d => d.target.data.end.y);
    links.filter(l => l.source.data.group[1] !== l.target.data.group[1] && !_.isEqual(l.target.data.start, l.target.data.end))
        .transition()
        .delay(d => (0.5 + d.target.data.group[1]) * perElementDelay)
        .duration(perElementDelay/2)
        .ease(t => d3.easePoly(t/2+0.5, 2.0))
        .attr("stroke-opacity", 1.0)
        .attr('x1',d => d.source.data.end.x)
        .attr('y1',d => d.source.data.end.y)
        .attr('x2',d => d.target.data.end.x)
        .attr('y2',d => d.target.data.end.y);
    await nodes.transition()
        .delay(d => (d.data.group[1]) * perElementDelay)
        .duration(perElementDelay)
        .ease(t => d3.easePoly(t, 2.0))
        .attr("fill-opacity", 1.0)
        .attr("cx", d => d.data.end.x)
        .attr("cy", d => d.data.end.y)
        .end();

    // phase 4: transition back
    svg.transition()
        .duration(500)
        .ease(t => d3.easePolyOut(t, 2.0))
        .delay(3000)
        .attr("height", height)
        .on("end", callback);
    frame.transition()
        .duration(500)
        .ease(t => d3.easePolyOut(t, 2.0))
        .delay(3000)
        .attr("height", frameHeight);
    separator.transition()
        .duration(500)
        .ease(t => d3.easePolyOut(t, 2.0))
        .delay(3000)
        .attr("y1", separatorY1)
        .attr("y2", separatorY2);
    gs.transition()
        .duration(500)
        .ease(t => d3.easePolyOut(t, 2.0))
        .delay(3000)
        .attr("transform", "translate(0,0)");
    svg.selectAll("g.challenge line").transition()
        .delay(1000)
        .duration(500)
        .ease(t => d3.easePolyOut(t, 2.0))
        .attr('stroke-width',2.0)
        .attr("stroke", "black");
    svg.selectAll("g.animated-response line").transition()
        .delay(1000)
        .duration(500)
        .ease(t => d3.easePolyOut(t, 2.0))
        .attr('stroke-width',2.0)
        .attr("stroke", "black");
    svg.selectAll(".animated-response circle")
        .transition()
        .delay(2500)
        .duration(500)
        .ease(t => d3.easePolyOut(t, 2.0))
        .attr("fill-opacity", 0.0)
        .remove();
    svg.selectAll(".animated-response line")
        .transition()
        .delay(2500)
        .duration(500)
        .ease(t => d3.easePolyOut(t, 2.0))
        .attr("stroke-opacity", 0.0)
        .remove()
        .on("end", () => d3.select("g.animated-response").remove());
}

async function annotate_tree(alignment, root, x, y, width, height, r, gap, sep) {
    // create an object that tells me where it starts, where it goes, and what group it's in.
    var i = 0;
    var groups = assign_groups_tree(root.copy(), alignment, "output");
    return Promise.all([
        (async()=>await assign_end(root.copy(), x, y, width, height, r, gap, sep))(),
        (async()=>await assign_start(root, alignment, sep, sep, width, height, r, gap))()
    ]).then(([ends, starts]) => root.eachBefore(n => {
        n.data.group = groups[i];
        n.data.end = ends[i];
        if (starts[i].type === "new") {
            n.data.start = n.data.end;
        } else {
            n.data.start = starts[i];
        }
        ++i;
    }));
}

function assign_groups_tree(root, alignment, which) {
    // For each node in `root`, annotate what group it's part of in `which`.
    var length = alignment_length(alignment, which),
        contexts = _.sortBy(alignment_contexts(alignment, which), x => _.min(x[which])),
        groups = _.chain(length / 2)
        .range()
        .map(idx => _.find(_.range(contexts.length), c => 2 * idx >= contexts[c][which][0] && 2 * (idx + 1) <= contexts[c][which][1]))
        .map(x => [contexts[x].context === 1, contexts[x].context === 1 ? 0 : x])
        .value();
    return groups;
}

async function assign_end(root, x, y, width, height, r, gap, sep) {
    var nLeaves = root.leaves().length,
        treeWidth = nLeaves * 2 * r + (nLeaves - 1) * gap,
        ends = [];

    root = assign_nodes2(root, 2*r+gap, x + (width - treeWidth) / 2 + r, y + height - r, "end");

    root.each(n => {
        n.x = n.data.end.x;
        n.y = n.data.end.y;
    });

    return new Promise(
        (resolve) =>
            d3.forceSimulation(root.descendants())
            .alphaMin(0.02)
            .force('floatBranches', d3.forceY().strength(0.7).y(yFloatingBranch(sep + 2 * height, r + gap / 2)))
            .force('compact', forceCompactTree(2 * r + gap))
            .force('centerBranches', forceCenteredBranches())
            .force('fixRoot', forceFixRoot(sep + width / 2, sep + 2 * height))
            .on("end", () => {
                root.eachBefore(n => ends.push({x: n.x, y: n.y}));
                resolve(ends);
            }));
}

async function assign_start(root, alignment, x, y, width, height, r, gap) {
    var unsorted_response = await alignment_response_tree(alignment, x, y, width, height, r, gap),
        response = _.sortBy(unsorted_response, x => x.idx);
    return response;
}

function alignment_spanners(alignment, which) {
    var tree = alignment_word(alignment, which),
        contexts = _.sortBy(alignment_contexts(alignment, which), x => _.min(x[which])),
        queue = [[tree.slice(0,2), 0, 2]],
        spanners = [];
    while (queue.length > 0) {
        var [head, headB, headE] = queue.shift();
        var group_head = _.find(_.range(contexts.length), x => contexts[x][which][0] <= headB && contexts[x][which][1] >= headE);
        for (var iChild = 0, child, len, acc = headE, arity = Number(head[1]); iChild < arity; ++iChild) {
            [child, len] = get_next_term(tree.slice(acc));
            var group_child = _.find(_.range(contexts.length), x => contexts[x][which][0] <= acc && contexts[x][which][1] >= (acc + 2));
            var contained = group_head == group_child || (contexts[group_head].context === 1 && contexts[group_child].context === 1);
            spanners.push(contained ? null : [contexts[group_head].context === 1, group_child]);
            queue.push([child.slice(0,2), acc, acc + 2]);
            acc += len;
        }
    }
    return spanners;
}

function alignment_placement(alignment, which) {
    var length = alignment_length(alignment, which);
    var groups = _.sortBy(alignment_groups(alignment, which), x => _.min(x));
    return _.chain(length)
        .range()
        .map(x => _.find(_.range(groups.length), y => x >= groups[y][0] && x < groups[y][1]))
        .value();
}

function alignment_length(alignment, which) {
    return _.chain(alignment).pluck(which).flatten().max().value();
}

function alignment_contexts(alignment, which) {
    return _.chain(alignment)
        .map(x => _.map(x[which], y => ({context: x.context, [which]: y})))
        .flatten(true)
        .filter(x => x[which].length > 0 && x[which][0] != x[which][1]).value();
}

function alignment_groups(alignment, which) {
    return _.chain(alignment).pluck(which).flatten(true).filter(x => x.length > 0 && x[0] != x[1]).value();
}

function alignment_word(alignment, which) {
    return _.chain(alignment)
        .map(x => _.map(x[which], y => ({"string": x["string"], "position": y[0]})))
        .flatten(true)
        .sortBy("position")
        .pluck("string")
        .reduce((acc, x) => acc + x, "")
        .value();
}

// For each circle that appears in the response, I get an object telling me
// whether its old or new and if old, where it appears in the old
async function alignment_response_tree(alignment, x, y, width, height, r, gap) {
    var challenge = alignment_word(alignment, "input"),
        root = d3.hierarchy(convert_string_to_tree(challenge)),
        positions = await new Promise(
            (resolve) =>
                d3.forceSimulation(root.descendants())
                .alphaMin(0.02)
                .force('floatBranches', d3.forceY().strength(0.7).y(yFloatingBranch(y + height - r, r + gap / 2)))
                .force('compact', forceCompactTree(2 * r + gap))
                .force('centerBranches', forceCenteredBranches())
                .force('fixRoot', forceFixRoot(x + width / 2, y + height - r))
                .on("end", () => {
                    var ps = [];
                    root.eachBefore(n => ps.push({x: n.x, y: n.y}));
                    resolve(ps);
                }));
    return _.chain(alignment).map(group => {
        if (group["input"].length === 0) {
            return _.map(group["output"], out =>
                         _.map(_.range(group["string"].length / 2), idx =>
                               ({
                                   "type": "new",
                                   "symbol": group["string"].slice(2 * idx, 2 * (idx + 1)),
                                   "idx": out[0] / 2 + idx
                               })));
        } else {
            return _.map(group["output"], out =>
                         _.map(group["input"], inp =>
                               _.map(_.range(group["string"].length / 2), idx =>
                                     ({
                                         "type": "old",
                                         "symbol": group["string"].slice(2 * idx, 2 * (idx + 1)),
                                         "x": positions[inp[0] / 2 + idx].x,
                                         "y": positions[inp[0] / 2 + idx].y,
                                         "idxOrig": inp[0] / 2 + idx,
                                         "idx": out[0] / 2 + idx}))));
        }
    }).flatten().value();
}

// For each circle that appears in the response, I get an object telling me
// whether its old or new and if old, where it appears in the old
function alignment_response(alignment) {
    return _.chain(alignment).map(group => {
        if (group["input"].length === 0) {
            return _.map(group["output"], out =>
                         _.map(_.range(group["string"].length), idx =>
                               ({"type": "new", "char": group["string"][idx], "idx": out[0]+idx})));
        } else {
            return _.map(group["output"], out =>
                         _.map(group["input"], inp =>
                               _.map(_.range(group["string"].length), idx =>
                                     ({"type": "old", "char": group["string"][idx], "idxFrom": inp[0]+idx, "idxTo": out[0]+idx}))));
        }
    }).flatten().value();
}

function animate_mechanism(svg, alignment, symbols, type, r, gap, sep, callback) {
    if (svg === undefined) return;
    svg.classed("unclickable", true);
    var callback_wrapper = () => {
        svg.classed("unclickable", false);
        if (callback !== undefined) callback();
    };
    if (type === 'string') {
        animate_string(svg, alignment, symbols, r, gap, sep, callback_wrapper);
    } else {

        animate_tree(svg, alignment, symbols, r, gap, sep, callback_wrapper);
    }
}

async function animate_string(svg, alignment, symbols, r, gap, sep, callback) {
    if (svg === undefined) return;
    svg.classed("unclickable", true);
    var width = Number(svg.attr("width")),
        height = Number(svg.attr("height")),
        challenge_length = alignment_length(alignment, "input"),
        response_length = alignment_length(alignment, "output"),
        challenge_groups = alignment_groups(alignment, "input").length,
        response_groups = alignment_groups(alignment, "output").length,
        challenge_width = 2*r*challenge_length + (challenge_groups - 1) * gap,
        response_width = 2*r*response_length + (response_groups - 1) * gap,
        new_stim_width = Math.max(challenge_width, response_width),
        new_width = new_stim_width + 2*sep,
        deltaH = 3 * r,
        deltaW = Math.max(0, new_width - width),
        placesC = alignment_placement(alignment, "input"),
        placesR = alignment_placement(alignment, "output"),
        response = alignment_word(alignment, "output"),
        perElementDelay = 750,
        phase1Duration = _.max(placesC)*perElementDelay,
        phase2Duration = _.max(placesR)*perElementDelay;

    var frame = svg.select(".frame"),
        frameHeight = Number(frame.attr("height")),
        frameWidth = Number(frame.attr("width"));

    var separator = svg.select(".separator"),
        separatorX2 = Number(separator.attr("x2")),
        separatorY1 = Number(separator.attr("y1")),
        separatorY2 = Number(separator.attr("y2"));

    var gs = svg.selectAll("g.response-1,g.response-2");

    // phase 1: position everything
    svg.transition()
        .duration(phase1Duration)
        .ease(t => d3.easePolyOut(t, 2.0))
        .attr("height", height + deltaH)
        .attr("width", width + deltaW);
    frame.transition()
        .duration(phase1Duration)
        .ease(t => d3.easePolyOut(t, 2.0))
        .attr("width", frameWidth + deltaW)
        .attr("height", frameHeight + deltaH);
    separator.transition()
        .duration(phase1Duration)
        .ease(t => d3.easePolyOut(t, 2.0))
        .attr("x2", separatorX2 + deltaW)
        .attr("y1", separatorY1 + deltaH)
        .attr("y2", separatorY2 + deltaH);
    gs.transition()
        .duration(phase1Duration)
        .ease(t => d3.easePolyOut(t, 2.0))
        .attr("transform", "translate(0," + deltaH + ")");
    svg.selectAll(".challenge circle").transition()
        .duration((d, i) => perElementDelay * placesC[i])
        .ease(t => d3.easePolyOut(t, 2.0))
        .attr("transform", (d, i) => "translate(" + gap * placesC[i] + ",0)");

    var colormap = make_colormap(symbols, "ff"),
        colors = response.split('').map(function(c){return colormap[c];});

    var new_dots = alignment_response(alignment);

    // phase 2: create the grouped response
    await svg.append("g")
        .attr("class", "animated-response")
        .selectAll("circle")
        .data(new_dots)
        .enter()
        .append("circle")
        .style("pointer-events", "none")
        .attr("fill", d => colormap[d["char"]])
        .attr("fill-opacity", 0.0)
        .attr("cx", d => {
            if (d["type"] === "new") {
                return sep + r + d["idx"]*2*r + gap*placesR[d["idx"]];
            } else {
                return sep + r + d["idxFrom"]*2*r + gap*placesC[d["idxFrom"]];
            }})
        .attr("cy", d => d["type"] === "new" ? sep + 4*r : sep + r)
        .attr("r", r)
        .transition()
        .delay(d => {
            var idx = d.type === "new" ? d.idx : d.idxTo;
            return phase1Duration + (1+placesR[idx])*perElementDelay;
        })
        .duration(perElementDelay)
        .ease(d3.easeCubicOut)
        .attr("fill-opacity", 1.0)
        .attr("cx", d => {
            if (d["type"] === "new") {
                return sep + r + d["idx"]*2*r + gap*placesR[d["idx"]];
            } else {
                return sep + r + d["idxTo"]*2*r + gap*placesR[d["idxTo"]];
            }})
        .attr("cy", sep + 4*r)
        .end();

    // transition back
    svg.transition()
        .duration(1000)
        .ease(d3.easeCubicOut)
        .attr("width", width);
    svg.transition()
        .duration(500)
        .ease(d3.easeCubicOut)
        .delay(3000)
        .attr("height", height)
        .on("end", callback);
    frame.transition()
        .duration(1000)
        .ease(d3.easeCubicOut)
        .attr("width", frameWidth);
    frame.transition()
        .duration(500)
        .ease(d3.easeCubicOut)
        .delay(3000)
        .attr("height", frameHeight);
    separator.transition()
        .duration(1000)
        .ease(d3.easeCubicOut)
        .attr("x2", separatorX2);
    separator.transition()
        .duration(500)
        .ease(d3.easeCubicOut)
        .delay(3000)
        .attr("y1", separatorY1)
        .attr("y2", separatorY2);
    gs.transition()
        .duration(500)
        .ease(d3.easeCubicOut)
        .delay(3000)
        .attr("transform", "translate(0,0)");
    svg.selectAll(".challenge circle").transition()
        .duration(1000)
        .ease(d3.easeCubicOut)
        .attr("transform", "translate(0,0)");
    svg.selectAll(".animated-response circle")
        .data(new_dots)
        .transition()
        .duration(1000)
        .ease(d3.easeCubicOut)
        .attr("cx", d => sep + r + (d.type === "new" ? d.idx : d.idxTo)*2*r)
        .transition()
        .delay(1500)
        .duration(500)
        .ease(d3.easeCubicOut)
        .attr("fill-opacity", 0.0)
        .remove();
};

var make_colormap = function(symbols, opacity) {
    if (symbols == "EXAMPLE") {
        return {
            B: "#1edcdc" + opacity,
            P: "#dc1edc" + opacity,
            Y: "#dcdc1e" + opacity,
            B0: "#1edcdc" + opacity,
            P0: "#dc1edc" + opacity,
            Y0: "#dcdc1e" + opacity,
            .2: "#4dff4d" + opacity,
        };
    } else {
        // based on http://colorbrewer2.org/#type=qualitative&scheme=Dark2&n=8
        // modified to make green/blue colors more distinct
        var colors = ['#21c0c0','#d95f02','#7570b3','#e7298a','#6fd001','#e6ab02','#a6761d','#666666'];
        var used_colors = _.chain(colors).map(function(x) {return x + opacity;}).take(symbols.length).value();
        return _.object(symbols, used_colors);
    };
};

var get_domain = function() {
    var domains = [
        {
            name: "ALGAESTRING",
            type: "string",
            symbols: ['A', 'B']
        },
        {
            name: "BINARY",
            type: "string",
            symbols: ['A', 'B', 'C']
        },
        {
            name: "DGT",
            type: "string",
            symbols: ['D', 'G', 'T']
        },
        {
            name: "DOMINANCE",
            type: "string",
            symbols: ['A', 'B', 'C']
        },
        {
            name: "DYCK",
            type: "string",
            symbols: ['A', 'B', 'C']
        },
        {
            name: "MUI",
            type: "string",
            symbols: ['M', 'U', 'I']
        },
        {
            name: "ALGAETREE",
            type: "tree",
            symbols: ['S0', 'K0', 'I0', '.2']
        },
        {
            name: "DEMORGAN",
            type: "tree",
            symbols: ['N1', 'A2', 'O2', 'T0', 'F0']
        },
        {
            name: "UNARY",
            type: "tree",
            symbols: ['A2', 'S1', 'Z0', 'M2']
        },
        {
            name: "ABC",
            type: "tree",
            symbols: ['A0', 'B0', 'C0', '.2']
        },
        {
            name: "BCKW",
            type: "tree",
            symbols: ['B0', 'C0', 'K0', 'W0', '.2']
        },
        {
            name: "CCOMMAND",
            type: "tree",
            symbols: ['.3', 'T0', 'M1', 'R1', 'A0', 'B0', 'C0', 'D0']
        },
    ];
    return domains[1];
};

var convert_string_to_tree = function(string) {
    // get the head
    var head = string.slice(0, 2);
    // parse children into a list
    var arity = Number(string[1]);
    var children = [];
    var place = 2;
    for (var subterm = 0; subterm < arity; subterm++) {
        var [child, length] = get_next_term(string.slice(place));
        place += length;
        children.push(convert_string_to_tree(child));
    }
    // construct the term
    if (head === '.3') {
        return {
            head: children[0].head[0] + '0',
            children: children.slice(1)
        };
    } else {
        return {
            head: head,
            children: children
        };
    }
};

var get_next_term = function(string) {
    var term = string.slice(0,2);
    var length = 2;
    var arity = string[1];
    if (string[0].toLowerCase() == string[0] && string[0] != '.') {
        return [term, length];
    }
    for (var subterm = 0; subterm < arity; subterm++) {
        var [term2, length2] = get_next_term(string.slice(length));
        term += term2;
        length += length2;
    };
    return [term, length];
};

var assign_nodes = function(root, gap, x, y) {
    var x_offset = x;
    var y_offset = y;
    var helper = function(root) {
        if (root.children == undefined) {
            root.x = x_offset;
            x_offset += gap;
        } else {
            for (var i = 0; i < root.children.length; i++) {
                y_offset -= gap;
                helper(root.children[i]);
            }
            root.x = _.pluck(root.children, 'x').reduce(function(a,b) {return a + b;}, 0) / root.children.length;
        }
        root.y = y_offset;
        y_offset += gap;
        return root;
    };
    return helper(root);
};

function assign_nodes2 (root, gap, x, y, which) {
    var x_offset = x;
    var y_offset = y;
    var helper = function(root) {
        root.data[which] = {};
        if (root.children == undefined) {
            root.data[which].x = x_offset;
            x_offset += gap;
        } else {
            for (var i = 0; i < root.children.length; i++) {
                y_offset -= gap;
                helper(root.children[i]);
            }
            root.data[which].x = _.map(root.children, c => c.data[which].x).reduce((a,b) => a + b, 0) / root.children.length;
        }
        root.data[which].y = y_offset;
        y_offset += gap;
        return root;
    };
    return helper(root);
};

/***********
 * PreQuiz *
 ***********/

var PreQuiz = function(attempt) {

    var record_responses = function() {
        var passed = true; // assume passing until evidence suggests failure

        // tell psiturk that we're submitting pre-quiz data
        psiTurk.recordTrialData({'phase':'prequiz',
                                 'attempt':attempt,
                                 'status':'submit'
                                });

        // Collect the data
        $('#prequiz input[type=radio]:checked').each(function() {
            if ((this.name==="prequiz-q1" && this.value!=="2AFC") ||
                (this.name==="prequiz-q2" && this.value!=="harder") ||
                (this.name==="prequiz-q3" && this.value!=="report")) {
                passed = false;
            }
            psiTurk.recordUnstructuredData(this.name + "-a" + attempt, this.value);
        });
        return passed;
    };

    // Load the quiz snippet
    psiTurk.showPage('prequiz.html');
    psiTurk.recordTrialData({'phase':'prequiz',
                             'attempt':attempt,
                             'status':'begin'
                            });

    // launch the experiment after recording a pass
    $("#next").click(function () {
        var passed_prequiz = record_responses();
        if (passed_prequiz) {
            currentview = new AFCExperiment();
        } else {
            // show modal
            $("#redo_quiz").modal();
        }
    });

    // restart the instructions after recording a fail
    $('#redo_quiz').on('hidden.bs.modal', function (e) {
        psiTurk.doInstructions(
            instructionPages,
            function() { currentview = new PreQuiz(attempt+1); }
        );
    });
};


/*******************
 * 2AFC Experiment *
 *******************/

var AFCExperiment = function() {

    var listening = false, // listening for responses?
        animated = (counterbalance === 1), // do you animate feedback?
        correct, // did you respond correctly to the last trial?
        domain = get_domain(),
        nCorrect = 0, // how many correct responses have been chosen?
        nTrain = 50, // how many trials are used to teach each rule?
        nTrials, // how many trials are there?
        nTest = 16, // how many trials are used to test each rule?
        trial = -1, // what trial are we on now?
        progress = 0, // how many trials have we done (including skips)?
        total, // how many possible trials are there?
        responses = [], // responses to this block's rule
        blockIdx = 0, // what block are we on now?
        blocks, // trials, organized into blocks
        block, // the current block
        stimulus, // the current stimulus
        trial_start; // time trial is presented

    function next() {
        if (block.length === 0 && blocks.length === 0) {
            // start post-quiz
            currentview = new PostQuiz([]);
        } else {
            if (block.length === 0 || _.chain(responses).last(10).compact().value().length >= 9) {
                progress += block.length;
                block = blocks.shift();
                blockIdx++;
                responses = [];
                if (blocks.length > 0) {
                    announce_new_mechanism();
                }
            }

            trial += 1;

            stimulus = block.shift();

            show_stimulus();

            // scroll up to make trial visible
            $('html, body').animate({scrollTop: $(document).height()-$(window).height()},
                                    100,
                                    "swing");

            // start trial
            trial_start = new Date().getTime();
            listening = true;
        }
    }

    function insert_delay(callback) {
        // show modal
        $("#feedback").modal({
            backdrop: "static",
            keyboard: false
        });
        // wait 4s and hide modal
        setTimeout(() => {
            $("#feedback").modal('hide');
            callback();
        } , 4000);
    }

    function record_responses(response) {
        var rt = new Date().getTime() - trial_start;
        listening = false;
        correct = (response === stimulus.correct);
        nCorrect += correct;
        progress++;

        psiTurk.recordTrialData({
            'phase':"TEST",
            'task':"2AFC",
            'domain': domain.name,
            'animated': 1 * animated,
            'condition': condition,
            'type': domain.type,
            'block': blockIdx,
            'trial': trial,
            'stimulus': stimulus.stimulus,
            'challenge': stimulus.challenge,
            'correct': stimulus.correct,
            'incorrect': stimulus.incorrect,
            'target': stimulus.target,
            'response': response,
            'accuracy': 1 * correct,
            'rt': rt
        });

        // track how we're doing on the new rule
        if (stimulus.target) responses.push(correct);

        archive_stim(stimulus.correct, stimulus.incorrect, stimulus.alignment);
    }

    var show_stimulus = function() {
        var history = d3.select("#history");

        // remove the last tag from the current last
        history.selectAll(".last").classed("last", false);

        // add the trial number and trial itself
        history.call(add_trial_number).call(add_trial);
    };

    var add_trial_number = function(div) {
        div.append("div")
            .attr("class","attempt last col-10 offset-1")
            .append("div")
            .attr("class","row")
            .append("div")
            .attr("class","col text-center")
            .append("h4")
            .attr("class","last")
            .text("Lock Face " + (trial+1));
    };

    function add_trial(div) {
       div.append("div")
            .attr("class","trial last col-10 offset-1")
            .style("padding","0px 15px")
            .call(add_lock)
            .call(add_instructions)
            .call(add_performance)
            .call(add_progress_bar);
    }

    function make_clickable(div, stim) {
        div.style("pointer-events","all")
            .on("click", () => {
                d3.event.stopPropagation();
                record_responses(stim);})
            .on('mouseover', () => {
                div.attr('stroke',"#ffffff");
                div.transition().call(buttonize, "#000000", "#666666");})
            .on('mouseout', () =>
                div.transition().call(buttonize, "#ffffff", 'none'));
    }

    function add_lock(div) {
        // randomize the response orders
        var [stim_1, stim_2] = flip() ?
            [stimulus.correct, stimulus.incorrect] :
            [stimulus.incorrect, stimulus.correct];

        // add the lock
        div.append("div")
            .attr("class","row justify-content-center")
            .append("div")
            .attr("class","col-auto")
            .call(make_lock,
                  {word: stimulus.challenge},
                  {word: stim_1,
                   label: stim_1 === stimulus.correct ? "correct": "incorrect"},
                  {word: stim_2,
                   label: stim_2 === stimulus.correct ? "correct": "incorrect"},
                  domain);

        // make the lock responses clickable
        div.select(".response-1 rect").call(make_clickable, stim_1);
        div.select(".response-2 rect").call(make_clickable, stim_2);
    }

    function add_instructions(div) {
        div.append("div")
            .attr("class","row query justify-content-center mt-4")
            .append("div")
            .attr("class","col-auto font-weight-bold")
            .text("Which response is correct? Click one to respond." +
                  (trial > 0 ? " Click past trials to play animations." : ""));
    }

    function add_performance(div) {
        if (trial > 0) {
            div.append("div")
                .attr("class","row status-update justify-content-around")
                .append("div")
                .attr("class","col-auto")
                .text("You have correctly responded " +
                      nCorrect + " out of " + trial + " times.");
        }
    }

    function add_progress_bar(div) {
        div.append("div")
            .attr("class","row prog justify-content-around")
            .append("div")
            .attr("class","col-8")
            .append("div")
            .attr("class","progress")
            .append("div")
            .attr("class","progress-bar")
            .attr("role","progressbar")
            .attr("aria-valuenow",progress/total*100)
            .attr("aria-valuemin","0")
            .attr("aria-valuemax","100")
            .style("width",(progress/total*100)+"%")
            .text(Math.floor(progress/total*100)+"% complete");
    }

    function archive_stim(correct_option, incorrect_option, alignment) {
        var callback,
            lastTrial = d3.select(".trial.last");

        // add space
        lastTrial.classed("mb-3",true);

        // dismantle buttons
        lastTrial.selectAll("rect")
            .interrupt()
            .on("click mouseover mouseout", null)
            .attr("fill", "#ffffff");

        // add (in)correct to the attempt label
        d3.select(".attempt.last h4")
            .text("Lock Face " + (trial+1) + ": " + (correct ? "Correct!" : "Incorrect"));

        // provide feedback
        if (animated) {
            callback = () => {
                lastTrial.selectAll(".query, .status-update, .prog").remove();
                next();
            };
            lastTrial.select("svg")
                .call(display_feedback, correct, callback, alignment, domain.symbols, domain.type, 12, 5, 7)
                .on("click", () => {
                    lastTrial.select("svg:not(.unclickable)")
                        .call(animate_mechanism, alignment, domain.symbols, domain.type, 12, 5, 7);
                });
        } else {
            callback = () => {
                if (!correct) {
                    insert_delay(() => {
                        lastTrial.selectAll(".query, .status-update, .prog").remove();
                        next();
                    });
                } else {
                    lastTrial.selectAll(".query, .status-update, .prog").remove();
                    next();
                }
            };
            lastTrial.select("svg").call(display_feedback, correct, callback);
        }
    }

    var announce_new_mechanism = function() {
        var div = d3.select("#history")
            .append("div")
            .attr("class","mechanism my-5 col-10 offset-1")
            .style("padding","0px 15px")
            .append("div")
            .attr("class","row justify-content-center")
            .append("div")
            .attr("class","col-auto text-center");
        div.append("hr");
        div.append("h3")
            .text("A new mechanism has been activated!");
        div.append("h4")
            .text("Lock faces using this mechanism will appear soon.");
        div.append("h4")
            .text("There are now " + (blockIdx+1) + " active mechanisms.");
        div.append("hr");
    };

    var make_training_block = function(trials, iBlock, nTrials) {
        var block = [],
            trial;

        // put n-1 trials of current rule in block
        for (var iTrial = 0; iTrial < nTrials; iTrial++) {
            // put trial of current rule in block
            trial = trials[iBlock].shift();
            trial.target = true;
            block.push(trial);
            // put trial of previous rule in block
            if (iBlock > 0) {
                var rules = _.chain(trials.slice(0,iBlock)).map(function(x, i) {return _.map(x, function(y) {return i;});}).flatten().value();
                var a_previous_rule = rules[_.random(rules.length-1)];
                trial = trials[a_previous_rule].shift();
                trial.target = false;
                block.push(trial);
            }
        }

        // shuffle but make sure final trial is current rule
        var last_trial = block.shift();
        block = _.shuffle(block);
        block.push(last_trial);

        return block;
    };

    var make_testing_block = function(trials, nTrials) {
        // select nTrials trials for each rule and shuffle together
        var block = [];
        for (var iRule = 0; iRule < trials.length; iRule++) {
            for (var iTrial = 0; iTrial < nTrials; iTrial++) {
                var trial = trials[iRule].shift();
                trial.target = false;
                block.push(trial);
            }
        }
        return _.shuffle(block);
    };

    var schedule_trials = function(data, nTrain, nTest) {
        var blocks = [];

        // group trials by rule, shuffle the trials, and shuffle the rules
        var trials = _.chain(data)
            .groupBy('rule')
            .values()
            .map(xs => weighted_shuffle(xs, _.map(xs, x => 1 / (x.length * x.score))))
            .shuffle().value();

        // build testing block first so there are enough trials for each rule
        var testing_block = make_testing_block(trials, nTest);

        for (var iBlock = 0; iBlock < trials.length; iBlock++) {
            blocks.push(make_training_block(trials, iBlock, nTrain));
        }

        blocks.push(testing_block);

        return blocks;
    };

    // Load the stage.html snippet into the body of the page.
    psiTurk.showPage('stage.html');

    // Hide the post-quiz.
    $('#postquiz').hide();

    // Remove the instructions button.
    d3.select(".trialnav div").remove();

    // Load the stimuli and start the task.
    var stimuli_file = "static/data/" + domain.name + "_small.json";
    $.getJSON(stimuli_file, function( data ) {
        blocks = schedule_trials(data, nTrain, nTest);
        total = _.flatten(blocks).length;
        nTrials = blocks.length;
        block = blocks.shift();
        next();
    });

};


/************
 * PostQuiz *
 ************/

var PostQuiz = function(responses) {

      var error_message =
        "<h1>Oops!</h1><p>Something went wrong submitting your HIT." +
        "This might happen if you lose your internet connection." +
        "Press the button to resubmit.</p>" +
        "<button id='resubmit'>Resubmit</button>";

      var record_responses = function() {

            psiTurk.recordTrialData({'phase':'postquiz', 'status':'submit'});

            $('#postquiz textarea').each(function() {
                  psiTurk.recordUnstructuredData(this.name, this.value);
            });
        $('#postquiz input[type=radio]:checked').each(function() {
                  psiTurk.recordUnstructuredData(this.name, this.value);
        });
        $('#postquiz input[type=text]').each(function() {
                  psiTurk.recordUnstructuredData(this.name, this.value);
        });
      };

      var prompt_resubmit = function() {
            document.body.innerHTML = error_message;
            $("#resubmit").click(resubmit);
      };

      var resubmit = function() {
            document.body.innerHTML = "<h1>Trying to resubmit...</h1>";
            reprompt = setTimeout(prompt_resubmit, 10000);

            psiTurk.saveData({
                  success: function() {
                      clearInterval(reprompt);
                psiTurk.computeBonus('compute_bonus', function(){
                      psiTurk.completeHIT(); // when finished saving compute bonus, the quit
                });


                  },
                  error: prompt_resubmit
            });
      };

      // Show the post-quiz.
    $('#postquiz').show();

    // Mark the beginning of the quiz.
    psiTurk.recordTrialData({'phase':'postquiz', 'status':'begin'});

    // Tell the Finish button what to do.
    $("#next").click(function () {
        record_responses();
        psiTurk.saveData({
            success: function(){
                psiTurk.computeBonus('compute_bonus', function() {
                    psiTurk.completeHIT(); // after saving, compute bonus and quit
                });
            },
            error: prompt_resubmit});
    });

    $( "#datepicker" ).datepicker({
        changeMonth: true,
        changeYear: true,
        yearRange: "1900:2019",
        dateFormat: "yy-mm-dd",
        minDate: Date.parse("1900-01-01"),
        maxDate: "-1"
    });
};

// Task object to keep track of the current phase
var currentview;

/******************
 * Run Task       *
 ******************/
$(window).load( function(){
    psiTurk.doInstructions(
        // a list of instructional pages to display in sequence
        instructionPages,
        // what to do after finishing with the instructions
        function() { currentview = new PreQuiz(0); }
    );
});

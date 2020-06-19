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
    "instruct.html",
    "prequiz.html",
    "stage.html",
]);

// These pages will be given as instructions before the task
var instructionPages = [
    "instruct.html",
];

/*********************
 * LIBRARY FUNCTIONS *
 *********************/

var make_iq_pair = function(div, input, disabled) {
    var row = div.append("div").attr("class", "row stimulus text-center align-items-center");
    var i_div = row.append("div").attr("class", "col-auto input");
    make_list(i_div, input);
    row.append("div").style("font-size", "125%").append("div").append("span").attr("class", "fas fa-arrow-right");
    var q_div = row.append("div").attr("class", "col output needs-validation").attr("novalidate", "").append("div").attr("class", "input-group");
    var text = q_div.append("input")
        .attr("type", "text")
        .attr("class", "form-control")
        .attr("placeholder", "What's the output list (e.g. \"1,2,3\")?")
        .attr("aria-label", "output list")
        .attr("aria-describedby", "basic-addon2")
        .attr("required", "");
    var invalid = q_div.append("div")
        .attr("class", "invalid-tooltip");
    var button = q_div.append("div")
        .attr("class", "input-group-append")
        .append("button")
        .attr("class", "btn btn-outline-primary")
        .attr("type", "button")
        .text("Submit");
    if(disabled) {
        text.attr("disabled", disabled);
        button.attr("disabled", disabled);
    }
};

var make_io_pair = function(div, input, output) {
    var row = div.append("div").attr("class", "row text-center align-items-center");
    var i_div = row.append("div").attr("class", "col-auto");
    make_list(i_div, input);
    row.append("div").style("font-size", "125%").append("div").append("span").attr("class", "fas fa-arrow-right");
    var o_div = row.append("div").attr("class", "col-auto");
    make_list(o_div, output);
};

function make_list(div, input) {
    var list = input.list;
    var innerdiv = div.append("div").attr("class","list_stimulus");
    // add the list itself
    innerdiv.selectAll("text")
        .data([list])
        .enter().append("text")
        .style("pointer-events", "none")
        .text(d => pretty_list(d))
        .classed("io-list", true)
        .style("font-size", "125%");

}

var pretty_list = function(xs) {
    return "[" + _.map(xs, x => x.toString()).join(",") + "]";
};

function parse_list(string, max_length, max_elt) {
    // Remove leading whitespace.
    var s = string.trim(),
        xs;

    // Remove first and last characters if brackets.
    if (s.slice(0, 1) === "[" && s.slice(-1) === "]") {
        s = s.slice(1, -1).trim();
    }

    // Handle empty lists.
    if (/^\ *$/.test(s)) {
        return [];
    }

    // Parse the list.
    if (/,/.test(s)) {
        xs = _.map(s.split(/\ *,\ */), s => parseInt(s, 10));
    } else {
        xs = _.map(s.split(/\ +/), s => parseInt(s, 10));
    }

    if (xs.length <= max_length && _.all(xs, x => x <= max_elt && x >= 0)) {
        return xs;
    } else {
        return undefined;
    }
}

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
            if ((this.name==="prequiz-q1" && this.value!=="learn") ||
                (this.name==="prequiz-q2" && this.value!=="110") ||
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
            currentview = new IOExperiment();
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
 * IO Experiment *
 *******************/

function IOExperiment() {

    var listening = false, // listening for responses?
        concept, // What concept are we learning?
        correct, // did you respond correctly to the last trial?
        nCorrect = 0, // how many correct responses have been chosen?
        n_concepts = 250, // How many concepts are there to choose from?
        n_trials = 11, // how many trials are there for each block?
        n_blocks = 10, // how many blocks are there?
        trial = -1, // what trial are we on now?
        progress = 0, // how many trials have we done?
        total, // how many possible trials are there?
        blockIdx = -1, // what block are we on now?
        blocks, // trials, organized into blocks
        block = [], // the current block
        stimulus, // the current stimulus
        max_length = 15, // max length of an output list
        max_elt = 99, // max element in a list
        linguistic = true, // completed the linguistic description yet?
        trial_start; // time trial is presented

    function next() {
        if (block.length === 0 && blocks.length === 0 && linguistic) {
            currentview = new PostQuiz([]);
        } else if (block.length === 0 && !linguistic) {
            record_linguistic_description();
        } else {
            if (block.length === 0) {
                concept = blocks.shift();
                block = concept.trials;
                blockIdx++;
                trial = -1;
                linguistic = false;
                announce_new_block();
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

    function record_linguistic_description() {
        var instruct = d3.select("#history")
            .append("div")
            .attr("class","linguistic last col-12 mt-5 mb-3 text-center")
            .append("h5")
            .text("You answered the last question. What do you think the computer's rule was?");
        var div = d3.select("#history")
            .append("div")
            .attr("class","linguistic last col-12 needs-validation input-group")
            .attr("novalidate","");
        var text = div.append("input")
            .attr("type", "text")
            .attr("class", "form-control")
            .attr("placeholder", "What's the rule (e.g. \"count the number of sevens\")? ")
            .attr("aria-label", "output list")
            .attr("required", "");
        var invalid = div.append("div")
            .attr("class", "invalid-tooltip");
        var button = div.append("div")
            .attr("class", "input-group-append")
            .append("button")
            .attr("class", "btn btn-outline-primary")
            .attr("type", "button")
            .on("click", () => {
                d3.event.stopPropagation();
                // read the input
                $('.linguistic.last input[type=text]').each(function() {
                    if (this.value === "") {
                        this.setCustomValidity("empty");
                        invalid.text("Please enter a description of the rule.");
                        d3.select('.linguistic.last.needs-validation').classed("was-validated", true);
                        d3.select('.linguistic.last.was-validated').on('click', function() {d3.select(this).classed("was-validated", false);});
                    } else if (parse_list(this.value, max_length, max_elt) !== undefined) {
                            this.setCustomValidity("just a list");
                            invalid.text("It looks like you entered a list. Please enter a description of the rule.");
                            d3.select('.linguistic.last.needs-validation').classed("was-validated", true);
                            d3.select('.linguistic.last.was-validated').on('click', function() {d3.select(this).classed("was-validated", false);});
                    } else {
                        this.setCustomValidity("");
                        // record data
                        psiTurk.recordTrialData({
                            'phase':"TEST",
                            'task':"[(i,o)]->spec",
                            'concept': concept.concept,
                            'id': concept.id,
                            'condition': condition,
                            'block': blockIdx,
                            'response': this.value,
                        });
                        d3.selectAll('.linguistic.last *').remove();
                        d3.select('.linguistic.last')
                            .append('h4')
                            .text(`You thought the rule was: ${this.value}.`);
                        d3.select('.linguistic.last')
                            .classed("last needs-validation", false)
                            .attr("novalidate", null)
                            .classed("text-center justify-content-center my-3", true);
                        linguistic = true;
                        next();
                    }
                });
            })
            .text("Submit");
        $('.linguistic.last input').focus();

        // scroll up to make trial visible
        $('html, body').animate({scrollTop: $(document).height()-$(window).height()},
                                100,
                                "swing");
    }

    function announce_new_block() {
        var div = d3.select("#history")
            .append("div")
            .attr("class","block my-5 col-12")
            .style("padding","0px 15px")
            .append("div")
            .attr("class","row justify-content-center")
            .append("div")
            .attr("class","col-auto text-center");
        div.append("hr");
        div.append("h3")
            .text("Round " + (blockIdx+1));
        div.append("h5")
            .text("The computer has thought of a new rule. Can you figure it out?");
        div.append("hr");
    }

    function record_responses(response) {
        var rt = new Date().getTime() - trial_start;
        listening = false;
        correct = _.isEqual(response, stimulus.o);
        nCorrect += correct;
        progress++;

        psiTurk.recordTrialData({
            'phase':"TEST",
            'task':"[(i,o)]->i->o",
            'purpose': concept.purpose,
            'concept': concept.concept,
            'id': concept.id,
            'condition': condition,
            'block': blockIdx,
            'block_trial': trial,
            'total_trial': progress,
            'input': stimulus.i,
            'output': stimulus.o,
            'response': response,
            'accuracy': 1 * correct,
            'rt': rt
        });

        archive_stim(response);
    }

    function show_stimulus() {
        var history = d3.select("#history");

        // remove the last tag from the current last
        history.selectAll(".last").classed("last", false);

        // add the trial number and trial itself
        history
            .call(add_trial_number)
            .call(add_trial);
    }

    var add_trial_number = function(div) {
        div.append("div")
            .attr("class","attempt last col-12")
            .append("h6")
            .attr("class","mb-0")
            .text(`Question ${trial+1}:`);
    };

    function add_trial(div) {
       div.append("div")
            .attr("class","trial last col-12")
            .style("padding","0px 15px")
            .call(add_iq_pair)
            .call(add_instructions)
            .call(add_performance)
            .call(add_progress_bar);
    }

    function add_iq_pair(div) {
        // Add the stimuli.
        div.call(make_iq_pair, {list: stimulus.i}, false);

        // Automatically focus on the input.
        $('.trial.last input').focus();

        // Add behavior to "Submit" button.
        d3.select(".trial.last button")
            .style("pointer-events","all")
            .on("click", () => {
                d3.event.stopPropagation();
                // read the input
                $('.trial.last input[type=text]').each(function() {
                    var list = parse_list(this.value, max_length, max_elt);
                    if (list === undefined) {
                        this.setCustomValidity(this.value);
                        d3.select('.trial.last .output .invalid-tooltip').html(`\"${this.value}\" isn't a list.<br>Make sure you have 0 to ${max_length} numbers from 0 to ${max_elt} separated by commas or spaces.<br>For example: \"1,2,3,4,5,6,7,8,9\".`);
                        d3.select('.trial.last .needs-validation').classed("was-validated", true);
                        d3.select('.trial.last .was-validated').on('click', function() {d3.select(this).classed("was-validated", false);});
                    } else {
                        this.setCustomValidity("");
                        record_responses(list);
                    }
                });
            });
    }

    function add_instructions(div) {
        div.append("div")
            .attr("class","row query justify-content-center mt-4")
            .append("div")
            .attr("class","col-auto font-weight-bold")
            .html(`Type in 0 to ${max_length} numbers from 0 to ${max_elt} separated by commas or spaces, then press Tab Enter or click Submit.`);
    }

    function add_performance(div) {
        if (progress > 0) {
            div.append("div")
                .attr("class","row status-update justify-content-around")
                .append("div")
                .attr("class","col-auto")
                .text(`You have correctly answered ${nCorrect} out of ${progress} questions.`);
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

    function archive_stim(response) {
        var lastTrial = d3.select(".trial.last"),
            response_list = pretty_list(response),
            out_list = pretty_list(stimulus.o),
            callback = () => {
                lastTrial.selectAll(".query, .status-update, .prog").remove();
                next();
            };

        // Add space.
        lastTrial.classed("mb-3",true);

        // Replace input form with output list.
        lastTrial.selectAll(".output *").remove();
        lastTrial.selectAll(".output")
            .call(make_list, {list: stimulus.o})
            .classed("col needs-validation", false)
            .classed("col-auto", true)
            .attr("novalidate", null);
            //.attr("data-html", "true")
            //.attr("data-placement", "top")
            //.attr("data-template", `<div class="tooltip trial-tooltip" role="tooltip"><div class="arrow"></div><div class="tooltip-inner"></div></div>`)
            //.attr("data-trigger", "hover focus")
            //.attr("data-title", `You ${correct ? "" : "in"}correctly answered<br>${response_list}.`);
        //$(".output").tooltip();

        // Label the attempt (in)correct.
        d3.select(".attempt.last h6")
            .html("Question " + (trial+1) + ": " + (correct ? "<span class=\"text-success\">Correct!</span>" : `<span class="text-danger">Incorrect</span>. You said <span class="io-list">${response_list}</span>, but the correct answer is below.`));

        // Do the next trial.
        if (!correct) {
            setTimeout(callback, 3000);
        } else {
            callback();
        }
    }

    // Randomly select n_blocks concepts, then load trials for each selected
    // concept, then randomly select n_trials trials.
    function schedule_trials() {
        // TODO: Uncomment me for the full experiment.
        //let ids = _.chain(n_concepts+1).range().drop(1).shuffle().take(n_blocks).value();
        // TODO: Remove me after the pilot.
        let initial_ids = [1, 25, 68, 85, 101, 113, 120, 134, 139, 140, 155, 161, 166, 174, 182, 190, 200, 214, 235, 246];
        let ids = _.chain(initial_ids).shuffle().take(n_blocks).value();
        let promises = _.chain(ids).map(id => {
            let purpose = id > 150 ? "model" : "dataset";
            let nice_id = "c" + `000${id > 150 ? id - 150 : id}`.slice(-3);
            return d3.json(`/static/data/${purpose}/${nice_id}_1.json`);
        }).value();
        Promise.all(promises).then(datas => {
            blocks = _.chain(datas).zip(ids).map(data => {
                let json = data[0], id = data[1];
                if (id > 150) {
                    return {
                        concept: json.program,
                        purpose: "model",
                        id: "c" + `000${id - 150}`.slice(-3),
                        trials: json.data,
                    };
                } else {
                    return {
                        concept: json.concept,
                        purpose: "dataset",
                        id: "c" + `000${id}`.slice(-3),
                        trials: json.examples,
                    };
                }
            }).value();
            total = _.chain(blocks).pluck("trials").flatten().value().length;
            next();
        });
    }

    // Load the stage.html snippet into the body of the page.
    psiTurk.showPage('stage.html');

    // Hide the post-quiz.
    $('#postquiz').hide();

    // Begin.
    schedule_trials(n_trials, n_blocks);

}


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

    // scroll up to make trial visible
    $("#postquiz")[0].scrollIntoView({
        behavior: "smooth",
        block: "start",
    });

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
        defaultDate: "-21y",
        minDate: Date.parse("1900-01-01"),
        maxDate: "-1"
    });
};

// Task object to keep track of the current phase
var currentview;

/******************
 * Run Task       *
 ******************/
$(window).load(
    // //Use this to eliminate instructions during debugging.
    // function() { currentview = new IOExperiment(0);

    // Use this for the actual experiment.
    function(){
    psiTurk.doInstructions(
        // a list of instructional pages to display in sequence
        instructionPages,
        // what to do after finishing with the instructions
        function() { currentview = new PreQuiz(0); }
    );
});

'use strict';

/*
 * Purpose:
 *   Combines all the components of the interface. Creates each component, gets task
 *   data, updates components. When the user submits their work this class gets the workers
 *   annotations and other data and submits to the backend
 * Dependencies:
 *   AnnotationStages (src/annotation_stages.js), PlayBar & WorkflowBtns (src/components.js),
 *   HiddenImg (src/hidden_image.js), colormap (colormap/colormap.min.js) , Wavesurfer (lib/wavesurfer.min.js)
 * Globals variable from other files:
 *   colormap.min.js:
 *       magma // color scheme array that maps 0 - 255 to rgb values
 *
 */

 // import streamSaver from 'streamsaver';
 // const streamSaver = require('streamsaver');
const streamSaver = window.streamSaver;

function Annotator() {
    this.wavesurfer;
    this.playBar;
    this.predictions;
    this.file;
    this.stages;
    this.workflowBtns;
    this.currentTask;
    this.taskStartTime;
    this.hiddenImage;
    // only automatically open instructions modal when first loaded
    this.instructionsViewed = false;
    // Boolean, true if currently sending http post request
    this.sendingResponse = false;
    this.noCheckLabels = true;
    // Create color map for spectrogram
    var spectrogramColorMap = colormap({
        colormap: magma,
        nshades: 256,
        format: 'rgb',
        alpha: 1
    });

    // Create wavesurfer (audio visualization component)
    var height = 256;
    this.wavesurfer = Object.create(WaveSurfer);
    this.wavesurfer.init({
        container: '.audio_visual',
        waveColor: '#FF00FF',
        progressColor: '#FF00FF',
        // For the spectrogram the height is half the number of fftSamples
        fftSamples: height * 2,
        height: height,
        colorMap: spectrogramColorMap,
        scrollParent: true,
        fillparent: false
    });

    // Create labels (labels that appear above each region)
    var labels = Object.create(WaveSurfer.Labels);
    labels.init({
        wavesurfer: this.wavesurfer,
        container: '.labels'
    });

    // Create hiddenImage, an image that is slowly revealed to a user as they annotate
    // (only for this.currentTask.feedback === 'hiddenImage')
    this.hiddenImage = new HiddenImg('.hidden_img', 100);
    this.hiddenImage.create();

    // Create the play button and time that appear below the wavesurfer
    this.playBar = new PlayBar(this.wavesurfer);
    this.playBar.create();

    // Create the annotation stages that appear below the wavesurfer. The stages contain tags
    // the users use to label a region in the audio clip
    this.stages = new AnnotationStages(this.wavesurfer, this.hiddenImage);
    this.stages.create();

    // Create Workflow btns (submit and exit)
    this.workflowBtns = new WorkflowBtns();
    this.workflowBtns.create();

    this.addEvents();
}

Annotator.prototype = {
    addWaveSurferEvents: function() {
        var my = this;

        // function that moves the vertical progress bar to the current time in the audio clip
        var updateProgressBar = function () {
            var progress = my.wavesurfer.getCurrentTime() / my.wavesurfer.getDuration();
            my.wavesurfer.seekTo(progress);
        };

        // Update vertical progress bar to the currentTime when the sound clip is
        // finished or paused since it is only updated on audioprocess
        this.wavesurfer.on('pause', updateProgressBar);
        this.wavesurfer.on('finish', updateProgressBar);
        // When a new sound file is loaded into the wavesurfer update the  play bar, update the
        // annotation stages back to stage 1, update when the user started the task, update the workflow buttons.
        // Also if the user is suppose to get hidden image feedback, append that component to the page
        this.wavesurfer.on('ready', function () {
            for (const annotation of my.annotations) {
                my.wavesurfer.addRegion(annotation);
            }
            const loader = document.querySelector('.loader');
            loader.style.display = "none";
            my.playBar.update();
            my.stages.updateStage(1);
            my.updateTaskTime();
            my.workflowBtns.update();
            if (my.currentTask.feedback === 'hiddenImage') {
                my.hiddenImage.append(my.currentTask.imgUrl);
            }
            if (my.predictions) {plotData(my.predictions)};
        });

        this.wavesurfer.on('click', function (e) {
            my.stages.clickDeselectCurrentRegion();
        });
    },

    updateTaskTime: function() {
        this.taskStartTime = new Date().getTime();
    },

    // Event Handler, if the user clicks submit annotations call submitAnnotations
    addWorkflowBtnEvents: function() {
        $(this.workflowBtns).on('submit-annotations', this.submitAnnotations.bind(this));
    },

    addEvents: function() {
        this.addWaveSurferEvents();
        this.addWorkflowBtnEvents();
    },

    // Update the task specific data of the interfaces components
    update: function() {
        var my = this;
        var mainUpdate = function(annotationSolutions) {

            // Update the different tags the user can use to annotate, also update the solutions to the
            // annotation task if the user is suppose to recieve feedback
            var proximityTags = my.currentTask.proximityTag;
            var annotationTags = my.currentTask.annotationTag;
            var alwaysShowTags = my.currentTask.alwaysShowTags;

            my.stages.reset(
                proximityTags,
                annotationTags,
                annotationSolutions,
                alwaysShowTags
            );

            // Update the visualization type and the feedback type and load in the new audio clip
            my.wavesurfer.params.visualization = my.currentTask.visualization; // invisible, spectrogram, waveform
            my.wavesurfer.params.feedback = my.currentTask.feedback; // hiddenImage, silent, notify, none
            my.wavesurfer.load(my.currentTask.url);

            my.wavesurfer.params.minPxPerSec = 40;
        };

        if (this.currentTask.feedback !== 'none') {
            // If the current task gives the user feedback, load the tasks solutions and then update
            // interface components
            $.getJSON(this.currentTask.annotationSolutionsUrl)
            .done(function(data) {
                mainUpdate(data);
            })
            .fail(function() {
                alert('Error: Unable to retrieve annotation solution set');
            });
        } else {
            // If not, there is no need to make an additional request. Just update task specific data right away
            mainUpdate({});
        }
    },

    // Update the interface with the task's data
    loadTask: function(annotations) {
        var my = this;
        my.annotations = annotations;
        const JSONFeed = fileToJSON(my.file);
        my.currentTask = JSONFeed.task;
        my.update();
    },

    // Collect data about users annotations and submit it to the backend
    submitAnnotations: function() {
        // Check if all the regions have been labeled before submitting
        if (this.noCheckLabels || this.stages.annotationDataValidationCheck()) {
            this.sendingResponse = true;
            // Get data about the annotations the user has created
            var content = {
                task_start_time: this.taskStartTime,
                task_end_time: new Date().getTime(),
                visualization: this.wavesurfer.params.visualization,
                annotations: this.stages.getAnnotations(),
                deleted_annotations: this.stages.getDeletedAnnotations(),
                // List of the different types of actions they took to create the annotations
                annotation_events: this.stages.getEvents(),
                // List of actions the user took to play and pause the audio
                play_events: this.playBar.getEvents(),
                // Boolean, if at the end, the user was shown what city the clip was recorded in
                final_solution_shown: this.stages.aboveThreshold()
            };

            this.post(content);
        }
    },

    // Make POST request, passing back the content data. On success load in the next task
    post: function (content) {
        console.log('content', content);
        $.ajax({
            url : "",
            headers: { "X-CSRFToken": $.cookie("csrftoken") },
            type : "POST",
            data : {
                'annotation': JSON.stringify(content.annotations)
            },
            success : function(json) {
                console.log("success");
                document.location.href = json.url;
            },
            error : function(xhr, errmsg, err) {
                console.log("Something went wrong: ", errmsg);
            }
        });
    },

    updateFileNumberDisplay() {
        const filename = document.querySelector('.filename');
        filename.innerHTML = this.filename;
    }

};

function fileToJSON(file) {
  return {
      "task": {
          "feedback": "none",
          "visualization": "spectrogram",
          "proximityTag": [],
          "annotationTag": ["bird", "bird1", "bird2"],
          "url": `${file.webkitRelativePath}`,
          "tutorialVideoURL":"",
          "alwaysShowTags": true
      }
  }
}

function main(track_name, track_file, annotations, predictions) {
    console.log('track_file', track_file)
    var blob = null;
    var xhr = new XMLHttpRequest();
    xhr.open("GET", track_file);
    xhr.responseType = "blob";
    xhr.onload = function() {
        blob = xhr.response;
        blob.name = track_name;
        blob.webkitRelativePath = track_file;
        LoadAndDisplayFile(blob);
    }
    xhr.send()

    // Create all the components
    var annotator = new Annotator();

    const LoadAndDisplayFile = (blob) => {
      const file = blob;
      annotator.file = file;
      annotator.loadTask(annotations);
      annotator.predictions = predictions;
    }
}

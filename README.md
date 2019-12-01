# MicrofauneAnnotator

Webinterface for audio annotation

## Installation

* Install *django* in the environment
* Run *install.sh* (be careful, it deletes the current database)
* Go into *microfaune_annotator*: `cd microfaune_annotator`
* Run django dev server: `python manage.py runserver`

The script *install.sh* deletes the current project database , recreates
it and populates it with toy data for development purposes.

2 users are created (with the same password *microfaune*):
* *admin*
* *annotator*

## Architecture

### Models

The project has 3 custom models (cf *annotate/models.py*):
* **Project**: define an annotation project which contains a list of possible labels.
* **AudioTrack**: an object representing an audio track. It links an audio file, points to a *Project* and can have a prediction array.
* **Annotation**: an object representing an audio annotation. It points to an *AudioTrack*, to an user and can be marked as reviewed by another user.

### Web

The website has a simple architecture:
* The homepage lists all active projects and links to their pages
* A project page lists all the associated audio tracks and links to a page to annotate them
* The annotation page allows to view, create annotation and save annotation (TODO).

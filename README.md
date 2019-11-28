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

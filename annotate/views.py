import json
import os

from django.http import JsonResponse
from django.urls import reverse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.db.models import Count

from librosa.core import get_duration

from .models import Project, AudioTrack, Annotation
from .forms import JsonFileForm, MultipleFileFieldForm


# Create your views here.
@login_required()
def homepage(request):
    projects = Project.objects.filter(active=True).annotate(
        audiotrack_count=Count("audiotrack")).values("id", "name",
                                                     "audiotrack_count")
    annotations = Annotation.objects.values_list("track__project_id",
                                                 "reviewed")
    annotation_counter = {p["id"]: 0 for p in projects}
    review_counter = {p["id"]: 0 for p in projects}
    for a in annotations:
        annotation_counter[a[0]] += 1
        if a[1]:
            review_counter[a[0]] += 1
    for p in projects:
        p["annotation_count"] = annotation_counter[p["id"]]
        p["review_count"] = review_counter[p["id"]]

    return render(request, "annotate/homepage.html",
                  {"projects": projects})


@login_required()
def project_homepage(request, project_id):
    project = Project.objects.get(id=project_id)
    tracks = AudioTrack.objects.filter(project_id=project_id).annotate(
        annotation_count=Count("annotation"))
    user_annotations = Annotation.objects.filter(
        track__project=project, user=request.user).values_list("track",
                                                               flat=True)
    for t in tracks:
        t.user_annotation = "Yes" if t.id in user_annotations else "No"

    return render(request, "annotate/project_homepage.html",
                  {"project": project,
                   "tracks": tracks})


@login_required()
def audiotrack_homepage(request, audiotrack_id):
    track = AudioTrack.objects.get(id=audiotrack_id)
    annotations = Annotation.objects.filter(track_id=audiotrack_id)

    return render(request, "annotate/audiotrack_homepage.html",
                  {"track": track,
                   "annotations": annotations})


@login_required()
def annotate(request, audiotrack_id, annotation_id):
    track = AudioTrack.objects.get(id=audiotrack_id)

    if request.is_ajax():
        if request.method == 'POST':
            annotation_data = request.POST.get('annotation', None)

            if annotation_id == 0:
                Annotation.objects.create(
                    track=track,
                    value=annotation_data,
                    user=request.user,
                )
            else:
                annotation = Annotation.objects.get(id=annotation_id)
                if annotation.user != request.user:
                    annotation.reviewed = True
                    annotation.reviewed_by = request.user
                annotation.value = annotation_data
                annotation.save()
            return JsonResponse({
                'response': 'ok',
                'url': reverse('audiotrack_homepage', args=(audiotrack_id,))
                }, content_type="application/json")

    if annotation_id == 0:
        return render(request, "annotate/annotate.html",
                      {"track": track, })
    if annotation_id == 0:
        annotation = {"id": None, "value": ""}
    else:
        annotation = Annotation.objects.get(id=annotation_id)

    return render(request, "annotate/annotate.html",
                  {"track": track,
                   "annotation": annotation})


@login_required()
def save_annotation(request, audiotrack_id):
    if request.is_ajax():
        if request.method == 'POST':
            data = request.POST.get('data', None)
            print(f'\n\nRaw Data: {data}')

    return HttpResponse({'test': 1}, content_type="application/json")


@login_required()
def upload_tracks(request, project_id):
    message = ""
    project = Project.objects.get(id=project_id)
    if request.method == "POST":
        form = MultipleFileFieldForm(request.POST, request.FILES)
        current_files = project.audiotrack_set.values_list("name", flat=True)
        if form.is_valid():
            files = request.FILES.getlist("file_field")
            non_audio = 0
            duplicate = 0
            success = 0
            for f in files:
                if not f.name.endswith((".mp3", ".ogg", ".wav", ".flac")):
                    non_audio += 1
                    continue
                if f.name in current_files:
                    duplicate += 1
                    continue
                local_file = os.path.join(settings.MEDIA_ROOT, f.name)
                with open(local_file, 'wb+') as destination:
                    for chunk in f.chunks():
                        destination.write(chunk)
                try:
                    duration = get_duration(filename=local_file)
                except Exception as e:
                    duration = 0

                AudioTrack.objects.create(
                    name=f.name,
                    file=os.path.join(settings.MEDIA_URL, f.name),
                    format=os.path.splitext(f.name)[1][1:],
                    project=project,
                    duration=duration)
                success += 1

            message = f"{success} files successfully uploaded"
            if non_audio:
                message += f", {non_audio} non-audio files rejected"
            if duplicate:
                message += f", {duplicate} duplicate files rejected"

    form = MultipleFileFieldForm()
    return render(request, 'annotate/upload.html',
                  {'form': form, 'project': project, 'message': message})



@login_required()
def upload_predictions(request, project_id):
    project = Project.objects.get(id=project_id)
    message = ""

    if request.method == "POST":
        form = JsonFileForm(request.POST, request.FILES)
        if form.is_valid():
            json_file = request.FILES["json_file"]
            try:
                with json_file.open("r") as f:
                    data = json.load(f)
            except JsonDecodeError:
                message = "The uploaded json file is not a valid json."
                data = []
            if not isinstance(data, list):
                message = ("The uploaded json file does not contains a "
                           "list of dicionaries.\n")
                data = []
            print(data)
            success = 0
            failure = 0
            for d in data:
                try:
                    track = AudioTrack.objects.get(name=d["file"])
                    print(d["prediction"])
                    track.prediction = json.dumps(d["prediction"])
                    print(track.prediction)
                    track.save()
                    success += 1
                except Exception as e:
                    print(e)
                    failure += 1            
            if success:
                message += (f"{success} prediction(s) succesfully added to the "
                            "database\n")
            if failure:
                message += (f"{failure} prediction(s) failed to be added to the "
                            "database\n")

    
    form = JsonFileForm()
    instructions = (
        "The upload file must be a valid json. It must contain a list "
        "of dictionaries with the keys 'file' and 'prediction'. The  "
        "'file' value should be an audio track name (for example "
        "'foo.wav') already present in the database. The 'prediction' "
        " value should be a list of number.")
       
    return render(request, 'annotate/upload_json.html',
                  {"form": form, "project": project,
                   "title": "Upload predictions",
                   "instructions": instructions, "message": message})



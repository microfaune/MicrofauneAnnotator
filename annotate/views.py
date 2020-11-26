import json
import os

from django.http import JsonResponse
from django.urls import reverse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.db.models import Count, F
from django.forms.models import model_to_dict
from django.contrib.auth.models import User
from django.core.files.storage import default_storage


from .models import Project, AudioTrack, Annotation
from .forms import JsonFileForm, MultipleFileFieldForm


# Create your views here.
@login_required()
def homepage(request):
    projects = Project.objects.annotate(
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
    tracks = AudioTrack.objects.annotate(
        annotation_count=Count("annotation")).order_by("name")
    user_annotations = Annotation.objects.filter(
        track__project=project, user=request.user).values_list("track",
                                                               flat=True)
    for t in tracks:
        t.user_annotation = "Yes" if t.id in user_annotations else "No"

        annotations = Annotation.objects.filter(track_id=t.id)

        if annotations:
            t.annotation = True
            ann = Annotation.objects.get(track_id=t.id)
            if ann.reviewed:
                t.reviewed = True
            else:
                t.reviewed = False

            bird_calls = json.loads(ann.value)
            bird_calls_num = len(bird_calls)
            if bird_calls_num > 0:
                t.bird_calls = bird_calls_num

                labelized_bird_calls = [x for x in bird_calls if x['annotation'] != '']
                t.labelized_bird_calls = len(labelized_bird_calls)
        else:
            t.annotation = False
            t.reviewed = False


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
    print('------', settings.MEDIA_URL)

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
                   "annotation": annotation,})


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

                # with default_storage.open(f.name, 'wb') as destination:
                #     for chunk in f.chunks():
                #         destination.write(chunk)

                AudioTrack.objects.create(
                    name=f.name,
                    file=os.path.join(settings.MEDIA_URL, f.name),
                    format=os.path.splitext(f.name)[1][1:],
                    project=project,
                    duration=0)
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
            except json.JsonDecodeError:
                message = "The uploaded json file is not a valid json."
                data = []
            if not isinstance(data, list):
                message = ("The uploaded json file does not contains a "
                           "list of dicionaries.\n")
                data = []
            success = 0
            failure = 0
            for d in data:
                try:
                    track = AudioTrack.objects.get(name=d["file"])
                    track.prediction = json.dumps(d["prediction"])
                    track.save()
                    success += 1
                except Exception as e:
                    print(e)
                    failure += 1
            if success:
                message += (f"{success} prediction(s) successfully added to "
                            "the database\n")
            if failure:
                message += (f"{failure} prediction(s) failed to be added to "
                            "the database\n")

    form = JsonFileForm()
    instructions = (
        "The uploaded file must be a valid json.\n"
        "It must contain a list of dictionaries with the keys 'file' and "
        "'prediction'.\n"
        "The 'file' value should be an audio track name (for example "
        "'foo.wav') already present in the database.\n"
        "The 'prediction' value should be a list of numbers.")

    return render(request, 'annotate/upload_json.html',
                  {"form": form, "project": project,
                   "title": "Upload predictions",
                   "instructions": instructions, "message": message})


@login_required()
def upload_annotations(request, project_id):
    project = Project.objects.get(id=project_id)
    message = ""

    if request.method == "POST":
        form = JsonFileForm(request.POST, request.FILES)
        if form.is_valid():
            json_file = request.FILES["json_file"]
            try:
                with json_file.open("r") as f:
                    data = json.load(f)
            except json.JsonDecodeError:
                message = "The uploaded json file is not a valid json."
                data = []
            if not isinstance(data, list):
                message = ("The uploaded json file does not contains a "
                           "list of dicionaries.\n")
                data = []
            success = 0
            duplicate = 0
            failure = 0
            for d in data:
                try:
                    track = AudioTrack.objects.get(name=d["file"])
                    user = User.objects.get(username=d["username"])
                    if Annotation.objects.filter(track=track, user=user):
                        duplicate += 1
                        continue
                    annotation = Annotation()
                    annotation.track = track
                    annotation.user = user
                    annotation.value = json.dumps(d["value"])
                    annotation.save()
                    success += 1
                except Exception as e:
                    print(e)
                    failure += 1
            if success:
                message += (f"{success} annotation(s) successfully added to "
                            "the database\n")
            if duplicate:
                message += (f"{duplicate} annotation(s) already exists (same "
                            "track and user)\n")
            if failure:
                message += (f"{failure} annotation(s) failed to be added to "
                            "the database\n")

    form = JsonFileForm()
    instructions = (
        "The uploaded file must be a valid json.\n"
        "It must contain a list of dictionaries with the keys 'file', 'user' "
        "and 'value'.\n"
        "The 'file' value should be an audio track name (for example "
        "'foo.wav') already present in the database.\n"
        "The 'username' value should be the username of an user already "
        "present in the database.\n"
        "The 'value' value should be a list of dictionaries in the format "
        "generated by wavesurfer (with 4 keys: 'id', 'start', 'end', "
        "'annotation').")

    return render(request, 'annotate/upload_json.html',
                  {"form": form, "project": project,
                   "title": "Upload annotations",
                   "instructions": instructions, "message": message})


@login_required()
def download_project(request, project_id):
    project = model_to_dict(Project.objects.get(id=project_id))
    tracks = AudioTrack.objects.filter(project_id=project_id).values()
    annotations = list(Annotation.objects.filter(
        track__project_id=1).order_by("track_id").annotate(
        username=F("user__username"), reviewer=F("reviewed_by__username")
        ).values())
    ind = 0
    for t in tracks:
        t["annotation_set"] = []
        while (ind < len(annotations) and
               annotations[ind]["track_id"] == t["id"]):
            t["annotation_set"].append(annotations[ind])
            ind += 1
    project["tracks"] = list(tracks)

    response = JsonResponse(project, json_dumps_params={"indent": 2},
                            content_type="application/json")
    response['Content-Disposition'] = ('attachment;'
                                       f'filename={project["name"]}.json')
    return response

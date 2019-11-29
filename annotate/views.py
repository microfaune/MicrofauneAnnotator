from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count

from .models import Project, AudioTrack, Annotation

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
        print(p["id"])
        p["annotation_count"] = annotation_counter[p["id"]]
        p["review_count"] = review_counter[p["id"]]

    return render(request, "annotate/homepage.html",
                  {"projects": projects})


@login_required()
def project_homepage(request, project_id):
    project = Project.objects.get(id=project_id)
    tracks = AudioTrack.objects.filter(project_id=project_id).annotate(
        annotation_count=Count("annotation"),
    )
    return render(request, "annotate/project_homepage.html",
                  {"project": project,
                   "tracks": tracks})


@login_required()
def annotate(request, audiotrack_id):
    track = AudioTrack.objects.get(id=audiotrack_id)
    return render(request, "annotate/annotate.html",
                  {"track": track})

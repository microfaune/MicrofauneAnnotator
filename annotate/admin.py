from django.contrib import admin
from .models import Project, AudioTrack, Annotation

# Register your models here.
admin.site.register(Project)
admin.site.register(AudioTrack)
admin.site.register(Annotation)

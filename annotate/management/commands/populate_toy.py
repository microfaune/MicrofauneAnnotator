import os

from django.conf import settings
from django.core.management.base import BaseCommand

from django.contrib.auth.models import User
from annotate.models import Project, AudioTrack


class Command(BaseCommand):
    args = ''
    help = 'populate the database with toy data'

    def handle(self, *args, **options):
        User.objects.create_user(username="admin", password="microfaune",
                                 is_superuser=True, is_staff=True)

        user = User.objects.create_user(username="annotator",
                                        password="microfaune")

        project = Project.objects.create(name="CiteU", user=user)

        for audio_filename in os.listdir(settings.MEDIA_ROOT):
            audio_file = os.path.join(settings.MEDIA_ROOT, audio_filename)
            with open(audio_file, "rb") as f:
                binary_stream = f.read()
            AudioTrack.objects.create(
                name=audio_filename,
                file=binary_stream,
                format="wav",
                project=project,
                duration=60)

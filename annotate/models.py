from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

import json
from numbers import Number


def validate_string_list(value):
    labels = value.split(",")
    for lab in labels:
        if not lab:
            raise ValidationError("Wrong labels string: empty label")
    if len(lab) != len(set(lab)):
        raise ValidationError("Wrong labels string: duplicate label")


def validate_json(value):
    """Validate that the value is a valid json string or empty"""
    if not value:
        return
    try:
        v = json.loads(value)
    except json.JSONDecodeError:
        raise ValidationError("Wrong prediction array: not valid json")
    return v


def validate_json_list(value):
    """Valid if empty or list of numbers"""
    v = validate_json(value)

    if not isinstance(v, list):
        raise ValidationError("Wrong prediction array: not a list")

    if not isinstance(v[0], Number):
        raise ValidationError("Wrong prediction array: first element not"
                              " a number")


# Create your models here.
class Project(models.Model):
    name = models.CharField(max_length=50, unique=True)
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)

    # list of labels separated by commas
    labels = models.CharField(max_length=200,
                              validators=[validate_string_list],
                              default="bird,bird_low")
    default_label = models.PositiveSmallIntegerField(default=0)

    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class AudioTrack(models.Model):
    FORMAT_CHOICES = [("wav", "wav"), ("mp3", "mp3"), ("flac", "flac")]
    name = models.CharField(max_length=100)
    file = models.FileField(max_length=200)
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES,
                              default="wav")
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    duration = models.FloatField(default=0)
    prediction = models.TextField(validators=[validate_json_list], default="")

    def __str__(self):
        return self.name


class Annotation(models.Model):
    track = models.ForeignKey(AudioTrack, on_delete=models.CASCADE)
    value = models.TextField(validators=[validate_json], default="")
    user = models.ForeignKey(User, null=True, related_name='user',
                             on_delete=models.SET_NULL)
    reviewed = models.BooleanField(default=False)
    reviewed_by = models.ForeignKey(User, null=True,
                                    related_name='reviewed_by',
                                    on_delete=models.SET_NULL)
    date_time = models.DateTimeField(auto_now=True, blank=True)

    def __str__(self):
        return f"{self.track} by {self.user.username}"

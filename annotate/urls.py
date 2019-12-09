"""Annotate URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from . import views


urlpatterns = [
    path('', views.homepage, name="home"),
    path('project/<int:project_id>/', views.project_homepage,
         name="project_homepage"),
    path('audiotrack/<int:audiotrack_id>/', views.audiotrack_homepage,
         name="audiotrack_homepage"),
    path('annotate/<int:audiotrack_id>/<int:annotation_id>/', views.annotate,
         name="annotate"),
    path('project/<int:project_id>/upload', views.upload_tracks,
         name='upload_audio'),
    path('project/<int:project_id>/upload_predictions',
         views.upload_predictions, name='upload_pred'),
    path('project/<int:project_id>/upload_annotations',
         views.upload_annotations, name='upload_annotations')
]

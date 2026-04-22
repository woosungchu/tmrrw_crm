from django.urls import path
from . import views

urlpatterns = [
    path("assignment/", views.assignment_settings, name="assignment_settings"),
]

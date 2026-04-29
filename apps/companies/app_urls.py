from django.urls import path
from . import views

urlpatterns = [
    path("team/", views.team_settings, name="team_settings"),
    # 기존 URL 호환 — 새 통합 페이지로 redirect
    path("assignment/", views.assignment_settings, name="assignment_settings"),
]

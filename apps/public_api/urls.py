from django.urls import path
from . import views

urlpatterns = [
    path("leads", views.leads_create, name="public_api_leads_create"),
    path("sources/verify", views.source_verify, name="public_api_source_verify"),
]

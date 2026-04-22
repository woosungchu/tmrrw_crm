from django.urls import path
from . import views

urlpatterns = [
    path("", views.source_list, name="source_list"),
    path("new/", views.source_create, name="source_create"),
    path("<int:pk>/", views.source_detail, name="source_detail"),
    path("<int:pk>/keys/new/", views.api_key_create, name="api_key_create"),
    path("<int:pk>/keys/<int:key_id>/revoke/", views.api_key_revoke, name="api_key_revoke"),
]

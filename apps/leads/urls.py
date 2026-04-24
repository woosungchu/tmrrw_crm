from django.urls import path
from . import views

urlpatterns = [
    path("", views.lead_list, name="lead_list"),
    path("new/", views.lead_create, name="lead_create"),
    path("export.xlsx", views.lead_export, name="lead_export"),
    path("<int:pk>/", views.lead_detail, name="lead_detail"),
    path("<int:pk>/status/", views.lead_change_status, name="lead_change_status"),
    path("<int:pk>/assign/", views.lead_assign, name="lead_assign"),
    path("<int:pk>/memo/", views.lead_add_memo, name="lead_add_memo"),
]

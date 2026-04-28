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
    path("<int:pk>/call/", views.lead_call_init, name="lead_call_init"),
    path("<int:pk>/blacklist/", views.lead_add_to_blacklist, name="lead_add_to_blacklist"),
    path("<int:pk>/noti/retry/", views.lead_noti_retry, name="lead_noti_retry"),
    path("<int:pk>/noti/clear/", views.lead_noti_clear, name="lead_noti_clear"),
    # Blacklist 관리
    path("blacklist/", views.blacklist_list, name="blacklist_list"),
    path("blacklist/new/", views.blacklist_create_manual, name="blacklist_create_manual"),
    path("blacklist/<int:pk>/delete/", views.blacklist_delete, name="blacklist_delete"),
]

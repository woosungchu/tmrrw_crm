from django.urls import path

from . import views


urlpatterns = [
    # 템플릿 관리 (/app/templates/)
    path("templates/", views.template_list, name="template_list"),
    path("templates/new/", views.template_create, name="template_create"),
    path("templates/<int:pk>/edit/", views.template_edit, name="template_edit"),
    path("templates/<int:pk>/delete/", views.template_delete, name="template_delete"),

    # Lead 에서 SMS 발송
    path("leads/<int:lead_pk>/sms/", views.send_sms_to_lead, name="send_sms_to_lead"),

    # 콜백
    path("callbacks/", views.callback_list, name="callback_list"),
    path("leads/<int:lead_pk>/callback/", views.callback_create, name="callback_create"),
    path("callbacks/<int:pk>/done/", views.callback_done, name="callback_done"),
    path("callbacks/upcoming.json", views.callback_upcoming_json, name="callback_upcoming_json"),
]

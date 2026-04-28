from django.urls import path
from . import views

urlpatterns = [
    path("approvals/", views.approval_list, name="superadmin_approval_list"),
    path("approvals/<int:company_id>/approve/", views.approval_approve, name="superadmin_approval_approve"),
    path("approvals/<int:company_id>/deny/", views.approval_deny, name="superadmin_approval_deny"),
    path("approvals/<int:company_id>/reopen/", views.approval_reopen, name="superadmin_approval_reopen"),
]

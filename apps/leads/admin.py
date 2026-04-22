from django.contrib import admin
from .models import Lead, TimelineEntry


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "phone", "status", "company", "source", "agent", "received_at")
    list_filter = ("status", "assignment_type", "noti_status", "company")
    search_fields = ("name", "phone", "external_id")
    readonly_fields = ("phone_hash", "received_at")


@admin.register(TimelineEntry)
class TimelineEntryAdmin(admin.ModelAdmin):
    list_display = ("lead", "type", "actor", "at")
    list_filter = ("type",)

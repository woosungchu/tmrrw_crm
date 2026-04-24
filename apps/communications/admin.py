from django.contrib import admin

from .models import Template, Callback


@admin.register(Template)
class TemplateAdmin(admin.ModelAdmin):
    list_display = ("id", "company", "title", "channel", "is_active", "updated_at")
    list_filter = ("channel", "is_active", "company")
    search_fields = ("title", "body")


@admin.register(Callback)
class CallbackAdmin(admin.ModelAdmin):
    list_display = ("id", "company", "lead", "agent", "scheduled_at", "status", "reminder_sent")
    list_filter = ("status", "reminder_sent", "company")
    search_fields = ("lead__name", "lead__phone", "note")
    date_hierarchy = "scheduled_at"

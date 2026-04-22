from django.contrib import admin
from .models import Source, ApiKey


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ("title", "company", "is_active", "created_at")
    list_filter = ("is_active", "company")
    search_fields = ("title", "tmrw_form_id")


@admin.register(ApiKey)
class ApiKeyAdmin(admin.ModelAdmin):
    list_display = ("token_prefix", "source", "label", "is_active", "last_used_at")
    list_filter = ("revoked_at",)
    readonly_fields = ("token_hash", "token_prefix", "created_at", "last_used_at")

from django.contrib import admin
from .models import Company, AssignmentConfig, Billing, Invoice


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "billing_status", "plan", "owner",
                     "approved_at", "approved_by", "created_at")
    list_filter = ("billing_status", "plan", "is_internal_test")
    search_fields = ("name",)
    raw_id_fields = ("owner", "approved_by")
    readonly_fields = ("created_at", "updated_at")


admin.site.register(AssignmentConfig)
admin.site.register(Billing)
admin.site.register(Invoice)

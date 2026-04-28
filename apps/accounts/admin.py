from django.contrib import admin
from .models import User, InviteToken


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "id", "login_id", "name", "role", "company",
        "is_active", "is_approver", "is_staff", "is_superuser",
    )
    list_filter = ("role", "is_active", "is_approver", "is_staff", "is_superuser", "company")
    search_fields = ("login_id", "name", "email", "phone")
    fieldsets = (
        (None, {"fields": ("login_id", "password")}),
        ("프로필", {"fields": ("name", "email", "phone")}),
        ("회사 · 역할", {"fields": ("company", "role", "manager", "daily_quota")}),
        ("권한", {"fields": ("is_active", "is_staff", "is_approver",
                            "is_superuser", "groups", "user_permissions")}),
        ("기타", {"fields": ("last_login",)}),
    )
    readonly_fields = ("last_login",)


admin.site.register(InviteToken)

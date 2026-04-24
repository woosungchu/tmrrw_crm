from django.apps import AppConfig


class CommunicationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.communications"
    verbose_name = "커뮤니케이션 (SMS·알림톡·콜백)"

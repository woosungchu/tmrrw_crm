from django.db import models

from apps.common.models import CompanyScopedModel


class Template(CompanyScopedModel):
    """SMS/알림톡 본문 템플릿. `{name}`, `{phone}`, `{필드코드}` 형식 치환."""

    CHANNEL_CHOICES = [
        ("sms", "SMS"),
        ("alimtalk", "알림톡"),
    ]

    title = models.CharField(max_length=100)
    body = models.TextField(help_text="변수: {name} {phone} {fields.키}")
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES, default="sms")
    variables = models.JSONField(default=list, blank=True, help_text="['name','phone',...]")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["title"]
        indexes = [models.Index(fields=["company", "is_active"])]

    def __str__(self):
        return self.title


class Callback(CompanyScopedModel):
    """상담사가 특정 시각에 다시 연락하기로 한 리드."""

    STATUS_CHOICES = [
        ("pending", "대기"),
        ("done", "완료"),
        ("missed", "미처리"),
    ]

    lead = models.ForeignKey(
        "leads.Lead", on_delete=models.CASCADE, related_name="callbacks",
    )
    agent = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="callbacks",
    )
    scheduled_at = models.DateTimeField(db_index=True)
    note = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    reminder_sent = models.BooleanField(default=False, db_index=True)
    created_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="created_callbacks",
    )

    class Meta:
        ordering = ["scheduled_at"]
        indexes = [
            models.Index(fields=["agent", "status", "scheduled_at"]),
            models.Index(fields=["company", "status", "scheduled_at"]),
        ]

    def __str__(self):
        return f"{self.lead_id} @ {self.scheduled_at:%Y-%m-%d %H:%M}"

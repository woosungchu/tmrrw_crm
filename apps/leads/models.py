import hashlib

from django.db import models

from apps.common.models import CompanyScopedModel, TimestampedModel


def phone_to_hash(phone):
    """전화번호를 숫자만 정제해서 sha256 해싱 (중복/블랙리스트 감지용)."""
    if not phone:
        return ""
    digits = "".join(c for c in phone if c.isdigit())
    return hashlib.sha256(digits.encode("utf-8")).hexdigest() if digits else ""


def phone_to_masked(phone):
    """'01012345678' → '010-****-5678'. 로그·블랙리스트 표시용."""
    if not phone:
        return ""
    digits = "".join(c for c in phone if c.isdigit())
    if len(digits) < 7:
        return phone
    if len(digits) >= 10:
        return f"{digits[:3]}-****-{digits[-4:]}"
    return f"****-{digits[-4:]}"


class Lead(CompanyScopedModel):
    STATUS_CHOICES = [
        ("new", "접수"),
        ("contacted", "상담중"),
        ("qualified", "선별중"),
        ("negotiating", "진행중"),
        ("won", "결과-성사"),
        ("lost", "결과-실패"),
    ]
    ASSIGNMENT_CHOICES = [
        ("auto", "자동"),
        ("manual", "수동"),
        ("unassigned", "미배정"),
    ]
    NOTI_STATUS_CHOICES = [
        ("ok", "정상"),
        ("failed", "실패"),
        ("failed_cleared", "조치완료"),
        ("n/a", "해당없음"),
    ]

    source = models.ForeignKey("sources.Source", on_delete=models.PROTECT, related_name="leads")
    intake = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="intake_leads",
    )
    agent = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="agent_leads",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="new", db_index=True)
    assignment_type = models.CharField(
        max_length=20, choices=ASSIGNMENT_CHOICES, default="unassigned",
    )

    name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    phone_hash = models.CharField(max_length=64, blank=True, db_index=True)

    fields = models.JSONField(default=dict, blank=True)

    duplicate_of = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="duplicates",
    )

    noti_status = models.CharField(max_length=20, choices=NOTI_STATUS_CHOICES, default="n/a")
    noti_last_error = models.TextField(blank=True)

    external_id = models.CharField(max_length=200, blank=True)
    external_ip = models.GenericIPAddressField(null=True, blank=True)

    received_at = models.DateTimeField(auto_now_add=True)
    contacted_at = models.DateTimeField(null=True, blank=True)
    qualified_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    is_deleted = models.BooleanField(default=False, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["company", "status", "-received_at"]),
            models.Index(fields=["company", "agent", "status"]),
            models.Index(fields=["company", "source", "-received_at"]),
            models.Index(fields=["company", "phone_hash"]),
            models.Index(fields=["company", "noti_status"]),
        ]
        ordering = ["-received_at"]

    def __str__(self):
        return f"{self.name or self.phone} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        if self.phone and not self.phone_hash:
            self.phone_hash = phone_to_hash(self.phone)
        super().save(*args, **kwargs)


class TimelineEntry(TimestampedModel):
    TYPE_CHOICES = [
        ("received", "리드 수신"),
        ("status_change", "상태 변경"),
        ("memo", "메모"),
        ("sms_sent", "SMS 발송"),
        ("alimtalk_sent", "알림톡 발송"),
        ("callback_scheduled", "콜백 예약"),
        ("noti_sent", "NOTI 전송"),
        ("noti_failed", "NOTI 실패"),
        ("assigned", "배정"),
        ("reassigned", "재배정"),
        ("field_changed", "필드 변경"),
        ("blacklisted", "블랙리스트 추가"),
        ("blacklist_hit", "블랙리스트 차단"),
        ("call_initiated", "통화 시도"),
    ]

    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name="timeline")
    type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    actor = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True,
    )
    at = models.DateTimeField(auto_now_add=True)
    payload = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-at"]
        indexes = [models.Index(fields=["lead", "-at"])]

    def __str__(self):
        return f"{self.lead_id} · {self.get_type_display()} · {self.at:%Y-%m-%d %H:%M}"


class Blacklist(CompanyScopedModel):
    """전화번호 기반 블랙리스트. phone_hash 로 공개 API 수신 시 매칭."""

    phone_hash = models.CharField(max_length=64)
    phone_masked = models.CharField(max_length=20, help_text="010-****-1234 형식")
    reason = models.TextField(blank=True)
    added_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True,
    )
    source_lead = models.ForeignKey(
        Lead, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="generated_blacklists",
        help_text="이 리드를 계기로 추가된 경우 연결",
    )

    class Meta:
        ordering = ["-created_at"]
        unique_together = [["company", "phone_hash"]]
        indexes = [models.Index(fields=["company", "phone_hash"])]

    def __str__(self):
        return f"{self.phone_masked} ({self.reason[:30]})"

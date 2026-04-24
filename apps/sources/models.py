import hashlib
import secrets

from django.db import models

from apps.common.models import CompanyScopedModel, TimestampedModel


class Source(CompanyScopedModel):
    """리드 유입 채널 (광고 랜딩·자사 폼·수기 입력 등)."""
    title = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    tmrw_form_id = models.CharField(
        max_length=100, blank=True,
        help_text="tmrw_web 연동용 외부 form_id 매핑 (선택)",
    )
    field_map = models.JSONField(
        default=dict, blank=True,
        help_text="외부 payload key → CustomField code 매핑",
    )
    noti_webhook_url = models.URLField(
        max_length=500, blank=True,
        help_text="리드 수신 후 외부 시스템 알림용 Webhook URL (선택). 실패 시 '빨간불'",
    )

    class Meta:
        indexes = [models.Index(fields=["company", "is_active"])]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.company.name})"


class ApiKey(TimestampedModel):
    """
    Bearer 토큰 기반 API 키. 토큰 전체는 저장하지 않고 해시만 저장.
    생성 시점 1회만 plaintext 노출.
    """
    source = models.ForeignKey(Source, on_delete=models.CASCADE, related_name="api_keys")
    token_hash = models.CharField(max_length=64, db_index=True)
    token_prefix = models.CharField(max_length=12, help_text="UI 표시용 (tkr_XXXXXX)")
    label = models.CharField(max_length=100, blank=True)
    created_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="created_api_keys",
    )
    revoked_at = models.DateTimeField(null=True, blank=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        status = "revoked" if self.revoked_at else "active"
        return f"{self.token_prefix}… ({self.source.title}) [{status}]"

    @property
    def is_active(self):
        return self.revoked_at is None

    @classmethod
    def generate(cls, source, user, label=""):
        """
        새 토큰 생성. 반환: (api_key instance, plaintext_token).
        plaintext_token 은 즉시 UI 에 1회 노출 후 사라짐.
        """
        raw = "tkr_" + secrets.token_urlsafe(32)
        prefix = raw[:12]  # "tkr_XXXXXXXX"
        token_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        api_key = cls.objects.create(
            source=source,
            token_hash=token_hash,
            token_prefix=prefix,
            label=label,
            created_by=user,
        )
        return api_key, raw

    @classmethod
    def verify(cls, raw_token):
        """
        요청에서 받은 plaintext 토큰을 검증.
        반환: 매칭되는 활성 ApiKey 인스턴스 또는 None.
        """
        if not raw_token or not raw_token.startswith("tkr_"):
            return None
        prefix = raw_token[:12]
        token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        return cls.objects.filter(
            token_prefix=prefix, token_hash=token_hash, revoked_at__isnull=True
        ).select_related("source", "source__company").first()

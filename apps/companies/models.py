from django.db import models
from apps.common.models import TimestampedModel


class Company(TimestampedModel):
    PLAN_CHOICES = [
        ("trial", "Trial"),
        ("starter", "Starter"),
        ("pro", "Pro"),
        ("enterprise", "Enterprise"),
    ]
    BILLING_STATUS = [
        ("active", "활성"),
        ("past_due", "연체"),
        ("canceled", "해지"),
        ("trial", "체험중"),
        ("read_only", "읽기전용"),
    ]

    name = models.CharField(max_length=200)
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default="trial")
    billing_status = models.CharField(max_length=20, choices=BILLING_STATUS, default="trial")
    trial_end = models.DateTimeField(null=True, blank=True)
    timezone = models.CharField(max_length=50, default="Asia/Seoul")
    industry_preset = models.CharField(max_length=20, blank=True)
    logo_url = models.URLField(blank=True)
    owner = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="owned_companies",
        null=True,
        blank=True,
    )
    is_internal_test = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    def is_over_limit(self, metric):
        """월 리드·SMS 한도 초과 여부. Billing.usage_* 와 plan 별 한도 비교."""
        billing = getattr(self, "billing", None)
        if not billing:
            return False
        limits = PLAN_LIMITS.get(self.plan, PLAN_LIMITS["trial"])
        usage_attr = f"usage_{metric}_month"
        limit = limits.get(metric)
        if limit is None:
            return False
        return getattr(billing, usage_attr, 0) >= limit


# plan 별 월 한도 (v1/v2 기준, v3 에서 조정 가능)
PLAN_LIMITS = {
    "trial":      {"leads": 200,   "sms": 50,     "storage_mb": 500},
    "starter":    {"leads": 3000,  "sms": 500,    "storage_mb": 2000},
    "pro":        {"leads": 30000, "sms": 5000,   "storage_mb": 10000},
    "enterprise": {"leads": None,  "sms": None,   "storage_mb": None},
}


class AssignmentConfig(TimestampedModel):
    TIE_BREAKER_CHOICES = [
        ("round_robin", "Round Robin"),
        ("least_loaded", "Least Loaded"),
    ]

    company = models.OneToOneField(
        Company, on_delete=models.CASCADE, related_name="assignment_config"
    )
    auto_on = models.BooleanField(default=False)
    weekdays = models.JSONField(default=list, help_text="[0..6] 월=0")
    time_start = models.TimeField(default="09:00")
    time_end = models.TimeField(default="18:00")
    tie_breaker = models.CharField(
        max_length=20, choices=TIE_BREAKER_CHOICES, default="round_robin"
    )

    def __str__(self):
        return f"AssignmentConfig({self.company.name})"


class Billing(TimestampedModel):
    company = models.OneToOneField(
        Company, on_delete=models.CASCADE, related_name="billing"
    )
    plan = models.CharField(max_length=20)
    portone_billing_key = models.CharField(max_length=200, blank=True)
    pg_provider = models.CharField(max_length=30, default="tosspayments")
    next_billing_at = models.DateTimeField(null=True, blank=True)
    usage_leads_month = models.IntegerField(default=0)
    usage_sms_month = models.IntegerField(default=0)
    usage_storage_mb = models.IntegerField(default=0)
    cycle_start = models.DateField()

    def __str__(self):
        return f"Billing({self.company.name})"


class Invoice(TimestampedModel):
    STATUS_CHOICES = [
        ("pending", "대기"),
        ("paid", "결제완료"),
        ("failed", "실패"),
        ("refunded", "환불"),
    ]

    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="invoices"
    )
    amount = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    portone_payment_id = models.CharField(max_length=100, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    receipt_url = models.URLField(blank=True)

    def __str__(self):
        return f"Invoice({self.company.name} · {self.amount}₩ · {self.status})"

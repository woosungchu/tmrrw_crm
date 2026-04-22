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

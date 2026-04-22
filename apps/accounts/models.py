from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from apps.common.models import TimestampedModel


class UserManager(BaseUserManager):
    def create_user(self, login_id, password=None, **extra):
        if not login_id:
            raise ValueError("login_id 필수")
        user = self.model(login_id=login_id, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, login_id, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        extra.setdefault("role", "owner")
        return self.create_user(login_id, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ("owner", "오너"),
        ("admin", "관리자"),
        ("intake", "접수"),
        ("agent", "상담사"),
    ]

    company = models.ForeignKey(
        "companies.Company",
        on_delete=models.CASCADE,
        related_name="users",
        null=True,
        blank=True,
    )
    login_id = models.CharField(max_length=50, unique=True)
    email = models.EmailField(blank=True)
    name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="agent")
    manager = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="reports"
    )
    daily_quota = models.PositiveIntegerField(
        null=True, blank=True, help_text="agent 자동 배정 쿼터. null=무제한"
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "login_id"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        indexes = [models.Index(fields=["company", "role", "is_active"])]

    def __str__(self):
        return f"{self.name or self.login_id} ({self.role})"


class InviteToken(TimestampedModel):
    company = models.ForeignKey("companies.Company", on_delete=models.CASCADE, related_name="invites")
    email = models.EmailField()
    role = models.CharField(max_length=20, choices=User.ROLE_CHOICES)
    manager = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    token = models.CharField(max_length=64, unique=True, db_index=True)
    invited_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="sent_invites"
    )
    expires_at = models.DateTimeField()
    consumed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Invite({self.email} → {self.company.name}, {self.role})"

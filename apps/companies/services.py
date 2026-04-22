"""회사·오너 생성 등 도메인 서비스."""
from datetime import timedelta
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from .models import Company, AssignmentConfig, Billing


@transaction.atomic
def create_company_with_owner(*, company_name, owner_name, email, phone, login_id, password):
    """
    신규 회사 + 오너 유저 + 기본 AssignmentConfig + Billing 을 한 트랜잭션으로 생성.
    반환: (company, owner)
    """
    today = timezone.now()

    company = Company.objects.create(
        name=company_name,
        plan="trial",
        billing_status="trial",
        trial_end=today + timedelta(days=14),
    )

    owner = User.objects.create_user(
        login_id=login_id,
        password=password,
        email=email,
        name=owner_name,
        phone=phone or "",
        role="owner",
        company=company,
        is_staff=False,  # Django admin 접근권은 superuser 만
    )

    # 회사의 오너 역참조 설정
    company.owner = owner
    company.save(update_fields=["owner"])

    # 기본 배정 설정 (수동 모드로 시작)
    AssignmentConfig.objects.create(
        company=company,
        auto_on=False,
        weekdays=[0, 1, 2, 3, 4],  # 평일 기본
        time_start="09:00",
        time_end="18:00",
        tie_breaker="round_robin",
    )

    # 결제 객체 (체험중, billing_key 없음)
    Billing.objects.create(
        company=company,
        plan="trial",
        cycle_start=today.date(),
    )

    return company, owner

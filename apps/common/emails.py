"""
알림 이메일 헬퍼.

EMAIL_HOST_USER env 미설정 시 console backend 로 fallback (GAE 로그에 출력).
한 번이라도 실패해도 사용자 흐름에 영향 없도록 fail_silently=True.
"""
from __future__ import annotations

import logging
from urllib.parse import urljoin

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string


logger = logging.getLogger(__name__)


def _site_base_url() -> str:
    return getattr(settings, "SITE_BASE_URL", "https://tmrrwcrm.com")


def _from_email() -> str:
    return getattr(settings, "DEFAULT_FROM_EMAIL", "tmrrwcrm <noreply@tmrrwcrm.com>")


def _send(subject: str, template: str, context: dict, recipients: list[str]) -> None:
    """공통 발송 헬퍼. 실패해도 메인 흐름엔 영향 없음."""
    if not recipients:
        return
    try:
        body = render_to_string(template, context)
        send_mail(
            subject=subject,
            message=body,
            from_email=_from_email(),
            recipient_list=recipients,
            fail_silently=True,
        )
    except Exception as e:
        logger.exception("이메일 발송 실패: %s (%s)", subject, e)


def notify_approvers_new_signup(company) -> None:
    """신규 가입 → 모든 승인자에게."""
    from apps.accounts.models import User
    approvers = list(
        User.objects.filter(is_approver=True, is_active=True)
        .exclude(email="")
        .values_list("email", flat=True)
    )
    if not approvers:
        return
    ctx = {
        "company": company,
        "approval_url": urljoin(_site_base_url(), "/superadmin/approvals/"),
    }
    _send(
        f"[tmrrwcrm] 새 베타 신청: {company.name}",
        "emails/new_signup_for_approver.txt", ctx, approvers,
    )


def notify_owner_approved(company) -> None:
    """승인 완료 → 회사 오너에게."""
    if not company.owner or not company.owner.email:
        return
    ctx = {"company": company, "app_url": urljoin(_site_base_url(), "/app/")}
    _send(
        f"[tmrrwcrm] {company.name} 베타 승인 완료",
        "emails/approved.txt", ctx, [company.owner.email],
    )


def notify_owner_denied(company) -> None:
    """거부 → 회사 오너에게."""
    if not company.owner or not company.owner.email:
        return
    ctx = {"company": company}
    _send(
        f"[tmrrwcrm] {company.name} 베타 신청 거부",
        "emails/denied.txt", ctx, [company.owner.email],
    )

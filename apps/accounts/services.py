"""accounts 도메인 서비스 (초대 생성·수락)."""
import secrets
from datetime import timedelta

from django.contrib.auth import login
from django.core.mail import send_mail
from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from .models import User, InviteToken


INVITE_EXPIRY_DAYS = 7


def create_and_send_invite(*, company, email, role, manager, invited_by, site_base_url):
    """
    InviteToken 생성 + 수락 링크를 이메일로 전송.
    site_base_url: "http://127.0.0.1:8000" 같은 origin (스킴 포함, trailing slash 없이).
    """
    token = secrets.token_urlsafe(32)
    invite = InviteToken.objects.create(
        company=company,
        email=email,
        role=role,
        manager=manager,
        token=token,
        invited_by=invited_by,
        expires_at=timezone.now() + timedelta(days=INVITE_EXPIRY_DAYS),
    )

    accept_path = reverse("accept_invite", kwargs={"token": token})
    accept_url = f"{site_base_url}{accept_path}"

    subject = f"[tmrrwcrm] {company.name} 에서 초대했습니다"
    body = (
        f"안녕하세요.\n\n"
        f"{invited_by.name or invited_by.login_id} 님이 {company.name} 의 {dict(User.ROLE_CHOICES).get(role, role)} 역할로 당신을 초대했습니다.\n\n"
        f"아래 링크에서 7일 내에 계정을 생성하세요:\n{accept_url}\n\n"
        f"- tmrrwcrm\n"
    )
    send_mail(subject, body, None, [email])

    return invite


def is_invite_usable(invite):
    """초대 토큰이 아직 사용 가능한 상태인지."""
    if invite.consumed_at is not None:
        return False
    if invite.expires_at <= timezone.now():
        return False
    return True


@transaction.atomic
def accept_invite_and_create_user(*, invite, name, phone, login_id, password):
    """초대 수락 → User 생성 + 토큰 소비."""
    user = User.objects.create_user(
        login_id=login_id,
        password=password,
        email=invite.email,
        name=name,
        phone=phone or "",
        role=invite.role,
        manager=invite.manager,
        company=invite.company,
    )
    invite.consumed_at = timezone.now()
    invite.save(update_fields=["consumed_at"])
    return user

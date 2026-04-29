from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from .forms import InviteForm, AcceptInviteForm
from .models import InviteToken
from .services import create_and_send_invite, is_invite_usable, accept_invite_and_create_user


def _can_invite(user):
    return user.is_authenticated and user.role in ("owner", "admin")


@login_required
def blocked_page(request):
    """billing_status 가 차단 상태인 회사의 user 가 도달하는 안내 페이지."""
    company = request.company
    status = company.billing_status if company else None
    return render(request, 'app/blocked.html', {
        "company": company,
        "status": status,
    })


@login_required
def app_home(request):
    """로그인 후 랜딩 = 대시보드."""
    from apps.dashboard.services import compute_dashboard
    if not request.company:
        messages.warning(request, "회사가 설정되지 않은 계정입니다.")
        return render(request, 'app/home.html', {"no_company": True})
    data = compute_dashboard(request.user, request.company)
    return render(request, 'app/home.html', {"data": data})


@login_required
def invite_list(request):
    """기존 URL 유지용 — 통합 팀 관리 페이지로 redirect (초대 탭 활성)."""
    from django.urls import reverse
    return redirect(f"{reverse('team_settings')}#invite")


def accept_invite(request, token):
    """초대 링크 수락. 이미 로그인 상태면 로그아웃 권고."""
    invite = get_object_or_404(InviteToken, token=token)

    if not is_invite_usable(invite):
        return render(request, "public/invite_invalid.html", {
            "reason": "이미 사용됐거나 만료된 초대입니다.",
        })

    if request.user.is_authenticated:
        return render(request, "public/invite_invalid.html", {
            "reason": "초대를 수락하려면 먼저 로그아웃하세요.",
        })

    if request.method == "POST":
        form = AcceptInviteForm(request.POST)
        if form.is_valid():
            user = accept_invite_and_create_user(
                invite=invite,
                name=form.cleaned_data["name"],
                phone=form.cleaned_data["phone"],
                login_id=form.cleaned_data["login_id"],
                password=form.cleaned_data["password"],
            )
            login(request, user)
            messages.success(request, f"환영합니다, {user.name} 님!")
            return redirect("/app/")
    else:
        form = AcceptInviteForm()

    return render(request, "public/invite_accept.html", {
        "invite": invite,
        "form": form,
    })

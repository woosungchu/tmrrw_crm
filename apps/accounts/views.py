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
    """초대 목록 + 신규 초대 폼."""
    if not _can_invite(request.user):
        return HttpResponseForbidden("관리 권한이 필요합니다.")

    company = request.company
    if not company:
        messages.error(request, "회사가 설정되지 않은 계정입니다. Django admin 에서 본인 계정에 회사를 지정하거나, 신규 회사로 가입해주세요.")
        return redirect("/app/")

    form = InviteForm(company=company)

    if request.method == "POST":
        form = InviteForm(request.POST, company=company)
        if form.is_valid():
            site_base_url = f"{request.scheme}://{request.get_host()}"
            invite = create_and_send_invite(
                company=company,
                email=form.cleaned_data["email"],
                role=form.cleaned_data["role"],
                manager=form.cleaned_data["manager"],
                invited_by=request.user,
                site_base_url=site_base_url,
            )
            messages.success(request, f"{invite.email} 에게 초대 메일을 보냈습니다.")
            return redirect("invite_list")

    invites = InviteToken.objects.filter(company=company).order_by("-created_at")[:50]

    return render(request, "app/invite_list.html", {
        "form": form,
        "invites": invites,
    })


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

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect
from django.urls import reverse

from .forms import SignupForm, AssignmentConfigForm
from .models import AssignmentConfig
from .services import create_company_with_owner

from apps.accounts.forms import InviteForm
from apps.accounts.models import InviteToken, User
from apps.accounts.services import create_and_send_invite


def landing(request):
    # 로그인 상태면 바로 대시보드로
    if request.user.is_authenticated:
        return redirect('/app/')
    feature_list = [
        "리드 CRUD · 엑셀 다운로드",
        "중복 감지 · 블랙리스트",
        "상태 머신 (접수→상담→결과)",
        "타임라인 · 메모",
        "SMS 발송 (템플릿 변수)",
        "콜백 예약 · 브라우저 알림",
        "통화 원클릭 (Phone Link)",
        "자동 배정 엔진",
        "대시보드 · KPI 차트",
        "역할별 권한 (owner/admin/intake/agent)",
        "멀티 채널 수신 API",
        "팀 초대 · 조직 계층",
    ]
    return render(request, 'public/landing.html', {"feature_list": feature_list})


def signup(request):
    if request.user.is_authenticated:
        return redirect('/app/')

    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            company, owner = create_company_with_owner(
                company_name=form.cleaned_data['company_name'],
                owner_name=form.cleaned_data['name'],
                email=form.cleaned_data['email'],
                phone=form.cleaned_data['phone'],
                login_id=form.cleaned_data['login_id'],
                password=form.cleaned_data['password'],
            )
            login(request, owner)
            # 승인자에게 메일 알림 (실패해도 가입엔 영향 없음)
            try:
                from apps.common.emails import notify_approvers_new_signup
                notify_approvers_new_signup(company)
            except Exception:
                pass
            messages.success(request, f"{company.name} 신청 완료! 운영팀 승인 후 사용 가능합니다.")
            return redirect('/app/')
    else:
        form = SignupForm()

    return render(request, 'public/signup.html', {'form': form})


@login_required
def assignment_settings(request):
    """기존 URL 유지용 — 통합 페이지로 redirect (자동 배정 탭 활성)."""
    return redirect(f"{reverse('team_settings')}#assignment")


@login_required
def team_settings(request):
    """
    팀 관리 통합 페이지: 멤버 + 팀원 초대 + 자동 배정 (탭 UI).
    POST 요청은 hidden 'form_type' 으로 분기 (admin/owner 만):
      - invite: 초대 메일 발송
      - assignment: 자동 배정 설정 저장 (+ 비율 가중치 동시 저장)

    조회 (GET) 는 회사 소속 모든 role (agent 포함) 허용.
    POST 는 owner/admin 만.
    """
    if not request.company:
        return redirect("/app/")

    is_manager = request.user.role in ("owner", "admin")
    company = request.company
    config, _ = AssignmentConfig.objects.get_or_create(company=company)

    invite_form = InviteForm(company=company) if is_manager else None
    assignment_form = AssignmentConfigForm(instance=config) if is_manager else None

    if request.method == "POST":
        if not is_manager:
            return HttpResponseForbidden("관리 권한이 필요합니다.")

        form_type = request.POST.get("form_type", "")

        if form_type == "invite":
            invite_form = InviteForm(request.POST, company=company)
            if invite_form.is_valid():
                site_base_url = f"{request.scheme}://{request.get_host()}"
                invite = create_and_send_invite(
                    company=company,
                    email=invite_form.cleaned_data["email"],
                    role=invite_form.cleaned_data["role"],
                    manager=invite_form.cleaned_data["manager"],
                    invited_by=request.user,
                    site_base_url=site_base_url,
                )
                messages.success(request, f"{invite.email} 에게 초대 메일을 보냈습니다.")
                return redirect(f"{reverse('team_settings')}#invite")

        elif form_type == "assignment":
            assignment_form = AssignmentConfigForm(request.POST, instance=config)
            if assignment_form.is_valid():
                assignment_form.save()
                _save_agent_weights(company, request.POST)
                messages.success(request, "자동 배정 설정 저장됨.")
                return redirect(f"{reverse('team_settings')}#assignment")

    # 모든 role 이 보는 멤버 목록 (owner → admin → intake → agent 순으로 정렬)
    role_order = {"owner": 0, "admin": 1, "intake": 2, "agent": 3}
    members = list(
        User.objects.filter(company=company).order_by("-is_active", "name", "login_id")
    )
    members.sort(key=lambda u: (not u.is_active, role_order.get(u.role, 99), (u.name or u.login_id or "").lower()))

    invites = InviteToken.objects.filter(company=company).order_by("-created_at")[:50] if is_manager else None
    agents = User.objects.filter(
        company=company, role="agent", is_active=True,
    ).order_by("name", "login_id") if is_manager else None

    return render(request, "app/team_settings.html", {
        "invite_form": invite_form,
        "assignment_form": assignment_form,
        "invites": invites,
        "agents": agents,
        "config": config,
        "members": members,
        "is_manager": is_manager,
    })


def _save_agent_weights(company, post_data):
    """POST 데이터의 weight_<user_id> 키를 모아 한 번에 update."""
    updates = []
    for key, value in post_data.items():
        if not key.startswith("weight_"):
            continue
        try:
            user_id = int(key.split("_", 1)[1])
            weight = max(int(value or 0), 0)
        except (ValueError, IndexError):
            continue
        updates.append((user_id, weight))
    if not updates:
        return
    # bulk update — 회사 소속 + agent 역할만 (보안)
    user_ids = [uid for uid, _ in updates]
    weight_map = dict(updates)
    qs = User.objects.filter(id__in=user_ids, company=company, role="agent")
    for u in qs:
        u.assignment_weight = weight_map[u.id]
    User.objects.bulk_update(qs, ["assignment_weight"])

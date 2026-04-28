from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect

from .forms import SignupForm, AssignmentConfigForm
from .models import AssignmentConfig
from .services import create_company_with_owner


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
    """자동 배정 설정 편집 (owner/admin)."""
    if request.user.role not in ("owner", "admin"):
        return HttpResponseForbidden("관리 권한이 필요합니다.")
    if not request.company:
        return redirect("/app/")

    config, _ = AssignmentConfig.objects.get_or_create(company=request.company)

    if request.method == "POST":
        form = AssignmentConfigForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, "자동 배정 설정 저장됨.")
            return redirect("assignment_settings")
    else:
        form = AssignmentConfigForm(instance=config)

    return render(request, "app/assignment_settings.html", {
        "form": form,
        "config": config,
    })

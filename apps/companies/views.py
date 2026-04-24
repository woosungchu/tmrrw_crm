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
    return render(request, 'public/landing.html')


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
            messages.success(request, f"{company.name} 가입 완료! 14일 무료 체험 시작.")
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

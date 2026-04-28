"""베타 신청 승인 관리. is_approver=True 인 user 만 접근."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.companies.models import Company


def _is_approver(user):
    return user.is_authenticated and (user.is_superuser or getattr(user, "is_approver", False))


approver_required = user_passes_test(_is_approver, login_url="/accounts/login/")


@login_required
@approver_required
def approval_list(request):
    """탭별 신청 목록.
    ?status=pending(default) / granted / denied / all"""
    status = request.GET.get("status", "pending")
    qs = Company.objects.select_related("owner").order_by("-created_at")
    if status == "pending":
        qs = qs.filter(billing_status="pending_approval")
    elif status == "granted":
        qs = qs.filter(billing_status="granted_free")
    elif status == "denied":
        qs = qs.filter(billing_status="denied")
    # else: 전체

    counts = {
        "pending": Company.objects.filter(billing_status="pending_approval").count(),
        "granted": Company.objects.filter(billing_status="granted_free").count(),
        "denied": Company.objects.filter(billing_status="denied").count(),
    }

    return render(request, "superadmin/approval_list.html", {
        "companies": qs[:200],
        "current_status": status,
        "counts": counts,
    })


@login_required
@approver_required
@require_POST
@transaction.atomic
def approval_approve(request, company_id):
    if not _is_approver(request.user):
        return HttpResponseForbidden("권한 없음")
    company = get_object_or_404(Company, pk=company_id)
    company.billing_status = "granted_free"
    company.approved_at = timezone.now()
    company.approved_by = request.user
    company.denial_reason = ""  # 재신청 후 승인된 경우 이전 사유 클리어
    company.save(update_fields=["billing_status", "approved_at", "approved_by",
                                  "denial_reason", "updated_at"])
    try:
        from apps.common.emails import notify_owner_approved
        notify_owner_approved(company)
    except Exception:
        pass
    messages.success(request, f"{company.name} 승인 완료.")
    return redirect("superadmin_approval_list")


@login_required
@approver_required
@require_POST
@transaction.atomic
def approval_deny(request, company_id):
    if not _is_approver(request.user):
        return HttpResponseForbidden("권한 없음")
    company = get_object_or_404(Company, pk=company_id)
    reason = (request.POST.get("reason") or "").strip()[:500]
    company.billing_status = "denied"
    company.denial_reason = reason
    company.save(update_fields=["billing_status", "denial_reason", "updated_at"])
    try:
        from apps.common.emails import notify_owner_denied
        notify_owner_denied(company)
    except Exception:
        pass
    messages.success(request, f"{company.name} 신청 거부.")
    return redirect("superadmin_approval_list")


@login_required
@approver_required
@require_POST
@transaction.atomic
def approval_reopen(request, company_id):
    """이미 거부된 신청을 다시 pending 으로 되돌림 (재검토)."""
    if not _is_approver(request.user):
        return HttpResponseForbidden("권한 없음")
    company = get_object_or_404(Company, pk=company_id)
    company.billing_status = "pending_approval"
    company.denial_reason = ""
    company.save(update_fields=["billing_status", "denial_reason", "updated_at"])
    messages.success(request, f"{company.name} 재검토 대기로 되돌림.")
    return redirect("superadmin_approval_list")

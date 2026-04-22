import csv
from io import BytesIO

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.accounts.models import User
from .forms import LeadManualForm
from .models import Lead, TimelineEntry, phone_to_hash


def _scope_leads_for_user(user, company):
    """역할별 리드 스코프 (v3 §9)."""
    qs = Lead.objects.filter(company=company, is_deleted=False)
    if user.role in ("owner", "admin"):
        return qs
    if user.role == "intake":
        return qs.filter(intake=user)
    if user.role == "agent":
        return qs.filter(agent=user)
    return qs.none()


def _can_manual_create(user):
    return user.role in ("owner", "admin", "intake")


@login_required
def lead_list(request):
    if not request.company:
        return redirect("/app/")

    qs = _scope_leads_for_user(request.user, request.company).select_related("source", "intake", "agent")

    status = request.GET.get("status", "")
    if status:
        qs = qs.filter(status=status)

    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(phone__icontains=q))

    paginator = Paginator(qs, 50)
    page = paginator.get_page(request.GET.get("page") or 1)

    # 상태별 탭 카운트
    full_scope = _scope_leads_for_user(request.user, request.company)
    counts_map = {code: 0 for code, _ in Lead.STATUS_CHOICES}
    for row in full_scope.values("status").annotate(n=Count("id")):
        counts_map[row["status"]] = row["n"]
    status_tabs = [
        {"code": code, "label": label, "count": counts_map[code]}
        for code, label in Lead.STATUS_CHOICES
    ]

    return render(request, "app/leads_list.html", {
        "page": page,
        "status_tabs": status_tabs,
        "total_count": sum(counts_map.values()),
        "current_status": status,
        "q": q,
        "can_create": _can_manual_create(request.user),
    })


@login_required
def lead_detail(request, pk):
    if not request.company:
        return redirect("/app/")

    lead = get_object_or_404(
        _scope_leads_for_user(request.user, request.company)
        .select_related("source", "intake", "agent", "company"),
        pk=pk,
    )
    timeline = lead.timeline.select_related("actor").order_by("-at")[:200]

    # 액션용 선택지
    agents = User.objects.filter(
        company=request.company, role__in=["agent", "admin", "owner"], is_active=True,
    ).order_by("name")

    return render(request, "app/lead_detail.html", {
        "lead": lead,
        "timeline": timeline,
        "agents": agents,
        "status_choices": Lead.STATUS_CHOICES,
        "can_edit": request.user.role in ("owner", "admin", "intake") or lead.agent_id == request.user.id,
    })


@login_required
@require_POST
def lead_change_status(request, pk):
    lead = get_object_or_404(_scope_leads_for_user(request.user, request.company), pk=pk)
    new_status = request.POST.get("status", "")
    valid_codes = {c for c, _ in Lead.STATUS_CHOICES}
    if new_status not in valid_codes:
        return HttpResponseForbidden("잘못된 상태")

    if lead.status == new_status:
        return redirect("lead_detail", pk=lead.pk)

    # 권한: owner/admin/intake 는 모두 가능. agent 는 본인 담당 리드만.
    if request.user.role == "agent" and lead.agent_id != request.user.id:
        return HttpResponseForbidden("담당 리드만 변경 가능")

    old_status = lead.status
    lead.status = new_status
    now = timezone.now()
    if new_status == "contacted" and not lead.contacted_at:
        lead.contacted_at = now
    elif new_status == "qualified" and not lead.qualified_at:
        lead.qualified_at = now
    elif new_status in ("won", "lost") and not lead.closed_at:
        lead.closed_at = now
    lead.save(update_fields=["status", "contacted_at", "qualified_at", "closed_at", "updated_at"])

    TimelineEntry.objects.create(
        lead=lead, type="status_change", actor=request.user,
        payload={"from": old_status, "to": new_status},
    )
    messages.success(request, f"상태 변경: {dict(Lead.STATUS_CHOICES).get(old_status)} → {dict(Lead.STATUS_CHOICES).get(new_status)}")
    return redirect("lead_detail", pk=lead.pk)


@login_required
@require_POST
def lead_assign(request, pk):
    if request.user.role not in ("owner", "admin", "intake"):
        return HttpResponseForbidden("배정 권한 없음")

    lead = get_object_or_404(_scope_leads_for_user(request.user, request.company), pk=pk)
    agent_id = request.POST.get("agent_id") or None
    new_agent = None
    if agent_id:
        new_agent = get_object_or_404(
            User, pk=agent_id, company=request.company, is_active=True,
        )

    old_agent_id = lead.agent_id
    lead.agent = new_agent
    lead.assignment_type = "manual" if new_agent else "unassigned"
    lead.save(update_fields=["agent", "assignment_type", "updated_at"])

    TimelineEntry.objects.create(
        lead=lead,
        type="reassigned" if old_agent_id else "assigned",
        actor=request.user,
        payload={
            "from_agent_id": old_agent_id,
            "to_agent_id": new_agent.id if new_agent else None,
            "reason": "manual",
        },
    )
    messages.success(request, f"담당자 {('지정' if new_agent else '해제')} 완료.")
    return redirect("lead_detail", pk=lead.pk)


@login_required
def lead_create(request):
    if not request.company:
        return redirect("/app/")
    if not _can_manual_create(request.user):
        return HttpResponseForbidden("수동 등록 권한 없음")

    if request.method == "POST":
        form = LeadManualForm(request.POST, company=request.company)
        if form.is_valid():
            source = form.cleaned_data["source"]
            name = form.cleaned_data["name"]
            phone = form.cleaned_data["phone"]
            agent = form.cleaned_data["agent"]
            memo = form.cleaned_data["memo"]

            with transaction.atomic():
                lead = Lead.objects.create(
                    company=request.company,
                    source=source,
                    intake=request.user,
                    agent=agent,
                    assignment_type="manual" if agent else "unassigned",
                    name=name,
                    phone=phone,
                    phone_hash=phone_to_hash(phone),
                    status="new",
                )
                TimelineEntry.objects.create(
                    lead=lead, type="received", actor=request.user,
                    payload={"manual": True},
                )
                if agent:
                    TimelineEntry.objects.create(
                        lead=lead, type="assigned", actor=request.user,
                        payload={"to_agent_id": agent.id, "reason": "manual"},
                    )
                if memo:
                    TimelineEntry.objects.create(
                        lead=lead, type="memo", actor=request.user,
                        payload={"text": memo},
                    )
            messages.success(request, f"리드 #{lead.id} 생성됨.")
            return redirect("lead_detail", pk=lead.pk)
    else:
        form = LeadManualForm(company=request.company)

    return render(request, "app/lead_form.html", {"form": form})


@login_required
def lead_export(request):
    """현재 필터 조건의 리드 목록을 Excel (.xlsx) 로 내려받음."""
    from openpyxl import Workbook

    if not request.company:
        return redirect("/app/")

    qs = _scope_leads_for_user(request.user, request.company).select_related("source", "agent", "intake")
    status = request.GET.get("status", "")
    if status:
        qs = qs.filter(status=status)
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(phone__icontains=q))

    wb = Workbook()
    ws = wb.active
    ws.title = "leads"
    ws.append([
        "#", "이름", "전화", "상태", "채널", "담당", "접수", "수신일시",
        "연락일시", "선별일시", "종결일시", "외부ID", "외부IP",
    ])

    for lead in qs.order_by("-received_at").iterator(chunk_size=500):
        ws.append([
            lead.id,
            lead.name,
            lead.phone,
            lead.get_status_display(),
            lead.source.title if lead.source_id else "",
            (lead.agent.name or lead.agent.login_id) if lead.agent_id else "",
            (lead.intake.name or lead.intake.login_id) if lead.intake_id else "",
            lead.received_at.replace(tzinfo=None) if lead.received_at else None,
            lead.contacted_at.replace(tzinfo=None) if lead.contacted_at else None,
            lead.qualified_at.replace(tzinfo=None) if lead.qualified_at else None,
            lead.closed_at.replace(tzinfo=None) if lead.closed_at else None,
            lead.external_id,
            lead.external_ip or "",
        ])

    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)

    filename = f"leads_{timezone.now():%Y%m%d_%H%M}.xlsx"
    response = HttpResponse(
        buf.read(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f"attachment; filename={filename}"
    return response

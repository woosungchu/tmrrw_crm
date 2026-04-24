from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.leads.models import Lead, TimelineEntry

from .forms import TemplateForm, SendSmsForm, CallbackForm
from .models import Template, Callback
from .services import render_template_body, send_sms


def _can_manage_templates(user):
    return user.role in ("owner", "admin")


# ─── Templates CRUD ───────────────────────────────────────
@login_required
def template_list(request):
    if not request.company:
        return redirect("/app/")
    qs = Template.objects.filter(company=request.company).order_by("-is_active", "title")
    return render(request, "communications/template_list.html", {
        "templates": qs,
        "can_manage": _can_manage_templates(request.user),
    })


@login_required
def template_create(request):
    if not _can_manage_templates(request.user):
        return HttpResponseForbidden("템플릿 관리 권한 없음")
    if request.method == "POST":
        form = TemplateForm(request.POST)
        if form.is_valid():
            tmpl = form.save(commit=False)
            tmpl.company = request.company
            tmpl.save()
            messages.success(request, f"템플릿 '{tmpl.title}' 생성됨.")
            return redirect("template_list")
    else:
        form = TemplateForm()
    return render(request, "communications/template_form.html", {"form": form, "mode": "create"})


@login_required
def template_edit(request, pk):
    if not _can_manage_templates(request.user):
        return HttpResponseForbidden("템플릿 관리 권한 없음")
    tmpl = get_object_or_404(Template, pk=pk, company=request.company)
    if request.method == "POST":
        form = TemplateForm(request.POST, instance=tmpl)
        if form.is_valid():
            form.save()
            messages.success(request, "저장됨.")
            return redirect("template_list")
    else:
        form = TemplateForm(instance=tmpl)
    return render(
        request,
        "communications/template_form.html",
        {"form": form, "mode": "edit", "tmpl": tmpl},
    )


@login_required
@require_POST
def template_delete(request, pk):
    if not _can_manage_templates(request.user):
        return HttpResponseForbidden("템플릿 관리 권한 없음")
    tmpl = get_object_or_404(Template, pk=pk, company=request.company)
    tmpl.delete()
    messages.success(request, "삭제됨.")
    return redirect("template_list")


# ─── SMS 발송 (Lead 상세에서 호출) ─────────────────────────
@login_required
@require_POST
def send_sms_to_lead(request, lead_pk):
    lead = get_object_or_404(Lead, pk=lead_pk, company=request.company, is_deleted=False)
    # 권한: intake/agent 는 본인 담당·접수자 한정
    if request.user.role == "agent" and lead.agent_id != request.user.id:
        return HttpResponseForbidden("담당 리드만 가능")
    if request.user.role == "intake" and lead.intake_id != request.user.id:
        return HttpResponseForbidden("접수한 리드만 가능")

    form = SendSmsForm(request.POST, company=request.company)
    if not form.is_valid():
        for err in form.errors.values():
            messages.error(request, "; ".join(err))
        return redirect("lead_detail", pk=lead.pk)

    if not lead.phone:
        messages.error(request, "전화번호가 없는 리드입니다.")
        return redirect("lead_detail", pk=lead.pk)

    tmpl = form.cleaned_data.get("template")
    freeform = (form.cleaned_data.get("body") or "").strip()
    raw_body = tmpl.body if tmpl else freeform
    rendered = render_template_body(raw_body, lead)

    result = send_sms(lead.phone, rendered)
    TimelineEntry.objects.create(
        lead=lead,
        type="sms_sent" if (tmpl and tmpl.channel == "sms") or not tmpl else "alimtalk_sent",
        actor=request.user,
        payload={
            "template_id": tmpl.id if tmpl else None,
            "template_title": tmpl.title if tmpl else "(프리폼)",
            "body": rendered,
            "provider": result.provider,
            "ok": result.ok,
            "error": result.error,
            "request_id": result.request_id,
        },
    )
    if result.ok:
        msg = f"발송됨 ({'모의' if result.provider == 'dry_run' else 'NCP'})."
        messages.success(request, msg)
    else:
        messages.error(request, f"발송 실패: {result.error}")
    return redirect("lead_detail", pk=lead.pk)


# ─── Callback 예약 ────────────────────────────────────────
@login_required
@require_POST
def callback_create(request, lead_pk):
    lead = get_object_or_404(Lead, pk=lead_pk, company=request.company, is_deleted=False)

    # 예약 대상 agent: 본인(agent) or 리드 담당자(owner/admin)
    if request.user.role == "agent":
        target_agent = request.user
    else:
        target_agent_id = request.POST.get("agent_id") or (lead.agent_id or request.user.id)
        from apps.accounts.models import User
        target_agent = get_object_or_404(
            User, pk=target_agent_id, company=request.company, is_active=True,
        )

    form = CallbackForm(request.POST)
    if not form.is_valid():
        for err in form.errors.values():
            messages.error(request, "; ".join(err))
        return redirect("lead_detail", pk=lead.pk)

    cb = Callback.objects.create(
        company=request.company,
        lead=lead,
        agent=target_agent,
        scheduled_at=form.cleaned_data["scheduled_at"],
        note=form.cleaned_data.get("note", ""),
        created_by=request.user,
    )
    TimelineEntry.objects.create(
        lead=lead, type="callback_scheduled", actor=request.user,
        payload={
            "callback_id": cb.id,
            "scheduled_at": cb.scheduled_at.isoformat(),
            "agent_id": target_agent.id,
            "note": cb.note,
        },
    )
    messages.success(request, "콜백이 예약되었습니다.")
    return redirect("lead_detail", pk=lead.pk)


@login_required
def callback_list(request):
    if not request.company:
        return redirect("/app/")
    qs = Callback.objects.filter(company=request.company).select_related("lead", "agent")
    # 상담사는 본인만
    if request.user.role == "agent":
        qs = qs.filter(agent=request.user)
    status = request.GET.get("status", "pending")
    if status in ("pending", "done", "missed"):
        qs = qs.filter(status=status)
    qs = qs.order_by("scheduled_at")
    return render(request, "communications/callback_list.html", {
        "callbacks": qs[:200],
        "status": status,
    })


@login_required
@require_POST
def callback_done(request, pk):
    cb = get_object_or_404(Callback, pk=pk, company=request.company)
    if request.user.role == "agent" and cb.agent_id != request.user.id:
        return HttpResponseForbidden("본인 콜백만")
    cb.status = "done"
    cb.save(update_fields=["status", "updated_at"])
    messages.success(request, "콜백 완료 처리됨.")
    return redirect("callback_list")


# ─── 브라우저 알림 polling JSON ────────────────────────────
@login_required
def callback_upcoming_json(request):
    """
    현재 유저의 곧 도래하는 콜백을 반환 + reminder_sent=True 마킹.
    프런트엔드에서 60초마다 poll, 결과 있으면 Notification 표시.
    """
    if not request.company or not request.user.is_authenticated:
        return JsonResponse({"callbacks": []})

    now = timezone.now()
    threshold = now + timezone.timedelta(minutes=1)  # 1분 이내 도래
    qs = Callback.objects.filter(
        company=request.company,
        agent=request.user,
        status="pending",
        reminder_sent=False,
        scheduled_at__lte=threshold,
    ).select_related("lead")

    items = []
    for cb in qs[:10]:
        items.append({
            "id": cb.id,
            "lead_id": cb.lead_id,
            "lead_name": cb.lead.name or cb.lead.phone,
            "scheduled_at": cb.scheduled_at.isoformat(),
            "note": cb.note,
        })

    if items:
        Callback.objects.filter(pk__in=[i["id"] for i in items]).update(reminder_sent=True)
        # 미처리 상태 업데이트: 예약 지나간 pending 은 missed 로
    # 1시간+ 이전인데 pending 은 missed 로 정리
    Callback.objects.filter(
        company=request.company,
        agent=request.user,
        status="pending",
        scheduled_at__lt=now - timezone.timedelta(hours=1),
    ).update(status="missed")

    return JsonResponse({"callbacks": items})

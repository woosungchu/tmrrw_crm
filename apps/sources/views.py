from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import SourceForm, ApiKeyLabelForm
from .models import Source, ApiKey


def _can_manage(user):
    return user.is_authenticated and user.role in ("owner", "admin")


def _owned_source_or_403(request, pk):
    source = get_object_or_404(Source, pk=pk)
    if source.company_id != getattr(request.company, "id", None):
        raise PermissionError
    return source


@login_required
def source_list(request):
    if not _can_manage(request.user):
        return HttpResponseForbidden("관리 권한이 필요합니다.")
    if not request.company:
        messages.error(request, "회사가 설정되지 않은 계정입니다.")
        return redirect("/app/")

    sources = Source.objects.filter(company=request.company).order_by("-created_at")
    return render(request, "app/sources_list.html", {"sources": sources})


@login_required
def source_create(request):
    if not _can_manage(request.user):
        return HttpResponseForbidden("관리 권한이 필요합니다.")
    if not request.company:
        return redirect("/app/")

    if request.method == "POST":
        form = SourceForm(request.POST)
        if form.is_valid():
            source = form.save(commit=False)
            source.company = request.company
            source.save()
            messages.success(request, f"유입 채널 '{source.title}' 생성됨.")
            return redirect("source_detail", pk=source.pk)
    else:
        form = SourceForm()
    return render(request, "app/source_form.html", {"form": form, "mode": "create"})


@login_required
def source_detail(request, pk):
    if not _can_manage(request.user):
        return HttpResponseForbidden("관리 권한이 필요합니다.")
    try:
        source = _owned_source_or_403(request, pk)
    except PermissionError:
        return HttpResponseForbidden("권한이 없습니다.")

    # 새 키 생성이 방금 있었다면 세션에서 plaintext 1회 노출
    newly_issued_token = request.session.pop("newly_issued_token", None)

    keys = source.api_keys.order_by("-created_at")
    label_form = ApiKeyLabelForm()

    return render(request, "app/source_detail.html", {
        "source": source,
        "keys": keys,
        "label_form": label_form,
        "newly_issued_token": newly_issued_token,
    })


@login_required
@require_POST
def api_key_create(request, pk):
    if not _can_manage(request.user):
        return HttpResponseForbidden("관리 권한이 필요합니다.")
    try:
        source = _owned_source_or_403(request, pk)
    except PermissionError:
        return HttpResponseForbidden("권한이 없습니다.")

    form = ApiKeyLabelForm(request.POST)
    label = form.cleaned_data["label"] if form.is_valid() else ""

    api_key, plaintext = ApiKey.generate(source=source, user=request.user, label=label)
    # plaintext 는 이번 요청 끝에 한 번만 보여주고 사라짐
    request.session["newly_issued_token"] = plaintext
    messages.success(request, f"새 API 키 발급됨 (이 페이지에서만 1회 노출).")
    return redirect("source_detail", pk=source.pk)


@login_required
@require_POST
def api_key_revoke(request, pk, key_id):
    if not _can_manage(request.user):
        return HttpResponseForbidden("관리 권한이 필요합니다.")
    try:
        source = _owned_source_or_403(request, pk)
    except PermissionError:
        return HttpResponseForbidden("권한이 없습니다.")

    key = get_object_or_404(ApiKey, pk=key_id, source=source)
    if key.revoked_at is None:
        key.revoked_at = timezone.now()
        key.save(update_fields=["revoked_at"])
        messages.success(request, f"키 {key.token_prefix}… 무효화됨.")
    return redirect("source_detail", pk=source.pk)

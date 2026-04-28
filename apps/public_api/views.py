"""외부 리드 수신 API. v3 §4 스펙."""
import json

from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_http_methods

from apps.leads.models import Lead, TimelineEntry, Blacklist, phone_to_hash, phone_to_masked
from apps.leads.services.assignment import auto_assign
from apps.leads.services.noti import send_noti
from .auth import authenticate_bearer


@csrf_exempt
@require_http_methods(["GET", "POST"])
def source_verify(request):
    """
    토큰 검증용 메타정보 API.
    tmrw_web 등 외부 시스템에서 토큰을 입력받았을 때, 그 토큰이 어느
    회사의 어느 채널인지 보여주기 위한 read-only 엔드포인트.

    인증: Authorization: Bearer <token>
    응답: { company_name, source_title, source_id, field_map, ok: true }
    실패: 401 unauthorized
    """
    api_key = authenticate_bearer(request)
    if not api_key:
        return JsonResponse({"ok": False, "error": "unauthorized"}, status=401)

    source = api_key.source
    if not source.is_active:
        return JsonResponse({"ok": False, "error": "source_inactive"}, status=403)

    return JsonResponse({
        "ok": True,
        "source_id": source.id,
        "source_title": source.title,
        "company_id": source.company.id,
        "company_name": source.company.name,
        "field_map": source.field_map or {},
    })


@csrf_exempt
@require_POST
def leads_create(request):
    api_key = authenticate_bearer(request)
    if not api_key:
        return JsonResponse({"error": "unauthorized"}, status=401)

    source = api_key.source
    if not source.is_active:
        return JsonResponse({"error": "source_inactive"}, status=403)

    try:
        body = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "invalid_json"}, status=400)

    name = (body.get("name") or "").strip()[:100]
    phone = (body.get("phone") or "").strip()[:20]
    fields = body.get("fields") or {}
    external_id = (body.get("external_id") or "").strip()[:200]
    external_ip = body.get("external_ip") or request.META.get("REMOTE_ADDR")

    if not name and not phone:
        return JsonResponse({"error": "name_or_phone_required"}, status=400)

    if not isinstance(fields, dict):
        return JsonResponse({"error": "fields_must_be_object"}, status=400)

    # field_map 적용: 외부 페이로드 key → 내부 CustomField code 로 리매핑
    # field_map 예: {"업종": "business_type"}
    remapped = {}
    for k, v in fields.items():
        mapped = source.field_map.get(k, k) if source.field_map else k
        remapped[mapped] = v

    p_hash = phone_to_hash(phone)

    # 블랙리스트 체크
    is_blacklisted = False
    if p_hash:
        is_blacklisted = Blacklist.objects.filter(
            company=source.company, phone_hash=p_hash,
        ).exists()

    lead_kwargs = dict(
        company=source.company,
        source=source,
        name=name,
        phone=phone,
        phone_hash=p_hash,
        fields=remapped,
        external_id=external_id,
        external_ip=external_ip if external_ip else None,
        assignment_type="unassigned",
    )
    if is_blacklisted:
        lead_kwargs["status"] = "lost"
        lead_kwargs["closed_at"] = timezone.now()
    else:
        lead_kwargs["status"] = "new"

    lead = Lead(**lead_kwargs)
    lead.save()

    TimelineEntry.objects.create(
        lead=lead,
        type="received",
        actor=None,
        payload={"source_id": source.id, "api_key_prefix": api_key.token_prefix},
    )

    if is_blacklisted:
        TimelineEntry.objects.create(
            lead=lead,
            type="blacklist_hit",
            actor=None,
            payload={"phone_masked": phone_to_masked(phone)},
        )
        return JsonResponse({
            "id": lead.id,
            "status": lead.status,
            "received_at": lead.received_at.isoformat(),
            "blacklisted": True,
            "assigned_agent_id": None,
        }, status=201)

    # 자동 배정 시도 (조건 안 맞으면 None, 리드는 그대로 남음)
    assigned_agent = auto_assign(lead)

    # 외부 NOTI 발송 (실패해도 응답엔 영향 없음)
    noti_result = send_noti(lead)

    return JsonResponse({
        "id": lead.id,
        "status": lead.status,
        "received_at": lead.received_at.isoformat(),
        "assigned_agent_id": assigned_agent.id if assigned_agent else None,
        "noti_sent": noti_result,  # True/False/None
    }, status=201)

"""외부 리드 수신 API. v3 §4 스펙."""
import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from apps.leads.models import Lead, TimelineEntry, phone_to_hash
from .auth import authenticate_bearer


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

    lead = Lead(
        company=source.company,
        source=source,
        name=name,
        phone=phone,
        phone_hash=phone_to_hash(phone),
        fields=remapped,
        external_id=external_id,
        external_ip=external_ip if external_ip else None,
        status="new",
        assignment_type="unassigned",
    )
    lead.save()

    TimelineEntry.objects.create(
        lead=lead,
        type="received",
        actor=None,
        payload={"source_id": source.id, "api_key_prefix": api_key.token_prefix},
    )

    return JsonResponse({
        "id": lead.id,
        "status": lead.status,
        "received_at": lead.received_at.isoformat(),
    }, status=201)

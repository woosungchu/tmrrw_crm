"""
GAE 내부 호출 전용 view (Cloud Tasks worker 등).

보안:
  GAE 가 외부에서 들어오는 요청의 X-AppEngine-* 헤더를 자동 strip.
  따라서 X-AppEngine-QueueName 헤더가 존재하면 GAE 내부 (Cloud Tasks) 에서 온 것.
  공격자가 임의로 위조해서 보낼 수 없음.
"""
from __future__ import annotations

import logging

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def noti_worker(request, lead_id: int):
    """
    Cloud Tasks 가 호출하는 NOTI 발송 worker.
    실패 시 5xx 반환 → Cloud Tasks 가 자동 재시도 (큐 설정에 따라).
    """
    if not request.META.get("HTTP_X_APPENGINE_QUEUENAME"):
        return JsonResponse({"error": "forbidden"}, status=403)

    from apps.leads.models import Lead
    from apps.leads.services.noti import send_noti

    try:
        lead = Lead.objects.get(pk=lead_id)
    except Lead.DoesNotExist:
        # 리드가 삭제됐다면 task 도 폐기 (재시도 무의미). 200 반환 = 큐가 task 제거.
        logger.warning("noti_worker: lead %s 없음 — task 폐기", lead_id)
        return JsonResponse({"status": "lead_gone"}, status=200)

    retry_count = request.META.get("HTTP_X_APPENGINE_TASKRETRYCOUNT", "0")
    logger.info("noti_worker 시작 lead_id=%s retry=%s", lead_id, retry_count)

    result = send_noti(lead)
    if result is False:
        # 발송 실패 → 503 → Cloud Tasks 자동 재시도
        return JsonResponse({"status": "failed", "retry": retry_count}, status=503)
    return JsonResponse({"status": "ok", "noti": result})

"""
NOTI 발송 비동기화 — Cloud Tasks 큐 이용.

흐름:
  public_api 가 lead 생성 후 enqueue_noti(lead_id) 호출 (즉시 응답)
    → Cloud Tasks 큐에 task 생성
    → 별도 worker (internal_views.noti_worker) 가 task 받아 send_noti 실행
    → 실패 시 Cloud Tasks 가 자동 재시도 (지수 백오프)

dev 환경 (NOTI_DISPATCH=sync) 에선 즉시 인라인 실행 — Cloud Tasks 의존 없음.

Cloud Tasks 큐 생성 (1회):
  gcloud tasks queues create noti-webhook \\
      --location=asia-northeast3 \\
      --max-attempts=5 \\
      --min-backoff=1s \\
      --max-backoff=10s
"""
from __future__ import annotations

import json
import logging

from django.conf import settings

logger = logging.getLogger(__name__)


def enqueue_noti(lead_id: int) -> str:
    """
    NOTI 발송 task 등록 (또는 sync 모드 시 즉시 실행).
    반환값은 public_api 응답의 noti_sent 필드로 들어감 — 디버깅 단서.
      'queued'        — Cloud Tasks 등록 성공
      'sync_done'     — 인라인 발송 성공 (dev)
      'sync_failed'   — 인라인 발송 실패 (dev)
      'no_webhook'    — 채널에 webhook URL 없음 → enqueue 스킵
      'enqueue_failed_*' — Cloud Tasks API 자체 실패 후 sync 폴백 결과
    """
    # webhook 미설정인 lead 는 큐에 넣지 않음 (낭비 + worker 가 어차피 no-op)
    from apps.leads.models import Lead
    has_webhook = Lead.objects.filter(
        pk=lead_id, source__noti_webhook_url__gt=""
    ).exists()
    if not has_webhook:
        return "no_webhook"

    dispatch = getattr(settings, "NOTI_DISPATCH", "sync")
    if dispatch == "sync":
        return _run_sync(lead_id)

    # cloud_tasks 모드
    try:
        from google.cloud import tasks_v2
        client = tasks_v2.CloudTasksClient()
        parent = client.queue_path(
            settings.GCP_PROJECT_ID,
            settings.NOTI_QUEUE_LOCATION,
            settings.NOTI_QUEUE_NAME,
        )
        task = {
            "app_engine_http_request": {
                "http_method": tasks_v2.HttpMethod.POST,
                "relative_uri": f"/internal/noti/run/{lead_id}/",
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"lead_id": lead_id}).encode("utf-8"),
            },
        }
        response = client.create_task(parent=parent, task=task)
        logger.info("NOTI enqueued lead_id=%s task=%s", lead_id, response.name.split("/")[-1])
        return "queued"
    except Exception:
        # Cloud Tasks API 가 죽으면 sync 폴백 — NOTI 가 영영 사라지면 안 됨.
        # 응답이 느려질 수 있지만 신뢰성이 우선.
        logger.exception("NOTI enqueue 실패 lead_id=%s — sync fallback", lead_id)
        result = _run_sync(lead_id)
        return f"enqueue_failed_{result}"


def _run_sync(lead_id: int) -> str:
    from apps.leads.models import Lead
    from apps.leads.services.noti import send_noti
    try:
        lead = Lead.objects.get(pk=lead_id)
        result = send_noti(lead)
        if result is None:
            return "no_webhook"
        return "sync_done" if result else "sync_failed"
    except Exception:
        logger.exception("inline NOTI 실패 lead_id=%s", lead_id)
        return "sync_failed"

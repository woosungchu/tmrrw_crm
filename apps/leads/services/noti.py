"""
외부 NOTI 발송 서비스.

리드 수신 시 Source.noti_webhook_url 로 POST. 3초 timeout.
성공: Lead.noti_status='ok' + TimelineEntry('noti_sent')
실패: Lead.noti_status='failed' + TimelineEntry('noti_failed')
      → 관리자 화면에 '빨간불' 표시로 조치 유도.

예외 절대 bubble up 하지 않음 — 공개 API 응답 절대 실패 안 남.
"""
from __future__ import annotations

import logging
from typing import Optional

import requests
from django.utils import timezone

from apps.leads.models import Lead, TimelineEntry


logger = logging.getLogger(__name__)

NOTI_TIMEOUT_SEC = 3


def _build_payload(lead: Lead) -> dict:
    return {
        "lead_id": lead.id,
        "company_id": lead.company_id,
        "source_id": lead.source_id,
        "source_title": lead.source.title if lead.source_id else "",
        "name": lead.name,
        "phone": lead.phone,
        "fields": lead.fields or {},
        "external_id": lead.external_id,
        "external_ip": str(lead.external_ip) if lead.external_ip else "",
        "received_at": lead.received_at.isoformat() if lead.received_at else None,
    }


def _mark_ok(lead: Lead, status_code: int) -> None:
    lead.noti_status = "ok"
    lead.noti_last_error = ""
    lead.save(update_fields=["noti_status", "noti_last_error", "updated_at"])
    TimelineEntry.objects.create(
        lead=lead, type="noti_sent", actor=None,
        payload={"status_code": status_code},
    )


def _mark_failed(lead: Lead, error: str) -> None:
    lead.noti_status = "failed"
    lead.noti_last_error = error[:500]
    lead.save(update_fields=["noti_status", "noti_last_error", "updated_at"])
    TimelineEntry.objects.create(
        lead=lead, type="noti_failed", actor=None,
        payload={"error": error[:500]},
    )


def send_noti(lead: Lead) -> Optional[bool]:
    """
    실행 결과: True=성공, False=실패, None=NOTI 설정 없음(n/a).
    예외 던지지 않음.
    """
    source = lead.source
    if not source or not source.noti_webhook_url:
        return None  # NOTI 미설정 — noti_status 는 기본 'n/a' 유지

    url = source.noti_webhook_url
    payload = _build_payload(lead)

    try:
        r = requests.post(url, json=payload, timeout=NOTI_TIMEOUT_SEC)
    except requests.RequestException as e:
        _mark_failed(lead, f"{type(e).__name__}: {e}")
        logger.warning("NOTI 발송 실패 lead=%s url=%s err=%s", lead.id, url, e)
        return False

    if 200 <= r.status_code < 400:
        _mark_ok(lead, r.status_code)
        return True

    body_snippet = (r.text or "")[:300]
    _mark_failed(lead, f"HTTP {r.status_code}: {body_snippet}")
    logger.warning(
        "NOTI 발송 실패 (HTTP) lead=%s url=%s code=%s",
        lead.id, url, r.status_code,
    )
    return False


def retry_noti(lead: Lead) -> Optional[bool]:
    """관리자 화면에서 '재시도' 버튼 호출."""
    return send_noti(lead)


def clear_noti_failure(lead: Lead, actor=None) -> None:
    """실패 상태를 '조치완료' 로 전환. 실제 재전송은 아님 (수동 대응 후 마킹)."""
    lead.noti_status = "failed_cleared"
    lead.save(update_fields=["noti_status", "updated_at"])
    TimelineEntry.objects.create(
        lead=lead, type="noti_failed", actor=actor,
        payload={"note": "manual_clear", "prev_error": lead.noti_last_error},
    )

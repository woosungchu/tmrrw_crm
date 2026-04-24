"""
NCP SENS SMS wrapper.
키 env 세팅 안 됐으면 실제 발송 안 하고 콘솔에 '[DRY SMS]' 로깅 — 개발 친화.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import os
import time
from dataclasses import dataclass

import requests


logger = logging.getLogger(__name__)


NCP_HOST = "https://sens.apigw.ntruss.com"


@dataclass
class SmsResult:
    ok: bool
    provider: str           # "ncp" or "dry_run"
    request_id: str = ""
    error: str = ""


def _sign(method: str, uri: str, timestamp: str, access_key: str, secret_key: str) -> str:
    msg = f"{method} {uri}\n{timestamp}\n{access_key}"
    sig = hmac.new(secret_key.encode(), msg.encode(), hashlib.sha256).digest()
    return base64.b64encode(sig).decode()


def send_sms(to_phone: str, body: str) -> SmsResult:
    """단문/장문 자동 선택. 체이닝 발송 (여러 수신번호) 는 MVP 엔 불필요."""
    access_key = os.environ.get("NCP_SENS_ACCESS_KEY", "").strip()
    secret_key = os.environ.get("NCP_SENS_SECRET_KEY", "").strip()
    service_id = os.environ.get("NCP_SENS_SERVICE_ID", "").strip()
    from_phone = os.environ.get("NCP_SENS_FROM_PHONE", "").strip()

    if not (access_key and secret_key and service_id and from_phone):
        logger.info("[DRY SMS] to=%s  body=%r  (NCP_SENS_* env 미설정)", to_phone, body)
        return SmsResult(ok=True, provider="dry_run")

    uri = f"/sms/v2/services/{service_id}/messages"
    url = f"{NCP_HOST}{uri}"
    ts = str(int(time.time() * 1000))

    headers = {
        "Content-Type": "application/json",
        "x-ncp-apigw-timestamp": ts,
        "x-ncp-iam-access-key": access_key,
        "x-ncp-apigw-signature-v2": _sign("POST", uri, ts, access_key, secret_key),
    }
    payload = {
        "type": "LMS" if len(body) >= 80 else "SMS",
        "from": from_phone,
        "content": body[:2000],
        "messages": [{"to": _strip_phone(to_phone)}],
    }
    try:
        r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=10)
        data = r.json() if r.content else {}
        if r.status_code == 202 and data.get("statusCode") == "202":
            return SmsResult(
                ok=True, provider="ncp",
                request_id=str(data.get("requestId", "")),
            )
        return SmsResult(
            ok=False, provider="ncp",
            error=f"HTTP {r.status_code}: {data.get('errorMessage') or r.text[:200]}",
        )
    except Exception as e:  # noqa: BLE001
        return SmsResult(ok=False, provider="ncp", error=str(e)[:200])


def _strip_phone(phone: str) -> str:
    return "".join(c for c in (phone or "") if c.isdigit())

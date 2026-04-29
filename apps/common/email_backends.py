"""
NCP Cloud Outbound Mailer 용 Django EmailBackend.

Django 의 표준 EmailMessage 를 그대로 받아서 NCP API 로 발송.
- 표준 SMTP 가 아니라 HMAC-SHA256 서명된 REST 호출.
- send_mail / EmailMessage.send() 호출은 코드 변경 없이 그대로 동작.

설정:
- settings.EMAIL_BACKEND = "apps.common.email_backends.NCPMailBackend"
- settings.NCP_SENS_ACCESS_KEY (Secret Manager 또는 env)
- settings.NCP_SENS_SECRET_KEY (Secret Manager)
- settings.DEFAULT_FROM_EMAIL = "tmrrwcrm <noreply@tmrrwcrm.com>"
- 발신 도메인 (tmrrwcrm.com) NCP 콘솔에서 사전 등록 + DNS 인증 필수.

실패해도 예외를 raise 하지 않음 (fail_silently 지원). 메인 흐름 유지.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import logging
import time
from email.utils import parseaddr

import requests
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend


logger = logging.getLogger(__name__)

NCP_MAIL_ENDPOINT = "https://mail.apigw.ntruss.com"
NCP_MAIL_PATH = "/api/v1/mails"


def _make_signature(method: str, path: str, timestamp: str, access_key: str, secret_key: str) -> str:
    """tmrw_web/sms.py 의 서명 함수와 동일 패턴 (HMAC-SHA256)."""
    message = f"{method} {path}\n{timestamp}\n{access_key}"
    digest = hmac.new(
        secret_key.encode("utf-8"),
        message.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()
    return base64.b64encode(digest).decode("utf-8")


class NCPMailBackend(BaseEmailBackend):
    """NCP Cloud Outbound Mailer 백엔드."""

    def __init__(self, fail_silently: bool = False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.access_key = getattr(settings, "NCP_SENS_ACCESS_KEY", "")
        self.secret_key = getattr(settings, "NCP_SENS_SECRET_KEY", "")
        self.timeout = getattr(settings, "NCP_MAIL_TIMEOUT", 10)

    def send_messages(self, email_messages):
        if not email_messages:
            return 0
        if not (self.access_key and self.secret_key):
            logger.error("NCP 메일: access/secret key 미설정 — 발송 스킵")
            if not self.fail_silently:
                raise RuntimeError("NCP_SENS_ACCESS_KEY / NCP_SENS_SECRET_KEY 미설정")
            return 0

        sent_count = 0
        for msg in email_messages:
            try:
                if self._send_one(msg):
                    sent_count += 1
            except Exception:
                logger.exception("NCP 메일 발송 실패 (subject=%r)", msg.subject)
                if not self.fail_silently:
                    raise
        return sent_count

    def _send_one(self, msg) -> bool:
        sender_name, sender_address = parseaddr(msg.from_email or "")
        if not sender_address:
            logger.error("NCP 메일: from 주소 비어있음 — skip")
            return False

        recipients = []
        for to in (msg.to or []):
            name, addr = parseaddr(to)
            if not addr:
                continue
            recipients.append({"address": addr, "name": name or addr, "type": "R"})
        for cc in (msg.cc or []):
            name, addr = parseaddr(cc)
            if not addr:
                continue
            recipients.append({"address": addr, "name": name or addr, "type": "C"})
        for bcc in (msg.bcc or []):
            name, addr = parseaddr(bcc)
            if not addr:
                continue
            recipients.append({"address": addr, "name": name or addr, "type": "B"})

        if not recipients:
            logger.warning("NCP 메일: 수신자 없음 — skip (subject=%r)", msg.subject)
            return False

        # html alternative 가 있으면 html 본문, 아니면 plain text
        body = msg.body or ""
        is_html = False
        for content, mimetype in (msg.alternatives or []) if hasattr(msg, "alternatives") else []:
            if mimetype == "text/html":
                body = content
                is_html = True
                break

        payload = {
            "senderAddress": sender_address,
            "senderName": sender_name or "tmrrwcrm",
            "title": msg.subject or "(no subject)",
            "body": body,
            "recipients": recipients,
            "individual": True,
            "advertising": False,
        }
        # NCP 는 body 의 contentType 을 명시 안 하면 plain. html 이면 명시.
        if is_html:
            payload["contentType"] = "HTML"

        timestamp = str(int(time.time() * 1000))
        signature = _make_signature("POST", NCP_MAIL_PATH, timestamp, self.access_key, self.secret_key)
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "x-ncp-apigw-timestamp": timestamp,
            "x-ncp-iam-access-key": self.access_key,
            "x-ncp-apigw-signature-v2": signature,
        }

        url = NCP_MAIL_ENDPOINT + NCP_MAIL_PATH
        r = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
        if 200 <= r.status_code < 300:
            logger.info(
                "NCP 메일 발송 OK subject=%r → %d명 (requestId=%s)",
                msg.subject, len(recipients),
                (r.json() or {}).get("requestId", "?"),
            )
            return True

        logger.error(
            "NCP 메일 발송 실패 subject=%r status=%d body=%s",
            msg.subject, r.status_code, (r.text or "")[:300],
        )
        if not self.fail_silently:
            raise RuntimeError(f"NCP mail API {r.status_code}: {r.text[:200]}")
        return False

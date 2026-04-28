import logging

from django.conf import settings
from django.http import HttpResponseForbidden


logger = logging.getLogger(__name__)


class CompanyContextMiddleware:
    """로그인된 유저의 company 를 request 에 자동 주입.
    view 에서 request.company 로 바로 접근 가능."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.company = None
        if getattr(request, "user", None) and request.user.is_authenticated:
            request.company = getattr(request.user, "company", None)
        return self.get_response(request)


class CompanyBillingGateMiddleware:
    """
    billing_status 가 BLOCKING_STATUSES 면 /app/* 접근 차단 → /app/blocked/ 안내 페이지.

    예외:
    - /app/blocked/ 자체
    - /superadmin/* (승인자가 차단 상태에 있을 일은 거의 없지만 일관성)
    - 인증 관련 (/accounts/*, /signup/, 루트, static, django-admin)
    """

    APP_PREFIX = "/app/"
    BLOCKED_URL = "/app/blocked/"
    EXEMPT_PREFIXES = (
        "/app/blocked/",
        "/superadmin/",
        "/accounts/",
        "/django-admin/",
        "/api/",
        "/static/",
        "/webhooks/",
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        # /app/ 만 검사. 그 외 경로는 통과.
        if not path.startswith(self.APP_PREFIX):
            return self.get_response(request)
        # 면제 경로
        for prefix in self.EXEMPT_PREFIXES:
            if path.startswith(prefix):
                return self.get_response(request)

        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return self.get_response(request)

        company = getattr(request, "company", None)
        if not company:
            return self.get_response(request)

        # 지연 import 로 순환 참조 방지
        from apps.companies.models import Company
        if company.billing_status in Company.BLOCKING_STATUSES:
            from django.shortcuts import redirect
            return redirect(self.BLOCKED_URL)

        return self.get_response(request)


class AdminIPWhitelistMiddleware:
    """
    /django-admin/ 경로를 DJANGO_ADMIN_ALLOWED_IPS 에 포함된 IP 에서만 허용.

    - prod.py 에서만 MIDDLEWARE 에 추가됨 (dev 엔 영향 없음).
    - DJANGO_ADMIN_ALLOWED_IPS 비어있으면 전체 허용 + 로그 경고 (점진 도입 친화).
    - X-Forwarded-For 의 첫 IP 신뢰 (GAE 프록시 뒤 구조).
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.prefix = getattr(settings, "DJANGO_ADMIN_URL_PREFIX", "/django-admin/")
        self.allowed = set(getattr(settings, "DJANGO_ADMIN_ALLOWED_IPS", []) or [])
        if not self.allowed:
            logger.warning(
                "AdminIPWhitelistMiddleware: DJANGO_ADMIN_ALLOWED_IPS 미설정 "
                "→ %s 경로 전체 허용 중. 프로덕션에선 반드시 설정 권장.",
                self.prefix,
            )

    def __call__(self, request):
        if self.allowed and request.path.startswith(self.prefix):
            client_ip = self._client_ip(request)
            if client_ip not in self.allowed:
                logger.warning("Admin access denied from IP %s", client_ip)
                return HttpResponseForbidden("Forbidden")
        return self.get_response(request)

    @staticmethod
    def _client_ip(request) -> str:
        xff = request.META.get("HTTP_X_FORWARDED_FOR", "")
        if xff:
            return xff.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "")

"""GAE 운영 환경. Cloud SQL Unix socket 경유."""
import os
from django.core.exceptions import ImproperlyConfigured
from .base import *  # noqa
from . import base as _base

DEBUG = False
ALLOWED_HOSTS = ["tmrrwcrm.com", ".tmrrwcrm.com", ".appspot.com"]

# prod 에선 SECRET_KEY 누락 = 치명적 오류. 약한 디폴트로 돌아가지 않도록 startup 차단.
if not _base.SECRET_KEY:
    raise ImproperlyConfigured(
        "DJANGO_SECRET_KEY 환경변수가 설정되지 않았습니다. "
        "Secret Manager 에서 주입하거나 app.yaml env_variables 에 지정하세요."
    )

# Cloud SQL (Unix socket). DB_HOST 에 `/cloudsql/<project>:<region>:<instance>` 형태로 주입.
DATABASES["default"]["HOST"] = os.environ["DB_HOST"]

# GAE 뒤에 프록시가 있으므로 X-Forwarded-Proto 신뢰
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Django admin IP 화이트리스트 (v3 §14.4 "IP 화이트리스트" 구현)
# DJANGO_ADMIN_ALLOWED_IPS 쉼표 구분 env. 미설정 시 경고 후 허용 (점진 도입 친화).
# 예: DJANGO_ADMIN_ALLOWED_IPS="1.2.3.4,5.6.7.8"
DJANGO_ADMIN_URL_PREFIX = "/django-admin/"
_admin_ips_raw = os.environ.get("DJANGO_ADMIN_ALLOWED_IPS", "").strip()
DJANGO_ADMIN_ALLOWED_IPS = [ip.strip() for ip in _admin_ips_raw.split(",") if ip.strip()]

MIDDLEWARE = MIDDLEWARE + [
    "apps.common.middleware.AdminIPWhitelistMiddleware",
]

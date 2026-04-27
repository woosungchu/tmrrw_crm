"""GAE 운영 환경. Cloud SQL Unix socket 경유 + Secret Manager."""
import os
from django.core.exceptions import ImproperlyConfigured
from .base import *  # noqa
from . import base as _base
from .secrets_loader import get_secret

DEBUG = False
ALLOWED_HOSTS = ["tmrrwcrm.com", ".tmrrwcrm.com", ".appspot.com"]

# Secret Manager 에서 SECRET_KEY 로드 (env 가 우선, fallback 으로 SM)
if _base.SECRET_KEY:
    SECRET_KEY = _base.SECRET_KEY
else:
    try:
        SECRET_KEY = get_secret("DJANGO_SECRET_KEY")
    except Exception as e:
        raise ImproperlyConfigured(
            f"SECRET_KEY 로드 실패: env DJANGO_SECRET_KEY 도 없고 Secret Manager 도 실패. {e}"
        )

# Cloud SQL (Unix socket). DB_HOST 에 `/cloudsql/<project>:<region>:<instance>` 형태로 주입.
DATABASES["default"]["HOST"] = os.environ["DB_HOST"]

# DB 비밀번호 — env 우선, 없으면 Secret Manager
if not DATABASES["default"].get("PASSWORD"):
    DATABASES["default"]["PASSWORD"] = get_secret("DB_PASSWORD")

# GAE 뒤에 프록시가 있으므로 X-Forwarded-Proto 신뢰
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# 정적 파일: GAE handler 가 staticfiles/ 직접 서빙. WhiteNoise 불필요.
STATIC_ROOT = BASE_DIR / "staticfiles"

# Django admin IP 화이트리스트
DJANGO_ADMIN_URL_PREFIX = "/django-admin/"
_admin_ips_raw = os.environ.get("DJANGO_ADMIN_ALLOWED_IPS", "").strip()
DJANGO_ADMIN_ALLOWED_IPS = [ip.strip() for ip in _admin_ips_raw.split(",") if ip.strip()]

MIDDLEWARE = MIDDLEWARE + [
    "apps.common.middleware.AdminIPWhitelistMiddleware",
]

# CSRF: tmrrwcrm.com / *.appspot.com
CSRF_TRUSTED_ORIGINS = [
    "https://tmrrwcrm.com",
    "https://*.tmrrwcrm.com",
    "https://*.appspot.com",
]

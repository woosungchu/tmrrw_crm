"""GAE 운영 환경. Cloud SQL Unix socket 경유."""
import os
from .base import *  # noqa

DEBUG = False
ALLOWED_HOSTS = ["tmrrwcrm.com", ".tmrrwcrm.com", ".appspot.com"]

# Cloud SQL (Unix socket). DB_HOST 에 `/cloudsql/<project>:<region>:<instance>` 형태로 주입.
DATABASES["default"]["HOST"] = os.environ["DB_HOST"]

# GAE 뒤에 프록시가 있으므로 X-Forwarded-Proto 신뢰
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

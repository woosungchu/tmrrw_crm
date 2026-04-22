"""로컬 개발 환경."""
from .base import *  # noqa

DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# 로컬 Postgres 는 .env 의 DB_* 값 사용 (base.py 기본)

# 이메일: 콘솔에 출력 (실제 전송 없음). 초대 링크 등 개발 중 확인용.
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = "tmrrwcrm <noreply@tmrrwcrm.com>"

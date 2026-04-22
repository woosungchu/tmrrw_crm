"""로컬 개발 환경."""
from .base import *  # noqa

DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# 로컬 Postgres 는 .env 의 DB_* 값 사용 (base.py 기본)

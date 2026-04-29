"""
Base settings — dev/prod 가 공통으로 상속.
환경별 override 는 dev.py / prod.py 에서.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent

load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")
# dev 에선 dev.py 가 fallback 제공, prod 에선 prod.py 가 raise.

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # 3rd party
    "django_htmx",
    # local apps
    "apps.common",
    "apps.accounts",
    "apps.companies",
    "apps.sources",
    "apps.leads",
    "apps.communications",
    "apps.dashboard",
    "apps.superadmin",
    "apps.public_api",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
    "apps.common.middleware.CompanyContextMiddleware",
    "apps.common.middleware.CompanyBillingGateMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME", "crm"),
        "USER": os.environ.get("DB_USER", "postgres"),
        "PASSWORD": os.environ.get("DB_PASSWORD", ""),
        "HOST": os.environ.get("DB_HOST", "localhost"),
        "PORT": os.environ.get("DB_PORT", "5432"),
    }
}

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "ko-kr"
TIME_ZONE = "Asia/Seoul"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# 로그인 리다이렉트 (django.contrib.auth)
LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/app/"
LOGOUT_REDIRECT_URL = "/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ─── 로깅: app 로거 INFO 까지 stderr 로 (GAE 콘솔/Cloud Logging 으로 흐름) ───
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "[%(levelname)s] %(name)s — %(message)s"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "loggers": {
        # Django 기본은 WARNING 유지 (request 로그 등 시끄러움 방지)
        "django": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        # 우리 앱은 INFO 까지 — NOTI enqueue / worker 흐름 추적 가능
        "apps": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}

# ─── NOTI 비동기 발송 (Cloud Tasks) ────────────────────────────
# "sync"     — 즉시 인라인 실행 (dev 기본). public_api 응답에 NOTI 시간 포함.
# "cloud_tasks" — Cloud Tasks 큐로 enqueue (prod). 실패 시 자동 재시도.
NOTI_DISPATCH = os.environ.get("NOTI_DISPATCH", "sync")
NOTI_QUEUE_LOCATION = os.environ.get("NOTI_QUEUE_LOCATION", "asia-northeast3")
NOTI_QUEUE_NAME = os.environ.get("NOTI_QUEUE_NAME", "noti-webhook")
GCP_PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "")

"""루트 URL 설정 (v3 §4)."""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # 공개 (랜딩 / 가입 / 로그인 안내)
    path('', include('apps.companies.public_urls')),
    # Django 기본 auth URL (login, logout, password_change, password_reset 등)
    path('accounts/', include('django.contrib.auth.urls')),
    # superuser 용 Django admin (내부만 사용 — IP 화이트리스트는 prod 에서)
    path('django-admin/', admin.site.urls),
]

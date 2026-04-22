"""루트 URL 설정 (v3 §4)."""
from django.contrib import admin
from django.urls import path, include

from apps.accounts.views import accept_invite

urlpatterns = [
    # 공개 (랜딩 / 가입 / 로그인 안내)
    path('', include('apps.companies.public_urls')),
    # 초대 수락 (비로그인 상태에서 접근)
    path('invite/<str:token>/', accept_invite, name='accept_invite'),
    # Django 기본 auth URL (login, logout, password_change, password_reset 등)
    path('accounts/', include('django.contrib.auth.urls')),
    # 로그인 후 공통 (대시보드, 내 정보 등)
    path('app/', include('apps.accounts.app_urls')),
    # superuser 용 Django admin (내부만 사용 — IP 화이트리스트는 prod 에서)
    path('django-admin/', admin.site.urls),
]

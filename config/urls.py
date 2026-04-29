"""루트 URL 설정 (v3 §4)."""
from django.contrib import admin
from django.urls import path, include

from apps.accounts.views import accept_invite
from apps.leads.internal_views import noti_worker

urlpatterns = [
    # GAE 내부 호출 전용 (Cloud Tasks worker). 외부 요청은 X-AppEngine-* 헤더 부재로 403.
    path('internal/noti/run/<int:lead_id>/', noti_worker, name='noti_worker'),
    # 공개 (랜딩 / 가입 / 로그인 안내)
    path('', include('apps.companies.public_urls')),
    # 초대 수락 (비로그인 상태에서 접근)
    path('invite/<str:token>/', accept_invite, name='accept_invite'),
    # Django 기본 auth URL (login, logout, password_change, password_reset 등)
    path('accounts/', include('django.contrib.auth.urls')),
    # 로그인 후 공통 (대시보드, 내 정보 등)
    path('app/', include('apps.accounts.app_urls')),
    path('app/sources/', include('apps.sources.urls')),
    path('app/leads/', include('apps.leads.urls')),
    path('app/', include('apps.communications.urls')),
    path('app/', include('apps.companies.app_urls')),
    # 운영자 (베타 신청 승인 등)
    path('superadmin/', include('apps.superadmin.urls')),
    # 외부 리드 수신 API
    path('api/v1/', include('apps.public_api.urls')),
    # superuser 용 Django admin (내부만 사용 — IP 화이트리스트는 prod 에서)
    path('django-admin/', admin.site.urls),
]

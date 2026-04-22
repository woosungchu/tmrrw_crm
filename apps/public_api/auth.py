"""Bearer 토큰 기반 인증 헬퍼 (DRF 없이 순수 Django)."""
from django.utils import timezone

from apps.sources.models import ApiKey


def authenticate_bearer(request):
    """
    Authorization 헤더에서 Bearer 토큰을 꺼내 검증.
    반환: ApiKey 인스턴스 or None.
    성공 시 last_used_at 갱신.
    """
    auth = request.META.get("HTTP_AUTHORIZATION", "")
    if not auth.lower().startswith("bearer "):
        return None
    raw_token = auth[7:].strip()
    api_key = ApiKey.verify(raw_token)
    if not api_key:
        return None
    # 사용 기록 갱신 (race OK — 마지막 쓰기가 이김)
    ApiKey.objects.filter(pk=api_key.pk).update(last_used_at=timezone.now())
    return api_key

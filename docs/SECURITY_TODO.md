# Security TODO

보안 청소 진행 상황. 2026-04-24 기준.

## ✅ 완료 (2026-04-24)

### SECRET_KEY 강화
- **이전:** `os.environ.get("DJANGO_SECRET_KEY", "insecure-change-me")` — 약한 fallback
- **이후:**
  - `base.py`: fallback 제거
  - `dev.py`: 로컬용 고정 키 자동 세팅 (git 미반영, dev 전용)
  - `prod.py`: env 누락 시 `ImproperlyConfigured` raise → startup 실패
- **배포 체크:** GAE env_variables 또는 Secret Manager 에 `DJANGO_SECRET_KEY` 주입 필수

### Django Admin IP 화이트리스트
- `apps/common/middleware.py::AdminIPWhitelistMiddleware` 추가
- `prod.py` 에만 MIDDLEWARE 에 추가 (dev 영향 없음)
- `DJANGO_ADMIN_ALLOWED_IPS` env (쉼표 구분) 로 허용 IP 지정
- 미설정 시: 전체 허용 + startup 로그 경고 (점진 도입 친화)
- **배포 체크:** GAE env 에 본인 홈/오피스 IP 추가 후 테스트
- X-Forwarded-For 첫 번째 IP 신뢰 (GAE 프록시 구조)

---

## 🟡 보류 — 해당 주차에서 처리

### W8 (TimelineEntry + Communications 작업 시)
**Lead.fields JSONField XSS 방어**
- 템플릿에서 동적 값 렌더 시 `|safe` 금지
- 필요 시 `CustomField.type` 기준 화이트리스트 sanitize
- 위험: 공개 API 로 받은 `fields` payload 에 `<script>` 삽입 가능성

### W9 (NOTI + 대시보드 작업 시)
**Public API Rate Limiting**
- 현재 `POST /api/v1/leads` 는 Bearer 토큰만 검증. 분당 제한 없음
- 토큰 유출 시 DB 포화 공격 가능
- 대응: `django-ratelimit` 도입 or `ApiKey` 단위 분당 카운터
- 기본 제안: `60 요청/분 per ApiKey`, 초과 시 429

### W11 (랜딩 + 모바일 작업 시)
**공개 가입 Form 봇 보호**
- 가입 페이지에 CAPTCHA 없음 → 자동 가입 가능
- 대응: Cloudflare Turnstile (무료, reCAPTCHA 대비 프라이버시 친화) 도입
- env: `TURNSTILE_SITE_KEY` / `TURNSTILE_SECRET_KEY`

---

## 참고: 오해 해소

프로젝트 글로벌 메모리의 "2026-04-20 긴급 보안 이슈 3대 축" 은 **Flask 기반 tmrrwmkt/랜딩 프로젝트 얘기**이지 현재 Django tmrrw_crm 프로젝트와 무관. 혼동 주의.

해당 메모리의 3대 이슈 (하드코딩 시크릿 / 권한 부실 / CSRF 부재) 는 tmrrw_crm 에선 다음과 같이 처리됨:
- **하드코딩 시크릿**: 기본적으로 env 기반 + 위 SECRET_KEY 강화로 해결
- **권한 부실**: `@login_required` + `CompanyScopedManager` + role 체크 (`_can_invite` 등) 으로 구조적 해결
- **CSRF 부재**: Django 기본 `CsrfViewMiddleware` 로 모든 POST 요청에 자동 적용

# 🚀 tmrrw_crm — 실행 계획 v3 (Django + Postgres 전면 재설계)

> 본 문서가 **ground truth**. 코딩·설계 결정 시 항상 여기 먼저 참조.
>
> 작성일: 2026-04-22 · 결정자: Claude (lead) · 상태: 전체 확정
>
> v1·v2 는 `docs/` 에 보존. v3 은 v2 의 **스택·데이터 모델·일부 구조** 를 근본 교체한 버전. 비즈니스 전략·가격·UI 개념·법적 차별화 정책은 v2 결정을 승계.

---

## 0. 대원칙 (v2 에서 재확인)

우선순위:

| 1 | **유지보수 편의성** | 1인이 10년 유지 가능한 구조. 프레임워크가 많이 결정해주는 쪽. |
| 2 | **수익화** | 결제·요금제·사용량 측정 MVP 포함. |
| 3 | **법적 모방 리스크 제거** | 1000.sseye HTML/CSS/URL/API 패턴 직접 복제 금지. |

**v2 대비 해석 변화:** "유지보수 편의" = *네가 혼자 영원히 유지보수* 로 재해석. 출시 속도 제약 없고 인력 추가 없음. 이 재해석이 스택 전면 재선택의 근거.

---

## 1. 기술 스택 (확정)

### 1.1 Stack 전체

| 레이어 | 확정 | 비고 |
|---|---|---|
| Language | **Python 3.12** | tmrw_web 연속성 + Django 공식 지원 |
| Framework | **Django 5.x** | "배터리 포함" — admin, auth, forms, ORM, migrations, CSRF, middleware |
| DB | **PostgreSQL 16 (Cloud SQL)** | 관계형 + 복잡 쿼리 + migration 자동 |
| Template | **Django Template Language** | Jinja2 대신 DTL 사용 (Django 기본값, 학습비용 ≈ 0) |
| Frontend 상호작용 | **HTMX + Alpine.js** | `django-htmx` 공식 통합 |
| CSS | **Tailwind v4** (pre-built) | tmrw_web 과 동일 |
| 폰트 | **Pretendard** | 한국어 우선 |
| 차트 | **Chart.js v4** | sseye 의 Google Charts 와 다름 |
| Auth | **Django 기본 + django-allauth** | 이메일 인증/비밀번호 재설정/소셜로그인 (필요 시) |
| 멀티테넌트 | **Company FK 기반 column-level 격리** | `django-tenants`(스키마 격리) 는 Phase 2 에서 재검토 |
| 결제 | **포트원 (PortOne)** 기본 PG 토스페이먼츠 | v2 결정 승계 |
| SMS/알림톡 | **NCP SENS** | tmrw_web 코드 복사 (sms.py) |
| 파일 저장 | **GCS** | 회사 로고, 녹취 (Phase 2), 엑셀 업로드 |
| 비밀/키 | **GCP Secret Manager** | NCP 키, 포트원 키, Django SECRET_KEY |
| 인프라 | **GAE Standard Python 3.12** | Cloud SQL Unix socket 연결 |
| Cron | **Cloud Scheduler → GAE endpoint** | 월별 결제, 통계 집계 |
| 에러 모니터링 | **GCP Cloud Logging** (Phase 2에 Sentry) | 기본 무료 |
| AI | **Claude API** (Phase 3) | 한국어 품질 |
| 개발 환경 | **Django runserver + 로컬 Postgres (Docker)** | GCP 비용 0 |

### 1.2 배제한 것 + 사유

| 배제 | 사유 |
|---|---|
| Flask | Django 대비 "1인 혼자 결정 내려야 할 것" 너무 많음 |
| FastAPI | 타입·async 좋지만 Django admin/ORM/migrations/forms 없음 |
| Firestore | 스키마 없음이 **1인에겐 저주**. 복잡 쿼리 불가. migration 수동. |
| Next.js / React | Python 밖으로 나가는 순간 유지 스택 2배 |
| 별도 staging 환경 | 로컬 + internal-test company + `--no-promote` 카나리로 충분 |
| 다크모드 (MVP) | Tailwind 이중 클래스 부담, Phase 2 |
| Kanban drag-drop | 유지 부담. 상태 클릭으로 대체 |
| WebSocket / SSE | HTMX polling (5-10s) 으로 충분 |
| django-tenants (schema 격리) | MVP 규모에 오버엔지니어링 — `company_id` FK 만으로 격리 |

### 1.3 배포 환경 (prod-only)

- GCP 프로젝트 1개: **`tmrrw-crm-prod`**
- GAE Standard Python 3.12
- Cloud SQL Postgres 16 (인스턴스: `tmrrw-crm-db`, Seoul region)
- 로컬 개발: Docker `postgres:16` 컨테이너 + Django runserver
- staging 없음. 대체 안전장치 3개:
  1. 로컬 Docker Postgres 에서 마이그레이션·end-to-end 검증
  2. Prod 에 `internal_test_company` 1개 심어서 e2e 테스트 (통계·청구 제외)
  3. `gcloud app deploy --no-promote --version=canary-YYMMDD-HHMM` 로 카나리 배포 → 확인 후 traffic 이동

---

## 2. 레포 구조

```
tmrrw_crm/
├── manage.py
├── app.yaml                        GAE Standard 설정
├── requirements.txt
├── package.json                    Tailwind 빌드용 npm (tmrw_web 과 동일 패턴)
├── tailwind.config.js
├── tailwind/input.css
├── .gitignore
├── README.md
├── .claude/memory/                 세션간 맥락 유지
│   ├── MEMORY.md
│   ├── project_overview.md
│   ├── feedback_tailwind_rebuild.md
│   └── (추가 예정)
├── docs/
│   ├── CRM_MVP_기획보고서_v1.md    보존
│   ├── CRM_실행계획_v2.md          보존 (Flask 버전)
│   ├── CRM_실행계획_v3.md          ← 본 문서 (ground truth)
│   ├── 데이터_모델.md              (W1 작성)
│   ├── API_스펙.md                 (W4 작성)
│   └── 배포_플레이북.md            (W10 작성)
├── config/                         Django 프로젝트 루트
│   ├── settings/
│   │   ├── base.py                 공통
│   │   ├── dev.py                  로컬 개발
│   │   └── prod.py                 GAE 배포용
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/                           Django 앱들 (도메인별 분리)
│   ├── common/                     공통 유틸·miдlewares·base models
│   │   ├── models.py
│   │   ├── middleware.py           request.company 자동 설정
│   │   ├── decorators.py           @require_role('admin')
│   │   └── managers.py             CompanyScopedManager
│   ├── companies/                  회사·가입·결제
│   │   ├── models.py               Company, Billing, AssignmentConfig
│   │   ├── views.py
│   │   ├── admin.py
│   │   ├── portone.py              포트원 SDK wrapper
│   │   └── templates/companies/
│   ├── accounts/                   사용자·인증·권한
│   │   ├── models.py               User (AbstractBaseUser), InviteToken
│   │   ├── views.py
│   │   ├── forms.py
│   │   └── templates/accounts/
│   ├── sources/                    유입 채널 + API 토큰
│   │   ├── models.py               Source, ApiKey
│   │   ├── views.py
│   │   └── admin.py
│   ├── fields/                     커스텀 필드 정의
│   │   └── models.py               CustomField
│   ├── leads/                      리드 CRUD + 상태 + 타임라인 + 블랙리스트
│   │   ├── models.py               Lead, TimelineEntry, Blacklist
│   │   ├── views.py
│   │   ├── forms.py
│   │   ├── services/
│   │   │   ├── assignment.py       자동/수동 배정 엔진
│   │   │   ├── duplicate.py        중복 감지
│   │   │   └── noti.py             외부 NOTI + 실패 감지
│   │   └── templates/leads/
│   ├── communications/             SMS/알림톡 템플릿 + 발송 + 콜백
│   │   ├── models.py               Template, Callback
│   │   ├── sms.py                  NCP SENS wrapper (tmrw_web 복사)
│   │   └── views.py
│   ├── dashboard/                  대시보드 + 통계
│   │   ├── models.py               StatsDaily
│   │   ├── views.py
│   │   └── aggregators.py          일별 집계 태스크
│   ├── public_api/                 외부 리드 수신 API
│   │   ├── views.py                POST /api/v1/leads
│   │   ├── auth.py                 Bearer 토큰 검증
│   │   └── serializers.py
│   └── webhooks/                   포트원 등 외부 webhook
│       └── views.py
├── static/
│   ├── css/tailwind.css            빌드 산출물
│   ├── js/htmx.min.js
│   ├── js/alpine.min.js
│   └── img/
├── templates/                      공용 템플릿 (base, public)
│   ├── base.html
│   ├── public/landing.html
│   ├── public/signup.html
│   └── public/login.html
└── node_modules/ (gitignored)
```

### 레포 원칙

- **앱 = 도메인** (기술 레이어 아닌 비즈니스 도메인별 분리)
- **service 레이어**: 복잡한 로직은 `apps/{app}/services/*.py` 에 분리 (테스트 용이)
- **템플릿은 앱 내부** `templates/{app_name}/` 에 두고 (Django 관례)
- **settings 분할**: `base/dev/prod` 3파일
- tmrw_web 의 `sms.py` 는 `apps/communications/sms.py` 로 복사 (프레임워크 무관)

---

## 3. 용어 매핑 (v2 승계, 그대로)

### 역할 (사용자에 보여지는 UI vs 코드)

| 1000.sseye | UI 표기 | 코드명 | URL prefix |
|---|---|---|---|
| 관리자 (master) | 관리자 | `admin` | `/app/admin/` |
| 접수자 (accept) | 접수 | `intake` | `/app/intake/` |
| 상담자 (consult) | 상담사 | `agent` | `/app/agent/` |

(회사 생성한 최초 계정은 `owner` role — 결제 권한 독점. admin 은 복수 허용.)

### 리드 상태 6단계 (v2 승계)

| UI | 코드 | 색상 |
|---|---|---|
| 접수 | `new` | slate-500 |
| 상담중 | `contacted` | indigo-500 |
| 선별중 | `qualified` | amber-500 |
| 진행중 | `negotiating` | violet-500 |
| 결과-성사 | `won` | emerald-600 |
| 결과-실패 | `lost` | rose-500 |

### 엔티티 매핑

| 1000.sseye | UI | Django 모델 |
|---|---|---|
| 광고분류/랜딩 | 유입 채널 | `Source` |
| 항목설정 / DBfild | 커스텀 필드 | `CustomField` |
| 고객/리드 | 리드 | `Lead` |
| 관리메모 | 활동 로그 | `TimelineEntry` (type=`memo`) |
| 분배 | 배정 | `Lead.agent` FK + `AssignmentConfig` |

---

## 4. URL/화면 지도 (v2 승계, 변경 없음)

v2 §5 동일. `/app/admin/`, `/app/intake/`, `/app/agent/` prefix 유지. `.html` 확장자 없음.

Django URL conf 구조:

```python
# config/urls.py
urlpatterns = [
    path('', include('apps.companies.public_urls')),          # 랜딩, 가입, 로그인
    path('app/', include('apps.accounts.app_urls')),           # 로그인 후 공통 (/app, /app/me)
    path('app/admin/', include('apps.admin_area.urls')),
    path('app/intake/', include('apps.intake_area.urls')),
    path('app/agent/', include('apps.agent_area.urls')),
    path('api/v1/', include('apps.public_api.urls')),
    path('webhooks/', include('apps.webhooks.urls')),
    path('django-admin/', admin.site.urls),                   # Django admin (우리만 씀)
]
```

`django-admin` URL 은 우리(superuser)만 접근. 고객 대응·디버깅용. IP 화이트리스트로 제한.

### 리드 수신 API 스펙 (v2 승계)

```http
POST /api/v1/leads
Authorization: Bearer <source_token>
Content-Type: application/json

{
  "name": "홍길동",
  "phone": "01012345678",
  "fields": {"business_type": "도소매업", ...},
  "external_id": "abc",
  "external_ip": "1.2.3.4"
}
```

**변경:** Django REST framework 안 씀 — `views.py` 에 순수 Django `JsonResponse` 로 구현. MVP 에서 DRF 오버헤드 불필요. API 엔드포인트 3-5개라 간단.

---

## 5. 데이터 모델 (Django Models, Firestore 대체)

### 5.1 공통 베이스

```python
# apps/common/models.py
class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class CompanyScopedManager(models.Manager):
    """회사 격리 강제 헬퍼. view에서 Lead.objects.for_company(request.company) 로 사용."""
    def for_company(self, company):
        return self.get_queryset().filter(company=company)


class CompanyScopedModel(TimestampedModel):
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE, db_index=True)
    objects = CompanyScopedManager()

    class Meta:
        abstract = True
```

### 5.2 companies 앱

```python
# apps/companies/models.py
class Company(TimestampedModel):
    PLAN_CHOICES = [('trial', 'Trial'), ('starter', 'Starter'), ('pro', 'Pro'), ('enterprise', 'Enterprise')]
    BILLING_STATUS = [('active', '활성'), ('past_due', '연체'), ('canceled', '해지'), ('trial', '체험중'), ('read_only', '읽기전용')]

    name = models.CharField(max_length=200)
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default='trial')
    billing_status = models.CharField(max_length=20, choices=BILLING_STATUS, default='trial')
    trial_end = models.DateTimeField(null=True)
    timezone = models.CharField(max_length=50, default='Asia/Seoul')
    industry_preset = models.CharField(max_length=20, blank=True)  # 'loan', 'beauty', 'education', ...
    logo_url = models.URLField(blank=True)
    owner = models.ForeignKey('accounts.User', on_delete=models.PROTECT, related_name='owned_companies', null=True)
    is_internal_test = models.BooleanField(default=False)  # 통계·청구에서 제외

    def is_over_limit(self, metric):
        """월 리드·SMS 한도 초과 여부"""
        # Billing.usage_current_cycle 조회 + plan 기반 한도 비교
        ...


class AssignmentConfig(TimestampedModel):
    company = models.OneToOneField(Company, on_delete=models.CASCADE, related_name='assignment_config')
    auto_on = models.BooleanField(default=False)
    weekdays = models.JSONField(default=list)  # [0..6]
    time_start = models.TimeField(default='09:00')
    time_end = models.TimeField(default='18:00')
    tie_breaker = models.CharField(max_length=20, choices=[('round_robin', 'RR'), ('least_loaded', 'LL')], default='round_robin')


class Billing(TimestampedModel):
    company = models.OneToOneField(Company, on_delete=models.CASCADE, related_name='billing')
    plan = models.CharField(max_length=20)
    portone_billing_key = models.CharField(max_length=200, blank=True)
    pg_provider = models.CharField(max_length=30, default='tosspayments')
    next_billing_at = models.DateTimeField(null=True)
    usage_leads_month = models.IntegerField(default=0)
    usage_sms_month = models.IntegerField(default=0)
    usage_storage_mb = models.IntegerField(default=0)
    cycle_start = models.DateField()  # 사용량 리셋 기준


class Invoice(TimestampedModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='invoices')
    amount = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=[('pending', ), ('paid', ), ('failed', ), ('refunded', )])
    portone_payment_id = models.CharField(max_length=100, blank=True)
    paid_at = models.DateTimeField(null=True)
    receipt_url = models.URLField(blank=True)
```

### 5.3 accounts 앱

```python
# apps/accounts/models.py
class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [('owner', '오너'), ('admin', '관리자'), ('intake', '접수'), ('agent', '상담사')]

    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE, related_name='users', null=True)  # null 은 가입 중
    login_id = models.CharField(max_length=50, unique=True)
    email = models.EmailField()
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    manager = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, related_name='reports')
    daily_quota = models.PositiveIntegerField(null=True, help_text='agent 자동 배정 쿼터. null=무제한')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'login_id'

    class Meta:
        indexes = [models.Index(fields=['company', 'role', 'is_active'])]


class InviteToken(TimestampedModel):
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE)
    email = models.EmailField()
    role = models.CharField(max_length=20)
    manager_id = models.IntegerField(null=True)
    token = models.CharField(max_length=64, unique=True)
    invited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    expires_at = models.DateTimeField()
    consumed_at = models.DateTimeField(null=True)
```

**hierarchy 로직.** tmrw_web 의 `ancestors[]` + `depth` 수동 관리 **불필요**. Django `manager = ForeignKey('self')` 재귀 + `django-mptt` 또는 CTE 쿼리로 처리. MVP 는 단순 `manager` 만 쓰고 N-hop 조회는 `get_subtree()` 재귀 함수로 구현 (얕은 트리 전제).

### 5.4 sources 앱

```python
# apps/sources/models.py
class Source(CompanyScopedModel):
    title = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    tmrw_form_id = models.CharField(max_length=100, blank=True)  # tmrw_web 연동 매핑
    field_map = models.JSONField(default=dict)  # 외부 페이로드 → CustomField 매핑

    class Meta:
        indexes = [models.Index(fields=['company', 'is_active'])]


class ApiKey(TimestampedModel):
    source = models.ForeignKey(Source, on_delete=models.CASCADE, related_name='api_keys')
    token_hash = models.CharField(max_length=128)  # bcrypt
    token_prefix = models.CharField(max_length=12)  # UI 표시용 앞 6자리
    label = models.CharField(max_length=100)
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    revoked_at = models.DateTimeField(null=True)
    last_used_at = models.DateTimeField(null=True)
```

### 5.5 fields 앱

```python
# apps/fields/models.py
class CustomField(CompanyScopedModel):
    TYPE_CHOICES = [('text', '텍스트'), ('select', '선택'), ('number', '숫자')]

    code = models.SlugField(max_length=50)  # 'business_type'
    label = models.CharField(max_length=100)  # '업종'
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    options = models.JSONField(default=list, help_text='select 일 때만')
    sort_order = models.PositiveIntegerField(default=0)
    is_required = models.BooleanField(default=False)
    is_built_in = models.BooleanField(default=False)  # name/phone 등 시스템 필드

    class Meta:
        unique_together = [['company', 'code']]
        ordering = ['sort_order']
```

### 5.6 leads 앱 — 핵심

```python
# apps/leads/models.py
class Lead(CompanyScopedModel):
    STATUS_CHOICES = [
        ('new', '접수'), ('contacted', '상담중'), ('qualified', '선별중'),
        ('negotiating', '진행중'), ('won', '결과-성사'), ('lost', '결과-실패')
    ]
    ASSIGNMENT_CHOICES = [('auto', '자동'), ('manual', '수동'), ('unassigned', '미배정')]
    NOTI_STATUS_CHOICES = [('ok', '정상'), ('failed', '실패'), ('failed_cleared', '조치완료'), ('n/a', '해당없음')]

    source = models.ForeignKey('sources.Source', on_delete=models.PROTECT, related_name='leads')
    intake = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, related_name='intake_leads')
    agent = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, related_name='agent_leads')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', db_index=True)
    assignment_type = models.CharField(max_length=20, choices=ASSIGNMENT_CHOICES, default='unassigned')

    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    phone_hash = models.CharField(max_length=64, db_index=True)  # sha256, 중복 탐지용

    fields = models.JSONField(default=dict)  # {'business_type': '도소매업', ...}

    duplicate_of = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, related_name='duplicates')

    noti_status = models.CharField(max_length=20, choices=NOTI_STATUS_CHOICES, default='n/a')
    noti_last_error = models.TextField(blank=True)

    external_id = models.CharField(max_length=200, blank=True)
    external_ip = models.GenericIPAddressField(null=True, blank=True)

    received_at = models.DateTimeField(auto_now_add=True)
    contacted_at = models.DateTimeField(null=True)
    qualified_at = models.DateTimeField(null=True)
    closed_at = models.DateTimeField(null=True)

    is_deleted = models.BooleanField(default=False, db_index=True)  # 휴지통

    class Meta:
        indexes = [
            models.Index(fields=['company', 'status', '-received_at']),
            models.Index(fields=['company', 'agent', 'status']),
            models.Index(fields=['company', 'source', '-received_at']),
            models.Index(fields=['company', 'phone_hash']),
            models.Index(fields=['company', 'noti_status']),
        ]


class TimelineEntry(TimestampedModel):
    TYPE_CHOICES = [
        ('status_change', '상태 변경'),
        ('memo', '메모'),
        ('sms_sent', 'SMS 발송'),
        ('alimtalk_sent', '알림톡 발송'),
        ('callback_scheduled', '콜백 예약'),
        ('noti_sent', 'NOTI 전송'),
        ('noti_failed', 'NOTI 실패'),
        ('assigned', '배정'),
        ('reassigned', '재배정'),
        ('field_changed', '필드 변경'),
    ]

    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='timeline')
    type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    actor = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    at = models.DateTimeField(auto_now_add=True)
    payload = models.JSONField(default=dict)  # type 별 자유 스키마

    class Meta:
        ordering = ['-at']
        indexes = [models.Index(fields=['lead', '-at'])]


class Blacklist(CompanyScopedModel):
    phone_hash = models.CharField(max_length=64)
    phone_masked = models.CharField(max_length=20)  # '010-****-1234'
    reason = models.TextField(blank=True)
    added_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)

    class Meta:
        unique_together = [['company', 'phone_hash']]
```

### 5.7 communications 앱

```python
# apps/communications/models.py
class Template(CompanyScopedModel):
    CHANNEL_CHOICES = [('sms', 'SMS'), ('alimtalk', '알림톡')]

    title = models.CharField(max_length=100)
    body = models.TextField()
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES, default='sms')
    variables = models.JSONField(default=list)  # ['name', 'phone', ...] 치환 키
    is_active = models.BooleanField(default=True)


class Callback(CompanyScopedModel):
    STATUS_CHOICES = [('pending', '대기'), ('done', '완료'), ('missed', '미처리')]

    lead = models.ForeignKey('leads.Lead', on_delete=models.CASCADE)
    agent = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    scheduled_at = models.DateTimeField(db_index=True)
    note = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reminder_sent = models.BooleanField(default=False)

    class Meta:
        indexes = [models.Index(fields=['agent', 'status', 'scheduled_at'])]
```

### 5.8 dashboard 앱

```python
# apps/dashboard/models.py
class StatsDaily(CompanyScopedModel):
    date = models.DateField(db_index=True)
    by_status = models.JSONField(default=dict)  # {'new': 5, 'contacted': 3, ...}
    by_source = models.JSONField(default=dict)
    by_agent = models.JSONField(default=dict)
    total = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = [['company', 'date']]
```

집계 방식: 매 리드 상태 변경 시 **signal** 로 실시간 증감 — Django post_save signal 활용. Cron 으로 새벽마다 무결성 재계산 (drift 방지).

### 5.9 인덱스 요약

위 각 모델의 `Meta.indexes` 선언에 이미 포함. Django migration 이 자동 생성·관리. 수동 `index.yaml` 관리 불필요 (Firestore 대비 엄청난 이점).

### 5.10 hierarchy — 조직 계층

v2 에서 `ancestors[]` + `depth` 필드로 관리했으나, Django 에선 `manager` FK 만 있으면 충분. 재귀 쿼리로 subtree 조회:

```python
def get_subtree(user):
    descendants = []
    queue = list(User.objects.filter(manager=user))
    while queue:
        u = queue.pop(0)
        descendants.append(u)
        queue.extend(User.objects.filter(manager=u))
    return descendants
```

조직 규모 수십~수백명 가정. Postgres recursive CTE 로 더 빠르게 가능 (Django 5 의 `models.CharField(...)` + raw query).

**`user_migration.py` 로직 대폭 축소:** Firestore 청크 버퍼 필요 없음 — Django `@transaction.atomic` 한 블록으로 end-to-end 트랜잭션. 하위 유저 재연결 + 리드 이관 + 통계 이관 전부 atomic.

```python
@transaction.atomic
def delete_user_and_migrate(target, trigger):
    parent = target.manager
    if not parent: raise ValueError('루트 삭제 불가')
    if trigger not in target.get_ancestors(): raise ValueError('권한 없음')

    # 하위 유저 재연결
    User.objects.filter(manager=target).update(manager=parent)

    # 리드 이관
    target.agent_leads.update(agent=parent)
    target.intake_leads.update(intake=parent)

    # 사용자 삭제
    target.delete()
```

20줄. Firestore 버전 200+줄 대비.

---

## 6. 멀티테넌트 격리 전략

**선택: column-level 격리 (shared schema, 모든 테이블에 `company_id`).**

근거: 
- `django-tenants` (schema 격리) 는 고객사 수가 수백~수천 넘어가면 의미. MVP 30개사 규모에 오버엔지니어링.
- column-level 은 Django ORM/admin/쿼리가 모두 같은 방식으로 동작.

강제 수단:

1. **Middleware**: 로그인 세션에서 `request.company` 자동 주입
   ```python
   class CompanyContextMiddleware:
       def __call__(self, request):
           if request.user.is_authenticated:
               request.company = request.user.company
           return self.get_response(request)
   ```

2. **CompanyScopedManager**: 모든 쿼리는 `Lead.objects.for_company(request.company)` 패턴 권장
   - 어기면 코드 리뷰에서 (self review 지만) 플래그
   
3. **View-level decorator**:
   ```python
   @require_company  # request.company 없으면 403
   @require_role('admin')
   def lead_list(request):
       leads = Lead.objects.for_company(request.company).filter(...)
   ```

4. **ForeignKey 간접 보호**: `Lead.source` → `Source.company` 같아야 함. 저장 시 `clean()` 에서 검증.

5. **Django admin 커스터마이징**: superuser(우리) 만 전체 조회. 스태프 권한도 회사별 limit.

**추가 안전장치:** 중요 경로에 pytest 로 `cross_company_access_denied` 류 통합 테스트 작성 (W5).

---

## 7. MVP v1.0 기능 (v2 §7.1 승계, 변경 없음)

28개 기능 동일. Django 로 구현 방식만 달라짐.

**Django로 훨씬 쉬워지는 것들:**

| 기능 | Flask+Firestore 구현 | Django+Postgres 구현 |
|---|---|---|
| 회사·유저 CRUD | Firestore 경로 직접 제작 | **Django admin 자동 제공** |
| 인증 (로그인/비번리셋/이메일 인증) | 직접 구현 or flask-login | **django-allauth** 1회 설정 |
| 이메일 발송 | 직접 SMTP | `django.core.mail.send_mail` |
| 폼 validation | 수동 | **Django Forms** 자동 |
| CSRF 방어 | 수동 | **Django middleware** 자동 |
| 페이지네이션 | 수동 | **Paginator** 내장 |
| 복잡 쿼리 (통계, 집계) | 카운터 문서 수동 | **`annotate/aggregate`** 한 줄 |
| 데이터 마이그레이션 | 수동 코드 | **makemigrations/migrate** 자동 |
| 관리자 디버깅 | 별도 도구 필요 | **Django admin GUI** 즉시 |

**그대로 어려운 것:**
- 자동 배정 엔진 (경합, 쿼터, 시간대)
- NOTI 실패 감지·빨간불
- 포트원 결제 연동
- HTMX 기반 실시간 UI

---

## 8. 디자인 시스템 (v2 §8 승계)

- 색상: slate-900 sidebar + indigo-600 accent + emerald-500 success + rose-500 danger
- 폰트: Pretendard
- 아이콘: Lucide
- 차트: Chart.js v4 (파이 회피, KPI 카드 + 라인/도넛)
- Jinja2 macro 대신 **Django Template Language `{% include %}` + `inclusion_tag`**
- 재사용 컴포넌트는 `templates/components/*.html` + `templatetags/components.py`

---

## 9. 권한 매트릭스 (v2 §9 승계)

| 기능 | Owner | Admin | Intake | Agent |
|---|---|---|---|---|
| 회사 설정·결제 | ✅ | ❌ | ❌ | ❌ |
| 사용자 초대/역할/삭제 | ✅ | ✅ | ❌ | ❌ |
| 유입 채널·커스텀 필드·배정 규칙 | ✅ | ✅ | ❌ | ❌ |
| 전체 리드 조회 | ✅ | ✅ | 본인 범위 | 본인 담당 |
| 리드 수동 등록 | ✅ | ✅ | ✅ | ❌ |
| 리드 배정/재배정 | ✅ | ✅ | ✅ (→agent) | ❌ |
| 리드 상태 변경 | ✅ | ✅ | ✅ | ✅ (본인) |
| 메모/SMS | ✅ | ✅ | ✅ | ✅ (본인) |
| 블랙리스트·템플릿 관리 | ✅ | ✅ | ❌ | ❌ |
| 콜백 예약 | ✅ | ✅ | ❌ | ✅ |

구현: `@require_role('admin')` 데코레이터 + Django Permissions framework + 커스텀 `has_perm()`.

---

## 10. 타임라인 (재조정)

v2 의 10주 계획은 Flask 기준. Django 학습 2-3주 + 프레임워크가 주는 시간 절약을 상쇄하면 **대략 12주**.

출시 속도 제약 없다 했으니 이 정도 여유는 이득. 하지만 **deadline 설정 자체는 유지** (동기 부여).

| 주차 | 기간 | 작업 |
|---|---|---|
| W0 | 04-22 ~ 04-28 | **Django 학습 + 튜토리얼 완주** (Mozilla Django 또는 Django Girls) |
| W1 | 04-29 ~ 05-05 | GCP 프로젝트·Cloud SQL 생성, Django 프로젝트 scaffold, GAE 배포 실험 (hello world), `config/settings/{base,dev,prod}.py` 분리, Cloud SQL Unix socket 연결 검증 |
| W2 | 05-06 ~ 05-12 | `companies`·`accounts` 앱: Company, User, 가입, 이메일 인증, 로그인, owner 자동 부여 |
| W3 | 05-13 ~ 05-19 | 초대·역할 관리·조직 계층·사용자 삭제(transaction.atomic 버전) |
| W4 | 05-20 ~ 05-26 | `sources` + ApiKey, `public_api` POST /api/v1/leads, tmrw_web webhook 수신 |
| W5 | 05-27 ~ 06-02 | `fields` + `leads` CRUD, 목록 검색/필터/엑셀, 중복 감지 |
| W6 | 06-03 ~ 06-09 | 리드 상세·상태 머신·그리드 뷰·수동 등록 |
| W7 | 06-10 ~ 06-16 | 자동 배정 엔진 (§11 참조) + 수동 배정 + 재배정 |
| W8 | 06-17 ~ 06-23 | `TimelineEntry`, `communications` (템플릿·SMS 발송), 콜백 예약·브라우저 알림 |
| W9 | 06-24 ~ 06-30 | 블랙리스트, NOTI 실패 감지·빨간불, 대시보드·통계·집계 signal |
| W10 | 07-01 ~ 07-07 | 포트원 정기결제·요금제·체험판·사용량 측정 |
| W11 | 07-08 ~ 07-14 | 마케팅 랜딩, 모바일 반응형, 키보드 단축키, 접근성 |
| W12 | 07-15 ~ 07-21 | QA·버그 수정·베타 준비·문서 |

**베타 시작:** 07-22.
**정식 런칭:** 08-19 (결제 유도 개시).

---

## 11. 자동 배정 엔진 설계 (핵심 복잡 로직, 미리 스케치)

### 조건
- `AssignmentConfig.auto_on = True`
- 현재 요일이 `weekdays` 에 포함
- 현재 시각이 `time_start ~ time_end` 범위
- 리드가 `source` 에서 들어왔고 회사 격리 통과

### 알고리즘
1. 대상 상담사 = `User.objects.filter(company=..., role='agent', is_active=True)`
2. 각 상담사에 대해 **오늘 이미 받은 리드 수** 쿼리 (`StatsDaily` 또는 직접 count)
3. `daily_quota` 설정된 상담사 중 **쿼터 여유 있음** 만 필터
4. `tie_breaker`:
   - `round_robin`: `AssignmentState.last_assigned_agent_id` 이후 다음
   - `least_loaded`: 오늘 건수가 가장 적은 agent (동률 시 랜덤)
5. 선택된 agent 에게 `Lead.agent = selected` + `assignment_type = 'auto'` + `TimelineEntry(type='assigned')`
6. 모두 DB 트랜잭션 (select_for_update 로 경합 방지)

### 경합 방지

```python
@transaction.atomic
def auto_assign(lead):
    config = AssignmentConfig.objects.select_for_update().get(company=lead.company)
    if not _is_in_window(config):
        return None
    candidates = _eligible_agents(lead.company, config)
    if not candidates:
        return None
    chosen = _pick(candidates, config.tie_breaker, config)
    lead.agent = chosen
    lead.assignment_type = 'auto'
    lead.save()
    TimelineEntry.objects.create(lead=lead, type='assigned', actor=None, payload={'agent_id': chosen.id, 'reason': 'auto'})
    return chosen
```

**Postgres `SELECT FOR UPDATE`** 로 동시 제출 시 one-at-a-time 직렬화. Firestore transaction 보다 단순.

---

## 12. 수익화 (v2 §11 승계, 모델만 Django 적응)

가격 (Starter ₩49,000 / Pro ₩149,000 / Enterprise ₩500,000+), 14일 체험, 포트원(토스페이먼츠 PG) 정기결제. 

**실행 주체 모델:** `apps/companies/models.py` 의 `Billing` + `Invoice` (위 §5.2). 매월 1일 Cloud Scheduler 가 `/internal/billing/charge-all` 호출 → 각 Company 에 대해 포트원 API `POST /v2/billing/{billing_key}` → 성공/실패 `Invoice` 생성 + Company.billing_status 업데이트.

**체험 만료 처리:** `trial_end < now()` 이고 결제수단 미등록 → `billing_status='read_only'` → middleware 에서 쓰기 요청 차단 + 경고 배너.

---

## 13. 법·컴플라이언스 (v2 §12 승계)

개인정보처리방침 모델(`Company.privacy_doc` or 별도 `PrivacySetting`), 녹취 보관기한 자동삭제(Phase 2), 데이터 격리(§6 위 참조), 감사 로그(`TimelineEntry` + `admin_log` 확장).

---

## 14. 유지보수 플레이북 (Django 특화)

### 14.1 로컬 개발 세팅

```bash
# Postgres 로컬 실행
docker run -d --name crm-pg -e POSTGRES_PASSWORD=dev -e POSTGRES_DB=crm -p 5432:5432 postgres:16

# Python 환경
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 초기 마이그레이션
python manage.py migrate
python manage.py createsuperuser  # Django admin 접근용
python manage.py loaddata fixtures/industry_presets.json

# Tailwind
npm install
./node_modules/.bin/tailwindcss -i tailwind/input.css -o static/css/tailwind.css --watch

# 서버
python manage.py runserver
```

### 14.2 배포 체크리스트

1. `python manage.py check --deploy` (Django 보안 점검)
2. `pytest` (핵심 로직 단위 테스트)
3. `npm run build:css` (Tailwind 재빌드 — 우리 규칙)
4. `python manage.py makemigrations --check` (빠진 migration 없는지)
5. `gcloud app deploy --no-promote --version=canary-YYMMDD-HHMM`
6. 카나리 URL 에서 smoke test (로그인 / 리드 수신 / 상태 변경)
7. Cloud SQL 마이그레이션: `gcloud app deploy app.yaml` 이후 `gcloud app browse --version=canary-...` 에서 `?run-migrations=1` 호출 (보호된 endpoint) — **또는** 로컬에서 Cloud SQL Proxy 통해 `python manage.py migrate` 직접
8. 트래픽 전환 `gcloud app services set-traffic default --splits canary=1`
9. 5분 모니터링

### 14.3 장애 대응

- P0: `gcloud app services set-traffic default --splits PREVIOUS_VERSION=1` (즉시 롤백)
- DB migration rollback: `python manage.py migrate app_name PREVIOUS_MIGRATION`
- 포트원 결제 webhook 실패: 재시도 큐 (Cloud Tasks)

### 14.4 Django Admin 활용

- URL: `/django-admin/` (IP 화이트리스트 — 내 IP + GCP Internal)
- 용도: 고객 지원(데이터 조회), 수동 교정, 신규 회사 수동 승인 (필요 시), 감사
- 만들어둘 커스텀 필터: 회사별·플랜별·상태별

### 14.5 모니터링

- GCP Cloud Logging: 기본
- Cloud SQL Insights: 느린 쿼리 자동 탐지
- Django Debug Toolbar (개발만)
- Sentry (Phase 2 도입 — 월 에러 50+ 돌파 시)

### 14.6 비용 가이드

| 항목 | MVP 예상 | Phase 2 예상 |
|---|---|---|
| GAE Standard | ₩30k-60k/월 | ₩100k+ |
| Cloud SQL (db-f1-micro) | ₩30k/월 | db-custom-1-3840 ₩80k |
| Cloud Storage | ₩5k | ₩30k+ |
| 예산 알림 | 월 ₩100k / 80% 알림 | 월 ₩300k |

Firestore 대비 **비용 예측 가능성이 압도적으로 높음**. 갑자기 수십만원 튀는 read-bomb 없음.

---

## 15. Phase 2 / 3 로드맵 (v2 §14 승계)

- Phase 2: CTI 연동, 녹음, 다크모드, Kanban drag, funnel, 리드 스코어링, 디비카트/sseye 임포터, Sentry
- Phase 3: AI 요약, AI 스코어링, Ads API 연동, SSO, 다국어, 고급 워크플로우

---

## 16. 즉시 착수 작업 (W0, 2026-04-22~28)

Django 학습이 선행.

- [ ] **Django 공식 튜토리얼 완주** (공식 polls 튜토리얼 7개 파트) — 6-10시간
- [ ] **Django for Beginners by William Vincent** (책, 발췌독) — 핵심 챕터만: 프로젝트 구조, 인증, 모델, 뷰, Admin
- [ ] **django-allauth 셋업 예제** 따라하기 — 이메일 인증·비번 재설정
- [ ] **django-htmx 사용법 훑기** — 공식 문서 30분
- [ ] **GAE + Cloud SQL Django 공식 가이드** 읽기 (https://cloud.google.com/python/django/appengine)
- [ ] 로컬에 Postgres docker container 띄우고 간단한 Django 프로젝트로 접근 확인

### W1 착수 (2026-04-29~)

- [ ] GCP 프로젝트 `tmrrw-crm-prod` 생성, 결제 계정 연결
- [ ] Cloud SQL Postgres 16 인스턴스 `tmrrw-crm-db` 생성 (Seoul, db-f1-micro)
- [ ] Secret Manager 에 `SECRET_KEY`, `DB_PASSWORD`, `NCP_ACCESS_KEY`, `NCP_SECRET_KEY`, `PORTONE_API_KEY` 저장
- [ ] `tmrrw_crm` 레포에 Django 프로젝트 scaffold (`django-admin startproject config .`)
- [ ] `config/settings/{base,dev,prod}.py` 분리
- [ ] `app.yaml` + Cloud SQL Unix socket 연결 (hello world 페이지)
- [ ] GitHub Actions CI: lint + test + deploy-on-main
- [ ] Tailwind v4 + HTMX + Alpine.js 정적 파일 셋업
- [ ] 첫 `git push` 후 GAE 자동 배포 확인

---

## 17. 성공 기준

| 지점 | 기준 |
|---|---|
| W12 MVP 완성 (07-21) | §7 의 28 기능 전부 동작 |
| 베타 런칭 (07-22) | 3 개사 실사용, P0 버그 0 |
| 정식 런칭 (08-19) | 유료 전환 1건 이상 |
| +12주 (11월 중) | MRR ₩1,000,000, 유료 10개사 |

---

## 18. v1 · v2 · v3 요약 비교

| 항목 | v1 (기획) | v2 (Flask) | v3 (현재) |
|---|---|---|---|
| Backend | 미확정 | Flask + Jinja2 | **Django** |
| DB | 미확정 | Firestore | **Postgres (Cloud SQL)** |
| 배포 | 미확정 | GAE Standard | GAE Standard (동일) |
| 결제 | Toss Payments | 포트원 | 포트원 (동일) |
| 환경 | prod+stg | prod-only | prod-only (동일) |
| 타임라인 | 10주 | 10주 | 12주 (Django 학습 포함) |
| 가격 | Starter/Pro/Ent | 동일 | 동일 |

---

## 19. 법적 안전 체크리스트 (v2 §17 승계)

런칭 전 self-review:

- [ ] URL 에 `/topmanager/`, `/accept/`, `/consult/`, `.html` **없음**
- [ ] HTML/CSS/JS/이미지 파일이 1000.sseye 와 동일한 파일명·경로 **없음**
- [ ] 색상 시스템이 1000.sseye 와 비교 시 명백히 다름
- [ ] 대시보드 레이아웃(파이차트 여러 개 row) 과 다름 (KPI + 라인)
- [ ] 리드 수신 API 스펙(`?ITEM=&DBname=&DBphone=&DBfild1~17=`) 지원 **안 함**
- [ ] 코드 내부 클래스·함수명에 sseye 원문 키워드(`DBfild`, `Move_value`, `Code_num`, `Mode_value`) **없음**
- [ ] 디자인 레퍼런스는 Linear/Attio/Pipedrive 계열

---

*문서 종료. W0 학습 단계 착수.*

# 🚀 tmrw Relay — 실행 계획 v2 (모든 결정 완료)

> 본 문서는 **내가 단독 의사결정권자**로서 확정한 실행 계획이다.
> 대표 결재/토의 대상 아님. 구현 착수 근거 문서.
>
> 작성일: 2026-04-22 · 결정자: 기획·엔지니어링 owner · 최종 승인: self
>
> v1(`CRM_MVP_기획보고서_v1.md`)의 의사결정 요청 7개 항목은 본 문서에서 전부 결론.

---

## 0. 대원칙 (판단 기준)

모든 설계 결정은 아래 순위로 판단한다.

| 순위 | 기준 | 의미 |
|---|---|---|
| 1 | **유지보수 편의성** | 1인 운영 가능한 단순함. tmrw_web과 같은 스택. 덜 움직이는 부품. |
| 2 | **수익화** | 결제·요금제·사용량 측정·영업 랜딩 모두 MVP 포함. |
| 3 | **법적 모방 리스크 제거** | 디자인·UI·URL·용어·API 스펙 전면 차별화. 기능 모방은 허용. |

이 원칙에 위배되는 후보는 기각한다.

---

## 1. 프로젝트 정의

### 1.1 서비스명 — **tmrw Relay**

`Relay` = 릴레이 경주처럼 리드가 *접수 → 배정 → 상담 → 매출* 로 바통 넘어가는 메타포. 짧고 기억 쉬우며, 한국어로도 "릴레이" 발음 자연스러움.

tmrw 브랜드 하위 서브 서비스 형태로 포지셔닝. 로고는 기존 tmrw 워드마크 옆에 `Relay` 첨부.

### 1.2 도메인

- 서비스: **`relay.tmrrwmkt.com`** (기존 tmrrwmkt 도메인 서브)
- 공개 랜딩: `relay.tmrrwmkt.com/` (로그인 전)
- 앱: `relay.tmrrwmkt.com/app/*` (로그인 후)
- 리드 수신 API: `api.tmrrwmkt.com/relay/v1/*` 또는 `relay.tmrrwmkt.com/api/v1/*` ← 단일 도메인으로 관리 편의 우선, 후자 채택

### 1.3 저작권/모방 리스크 회피 원칙

| 영역 | 1000.sseye | 우리 (tmrw Relay) | 차별화 강도 |
|---|---|---|---|
| 색상 | 진한 파란색 sidebar + 파이차트 | **slate-950 sidebar + indigo accent, KPI 카드 + 라인차트 중심** | 🔴 강함 |
| 레이아웃 | 좌측 진파랑 고정 + 전체 테이블 | 좌측 **collapsible** sidebar + 카드 그리드 + 오른쪽 슬라이드 drawer | 🔴 강함 |
| URL | `/topmanager/`, `/accept/`, `/consult/`, `.html` | `/app/admin/`, `/app/intake/`, `/app/agent/`, 확장자 없음 | 🔴 강함 |
| 역할명(UI) | 관리자 / 접수자 / 상담자 | **관리자 / 접수 / 상담사** (접수자 X, 상담자 X) | 🟡 약간 |
| 역할명(코드) | master / accept / consult | admin / intake / agent | 🔴 강함 |
| 리드 상태 이름 | 접수/상담중/선별중/진행중/결과 | 유지 (한국 업계 표준) — **하지만 색상·아이콘·배열 다름** | 🟢 부분 |
| API 스펙 | `GET /api/?ITEM=&DBname=&DBphone=&DBfild1=...` | `POST /api/v1/leads` JSON body | 🔴 강함 |
| 커스텀 필드 이름 | `DBfild1~17` | `fields.business_type`, `fields.loan_amount_need` (의미 이름) | 🔴 강함 |
| 폰트 | 기본 sans-serif | **Pretendard** | 🟡 약간 |
| 차트 | Google Charts (파이) | **Chart.js + minimal 라인/바** | 🔴 강함 |

**절대 금지 사항.**
- 1000.sseye/디비카트의 **HTML·CSS·JS·이미지 파일** 직접 복사 X
- **스크린샷 재사용** X (우리 구현에서)
- 캡처한 HTML은 *기능 분석용 참고만*, 코드 레퍼런스 X

**허용 사항.**
- 기능 개념 모방 (자동 배정, 진행 상태, 커스텀 필드 — 이것들은 CRM 업계 표준)
- 비즈니스 로직 벤치마킹 (쿼터 기반 자동 분배 아이디어)
- 용어 참고 (한국어 업계 표준 유지)

---

## 2. 기술 스택 확정 (유지보수 1위 기준)

| 레이어 | 확정 | 근거 |
|---|---|---|
| Backend | **Flask 3.0 + Python 3.12** | tmrw_web과 동일 — 학습 곡선 0, 공유 코드 가능 |
| DB | **Firestore** | tmrw_web 동일, 관리형, 백업 자동 |
| Frontend | **Jinja2 + HTMX + Alpine.js + Tailwind v4** | Next.js 추가 파이프라인 X, 1 repo 1 스택 |
| 실시간 업데이트 | **HTMX polling (5-10s)** | SSE/WebSocket 대비 디버깅 쉬움, Flask 기본 기능만 |
| 인증 | **Flask session** (tmrw_web 동일) | 외부 의존성 최소 |
| 인프라 | **GAE Standard** (별도 GCP 프로젝트) | 기존 운영 경험, 청구 분리 |
| SMS/알림톡 | **NCP SENS** | tmrw_web 이미 연동, `sms.py` 재사용 |
| GCS | 녹취·엑셀 업로드 저장용 (Phase 2부터) | 기존 ADC 그대로 |
| 결제 | **포트원(PortOne) — 기본 PG 토스페이먼츠** | 여러 PG·결제수단 한 SDK로 통합, 코드 변경 없이 PG 전환·추가 가능. B2B 고객 "KG이니시스 계약만 됨" 같은 요구 유연 대응. |
| AI | (Phase 3) **Claude API** | 한국어 품질, 장문 컨텍스트 |
| 에러 모니터링 | **Sentry** (Phase 2 추가) | GCP Cloud Logging 은 MVP 동안 충분 |
| CI/CD | GitHub Actions → GAE deploy | 기존 흐름과 일관 |

### 2.1 스택에서 명시적으로 배제한 것 + 사유

| 배제 대상 | 사유 |
|---|---|
| Next.js / React | 별도 빌드·배포·타입 체크 파이프라인. 1인 운영 부담 증가. |
| Postgres | Firestore 비용 리스크 알지만, MVP 단계 볼륨에선 비용 < 마이그레이션 비용. Phase 3에서 재검토. |
| WebSocket / SSE | 서버 리소스/디버깅 복잡. HTMX polling 으로 충분. |
| Firebase JS SDK (클라이언트) | 서버 중심 구조 깨짐. 다중 보안 경계 관리 부담. |
| GraphQL | REST로 충분. Firestore와 잘 안 맞음. |
| 자체 SMS 인프라 | 규제·발송률 문제, NCP 유지. |
| 다크모드 (MVP) | Tailwind 이중 클래스 관리 · QA 부담. **Phase 2**. |

---

## 3. 저장소 / 프로젝트 구조

### 3.1 새 GitHub 저장소: `tmrw_relay`

tmrw_web과 **분리**. 이유:
- 독립 배포, 장애 격리
- 청구 분리 (별도 GCP 프로젝트)
- 회사 내부 권한 다른 개발자 참여 시 보안 경계 명확

### 3.2 초기 공유 코드 (tmrw_web → tmrw_relay 복사)

아래 모듈은 초기 복사 + 분기 유지. 공통 라이브러리 추출은 Phase 2까지 보류 (이른 추상화 금지).

- `app/extensions.py` (Firestore init)
- `app/sms.py` (NCP SENS, access_key는 Secret Manager 로 이전 — tmrw_web 기술부채 함께 해소)
- `app/hierarchy.py` (조직 계층 권한 체크)
- `app/alerts.py` (NOTI 실패 throttle + SMS)
- `app/user_migration.py` (유저 삭제·자산 이관 청크 버퍼 패턴)
- `app/legal.py` (개인정보처리방침 read/write)

### 3.3 레포 디렉토리 스켈레톤

```
tmrw_relay/
├── app/
│   ├── __init__.py              Flask app factory
│   ├── extensions.py            Firestore, Secret Manager 초기화
│   ├── auth.py                  로그인·세션
│   ├── company.py               회사 가입·결제·요금제
│   ├── user.py                  사용자 CRUD·역할·삭제·이관
│   ├── hierarchy.py             조직 계층 (복사)
│   ├── source.py                유입 채널 (Source) CRUD
│   ├── field.py                 커스텀 필드 정의
│   ├── lead.py                  리드 CRUD · 목록 · 상세
│   ├── assignment.py            자동/수동 배정 엔진
│   ├── timeline.py              활동 로그 기록/조회
│   ├── template.py              SMS 템플릿
│   ├── callback.py              콜백 예약
│   ├── blacklist.py             중복 감지 · 블랙리스트
│   ├── noti.py                  외부 수신처로의 NOTI + 실패 모니터링
│   ├── dashboard.py             대시보드 · 통계
│   ├── api_v1.py                외부 리드 수신 API
│   ├── billing.py               Toss 정기결제 · 사용량 집계
│   ├── sms.py                   NCP SENS (복사)
│   ├── alerts.py                복사
│   ├── legal.py                 복사
│   └── templates/               Jinja2
│       ├── base.html
│       ├── admin/*.html
│       ├── intake/*.html
│       ├── agent/*.html
│       └── public/*.html        랜딩 · 가입
├── static/
│   ├── css/tailwind.css         빌드 산출물
│   ├── js/app.js                Alpine.js 컴포넌트
│   └── img/
├── tailwind/input.css
├── tailwind.config.js
├── app.yaml
├── requirements.txt
├── package.json
├── run.py
├── .claude/
│   └── memory/
│       ├── MEMORY.md
│       ├── project_tmrw_relay.md
│       └── feedback_*.md
└── docs/
    ├── CRM_MVP_기획보고서_v1.md  (보존)
    ├── CRM_실행계획_v2.md        (본 문서)
    ├── 데이터_모델.md
    ├── API_스펙.md
    └── 배포_플레이북.md
```

---

## 4. 용어 매핑 (1000.sseye → tmrw Relay)

### 4.1 역할

| 1000.sseye | 우리 UI 표기 | 우리 코드명 | URL prefix |
|---|---|---|---|
| 관리자 (master) | 관리자 | `admin` | `/app/admin/` |
| 접수자 (accept) | 접수 | `intake` | `/app/intake/` |
| 상담자 (consult) | 상담사 | `agent` | `/app/agent/` |

### 4.2 주요 엔티티

| 1000.sseye 개념 | UI 표기 | 코드명 | Firestore 경로 |
|---|---|---|---|
| 광고분류 / 랜딩 | **유입 채널** | `source` | `companies/{cid}/sources/{sid}` |
| 항목설정 / DBfild | **커스텀 필드** | `field` | `companies/{cid}/fields/{fid}` |
| 고객 / 리드 | **리드** | `lead` | `companies/{cid}/leads/{lid}` |
| 관리메모 | **활동 로그 / 메모** | `timeline_entry` | `.../leads/{lid}/timeline/{tid}` |
| 분배 / 자동분배 | **배정 / 자동 배정** | `assignment` | 관련 필드 + 서비스 |
| 진행상태 | **상태** | `status` | lead 필드 |
| 접수인 / 담당자 | **접수자 / 담당 상담사** | `intake_uid` / `agent_uid` | lead 필드 |

### 4.3 리드 상태 머신

| 한국어(UI) | 코드 | 색상 | 의미 |
|---|---|---|---|
| 접수 | `new` | slate-500 | 수신 직후, 아무도 터치 안 함 |
| 상담중 | `contacted` | indigo-500 | 상담사가 최소 1회 컨택 |
| 선별중 | `qualified` | amber-500 | 상담 진행, 성사 가능성 판별 중 |
| 진행중 | `negotiating` | violet-500 | 계약/가입 진행 |
| 결과-성사 | `won` | emerald-600 | 매출 확정 |
| 결과-실패 | `lost` | rose-500 | 최종 거절/연결 실패 |

*1000.sseye의 5단계를 6단계로 세분화 (결과를 won/lost로 분리). 실질적 차별화 + 매출 통계 정확도 향상.*

### 4.4 커스텀 필드 초기 프리셋 (대출·자금 업종)

1000.sseye의 `DBfild1~17` 대신 **의미 있는 이름** 사용:

| UI 레이블 | 코드 필드명 | 타입 | 초기 옵션 |
|---|---|---|---|
| 이름 | `name` | text (required) | — |
| 전화번호 | `phone` | text (required) | — |
| 업종 | `business_type` | select | 도소매업, 서비스업, 제조업, 건설업, 기타 |
| 전년도 매출 | `revenue_last_year` | select | 1천~5천, 5천~1억, 1억~3억, 3억 초과 |
| 필요자금 규모 | `loan_amount_need` | select | 1천~5천, 5천~1억, 1억 초과 |
| 상담가능 시간 | `preferred_time` | select | 오전/오후/저녁 |
| 신용점수 | `credit_score` | select | 700 미만, 700 이상 |
| 지역 | `region` | text | — |
| 상호명 | `business_name` | text | — |
| 사업자등록번호 | `business_no` | text | — |

회사 가입 시 "업종 선택" 단계에서 프리셋 자동 로드. 추가 필드는 관리자 설정에서 편집.

---

## 5. URL / 화면 지도

### 5.1 공개 (비로그인)

| URL | 역할 |
|---|---|
| `/` | 마케팅 랜딩 (서비스 소개, 가격, CTA: 14일 무료 시작) |
| `/pricing` | 가격제 상세 |
| `/signup` | 회사 가입 (대표 이메일 + 회사명) |
| `/login` | 로그인 |
| `/legal/privacy` | 개인정보처리방침 |
| `/legal/terms` | 이용약관 |

### 5.2 공용 앱 (로그인 후, 역할 무관)

| URL | 역할 |
|---|---|
| `/app` | 역할에 따라 대시보드로 redirect |
| `/app/me` | 내정보 · 비번/이름/전화 변경 |

### 5.3 Admin (`/app/admin/*`)

| URL | 화면 |
|---|---|
| `/app/admin` | 대시보드 (KPI 카드 + 7일 라인 + 리드 source 파이) |
| `/app/admin/leads` | 리드 목록 (테이블/그리드 전환) |
| `/app/admin/leads/{lid}` | 리드 상세 + 타임라인 drawer |
| `/app/admin/leads/new` | 수동 리드 등록 |
| `/app/admin/leads/trash` | 휴지통 |
| `/app/admin/sources` | 유입 채널 관리 |
| `/app/admin/sources/{sid}` | 유입 채널 편집 + API 토큰 |
| `/app/admin/fields` | 커스텀 필드 정의 |
| `/app/admin/assignment` | 배정 쿼터 설정 (상담사별) |
| `/app/admin/assignment/config` | 자동 배정 on/off + 요일 + 시간대 |
| `/app/admin/stats` | 통계 (일별/월별/채널별 탭) |
| `/app/admin/blacklist` | 블랙리스트 |
| `/app/admin/templates` | SMS 템플릿 |
| `/app/admin/users` | 사용자 CRUD + 조직 계층 + 삭제/이관 |
| `/app/admin/billing` | 요금제 · 결제 수단 · 청구서 · 사용량 |
| `/app/admin/settings` | 회사 정보 · 로고 · 타임존 |

### 5.4 Intake (`/app/intake/*`)

| URL | 화면 |
|---|---|
| `/app/intake` | 대시보드 (본인 접수 건 집계) |
| `/app/intake/queue` | 미배정 리드 큐 (수동 배정 primary) |
| `/app/intake/leads` | 리드 목록 (본인이 접수했거나 볼 수 있는 것) |
| `/app/intake/leads/{lid}` | 리드 상세 |
| `/app/intake/leads/new` | 수동 리드 등록 |
| `/app/intake/stats` | 본인 기준 통계 |

### 5.5 Agent (`/app/agent/*`)

| URL | 화면 |
|---|---|
| `/app/agent` | 대시보드 (내 할당 현황 + 오늘 콜백 + 미컨택 수) |
| `/app/agent/today` | 오늘 할 일 (콜백 + 미컨택 + 선별중) |
| `/app/agent/leads` | 내 담당 리드 목록 |
| `/app/agent/leads/{lid}` | 리드 상세 + 상담 기록 |
| `/app/agent/stats` | 본인 실적 |

### 5.6 API (`/api/v1/*`)

| Method | 경로 | 용도 |
|---|---|---|
| POST | `/api/v1/leads` | 외부에서 리드 수신 (Bearer token 인증) |
| POST | `/api/v1/leads/{lid}/timeline` | 타임라인 엔트리 추가 (for CTI 연동 등) |
| GET | `/api/v1/leads/{lid}` | 리드 조회 (Phase 2+, API 고객용) |
| POST | `/webhooks/toss` | Toss 결제 webhook |
| POST | `/webhooks/tmrw` | tmrw_web 랜딩 직주입 (내부) |

### 5.7 리드 수신 API 스펙 (MVP v1)

```http
POST /api/v1/leads
Host: relay.tmrrwmkt.com
Authorization: Bearer <source_token>
Content-Type: application/json

{
  "name": "홍길동",
  "phone": "01012345678",
  "fields": {
    "business_type": "도소매업",
    "loan_amount_need": "1천~5천",
    "credit_score": "700 이상"
  },
  "external_id": "my-landing-form-submission-abc",   // 선택
  "external_ip": "1.2.3.4"                             // 선택
}
```

응답:

```json
{
  "lead_id": "lid_abc123",
  "status": "new",
  "duplicate_of": null,      // 중복 전화 감지 시 기존 lead_id
  "blacklisted": false
}
```

에러:
- `401` 토큰 없음/유효하지 않음
- `400` 필수 필드 누락 / 스키마 오류
- `403` 요금제 한도 초과 (월 리드 한도)
- `422` blacklist 된 전화번호 (선택적으로 201 + `blacklisted:true`로 저장할 수도 — 감사 목적)

**1000.sseye의 `?ITEM=&DBname=&DBphone=&DBfild1=` 구조는 의도적으로 지원 안 함.** 고객에게는 "RESTful 현대 표준" 포지셔닝. 마이그레이션이 필요하면 공식 임포터 제공 (Phase 2).

---

## 6. 데이터 모델 최종

### 6.1 Firestore 계층

```
companies/{cid}                       ─ 테넌트 최상위, 절대 격리
├── (회사 문서 필드)
│   name, created_at, plan, billing_status, trial_end,
│   timezone, industry_preset, owner_uid, custom_domain?, logo_url
│
├── users/{uid}
│   ├── login_id, password_hash, email
│   ├── name, phone
│   ├── role                         — 'admin' | 'intake' | 'agent' | 'owner'
│   ├── manager_id, ancestors[], depth
│   ├── daily_quota                  — 자동 배정 쿼터 (agent 전용, null=무제한)
│   ├── is_active, created_at
│   └── last_login_at
│
├── sources/{sid}
│   ├── title                        — "A사 랜딩", "스마트 광고" 등
│   ├── api_token_hash               — bcrypt 해시, 원문은 발급 시 1회만
│   ├── api_token_prefix             — 토큰 앞 6자리 (UI 표시용)
│   ├── tmrw_form_id?                — tmrw_web 랜딩 연동 시 매핑
│   ├── is_active
│   └── created_at
│
├── fields/{fid}
│   ├── code                         — 'business_type' 등 (고유, 필드 API key)
│   ├── label                        — '업종'
│   ├── type                         — 'text' | 'select' | 'number'
│   ├── options[]                    — select 일 때
│   ├── sort_order, is_required
│   └── is_built_in                  — 'name', 'phone' 등 시스템 필드 여부
│
├── leads/{lid}
│   ├── source_id, intake_uid?, agent_uid?
│   ├── status                       — 'new' | 'contacted' | 'qualified' | 'negotiating' | 'won' | 'lost'
│   ├── assignment_type              — 'auto' | 'manual' | 'unassigned'
│   ├── name, phone, phone_hash      — 중복 감지용 해시
│   ├── fields                       — {business_type, loan_amount_need, ...}
│   ├── duplicate_of                 — 기존 lid (있으면)
│   ├── noti_status                  — 'ok' | 'failed' | 'failed_cleared'
│   ├── noti_last_error?
│   ├── external_id?, external_ip?
│   ├── created_at, received_at
│   ├── contacted_at?, qualified_at?, closed_at?
│   └── timeline/{tid}               ─ 활동 로그 서브컬렉션
│       ├── type                     — 'status_change' | 'memo' | 'sms_sent' | 'callback_scheduled' | 'noti_sent' | 'noti_failed' | 'assigned'
│       ├── actor_uid                — 'system' 도 허용
│       ├── at
│       └── payload                  — type 별 자유 스키마
│
├── blacklist/{phone_hash}
│   ├── phone_masked                 — '010-****-1234' 표시용
│   ├── reason, added_by, added_at
│
├── templates/{tid}
│   ├── title, body, channel('sms'|'alimtalk')
│   ├── variables[]                  — '{name}' 같은 치환 키
│   └── is_active
│
├── callbacks/{kid}
│   ├── lead_id, agent_uid
│   ├── scheduled_at
│   ├── reminder_sent (bool)
│   └── status                       — 'pending' | 'done' | 'missed'
│
├── assignment_config (singleton)
│   ├── auto_on (bool)
│   ├── weekdays[]                   — [0..6]
│   ├── time_start, time_end         — "09:00", "18:00"
│   └── tie_breaker                  — 'round_robin' | 'least_loaded'
│
├── stats_daily/{yyyymmdd}
│   ├── by_status {new:N, contacted:N, ...}
│   ├── by_source {sid: N}
│   ├── by_agent {uid: N}
│   └── total
│
├── billing (singleton)
│   ├── plan, payment_method_id
│   ├── toss_billing_key
│   ├── next_billing_at
│   ├── usage_current_cycle {leads:N, sms:N, storage_mb:N}
│   └── invoices/{invoice_id}
│
├── alerts_throttle/{uid__step}      — tmrw_web 패턴 재사용
└── settings (singleton)
    ├── company info
    └── integrations {tmrw_web_api_key?, naver_biz_talk_key?}
```

### 6.2 전역 컬렉션 (회사 외부)

```
signup_tokens/{token}                 — 가입 이메일 인증
password_resets/{token}
sms_verifications/{phone}             — tmrw_web 재사용
api_access_log/{log_id}               — 외부 수신 API 감사 로그 (선택)
```

### 6.3 Firestore 인덱스 사전 정의

초기 배포 전에 `index.yaml` 에 아래 전부 명시. 운영 중 "인덱스 필요" 에러 방지.

| 컬렉션 그룹 | 필드 | 쿼리 용도 |
|---|---|---|
| `leads` | `status` + `created_at desc` | 상태별 최신순 |
| `leads` | `agent_uid` + `status` + `created_at desc` | 담당자별 상태 필터 |
| `leads` | `source_id` + `created_at desc` | 채널별 |
| `leads` | `phone_hash` + `created_at desc` | 중복 탐지 |
| `leads` | `noti_status` + `created_at desc` | 실패 건 조회 |
| `callbacks` | `agent_uid` + `scheduled_at` | 내 콜백 목록 |
| `timeline` (collection_group) | `at desc` | 사용 시 필요 |

---

## 7. MVP v1.0 기능 확정 (10주 출시)

### 7.1 포함 (20개 기능)

#### 기반
1. **회사 가입** (이메일 인증 + 14일 무료체험 자동 개시)
2. **로그인 / 세션 / 비번 재설정**
3. **사용자 초대 + 역할 지정** (이메일 링크)
4. **조직 계층** (tmrw_web 로직 복사)
5. **사용자 삭제 + 자산 이관** (tmrw_web 로직 복사)

#### 리드 수집
6. **유입 채널 CRUD + API 토큰 발급**
7. **리드 수신 API** (`POST /api/v1/leads`)
8. **tmrw_web 랜딩 직접 통합** (내부 webhook 또는 Firestore 다중 쓰기)
9. **수동 리드 등록 화면**

#### 리드 작업
10. **커스텀 필드 정의** (select | text | number, 업종 프리셋 지원)
11. **리드 목록** (검색/필터/정렬/페이지네이션/엑셀)
12. **리드 상태 그리드 뷰** (상태별 열, 카드형 — Kanban 룩)
13. **리드 상세 + 상태 머신**
14. **활동 타임라인** (상태전환/메모/SMS/배정 자동 로그)

#### 배정
15. **자동 배정 엔진** (쿼터 + 요일 + 시간대)
16. **수동 배정 + 재배정** (단건/일괄)

#### 커뮤니케이션
17. **SMS/알림톡 템플릿 CRUD + 발송** (NCP SENS)
18. **콜백 예약 + 브라우저 알림**

#### 품질/모니터링
19. **중복 전화 감지 + 블랙리스트**
20. **NOTI 실패 감지 🔴** (외부 수신처로 보낼 때 — tmrw_web 모듈 복사)

#### 통계
21. **대시보드** (KPI 카드 + 7일 라인차트 + 채널별 도넛)
22. **통계 페이지** (일별/월별 테이블, 채널별, 엑셀)

#### 수익화
23. **가격제 3단 + 포트원 정기결제 (기본 PG 토스페이먼츠)**
24. **사용량 측정 + 한도 초과 시 API 403**
25. **청구서/결제수단 관리**

#### 공개
26. **마케팅 랜딩 페이지** (서비스 소개 + 가격 + CTA)

#### UX
27. **모바일 반응형**
28. **키보드 단축키** (리드 목록: j/k 이동, e 편집, s 상태, m 메모)

### 7.2 제외 (Phase 2 이후)

| 기능 | 제외 사유 | Phase |
|---|---|---|
| CTI 통화 연동 | 파트너사 협의 필요 | 2 |
| 통화 녹음 보관 | 법적 검토 + GCS 설계 | 2 |
| Kanban drag-and-drop | 유지보수 부담 → 클릭 이동으로 대체 | 2 |
| 다크모드 | Tailwind 이중 클래스 부담 | 2 |
| 전환 funnel / ROI | 데이터 쌓인 후 의미 | 2 |
| AI 통화 요약 | 녹음 기능 선행 필요 | 3 |
| AI 리드 스코어링 | 데이터 필요 | 3 |
| SSO / SAML | 엔터프라이즈 수요 생길 때 | 3 |
| Salesforce 임포터 | MVP 고객 대상 아님 | 3 |
| 다국어 | MVP는 한국어 전용 | 3 |

---

## 8. 디자인 시스템 (1000.sseye와 시각적 절대 차이)

### 8.1 컬러 팔레트

```
Background         bg-white (라이트) / bg-slate-50 (앱 배경)
Sidebar            bg-slate-900 text-slate-100 (다크 고정)
Primary accent     indigo-600 (#4f46e5) — 버튼, 링크
Success            emerald-500
Warning            amber-500
Danger             rose-500
Neutral text       slate-800 (제목) / slate-600 (본문) / slate-400 (보조)
Border             slate-200
Status badge       상태별 tailwind 색상 (§4.3)
```

1000.sseye의 **진한 블루 sidebar + 밝은 cyan accent** 과 확연히 다른 **slate-900 sidebar + indigo accent** 조합. 감각적으로 Linear / Attio / Notion 계열.

### 8.2 타이포그래피

- **Pretendard** (CDN via `cdn.jsdelivr.net/gh/orioncactus/pretendard/...`)
- 본문 14px / 소제목 16px / 제목 20-24px / 숫자(대시보드) 28-32px
- font-weight: 400 / 500 / 600 / 700 (800 금지 — 디자인 통일)

### 8.3 레이아웃

```
┌──────────────────────────────────────────────────────────┐
│ Sidebar (slate-900)  │   Topbar (회사명 · 검색 · 내정보)   │
│                      ├──────────────────────────────────┤
│ · 대시보드           │                                    │
│ · 리드 🔴            │    본문 영역                         │
│ · 유입 채널          │    카드 기반 레이아웃                │
│ · ...                │                                    │
│                      │                                    │
│ [⇐ 접기]             │                                    │
└──────────────────────┴──────────────────────────────────┘
```

- Sidebar **collapse 지원** (아이콘만 남김) — 1000.sseye 고정 sidebar 와 다름
- 모바일: sidebar off-canvas (햄버거 버튼)
- Topbar: Cmd/Ctrl+K 눌러 빠른 검색 (Phase 2에서 명령 팔레트 확장 가능)

### 8.4 컴포넌트 라이브러리 (자체 구축, 최소)

재사용 컴포넌트 (Jinja macro + Tailwind 조합):

| 컴포넌트 | macro |
|---|---|
| 버튼 (primary/secondary/danger/ghost) | `btn(text, variant)` |
| 배지 (상태용) | `status_badge(status)` |
| 카드 (제목·본문) | `card(title, body)` |
| KPI 카드 (숫자+라벨+추세) | `kpi_card(value, label, delta)` |
| 테이블 (정렬·빈 상태) | `table(headers, rows)` |
| 빈 상태 | `empty_state(icon, title, cta)` |
| 모달 (Alpine) | `modal(id, title, body)` |
| Drawer (오른쪽 슬라이드, Alpine) | `drawer(id, title, body)` |
| Confirm 다이얼로그 | `confirm_dialog(message, onconfirm)` |
| Toast (Alpine + localStorage) | `toast()` |
| Form field | `field(label, input, hint, error)` |
| Dropdown | `dropdown(label, items)` |

### 8.5 아이콘

- **Lucide Icons** (오픈소스, Linear 계열 감각). 1000.sseye 스타일과 달라서 적합.
- SVG 인라인 (Jinja include)

### 8.6 차트

- **Chart.js v4** (Tailwind와 잘 맞음, 가벼움, MIT)
- 1000.sseye는 Google Charts — 완전 다른 선택
- MVP 차트 3종: 라인 (7일 추이) / 바 (일별 건수) / 도넛 (채널 비중)
- 파이차트 X (작게 여러 개 배열하는 1000.sseye 스타일 회피)

---

## 9. 권한 매트릭스

| 기능 | Owner | Admin | Intake | Agent |
|---|---|---|---|---|
| 회사 설정 · 결제 | ✅ | ❌ | ❌ | ❌ |
| 사용자 초대 / 역할 변경 / 삭제 | ✅ | ✅ | ❌ | ❌ |
| 조직 계층 변경 | ✅ | ✅ | ❌ | ❌ |
| 유입 채널 CRUD + API 토큰 | ✅ | ✅ | 보기 | ❌ |
| 커스텀 필드 정의 | ✅ | ✅ | ❌ | ❌ |
| 자동 배정 규칙 설정 | ✅ | ✅ | ❌ | ❌ |
| 모든 리드 조회 | ✅ | ✅ | 본인 범위 | 본인 담당 |
| 리드 수동 등록 | ✅ | ✅ | ✅ | ❌ |
| 리드 배정/재배정 | ✅ | ✅ | ✅ (본인→상담사) | ❌ |
| 리드 상태 변경 | ✅ | ✅ | ✅ | ✅ (본인 담당) |
| 리드 삭제 | ✅ | ✅ | ❌ | ❌ |
| 메모 · SMS 발송 | ✅ | ✅ | ✅ | ✅ (본인 담당) |
| 블랙리스트 관리 | ✅ | ✅ | ❌ | ❌ |
| 템플릿 CRUD | ✅ | ✅ | ❌ | ❌ |
| 콜백 예약 | ✅ | ✅ | ❌ | ✅ |
| 통계 전체 | ✅ | ✅ | 본인 범위 | 본인 실적 |

**Owner**: 회사 가입한 최초 계정. 결제권 보유. Admin 여러 명 가능하지만 Owner는 1명.

---

## 10. 타임라인 (10주 확정, 2026-05-01 ~ 2026-08-07)

| 주차 | 기간 | 작업 | 완료 기준 |
|---|---|---|---|
| W1 | 05-01 ~ 05-07 | 신규 GCP 프로젝트 · 레포 초기화 · CI/CD · 기본 app factory · tmrw_web 공유 코드 복사 | `hello world` GAE 배포, Firestore 연결 |
| W2 | 05-08 ~ 05-14 | 인증 (가입/로그인/세션/비번재설정) · 회사 생성 · owner 자동 부여 · 디자인 시스템 base | 계정 만들고 로그인 가능 |
| W3 | 05-15 ~ 05-21 | 사용자 초대 · 역할 · 조직 계층 · 삭제/이관 | 멀티 유저 회사 운영 가능 |
| W4 | 05-22 ~ 05-28 | 유입 채널 CRUD · API 토큰 · 리드 수신 API · tmrw_web 통합 | 외부 curl 으로 리드 POST → Firestore 저장 |
| W5 | 05-29 ~ 06-04 | 커스텀 필드 · 리드 목록 (검색/필터) · 엑셀 export | 리드 100건 들어있을 때 빠르게 조회 |
| W6 | 06-05 ~ 06-11 | 리드 상세 · 상태 머신 · 그리드 뷰 · 수동 리드 등록 | 한 리드 full lifecycle 처리 |
| W7 | 06-12 ~ 06-18 | 자동 배정 엔진 · 수동 배정 · 재배정 · 배정 설정 UI | 쿼터·요일·시간대 제약 자동 작동 |
| W8 | 06-19 ~ 06-25 | 활동 타임라인 · SMS 템플릿 발송 · 콜백 예약 + 브라우저 알림 | 리드 상세에서 모든 커뮤니케이션 로그됨 |
| W9 | 06-26 ~ 07-02 | 블랙리스트 · 중복 감지 · NOTI 실패 빨간불 · 대시보드 · 통계 | 대시보드 실데이터로 의미 있음 |
| W10 | 07-03 ~ 07-09 | 포트원 정기결제 · 요금제 · 사용량 · 체험판 · 마케팅 랜딩 · 버그 | 유료 결제까지 end-to-end 가능 |

**베타 운영:** 07-10 ~ 08-07 (4주). 기존 tmrw 고객 3개사 대상, 피드백 기반 패치.

**정식 런칭:** 08-08 (실제 결제 유도 개시).

### 10.1 버퍼 & 리스크 관리

- 매주 금요일 30분 자가 회고 (completed / blocked / next)
- 2주 연속 지연 시 범위 재조정 (Should Have 순으로 컷)
- 마감 4주 전(W6 끝) 중간 점검 지점 — 가장 복잡한 자동 배정 엔진이 끝났는지 확인

---

## 11. 수익화 설계

### 11.1 요금제 확정

| 플랜 | 월 정가 | 연납 할인 | 포함 | 상단 한도 |
|---|---|---|---|---|
| **Starter** | ₩49,000 | 2개월 free | 유저 3 / 리드 1,000/월 / SMS 100/월 | — |
| **Pro** *(주력)* | ₩149,000 | 2개월 free | 유저 10 / 리드 10,000/월 / SMS 1,000/월 / 녹취 50GB (Phase 2) | AI 요약 월 500건 (Phase 3) |
| **Enterprise** | 협의 (₩500,000+) | 협의 | 무제한 / SSO (Phase 3) / 전담 지원 | 맞춤 계약 |

**추가 상품.** SMS 추가 건당 ₩20 / 녹취 100GB ₩30,000·월

### 11.2 체험판 정책

- 가입 즉시 **Pro 플랜 14일 무료**
- 체험 중 SMS 10건 · 리드 300건 · 사용자 3명 한도 (남용 방지)
- 만료 전 결제 수단 등록 안 하면 자동으로 **read-only 모드** (데이터는 30일 보존)

### 11.3 결제 플로우 (포트원)

**용어 정리.** 포트원(PortOne, 구 아임포트) = 여러 PG·결제수단을 단일 SDK로 통합하는 한국 결제 미들웨어. 우리 기본 PG는 **토스페이먼츠**로 시작하되, 고객 요구 시 KG이니시스·카카오페이·네이버페이 등을 콘솔에서 추가만 하면 됨.

**결제 수단.** 신용카드 / 계좌이체 / 카카오페이 / 네이버페이 / 토스페이 / 페이코 / 삼성페이 / 휴대폰 결제 (선택 가능 수단은 PG 계약과 포트원 콘솔 설정으로 제어).

**가입 및 정기결제 흐름.**
1. `/app/admin/billing` → **포트원 SDK로 빌링키 발급** (카드/간편결제 등 1회 등록)
2. 빌링키 저장 (`companies/{cid}/billing.portone_billing_key`, `billing.pg_provider`)
3. 매월 자동 결제 Cloud Scheduler(GAE Cron) → **포트원 REST API 호출**로 키 기반 결제
4. 실패 시 관리자 이메일 + 3일 후 read-only 전환
5. webhook (`/webhooks/portone`) 으로 결제 성공/실패 동기화 + 영수증 발급

**테스트.** 포트원 대시보드의 테스트 모드 + 각 PG 의 sandbox 카드 번호로 실결제 없이 end-to-end 검증 가능.

### 11.4 사용량 측정 엔드포인트

- 리드 수신 시 `billing.usage_current_cycle.leads += 1`
- SMS 발송 시 `billing.usage_current_cycle.sms += 1`
- 월 한도 초과 시 API 403 + UI 경고
- 월 1일 Cloud Scheduler 로 usage 리셋

### 11.5 영업 랜딩 포인트 (마케팅 랜딩에 노출)

- **Hero**: "디비카트에서 이관받은 광고주 N개사가 이미 사용중" *(실제 숫자 채우기)*
- **USP 3줄**: 실패 감지 🔴 / 현대 UX / AI 준비 (Phase 3 티저)
- **비교표**: 디비카트 / 1000.sseye / 엑셀 vs tmrw Relay
- **가격표**
- **고객 후기** (베타 단계 후 수집)
- **CTA**: "14일 무료로 시작하기"

---

## 12. 법·컴플라이언스 (MVP 단계 범위)

### 12.1 개인정보처리방침

- `tmrw_web/app/legal.py` 재사용. 회사별 `settings/privacy` 문서에 저장.
- 처리 목적, 보관기한, 파기 절차 명시
- 고객사는 "고객사 = 개인정보 처리자, tmrw Relay = 처리 위탁자" 관계 → 위탁 계약서 자동 제공 기능 (가입 시 체크박스)

### 12.2 녹취 (Phase 2, 미리 설계)

- GCS 버킷 **고객사별 분리** + CMEK 암호화
- 보관 기한 디폴트 90일 (설정 가능, 최대 3년)
- 보관 기한 초과 시 Cloud Scheduler 로 자동 삭제

### 12.3 데이터 격리 (MVP부터 필수)

- 모든 쿼리는 `companies/{cid}/` 하위에서만 수행
- 코드 레벨 헬퍼 `company_scoped_query(cid)` 로 강제
- 보안 리뷰 체크리스트: 모든 route 에서 `session['company_id']` 검증 필수

### 12.4 감사 로그

- 민감 작업 (유저 삭제, 블랙리스트 추가/제거, 토큰 발급, 권한 변경) → `timeline` + 별도 `audit_log` 컬렉션
- 로그 보관 1년

---

## 13. 유지보수 플레이북 (1인 운영 전제)

### 13.1 배포 체크리스트 (매 배포 전)

1. `pytest` (단위 테스트 통과, MVP 핵심 로직만 작성)
2. `npm run build:css` (Tailwind 재빌드 — 우리 규칙!)
3. Staging 배포 (`gcloud app deploy --version=stg-XXX --no-promote`)
4. Smoke test 체크리스트 (로그인 / 리드 수신 / 배정 / SMS 1건)
5. Prod 배포 (`--promote`)
6. 5분 로그 모니터링

### 13.2 장애 대응 3단계

- **P0 (서비스 다운):** GAE rollback (이전 버전 트래픽 100%), 원인 조사
- **P1 (기능 오동작):** 핫픽스 1시간 내
- **P2 (UI 버그 등):** 다음 배포에 포함

### 13.3 로그 / 모니터링

- GCP Cloud Logging (GAE 기본)
- `logging.error(...)` / `logging.exception(...)` 기본 정책
- 주간 대시보드: 에러율 / 평균 응답시간 / 월 사용량
- Sentry 연동은 Phase 2 (월 ~50개 에러 넘어가는 순간)

### 13.4 백업

- Firestore 자동 PITR (Point-in-time Recovery) 7일
- 매월 1일 수동 export → GCS (보관 1년)

### 13.5 비용 알림

- GCP 예산 알림 월 ₩500,000 기준 80% / 100% / 150%
- 초과 시 Firestore read 패턴 리뷰 (캐싱 강화)

---

## 14. Phase 2 / 3 로드맵 (참고용, 본 문서 범위 외)

**Phase 2 (2026-09 ~ 2027-02):**
- CTI 연동 (API 제공 + 파트너사 SDK)
- 통화 녹음 (GCS + 법정 보관기한)
- 다크모드
- Kanban drag-and-drop
- 전환 funnel / 채널별 ROI
- 팀 KPI 대시보드
- 리드 스코어링 (규칙 기반)
- Sentry / 고급 모니터링
- 디비카트/sseye 임포터 (엑셀 → 리드/사용자 마이그레이션)

**Phase 3 (2027-03 ~):**
- AI 통화 요약 (Whisper + Claude)
- AI 리드 우선순위 추천
- AI 상담 스크립트 실시간 제안
- Meta / TikTok / Google Ads API 연동 (광고비 ROI)
- SSO / SAML
- 다국어 (영어 1순위)
- 고급 워크플로우 (if-then-else 자동화)

---

## 15. 즉시 착수 작업 (이번 주, W1)

- [ ] GitHub `tmrw_relay` 레포 생성
- [ ] GCP 신규 프로젝트 `tmrw-relay-prod` 생성, Firestore enable, GAE Standard 세팅
- [ ] 도메인 `relay.tmrrwmkt.com` DNS A/CNAME 설정
- [ ] tmrw_web 공유 파일 초기 복사 + import 경로 수정
- [ ] `app.yaml` / `run.py` / `requirements.txt` 스켈레톤
- [ ] Tailwind v4 설정 + Pretendard 로드 + 베이스 레이아웃
- [ ] GitHub Actions: lint + (있다면) pytest + deploy-on-main
- [ ] Secret Manager에 NCP SENS 키 이전 (tmrw_web 기술부채 함께 해소)
- [ ] `/` 마케팅 랜딩 최소 HTML + `/signup` 폼 더미
- [ ] GAE 배포 확인 → W1 완료

---

## 16. 성공 기준 (MVP 런칭 시점 = 08-08)

| 지표 | 목표 |
|---|---|
| 출시된 기능 | 위 §7.1 의 28개 전부 |
| 베타 고객 | 3개사 이상 실사용 |
| 유료 전환 | 1건 이상 (체험 만료 후 결제) |
| 기능 결함 P0 | 0건 |
| 기능 결함 P1 | 5건 이하 |
| 월 GCP 비용 | ₩300,000 이하 |

**12주 후 (10-31) 목표:** 유료 고객 10개사 / MRR ₩1,000,000.

---

## 17. 부록: 차별화 확인 체크리스트 (법적 안전성)

런칭 전 self-review. 하나라도 ❌ 이면 수정 후 재검토.

- [ ] URL 경로에 `/topmanager/`, `/accept/`, `/consult/`, `.html` 확장자 **없음**
- [ ] HTML / CSS / JS / 이미지 파일이 1000.sseye 와 동일한 파일명·경로 **없음**
- [ ] 색상 시스템이 1000.sseye 스크린샷과 비교 시 **명백히 다름**
- [ ] 대시보드 레이아웃 (파이차트 4-5개 row) 과 **다름** (KPI 카드 + 라인)
- [ ] 리드 수신 API 스펙 (`?ITEM=&DBname=&DBphone=&DBfild1~17=`) 지원 **안 함**
- [ ] 코드 내부 클래스·함수명이 디비카트/sseye 관련 키워드 **사용 안 함**
- [ ] 용어 중 `DBfild`, `Move_value`, `Code_num`, `Mode_value` 등 원문 표기 **없음**
- [ ] 디자인 레퍼런스는 Linear / Attio / Pipedrive 등 **서양 B2B SaaS** 계열

---

*문서 종료. 본 계획에 따라 W1 작업 착수.*

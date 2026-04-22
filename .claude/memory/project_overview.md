---
name: tmrrw_crm 프로젝트 개요
description: 한국 콜센터·리드 영업 조직용 멀티테넌트 SaaS CRM. 1000.sseye(디비카트 모회사) 벤치마크. 실행계획 ground truth는 docs/CRM_실행계획_v3.md (Django + Postgres 스택).
type: project
---

**현재 상태 (2026-04-22):** v3 실행계획 확정. W0 Django 학습 착수.

**핵심 문서 (항상 v3 먼저 참조):**
- `docs/CRM_실행계획_v3.md` — **Ground truth. Django + Postgres 버전. 모든 결정 포함.**
- `docs/CRM_실행계획_v2.md` — Flask + Firestore 버전 (역사, 참조 금지)
- `docs/CRM_MVP_기획보고서_v1.md` — v1 초안 (역사)

**판단 대원칙:**
1. 유지보수 편의성 (**1인이 영원히 유지보수** — 이게 이유)
2. 수익화
3. 법적 모방 리스크 회피 (1000.sseye 디자인·UI·URL·API 패턴 직접 복제 금지)

**확정된 것 (v3):**
- Backend: **Django 5.x + Python 3.12** (Flask 에서 변경)
- DB: **PostgreSQL 16 (Cloud SQL)** (Firestore 에서 변경)
- Frontend: HTMX + Alpine.js + Tailwind v4 + Pretendard
- 인증: Django 기본 + django-allauth
- 배포: GAE Standard (prod-only, staging 없음, 로컬 Docker Postgres + internal-test company + --no-promote 카나리)
- 결제: 포트원 (PortOne, 기본 PG 토스페이먼츠)
- 멀티테넌트: Company FK column-level 격리 (django-tenants 는 Phase 2 재검토)
- 역할(코드): owner / admin / intake / agent
- 역할(UI): 오너 / 관리자 / 접수 / 상담사
- URL: /app/admin/, /app/intake/, /app/agent/ (확장자 없음)
- 리드 상태 6단계: new / contacted / qualified / negotiating / won / lost
- API: POST /api/v1/leads (JSON + Bearer)
- MVP: 28 기능, 12주 (W0 학습 2026-04-22 ~ W12 2026-07-21 완성 → 08-19 정식 런칭)

**미확정 (user 결정 대기):**
- 최종 서비스 브랜드명
- 도메인 (tmrrwmkt 서브 아닌 별도 구매 방향)

**Why Django + Postgres:**
1. Django admin = 무료 고객지원·디버깅 GUI (1인에 결정적)
2. Django ORM = 복잡 집계 쿼리 한 줄 (Firestore 는 수십 줄 + 수동 카운터)
3. Django migrations = 스키마 변경 자동 추적·롤백 (Firestore 는 수동)
4. 보안 기본값 강함 (CSRF, SQL injection 자동 차단)
5. 패키지 생태계 두꺼움 (django-allauth, django-htmx, django-celery-beat 등)
6. Convention over Configuration = 6개월 후 내 코드 다시 볼 때 길 잃지 않음
7. Postgres = 비용 예측 가능, 복잡 쿼리 무제약, SQL 디버깅 쉬움

**tmrw_web 코드 재사용 전략:**
- `sms.py` (NCP SENS) → 그대로 복사 (프레임워크 무관)
- `hierarchy.py` → Django `manager = ForeignKey('self')` 재작성 (대폭 축소)
- `user_migration.py` → `@transaction.atomic` 블록 하나로 축소 (200줄 → 20줄)
- `alerts.py` → Django 모델로 재작성
- `legal.py` → Django model 필드로 재작성
- `extensions.py` → Django settings.py 로 대체

**How to apply:** 이 repo 관련 코딩·설계 결정 시 **항상 `docs/CRM_실행계획_v3.md` 먼저 참조**. v3 가 ground truth. v2 는 역사 참조용 (실행 계획 아님). 1000.sseye 의 HTML/CSS/JS/URL/용어 패턴 직접 복제 제안 금지. Django 관용구(ORM, forms, admin, migrations) 적극 활용.

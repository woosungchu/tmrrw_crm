# tmrrw_crm *(가칭)*

한국 콜센터·리드 영업 조직용 멀티테넌트 SaaS CRM.

> 서비스 브랜드명 미확정. 확정 전까지 repo 명은 중립적으로 유지.

## 현재 상태

**2026-04-22.** v3 실행계획 확정 (Django + Postgres 전면 재설계). W0 학습 착수.

## 문서

- [v1 기획보고서](docs/CRM_MVP_기획보고서_v1.md) — 초안 (역사)
- [v2 실행계획](docs/CRM_실행계획_v2.md) — Flask 버전 (역사)
- [v3 실행계획](docs/CRM_실행계획_v3.md) — **Ground truth. 모든 코딩·설계 결정은 여기 기준.**

## 핵심 결정 요약

| 항목 | 결정 |
|---|---|
| Backend | **Django 5.x + Python 3.12** |
| DB | **PostgreSQL 16 (Cloud SQL)** |
| Frontend | HTMX + Alpine.js + Tailwind v4 + Pretendard |
| 인증 | Django 기본 + django-allauth |
| 결제 | 포트원 (PortOne) — 기본 PG 토스페이먼츠 |
| 멀티테넌트 | Company FK column-level 격리 |
| 배포 | GAE Standard (prod-only, staging 없음) |
| 판단 기준 | 유지보수 편의성 1위 · 수익화 2위 · 법적 차별화 |
| MVP 일정 | 2026-04-22 학습 착수 → 12주 → 2026-07-21 완성 → 08-19 정식 런칭 |

## 왜 Django + Postgres?

- 1인 유지보수 극대화 — 프레임워크가 decision 을 많이 대신 내려줌
- Django admin 으로 고객지원·디버깅 무료 GUI 확보
- 복잡 쿼리(통계·리포트)에 Postgres 가 결정적
- migration 자동 추적

자세한 근거는 [v3 §1](docs/CRM_실행계획_v3.md) 참조.

## 경쟁사 분석

1000.sseye.com (디비카트 모회사 상상의눈) 전수 크롤 기반.
- 관리자 80 페이지 / 접수자 23 / 상담자 17

## 개발 착수

v3 §16 "즉시 착수 작업" 체크리스트 기준.

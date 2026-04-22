# tmrrw_crm *(가칭)*

한국 콜센터·리드 영업 조직용 멀티테넌트 SaaS CRM.

> 서비스 브랜드명 미확정 (현재 후보: "tmrw Relay"). 확정 전까지 repo 명은 중립적으로 유지.

## 현재 상태

**2026-04-22.** 기획·실행계획 확정. 개발 착수 전 단계.

## 문서

- [v1 기획보고서](docs/CRM_MVP_기획보고서_v1.md) — 초안 (의사결정 요청 포함, 역사 보존용)
- [v2 실행계획](docs/CRM_실행계획_v2.md) — **모든 결정 확정본. Ground truth.**

## 핵심 결정 요약

| 항목 | 결정 |
|---|---|
| 스택 | Flask + Jinja2 + HTMX + Alpine.js + Tailwind v4 + Firestore + GAE Standard |
| 배포 | GAE Standard (prod-only, staging 없음 — 로컬 emulator + internal-test company + `--no-promote` 카나리) |
| DB | Firestore (Postgres 전환 트리거: 월 1000만 read 또는 월 GCP 50만원) |
| 결제 | 포트원(PortOne) — 기본 PG 토스페이먼츠 |
| 역할(코드) | `admin` / `intake` / `agent` |
| 역할(UI) | 관리자 / 접수 / 상담사 |
| 리드 상태 | new · contacted · qualified · negotiating · won · lost (6단계) |
| 판단 기준 | 유지보수 편의성 1위 · 수익화 2위 · 법적 모방 리스크 회피 |
| MVP 일정 | 2026-05-01 ~ 2026-08-07 (10주) · 런칭 2026-08-08 |

## 경쟁사 분석

1000.sseye.com (디비카트 모회사 상상의눈) 전수 크롤 기반.
- 관리자 모드 80 페이지 / 접수자 23 / 상담자 17 (스크린샷 + HTML 확보)
- 분석 요약은 v2 §1

## 개발 착수 (W1, 2026-05-01~)

v2 §15 "즉시 착수 작업" 체크리스트 기준.

---
name: tmrrw_crm 프로젝트 개요
description: 한국 콜센터·리드 영업 조직용 멀티테넌트 SaaS CRM. 1000.sseye(디비카트 모회사) 벤치마크. 실행계획 ground truth는 docs/CRM_실행계획_v2.md
type: project
---

**현재 상태 (2026-04-22):** 기획·실행계획 확정. 레포 초기 파일 업로드 완료. 개발 착수 대기.

**핵심 문서:**
- `docs/CRM_실행계획_v2.md` — 모든 결정 확정본. 스택·역할·URL·데이터 모델·타임라인·수익화 전부 포함. **코딩·설계 결정 시 항상 여기 기준.**
- `docs/CRM_MVP_기획보고서_v1.md` — v1 초안 (역사)

**판단 대원칙 (우선순위):**
1. 유지보수 편의성 (1인 운영 가능성)
2. 수익화
3. 법적 모방 리스크 회피 (1000.sseye 디자인·UI·URL·API 패턴 직접 복제 금지)

**확정된 것:**
- 스택: Flask + Jinja2 + HTMX + Alpine.js + Tailwind v4 + Firestore + GAE Standard
- 배포: prod-only (staging 없음, 로컬 Firestore emulator + internal-test company + --no-promote 카나리)
- 결제: 포트원(PortOne, 기본 PG 토스페이먼츠)
- 역할(코드): admin / intake / agent
- 역할(UI): 관리자 / 접수 / 상담사
- URL: /app/admin/, /app/intake/, /app/agent/ (.html 확장자 없음, sseye의 /topmanager/ 등과 차별화)
- 리드 상태: new / contacted / qualified / negotiating / won / lost (6단계, sseye 5단계에서 결과를 won/lost 분리)
- 커스텀 필드: DBfild1~17 대신 business_type, loan_amount_need 등 의미 이름
- API: POST /api/v1/leads (JSON + Bearer), sseye 레거시 GET ?ITEM= 지원 안 함
- MVP: 28개 기능, 10주 (2026-05-01 ~ 2026-08-07), 런칭 2026-08-08

**미확정 (user 결정 대기):**
- 최종 서비스 브랜드명 — "tmrw Relay" 가안이지만 user 고민 중
- 도메인 — tmrrwmkt.com 서브도메인 말고 별도 구매 방향이지만 이름 미정

**Why:** 디비카트(상상의눈) NOTI 불안정으로 대표가 2천만 원 손실 경험. 기존 선택지(디비카트/1000.sseye) 2006년부터 기능·UI 정체. tmrw_web 기존 고객 업셀 경로 확보됨.

**How to apply:** 이 repo 관련 코딩·결정 요청 오면 항상 docs/CRM_실행계획_v2.md 먼저 참고. v2가 ground truth. 1000.sseye의 HTML/CSS/JS/이미지/URL/용어 패턴 직접 복제 제안 금지.

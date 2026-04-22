---
name: Tailwind CSS 재빌드 필수
description: tmrrw_crm도 tmrw_web과 동일한 pre-built CSS 방식. 새 유틸리티 클래스 추가 시 반드시 CLI 재빌드 후 배포.
type: feedback
---

Tailwind v4 pre-built CSS 방식 (tmrw_web과 동일). tree-shaking이 강해서 **빌드 시점 소스에 없던 클래스는 CSS에 포함되지 않음**. 새 유틸리티 클래스(w-4, rotate-180, space-y-4 등)를 템플릿·JS에 추가하면 반드시 CLI로 재빌드.

**재빌드 명령 (repo root 기준):**
```
./node_modules/.bin/tailwindcss -i tailwind/input.css -o app/static/css/tailwind.css
```

**Why:** tmrw_web 2026-04-21 사고 재현 방지. 커스텀 드롭다운 작업 시 SVG chevron 에 `w-4 h-4` 추가 후 재빌드 없이 배포 → CSS에 클래스 부재 → SVG가 브라우저 기본 크기(300×150)로 렌더 → UI 박살.

**How to apply:** Jinja 템플릿·정적 JS에서 Tailwind 클래스를 추가·변경했으면 `gcloud app deploy` 전에 항상 재빌드. 기존 클래스만 썼어도 습관적으로 재빌드 안전. 의심되면 `grep '\.새클래스명' app/static/css/tailwind.css` 로 포함 여부 확인.

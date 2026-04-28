# tmrrwcrm

한국 콜센터·리드 영업 조직을 위한 멀티테넌트 SaaS CRM.

**2026-04-28 베타 운영 시작.** 비공개 베타. 운영팀 승인 시 무료 사용.

🌐 https://tmrrwcrm.com

---

## 빠른 인덱스

| 항목 | 위치 |
|---|---|
| 운영 절차 (배포·승인·문제대응) | **이 문서 §운영 가이드** |
| 보안 미해결 항목 | [docs/SECURITY_TODO.md](docs/SECURITY_TODO.md) |
| 전체 설계 ground truth | [docs/CRM_실행계획_v3.md](docs/CRM_실행계획_v3.md) |
| Claude 메모리 | [CLAUDE.md](CLAUDE.md) |

---

## 스택 (확정)

| 레이어 | 결정 |
|---|---|
| Backend | Django 5.x + Python 3.12 |
| DB | PostgreSQL 16 (Cloud SQL) |
| Frontend | HTMX + Alpine.js + Tailwind v4 + Pretendard |
| 인증 | Django 기본 |
| 결제 | (보류) 포트원 — 베타는 운영팀 수동 승인 무료 |
| 멀티테넌트 | Company FK column-level 격리 |
| 인프라 | GAE Standard (asia-northeast3) + Cloud SQL |
| 시크릿 | GCP Secret Manager |
| 이메일 | Gmail SMTP (env 있을 때) / console (없을 때) |

---

## 운영 가이드

### 1. 베타 신청 승인 (일상)

새 가입자가 들어오면:
1. **승인자에게 메일** 자동 발송 (`is_approver=True` 인 모든 user)
2. https://tmrrwcrm.com/superadmin/approvals/ 접속
3. 대기 탭에서 [승인] 또는 [거부] (사유 입력 가능)
4. 승인/거부 시 **신청자에게 메일** 자동 발송

승인자 권한 부여:
```
Django admin 의 User 화면 → is_approver 체크 → 저장
```

### 2. 배포

```cmd
cd C:\aProject\tmrrw_crm
deploy.bat <버전이름>
```

이게 자동으로:
1. `npm run build:css` (Tailwind)
2. `python manage.py collectstatic --clear`
3. `gcloud app deploy --no-promote --version=<이름>`

배포 후 카나리 검증 → 트래픽 승격:
```cmd
gcloud app services set-traffic default --splits=<이름>=1 --quiet
```

### 3. DB 마이그레이션 (스키마 변경 시)

```cmd
:: 1. 로컬에서 모델 변경 + makemigrations
python manage.py makemigrations

:: 2. Cloud SQL Proxy 띄우기 (별도 터미널)
cloud-sql-proxy.exe tmrrwcrm:asia-northeast3:tmrrw-crm-db --port 5433

:: 3. prod DB 에 migrate
gcloud secrets versions access latest --secret=DB_PASSWORD > .pwtmp
set /p DB_PASSWORD=<.pwtmp
del .pwtmp
set DB_HOST=127.0.0.1
set DB_PORT=5433
set DB_NAME=crm
set DB_USER=crm_app
set DJANGO_SETTINGS_MODULE=config.settings.dev
python manage.py migrate

:: 4. 코드 deploy
deploy.bat <이름>
```

### 4. 시크릿 관리 (GCP Secret Manager)

생성:
```
echo -n "값" | gcloud secrets create <NAME> --replication-policy=automatic --data-file=- --project=tmrrwcrm
```

업데이트 (새 버전):
```
echo -n "새값" | gcloud secrets versions add <NAME> --data-file=- --project=tmrrwcrm
```

현재 시크릿:
- `DJANGO_SECRET_KEY`
- `DB_PASSWORD`
- `EMAIL_HOST_PASSWORD` (이메일 발송 활성화 시)

### 5. 이메일 발송 활성화

기본은 console backend (실 발송 X, GAE 로그에만 출력).

실 발송 활성화:
1. Gmail 앱 비밀번호 발급 (Google 계정 → 보안 → 2단계 인증 → 앱 비밀번호)
2. Secret Manager 에 박기:
   ```
   echo -n "<앱비밀번호>" | gcloud secrets create EMAIL_HOST_PASSWORD --replication-policy=automatic --data-file=- --project=tmrrwcrm
   ```
3. App Engine env 변수 설정 (`app.yaml`):
   ```yaml
   env_variables:
     EMAIL_HOST_USER: "운영이메일@gmail.com"
     EMAIL_FROM: "tmrrwcrm <운영이메일@gmail.com>"
   ```
4. 재배포

### 6. 문제 대응 빠른 명령어

```bash
# 최근 ERROR 로그
gcloud logging read "resource.type=gae_app AND severity>=ERROR" --freshness=1h --limit=20 --project=tmrrwcrm

# 라이브 로그 tail
gcloud app logs tail --service=default --project=tmrrwcrm

# 즉시 롤백 (이전 버전으로)
gcloud app versions list --service=default --project=tmrrwcrm
gcloud app services set-traffic default --splits=<이전버전>=1 --quiet --project=tmrrwcrm

# DB schema 점검
python manage.py check
python manage.py showmigrations
```

### 7. 비용 확인

매월 청구서: https://console.cloud.google.com/billing?project=tmrrwcrm

주요 비용:
- Cloud SQL db-f1-micro 24/7: 약 ₩15,000/월
- App Engine F1 자동 스케일: 트래픽 적으면 사실상 무료
- Secret Manager: ₩100 미만
- Cloud Logging: 50GB 무료

### 8. 주기 점검 (매주)

- [ ] 신청 승인 처리 (`/superadmin/approvals/`)
- [ ] 최근 7일 ERROR 로그 0건 확인
- [ ] Cloud SQL 백업 정상 (자동 — 18:00 UTC)
- [ ] [SECURITY_TODO.md](docs/SECURITY_TODO.md) 미해결 항목 1개 진행

---

## 디렉토리 구조 (요약)

```
apps/
  accounts/        — User, InviteToken, 인증
  companies/       — Company, Billing, Invoice, AssignmentConfig
  sources/         — 수신 채널, ApiKey
  leads/           — Lead, TimelineEntry, Blacklist
  communications/  — Template, Callback, SMS
  dashboard/       — KPI · 차트 집계
  public_api/      — 외부 리드 수신 API (/api/v1/)
  superadmin/      — 운영자 (베타 신청 승인)
  common/          — middleware, emails, base models

config/settings/
  base.py / dev.py / prod.py
  secrets_loader.py — Secret Manager wrapper

templates/
  base.html
  app/             — 로그인 후 화면
  public/          — 랜딩, 가입
  emails/          — 메일 템플릿
  superadmin/      — 승인 페이지
```

---

## 라이선스 / 컨택

internal — 운영자: 주우성 (woosungchu@gmail.com)

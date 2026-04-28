@echo off
REM ============================================================
REM tmrrw_crm 카나리 배포 스크립트
REM
REM 순서: Tailwind 빌드 → collectstatic → gcloud app deploy --no-promote
REM 배포 후 카나리 URL 검증하고 직접 트래픽 승격.
REM
REM 사용법:
REM   deploy.bat <버전이름>
REM 예:
REM   deploy.bat call-fix
REM   deploy.bat v-20260428a
REM ============================================================

setlocal

if "%~1"=="" (
  echo Usage: deploy.bat ^<version-name^>
  echo.
  echo Examples:
  echo   deploy.bat call-fix
  echo   deploy.bat v-20260428a
  echo.
  echo 버전 이름은 영문/숫자/하이픈만. 길이 ^<= 63.
  exit /b 1
)
set VERSION=%~1

cd /d "%~dp0"

echo.
echo ============================================================
echo [1/3] Tailwind CSS 빌드
echo ============================================================
call npm run build:css
if errorlevel 1 goto error

echo.
echo ============================================================
echo [2/3] Django collectstatic (--clear)
echo ============================================================
call .venv\Scripts\activate.bat
if errorlevel 1 goto error
set DJANGO_SECRET_KEY=deploy-tmp-not-used
set DJANGO_SETTINGS_MODULE=config.settings.dev
set DB_NAME=cb
set DB_USER=cb
set DB_PASSWORD=cb
set DB_HOST=127.0.0.1
python manage.py collectstatic --noinput --clear
if errorlevel 1 goto error

echo.
echo ============================================================
echo [3/3] gcloud app deploy --no-promote --version=%VERSION%
echo ============================================================
gcloud app deploy --no-promote --version=%VERSION% --quiet
if errorlevel 1 goto error

echo.
echo ============================================================
echo 배포 완료. 카나리 URL:
echo   https://%VERSION%-dot-tmrrwcrm.du.r.appspot.com
echo.
echo 검증 후 트래픽 100%% 승격하려면:
echo   gcloud app services set-traffic default --splits=%VERSION%=1 --quiet
echo ============================================================
goto end

:error
echo.
echo X 실패. 위 로그 확인.
exit /b 1

:end
endlocal

@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0\.."

echo ========================================
echo  PyArmor 난독화 + PyInstaller 빌드
echo ========================================

REM venv 확인
if not exist ".venv\Scripts\activate.bat" (
    echo [1/5] venv 생성 중...
    python -m venv .venv
)
call .venv\Scripts\activate.bat

echo [2/5] 패키지 설치 중...
pip install -q -r requirements.txt
pip install -q pyinstaller pyarmor

REM PyArmor 라이선스 확인 (Basic은 무료)
pyarmor --version 2>nul
if errorlevel 1 (
    echo [오류] PyArmor가 설치되지 않았습니다. pip install pyarmor
    pause
    exit /b 1
)

echo [3/6] 난독화 대상 모듈 준비...
REM 핵심 모듈 우선 난독화 (auth, config - API키/라이선스 관련)
set OBF_MODULES=gui.py main.py auth.py config.py blog_poster.py cafe_poster.py cafe_extractor.py cafe_autojoin.py coupang_api.py gemini_api.py image_downloader.py supabase_client.py url_shortener.py

echo [4/6] PyArmor PyInstaller 옵션 설정 (콘솔숨김)...
pyarmor cfg pack:pyi_options = "--noconfirm --windowed"

echo [5/6] PyArmor 난독화 + Onefile 패킹 중...
REM Trial: --mix-str 제외 (Can't obfuscate big script and mix str)
pyarmor gen --pack onefile -e gui.py ^
    gui.py main.py auth.py config.py blog_poster.py cafe_poster.py cafe_extractor.py cafe_autojoin.py coupang_api.py gemini_api.py image_downloader.py supabase_client.py url_shortener.py

if errorlevel 1 (
    echo.
    echo [대안] PyArmor 없이 일반 빌드 시: build_onefile.bat 실행
    echo [참고] PyArmor Basic(무료)은 일부 제한 있음. Pro는 상용 라이선스 필요.
    pause
    exit /b 1
)

echo [6/6] 결과 확인...
if exist "dist\gui.exe" (
    move /y "dist\gui.exe" "dist\CoupangBot_obfuscated.exe"
    echo.
    echo ========================================
    echo  완료: dist\CoupangBot_obfuscated.exe
    echo ========================================
    start "" "dist\CoupangBot_obfuscated.exe"
) else (
    echo [알림] 출력: dist\gui.exe 또는 .pyarmor\pack\dist 확인
    dir /s /b dist\*.exe 2>nul
)

pause

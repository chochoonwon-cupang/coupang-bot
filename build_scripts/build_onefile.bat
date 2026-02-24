@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0\.."

echo ========================================
echo  PyInstaller Onefile 빌드
echo ========================================

REM venv 확인
if not exist ".venv\Scripts\activate.bat" (
    echo [1/4] venv 생성 중...
    python -m venv .venv
)
call .venv\Scripts\activate.bat

echo [2/4] 패키지 설치 중...
pip install -q -r requirements.txt
pip install -q -r build_scripts\requirements-build.txt

echo [3/5] PyInstaller Onefile 빌드 중...
pyinstaller --clean --noconfirm coupang_bot.spec

if errorlevel 1 (
    echo [오류] 빌드 실패
    exit /b 1
)

echo [4/5] PyInstaller 콘솔 버전 빌드 중 (원인 확인용)...
pyinstaller --clean --noconfirm coupang_bot_console.spec

echo [5/5] 실행 테스트...
start "" "dist\CoupangBot.exe"
timeout /t 3 >nul
echo.
echo ========================================
echo  완료: dist\CoupangBot.exe (GUI)
echo        dist\CoupangBot_console.exe (콘솔/디버그)
echo ========================================
pause

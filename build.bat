@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo   쿠팡 파트너스 봇 - 실행파일 빌드
echo ========================================
echo [안내] 난독화 포함 빌드는 build_obfuscated.bat 실행
echo.

REM 가상환경 사용 (있으면)
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    echo [가상환경] .venv 활성화
) else (
    echo [안내] .venv 없음 - 시스템 Python 사용
)

echo.
echo [1/4] 의존성 설치...
pip install -q -r requirements.txt
pip install -q pyinstaller

echo.
echo [2/4] build, dist 폴더 정리...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo.
echo [3/4] PyInstaller로 exe 빌드 중... (1~2분 소요)
pyinstaller --clean --noconfirm coupang_bot.spec

echo.
if exist "dist\CoupangBot.exe" (
    echo ========================================
    echo   빌드 완료!
    echo   실행파일: dist\CoupangBot.exe
    echo ========================================
    explorer dist
) else (
    echo [오류] 빌드 실패. 위 로그를 확인하세요.
)
echo.
pause

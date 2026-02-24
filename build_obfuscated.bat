@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo ========================================
echo   쿠팡 파트너스 봇 - 실행파일 빌드 (난독화)
echo ========================================
echo.

REM 가상환경 사용 (있으면)
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    echo [가상환경] .venv 활성화
) else (
    echo [안내] .venv 없음 - 시스템 Python 사용
)

echo.
echo [1/5] 의존성 설치...
pip install -q -r requirements.txt
pip install -q pyinstaller pyarmor

echo.
echo [2/5] PyArmor 확인...
pyarmor --version 2>nul
if errorlevel 1 (
    echo [경고] PyArmor 미설치 - 난독화 없이 빌드합니다.
    goto :normal_build
)

echo.
echo [3/5] build, dist 폴더 정리...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist .pyarmor rmdir /s /q .pyarmor 2>nul

echo.
echo [4/5] PyArmor 난독화 + PyInstaller 패킹 중... (2~3분 소요)
REM 핵심 모듈 난독화 (인코딩 이슈 가능 모듈은 제외)
pyarmor cfg pack:pyi_options = "--noconfirm --windowed"
pyarmor gen --pack onefile -e gui.py ^
    gui.py main.py auth.py config.py blog_poster.py cafe_poster.py cafe_extractor.py cafe_autojoin.py coupang_api.py gemini_api.py image_downloader.py supabase_client.py url_shortener.py

if errorlevel 1 (
    echo.
    echo [경고] PyArmor 난독화 실패 - 일반 빌드로 진행합니다.
    goto :normal_build
)

REM PyArmor 출력 위치 확인
if exist ".pyarmor\pack\dist\gui.exe" (
    if not exist dist mkdir dist
    copy /y ".pyarmor\pack\dist\gui.exe" "dist\CoupangBot.exe"
    goto :done
)
if exist ".pyarmor\pack\dist\CoupangBot.exe" (
    if not exist dist mkdir dist
    copy /y ".pyarmor\pack\dist\CoupangBot.exe" "dist\CoupangBot.exe"
    goto :done
)
if exist "dist\gui.exe" (
    if not exist dist mkdir dist
    move /y "dist\gui.exe" "dist\CoupangBot.exe"
    goto :done
)

echo [알림] PyArmor 출력을 찾을 수 없음 - 일반 빌드로 진행합니다.
goto :normal_build

:normal_build
echo.
echo [대안] PyInstaller 일반 빌드 중...
pyinstaller --clean --noconfirm coupang_bot.spec
if not exist "dist\CoupangBot.exe" (
    echo [오류] 빌드 실패.
    pause
    exit /b 1
)
goto :done

:done
echo.
echo [5/5] 결과 확인...
if exist "dist\CoupangBot.exe" (
    echo ========================================
    echo   빌드 완료!
    echo   실행파일: dist\CoupangBot.exe
    echo ========================================
    explorer dist
) else (
    echo [오류] dist\CoupangBot.exe를 찾을 수 없습니다.
)
echo.
pause

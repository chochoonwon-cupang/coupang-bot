@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0\.."

echo ========================================
echo  python-minifier 난독화 + PyInstaller 빌드
echo ========================================

if not exist ".venv\Scripts\activate.bat" (
    python -m venv .venv
)
call .venv\Scripts\activate.bat

echo [1/5] 패키지 설치...
pip install -q -r requirements.txt
pip install -q pyinstaller python-minifier

echo [2/5] build, dist, dist_min 정리...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist dist_min rmdir /s /q dist_min
mkdir dist_min

echo [3/5] python-minifier로 난독화 (주석제거, 변수명 단축)...
set MODULES=gui.py main.py auth.py config.py blog_poster.py cafe_poster.py cafe_extractor.py cafe_autojoin.py coupang_api.py gemini_api.py image_downloader.py supabase_client.py url_shortener.py
for %%f in (%MODULES%) do (
    pyminify --rename-locals --rename-globals -o dist_min\%%f %%f 2>nul
    if errorlevel 1 (
        echo [복사] %%f - minify 실패, 원본 사용
        copy /y %%f dist_min\%%f >nul
    )
)

echo [4/5] PyInstaller 빌드 (난독화된 gui.py + 경로)...
pyinstaller --clean --noconfirm --onefile --windowed ^
    --name CoupangBot_obfuscated ^
    --paths=dist_min ^
    --hidden-import=PIL --hidden-import=PIL.Image ^
    --hidden-import=supabase --hidden-import=selenium ^
    --hidden-import=webdriver_manager --hidden-import=pyperclip ^
    --hidden-import=blog_poster --hidden-import=cafe_poster ^
    --collect-all supabase --collect-all postgrest --collect-all realtime --collect-all storage3 --collect-all httpx ^
    dist_min\gui.py

if errorlevel 1 (
    echo [대안] 기존 spec으로 빌드 후 이름 변경...
    pyinstaller --clean --noconfirm coupang_bot.spec
    if exist "dist\CoupangBot.exe" (
        move /y "dist\CoupangBot.exe" "dist\CoupangBot_obfuscated.exe"
    )
)

echo [5/5] 정리...
if exist dist_min rmdir /s /q dist_min

if exist "dist\CoupangBot_obfuscated.exe" (
    echo.
    echo ========================================
    echo   완료: dist\CoupangBot_obfuscated.exe
    echo ========================================
) else if exist "dist\CoupangBot.exe" (
    echo.
    echo ========================================
    echo   완료: dist\CoupangBot.exe
    echo ========================================
)
pause

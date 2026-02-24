@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0\.."

echo ========================================
echo  Supabase 포함 PyInstaller 빌드
echo ========================================

if not exist ".venv\Scripts\activate.bat" (
    python -m venv .venv
)
call .venv\Scripts\activate.bat

pip install -q -r requirements.txt
pip install -q supabase pyinstaller

echo [1/3] build, dist 정리...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo [2/3] GUI 버전 빌드 (--windowed)...
pyinstaller --clean --noconfirm --onefile --windowed ^
  --collect-all supabase ^
  --collect-all postgrest ^
  --collect-all realtime ^
  --collect-all storage3 ^
  --collect-all httpx ^
  --collect-all supabase_auth ^
  --name CoupangBot gui.py

echo [3/3] 콘솔 버전 빌드 (디버그용)...
pyinstaller --clean --noconfirm --onefile ^
  --collect-all supabase ^
  --collect-all postgrest ^
  --collect-all realtime ^
  --collect-all storage3 ^
  --collect-all httpx ^
  --collect-all supabase_auth ^
  --name CoupangBot_console gui.py

echo.
echo ========================================
echo  완료: dist\CoupangBot.exe
echo        dist\CoupangBot_console.exe
echo  VPS로 복사 후 기존 EXE 교체
echo ========================================
pause

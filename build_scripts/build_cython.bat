@echo off
chcp 65001 >nul
cd /d "%~dp0\.."

echo ========================================
echo  Cython 빌드 (auth_core)
echo ========================================

if not exist ".venv\Scripts\activate.bat" (
    python -m venv .venv
)
call .venv\Scripts\activate.bat

pip install -q cython

echo auth_core.pyx 컴파일 중...
python build_scripts\setup_cython.py build_ext --inplace

if exist "auth_core*.pyd" (
    echo 완료: auth_core.pyd 생성됨
) else if exist "auth_core*.so" (
    echo 완료: auth_core.so 생성됨
) else (
    echo [오류] 빌드 실패
    exit /b 1
)

REM 테스트
python -c "from auth_core import _hash_password, _verify_password; h=_hash_password('test'); print('OK' if _verify_password('test',h) else 'FAIL')"
echo.
pause

# 쿠팡 파트너스 봇 - 빌드 가이드

## 필수 정보

| 항목 | 값 |
|------|-----|
| **파이썬 버전** | 3.10 / 3.11 권장 |
| **엔트리 파일** | `gui.py` |
| **GUI** | Tkinter |
| **외부 리소스** | `images/`, `output/`, `cafe_settings.json`, `.api_keys.json`, `keywords.txt`, `cafe_list.txt`, `app_icon.ico` |
| **배포 형태** | onefile + onedir 둘 다 지원 |

---

## 1. 빌드 파이프라인

### 1-1. Onefile (단일 exe)

```batch
build_scripts\build_onefile.bat
```

- 결과: `dist\CoupangBot.exe`
- 실행 시 임시 폴더에 압축 해제 후 실행
- 설정 파일(`cafe_settings.json`, `.api_keys.json`)은 **exe와 같은 폴더**에 저장됨

### 1-2. Onedir (폴더 형태)

```batch
build_scripts\build_onedir.bat
```

- 결과: `dist\CoupangBot\` 폴더
- `CoupangBot.exe` + 의존성 dll/폴더
- 배포 시 전체 폴더를 압축해서 배포

### 1-3. 난독화 + 빌드 (PyArmor)

```batch
build_scripts\obfuscate_and_build.bat
```

- PyArmor로 소스 난독화 후 PyInstaller 패킹
- 결과: `dist\CoupangBot_obfuscated.exe`
- **주의**: PyArmor Basic(무료)은 제한 있음. `--enable-jit` 실패 시 자동으로 제외 후 재시도

### 1-4. Cython 빌드 (선택)

```batch
build_scripts\build_cython.bat
```

- `auth_core.pyx` → `auth_core.pyd` 컴파일
- 비밀번호 해싱/검증 로직을 C 확장으로 분리 → 리버스 어려움
- 빌드 후 `build_onefile.bat` 실행 시 `.pyd` 포함됨

---

## 2. 수동 빌드 (PowerShell/CMD)

```batch
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install pyinstaller

REM Onefile
pyinstaller --clean coupang_bot.spec

REM Onedir
pyinstaller --clean coupang_bot_onedir.spec
```

---

## 3. 트러블슈팅

### 3-1. `ModuleNotFoundError` / `ImportError`

- **원인**: 동적 import 누락
- **해결**: `coupang_bot.spec`의 `hiddenimports`에 모듈 추가 후 재빌드

### 3-2. `FileNotFoundError` (cafe_settings.json 등)

- **원인**: exe 실행 시 작업 디렉터리 불일치
- **해결**: `gui.py`에 PyInstaller frozen 대응 코드 적용됨 (`BASE_DIR = sys.executable` 기준)

### 3-3. Chrome/WebDriver 오류

- **원인**: `webdriver-manager`가 Chrome 드라이버를 사용자 폴더에 다운로드
- **해결**: exe와 동일 폴더 또는 `%USERPROFILE%\.wdm` 사용. 별도 설치 불필요

### 3-4. PyArmor `--enable-jit` 실패

- **원인**: PyArmor Basic 라이선스 제한
- **해결**: `obfuscate_and_build.bat`이 자동으로 `--enable-jit` 제외 후 재시도

### 3-5. Cython 빌드 실패 (Microsoft C++ Build Tools 없음)

- **원인**: Windows에서 C 확장 빌드 시 Visual C++ 필요
- **해결**: [Build Tools for Visual Studio](https://visualstudio.microsoft.com/visual-cpp-build-tools/) 설치
- **대안**: Cython 빌드 생략 → `auth.py`가 로컬 구현 사용 (기능 동일)

### 3-6. `strip=True` 오류 (UPX 관련)

- **원인**: UPX 미설치 또는 호환성 문제
- **해결**: `coupang_bot.spec`에서 `upx=False`로 변경

---

## 4. 보호 강화 옵션 요약

| 단계 | 도구 | 적용 |
|------|------|------|
| 1차 | PyArmor | 소스 난독화 (`obfuscate_and_build.bat`) |
| 2차 | PyInstaller spec | `debug=False`, `strip=True`, `console=False` |
| 3차 | Cython | `auth_core` (비밀번호 해싱) C 확장화 |

---

## 5. 배포 시 포함/제외

**포함**: exe, 필요한 dll, `pyarmor_runtime` (난독화 시)

**제외** (사용자별 생성):
- `.api_keys.json` - API 키 (사용자 입력)
- `cafe_settings.json` - 카페 설정 (실행 시 생성)
- `.auth_session.json` - 로그인 세션
- `keywords.txt`, `cafe_list.txt` - 사용자 데이터

**선택 포함**:
- `app_icon.ico` - 앱 아이콘 (있으면 spec에 포함)
- **exe 버전정보**: `pyi-grab_version python.exe version_info.txt`로 생성 후 spec에 `version='version_info.txt'` 추가

# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec - Onefile (단일 exe)
# 실행: pyinstaller coupang_bot.spec

import sys
import os
from PyInstaller.utils.hooks import collect_all

block_cipher = None

# Supabase 및 의존성 전체 수집 (VPS import 실패 방지)
def _safe_collect(pkg):
    try:
        return collect_all(pkg)
    except Exception:
        return [], [], []

_supabase_datas, _supabase_binaries, _supabase_hidden = collect_all('supabase')
_gotrue_datas, _gotrue_binaries, _gotrue_hidden = _safe_collect('gotrue')
_postgrest_datas, _postgrest_binaries, _postgrest_hidden = _safe_collect('postgrest')
_realtime_datas, _realtime_binaries, _realtime_hidden = _safe_collect('realtime')
_storage3_datas, _storage3_binaries, _storage3_hidden = _safe_collect('storage3')
_httpx_datas, _httpx_binaries, _httpx_hidden = _safe_collect('httpx')

# 동적 import 모듈 (hiddenimports)
hidden_imports = [
    'PIL',
    'PIL.Image',
    'PIL.ImageDraw',
    'PIL.ImageTk',
    'supabase',
    'supabase.client',
    'auth',
    'config',
    'blog_poster',
    'cafe_poster',
    'cafe_extractor',
    'cafe_autojoin',
    'main',
    'coupang_api',
    'gemini_api',
    'image_downloader',
    'supabase_client',
    'url_shortener',
    'auth_core',      # Cython 컴파일된 auth 핵심 (있으면)
    'selenium',
    'selenium.webdriver',
    'selenium.webdriver.chrome.service',
    'selenium.webdriver.chrome.options',
    'selenium.webdriver.common.by',
    'selenium.webdriver.common.keys',
    'selenium.webdriver.common.action_chains',
    'selenium.webdriver.support.ui',
    'selenium.webdriver.support.expected_conditions',
    'webdriver_manager',
    'webdriver_manager.chrome',
    'pyperclip',
    'requests',
    'json',
    'httpcore',
    'certifi',
    'anyio',
    'sniffio',
    'supabase.lib.client_options',
    'supabase.lib.client',
] + _supabase_hidden + _gotrue_hidden + _postgrest_hidden + _realtime_hidden + _storage3_hidden + _httpx_hidden

# 데이터 파일 (Supabase 등 패키지 데이터 포함)
datas = _supabase_datas + _gotrue_datas + _postgrest_datas + _realtime_datas + _storage3_datas + _httpx_datas

# 아이콘 (있으면 포함)
icon_path = 'app_icon.ico'
if os.path.exists(icon_path):
    datas.append((icon_path, '.'))

# Supabase 등 바이너리
binaries = _supabase_binaries + _gotrue_binaries + _postgrest_binaries + _realtime_binaries + _storage3_binaries + _httpx_binaries

a = Analysis(
    ['gui.py'],  # 엔트리: GUI 앱
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['pyi_rth_cwd.py'],
    excludes=[
        'matplotlib', 'numpy', 'pandas', 'scipy', 'tkinter.test',
        'test', 'unittest', 'pydoc', 'doctest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='CoupangBot',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,           # 심볼 제거 (리버스 어려움)
    upx=True,             # UPX 압축 (있으면)
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,        # 콘솔 창 숨김 (GUI 앱)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='app_icon.ico' if os.path.exists('app_icon.ico') else None,
    version=None,  # 버전정보: pyi-grab_version으로 생성 후 version='version_info.txt' 지정
)

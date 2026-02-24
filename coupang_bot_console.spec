# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec - Onefile + 콘솔 (원인 확인용)
# 실행: pyinstaller coupang_bot_console.spec
# 출력: dist/CoupangBot_console.exe

import sys
import os
from PyInstaller.utils.hooks import collect_all

block_cipher = None

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

hidden_imports = [
    'PIL', 'PIL.Image', 'PIL.ImageDraw', 'PIL.ImageTk',
    'supabase', 'supabase.client', 'auth', 'config',
    'cafe_poster', 'cafe_extractor', 'cafe_autojoin', 'main',
    'coupang_api', 'gemini_api', 'image_downloader', 'supabase_client', 'url_shortener',
    'auth_core',
    'selenium', 'selenium.webdriver', 'selenium.webdriver.chrome.service',
    'selenium.webdriver.chrome.options', 'selenium.webdriver.common.by',
    'selenium.webdriver.common.keys', 'selenium.webdriver.common.action_chains',
    'selenium.webdriver.support.ui', 'selenium.webdriver.support.expected_conditions',
    'webdriver_manager', 'webdriver_manager.chrome', 'pyperclip', 'requests', 'json',
] + _supabase_hidden + _gotrue_hidden + _postgrest_hidden + _realtime_hidden + _storage3_hidden + _httpx_hidden

datas = _supabase_datas + _gotrue_datas + _postgrest_datas + _realtime_datas + _storage3_datas + _httpx_datas
if os.path.exists('app_icon.ico'):
    datas.append(('app_icon.ico', '.'))

binaries = _supabase_binaries + _gotrue_binaries + _postgrest_binaries + _realtime_binaries + _storage3_binaries + _httpx_binaries

a = Analysis(
    ['gui.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy', 'pandas', 'scipy', 'tkinter.test', 'test', 'unittest', 'pydoc', 'doctest'],
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
    name='CoupangBot_console',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,   # 콘솔 표시 (에러/로그 확인용)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='app_icon.ico' if os.path.exists('app_icon.ico') else None,
    version=None,
)

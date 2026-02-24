# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec - Onedir (폴더 형태)
# 실행: pyinstaller coupang_bot_onedir.spec

import sys
import os

block_cipher = None

hidden_imports = [
    'PIL', 'PIL.Image', 'PIL.ImageDraw', 'PIL.ImageTk',
    'supabase', 'supabase.client',
    'auth', 'config', 'cafe_poster', 'cafe_extractor', 'cafe_autojoin',
    'main', 'coupang_api', 'gemini_api', 'image_downloader',
    'supabase_client', 'url_shortener',
    'auth_core',
    'selenium', 'selenium.webdriver', 'selenium.webdriver.chrome.service',
    'selenium.webdriver.chrome.options', 'selenium.webdriver.common.by',
    'selenium.webdriver.common.keys', 'selenium.webdriver.common.action_chains',
    'selenium.webdriver.support.ui', 'selenium.webdriver.support.expected_conditions',
    'webdriver_manager', 'webdriver_manager.chrome',
    'pyperclip', 'requests', 'json',
]

datas = []
if os.path.exists('app_icon.ico'):
    datas.append(('app_icon.ico', '.'))

a = Analysis(
    ['gui.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy', 'pandas', 'scipy', 'tkinter.test', 'test', 'unittest'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='CoupangBot',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='app_icon.ico' if os.path.exists('app_icon.ico') else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=True,
    upx=True,
    upx_exclude=[],
    name='CoupangBot',
)

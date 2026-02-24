# -*- coding: utf-8 -*-
# PyInstaller runtime hook: exe 실행 시 작업 디렉터리를 exe 위치로 설정
import sys
import os
if getattr(sys, "frozen", False):
    exe_dir = os.path.dirname(sys.executable)
    if exe_dir and os.path.isdir(exe_dir):
        os.chdir(exe_dir)

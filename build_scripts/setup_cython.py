"""
Cython 빌드 스크립트 - auth_core.pyx → auth_core.pyd (Windows)
실행: python build_scripts/setup_cython.py build_ext --inplace
(프로젝트 루트에서 실행)
"""
from setuptools import setup, Extension
from Cython.Build import cythonize
import sys
import os

# 프로젝트 루트 기준
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(root)

ext = Extension(
    "auth_core",
    sources=[os.path.join(root, "auth_core.pyx")],
    extra_compile_args=["/O2"] if sys.platform == "win32" else ["-O3"],
)
setup(ext_modules=cythonize(ext, compiler_directives={"language_level": "3"}))

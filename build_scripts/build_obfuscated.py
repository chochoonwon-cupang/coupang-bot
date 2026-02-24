# -*- coding: utf-8 -*-
"""python-minifier 난독화 후 PyInstaller 빌드"""
import os
import sys
import shutil
import subprocess

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(BASE)

MODULES = [
    "gui.py", "main.py", "auth.py", "config.py", "blog_poster.py",
    "cafe_poster.py", "cafe_extractor.py", "cafe_autojoin.py",
    "coupang_api.py", "gemini_api.py", "image_downloader.py",
    "supabase_client.py", "url_shortener.py",
]

def main():
    print("=" * 50)
    print("  python-minifier 난독화 + PyInstaller 빌드")
    print("=" * 50)

    # 1. dist_min 준비
    dist_min = os.path.join(BASE, "dist_min")
    if os.path.exists(dist_min):
        shutil.rmtree(dist_min)
    os.makedirs(dist_min)

    # 2. python-minifier로 난독화
    print("\n[1/3] python-minifier 난독화 중...")
    try:
        import python_minifier
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "python-minifier"], check=True)
        import python_minifier

    for mod in MODULES:
        src = os.path.join(BASE, mod)
        dst = os.path.join(dist_min, mod)
        if not os.path.exists(src):
            print(f"  [건너뜀] {mod} 없음")
            continue
        try:
            with open(src, "r", encoding="utf-8") as f:
                code = f.read()
            minified = python_minifier.minify(
                code,
                rename_locals=True,
                rename_globals=False,
            )
            with open(dst, "w", encoding="utf-8") as f:
                f.write(minified)
            print(f"  [OK] {mod}")
        except Exception as e:
            print(f"  [복사] {mod} - minify 실패: {e}")
            shutil.copy2(src, dst)

    # 3. PyInstaller 빌드 (dist_min을 pathex에 추가)
    print("\n[2/3] PyInstaller 빌드 중...")
    spec_path = os.path.join(BASE, "coupang_bot.spec")
    with open(spec_path, "r", encoding="utf-8") as f:
        spec_content = f.read()

    # spec 수정: gui.py -> dist_min/gui.py, pathex에 dist_min 추가
    gui_path = "dist_min/gui.py"
    dist_min_norm = "dist_min"
    spec_obf = spec_content.replace(
        "['gui.py'],  # 엔트리: GUI 앱\n    pathex=[]",
        f"['{gui_path}'],  # 엔트리 (난독화)\n    pathex=['{dist_min_norm}', '.']",
    ).replace(
        "name='CoupangBot'",
        "name='CoupangBot_obfuscated'",
    )
    spec_obf_path = os.path.join(BASE, "coupang_bot_obf.spec")
    with open(spec_obf_path, "w", encoding="utf-8") as f:
        f.write(spec_obf)

    r = subprocess.run(
        [sys.executable, "-m", "PyInstaller", "--clean", "--noconfirm", spec_obf_path],
        cwd=BASE,
    )
    try:
        os.remove(spec_obf_path)
    except Exception:
        pass

    # 4. 정리
    print("\n[3/3] 정리 중...")
    if os.path.exists(dist_min):
        shutil.rmtree(dist_min)

    if r.returncode == 0 and os.path.exists(os.path.join(BASE, "dist", "CoupangBot_obfuscated.exe")):
        print("\n" + "=" * 50)
        print("  완료: dist\\CoupangBot_obfuscated.exe")
        print("=" * 50)
    else:
        print("\n[오류] 빌드 실패")
        sys.exit(1)

if __name__ == "__main__":
    main()

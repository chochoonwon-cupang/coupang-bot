# ============================================================
# 이미지 다운로더 모듈 (Pillow 기반 강화 버전)
# ============================================================
# 1) EXIF 메타데이터 완전 제거
# 2) 미세 리사이즈 (90~110%) + 랜덤 크롭 (1~2px)
# 3) 랜덤 파일명 (상품명_랜덤문자열.jpg) + 상품-파일 매핑
# 4) JPEG Quality 85~95 랜덤 저장
# ============================================================

import io
import os
import random
import re
import string
import requests
from config import IMAGE_SAVE_DIR

try:
    from PIL import Image
except ImportError:
    raise ImportError(
        "Pillow 패키지가 필요합니다. 설치: pip install Pillow"
    )


# ─────────────────────────────────────────────────────────────
# 유틸리티
# ─────────────────────────────────────────────────────────────
def _random_suffix(length=8):
    """랜덤 영숫자 문자열 생성"""
    chars = string.ascii_lowercase + string.digits
    return "".join(random.choices(chars, k=length))


def sanitize_filename(name, max_length=40):
    """파일명에 사용할 수 없는 문자를 제거하고 길이를 제한합니다."""
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    name = name.replace(" ", "_")
    return name[:max_length]


# ─────────────────────────────────────────────────────────────
# 이미지 후처리 (EXIF 제거 + 리사이즈 + 크롭 + 저장)
# ─────────────────────────────────────────────────────────────
def _strip_exif_and_process(raw_bytes, save_path):
    """
    원본 이미지 바이트를 받아 아래 처리를 수행한 뒤 JPEG로 저장한다.

    1. EXIF/메타데이터 완전 제거 (새 Image 객체로 복사)
    2. 90%~110% 사이 랜덤 비율로 미세 리사이즈
    3. 상하좌우 1~2px 랜덤 크롭
    4. JPEG Quality 85~95 랜덤 저장

    Args:
        raw_bytes: 다운로드한 이미지의 원본 바이트
        save_path: 저장할 파일 경로 (.jpg)
    """
    img = Image.open(io.BytesIO(raw_bytes))

    # ── 1) EXIF 메타데이터 완전 제거 ──
    # 새 이미지 객체로 픽셀 데이터만 복사 → EXIF/ICC/XMP 등 모든 메타 삭제
    clean_img = Image.new(img.mode, img.size)
    clean_img.putdata(list(img.getdata()))

    # RGBA/P 등 알파 채널 → RGB 변환 (JPEG 저장 위해)
    if clean_img.mode not in ("RGB", "L"):
        clean_img = clean_img.convert("RGB")

    # ── 2) 미세 리사이즈 (90%~110%) ──
    w, h = clean_img.size
    scale = random.uniform(0.90, 1.10)
    new_w = max(1, int(w * scale))
    new_h = max(1, int(h * scale))
    clean_img = clean_img.resize((new_w, new_h), Image.LANCZOS)

    # ── 3) 랜덤 크롭 (상하좌우 1~2px 잘라내기) ──
    cw, ch = clean_img.size
    crop_left = random.randint(1, 2) if cw > 10 else 0
    crop_top = random.randint(1, 2) if ch > 10 else 0
    crop_right = random.randint(1, 2) if cw > 10 else 0
    crop_bottom = random.randint(1, 2) if ch > 10 else 0

    box = (crop_left, crop_top, cw - crop_right, ch - crop_bottom)
    if box[2] > box[0] and box[3] > box[1]:
        clean_img = clean_img.crop(box)

    # ── 4) JPEG Quality 85~95 랜덤 저장 ──
    quality = random.randint(85, 95)
    clean_img.save(save_path, format="JPEG", quality=quality, optimize=True)

    final_w, final_h = clean_img.size
    print(f"  [후처리] {w}×{h} → {final_w}×{final_h} "
          f"(scale={scale:.2f}, Q={quality})")


# ─────────────────────────────────────────────────────────────
# 단일 이미지 다운로드 + 후처리
# ─────────────────────────────────────────────────────────────
def download_image(image_url, product_name, save_dir=None):
    """
    이미지 URL에서 이미지를 다운로드하고 Pillow로 후처리하여 저장합니다.

    처리 내용:
      - EXIF 메타데이터 완전 제거
      - 90~110% 랜덤 리사이즈
      - 1~2px 랜덤 크롭
      - JPEG Q85~95 랜덤 저장
      - 파일명: {상품명}_{랜덤8자}.jpg

    Args:
        image_url: 이미지 URL
        product_name: 상품명 (파일명 및 매핑 키로 사용)
        save_dir: 저장 폴더

    Returns:
        저장된 이미지의 로컬 파일 경로, 실패 시 None
    """
    if not image_url:
        print(f"[경고] 이미지 URL이 비어있습니다: {product_name}")
        return None

    save_dir = save_dir or IMAGE_SAVE_DIR
    os.makedirs(save_dir, exist_ok=True)

    # 랜덤 파일명: 상품명_랜덤문자열.jpg
    safe_name = sanitize_filename(product_name)
    suffix = _random_suffix(8)
    filename = f"{safe_name}_{suffix}.jpg"
    filepath = os.path.join(save_dir, filename)

    try:
        response = requests.get(
            image_url, timeout=15,
            proxies={"http": None, "https": None},
        )
        response.raise_for_status()

        raw_bytes = response.content
        _strip_exif_and_process(raw_bytes, filepath)

        print(f"[완료] 이미지 저장: {filepath}")
        return filepath

    except requests.RequestException as e:
        print(f"[오류] 이미지 다운로드 실패 ({product_name}): {e}")
        return None
    except Exception as e:
        print(f"[오류] 이미지 후처리 실패 ({product_name}): {e}")
        return None


# ─────────────────────────────────────────────────────────────
# 전체 상품 이미지 다운로드 + 매핑 딕셔너리 반환
# ─────────────────────────────────────────────────────────────
def download_all_images(products, save_dir=None):
    """
    상품 리스트의 모든 이미지를 다운로드하고 후처리합니다.

    Returns:
        {상품명: 이미지경로} 딕셔너리
        — 파일명이 랜덤이어도 상품명을 키로 정확히 매칭 가능
    """
    image_paths = {}

    for product in products:
        name = product.get("productName", "unknown")
        image_url = product.get("productImage", "")

        path = download_image(image_url, name, save_dir)
        if path:
            image_paths[name] = path

    print(f"\n총 {len(image_paths)}/{len(products)}개 이미지 다운로드 완료"
          f" (EXIF 제거 + 리사이즈 + 크롭 처리됨)")
    return image_paths

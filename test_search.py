# ============================================================
# 개별 모듈 테스트 스크립트
# ============================================================

import json
from coupang_api import search_products

# ── 1. 상품 검색 테스트 ──
print("=" * 40)
print("상품 검색 테스트")
print("=" * 40)

data = search_products("무선청소기", limit=3)

for item in data:
    print(f"상품명: {item['productName']}")
    print(f"가격: {item['productPrice']:,}원")
    print(f"이미지: {item['productImage']}")
    print(f"링크: {item['productUrl']}")
    print(f"카테고리: {item['categoryName']}")
    print("-" * 40)

# ── 2. 이미지 다운로드 테스트 ──
print("\n이미지 다운로드 테스트")
print("=" * 40)

from image_downloader import download_all_images

image_paths = download_all_images(data, save_dir="test_images")
print(f"다운로드 결과: {json.dumps(image_paths, ensure_ascii=False, indent=2)}")

# ── 3. URL 단축 테스트 ──
print("\nURL 단축 테스트")
print("=" * 40)

from url_shortener import shorten_product_urls

data = shorten_product_urls(data)
for item in data:
    print(f"원본: {item['productUrl'][:50]}...")
    print(f"단축: {item.get('short_url', 'N/A')}")
    print("-" * 40)

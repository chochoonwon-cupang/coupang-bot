# ============================================================
# 쿠팡 파트너스 자동 홍보 봇 - 메인 파이프라인
# ============================================================
# 실행 흐름:
#   1. 쿠팡 파트너스 API로 키워드 상품 검색
#   2. 딥링크 API + go.kdgc.co.kr 리다이렉트 URL 생성
#   3. 상품 이미지를 로컬에 다운로드
#   4. Gemini API로 네이버 카페 홍보 글 생성
# ============================================================

import json
import os
import random
import sys
from datetime import datetime

from coupang_api import search_products, create_deeplinks
from image_downloader import download_all_images
from gemini_api import generate_promo_post
from config import IMAGE_SAVE_DIR, DEFAULT_SEARCH_LIMIT


def run_pipeline(keyword, limit=None, gemini_api_key=None, log_callback=None,
                  image_save_dir=None,
                  keyword_repeat_min=3, keyword_repeat_max=7,
                  coupang_access_key=None, coupang_secret_key=None,
                  use_product_name=False, category="건강식품"):
    """
    전체 파이프라인을 실행합니다.

    Args:
        keyword: 검색 키워드
        limit: 검색 결과 수 (기본값: config의 DEFAULT_SEARCH_LIMIT)
        gemini_api_key: Gemini API 키 (None이면 config에서 가져옴)
        log_callback: 로그 출력 콜백 함수 (GUI 연동용). None이면 print 사용.
        image_save_dir: 이미지 저장 폴더 (None이면 config의 IMAGE_SAVE_DIR 사용)
        keyword_repeat_min: 키워드 반복 최소 횟수 (본문 내 자연 삽입)
        keyword_repeat_max: 키워드 반복 최대 횟수
        coupang_access_key: 쿠팡 파트너스 Access Key
        coupang_secret_key: 쿠팡 파트너스 Secret Key

    Returns:
        dict: {
            "keyword": 검색 키워드,
            "products": 상품 리스트,
            "image_paths": {상품명: 이미지경로},
            "post_content": 생성된 게시글,
            "output_file": 저장된 결과 파일 경로
        }
    """
    limit = limit or DEFAULT_SEARCH_LIMIT
    image_save_dir = image_save_dir or IMAGE_SAVE_DIR
    log = log_callback or print

    log("=" * 60)
    log(f"  쿠팡 파트너스 자동 홍보 봇")
    log(f"  검색 키워드: {keyword} | 상품 수: {limit}")
    log("=" * 60)

    # ── Step 1: 쿠팡 상품 검색 ──
    log("\n[Step 1/4] 쿠팡 파트너스 상품 검색 중...")
    try:
        products = search_products(keyword, limit=limit,
                                   access_key=coupang_access_key,
                                   secret_key=coupang_secret_key)
    except Exception as e:
        log(f"[오류] 상품 검색 실패: {e}")
        return None

    if not products:
        log("[결과] 검색 결과가 없습니다.")
        return None

    # 검색 결과에서 랜덤 n개 선택 (순서 섞기)
    random.shuffle(products)
    products = products[:limit]
    log(f"  → {len(products)}개 상품 검색 완료 (랜덤 {limit}개)")
    for i, p in enumerate(products, 1):
        price_str = f"{p['productPrice']:,}원" if isinstance(p['productPrice'], (int, float)) else str(p['productPrice'])
        log(f"  {i}. {p['productName'][:40]}... ({price_str})")

    # ── Step 2: 딥링크 변환 + 리다이렉트 URL 생성 ──
    import re as _re
    log(f"\n[Step 2/4] URL 생성 중...")

    # 2-a) 검색 API가 반환한 원본 URL 상세 출력
    log("  ── 원본 URL (검색 API) ──")
    for i, p in enumerate(products, 1):
        log(f"  [{i}] {p.get('productUrl', 'N/A')}")

    # 2-b) 딥링크 API 호출
    raw_urls = [p["productUrl"] for p in products if p.get("productUrl")]
    deeplink_map = {}
    if raw_urls:
        deeplink_map = create_deeplinks(
            raw_urls,
            access_key=coupang_access_key,
            secret_key=coupang_secret_key,
        )

    # 2-c) 딥링크 결과 + go.kdgc.co.kr 리다이렉트 URL 생성
    log("  ── 변환 결과 ──")
    converted = 0
    for i, p in enumerate(products, 1):
        orig = p.get("productUrl", "")
        deep = deeplink_map.get(orig)

        if deep:
            # link.coupang.com/a/CODE 에서 CODE 추출
            m = _re.search(r'/a/([A-Za-z0-9_\-]+)', deep)
            if m:
                code = m.group(1)
                redirect_url = f"https://go.kdgc.co.kr/go?id={code}"
            else:
                redirect_url = deep
            p["original_url"] = orig
            p["productUrl"] = deep
            p["short_url"] = redirect_url
            converted += 1
        else:
            # 딥링크 실패 → 원본 URL 그대로
            p["original_url"] = orig
            p["short_url"] = orig
            log(f"  [{i}] 딥링크 실패 → 원본 URL 사용")
            log(f"       {orig}")

    # ── Step 3: 이미지 다운로드 ──
    log(f"\n[Step 3/4] 상품 이미지 다운로드 중... (저장 위치: {image_save_dir})")
    image_paths = download_all_images(products, save_dir=image_save_dir)

    # ── Step 4: Gemini로 홍보 글 생성 (통합 호출) ──
    log("\n[Step 4/4] Gemini API로 네이버 카페 홍보 글 생성 중...")
    log("  4a) 공감 도입부 + 상품별 요약 통합 생성")
    log("  4b) 랜덤 제목 선택 + 키워드 반복 삽입 + 최종 조립")
    log(f"  (키워드 반복: {keyword_repeat_min}~{keyword_repeat_max}회)")
    post_content = generate_promo_post(
        products, keyword,
        gemini_api_key=gemini_api_key,
        image_paths=image_paths,
        keyword_repeat_min=keyword_repeat_min,
        keyword_repeat_max=keyword_repeat_max,
        use_product_name=use_product_name,
        category=category,
    )

    # ── 최종 결과 출력 ──
    log("\n" + "=" * 60)
    log("  최종 생성 결과")
    log("=" * 60)

    log("\n── 이미지 파일 경로 ──")
    if image_paths:
        for name, path in image_paths.items():
            log(f"  {name[:30]}... → {path}")
    else:
        log("  (다운로드된 이미지 없음)")

    log("\n── 상품별 파트너 링크 ──")
    for p in products:
        log(f"  {p['productName'][:30]}...")
        log(f"    원본: {p.get('original_url', 'N/A')}")
        log(f"    딥링크: {p.get('productUrl', 'N/A')}")
        log(f"    댓글링크: {p.get('short_url', 'N/A')}")

    # ── 결과를 파일로 저장 ──
    output = _save_result(keyword, products, image_paths, post_content)

    log(f"\n결과 파일 저장 완료: {output}")
    log("=" * 60)

    return {
        "keyword": keyword,
        "products": products,
        "image_paths": image_paths,
        "post_content": post_content,
        "output_file": output,
    }


def _save_result(keyword, products, image_paths, post_content):
    """
    결과를 JSON과 텍스트 파일로 저장합니다.
    """
    os.makedirs("output", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 텍스트 파일 (게시글 복사용)
    txt_path = f"output/{keyword}_{timestamp}.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(post_content)
        f.write("\n\n--- 이미지 경로 ---\n")
        for name, path in image_paths.items():
            f.write(f"{name}: {path}\n")

    # JSON 파일 (데이터 보관용)
    json_path = f"output/{keyword}_{timestamp}.json"
    result_data = {
        "keyword": keyword,
        "generated_at": timestamp,
        "products": products,
        "image_paths": image_paths,
        "post_content": post_content,
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)

    return txt_path


# ============================================================
# CLI 실행
# ============================================================
if __name__ == "__main__":
    KEYWORD = "무선청소기"
    LIMIT = 5

    result = run_pipeline(KEYWORD, limit=LIMIT)

    if result:
        print("\n파이프라인 실행 완료!")
    else:
        print("\n파이프라인 실행 실패")

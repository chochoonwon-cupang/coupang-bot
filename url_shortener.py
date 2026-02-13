# ============================================================
# URL 변환 모듈 (커스텀 리다이렉트 도메인)
# ============================================================
# 쿠팡 파트너 링크에서 ID를 추출하고,
# 커스텀 도메인(go.kdgc.co.kr)을 사용한 리다이렉트 URL로 변환합니다.
# Bitly 대신 자체 도메인을 사용하여 링크를 짧게 만듭니다.
# ============================================================

import re
from urllib.parse import quote, urlparse
from config import REDIRECT_BASE_URL


def extract_coupang_id(coupang_url):
    """
    쿠팡 파트너스 링크에서 마지막 ID 값을 추출합니다.

    지원 형식:
      - https://link.coupang.com/a/XXXXX      → XXXXX
      - https://link.coupang.com/a/bOSomY     → bOSomY
      - https://link.coupang.com/re/AFFSDP?... → URL-encode 전체 사용

    Args:
        coupang_url: 쿠팡 파트너 링크 원본 URL

    Returns:
        추출된 ID 문자열 (또는 URL-encode된 전체 URL)
    """
    if not coupang_url:
        return ""

    # 패턴 1: /a/XXXXX 형태의 짧은 링크
    match = re.search(r'/a/([A-Za-z0-9_\-]+)', coupang_url)
    if match:
        return match.group(1)

    # 패턴 2: /re/ 또는 기타 형태 → URL 전체를 이중 인코딩하여 ID로 사용
    # Vercel(Node.js)이 req.query에서 1차 디코딩 → go.js에서 2차 디코딩
    # 이중 인코딩해야 쿠팡 URL 내부의 & ? 등이 보존됨
    return quote(quote(coupang_url, safe=""), safe="")


def convert_to_redirect_url(coupang_url):
    """
    쿠팡 파트너 링크를 커스텀 리다이렉트 URL로 변환합니다.

    원본: https://link.coupang.com/a/XXXXX
    변환: https://go.kdgc.co.kr/go?id=XXXXX

    Args:
        coupang_url: 쿠팡 파트너 링크

    Returns:
        커스텀 도메인을 사용한 리다이렉트 URL
    """
    if not coupang_url:
        return ""

    coupang_id = extract_coupang_id(coupang_url)

    if not coupang_id:
        print(f"[경고] ID 추출 실패, 원본 URL 사용: {coupang_url}")
        return coupang_url

    redirect_url = f"{REDIRECT_BASE_URL}?id={coupang_id}"

    # 변환 로그 출력
    print(f"[링크 변환] 원본: {coupang_url[:60]}...")
    print(f"           → ID: {coupang_id}")
    print(f"           → 변환: {redirect_url}")

    return redirect_url


def shorten_product_urls(products):
    """
    상품 리스트의 모든 파트너 링크를 커스텀 리다이렉트 URL로 변환합니다.

    Args:
        products: 상품 정보 딕셔너리 리스트

    Returns:
        redirect_url 필드가 추가된 상품 리스트
    """
    print("\n🔗 링크 변환 처리 중 (커스텀 도메인: go.kdgc.co.kr)...")
    print("-" * 50)

    for i, product in enumerate(products, 1):
        original_url = product.get("productUrl", "")
        if original_url:
            print(f"\n[{i}/{len(products)}] {product.get('productName', '')[:30]}...")
            redirect_url = convert_to_redirect_url(original_url)
            product["short_url"] = redirect_url
            product["original_url"] = original_url  # 원본도 보관
        else:
            product["short_url"] = ""
            product["original_url"] = ""

    print("-" * 50)
    print(f"✅ 총 {len(products)}개 링크 변환 완료\n")
    return products

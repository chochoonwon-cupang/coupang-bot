# ============================================================
# 쿠팡 파트너스 API - 상품 검색 모듈
# ============================================================
# main.py의 generate_hmac 함수를 사용하여 HMAC 서명을 생성하고
# 쿠팡 파트너스 상품 검색 API를 호출합니다.
# ============================================================

import requests
from urllib.parse import urlencode
from config import ACCESS_KEY as DEFAULT_ACCESS_KEY, SECRET_KEY as DEFAULT_SECRET_KEY

DOMAIN = "https://api-gateway.coupang.com"

# 시스템 프록시를 무시 (프록시 연결 오류 방지)
NO_PROXY = {"http": None, "https": None}


def generate_hmac(method, url, secret_key, access_key):
    """
    쿠팡 파트너스 API용 HMAC-SHA256 서명을 생성합니다.
    Windows에서도 정확한 UTC 시간을 사용합니다.
    """
    import hmac
    import hashlib
    from datetime import datetime, timezone

    path, *query = url.split("?")

    # Windows 호환: datetime 모듈로 확실한 UTC 시간 생성
    now_utc = datetime.now(timezone.utc)
    datetime_str = now_utc.strftime('%y%m%d') + 'T' + now_utc.strftime('%H%M%S') + 'Z'

    message = datetime_str + method + path + (query[0] if query else "")

    signature = hmac.new(
        bytes(secret_key, "utf-8"),
        message.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    return (
        f"CEA algorithm=HmacSHA256, "
        f"access-key={access_key}, "
        f"signed-date={datetime_str}, "
        f"signature={signature}"
    )


def search_products(keyword, limit=5, access_key=None, secret_key=None):
    """
    쿠팡 파트너스 상품 검색 API를 호출합니다.

    Args:
        keyword: 검색 키워드
        limit: 가져올 상품 수 (기본 5)
        access_key: 쿠팡 파트너스 Access Key (None이면 config에서 가져옴)
        secret_key: 쿠팡 파트너스 Secret Key (None이면 config에서 가져옴)

    Returns:
        파싱된 상품 리스트 (dict 목록)
    """
    ak = access_key or DEFAULT_ACCESS_KEY
    sk = secret_key or DEFAULT_SECRET_KEY

    if not ak or not sk:
        raise ValueError("쿠팡 파트너스 Access Key와 Secret Key를 설정해주세요.")

    path = "/v2/providers/affiliate_open_api/apis/openapi/products/search"
    query_params = urlencode({"keyword": keyword, "limit": limit})
    request_url = f"{path}?{query_params}"

    # generate_hmac으로 인증 헤더 생성
    authorization = generate_hmac("GET", request_url, sk, ak)

    headers = {
        "Authorization": authorization,
        "Content-Type": "application/json;charset=UTF-8"
    }

    full_url = DOMAIN + request_url
    response = requests.get(full_url, headers=headers, proxies=NO_PROXY, timeout=15)
    response.raise_for_status()

    data = response.json()

    # 응답에서 상품 데이터 파싱
    products = []
    product_list = data.get("data", {}).get("productData", [])

    for item in product_list:
        product = {
            "productName": item.get("productName", ""),
            "productPrice": item.get("productPrice", 0),
            "productImage": item.get("productImage", ""),
            "productUrl": item.get("productUrl", ""),        # 파트너 링크
            "categoryName": item.get("categoryName", ""),
            "isRocket": item.get("isRocket", False),
            "isFreeShipping": item.get("isFreeShipping", False),
        }
        products.append(product)

    return products


def _tracking_url_to_product_url(tracking_url):
    """
    쿠팡 파트너스 검색 API의 tracking URL에서 깨끗한 상품 URL을 추출합니다.

    link.coupang.com/re/AFFSDP?...pageKey=12345&itemId=...&vendorItemId=...
    → https://www.coupang.com/vp/products/12345?itemId=...&vendorItemId=...

    이미 www.coupang.com URL이면 그대로 반환합니다.
    """
    from urllib.parse import urlparse, parse_qs

    if not tracking_url:
        return tracking_url

    # 이미 www.coupang.com 상품 URL이면 그대로
    if "www.coupang.com/vp/products" in tracking_url:
        return tracking_url

    # link.coupang.com/re/AFFSDP?... 형태에서 파라미터 추출
    if "link.coupang.com" in tracking_url and "/re/" in tracking_url:
        parsed = urlparse(tracking_url)
        qs = parse_qs(parsed.query)
        page_key = qs.get("pageKey", [None])[0]
        item_id = qs.get("itemId", [None])[0]
        vendor_item_id = qs.get("vendorItemId", [None])[0]

        if page_key:
            clean = f"https://www.coupang.com/vp/products/{page_key}"
            params = []
            if item_id:
                params.append(f"itemId={item_id}")
            if vendor_item_id:
                params.append(f"vendorItemId={vendor_item_id}")
            if params:
                clean += "?" + "&".join(params)
            return clean

    # 추출 실패 시 원본 반환
    return tracking_url


def create_deeplinks(product_urls, access_key=None, secret_key=None):
    """
    쿠팡 딥링크 API를 호출하여 상품 URL을 정식 파트너 링크로 변환합니다.

    www.coupang.com/vp/products/... → link.coupang.com/a/XXXXX

    tracking URL(link.coupang.com/re/AFFSDP?...)도 자동으로
    깨끗한 상품 URL로 변환한 후 딥링크 API에 전달합니다.

    Args:
        product_urls: 변환할 쿠팡 상품 URL 리스트
        access_key: 쿠팡 파트너스 Access Key
        secret_key: 쿠팡 파트너스 Secret Key

    Returns:
        dict: {원본URL: 딥링크URL, ...}
    """
    import json as _json

    ak = access_key or DEFAULT_ACCESS_KEY
    sk = secret_key or DEFAULT_SECRET_KEY

    if not ak or not sk:
        print("[딥링크] ✘ API 키가 없습니다")
        return {}

    # tracking URL → 깨끗한 상품 URL로 변환
    # 원본 URL → 깨끗한 URL 매핑 보관
    original_to_clean = {}
    clean_urls = []
    for url in product_urls:
        clean = _tracking_url_to_product_url(url)
        original_to_clean[url] = clean
        clean_urls.append(clean)
        print(f"[딥링크] 원본: {url}")
        print(f"[딥링크] 변환: {clean}")

    path = "/v2/providers/affiliate_open_api/apis/openapi/v1/deeplink"
    request_url = path

    authorization = generate_hmac("POST", request_url, sk, ak)

    headers = {
        "Authorization": authorization,
        "Content-Type": "application/json;charset=UTF-8"
    }

    body = {"coupangUrls": clean_urls}

    full_url = DOMAIN + request_url
    try:
        print(f"[딥링크] API 호출 중... ({len(clean_urls)}개 URL)")
        response = requests.post(
            full_url, headers=headers,
            data=_json.dumps(body),
            proxies=NO_PROXY, timeout=15)
        response.raise_for_status()
        data = response.json()

        print(f"[딥링크] API 응답: rCode={data.get('rCode')}, "
              f"rMessage={data.get('rMessage', '')}")

        # 딥링크 결과를 원본 URL 기준으로 매핑
        # API는 clean_url을 originalUrl로 반환
        clean_to_short = {}
        api_data = data.get("data", [])
        print(f"[딥링크] API 반환 개수: {len(api_data)}개")
        for item in api_data:
            original = item.get("originalUrl", "")
            shorten = item.get("shortenUrl", "")
            print(f"[딥링크] API 결과: originalUrl={original}")
            print(f"[딥링크] API 결과: shortenUrl={shorten}")
            if original and shorten:
                clean_to_short[original] = shorten

        # 원본 URL → 딥링크 매핑 구성
        result = {}
        for orig_url in product_urls:
            clean = original_to_clean.get(orig_url, orig_url)
            short = clean_to_short.get(clean)
            if short:
                result[orig_url] = short
                print(f"[딥링크] 매핑 성공: orig→clean→short 일치")
            else:
                # clean URL이 API 응답의 originalUrl과 다를 수 있음
                print(f"[딥링크] 매핑 실패!")
                print(f"  요청한 clean URL: {clean}")
                print(f"  API가 반환한 originalUrl 목록:")
                for k in clean_to_short:
                    print(f"    {k}")
                # 부분 매칭 시도 (pageKey 기준)
                from urllib.parse import urlparse, parse_qs
                try:
                    req_parsed = urlparse(clean)
                    req_path = req_parsed.path  # /vp/products/XXXX
                    for api_orig, api_short in clean_to_short.items():
                        if req_path in api_orig:
                            result[orig_url] = api_short
                            print(f"  → 부분 매칭 성공: {api_short}")
                            break
                except Exception:
                    pass

        print(f"[딥링크] 총 {len(result)}/{len(product_urls)}개 변환 성공")
        return result
    except Exception as e:
        print(f"[딥링크] ✘ API 호출 실패: {e}")
        return {}


def get_goldbox_deals(limit=10):
    """
    쿠팡 골드박스(오늘의 특가) API를 호출합니다.

    Args:
        limit: 가져올 특가 상품 수

    Returns:
        파싱된 특가 상품 리스트
    """
    path = "/v2/providers/affiliate_open_api/apis/openapi/products/goldbox"
    query_params = urlencode({"subId": "coupang_bot", "limit": limit})
    request_url = f"{path}?{query_params}"

    authorization = generate_hmac("GET", request_url, SECRET_KEY, ACCESS_KEY)

    headers = {
        "Authorization": authorization,
        "Content-Type": "application/json;charset=UTF-8"
    }

    full_url = DOMAIN + request_url
    response = requests.get(full_url, headers=headers, proxies=NO_PROXY, timeout=15)
    response.raise_for_status()

    data = response.json()

    products = []
    product_list = data.get("data", [])

    for item in product_list:
        product = {
            "productName": item.get("productName", ""),
            "productPrice": item.get("productPrice", 0),
            "originalPrice": item.get("originalPrice", 0),
            "discountRate": item.get("discountRate", ""),
            "productImage": item.get("productImage", ""),
            "productUrl": item.get("productUrl", ""),
            "categoryName": item.get("categoryName", ""),
        }
        products.append(product)

    return products

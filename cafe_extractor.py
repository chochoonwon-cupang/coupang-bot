# ============================================================
# 네이버 카페 URL → 카페 ID / 메뉴 ID 추출
# ============================================================
# requests로 카페 페이지를 가져와 HTML에서 clubid, menuid 파싱
# ============================================================

import re
import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
}


def extract_cafe_info(cafe_url: str, timeout: int = 10):
    """
    네이버 카페 URL에서 카페 ID와 메뉴 목록을 추출합니다.

    Args:
        cafe_url: 네이버 카페 URL (예: https://cafe.naver.com/jo/741450)
        timeout: 요청 타임아웃(초)

    Returns:
        dict: {
            "cafe_id": str or None,
            "menus": [{"menu_name": str, "menu_id": str, "type": str}, ...],
            "error": str or None
        }
    """
    url = (cafe_url or "").strip()
    if not url:
        return {"cafe_id": None, "menus": [], "error": "URL을 입력해주세요."}

    if "cafe.naver.com" not in url:
        return {"cafe_id": None, "menus": [], "error": "네이버 카페 URL이 아닙니다."}

    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        html = resp.text
    except requests.RequestException as e:
        return {"cafe_id": None, "menus": [], "error": f"페이지 요청 실패: {e}"}

    # 1. clubid 추출 (cafe_id)
    cafe_id = None
    for pat in [
        r'["\']?clubid["\']?\s*[:=]\s*["\']?(\d+)',
        r'search\.clubid=(\d+)',
        r'clubid=(\d+)',
        r'clubId=(\d+)',
        r'/cafes/(\d+)',
    ]:
        m = re.search(pat, html, re.IGNORECASE)
        if m:
            cafe_id = m.group(1)
            break

    # 2. 메뉴 목록 추출 (menuid=XXX, menu_name)
    menus = []
    seen = set()

    # [메뉴명](URL...search.menuid=XXX...) 마크다운/링크 형태 (메뉴명+menuid 동시 추출)
    for m in re.finditer(
        r'\[([^\]]+)\]\([^)]*search\.menuid=(\d+)[^)]*\)',
        html,
    ):
        name, mid = m.group(1).strip(), m.group(2)
        if mid not in seen and name and len(name) < 50:
            seen.add(mid)
            menus.append({"menu_name": name, "menu_id": mid, "type": "일반"})

    # <a ...>메뉴명</a> 내부에 href에 menuid 있는 경우
    for m in re.finditer(
        r'<a[^>]*href="[^"]*search\.menuid=(\d+)[^"]*"[^>]*>([^<]+)</a>',
        html,
        re.IGNORECASE,
    ):
        mid, name = m.group(1), m.group(2).strip()
        if mid not in seen and name and len(name) < 50 and not name.startswith("http"):
            seen.add(mid)
            menus.append({"menu_name": name, "menu_id": mid, "type": "일반"})

    # JSON 형태: "menuId":32,"menuName":"공지사항"
    for m in re.finditer(
        r'["\']?menu_?[iI]d["\']?\s*:\s*["\']?(\d+)["\']?\s*[,}][^}]*["\']?(?:menu_?[nN]ame|name|title)["\']?\s*:\s*["\']([^"\']+)["\']',
        html,
    ):
        mid, name = m.group(1), m.group(2).strip()
        if mid not in seen:
            seen.add(mid)
            menus.append({"menu_name": name, "menu_id": mid, "type": "일반"})

    # menuid만 있는 경우 (메뉴명 없음) - 마지막에 추가
    for m in re.finditer(
        r'search\.menuid=(\d+)|menuid=(\d+)|menu_id=(\d+)|menus/(\d+)',
        html,
        re.IGNORECASE,
    ):
        mid = m.group(1) or m.group(2) or m.group(3) or m.group(4)
        if mid and mid not in seen:
            seen.add(mid)
            menus.append({"menu_name": mid, "menu_id": mid, "type": "일반"})

    # 중복 제거 후 정렬 (menu_id 숫자순)
    def sort_key(x):
        try:
            return int(x["menu_id"])
        except ValueError:
            return 0

    menus = sorted(menus, key=sort_key)

    # 메뉴가 없으면 기본 게시판(전체글) 추가 시도
    if not menus and cafe_id:
        menus.append({"menu_name": "전체글", "menu_id": "0", "type": "일반"})

    return {"cafe_id": cafe_id, "menus": menus, "error": None}

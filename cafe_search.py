# ============================================================
# 네이버 카페 검색 (키워드로 카페 URL 수집)
# ============================================================
# 1. search_naver_cafes: search.naver.com (requests, 구버전)
# 2. search_naver_cafes_selenium: section.cafe.naver.com (Selenium, 로그인 후)
# ============================================================

import re
import time
import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9",
}


def search_naver_cafes(keyword: str, limit: int = 30, timeout: int = 10):
    """
    네이버 검색에서 카페 URL 목록 추출 (requests 기반, 구버전).
    https://search.naver.com/search.naver?where=nexearch&query=키워드+카페

    Returns:
        list[str]: 카페 URL 목록 (중복 제거)
    """
    if not (keyword or "").strip():
        return []
    q = f"{keyword.strip()} 카페"
    url = f"https://search.naver.com/search.naver?where=nexearch&query={requests.utils.quote(q)}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        html = resp.text
    except Exception:
        return []

    # cafe.naver.com URL 추출
    pattern = r'https?://cafe\.naver\.com/[a-zA-Z0-9_\-./]+(?:\?[^"\')\s]*)?'
    urls = re.findall(pattern, html)
    seen = set()
    result = []
    for u in urls:
        base = u.split("?")[0].rstrip("/")
        if "/ArticleRead" in base or "/ArticleList" in base:
            base = re.sub(r"/Article(Read|List).*", "", base)
        if base not in seen and "cafe.naver.com" in base:
            seen.add(base)
            result.append(base)
            if len(result) >= limit:
                break
    return result


def search_naver_cafes_selenium(driver, keyword: str, max_pages: int = 200, stop_flag=None, log=None):
    """
    section.cafe.naver.com에서 로그인 후 카페 검색 (Selenium).
    - https://section.cafe.naver.com/ca-fe/home 이동
    - 검색어 입력 → 2초 대기 → Enter
    - '카페명' 탭 클릭
    - 다음 버튼으로 최대 max_pages 페이지까지 순회하며 카페 URL 수집

    Args:
        driver: Selenium WebDriver (로그인 완료된 상태)
        keyword: 검색 키워드
        max_pages: 최대 페이지 수 (기본 200)
        stop_flag: callable, True 반환 시 중지
        log: 로그 콜백

    Returns:
        list[str]: 카페 URL 목록 (중복 제거, 상단부터 순서 유지)
    """
    _log = log or print
    stop_flag = stop_flag or (lambda: False)

    try:
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.common.exceptions import TimeoutException
    except ImportError:
        _log("[카페검색] Selenium 미설치")
        return []

    if not (keyword or "").strip():
        return []

    base_url = "https://section.cafe.naver.com/ca-fe/home"
    all_urls = []
    seen = set()

    try:
        _log(f"[카페검색] {base_url} 이동")
        driver.get(base_url)
        time.sleep(2)

        # 검색 입력창 찾기
        search_selectors = [
            "input[type='search']",
            "input[placeholder*='검색']",
            "input[placeholder*='카페']",
            "input.search_input",
            "input[name='query']",
            "input[aria-label*='검색']",
        ]
        search_input = None
        for sel in search_selectors:
            try:
                search_input = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, sel))
                )
                if search_input and search_input.is_displayed():
                    break
            except TimeoutException:
                continue
        if not search_input:
            _log("[카페검색] 검색 입력창을 찾을 수 없음")
            return []

        search_input.clear()
        search_input.send_keys(keyword.strip())
        _log(f"[카페검색] 검색어 입력: {keyword.strip()}")
        time.sleep(2)
        search_input.send_keys(Keys.ENTER)
        time.sleep(3)

        # 카페명 탭 클릭
        tab_selectors = [
            "button.tab_btn span.tab_name",
            "button[role='tab'] span.tab_name",
            "[role='tablist'] button span.tab_name",
        ]
        tab_clicked = False
        for sel in tab_selectors:
            try:
                tabs = driver.find_elements(By.CSS_SELECTOR, sel)
                for t in tabs:
                    if t and t.text and "카페명" in t.text:
                        parent = t.find_element(By.XPATH, "..")
                        if parent:
                            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", parent)
                            time.sleep(0.5)
                            parent.click()
                            tab_clicked = True
                            _log("[카페검색] 카페명 탭 클릭")
                            break
                if tab_clicked:
                    break
            except Exception:
                continue
        if not tab_clicked:
            _log("[카페검색] 카페명 탭을 찾을 수 없음 (전체글 탭 결과 사용)")
        time.sleep(2)

        # 페이지 순회
        for page_num in range(1, max_pages + 1):
            if stop_flag():
                _log("[카페검색] 중지됨")
                break

            if page_num > 1:
                _log(f"[카페검색] {page_num}페이지 이동 중...")

            # 현재 페이지에서 카페 URL 추출
            page_urls = _extract_cafe_urls_from_page(driver, log=_log)
            for u in page_urls:
                if u not in seen:
                    seen.add(u)
                    all_urls.append(u)

            # 다음 버튼 클릭
            next_btn = None
            for sel in [
                "button.btn.type_next",
                "button[class*='type_next']",
                "button[aria-label='다음']",
                ".ArticlePaginate button.type_next",
                "button.btn[class*='next']",
            ]:
                try:
                    btns = driver.find_elements(By.CSS_SELECTOR, sel)
                    for b in btns:
                        if b and b.is_displayed() and b.is_enabled():
                            next_btn = b
                            break
                    if next_btn:
                        break
                except Exception:
                    continue

            if not next_btn:
                _log(f"[카페검색] {page_num}페이지까지 수집 완료 (다음 버튼 없음)")
                break

            try:
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", next_btn)
                time.sleep(0.5)
                next_btn.click()
                time.sleep(2)
            except Exception as e:
                _log(f"[카페검색] 다음 페이지 이동 실패: {e}")
                break

        _log(f"[카페검색] 총 {len(all_urls)}개 카페 URL 수집")
        return all_urls

    except Exception as e:
        _log(f"[카페검색] 오류: {e}")
        import traceback
        traceback.print_exc()
        return all_urls


def _extract_cafe_urls_from_page(driver, log=None):
    """현재 페이지에서 cafe.naver.com URL 추출"""
    from selenium.webdriver.common.by import By
    urls = []
    try:
        # a[href*="cafe.naver.com"] 링크 수집
        links = driver.find_elements(By.CSS_SELECTOR, "a[href*='cafe.naver.com']")
        for a in links:
            try:
                href = a.get_attribute("href") or ""
                if not href or "section.cafe.naver.com" in href:
                    continue
                # cafe.naver.com/xxx 형태로 정규화
                base = href.split("?")[0].rstrip("/")
                if "/ArticleRead" in base or "/ArticleList" in base:
                    base = re.sub(r"/Article(Read|List).*", "", base)
                if "cafe.naver.com" in base and base not in urls:
                    urls.append(base)
            except Exception:
                continue
        # HTML에서 정규식으로 보강
        html = driver.page_source
        for m in re.finditer(r'https?://cafe\.naver\.com/[a-zA-Z0-9_\-./]+', html):
            u = m.group(0).split("?")[0].rstrip("/")
            if "/ArticleRead" in u or "/ArticleList" in u:
                u = re.sub(r"/Article(Read|List).*", "", u)
            if u not in urls:
                urls.append(u)
    except Exception as ex:
        if log:
            log(f"[카페검색] URL 추출 오류: {ex}")
    return urls

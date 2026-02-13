# ============================================================
# Supabase 클라이언트 — 유료회원 데이터 관리
# ============================================================

from config import SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_KEY

# 유효한 발행 카테고리 (이 목록에 없으면 기본값 '기타' 사용)
VALID_CATEGORIES = ("건강식품", "생활용품", "가전제품", "유아/출산", "기타")

"""
Supabase paid_members 테이블: supabase_schema.sql 참고
users 테이블: 추천인(referrer_id) 정보 — distribute_keyword, distribute_category
"""


def _get_client():
    """Supabase 클라이언트 인스턴스를 생성합니다."""
    try:
        from supabase import create_client
    except ImportError:
        raise ImportError(
            "supabase 패키지가 설치되어 있지 않습니다. "
            "pip install supabase 를 실행하세요."
        )
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        raise ValueError(
            "config.py에 SUPABASE_URL과 SUPABASE_ANON_KEY를 설정하세요."
        )
    return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


def _get_service_client():
    """RLS 우회용 service_role 클라이언트 (users 테이블 조회)"""
    try:
        from supabase import create_client
    except ImportError:
        raise ImportError("pip install supabase")
    key = SUPABASE_SERVICE_KEY or ""
    if not key:
        raise ValueError("config.py에 SUPABASE_SERVICE_KEY를 설정하세요.")
    return create_client(SUPABASE_URL, key)


def fetch_referrer(referrer_username: str, log=None):
    """
    users 테이블에서 추천인 정보를 조회합니다.
    referrer_username = users.username (추천인 아이디)

    Returns:
        dict | None: 추천인 정보 (paid_members와 동일 형식)
            {
                "name": str,
                "keywords": list[str],
                "category": str,
                "coupang_access_key": str,
                "coupang_secret_key": str,
            }
        None: 추천인 없음, 데이터 비어있음, API 키 없음
    """
    _log = log or print
    if not referrer_username or not (referrer_username or "").strip():
        return None

    referrer_username = (referrer_username or "").strip()
    try:
        client = _get_service_client()
        r = (
            client.table("users")
            .select("username, distribute_keyword, distribute_category, coupang_access_key, coupang_secret_key")
            .eq("username", referrer_username)
            .execute()
        )
        if not r.data or len(r.data) == 0:
            _log(f"[Supabase] 추천인 '{referrer_username}' 조회 결과 없음")
            return None

        row = r.data[0]
        raw_kw = (row.get("distribute_keyword") or "").strip()
        kw_list = [k.strip() for k in raw_kw.split(",") if k.strip()]
        if not kw_list:
            _log(f"[Supabase] 추천인 '{referrer_username}' — 키워드가 등록되어 있지 않습니다.")
            return None

        ak = (row.get("coupang_access_key") or "").strip()
        sk = (row.get("coupang_secret_key") or "").strip()
        if not ak or not sk:
            _log(f"[Supabase] 추천인 '{referrer_username}' — 쿠팡 API 키 없음")
            return None

        raw_cat = (row.get("distribute_category") or "").strip()
        category = raw_cat if raw_cat in VALID_CATEGORIES else "기타"

        _log(f"[Supabase] 추천인 '{referrer_username}' 로드 완료")
        return {
            "name": referrer_username,
            "keywords": kw_list,
            "category": category,
            "coupang_access_key": ak,
            "coupang_secret_key": sk,
        }
    except Exception as e:
        _log(f"[Supabase] 추천인 조회 실패: {e}")
        return None


def fetch_banned_brands(log=None):
    """
    Supabase banned_brands 테이블에서 쿠팡 활동금지 업체/브랜드 목록을 가져옵니다.

    Returns:
        list[str]: 금지 브랜드명 리스트 (예: ["락토핏", "종근당", ...])
        빈 리스트: 데이터 없거나 오류 발생 시
    """
    _log = log or print
    try:
        client = _get_client()
        r = client.table("banned_brands").select("brand_name").execute()
        brands = [row.get("brand_name", "").strip() for row in (r.data or []) if row.get("brand_name", "").strip()]
        if brands:
            _log(f"[Supabase] 활동금지 브랜드 {len(brands)}개 로드")
        return brands
    except Exception as e:
        _log(f"[Supabase] banned_brands 조회 실패: {e}")
        return []


def fetch_banners(log=None):
    """
    Supabase banners 테이블에서 하단 배너 목록을 가져옵니다.

    Returns:
        list[dict]: [{main_text, sub_text, url}, ...]
        빈 리스트: 데이터 없거나 오류 발생 시
    """
    _log = log or print
    try:
        client = _get_client()
        r = client.table("banners").select("main_text, sub_text, url").execute()
        banners = []
        for row in (r.data or []):
            mt = (row.get("main_text") or "").strip()
            st = (row.get("sub_text") or "").strip()
            url = (row.get("url") or "").strip()
            if mt and url:
                banners.append({"main_text": mt, "sub_text": st, "url": url})
        if banners:
            _log(f"[Supabase] 배너 {len(banners)}개 로드")
        return banners
    except Exception as e:
        _log(f"[Supabase] banners 조회 실패: {e}")
        return []


def fetch_helper_cafes(log=None):
    """
    Supabase helper_cafes 테이블에서 도우미 기본 카페리스트를 가져옵니다.

    Returns:
        list[dict]: [{"cafe_url", "cafe_id", "menu_id", "created_at"}, ...]
        빈 리스트: 데이터 없거나 오류 발생 시
    """
    _log = log or print
    try:
        client = _get_client()
        r = client.table("helper_cafes").select("cafe_url, cafe_id, menu_id, created_at").order("sort_order").execute()
        cafes = []
        for row in (r.data or []):
            url = (row.get("cafe_url") or "").strip()
            cid = (row.get("cafe_id") or "").strip()
            mid = (row.get("menu_id") or "").strip()
            if url and cid and mid:
                cafes.append({
                    "cafe_url": url, "cafe_id": cid, "menu_id": mid,
                    "created_at": row.get("created_at"),
                })
        if cafes:
            _log(f"[Supabase] 도우미 카페 {len(cafes)}개 로드")
        return cafes
    except Exception as e:
        _log(f"[Supabase] helper_cafes 조회 실패: {e}")
        return []


def fetch_helper_new_cafe_since(log=None):
    """
    app_links에서 신규 카페 기준일 조회.
    link_key='helper_new_cafe_since', url='2026-02-07' (YYYY-MM-DD)

    Returns:
        str | None: 기준일 문자열 (YYYY-MM-DD), 없으면 None
    """
    _log = log or print
    try:
        client = _get_client()
        r = client.table("app_links").select("url").eq("link_key", "helper_new_cafe_since").limit(1).execute()
        if r.data and len(r.data) > 0:
            val = (r.data[0].get("url") or "").strip()
            if val:
                return val
        return None
    except Exception as e:
        _log(f"[Supabase] helper_new_cafe_since 조회 실패: {e}")
        return None


def fetch_app_links(log=None):
    """
    Supabase app_links 테이블에서 링크 설정을 가져옵니다.

    Returns:
        dict: link_key → url 매핑
            - inquiry: 문의접수 링크
            - tutorial_video: 프로그램 사용법 영상 링크
            - banner: 하단배너 링크
        빈 dict: 데이터 없거나 오류 발생 시
    """
    _log = log or print
    try:
        client = _get_client()
        r = client.table("app_links").select("link_key, url").execute()
        links = {}
        for row in (r.data or []):
            k = (row.get("link_key") or "").strip()
            v = (row.get("url") or "").strip()
            if k and v:
                links[k] = v
        if links:
            _log(f"[Supabase] 앱 링크 {len(links)}개 로드")
        return links
    except Exception as e:
        _log(f"[Supabase] app_links 조회 실패: {e}")
        return {}


def is_keyword_banned(keyword: str, banned_brands: list) -> bool:
    """키워드에 금지 브랜드가 포함되어 있는지 확인 (대소문자 무시)"""
    if not keyword or not banned_brands:
        return False
    kw_lower = keyword.lower()
    return any(b.strip().lower() in kw_lower for b in banned_brands if b and b.strip())


def fetch_paid_members(log=None):
    """
    Supabase에서 active=true인 유료회원 목록을 가져옵니다.

    Returns:
        list[dict]: 각 회원 정보
            {
                "name": str,
                "keywords": list[str],   # 콤마 구분 → 리스트 변환
                "category": str,         # 유효하면 그대로, 없으면 '기타'
                "coupang_access_key": str,
                "coupang_secret_key": str,
            }
        빈 리스트: 데이터 없거나 오류 발생 시
    """
    _log = log or print

    try:
        client = _get_client()
        response = (
            client.table("paid_members")
            .select("name, keywords, category, coupang_access_key, coupang_secret_key")
            .eq("active", True)
            .execute()
        )

        members = []
        for row in response.data:
            # 키워드 문자열을 리스트로 변환 (콤마 구분, 공백 제거)
            raw_kw = row.get("keywords", "")
            kw_list = [k.strip() for k in raw_kw.split(",") if k.strip()]

            if not kw_list:
                _log(f"  [주의] 회원 '{row.get('name', '?')}' — 키워드가 비어있어 건너뜁니다.")
                continue

            ak = row.get("coupang_access_key", "")
            sk = row.get("coupang_secret_key", "")
            if not ak or not sk:
                _log(f"  [주의] 회원 '{row.get('name', '?')}' — 쿠팡 API 키가 비어있어 건너뜁니다.")
                continue

            raw_cat = (row.get("category") or "").strip()
            category = raw_cat if raw_cat in VALID_CATEGORIES else "기타"

            members.append({
                "name": row.get("name", "이름없음"),
                "keywords": kw_list,
                "category": category,
                "coupang_access_key": ak,
                "coupang_secret_key": sk,
            })

        _log(f"[Supabase] 유료회원 {len(members)}명 로드 완료")
        return members

    except ImportError as e:
        _log(f"[Supabase] 오류: {e}")
        return []
    except ValueError as e:
        _log(f"[Supabase] 설정 오류: {e}")
        return []
    except Exception as e:
        _log(f"[Supabase] 데이터 조회 실패: {e}")
        return []


# ─────────────────────────────────────────────────────────────
# tasks 테이블 (SaaS 에이전트 모드)
# ─────────────────────────────────────────────────────────────

def fetch_pending_task(log=None):
    """
    status='pending' (또는 '대기')인 작업 1건을 가져옵니다. (가장 오래된 것)
    service_role 사용 (RLS 우회)

    Returns:
        dict | None: {"id", "keyword", "status", "result_url", "created_at"} 또는 None
    """
    _log = log or print
    try:
        client = _get_service_client()
        r = (
            client.table("tasks")
            .select("id, keyword, status, result_url, created_at")
            .in_("status", ["pending", "대기"])
            .order("created_at")
            .limit(1)
            .execute()
        )
        if r.data and len(r.data) > 0:
            return dict(r.data[0])
        return None
    except Exception as e:
        _log(f"[Supabase] tasks 대기 작업 조회 실패: {e}")
        return None


def update_task_status(task_id, status, result_url=None, error_message=None, log=None):
    """
    tasks 테이블의 status(및 result_url, error_message)를 업데이트합니다.
    status: 'processing' | 'completed' | 'failed' (또는 '진행'|'완료' 호환)
    """
    _log = log or print
    try:
        from datetime import datetime, timezone
        client = _get_service_client()
        data = {"status": status, "updated_at": datetime.now(timezone.utc).isoformat()}
        if result_url is not None:
            data["result_url"] = result_url
        if error_message is not None:
            data["error_message"] = error_message
        client.table("tasks").update(data).eq("id", task_id).execute()
        _log(f"[Supabase] tasks id={task_id} → status={status}")
    except Exception as e:
        _log(f"[Supabase] tasks 업데이트 실패: {e}")

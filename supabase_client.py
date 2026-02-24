# ============================================================
# Supabase 클라이언트 — 유료회원 데이터 관리
# ============================================================

import datetime

from config import SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_KEY, OWNER_USER_ID

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


def fetch_user_coupang_keys(username: str, log=None):
    """
    users 테이블에서 본인(로그인 사용자)의 쿠팡 API 키를 조회합니다.
    본인글 작성 시 블로그·카페 모두 이 키를 사용합니다.

    Returns:
        tuple[str, str] | None: (access_key, secret_key) 또는 None (키 없음/오류)
    """
    _log = log or print
    username = (username or "").strip()
    if not username:
        return None
    try:
        client = _get_service_client()
        r = (
            client.table("users")
            .select("coupang_access_key, coupang_secret_key")
            .eq("username", username)
            .execute()
        )
        if not r.data or len(r.data) == 0:
            return None
        row = r.data[0]
        ak = (row.get("coupang_access_key") or "").strip()
        sk = (row.get("coupang_secret_key") or "").strip()
        if not ak or not sk:
            return None
        return (ak, sk)
    except Exception as e:
        _log(f"[Supabase] users 쿠팡키 조회 실패: {e}")
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


def upsert_helper_cafe(cafe_url: str, cafe_id: str, menu_id: str, sort_order: int = 0, log=None):
    """
    helper_cafes 테이블: cafe_url이 있으면 cafe_id, menu_id 덮어쓰기 (UPDATE).
    없으면 새로 추가 (INSERT). 같은 cafe_url이 하나만 유지되도록 함.
    service_role 사용 (RLS 우회).

    Returns:
        bool: 성공 시 True, 실패 시 False
    """
    _log = log or print
    url = (cafe_url or "").strip()
    cid = (cafe_id or "").strip()
    mid = (menu_id or "").strip()
    if not url or not cid or not mid:
        _log("[Supabase] helper_cafes 저장 실패: cafe_url, cafe_id, menu_id 필수")
        return False
    try:
        client = _get_service_client()
        # 1) cafe_url이 있는 행이 있으면 UPDATE (덮어쓰기)
        r = client.table("helper_cafes").update({
            "cafe_id": cid,
            "menu_id": mid,
            "sort_order": sort_order,
        }).eq("cafe_url", url).execute()
        if r.data and len(r.data) > 0:
            _log(f"[Supabase] helper_cafes 갱신: {url[:40]}... → cafe_id={cid}, menu_id={mid}")
            return True
        # 2) 없으면 INSERT
        client.table("helper_cafes").insert({
            "cafe_url": url,
            "cafe_id": cid,
            "menu_id": mid,
            "sort_order": sort_order,
        }).execute()
        _log(f"[Supabase] helper_cafes 추가: {cid} / {mid}")
        return True
    except Exception as e:
        _log(f"[Supabase] helper_cafes 저장 실패: {e}")
        return False


def insert_helper_cafe(cafe_url: str, cafe_id: str, menu_id: str, sort_order: int = 0, log=None):
    """upsert_helper_cafe의 별칭 (하위 호환)"""
    return upsert_helper_cafe(cafe_url, cafe_id, menu_id, sort_order, log)


def delete_helper_cafe_by_url(cafe_url: str, log=None):
    """
    helper_cafes 테이블에서 cafe_url에 해당하는 행 삭제.
    service_role 사용 (RLS 우회).

    Returns:
        bool: 성공 시 True, 실패 시 False
    """
    _log = log or print
    url = (cafe_url or "").strip()
    if not url:
        return False
    try:
        client = _get_service_client()
        client.table("helper_cafes").delete().eq("cafe_url", url).execute()
        _log(f"[Supabase] helper_cafes 삭제: {url[:50]}...")
        return True
    except Exception as e:
        _log(f"[Supabase] helper_cafes 삭제 실패: {e}")
        return False


def fetch_cafe_join_policy_for_program(program_username: str, owner_user_id: str = None, log=None):
    """agent_configs.config.cafe_join 우선 조회. 없으면 cafe_join_policy(id=1) fallback."""
    _log = log or print
    try:
        row = fetch_agent_config(program_username, owner_user_id=owner_user_id, log=_log)
        cfg = row.get("config") or {}
        cj = cfg.get("cafe_join")
        if isinstance(cj, dict) and cj:
            run_days = cj.get("run_days")
            if not isinstance(run_days, list):
                run_days = [4, 14, 24]
            return {
                "run_days": run_days,
                "start_time": (cj.get("start_time") or "09:00").strip() or "09:00",
                "created_year_min": int(cj.get("created_year_min") or 2020),
                "created_year_max": int(cj.get("created_year_max") or 2025),
                "recent_post_days": int(cj.get("recent_post_days") or 7),
                "recent_post_enabled": bool(cj.get("recent_post_enabled", True)),
                "target_count": int(cj.get("target_count") or 50),
                "search_keyword": (cj.get("search_keyword") or "").strip(),
            }
    except Exception as e:
        _log(f"[Supabase] agent_config cafe_join 조회 실패: {e}")
    return fetch_cafe_join_policy(log=_log)


def fetch_cafe_join_policy(log=None):
    """cafe_join_policy id=1 조회. 없으면 기본값 반환.
    service_role 사용 (RLS 우회 — PC 에이전트가 정책 읽기 위해).
    실제 DB 컬럼명(min_created_year, max_created_year, require_no_recent_posts)과
    표준명(created_year_min 등) 모두 지원."""
    _log = log or print
    try:
        client = _get_service_client()
        r = client.table("cafe_join_policy").select("*").eq("id", 1).limit(1).execute()
        if r.data and len(r.data) > 0:
            row = r.data[0]
            year_min = row.get("created_year_min") or row.get("min_created_year")
            year_max = row.get("created_year_max") or row.get("max_created_year")
            recent_en = row.get("recent_post_enabled")
            if recent_en is None:
                rnrp = row.get("require_no_recent_posts")
                recent_en = True if rnrp is None else bool(rnrp)
            return {
                "run_days": row.get("run_days") or [4, 14, 24],
                "start_time": (row.get("start_time") or "09:00").strip() or "09:00",
                "created_year_min": int(year_min or 2020),
                "created_year_max": int(year_max or 2025),
                "recent_post_days": int(row.get("recent_post_days") or 7),
                "recent_post_enabled": bool(recent_en),
                "target_count": int(row.get("target_count") or 50),
                "search_keyword": (row.get("search_keyword") or "").strip(),
            }
        return {"run_days": [4, 14, 24], "start_time": "09:00", "created_year_min": 2020, "created_year_max": 2025,
                "recent_post_days": 7, "recent_post_enabled": True, "target_count": 50, "search_keyword": ""}
    except Exception as e:
        _log(f"[Supabase] cafe_join_policy 조회 실패: {e}")
        return {"run_days": [4, 14, 24], "start_time": "09:00", "created_year_min": 2020, "created_year_max": 2025,
                "recent_post_days": 7, "recent_post_enabled": True, "target_count": 50, "search_keyword": ""}


def upsert_cafe_join_policy(policy: dict, log=None):
    """cafe_join_policy id=1 upsert. service_role 사용.
    min_created_year/max_created_year/require_no_recent_posts 또는
    created_year_min/created_year_max/recent_post_enabled 스키마 모두 지원."""
    _log = log or print
    try:
        client = _get_service_client()
        year_min = int(policy.get("created_year_min", 2020))
        year_max = int(policy.get("created_year_max", 2025))
        recent_en = bool(policy.get("recent_post_enabled", True))
        base = {
            "id": 1,
            "run_days": policy.get("run_days", [4, 14, 24]),
            "start_time": (policy.get("start_time") or "09:00").strip() or "09:00",
            "recent_post_days": int(policy.get("recent_post_days", 7)),
            "target_count": int(policy.get("target_count", 50)),
            "search_keyword": (policy.get("search_keyword") or "").strip(),
            "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
        base_no_time = {k: v for k, v in base.items() if k != "start_time"}
        # 표준 컬럼명 시도 후, 실패 시 실제 DB 컬럼명(min_created_year 등) 또는 start_time 제외로 재시도
        for data in [
            {**base, "created_year_min": year_min, "created_year_max": year_max, "recent_post_enabled": recent_en},
            {**base, "min_created_year": year_min, "max_created_year": year_max, "require_no_recent_posts": recent_en},
            {**base_no_time, "created_year_min": year_min, "created_year_max": year_max, "recent_post_enabled": recent_en},
        ]:
            try:
                client.table("cafe_join_policy").upsert(data, on_conflict="id").execute()
                _log("[Supabase] cafe_join_policy 저장 완료")
                return True
            except Exception as inner:
                if "column" in str(inner).lower() or "does not exist" in str(inner).lower():
                    continue
                raise
        return False
    except Exception as e:
        _log(f"[Supabase] cafe_join_policy 저장 실패: {e}")
        return False


def fetch_agent_cafe_lists(program_username: str, statuses=None, log=None, use_service=False):
    """agent_cafe_lists에서 status='saved' 또는 'joined' 조회. use_service=True면 service_role 사용."""
    _log = log or print
    statuses = statuses or ["saved", "joined"]
    try:
        client = _get_service_client() if use_service else _get_client()
        r = client.table("agent_cafe_lists").select("cafe_url, cafe_id, menu_id, status").eq(
            "program_username", program_username
        ).in_("status", statuses).order("created_at").execute()
        return [
            {"cafe_url": row.get("cafe_url"), "cafe_id": row.get("cafe_id"), "menu_id": row.get("menu_id")}
            for row in (r.data or [])
        ]
    except Exception as e:
        _log(f"[Supabase] agent_cafe_lists 조회 실패: {e}")
        return []


def insert_agent_cafe_list(owner_user_id, program_username, cafe_url, cafe_id=None, menu_id=None, status="saved", reject_reason=None, log=None):
    """agent_cafe_lists에 insert. service_role 사용."""
    _log = log or print
    try:
        client = _get_service_client()
        data = {
            "owner_user_id": owner_user_id,
            "program_username": program_username,
            "cafe_url": cafe_url,
            "cafe_id": cafe_id or "",
            "menu_id": menu_id or "",
            "status": status,
        }
        if reject_reason is not None:
            data["reject_reason"] = reject_reason
        client.table("agent_cafe_lists").insert(data).execute()
        return True
    except Exception as e:
        _log(f"[Supabase] agent_cafe_lists insert 실패: {e}")
        return False


def update_agent_cafe_list_status(cafe_url: str, program_username: str, status: str, reject_reason: str = None, cafe_id=None, menu_id=None, log=None):
    """agent_cafe_lists status 업데이트. service_role 사용."""
    _log = log or print
    try:
        client = _get_service_client()
        data = {"status": status}
        if reject_reason is not None:
            data["reject_reason"] = reject_reason
        if cafe_id is not None:
            data["cafe_id"] = cafe_id
        if menu_id is not None:
            data["menu_id"] = menu_id
        client.table("agent_cafe_lists").update(data).eq("cafe_url", cafe_url).eq(
            "program_username", program_username
        ).execute()
        return True
    except Exception as e:
        _log(f"[Supabase] agent_cafe_lists update 실패: {e}")
        return False


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


def fetch_paid_member_keywords_pool(count=None, log=None):
    """
    유료회원들의 키워드를 모아 랜덤 풀로 반환합니다.
    관리자(okdog)용 — 키워드 설정 없이 유료회원 키워드로 발행할 때 사용.

    Returns:
        list[str]: 랜덤 섞인 키워드 리스트 (회원별 랜덤, 키워드별 랜덤)
        count 지정 시 해당 개수만 반환 (부족하면 중복 허용)
    """
    import random
    _log = log or print
    members = fetch_paid_members(log=_log)
    pool = []
    for m in members:
        kws = m.get("keywords") or []
        for kw in kws:
            if kw and str(kw).strip():
                pool.append(str(kw).strip())
    random.shuffle(pool)
    if not pool:
        return []
    if count and count > 0:
        if len(pool) >= count:
            return pool[:count]
        # 부족하면 중복 허용
        return [random.choice(pool) for _ in range(count)]
    return pool


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


# ─────────────────────────────────────────────────────────────
# agent_commands / agent_configs / agent_heartbeats (에이전트 모드)
# ─────────────────────────────────────────────────────────────

def fetch_pending_stop_commands(program_username: str, limit=20, log=None):
    """
    status='pending' 이면서 command='stop' 인 row들 조회 (최우선 처리용).
    Returns: [{"id", "command", ...}, ...] (빈 리스트 가능)
    """
    _log = log or print
    try:
        client = _get_service_client()
        r = (
            client.table("agent_commands")
            .select("id, command, payload, created_at")
            .eq("program_username", program_username)
            .eq("status", "pending")
            .eq("command", "stop")
            .order("created_at", desc=False)
            .limit(limit)
            .execute()
        )
        rows = []
        if r.data:
            for raw in r.data:
                row = dict(raw)
                row["command"] = "stop"
                row["payload"] = row.get("payload") or {}
                rows.append(row)
        return rows
    except Exception as e:
        _log(f"[Supabase] agent_commands stop 조회 실패: {e}")
        return []


def fetch_pending_agent_commands(program_username: str, limit=20, exclude_stop=False, log=None):
    """
    agent_commands에서 status='pending'인 명령을 created_at asc로 limit건 조회.
    exclude_stop=True: (A)에서 stop 처리했으므로 stop 제외.
    Returns: [{"id", "command", "payload", ...}, ...] (빈 리스트 가능)
    """
    _log = log or print
    try:
        client = _get_service_client()
        q = (
            client.table("agent_commands")
            .select("id, command, payload, created_at")
            .eq("program_username", program_username)
            .eq("status", "pending")
            .order("created_at", desc=False)
            .limit(limit)
        )
        if exclude_stop:
            q = q.neq("command", "stop")
        r = q.execute()
        rows = []
        if r.data:
            for raw in r.data:
                row = dict(raw)
                cmd = row.get("command")
                # 신규: command=문자열, payload=별도 컬럼
                if isinstance(cmd, str):
                    row["command"] = cmd
                    row["payload"] = row.get("payload") or {}
                # 구버전: command에 {command, payload} JSON 저장
                elif isinstance(cmd, dict):
                    row["command"] = cmd.get("command")
                    row["payload"] = cmd.get("payload") or {}
                else:
                    row["command"] = str(cmd) if cmd else ""
                    row["payload"] = row.get("payload") or {}
                rows.append(row)
        return rows
    except Exception as e:
        _log(f"[Supabase] agent_commands 조회 실패: {e}")
        return []


def mark_agent_command_done(cmd_id, error_message=None, log=None):
    """agent_commands row를 done으로 업데이트. error_message 있으면 기록"""
    _log = log or print
    try:
        from datetime import datetime, timezone
        client = _get_service_client()
        data = {
            "status": "done",
            "processed_at": datetime.now(timezone.utc).isoformat(),
        }
        if error_message is not None:
            data["error_message"] = str(error_message)[:2000]
        client.table("agent_commands").update(data).eq("id", cmd_id).execute()
        _log(f"[Supabase] agent_commands id={cmd_id} → done" + (f" (error: {(error_message[:80] + '...') if len(error_message) > 80 else error_message})" if error_message else ""))
    except Exception as e:
        _log(f"[Supabase] agent_commands 업데이트 실패: {e}")


def mark_agent_command_error(cmd_id, error_message, log=None):
    """agent_commands row를 status='error'로 업데이트"""
    _log = log or print
    try:
        from datetime import datetime, timezone
        client = _get_service_client()
        data = {
            "status": "error",
            "processed_at": datetime.now(timezone.utc).isoformat(),
            "error_message": str(error_message)[:2000],
        }
        client.table("agent_commands").update(data).eq("id", cmd_id).execute()
        _log(f"[Supabase] agent_commands id={cmd_id} → error: {str(error_message)[:80]}")
    except Exception as e:
        _log(f"[Supabase] agent_commands 업데이트 실패: {e}")


def fetch_agent_config(program_username: str, owner_user_id: str = None, log=None):
    """agent_configs에서 config 조회. owner_user_id 있으면 복합키로, 없으면 program_username만으로 조회(구버전 호환)"""
    _log = log or print
    try:
        client = _get_service_client()
        q = client.table("agent_configs").select("config, updated_at").eq("program_username", program_username)
        if owner_user_id:
            q = q.eq("owner_user_id", owner_user_id)
        r = q.execute()
        if r.data and len(r.data) > 0:
            return dict(r.data[0])
        return {}
    except Exception as e:
        _log(f"[Supabase] agent_configs 조회 실패: {e}")
        return {}


def insert_agent_run(program_username: str, status: str, message: str = None, log=None):
    """agent_runs에 start/stop/error 기록 (디버깅용)"""
    _log = log or print
    if status not in ("started", "stopped", "error"):
        return
    try:
        client = _get_service_client()
        payload = {"program_username": program_username, "status": status}
        if message:
            payload["message"] = str(message)[:2000]
        client.table("agent_runs").insert(payload).execute()
        _log(f"[Supabase] agent_runs: {status}" + (f" — {(message[:80] + '...') if len(message) > 80 else message}" if message else ""))
    except Exception as e:
        _log(f"[Supabase] agent_runs insert 실패: {e}")


def agent_heartbeat(program_username: str, log=None):
    """agent_heartbeats에 heartbeat 기록"""
    _log = log or print
    try:
        from datetime import datetime, timezone
        client = _get_service_client()
        client.table("agent_heartbeats").upsert({
            "program_username": program_username,
            "last_heartbeat_at": datetime.now(timezone.utc).isoformat(),
        }, on_conflict="program_username").execute()
    except Exception as e:
        _log(f"[Supabase] agent_heartbeat 실패: {e}")


# ─────────────────────────────────────────────────────────────
# post_logs 테이블 — 포스팅 로그 기록
# ─────────────────────────────────────────────────────────────

def insert_post_log(program_username: str, keyword: str, posting_url: str = None, server_name: str = None, post_type: str = "self", partner_id: str = None, status: str = None, log=None):
    """
    post_logs 테이블에 포스팅 로그를 삽입합니다.

    Args:
        program_username: 프로그램 로그인 사용자명
        keyword: 포스팅 키워드
        posting_url: 포스팅 URL (선택)
        server_name: 서버명 (선택)
        post_type: 글 타입 ('self'|'paid'|'referrer'), 기본값 'self'
        partner_id: 쿠팡 파트너스 아이디(lptag, 예: AF4771282) (선택)
        status: 상태 (예: 'started' — post_logs 테이블에 status 컬럼 필요)
        log: 로그 콜백 (선택)
    """
    _log = log or print
    if post_type not in ("self", "paid", "referrer"):
        post_type = "self"
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        raise RuntimeError("config.py에 SUPABASE_URL / SUPABASE_SERVICE_KEY를 설정하세요.")

    try:
        client = _get_service_client()
        payload = {
            "program_username": program_username,
            "keyword": keyword,
            "posting_url": posting_url,
            "server_name": server_name,
            "post_type": post_type,
            "partner_id": partner_id,
        }
        if status is not None:
            payload["status"] = status
        if OWNER_USER_ID:
            payload["owner_user_id"] = OWNER_USER_ID
        client.table("post_logs").insert(payload).execute()
        _log(f"[Supabase] post_logs 삽입: {program_username} / {keyword}")
    except Exception as e:
        _log(f"[Supabase] post_logs 삽입 실패: {e}")
        raise

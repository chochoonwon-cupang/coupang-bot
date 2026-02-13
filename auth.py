# ============================================================
# 회원가입 / 로그인 / 세션 관리
# ============================================================
# Supabase users 테이블 연동, 비밀번호 해싱, 기기 제한
# ============================================================

import hashlib
import secrets
import json
import os
import uuid
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SESSION_FILE = os.path.join(BASE_DIR, ".auth_session.json")


def _hash_password(password: str) -> str:
    """비밀번호를 salt + SHA256으로 해싱"""
    salt = secrets.token_hex(16)
    h = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return f"{salt}:{h}"


def _verify_password(password: str, stored: str) -> bool:
    """저장된 해시와 비밀번호 검증"""
    if not stored or ":" not in stored:
        return False
    salt, h = stored.split(":", 1)
    computed = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return secrets.compare_digest(computed, h)


def _get_client():
    """Supabase 클라이언트 (service key로 auth 작업)"""
    try:
        from supabase import create_client
    except ImportError:
        raise ImportError("pip install supabase")
    import config
    # service_role key (RLS 우회) - auth 작업용
    key = getattr(config, "SUPABASE_SERVICE_KEY", None) or os.environ.get("SUPABASE_SERVICE_KEY")
    if not key:
        raise ValueError("config.py에 SUPABASE_SERVICE_KEY를 설정하세요. (Supabase Dashboard > Settings > API)")
    return create_client(config.SUPABASE_URL, key)


def register(username: str, password: str, referral_username: str = None, log=None) -> tuple[bool, str]:
    """
    회원가입.
    Returns: (성공여부, 메시지)
    """
    _log = log or print
    username = (username or "").strip()
    password = (password or "").strip()
    referral_username = (referral_username or "").strip() or None

    if not username or len(username) < 2:
        return False, "아이디는 2자 이상이어야 합니다."
    if not password or len(password) < 4:
        return False, "비밀번호는 4자 이상이어야 합니다."

    try:
        client = _get_client()
        # 중복 체크
        r = client.table("users").select("id").eq("username", username).execute()
        if r.data and len(r.data) > 0:
            return False, "이미 사용 중인 아이디입니다."

        free_until = (datetime.utcnow() + timedelta(days=180)).strftime("%Y-%m-%d")  # +6개월
        pw_hash = _hash_password(password)

        row = {
            "username": username,
            "password_hash": pw_hash,
            "max_devices": 5,
            "free_use_until": free_until,
            "referral_count": 0,
            "agreed_to_terms": True,
        }
        if referral_username:
            row["referrer_id"] = referral_username
        client.table("users").insert(row).execute()

        # 추천인 처리
        if referral_username:
            ref = client.table("users").select("id, referral_count").eq("username", referral_username).execute()
            if ref.data and len(ref.data) > 0:
                ref_id = ref.data[0]["id"]
                ref_count = ref.data[0].get("referral_count", 0) or 0
                client.table("users").update({"referral_count": ref_count + 1}).eq("id", ref_id).execute()

        _log(f"[회원가입] 성공: {username}")
        return True, "회원가입이 완료되었습니다. 로그인해주세요."
    except Exception as e:
        _log(f"[회원가입] 오류: {e}")
        return False, str(e)


def login(username: str, password: str, log=None) -> tuple[bool, str, dict]:
    """
    로그인.
    Returns: (성공여부, 메시지, 사용자정보 또는 None)
    """
    _log = log or print
    username = (username or "").strip()
    password = (password or "").strip()
    if not username or not password:
        return False, "아이디와 비밀번호를 입력하세요.", None

    try:
        client = _get_client()
        r = client.table("users").select("*").eq("username", username).execute()
        if not r.data or len(r.data) == 0:
            return False, "아이디 또는 비밀번호가 올바르지 않습니다.", None
        row = r.data[0]
        if not _verify_password(password, row.get("password_hash", "")):
            return False, "아이디 또는 비밀번호가 올바르지 않습니다.", None
        free_until = row.get("free_use_until") or ""
        try:
            from datetime import datetime
            end = datetime.strptime(str(free_until)[:10], "%Y-%m-%d")
            if datetime.utcnow().date() > end.date():
                return False, "사용 가능 기간이 만료되었습니다.", None
        except Exception:
            pass
        user = {
            "id": row.get("id"),
            "username": row.get("username"),
            "max_devices": row.get("max_devices", 5),
            "free_use_until": free_until,
            "coupang_access_key": row.get("coupang_access_key") or "",
            "coupang_secret_key": row.get("coupang_secret_key") or "",
            "referrer_id": (row.get("referrer_id") or "").strip() or None,
        }
        _save_session(user)
        _log(f"[로그인] 성공: {username}")
        return True, "로그인되었습니다.", user
    except Exception as e:
        _log(f"[로그인] 오류: {e}")
        return False, str(e), None


def logout(log=None):
    """로그아웃 - 세션 삭제"""
    if os.path.exists(SESSION_FILE):
        try:
            os.remove(SESSION_FILE)
        except Exception:
            pass
    if log:
        log("[로그아웃] 완료")


def _save_session(user: dict):
    with open(SESSION_FILE, "w", encoding="utf-8") as f:
        json.dump(user, f, ensure_ascii=False, indent=2)


def get_session() -> dict | None:
    """저장된 로그인 세션 반환. 없으면 None"""
    if not os.path.exists(SESSION_FILE):
        return None
    try:
        with open(SESSION_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def is_logged_in() -> bool:
    return get_session() is not None


def get_free_use_until() -> str:
    s = get_session()
    return (s.get("free_use_until") or "")[:10] if s else ""


# ============================================================
# 쿠팡 키 저장 및 active_sessions (기기 제한)
# ============================================================

# 유효한 발행 카테고리 (추천인 distribute_category용)
VALID_CATEGORIES = ("건강식품", "생활용품", "가전제품", "유아/출산", "기타")


def update_distribute_keywords(user_id: str, keywords_str: str, category_str: str = None, log=None) -> tuple[bool, str]:
    """
    추천인 포스팅 발행용 키워드·카테고리를 Supabase users에 저장.
    keywords_str: 콤마(,)로 구분된 키워드 문자열 (한 줄)
    category_str: 발행 카테고리 (유효하지 않으면 '기타')
    Returns: (성공여부, 메시지)
    """
    _log = log or print
    try:
        client = _get_client()
        data = {"distribute_keyword": (keywords_str or "").strip()}
        if category_str is not None:
            raw = (category_str or "").strip()
            data["distribute_category"] = raw if raw in VALID_CATEGORIES else "기타"
        client.table("users").update(data).eq("id", user_id).execute()
        _log("[추천인 키워드·카테고리] 저장 완료")
        return True, "저장되었습니다."
    except Exception as e:
        _log(f"[추천인 키워드] 저장 실패: {e}")
        return False, str(e)


def get_distribute_keywords(user_id: str, log=None) -> str:
    """저장된 distribute_keyword 반환"""
    _log = log or print
    try:
        client = _get_client()
        r = client.table("users").select("distribute_keyword").eq("id", user_id).execute()
        if r.data and len(r.data) > 0:
            return r.data[0].get("distribute_keyword") or ""
    except Exception as e:
        _log(f"[추천인 키워드] 조회 실패: {e}")
    return ""


def get_distribute_category(user_id: str, log=None) -> str:
    """저장된 distribute_category 반환 (유효하지 않으면 '기타')"""
    _log = log or print
    try:
        client = _get_client()
        r = client.table("users").select("distribute_category").eq("id", user_id).execute()
        if r.data and len(r.data) > 0:
            raw = (r.data[0].get("distribute_category") or "").strip()
            return raw if raw in VALID_CATEGORIES else "기타"
    except Exception as e:
        _log(f"[추천인 카테고리] 조회 실패: {e}")
    return "기타"


def save_coupang_keys(user_id: str, access_key: str, secret_key: str, log=None) -> tuple[bool, str]:
    """
    로그인 사용자의 쿠팡 키를 DB에 저장.
    Returns: (성공여부, 메시지)
    """
    _log = log or print
    try:
        client = _get_client()
        client.table("users").update({
            "coupang_access_key": access_key,
            "coupang_secret_key": secret_key,
        }).eq("id", user_id).execute()
        _log("[쿠팡키] 저장 완료")
        return True, "저장됨"
    except Exception as e:
        _log(f"[쿠팡키] 저장 실패: {e}")
        return False, str(e)


def check_device_limit(access_key: str, user_id: str, max_devices: int, log=None) -> tuple[bool, str]:
    """
    해당 Access Key 사용 중인 active_sessions 수가 max_devices 초과인지 확인.
    Returns: (허용여부, 메시지)
    """
    _log = log or print
    if not access_key or not user_id:
        return False, "쿠팡 API 키를 입력하세요."
    try:
        client = _get_client()
        r = client.table("active_sessions").select("id").eq("coupang_access_key", access_key).execute()
        count = len(r.data) if r.data else 0
        if count >= max_devices:
            return False, f"실행 허용 대수 초과 (최대 {max_devices}대)"
        return True, ""
    except Exception as e:
        _log(f"[기기체크] 오류: {e}")
        return True, ""  # 오류 시 일단 허용


def add_active_session(user_id: str, access_key: str, secret_key: str, log=None) -> tuple[bool, str]:
    """
    실행 시작 시 active_sessions에 세션 추가.
    Returns: (성공여부, 메시지)
    """
    _log = log or print
    try:
        client = _get_client()
        sid = str(uuid.uuid4())
        client.table("active_sessions").insert({
            "id": sid,
            "user_id": user_id,
            "coupang_access_key": access_key,
            "coupang_secret_key": secret_key,
            "created_at": datetime.utcnow().isoformat(),
        }).execute()
        return True, sid
    except Exception as e:
        _log(f"[세션추가] 오류: {e}")
        return False, str(e)


def remove_active_session(session_id: str, log=None):
    """실행 종료/앱 종료 시 세션 제거"""
    if not session_id:
        return
    _log = log or print
    try:
        client = _get_client()
        client.table("active_sessions").delete().eq("id", session_id).execute()
    except Exception as e:
        _log(f"[세션제거] 오류: {e}")

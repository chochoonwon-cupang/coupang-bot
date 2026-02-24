# ============================================================
# 쿠팡 파트너스 봇 - 설정 파일
# ============================================================
# 각 API 키를 본인의 키로 교체하세요.
# 실서비스에서는 .env 파일이나 환경변수로 관리하는 것을 권장합니다.
# ============================================================

import os

# ── SaaS 소유자 UID (post_logs.owner_user_id) ──
# Supabase auth.uid() 또는 users.id 값. 환경변수 OWNER_USER_ID 또는 config.json
_owner = os.getenv("OWNER_USER_ID", "")
if not _owner:
    try:
        import json
        _cfg = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
        if os.path.isfile(_cfg):
            with open(_cfg, "r", encoding="utf-8") as f:
                _owner = (json.load(f) or {}).get("OWNER_USER_ID", "") or ""
    except Exception:
        pass
OWNER_USER_ID = (_owner or "").strip()

# ── 쿠팡 파트너스 API ──
# GUI에서 사용자가 직접 입력합니다.
ACCESS_KEY = ""
SECRET_KEY = ""

# ── Google Gemini API ──
# https://aistudio.google.com/app/apikey 에서 발급
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"

# ── Bitly 단축 링크 API ──
# https://app.bitly.com/settings/api/ 에서 발급
BITLY_ACCESS_TOKEN = "YOUR_BITLY_ACCESS_TOKEN"

# ── 커스텀 리다이렉트 도메인 ──
# 가비아+Vercel 연결된 리다이렉트 주소
REDIRECT_BASE_URL = "https://go.kdgc.co.kr/go"

# ── Supabase (유료회원 데이터 서버) ──
# Supabase 프로젝트 대시보드 → Settings → API 에서 확인
SUPABASE_URL      = "https://vdyliufqshfdhvjshdfa.supabase.co"   # 예: "https://xxxx.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZkeWxpdWZxc2hmZGh2anNoZGZhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzA3MDg1NDMsImV4cCI6MjA4NjI4NDU0M30.JIiDmwFXx1gJ4jaYs8wfhoKpO9JKyga1v0YRg2CgEMk"   # 예: "eyJhbGciOi..."
# 회원가입/로그인용 (RLS 우회) — Settings > API > service_role key
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZkeWxpdWZxc2hmZGh2anNoZGZhIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MDcwODU0MywiZXhwIjoyMDg2Mjg0NTQzfQ.7TBA_6bh66GMIuGlD6UYn5R4tzQfv4nl2GjDsy7w1cU"   # service_role key 입력 (auth.py에서 사용)

# ── 기본 설정 ──
IMAGE_SAVE_DIR = "images"           # 이미지 저장 폴더
DEFAULT_SEARCH_LIMIT = 5            # 기본 검색 결과 수

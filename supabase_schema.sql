-- ============================================================
-- 쿠팡 봇 회원/세션 테이블 (Supabase)
-- ============================================================
-- Supabase SQL Editor에서 실행
-- ============================================================

-- users 테이블
CREATE TABLE IF NOT EXISTS users (
    id          UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    username    TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    max_devices INTEGER DEFAULT 5,
    free_use_until DATE NOT NULL,
    referral_count INTEGER DEFAULT 0,
    coupang_access_key TEXT,
    coupang_secret_key TEXT,
    distribute_keyword  TEXT,
    distribute_category TEXT DEFAULT '기타',
    agreed_to_terms     BOOLEAN DEFAULT FALSE,
    created_at  TIMESTAMPTZ DEFAULT now()
);

-- 기존 users 테이블에 컬럼이 없다면 실행:
-- ALTER TABLE users ADD COLUMN IF NOT EXISTS distribute_keyword TEXT;
-- ALTER TABLE users ADD COLUMN IF NOT EXISTS distribute_category TEXT DEFAULT '기타';
-- ALTER TABLE users ADD COLUMN IF NOT EXISTS agreed_to_terms BOOLEAN DEFAULT FALSE;
-- ALTER TABLE users ADD COLUMN IF NOT EXISTS referrer_id TEXT;  -- 추천인 username (회원가입 시 추천인 코드)
-- 위 ALTER를 Supabase SQL Editor에서 실행하여 referrer_id 컬럼을 추가하세요.

-- RLS (필요시)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
-- service_role이면 RLS 우회됨

-- active_sessions 테이블 (동시 실행 기기 추적)
CREATE TABLE IF NOT EXISTS active_sessions (
    id                  UUID PRIMARY KEY,
    user_id             UUID REFERENCES users(id) ON DELETE CASCADE,
    coupang_access_key  TEXT NOT NULL,
    coupang_secret_key  TEXT,
    created_at          TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_active_sessions_access_key ON active_sessions(coupang_access_key);
CREATE INDEX IF NOT EXISTS idx_active_sessions_user_id ON active_sessions(user_id);

-- RLS
ALTER TABLE active_sessions ENABLE ROW LEVEL SECURITY;

-- paid_members 테이블 (유료회원 교차발행)
CREATE TABLE IF NOT EXISTS paid_members (
    id                  UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name                TEXT NOT NULL,
    keywords            TEXT NOT NULL,
    category            TEXT DEFAULT '기타',
    coupang_access_key  TEXT NOT NULL,
    coupang_secret_key  TEXT NOT NULL,
    active              BOOLEAN DEFAULT TRUE,
    created_at          TIMESTAMPTZ DEFAULT now()
);

-- 기존 paid_members 테이블에 category 컬럼이 없다면 실행:
-- ALTER TABLE paid_members ADD COLUMN IF NOT EXISTS category TEXT DEFAULT '기타';

ALTER TABLE paid_members ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow anon read" ON paid_members FOR SELECT USING (true);

-- banned_brands 테이블 (쿠팡 활동금지 업체/브랜드)
CREATE TABLE IF NOT EXISTS banned_brands (
    id          UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    brand_name  TEXT NOT NULL UNIQUE,
    created_at  TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE banned_brands ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow anon read banned_brands" ON banned_brands FOR SELECT USING (true);

-- 활동금지 브랜드 등록 예시:
-- INSERT INTO banned_brands (brand_name) VALUES ('락토핏'), ('종근당'), ('업체명');

-- app_links 테이블 (문의접수, 프로그램사용방법영상, 하단배너 링크)
CREATE TABLE IF NOT EXISTS app_links (
    id          UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    link_key    TEXT NOT NULL UNIQUE,
    url         TEXT NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE app_links ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow anon read app_links" ON app_links FOR SELECT USING (true);

-- 앱 링크 등록 예시 (Supabase SQL Editor에서 실행):
-- INSERT INTO app_links (link_key, url) VALUES
--   ('inquiry', 'https://open.kakao.com/o/xxx'),
--   ('tutorial_video', 'https://www.youtube.com/watch?v=xxx'),
--   ('banner', 'https://posting-webna.vercel.app/')
-- ON CONFLICT (link_key) DO UPDATE SET url = EXCLUDED.url;

-- banners 테이블 (하단 배너 여러 개 등록 → 1분마다 랜덤 노출)
CREATE TABLE IF NOT EXISTS banners (
    id          UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    main_text   TEXT NOT NULL,
    sub_text    TEXT NOT NULL,
    url         TEXT NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE banners ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow anon read banners" ON banners FOR SELECT USING (true);

-- 배너 등록 예시:
-- INSERT INTO banners (main_text, sub_text, url) VALUES
--   ('월 30만원으로 채용하는 AI 광고직원을 아시나요?', '24시간 쉬지 않고 사장님 대신 포스팅하는 스마트 비서 서비스', 'https://posting-webna.vercel.app/'),
--   ('두 번째 배너 문구', '두 번째 배너 설명', 'https://example.com');

-- helper_cafes 테이블 (도우미 기본 카페리스트 — 서버 저장)
-- 카페 주소로 가입 시 사용, cafe_id/menu_id는 포스팅 등록 시 사용
CREATE TABLE IF NOT EXISTS helper_cafes (
    id          UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    cafe_url    TEXT NOT NULL,
    cafe_id     TEXT NOT NULL,
    menu_id     TEXT NOT NULL,
    sort_order  INTEGER DEFAULT 0,
    created_at  TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE helper_cafes ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow anon read helper_cafes" ON helper_cafes FOR SELECT USING (true);

-- 도우미 카페 등록 예시 (cafe_url: 가입용, cafe_id/menu_id: 포스팅용):
-- INSERT INTO helper_cafes (cafe_url, cafe_id, menu_id, sort_order) VALUES
--   ('https://cafe.naver.com/myclub', '12345678', '2', 0);

-- tasks 테이블 (SaaS 에이전트 모드 — pending/processing/completed/failed)
CREATE TABLE IF NOT EXISTS tasks (
    id            UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    keyword       TEXT NOT NULL,
    status        TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed', '대기', '진행', '완료')),
    result_url    TEXT,
    error_message TEXT,
    created_at    TIMESTAMPTZ DEFAULT now(),
    updated_at    TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at);

ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
-- 에이전트가 읽기/수정하려면 service_role 사용 (RLS 우회)

-- 기존 테이블에 error_message 컬럼 추가 (이미 있으면 무시):
-- ALTER TABLE tasks ADD COLUMN IF NOT EXISTS error_message TEXT;
-- 기존 status 제약 변경 (Supabase SQL Editor에서 실행):
-- ALTER TABLE tasks DROP CONSTRAINT IF EXISTS tasks_status_check;
-- ALTER TABLE tasks ADD CONSTRAINT tasks_status_check CHECK (status IN ('pending', 'processing', 'completed', 'failed', '대기', '진행', '완료'));
-- ALTER TABLE tasks ALTER COLUMN status SET DEFAULT 'pending';

-- 작업 등록 예시:
-- INSERT INTO tasks (keyword, status) VALUES ('무선청소기', 'pending');

-- 캡챠 API 키 (app_links에 저장, link_key='captcha_api_key')
-- INSERT INTO app_links (link_key, url) VALUES ('captcha_api_key', 'YOUR_CAPTCHA_API_KEY')
-- ON CONFLICT (link_key) DO UPDATE SET url = EXCLUDED.url;

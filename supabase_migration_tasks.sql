-- Supabase SQL Editor에서 실행: 기존 tasks 테이블을 새 스키마로 마이그레이션
-- (이미 새 스키마라면 일부만 실행해도 됨)

-- 1. error_message 컬럼 추가
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS error_message TEXT;

-- 2. 기존 status 제약 제거 후 새 제약 추가
ALTER TABLE tasks DROP CONSTRAINT IF EXISTS tasks_status_check;
ALTER TABLE tasks ADD CONSTRAINT tasks_status_check 
  CHECK (status IN ('pending', 'processing', 'completed', 'failed', '대기', '진행', '완료'));

-- 3. 기본값을 pending으로 변경 (선택)
ALTER TABLE tasks ALTER COLUMN status SET DEFAULT 'pending';

-- 4. 기존 한글 status를 영문으로 변환 (선택)
-- UPDATE tasks SET status = 'pending' WHERE status = '대기';
-- UPDATE tasks SET status = 'processing' WHERE status = '진행';
-- UPDATE tasks SET status = 'completed' WHERE status = '완료';

-- ============================================================
-- cafe_join_policy: search_keyword, start_time 컬럼 추가
-- Supabase SQL Editor에서 실행
-- ============================================================
ALTER TABLE cafe_join_policy ADD COLUMN IF NOT EXISTS search_keyword TEXT DEFAULT '';
ALTER TABLE cafe_join_policy ADD COLUMN IF NOT EXISTS start_time TEXT DEFAULT '09:00';

-- ============================================================
-- agent_cafe_lists: reject_reason 컬럼 추가 (가입 실패 사유 저장)
-- Supabase SQL Editor에서 실행
-- ============================================================
ALTER TABLE agent_cafe_lists ADD COLUMN IF NOT EXISTS reject_reason TEXT;

-- ============================================================
-- users: 쿠팡 API 키 컬럼 (SaaS 쿠팡API 탭에서 저장 시 사용)
-- Supabase SQL Editor에서 실행
-- ============================================================
ALTER TABLE users ADD COLUMN IF NOT EXISTS coupang_access_key TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS coupang_secret_key TEXT;

# 로그인 시스템 설정 가이드

## 1. Supabase 테이블 생성

`supabase_schema.sql` 파일을 Supabase SQL Editor에서 실행하세요.

```sql
-- users, active_sessions 테이블 생성
```

## 2. config.py 설정

`config.py`에 **SUPABASE_SERVICE_KEY**를 추가하세요.
- Supabase Dashboard → Settings → API → `service_role` key (secret) 복사

```python
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

## 3. 동작 요약

- **회원가입**: 아이디, 비밀번호, 추천인(선택) → 비밀번호 해싱 저장, free_use_until +6개월
- **로그인**: 세션 저장 (.auth_session.json)
- **실행 차단**: 로그인 없으면 "로그인이 필요합니다"
- **기간 만료**: free_use_until 지나면 실행 차단
- **쿠팡 키**: 첫 실행 시 자동 저장
- **기기 제한**: 동일 Access Key로 max_devices(기본 5대) 초과 시 "실행 허용 대수 초과"

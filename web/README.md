# 포스팅 작업 관리 웹

Next.js + Tailwind CSS로 만든 키워드 발행 대시보드입니다.

## 기능

- **입력창**: 포스팅할 키워드 입력
- **발행 버튼**: 클릭 시 Supabase `tasks` 테이블에 새 작업 등록
- **상태 테이블**: 대기 / 진행 중 / 완료 실시간 표시 (3초마다 갱신)

## 설정

1. `.env.local` 파일 생성 (또는 `.env.local.example` 복사):

```
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key
```

2. `config.py`의 Supabase URL과 service_role 키를 그대로 사용하세요.

## 실행

```bash
npm run dev
```

http://localhost:3000 에서 확인

## 배포 (Vercel)

Vercel에 배포 시 환경 변수 `NEXT_PUBLIC_SUPABASE_URL`, `SUPABASE_SERVICE_KEY`를 설정하세요.

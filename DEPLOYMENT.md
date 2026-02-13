# Vercel 배포 가이드

## 404 에러 해결 방법

웹 앱 소스 코드가 `web/` 폴더에 있으므로, Vercel에서 **Root Directory**를 반드시 설정해야 합니다.

### 설정 방법

1. [Vercel 대시보드](https://vercel.com/dashboard) 접속
2. 프로젝트 선택 → **Settings** 탭
3. **General** → **Build and Development Settings**
4. **Root Directory**를 `web`으로 설정 (또는 `web` 입력 후 **Edit** → **Save**)
5. **Redeploy** 실행

### Root Directory를 설정하지 않으면

- Vercel이 프로젝트 루트(`coupang_bot`)를 기준으로 빌드
- `web/` 안의 Next.js 앱을 인식하지 못함
- 404 에러 발생

### Root Directory를 `web`으로 설정하면

- Vercel이 `web/` 폴더를 프로젝트 루트로 인식
- `package.json`, `next.config.ts`를 올바르게 찾음
- 정상 배포됨

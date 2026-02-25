"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import SubNav from "./SubNav";
import FloatingHelpBanner from "./FloatingHelpBanner";
import AutoPostingInfoModal from "./AutoPostingInfoModal";

type User = { id: string; username: string; managed_usernames?: string[] } | null;

const TERMS_TEXT = `제1조 (목적)
본 약관은 '포스팅 도우미'(이하 "프로그램") 개발자(이하 "판매자")가 제공하는 소프트웨어의 이용 조건 및 절차, 판매자와 이용자(이하 "회원") 간의 권리, 의무 및 책임 사항을 규정함을 목적으로 합니다.

제2조 (서비스 이용 및 승인)
회원은 본 약관에 동의하고 회원가입을 완료함으로써 서비스를 이용할 수 있습니다.

• 라이선스 관리: 본 프로그램은 쿠팡 Access Key를 기준으로 실행 대수를 제한하며, 회원은 본인 소유의 유효한 키를 사용해야 합니다.

• 무료 사용 기간: 가입 시점으로부터 6개월간 무료 이용 권한이 부여되며, 기간 만료 후에는 서비스가 제한될 수 있습니다.

제3조 (회원의 의무 및 금지사항)
회원은 본 프로그램을 마케팅 보조 용도로만 사용해야 하며, 플랫폼(네이버, 쿠팡 등)의 가이드라인을 준수할 책임이 있습니다.

• 비정상적 이용 금지: 플랫폼 서버에 과도한 부하를 주거나, 타인의 계정을 도용하여 포스팅하는 등 비정상적인 방법으로 시스템에 접근하는 행위를 금지합니다.

• 재판매 금지: 회원은 구매한 프로그램을 무단 복제, 분해, 재판매하거나 제3자에게 배포할 수 없습니다.

제4조 (개인정보 수집 및 보안)
판매자는 서비스 제공 및 라이선스 확인을 위해 아이디, 비밀번호, 쿠팡 API 키 정보를 수집 및 저장합니다.

수집된 정보는 실행 대수 확인 및 서비스 운영 목적으로만 사용되며, 회원의 명시적 동의 없이 제3자에게 제공되지 않습니다.

제5조 (면책조항 및 책임의 제한) - 중요
• 플랫폼 제재 관련: 본 프로그램은 자동화 툴로서, 네이버 및 쿠팡의 운영 정책에 따라 게시글 삭제, 검색 노출 제한, 계정 정지 등의 불이익을 받을 수 있습니다. 판매자는 플랫폼의 정책 변화로 인해 발생하는 어떠한 유무형의 손해에 대해서도 책임을 지지 않습니다.

• 수익 보장 불가: 본 프로그램은 포스팅을 돕는 도구일 뿐이며, 이를 통한 수익 발생이나 검색 순위 상위 노출을 보장하지 않습니다.

• 서비스 중단: 플랫폼의 API 변경, 서버 점검, 천재지변 등으로 인해 서비스가 일시적 또는 영구적으로 중단될 수 있으며, 이로 인한 보상 책임은 없습니다.

• 콘텐츠 책임: 프로그램을 통해 발행되는 콘텐츠의 저작권 및 내용에 대한 모든 책임은 회원 본인에게 있습니다.`;

export default function AppShell({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User>(null);
  const [sessionLoading, setSessionLoading] = useState(true);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [loginUsername, setLoginUsername] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [loginLoading, setLoginLoading] = useState(false);
  const [loginError, setLoginError] = useState<string | null>(null);
  const [showRegisterModal, setShowRegisterModal] = useState(false);
  const [regUsername, setRegUsername] = useState("");
  const [regPassword, setRegPassword] = useState("");
  const [regReferrer, setRegReferrer] = useState("");
  const [regAgreed, setRegAgreed] = useState(false);
  const [regError, setRegError] = useState<string | null>(null);
  const [regLoading, setRegLoading] = useState(false);
  const [showTermsModal, setShowTermsModal] = useState(false);
  const [showInfoModal, setShowInfoModal] = useState(false);

  const checkSession = useCallback(async () => {
    try {
      const res = await fetch("/api/auth/session");
      const data = await res.json();
      const u = data.ok ? data.user : null;
      setUser(u);
    } catch {
      setUser(null);
    } finally {
      setSessionLoading(false);
    }
  }, []);

  useEffect(() => {
    checkSession();
  }, [checkSession]);

  useEffect(() => {
    const handler = () => setShowLoginModal(true);
    window.addEventListener("open-login-modal", handler);
    return () => window.removeEventListener("open-login-modal", handler);
  }, []);

  const handleLogin = async () => {
    const u = loginUsername.trim();
    const p = loginPassword.trim();
    if (!u || !p) {
      setLoginError("아이디와 비밀번호를 입력하세요.");
      return;
    }
    setLoginLoading(true);
    setLoginError(null);
    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: u, password: p }),
      });
      const contentType = res.headers.get("content-type");
      let data: { error?: string; user?: User; ok?: boolean };
      if (contentType?.includes("application/json")) {
        data = await res.json();
      } else {
        const text = await res.text();
        throw new Error(
          "서버 오류가 발생했습니다. .env.local에 SUPABASE_URL, SUPABASE_SERVICE_KEY를 설정한 뒤 서버를 재시작하세요."
        );
      }
      if (!res.ok) throw new Error(data.error || "로그인 실패");
      setUser(data.user || null);
      setShowLoginModal(false);
      checkSession();
      setLoginUsername("");
      setLoginPassword("");
      window.dispatchEvent(new CustomEvent("auth-changed"));
    } catch (e) {
      setLoginError(e instanceof Error ? e.message : "로그인에 실패했습니다.");
    } finally {
      setLoginLoading(false);
    }
  };

  const handleRegister = async () => {
    const u = regUsername.trim();
    const p = regPassword.trim();
    if (!u || u.length < 2) {
      setRegError("아이디는 2자 이상이어야 합니다.");
      return;
    }
    if (!p || p.length < 4) {
      setRegError("비밀번호는 4자 이상이어야 합니다.");
      return;
    }
    if (!regAgreed) {
      setRegError("이용약관에 동의해주세요.");
      return;
    }
    setRegLoading(true);
    setRegError(null);
    try {
      const res = await fetch("/api/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: u,
          password: p,
          referrer_id: regReferrer.trim() || undefined,
          agreed_to_terms: true,
        }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.error || "회원가입 실패");
      setShowRegisterModal(false);
      setRegUsername("");
      setRegPassword("");
      setRegReferrer("");
      setRegAgreed(false);
      setShowLoginModal(true);
      setLoginUsername(u);
      alert("회원가입이 완료되었습니다. 로그인해주세요.");
    } catch (e) {
      setRegError(e instanceof Error ? e.message : "회원가입에 실패했습니다.");
    } finally {
      setRegLoading(false);
    }
  };

  const handleLogout = async () => {
    await fetch("/api/auth/logout", { method: "POST" });
    setUser(null);
    window.dispatchEvent(new CustomEvent("auth-changed"));
  };

  return (
    <>
      <header className="sticky top-0 z-50 border-b border-slate-700/60 bg-slate-900/80 backdrop-blur">
        <div className="mx-auto max-w-6xl px-4 py-3 md:px-8 md:py-4">
          <div className="flex items-center justify-between gap-2">
            <Link
              href="/"
              className="flex min-w-0 shrink cursor-pointer items-center gap-2 rounded-lg border-0 bg-transparent p-0 text-left transition hover:opacity-90 sm:gap-3"
            >
              <span className="flex shrink-0 items-baseline text-base font-bold tracking-tight sm:text-lg md:text-2xl" aria-hidden>
                <span className="text-[#E04A2A]">c</span>
                <span className="text-[#F59E0B]">o</span>
                <span className="text-[#EAB308]">u</span>
                <span className="text-[#22C55E]">p</span>
                <span className="text-[#0EA5E9]">a</span>
                <span className="text-[#6366F1]">n</span>
                <span className="text-[#A855F7]">g</span>
              </span>
              <span className="hidden h-5 w-px shrink-0 bg-slate-600 sm:block" aria-hidden />
              <h1 className="min-w-0 truncate text-sm font-bold text-white sm:text-base md:text-xl">
                <span className="hidden sm:inline">쿠팡파트너스 자동포스팅 시스템</span>
                <span className="sm:hidden">자동포스팅</span>
              </h1>
            </Link>
            <div className="flex shrink-0 items-center gap-2 md:gap-4">
              {sessionLoading ? (
                <span className="text-xs text-slate-400 md:text-sm">확인 중...</span>
              ) : user ? (
                <>
                  <span className="text-xs text-slate-300 md:text-sm">{user.username}님</span>
                  <button
                    onClick={handleLogout}
                    className="rounded-lg border border-slate-600 bg-slate-800/80 px-3 py-1.5 text-xs font-medium text-slate-300 transition hover:bg-slate-700 hover:text-white md:px-4 md:py-2 md:text-sm"
                  >
                    로그아웃
                  </button>
                </>
              ) : (
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setShowLoginModal(true)}
                    className="rounded-lg bg-indigo-600 px-4 py-2 text-xs font-semibold text-white transition hover:bg-indigo-500 md:px-5 md:py-2.5 md:text-sm"
                  >
                    로그인
                  </button>
                  <button
                    onClick={() => setShowRegisterModal(true)}
                    className="rounded-lg border border-slate-600 bg-slate-800/80 px-4 py-2 text-xs font-semibold text-slate-300 transition hover:bg-slate-700 hover:text-white md:px-5 md:py-2.5 md:text-sm"
                  >
                    회원가입
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      <SubNav />

      {children}

      <FloatingHelpBanner
        onGuideClick={() => setShowInfoModal(true)}
      />
      <AutoPostingInfoModal
        isOpen={showInfoModal}
        onClose={() => setShowInfoModal(false)}
        onStart={() => {
          if (!user) setShowLoginModal(true);
        }}
      />

      {/* 로그인 모달 */}
      {showLoginModal && (
        <div
          className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
          onClick={() => !loginLoading && setShowLoginModal(false)}
        >
          <div
            className="w-full max-w-sm rounded-2xl border border-slate-700/60 bg-slate-800/95 p-6 shadow-xl md:p-8"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 className="mb-4 text-lg font-bold text-white md:mb-6 md:text-xl">로그인</h2>
            <p className="mb-3 text-sm text-slate-400 md:mb-4">
              메인 프로그램과 동일한 아이디/비밀번호를 입력하세요.
            </p>
            <input
              type="text"
              value={loginUsername}
              onChange={(e) => setLoginUsername(e.target.value)}
              placeholder="아이디"
              className="mb-3 w-full rounded-xl border border-slate-600 bg-slate-800/80 px-4 py-3 text-sm text-slate-100 placeholder-slate-500 outline-none focus:border-indigo-500 md:text-base"
              autoFocus
            />
            <input
              type="password"
              value={loginPassword}
              onChange={(e) => setLoginPassword(e.target.value)}
              placeholder="비밀번호"
              onKeyDown={(e) => e.key === "Enter" && handleLogin()}
              className="mb-4 w-full rounded-xl border border-slate-600 bg-slate-800/80 px-4 py-3 text-sm text-slate-100 placeholder-slate-500 outline-none focus:border-indigo-500 md:text-base"
            />
            {loginError && (
              <p className="mb-4 text-sm text-rose-400">{loginError}</p>
            )}
            <div className="flex flex-col gap-2 sm:flex-row sm:gap-3">
              <button
                onClick={handleLogin}
                disabled={loginLoading}
                className="flex-1 rounded-xl bg-indigo-600 py-3 text-sm font-semibold text-white transition hover:bg-indigo-500 disabled:opacity-50 md:text-base"
              >
                {loginLoading ? "로그인 중..." : "로그인"}
              </button>
              <button
                onClick={() => !loginLoading && setShowLoginModal(false)}
                disabled={loginLoading}
                className="rounded-xl border border-slate-600 bg-slate-800/80 px-6 py-3 text-sm text-slate-300 transition hover:bg-slate-700 disabled:opacity-50 md:text-base"
              >
                취소
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 회원가입 모달 */}
      {showRegisterModal && (
        <div
          className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
          onClick={() => !regLoading && setShowRegisterModal(false)}
        >
          <div
            className="w-full max-w-sm rounded-2xl border border-slate-700/60 bg-slate-800/95 p-6 shadow-xl md:p-8"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 className="mb-4 text-lg font-bold text-white md:mb-6 md:text-xl">회원가입</h2>
            <p className="mb-3 text-sm text-slate-400 md:mb-4">
              프로그램과 동일한 아이디/비밀번호로 가입하세요.
            </p>
            <input
              type="text"
              value={regUsername}
              onChange={(e) => setRegUsername(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleRegister()}
              placeholder="아이디"
              className="mb-3 w-full rounded-xl border border-slate-600 bg-slate-800/80 px-4 py-3 text-sm text-slate-100 placeholder-slate-500 outline-none focus:border-indigo-500 md:text-base"
              autoFocus
            />
            <input
              type="password"
              value={regPassword}
              onChange={(e) => setRegPassword(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleRegister()}
              placeholder="비밀번호"
              className="mb-3 w-full rounded-xl border border-slate-600 bg-slate-800/80 px-4 py-3 text-sm text-slate-100 placeholder-slate-500 outline-none focus:border-indigo-500 md:text-base"
            />
            <input
              type="text"
              value={regReferrer}
              onChange={(e) => setRegReferrer(e.target.value)}
              placeholder="추천인 아이디 (선택)"
              onKeyDown={(e) => e.key === "Enter" && handleRegister()}
              className="mb-4 w-full rounded-xl border border-slate-600 bg-slate-800/80 px-4 py-3 text-sm text-slate-100 placeholder-slate-500 outline-none focus:border-indigo-500 md:text-base"
            />
            <div className="mb-4 flex flex-wrap items-center gap-2">
              <label className="flex cursor-pointer items-center gap-2 text-sm text-slate-300">
                <input
                  type="checkbox"
                  checked={regAgreed}
                  onChange={(e) => setRegAgreed(e.target.checked)}
                  className="rounded border-slate-600 bg-slate-800 text-indigo-500 focus:ring-indigo-500"
                />
                이용약관 및 면책고지 사항을 확인하였으며 이에 동의합니다
              </label>
              <button
                type="button"
                onClick={() => setShowTermsModal(true)}
                className="text-xs text-indigo-400 underline hover:text-indigo-300"
              >
                [약관 보기]
              </button>
            </div>
            {regError && (
              <p className="mb-4 text-sm text-rose-400">{regError}</p>
            )}
            <div className="flex flex-col gap-2 sm:flex-row sm:gap-3">
              <button
                onClick={handleRegister}
                disabled={regLoading || !regAgreed}
                className="flex-1 rounded-xl bg-indigo-600 py-3 text-sm font-semibold text-white transition hover:bg-indigo-500 disabled:opacity-50 md:text-base"
              >
                {regLoading ? "가입 중..." : "가입하기"}
              </button>
              <button
                onClick={() => !regLoading && setShowRegisterModal(false)}
                disabled={regLoading}
                className="rounded-xl border border-slate-600 bg-slate-800/80 px-6 py-3 text-sm text-slate-300 transition hover:bg-slate-700 disabled:opacity-50 md:text-base"
              >
                취소
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 약관 보기 모달 */}
      {showTermsModal && (
        <div
          className="fixed inset-0 z-[110] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
          onClick={() => setShowTermsModal(false)}
        >
          <div
            className="max-h-[85vh] w-full max-w-lg overflow-hidden rounded-2xl border border-slate-700/60 bg-slate-800/95 shadow-xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="border-b border-slate-700/60 p-4">
              <h3 className="text-lg font-bold text-white">이용약관 및 면책고지</h3>
            </div>
            <div className="max-h-[50vh] overflow-y-auto p-4 text-sm leading-relaxed text-slate-300 whitespace-pre-wrap">
              {TERMS_TEXT}
            </div>
            <div className="border-t border-slate-700/60 p-4">
              <button
                onClick={() => setShowTermsModal(false)}
                className="rounded-xl bg-slate-600 px-6 py-2 text-sm font-medium text-white transition hover:bg-slate-500"
              >
                닫기
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

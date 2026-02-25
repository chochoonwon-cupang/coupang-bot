"use client";

import { useState, useEffect, useCallback } from "react";

type PostLog = {
  id: string;
  keyword: string;
  post_type: string;
  partner_id: string | null;
  status: string;
  posting_url: string | null;
  created_at: string;
};

function postTypeLabel(pt: string): string {
  if (pt === "paid") return "유료회원";
  if (pt === "referrer") return "추천인";
  return "본인";
}

function getLinkLabel(url?: string | null): string | null {
  if (!url) return null;
  const u = url.toLowerCase();
  if (u.includes("cafe.naver.com")) return "CAFE";
  if (u.includes("blog.naver.com") || u.includes("m.blog.naver.com")) return "BLOG";
  return null;
}

type User = { id: string; username: string; managed_usernames?: string[] } | null;

function computeStatus(lastJobAt: string | null): { label: string; dot: string } {
  if (!lastJobAt) return { label: "서버체크", dot: "red" };
  const diffMs = Date.now() - new Date(lastJobAt).getTime();
  const diffH = diffMs / 1000 / 60 / 60;
  if (diffH <= 1) return { label: "작업중", dot: "green" };
  if (diffH <= 6) return { label: "작업확인", dot: "orange" };
  if (diffH > 24) return { label: "서버체크", dot: "red" };
  return { label: "작업확인", dot: "orange" };
}

function formatKST(iso: string) {
  return new Intl.DateTimeFormat("ko-KR", {
    timeZone: "Asia/Seoul",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).format(new Date(iso));
}

const POST_LOGS_PER_PAGE = 9;

function isTodayKST(iso: string): boolean {
  const d = new Date(iso);
  const kst = new Date(d.toLocaleString("en-US", { timeZone: "Asia/Seoul" }));
  const nowKst = new Date(new Date().toLocaleString("en-US", { timeZone: "Asia/Seoul" }));
  return kst.getFullYear() === nowKst.getFullYear() && kst.getMonth() === nowKst.getMonth() && kst.getDate() === nowKst.getDate();
}

type CafeJoinPolicy = {
  run_days: number[];
  start_time: string;
  created_year_min: number;
  created_year_max: number;
  recent_post_days: number;
  recent_post_enabled: boolean;
  target_count: number;
  search_keyword: string;
};

function expandDigitsToDays(digits: number[]): number[] {
  const set = new Set<number>();
  for (const d of digits) {
    if (d === 0) set.add(10).add(20).add(30);
    else if (d >= 1 && d <= 9) set.add(d).add(10 + d).add(20 + d);
  }
  return [...set].sort((a, b) => a - b);
}
function compressDaysToDigits(days: number[]): number[] {
  const set = new Set<number>();
  for (const d of days) {
    if (d === 10 || d === 20 || d === 30) set.add(0);
    else if (d >= 1 && d <= 29) set.add(d % 10);
  }
  return [...set].sort((a, b) => a - b);
}

function CafeJoinPolicyTab({
  selectedAccount,
  onStartCafeJoin,
  cafeJoinLoading,
}: {
  selectedAccount: string;
  onStartCafeJoin: () => void;
  cafeJoinLoading: boolean;
}) {
  const [policy, setPolicy] = useState<CafeJoinPolicy>({
    run_days: [4],
    start_time: "09:00",
    created_year_min: 2020,
    created_year_max: 2025,
    recent_post_days: 7,
    recent_post_enabled: true,
    target_count: 50,
    search_keyword: "",
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!selectedAccount) return;
    let cancelled = false;
    (async () => {
      setLoading(true);
      try {
        const res = await fetch(`/api/agent-configs?account=${encodeURIComponent(selectedAccount)}`);
        if (res.ok && !cancelled) {
          const data = await res.json();
          const cafeJoin = (data?.cafe_join ?? {}) as Record<string, unknown>;
          const runDays = Array.isArray(cafeJoin.run_days) ? cafeJoin.run_days : [4, 14, 24];
          const digits = compressDaysToDigits(runDays.map(Number));
          setPolicy({
            run_days: digits.length > 0 ? [digits[0]] : [4],
            start_time: (cafeJoin.start_time as string) ?? "09:00",
            created_year_min: (cafeJoin.created_year_min as number) ?? 2020,
            created_year_max: (cafeJoin.created_year_max as number) ?? 2025,
            recent_post_days: (cafeJoin.recent_post_days as number) ?? 7,
            recent_post_enabled: (cafeJoin.recent_post_enabled as boolean) ?? true,
            target_count: (cafeJoin.target_count as number) ?? 50,
            search_keyword: (cafeJoin.search_keyword as string) ?? "",
          });
        }
      } catch {
        if (!cancelled) setPolicy((p) => p);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [selectedAccount]);

  const handleStartClick = () => {
    if (!selectedAccount) return;
    if (window.confirm("새로운 카페를 가입하시겠습니까?")) {
      onStartCafeJoin();
    }
  };

  const handleSave = async () => {
    if (!selectedAccount) return;
    setSaving(true);
    try {
      const toSend = { ...policy, run_days: expandDigitsToDays(policy.run_days) };
      const getRes = await fetch(`/api/agent-configs?account=${encodeURIComponent(selectedAccount)}`);
      const fullConfig = getRes.ok ? await getRes.json() : {};
      const config = {
        ...fullConfig,
        cafe_join: {
          run_days: toSend.run_days,
          start_time: toSend.start_time,
          created_year_min: toSend.created_year_min,
          created_year_max: toSend.created_year_max,
          recent_post_days: toSend.recent_post_days,
          recent_post_enabled: toSend.recent_post_enabled,
          target_count: toSend.target_count,
          search_keyword: toSend.search_keyword,
        },
      };
      const res = await fetch("/api/agent-configs", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          program_username: selectedAccount,
          config,
        }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const msg = (data as { message?: string })?.message ?? (data as { error?: string })?.error ?? "저장 실패";
        throw new Error(msg);
      }
      await fetch("/api/agent-commands", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          program_username: selectedAccount,
          command: "apply_config",
          payload: {},
        }),
      }).catch(() => {});
      alert("저장 완료");
    } catch (e) {
      alert(`저장 실패: ${e instanceof Error ? e.message : "알 수 없는 오류"}`);
    } finally {
      setSaving(false);
    }
  };

  const setRunDay = (d: number) => {
    setPolicy((p) => ({ ...p, run_days: [d] }));
  };

  return (
    <div className="mb-6 rounded-2xl border border-slate-700/60 bg-slate-800/40 p-4 md:p-6">
      <div className="mb-4 flex gap-2">
        <button
          type="button"
          onClick={handleStartClick}
          disabled={cafeJoinLoading || !selectedAccount}
          className="rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-indigo-500 disabled:opacity-50 md:px-6"
        >
          카페가입 시작
        </button>
      </div>
      <div className="mb-6 rounded-xl border border-slate-700/60 bg-slate-800/60 p-4 md:p-5">
        <h3 className="mb-4 text-sm font-semibold text-white md:text-base">정책 설정</h3>
        {loading ? (
          <p className="text-sm text-slate-400">로딩 중...</p>
        ) : (
          <div className="space-y-4">
            <div>
              <label className="mb-2 block text-xs text-slate-400">
                실행 날짜 (하나만 선택, 0=10·20·30일 / 1=1·11·21일 / 2=2·12·22일 … 저장 시 4→[4,14,24]로 저장)
              </label>
              <div className="flex flex-wrap gap-2">
                {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9].map((d) => (
                  <label key={d} className="flex cursor-pointer items-center gap-1.5">
                    <input
                      type="radio"
                      name="run_day"
                      checked={(policy.run_days[0] ?? 4) === d}
                      onChange={() => setRunDay(d)}
                      className="h-4 w-4 border-slate-600 bg-slate-800 text-indigo-600 focus:ring-indigo-500"
                    />
                    <span className="text-sm text-slate-300">{d}</span>
                  </label>
                ))}
              </div>
            </div>
            <div>
              <label className="mb-1 block text-xs text-slate-400">가입시작시간 (해당 날짜 이 시간에 자동 실행)</label>
              <input
                type="time"
                value={policy.start_time}
                onChange={(e) => setPolicy((p) => ({ ...p, start_time: e.target.value || "09:00" }))}
                className="mt-1 rounded-lg border border-slate-600 bg-slate-800/80 px-3 py-2 text-sm text-slate-100 outline-none focus:border-indigo-500"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs text-slate-400">생성년도 min / max</label>
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  min={2010}
                  max={2030}
                  value={policy.created_year_min}
                  onChange={(e) => setPolicy((p) => ({ ...p, created_year_min: Number(e.target.value) || 2020 }))}
                  className="w-20 rounded-lg border border-slate-600 bg-slate-800/80 px-3 py-2 text-sm text-slate-100 outline-none focus:border-indigo-500"
                />
                <span className="text-slate-500">~</span>
                <input
                  type="number"
                  min={2010}
                  max={2030}
                  value={policy.created_year_max}
                  onChange={(e) => setPolicy((p) => ({ ...p, created_year_max: Number(e.target.value) || 2025 }))}
                  className="w-20 rounded-lg border border-slate-600 bg-slate-800/80 px-3 py-2 text-sm text-slate-100 outline-none focus:border-indigo-500"
                />
              </div>
            </div>
            <div>
              <label className="flex cursor-pointer items-center gap-2">
                <input
                  type="checkbox"
                  checked={policy.recent_post_enabled}
                  onChange={(e) => setPolicy((p) => ({ ...p, recent_post_enabled: e.target.checked }))}
                  className="h-4 w-4 rounded border-slate-600 bg-slate-800 text-indigo-600 focus:ring-indigo-500"
                />
                <span className="text-sm text-slate-300">최근 N일 이내 글 없음</span>
              </label>
              <input
                type="number"
                min={1}
                max={90}
                value={policy.recent_post_days}
                onChange={(e) => setPolicy((p) => ({ ...p, recent_post_days: Number(e.target.value) || 7 }))}
                className="mt-2 w-20 rounded-lg border border-slate-600 bg-slate-800/80 px-3 py-2 text-sm text-slate-100 outline-none focus:border-indigo-500"
              />
              <span className="ml-2 text-xs text-slate-500">일</span>
            </div>
            <div>
              <label className="mb-1 block text-xs text-slate-400">목표 저장 개수 (target_count)</label>
              <input
                type="number"
                min={1}
                max={200}
                value={policy.target_count}
                onChange={(e) => setPolicy((p) => ({ ...p, target_count: Number(e.target.value) || 50 }))}
                className="w-24 rounded-lg border border-slate-600 bg-slate-800/80 px-3 py-2 text-sm text-slate-100 outline-none focus:border-indigo-500"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs text-slate-400">검색 키워드 (비워두면 랜덤 키워드 사용)</label>
              <input
                type="text"
                value={policy.search_keyword}
                onChange={(e) => setPolicy((p) => ({ ...p, search_keyword: e.target.value }))}
                placeholder="카페 검색 키워드 (미입력 시 랜덤)"
                className="w-full max-w-xs rounded-lg border border-slate-600 bg-slate-800/80 px-3 py-2 text-sm text-slate-100 placeholder-slate-500 outline-none focus:border-indigo-500"
              />
            </div>
          </div>
        )}
      </div>
      <button
        type="button"
        onClick={handleSave}
        disabled={saving || loading || !selectedAccount}
        className="rounded-xl bg-indigo-600 px-6 py-2.5 text-sm font-semibold text-white transition hover:bg-indigo-500 disabled:opacity-50"
      >
        {saving ? "저장 중..." : "저장"}
      </button>
      <p className="mt-2 text-xs text-slate-500">
        {selectedAccount} 계정의 카페가입 정책을 저장합니다. PC 에이전트가 이 설정을 사용합니다.
      </p>
    </div>
  );
}

function PostLogCard({ row }: { row: PostLog }) {
  const linkLabel = getLinkLabel(row.posting_url);

  return (
    <div className="flex min-h-[100px] flex-col rounded-xl border border-white/10 bg-white/5 p-3 backdrop-blur transition hover:bg-white/7 md:min-h-[110px] md:p-4">
      <div className="flex min-w-0 flex-1 flex-col gap-2">
        <div className="min-w-0 truncate font-semibold text-slate-100">
          {row.keyword}
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <span className="shrink-0 rounded-full bg-slate-600/40 px-2 py-0.5 text-xs text-slate-300">
            {postTypeLabel(row.post_type)}
          </span>
          {linkLabel && (
            <span className="shrink-0 font-medium text-[#03C75A] text-xs">
              {linkLabel}
            </span>
          )}
        </div>
      </div>
      <div className="mt-2 flex items-center justify-between gap-2 border-t border-white/5 pt-2">
        {row.posting_url ? (
          <a
            href={row.posting_url}
            target="_blank"
            rel="noreferrer"
            className="shrink-0 rounded-lg border border-white/10 bg-white/5 px-2.5 py-1.5 text-xs text-slate-200 transition hover:bg-white/10 md:px-3 md:py-2 md:text-sm"
          >
            링크 열기
          </a>
        ) : (
          <span className="text-xs text-white/50">-</span>
        )}
        <span className="shrink-0 text-xs text-slate-500">
          {formatKST(row.created_at)}
        </span>
      </div>
    </div>
  );
}

type DashboardMode = "full" | "history";

export default function Dashboard({ mode = "full" }: { mode?: DashboardMode }) {
  const showSettingsTabs = mode === "full";
  const [user, setUser] = useState<User>(null);
  const [sessionLoading, setSessionLoading] = useState(true);

  const [postLogs, setPostLogs] = useState<PostLog[]>([]);
  const [logPage, setLogPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [managedAccounts, setManagedAccounts] = useState<string[]>([]);
  const [selectedAccount, setSelectedAccount] = useState<string>("");
  const [accountStats, setAccountStats] = useState<Record<string, { label: string; dot: string }>>({});

  const [activeTab, setActiveTab] = useState<"blog" | "cafe" | "cafe_join" | "coupang_api" | null>(null);

  const [blogConfig, setBlogConfig] = useState({
    naver_id: "",
    naver_pw: "",
    publish_count: 10,
    delay_min: 2,
    delay_max: 5,
    auto_restart: { enabled: false, after_minutes: 10 },
    auto_start_cafe_after_blog: false,
    use_server_keywords: false,
    keyword_columns: "keyword",
  });
  const [blogConfigLoading, setBlogConfigLoading] = useState(false);
  const [blogConfigSaving, setBlogConfigSaving] = useState(false);
  const [blogCommandLoading, setBlogCommandLoading] = useState(false);
  const [cafeConfigLoading, setCafeConfigLoading] = useState(false);
  const [cafeConfigSaving, setCafeConfigSaving] = useState(false);
  const [cafeCommandLoading, setCafeCommandLoading] = useState(false);
  const [cafeJoinLoading, setCafeJoinLoading] = useState(false);

  const [coupangApiConfig, setCoupangApiConfig] = useState({ coupang_access_key: "", coupang_secret_key: "" });
  const [coupangApiApplyToAll, setCoupangApiApplyToAll] = useState(false);
  const [coupangApiLoading, setCoupangApiLoading] = useState(false);
  const [coupangApiSaving, setCoupangApiSaving] = useState(false);

  const [cafeConfig, setCafeConfig] = useState({
    naver_id: "",
    naver_pw: "",
    publish_count: 10,
    delay_min: 5,
    delay_max: 30,
    auto_restart: { enabled: false, after_minutes: 10 },
    use_new_cafe_list: false,
  });

  const mainUsername = user?.username ?? "";
  const allAccounts = [mainUsername, ...managedAccounts].filter(Boolean);

  const checkSession = useCallback(async () => {
    try {
      const res = await fetch("/api/auth/session");
      const data = await res.json();
      const u = data.ok ? data.user : null;
      setUser(u);
      if (u) {
        const managed = (u.managed_usernames ?? [])
          .map((s: string) => String(s).trim())
          .filter(Boolean);
        setManagedAccounts(managed);
        setSelectedAccount((prev) => (prev && (prev === u.username || managed.includes(prev)) ? prev : u.username));
      } else {
        setManagedAccounts([]);
        setSelectedAccount("");
      }
    } catch {
      setUser(null);
      setManagedAccounts([]);
      setSelectedAccount("");
    } finally {
      setSessionLoading(false);
    }
  }, []);

  useEffect(() => {
    checkSession();
  }, [checkSession]);

  useEffect(() => {
    const handler = () => checkSession();
    window.addEventListener("auth-changed", handler);
    return () => window.removeEventListener("auth-changed", handler);
  }, [checkSession]);

  const loadPostLogs = useCallback(async () => {
    if (!user || !selectedAccount) return;
    setLoading(true);
    try {
      const res = await fetch(`/api/post-logs?account=${encodeURIComponent(selectedAccount)}`);
      if (!res.ok) {
        if (res.status === 401) return;
        throw new Error("목록 조회 실패");
      }
      const data = await res.json();
      setPostLogs(Array.isArray(data) ? data : []);
      setLogPage(1);
      setError(null);
    } catch (e) {
      setError("포스팅 로그를 불러오지 못했습니다.");
    } finally {
      setLoading(false);
    }
  }, [user, selectedAccount]);

  const loadLastActivity = useCallback(async () => {
    if (!user || allAccounts.length === 0) return;
    try {
      const res = await fetch(`/api/post-last-activity?accounts=${encodeURIComponent(allAccounts.join(","))}`);
      if (!res.ok) return;
      const data = await res.json();
      const stats: Record<string, { label: string; dot: string }> = {};
      for (const row of Array.isArray(data) ? data : []) {
        const un = row?.program_username;
        if (un) stats[un] = computeStatus(row.last_job_at ?? null);
      }
      for (const un of allAccounts) {
        if (!(un in stats)) stats[un] = computeStatus(null);
      }
      setAccountStats(stats);
    } catch {
      // ignore
    }
  }, [user, allAccounts.join(",")]);

  useEffect(() => {
    if (user && selectedAccount) {
      loadPostLogs();
    }
  }, [loadPostLogs, user, selectedAccount]);

  useEffect(() => {
    if (user && allAccounts.length > 0) {
      loadLastActivity();
      const t = setInterval(loadLastActivity, 300000);
      return () => clearInterval(t);
    }
  }, [loadLastActivity, user, allAccounts.join(",")]);

  const [fullConfig, setFullConfig] = useState<Record<string, unknown>>({});

  const loadBlogConfig = useCallback(async () => {
    if (!user || !selectedAccount) return;
    setBlogConfigLoading(true);
    try {
      const res = await fetch(`/api/agent-configs?account=${encodeURIComponent(selectedAccount)}`);
      if (!res.ok) return;
      const data = await res.json();
      setFullConfig(typeof data === "object" && data !== null ? data : {});
      const blog = (data?.blog ?? {}) as Record<string, unknown>;
      setBlogConfig({
        naver_id: (blog.naver_id as string) ?? "",
        naver_pw: (blog.naver_pw as string) ?? "",
        publish_count: (blog.publish_count as number) ?? 10,
        delay_min: (blog.delay_min as number) ?? 2,
        delay_max: (blog.delay_max as number) ?? 5,
        auto_restart: (blog.auto_restart as { enabled: boolean; after_minutes: number }) ?? { enabled: false, after_minutes: 10 },
        auto_start_cafe_after_blog: (blog.auto_start_cafe_after_blog as boolean) ?? false,
        use_server_keywords: (blog.use_server_keywords as boolean) ?? false,
        keyword_columns: (blog.keyword_columns as string) ?? "keyword",
      });
    } catch {
      // ignore
    } finally {
      setBlogConfigLoading(false);
    }
  }, [user, selectedAccount]);

  useEffect(() => {
    if (activeTab === "blog" && user && selectedAccount) {
      loadBlogConfig();
    }
  }, [activeTab, loadBlogConfig, user, selectedAccount]);

  const loadCafeConfig = useCallback(async () => {
    if (!user || !selectedAccount) return;
    setCafeConfigLoading(true);
    try {
      const res = await fetch(`/api/agent-configs?account=${encodeURIComponent(selectedAccount)}`);
      if (!res.ok) return;
      const data = await res.json();
      setFullConfig(typeof data === "object" && data !== null ? data : {});
      const cafe = (data?.cafe ?? {}) as Record<string, unknown>;
      setCafeConfig({
        naver_id: (cafe.naver_id as string) ?? "",
        naver_pw: (cafe.naver_pw as string) ?? "",
        publish_count: (cafe.publish_count as number) ?? 10,
        delay_min: (cafe.delay_min as number) ?? 5,
        delay_max: (cafe.delay_max as number) ?? 30,
        auto_restart: (cafe.auto_restart as { enabled: boolean; after_minutes: number }) ?? { enabled: false, after_minutes: 10 },
        use_new_cafe_list: (cafe.use_new_cafe_list as boolean) ?? false,
      });
    } catch {
      // ignore
    } finally {
      setCafeConfigLoading(false);
    }
  }, [user, selectedAccount]);

  useEffect(() => {
    if (activeTab === "cafe" && user && selectedAccount) {
      loadCafeConfig();
    }
  }, [activeTab, loadCafeConfig, user, selectedAccount]);

  const loadCoupangApiConfig = useCallback(async () => {
    if (!user || !selectedAccount) return;
    setCoupangApiLoading(true);
    try {
      const res = await fetch(`/api/coupang-keys?account=${encodeURIComponent(selectedAccount)}`);
      if (!res.ok) return;
      const data = await res.json();
      setCoupangApiConfig({
        coupang_access_key: (data.coupang_access_key as string) ?? "",
        coupang_secret_key: (data.coupang_secret_key as string) ?? "",
      });
    } catch {
      // ignore
    } finally {
      setCoupangApiLoading(false);
    }
  }, [user, selectedAccount]);

  useEffect(() => {
    if (activeTab === "coupang_api" && user && selectedAccount) {
      loadCoupangApiConfig();
    }
  }, [activeTab, loadCoupangApiConfig, user, selectedAccount]);

  const handleSaveCoupangApiConfig = async () => {
    if (!user) return;
    if (!coupangApiApplyToAll && !selectedAccount) return;
    setCoupangApiSaving(true);
    setError(null);
    try {
      const res = await fetch("/api/coupang-keys", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          account: coupangApiApplyToAll ? undefined : selectedAccount,
          apply_to_all: coupangApiApplyToAll,
          coupang_access_key: coupangApiConfig.coupang_access_key,
          coupang_secret_key: coupangApiConfig.coupang_secret_key,
        }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const msg = (data as { error?: string })?.error ?? "저장 실패";
        alert(`저장 실패: ${msg}`);
        setError(msg);
        return;
      }
      const updatedCount = (data as { updated_count?: number })?.updated_count;
      alert(updatedCount != null ? `${updatedCount}개 계정에 저장 완료` : "저장 완료");
    } catch (e) {
      alert(`저장 실패: ${e instanceof Error ? e.message : "알 수 없는 오류"}`);
    } finally {
      setCoupangApiSaving(false);
    }
  };

  const handleStartBlog = async () => {
    if (!user) return;
    setBlogCommandLoading(true);
    try {
      const res = await fetch("/api/agent-commands", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          program_username: selectedAccount || mainUsername,
          command: "start",
          payload: { mode: "blog" },
        }),
      });
      if (!res.ok) throw new Error("전송 실패");
    } catch {
      setError("발행시작 명령 전송 실패");
    } finally {
      setBlogCommandLoading(false);
    }
  };

  const handleStopBlog = async () => {
    if (!user) return;
    setBlogCommandLoading(true);
    try {
      const res = await fetch("/api/agent-commands", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          program_username: selectedAccount || mainUsername,
          command: "stop",
          payload: {},
        }),
      });
      if (!res.ok) throw new Error("전송 실패");
    } catch {
      setError("발행중지 명령 전송 실패");
    } finally {
      setBlogCommandLoading(false);
    }
  };

  const handleStartCafeJoin = async () => {
    if (!user) return;
    setCafeJoinLoading(true);
    try {
      const res = await fetch("/api/agent-commands", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          program_username: selectedAccount || mainUsername,
          command: "start",
          payload: { mode: "cafe_join", immediate: true },
        }),
      });
      if (!res.ok) throw new Error("전송 실패");
    } catch {
      setError("카페가입 시작 명령 전송 실패");
    } finally {
      setCafeJoinLoading(false);
    }
  };

  const handleStartCafe = async () => {
    if (!user) return;
    setCafeCommandLoading(true);
    try {
      const res = await fetch("/api/agent-commands", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          program_username: selectedAccount || mainUsername,
          command: "start",
          payload: { mode: "cafe" },
        }),
      });
      if (!res.ok) throw new Error("전송 실패");
    } catch {
      setError("카페 발행시작 명령 전송 실패");
    } finally {
      setCafeCommandLoading(false);
    }
  };

  const handleStopCafe = async () => {
    if (!user) return;
    setCafeCommandLoading(true);
    try {
      const res = await fetch("/api/agent-commands", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          program_username: selectedAccount || mainUsername,
          command: "stop",
          payload: {},
        }),
      });
      if (!res.ok) throw new Error("전송 실패");
    } catch {
      setError("카페 발행중지 명령 전송 실패");
    } finally {
      setCafeCommandLoading(false);
    }
  };

  const handleSaveCafeConfig = async () => {
    const uid = user?.id;
    const programUsername = selectedAccount || mainUsername;
    if (!uid) {
      alert("로그인 정보가 없습니다.");
      return;
    }
    if (!programUsername) {
      alert("선택된 아이디가 없습니다.");
      return;
    }
    setCafeConfigSaving(true);
    setError(null);
    try {
      const config = {
        ...fullConfig,
        cafe: {
          naver_id: cafeConfig.naver_id,
          naver_pw: cafeConfig.naver_pw,
          publish_count: cafeConfig.publish_count,
          delay_min: cafeConfig.delay_min,
          delay_max: cafeConfig.delay_max,
          auto_restart: cafeConfig.auto_restart,
          use_new_cafe_list: cafeConfig.use_new_cafe_list,
        },
      };
      const res = await fetch("/api/agent-configs", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          program_username: programUsername,
          config,
        }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const msg = data.message || data.error || "저장 실패";
        const details = data.details ? ` (${JSON.stringify(data.details)})` : "";
        console.error("save cafe config error", data);
        alert(`저장 실패: ${msg}${details}`);
        setError(msg);
        return;
      }

      await fetch("/api/agent-commands", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          program_username: programUsername,
          command: "apply_config",
          payload: {},
        }),
      }).catch(() => {});

      alert("저장 완료");
    } catch (e) {
      const msg = e instanceof Error ? e.message : "설정 저장 실패";
      console.error("save cafe config error", e);
      alert(`저장 실패: ${msg}`);
      setError(msg);
    } finally {
      setCafeConfigSaving(false);
    }
  };

  const handleSaveBlogConfig = async () => {
    const uid = user?.id;
    const programUsername = selectedAccount || mainUsername;
    if (!uid) {
      alert("로그인 정보가 없습니다.");
      return;
    }
    if (!programUsername) {
      alert("선택된 아이디가 없습니다.");
      return;
    }
    setBlogConfigSaving(true);
    setError(null);
    try {
      const config = {
        ...fullConfig,
        blog: {
          naver_id: blogConfig.naver_id,
          naver_pw: blogConfig.naver_pw,
          publish_count: blogConfig.publish_count,
          delay_min: blogConfig.delay_min,
          delay_max: blogConfig.delay_max,
          auto_restart: blogConfig.auto_restart,
          auto_start_cafe_after_blog: blogConfig.auto_start_cafe_after_blog,
          use_server_keywords: blogConfig.use_server_keywords,
          keyword_columns: blogConfig.keyword_columns,
        },
      };
      const res = await fetch("/api/agent-configs", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          program_username: programUsername,
          config,
        }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const msg = data.message || data.error || "저장 실패";
        const details = data.details ? ` (${JSON.stringify(data.details)})` : "";
        console.error("save config error", data);
        alert(`저장 실패: ${msg}${details}`);
        setError(msg);
        return;
      }

      await fetch("/api/agent-commands", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          program_username: programUsername,
          command: "apply_config",
          payload: {},
        }),
      }).catch(() => {});

      alert("저장 완료");
    } catch (e) {
      const msg = e instanceof Error ? e.message : "설정 저장 실패";
      console.error("save config error", e);
      alert(`저장 실패: ${msg}`);
      setError(msg);
    } finally {
      setBlogConfigSaving(false);
    }
  };

  const todayLogs = postLogs.filter((r) => isTodayKST(r.created_at));
  const totalPages = Math.max(1, Math.ceil(todayLogs.length / POST_LOGS_PER_PAGE));
  const displayedLogs = todayLogs.slice((logPage - 1) * POST_LOGS_PER_PAGE, logPage * POST_LOGS_PER_PAGE);

  const summaryCounts = {
    self: todayLogs.filter((r) => r.post_type === "self").length,
    paid: todayLogs.filter((r) => r.post_type === "paid").length,
    referrer: todayLogs.filter((r) => r.post_type === "referrer").length,
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 text-slate-100">
      {user && allAccounts.length > 0 && (
        <div className="border-b border-slate-700/60 bg-slate-800/30">
          <div className="mx-auto max-w-6xl px-4 py-3 md:px-8 md:py-4">
            <p className="mb-2 text-xs text-slate-400 md:text-sm">
              {showSettingsTabs
                ? "클릭 시 해당 아이디의 블로그·카페·카페가입 설정을 편집하고 제어합니다."
                : "클릭 시 해당 아이디의 작업 내역을 확인합니다."}
            </p>
            <div className="mb-2 flex flex-wrap items-center gap-3 text-xs text-slate-400 md:text-sm">
              <span className="flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-rose-500" />
                서버체크
              </span>
              <span className="flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-amber-500" />
                작업확인
              </span>
              <span className="flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-emerald-500" />
                작업중
              </span>
            </div>
            <div className="flex flex-wrap gap-2 md:gap-3">
              {[...allAccounts]
                .sort((a, b) => {
                  const order = { red: 0, orange: 1, green: 2 };
                  const dotA = (accountStats[a] ?? computeStatus(null)).dot;
                  const dotB = (accountStats[b] ?? computeStatus(null)).dot;
                  return (order[dotA as keyof typeof order] ?? 0) - (order[dotB as keyof typeof order] ?? 0);
                })
                .map((un) => {
                  const stat = accountStats[un] ?? computeStatus(null);
                  const isSelected = un === selectedAccount;
                  const dotColor =
                    stat.dot === "green"
                      ? "bg-emerald-500"
                      : stat.dot === "orange"
                        ? "bg-amber-500"
                        : "bg-rose-500";
                  return (
                    <button
                      key={un}
                      type="button"
                      onClick={() => setSelectedAccount(un)}
                      className={`flex min-w-[120px] flex-1 basis-[calc(50%-0.25rem)] items-center gap-2 rounded-xl border px-3 py-2.5 transition md:min-w-[140px] md:flex-initial md:basis-auto md:gap-3 md:px-4 ${
                        isSelected
                          ? "border-indigo-500/60 bg-indigo-500/20"
                          : "border-slate-600/60 bg-slate-800/50 hover:bg-slate-800/70"
                      }`}
                    >
                      <span className={`h-2 w-2 shrink-0 rounded-full ${dotColor}`} />
                      <span className="min-w-0 flex-1 truncate text-left text-sm font-medium text-slate-200 md:text-base">
                        {un}
                      </span>
                      <span className="shrink-0 text-xs text-slate-400 md:text-sm">
                        {isSelected ? (showSettingsTabs ? "설정중" : "조회중") : showSettingsTabs ? "설정/제어" : "작업내역"}
                      </span>
                    </button>
                  );
                })}
            </div>
          </div>
        </div>
      )}

      <div className="mx-auto max-w-6xl px-4 py-8 md:px-8 md:py-16">
        {sessionLoading ? (
          <div className="flex justify-center py-16 text-sm text-slate-400 md:py-24">
            로딩 중...
          </div>
        ) : !user ? (
          <div className="flex flex-col items-center justify-center py-16 text-center md:py-24">
            <p className="mb-4 text-lg text-slate-400 md:mb-6 md:text-xl">
              로그인 후 서비스를 이용할 수 있습니다.
            </p>
            <button
              onClick={() => window.dispatchEvent(new CustomEvent("open-login-modal"))}
              className="rounded-xl bg-indigo-600 px-6 py-3 text-sm font-semibold text-white transition hover:bg-indigo-500 md:px-8 md:py-4 md:text-base"
            >
              로그인
            </button>
          </div>
        ) : (
          <>
            {showSettingsTabs && (
            <div className="mb-4 grid grid-cols-2 gap-2 rounded-xl border border-slate-700/60 bg-slate-800/40 p-2 sm:flex sm:gap-1 sm:p-1">
              <button
                type="button"
                onClick={() => setActiveTab((t) => (t === "blog" ? null : "blog"))}
                className={`flex items-center justify-center gap-2 rounded-lg px-3 py-3 text-sm font-medium transition sm:flex-1 sm:px-4 sm:py-2.5 md:px-6 ${
                  activeTab === "blog"
                    ? "bg-indigo-600 text-white"
                    : "text-slate-400 hover:bg-slate-700/60 hover:text-slate-200"
                }`}
              >
                <span className="text-lg sm:text-base" aria-hidden>📝</span>
                <span className="whitespace-nowrap">블로그</span>
              </button>
              <button
                type="button"
                onClick={() => setActiveTab((t) => (t === "cafe" ? null : "cafe"))}
                className={`flex items-center justify-center gap-2 rounded-lg px-3 py-3 text-sm font-medium transition sm:flex-1 sm:px-4 sm:py-2.5 md:px-6 ${
                  activeTab === "cafe"
                    ? "bg-indigo-600 text-white"
                    : "text-slate-400 hover:bg-slate-700/60 hover:text-slate-200"
                }`}
              >
                <span className="text-lg sm:text-base" aria-hidden>☕</span>
                <span className="whitespace-nowrap">카페</span>
              </button>
              <button
                type="button"
                onClick={() => setActiveTab((t) => (t === "cafe_join" ? null : "cafe_join"))}
                className={`flex items-center justify-center gap-2 rounded-lg px-3 py-3 text-sm font-medium transition sm:flex-1 sm:px-4 sm:py-2.5 md:px-6 ${
                  activeTab === "cafe_join"
                    ? "bg-indigo-600 text-white"
                    : "text-slate-400 hover:bg-slate-700/60 hover:text-slate-200"
                }`}
              >
                <span className="text-lg sm:text-base" aria-hidden>➕</span>
                <span className="whitespace-nowrap">카페가입</span>
              </button>
              <button
                type="button"
                onClick={() => setActiveTab((t) => (t === "coupang_api" ? null : "coupang_api"))}
                className={`flex items-center justify-center gap-2 rounded-lg px-3 py-3 text-sm font-medium transition sm:flex-1 sm:px-4 sm:py-2.5 md:px-6 ${
                  activeTab === "coupang_api"
                    ? "bg-indigo-600 text-white"
                    : "text-slate-400 hover:bg-slate-700/60 hover:text-slate-200"
                }`}
              >
                <span className="text-lg sm:text-base" aria-hidden>🔑</span>
                <span className="whitespace-nowrap">쿠팡API</span>
              </button>
            </div>
            )}

            {showSettingsTabs && activeTab === "blog" && (
              <div className="mb-6 rounded-2xl border border-slate-700/60 bg-slate-800/40 p-4 md:p-6">
                <div className="mb-4 flex gap-2">
                  <button
                    type="button"
                    onClick={handleStartBlog}
                    disabled={blogCommandLoading}
                    className="rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-indigo-500 disabled:opacity-50 md:px-6"
                  >
                    발행시작
                  </button>
                  <button
                    type="button"
                    onClick={handleStopBlog}
                    disabled={blogCommandLoading}
                    className="rounded-xl border border-slate-600 bg-slate-800/80 px-4 py-2.5 text-sm font-medium text-slate-300 transition hover:bg-slate-700 hover:text-white disabled:opacity-50 md:px-6"
                  >
                    발행중지
                  </button>
                </div>

                <div className="mb-6 rounded-xl border border-slate-700/60 bg-slate-800/60 p-4 md:p-5">
                  <h3 className="mb-4 text-sm font-semibold text-white md:text-base">기본설정</h3>
                  {blogConfigLoading ? (
                    <p className="text-sm text-slate-400">로딩 중...</p>
                  ) : (
                    <div className="space-y-4">
                      <div>
                        <label className="mb-1 block text-xs text-slate-400">네이버 아이디</label>
                        <input
                          type="text"
                          value={blogConfig.naver_id}
                          onChange={(e) => setBlogConfig((c) => ({ ...c, naver_id: e.target.value }))}
                          className="w-full rounded-lg border border-slate-600 bg-slate-800/80 px-3 py-2 text-sm text-slate-100 placeholder-slate-500 outline-none focus:border-indigo-500 md:max-w-xs"
                          placeholder="네이버 아이디"
                        />
                      </div>
                      <div>
                        <label className="mb-1 block text-xs text-slate-400">네이버 비번</label>
                        <input
                          type="password"
                          value={blogConfig.naver_pw}
                          onChange={(e) => setBlogConfig((c) => ({ ...c, naver_pw: e.target.value }))}
                          className="w-full rounded-lg border border-slate-600 bg-slate-800/80 px-3 py-2 text-sm text-slate-100 placeholder-slate-500 outline-none focus:border-indigo-500 md:max-w-xs"
                          placeholder="네이버 비밀번호"
                        />
                        <p className="mt-1 text-xs text-amber-500/80">※ 비밀번호는 DB에 저장됩니다. 보안상 PC에만 저장하는 방식을 권장합니다.</p>
                      </div>
                      <div>
                        <label className="mb-1 block text-xs text-slate-400">발행개수</label>
                        <input
                          type="number"
                          min={1}
                          value={blogConfig.publish_count}
                          onChange={(e) => setBlogConfig((c) => ({ ...c, publish_count: Number(e.target.value) || 0 }))}
                          className="w-full rounded-lg border border-slate-600 bg-slate-800/80 px-3 py-2 text-sm text-slate-100 outline-none focus:border-indigo-500 md:max-w-[120px]"
                        />
                      </div>
                      <div>
                        <label className="mb-1 block text-xs text-slate-400">작업딜레이 (N분~N분)</label>
                        <div className="flex items-center gap-2">
                          <input
                            type="number"
                            min={0}
                            value={blogConfig.delay_min}
                            onChange={(e) => setBlogConfig((c) => ({ ...c, delay_min: Number(e.target.value) || 0 }))}
                            className="w-20 rounded-lg border border-slate-600 bg-slate-800/80 px-3 py-2 text-sm text-slate-100 outline-none focus:border-indigo-500"
                          />
                          <span className="text-slate-500">~</span>
                          <input
                            type="number"
                            min={0}
                            value={blogConfig.delay_max}
                            onChange={(e) => setBlogConfig((c) => ({ ...c, delay_max: Number(e.target.value) || 0 }))}
                            className="w-20 rounded-lg border border-slate-600 bg-slate-800/80 px-3 py-2 text-sm text-slate-100 outline-none focus:border-indigo-500"
                          />
                          <span className="text-xs text-slate-500">분</span>
                        </div>
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <button
                            type="button"
                            role="switch"
                            aria-checked={blogConfig.auto_restart.enabled}
                            onClick={() =>
                              setBlogConfig((c) => ({
                                ...c,
                                auto_restart: { ...c.auto_restart, enabled: !c.auto_restart.enabled },
                              }))
                            }
                            className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-slate-900 ${
                              blogConfig.auto_restart.enabled ? "bg-indigo-600" : "bg-slate-600"
                            }`}
                          >
                            <span
                              className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition ${
                                blogConfig.auto_restart.enabled ? "translate-x-5" : "translate-x-1"
                              }`}
                            />
                          </button>
                          <span className="text-sm text-slate-300">자동재시작 설정</span>
                        </div>
                        <div className="mt-2 flex items-center gap-2">
                          <span className="text-xs text-slate-500">작업종료 후</span>
                          <input
                            type="number"
                            min={1}
                            value={blogConfig.auto_restart.after_minutes}
                            onChange={(e) =>
                              setBlogConfig((c) => ({
                                ...c,
                                auto_restart: { ...c.auto_restart, after_minutes: Number(e.target.value) || 10 },
                              }))
                            }
                            className="w-16 rounded-lg border border-slate-600 bg-slate-800/80 px-2 py-1.5 text-sm text-slate-100 outline-none focus:border-indigo-500"
                          />
                          <span className="text-xs text-slate-500">분 뒤 재시작</span>
                        </div>
                      </div>
                      <div>
                        <label className="flex cursor-pointer items-center gap-2">
                          <input
                            type="checkbox"
                            checked={blogConfig.auto_start_cafe_after_blog}
                            onChange={(e) => setBlogConfig((c) => ({ ...c, auto_start_cafe_after_blog: e.target.checked }))}
                            className="h-4 w-4 rounded border-slate-600 bg-slate-800 text-indigo-600 focus:ring-indigo-500"
                          />
                          <span className="text-sm text-slate-300">카페자동시작</span>
                        </label>
                        <p className="mt-1 text-xs text-slate-500">
                          체크된 상태에서 블로그 작업이 완료되면, 설정된 카페작업을 연속으로 진행합니다.
                        </p>
                      </div>
                    </div>
                  )}
                </div>

                <button
                  type="button"
                  onClick={handleSaveBlogConfig}
                  disabled={
                    blogConfigSaving ||
                    blogConfigLoading ||
                    !user?.id ||
                    !(selectedAccount || mainUsername)
                  }
                  className="rounded-xl bg-indigo-600 px-6 py-2.5 text-sm font-semibold text-white transition hover:bg-indigo-500 disabled:opacity-50"
                >
                  {blogConfigSaving ? "저장 중..." : "설정 저장"}
                </button>
                <p className="mt-3 text-xs leading-relaxed text-slate-500">
                  PC에서 프로그램이 실행 중이면: 설정 저장 후 PC 프로그램이 종료됐다가 새 설정값으로 다시 시작된다(에이전트 모드일 때).
                  <br />
                  프로그램이 작업을 마치고 대기 중이면: 설정 저장 후 바로 새 설정으로 작업을 시작할 수 있다.
                </p>
              </div>
            )}

            {showSettingsTabs && activeTab === "cafe" && (
              <div className="mb-6 rounded-2xl border border-slate-700/60 bg-slate-800/40 p-4 md:p-6">
                <div className="mb-4 flex gap-2">
                  <button
                    type="button"
                    onClick={handleStartCafe}
                    disabled={cafeCommandLoading}
                    className="rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-indigo-500 disabled:opacity-50 md:px-6"
                  >
                    발행시작
                  </button>
                  <button
                    type="button"
                    onClick={handleStopCafe}
                    disabled={cafeCommandLoading}
                    className="rounded-xl border border-slate-600 bg-slate-800/80 px-4 py-2.5 text-sm font-medium text-slate-300 transition hover:bg-slate-700 hover:text-white disabled:opacity-50 md:px-6"
                  >
                    발행중지
                  </button>
                </div>

                <div className="mb-6 rounded-xl border border-slate-700/60 bg-slate-800/60 p-4 md:p-5">
                  <h3 className="mb-4 text-sm font-semibold text-white md:text-base">기본설정</h3>
                  {cafeConfigLoading ? (
                    <p className="text-sm text-slate-400">로딩 중...</p>
                  ) : (
                    <div className="space-y-4">
                      <div>
                        <label className="mb-1 block text-xs text-slate-400">네이버 아이디</label>
                        <input
                          type="text"
                          value={cafeConfig.naver_id}
                          onChange={(e) => setCafeConfig((c) => ({ ...c, naver_id: e.target.value }))}
                          className="w-full rounded-lg border border-slate-600 bg-slate-800/80 px-3 py-2 text-sm text-slate-100 placeholder-slate-500 outline-none focus:border-indigo-500 md:max-w-xs"
                          placeholder="네이버 아이디"
                        />
                      </div>
                      <div>
                        <label className="mb-1 block text-xs text-slate-400">네이버 비번</label>
                        <input
                          type="password"
                          value={cafeConfig.naver_pw}
                          onChange={(e) => setCafeConfig((c) => ({ ...c, naver_pw: e.target.value }))}
                          className="w-full rounded-lg border border-slate-600 bg-slate-800/80 px-3 py-2 text-sm text-slate-100 placeholder-slate-500 outline-none focus:border-indigo-500 md:max-w-xs"
                          placeholder="네이버 비밀번호"
                        />
                        <p className="mt-1 text-xs text-amber-500/80">※ 비밀번호는 DB에 저장됩니다. 보안상 PC에만 저장하는 방식을 권장합니다.</p>
                      </div>
                      <div>
                        <label className="mb-1 block text-xs text-slate-400">발행개수</label>
                        <input
                          type="number"
                          min={1}
                          value={cafeConfig.publish_count}
                          onChange={(e) => setCafeConfig((c) => ({ ...c, publish_count: Number(e.target.value) || 0 }))}
                          className="w-full rounded-lg border border-slate-600 bg-slate-800/80 px-3 py-2 text-sm text-slate-100 outline-none focus:border-indigo-500 md:max-w-[120px]"
                        />
                      </div>
                      <div>
                        <label className="mb-1 block text-xs text-slate-400">작업딜레이 (N분~N분)</label>
                        <div className="flex items-center gap-2">
                          <input
                            type="number"
                            min={0}
                            value={cafeConfig.delay_min}
                            onChange={(e) => setCafeConfig((c) => ({ ...c, delay_min: Number(e.target.value) || 0 }))}
                            className="w-20 rounded-lg border border-slate-600 bg-slate-800/80 px-3 py-2 text-sm text-slate-100 outline-none focus:border-indigo-500"
                          />
                          <span className="text-slate-500">~</span>
                          <input
                            type="number"
                            min={0}
                            value={cafeConfig.delay_max}
                            onChange={(e) => setCafeConfig((c) => ({ ...c, delay_max: Number(e.target.value) || 0 }))}
                            className="w-20 rounded-lg border border-slate-600 bg-slate-800/80 px-3 py-2 text-sm text-slate-100 outline-none focus:border-indigo-500"
                          />
                          <span className="text-xs text-slate-500">분</span>
                        </div>
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <button
                            type="button"
                            role="switch"
                            aria-checked={cafeConfig.auto_restart.enabled}
                            onClick={() =>
                              setCafeConfig((c) => ({
                                ...c,
                                auto_restart: { ...c.auto_restart, enabled: !c.auto_restart.enabled },
                              }))
                            }
                            className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-slate-900 ${
                              cafeConfig.auto_restart.enabled ? "bg-indigo-600" : "bg-slate-600"
                            }`}
                          >
                            <span
                              className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition ${
                                cafeConfig.auto_restart.enabled ? "translate-x-5" : "translate-x-1"
                              }`}
                            />
                          </button>
                          <span className="text-sm text-slate-300">자동재시작 설정</span>
                        </div>
                        <div className="mt-2 flex items-center gap-2">
                          <span className="text-xs text-slate-500">작업종료 후</span>
                          <input
                            type="number"
                            min={1}
                            value={cafeConfig.auto_restart.after_minutes}
                            onChange={(e) =>
                              setCafeConfig((c) => ({
                                ...c,
                                auto_restart: { ...c.auto_restart, after_minutes: Number(e.target.value) || 10 },
                              }))
                            }
                            className="w-16 rounded-lg border border-slate-600 bg-slate-800/80 px-2 py-1.5 text-sm text-slate-100 outline-none focus:border-indigo-500"
                          />
                          <span className="text-xs text-slate-500">분 뒤 재시작</span>
                        </div>
                      </div>
                      <div>
                        <label className="flex cursor-pointer items-center gap-2">
                          <input
                            type="checkbox"
                            checked={cafeConfig.use_new_cafe_list}
                            onChange={(e) => setCafeConfig((c) => ({ ...c, use_new_cafe_list: e.target.checked }))}
                            className="h-4 w-4 rounded border-slate-600 bg-slate-800 text-indigo-600 focus:ring-indigo-500"
                          />
                          <span className="text-sm text-slate-300">서버뉴카페로 작업</span>
                        </label>
                        <p className="mt-1 text-xs text-slate-500">
                          체크 시: 카페가입 후 저장된 agent_cafe_lists를 순서대로 포스팅. 모두 완료 시 처음부터 반복.
                          <br />
                          미체크 시: PC에 저장된 카페리스트 또는 서버 도우미 카페를 사용합니다.
                        </p>
                      </div>
                    </div>
                  )}
                </div>

                <button
                  type="button"
                  onClick={handleSaveCafeConfig}
                  disabled={
                    cafeConfigSaving ||
                    cafeConfigLoading ||
                    !user?.id ||
                    !(selectedAccount || mainUsername)
                  }
                  className="rounded-xl bg-indigo-600 px-6 py-2.5 text-sm font-semibold text-white transition hover:bg-indigo-500 disabled:opacity-50"
                >
                  {cafeConfigSaving ? "저장 중..." : "설정 저장"}
                </button>
                <p className="mt-3 text-xs leading-relaxed text-slate-500">
                  PC에서 프로그램이 실행 중이면: 설정 저장 후 PC 프로그램이 종료됐다가 새 설정값으로 다시 시작된다(에이전트 모드일 때).
                </p>
              </div>
            )}

            {showSettingsTabs && activeTab === "cafe_join" && (
              <CafeJoinPolicyTab
                selectedAccount={selectedAccount || mainUsername}
                onStartCafeJoin={handleStartCafeJoin}
                cafeJoinLoading={cafeJoinLoading}
              />
            )}

            {showSettingsTabs && activeTab === "coupang_api" && (
              <div className="mb-6 rounded-2xl border border-slate-700/60 bg-slate-800/40 p-4 md:p-6">
                <div className="mb-6 rounded-xl border border-slate-700/60 bg-slate-800/60 p-4 md:p-5">
                  <h3 className="mb-4 text-sm font-semibold text-white md:text-base">쿠팡파트너스 API KEY</h3>
                  <p className="mb-4 text-xs text-slate-400">
                    <span className="text-indigo-300">{selectedAccount || mainUsername}</span> 계정의 API 키 — 본인글 작성 시 블로그·카페 모두 이 키를 사용합니다. 유료회원글은 유료회원 API 키를 사용합니다.
                  </p>
                  {coupangApiLoading ? (
                    <p className="text-sm text-slate-400">로딩 중...</p>
                  ) : (
                    <div className="space-y-4">
                      <div>
                        <label className="mb-1 block text-xs text-slate-400">Access Key</label>
                        <input
                          type="text"
                          value={coupangApiConfig.coupang_access_key}
                          onChange={(e) => setCoupangApiConfig((c) => ({ ...c, coupang_access_key: e.target.value }))}
                          className="w-full max-w-md rounded-lg border border-slate-600 bg-slate-800/80 px-3 py-2 text-sm text-slate-100 placeholder-slate-500 outline-none focus:border-indigo-500"
                          placeholder="쿠팡 파트너스 Access Key"
                        />
                      </div>
                      <div>
                        <label className="mb-1 block text-xs text-slate-400">Secret Key</label>
                        <input
                          type="password"
                          value={coupangApiConfig.coupang_secret_key}
                          onChange={(e) => setCoupangApiConfig((c) => ({ ...c, coupang_secret_key: e.target.value }))}
                          className="w-full max-w-md rounded-lg border border-slate-600 bg-slate-800/80 px-3 py-2 text-sm text-slate-100 placeholder-slate-500 outline-none focus:border-indigo-500"
                          placeholder="쿠팡 파트너스 Secret Key"
                        />
                      </div>
                    </div>
                  )}
                </div>
                <div className="mb-4 flex flex-wrap items-center gap-3">
                  <label className="flex cursor-pointer items-center gap-2">
                    <input
                      type="checkbox"
                      checked={coupangApiApplyToAll}
                      onChange={(e) => setCoupangApiApplyToAll(e.target.checked)}
                      className="h-4 w-4 rounded border-slate-600 bg-slate-800 text-indigo-600 focus:ring-indigo-500"
                    />
                    <span className="text-sm text-slate-300">전체아이디사용</span>
                  </label>
                  <span className="text-xs text-slate-500">
                    체크 후 저장 시 메인 로그인 아이디({mainUsername})의 API 키를 전체 아이디에 동일하게 저장합니다.
                  </span>
                </div>
                <button
                  type="button"
                  onClick={handleSaveCoupangApiConfig}
                  disabled={coupangApiSaving || coupangApiLoading || !user?.id || (!coupangApiApplyToAll && !selectedAccount)}
                  className="rounded-xl bg-indigo-600 px-6 py-2.5 text-sm font-semibold text-white transition hover:bg-indigo-500 disabled:opacity-50"
                >
                  {coupangApiSaving ? "저장 중..." : "저장"}
                </button>
                <p className="mt-3 text-xs leading-relaxed text-slate-500">
                  users 테이블에 저장됩니다. PC 프로그램에서 본인글 작성 시 이 키를 사용합니다.
                </p>
              </div>
            )}

            {mode === "history" && (
            <>
            <div className="mb-4 overflow-x-auto pb-2">
              <div className="flex gap-2">
                <span className="shrink-0 rounded-full bg-slate-700/60 px-3 py-1.5 text-xs text-slate-300">
                  본인 {summaryCounts.self}
                </span>
                <span className="shrink-0 rounded-full bg-slate-700/60 px-3 py-1.5 text-xs text-slate-300">
                  유료회원 {summaryCounts.paid}
                </span>
                <span className="shrink-0 rounded-full bg-slate-700/60 px-3 py-1.5 text-xs text-slate-300">
                  추천인 {summaryCounts.referrer}
                </span>
                <span className="shrink-0 rounded-full bg-slate-700/60 px-3 py-1.5 text-xs text-slate-300">
                  전체 {todayLogs.length}
                </span>
              </div>
            </div>

            <div className="rounded-2xl border border-slate-700/60 bg-slate-800/40 shadow-xl backdrop-blur overflow-hidden">
              <div className="border-b border-slate-700/60 px-4 py-3 md:px-6 md:py-4">
                <h2 className="text-base font-semibold text-white md:text-lg">
                  작업 내역
                </h2>
                <p className="text-xs text-slate-400 md:text-sm">
                  5분마다 자동 갱신
                </p>
              </div>

              {loading && postLogs.length === 0 ? (
                <div className="flex justify-center py-12 text-slate-400 md:py-16">
                  로딩 중...
                </div>
              ) : postLogs.length === 0 ? (
                <div className="flex justify-center py-12 text-slate-500 md:py-16">
                  포스팅 로그가 없습니다.
                </div>
              ) : todayLogs.length === 0 ? (
                <div className="flex justify-center py-12 text-slate-500 md:py-16">
                  오늘 작업 내역이 없습니다.
                </div>
              ) : (
                <div className="grid grid-cols-1 gap-3 p-4 md:grid-cols-2 md:gap-4 lg:grid-cols-3">
                  {displayedLogs.map((row) => (
                    <PostLogCard key={row.id} row={row} />
                  ))}
                </div>
              )}

              {!loading && todayLogs.length > 0 && totalPages > 1 && (
                <div className="flex flex-wrap items-center justify-center gap-2 border-t border-slate-700/60 p-4">
                  {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => (
                    <button
                      key={p}
                      type="button"
                      onClick={() => setLogPage(p)}
                      className={`min-w-[2.25rem] rounded-lg px-3 py-2 text-sm font-medium transition ${
                        logPage === p
                          ? "bg-indigo-600 text-white"
                          : "border border-slate-600 bg-slate-800/60 text-slate-300 hover:bg-slate-700/60"
                      }`}
                    >
                      {p}
                    </button>
                  ))}
                </div>
              )}
            </div>
            </>
            )}

            {error && (
              <p className="mt-4 text-sm text-rose-400">{error}</p>
            )}
          </>
        )}
      </div>
    </div>
  );
}

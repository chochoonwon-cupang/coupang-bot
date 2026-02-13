"use client";

import { useState, useEffect, useCallback } from "react";

type Task = {
  id: string;
  keyword: string;
  status: string;
  result_url: string | null;
  error_message: string | null;
  created_at: string;
  updated_at?: string;
};

const STATUS_LABEL: Record<string, string> = {
  pending: "대기",
  processing: "진행 중",
  completed: "완료",
  failed: "실패",
  대기: "대기",
  진행: "진행 중",
  완료: "완료",
};

export default function Home() {
  const [keyword, setKeyword] = useState("");
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(false);
  const [submitLoading, setSubmitLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchTasks = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/tasks");
      if (!res.ok) throw new Error("목록 조회 실패");
      const data = await res.json();
      setTasks(data);
      setError(null);
    } catch (e) {
      setError("작업 목록을 불러오지 못했습니다.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTasks();
    const interval = setInterval(fetchTasks, 3000);
    return () => clearInterval(interval);
  }, [fetchTasks]);

  const handleSubmit = async () => {
    const kw = keyword.trim();
    if (!kw) {
      setError("키워드를 입력해주세요.");
      return;
    }
    setSubmitLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/tasks", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ keyword: kw }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "등록 실패");
      setKeyword("");
      await fetchTasks();
    } catch (e) {
      setError(e instanceof Error ? e.message : "등록에 실패했습니다.");
    } finally {
      setSubmitLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 text-slate-100">
      <div className="mx-auto max-w-4xl px-6 py-16">
        <h1 className="mb-2 text-3xl font-bold tracking-tight text-white">
          포스팅 작업 관리
        </h1>
        <p className="mb-12 text-slate-400">
          키워드를 입력하고 발행하면 에이전트가 자동으로 포스팅합니다.
        </p>

        {/* 입력 영역 */}
        <div className="mb-12 rounded-2xl border border-slate-700/60 bg-slate-800/40 p-8 shadow-xl backdrop-blur">
          <label className="mb-3 block text-sm font-medium text-slate-300">
            포스팅할 키워드
          </label>
          <div className="flex gap-4">
            <input
              type="text"
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
              placeholder="예: 무선청소기, 다이어트보조제"
              className="flex-1 rounded-xl border border-slate-600 bg-slate-800/80 px-5 py-4 text-slate-100 placeholder-slate-500 outline-none transition focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/30"
            />
            <button
              onClick={handleSubmit}
              disabled={submitLoading}
              className="rounded-xl bg-indigo-600 px-8 py-4 font-semibold text-white transition hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {submitLoading ? "등록 중..." : "발행"}
            </button>
          </div>
          {error && (
            <p className="mt-3 text-sm text-rose-400">{error}</p>
          )}
        </div>

        {/* 상태 테이블 */}
        <div className="rounded-2xl border border-slate-700/60 bg-slate-800/40 shadow-xl backdrop-blur overflow-hidden">
          <div className="border-b border-slate-700/60 px-6 py-4">
            <h2 className="text-lg font-semibold text-white">
              작업 상태
            </h2>
            <p className="text-sm text-slate-400">
              3초마다 자동 갱신
            </p>
          </div>
          <div className="overflow-x-auto">
            {loading && tasks.length === 0 ? (
              <div className="flex items-center justify-center py-16 text-slate-400">
                로딩 중...
              </div>
            ) : tasks.length === 0 ? (
              <div className="flex items-center justify-center py-16 text-slate-500">
                등록된 작업이 없습니다.
              </div>
            ) : (
              <table className="w-full">
                <thead>
                  <tr className="border-b border-slate-700/60 bg-slate-800/60">
                    <th className="px-6 py-4 text-left text-xs font-medium uppercase tracking-wider text-slate-400">
                      키워드
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-medium uppercase tracking-wider text-slate-400">
                      상태
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-medium uppercase tracking-wider text-slate-400">
                      결과
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-medium uppercase tracking-wider text-slate-400">
                      등록일시
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {tasks.map((t) => (
                    <tr
                      key={t.id}
                      className="border-b border-slate-700/40 transition hover:bg-slate-800/30"
                    >
                      <td className="px-6 py-4 font-medium text-slate-100">
                        {t.keyword}
                      </td>
                      <td className="px-6 py-4">
                        <span
                          className={`inline-flex rounded-full px-3 py-1 text-xs font-medium ${
                            t.status === "pending" || t.status === "대기"
                              ? "bg-amber-500/20 text-amber-400"
                              : t.status === "processing" || t.status === "진행"
                              ? "bg-blue-500/20 text-blue-400"
                              : t.status === "failed"
                              ? "bg-rose-500/20 text-rose-400"
                              : "bg-emerald-500/20 text-emerald-400"
                          }`}
                        >
                          {STATUS_LABEL[t.status] ?? t.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-slate-400 max-w-xs truncate">
                        {t.status === "failed" && t.error_message
                          ? t.error_message
                          : t.result_url || "-"}
                      </td>
                      <td className="px-6 py-4 text-sm text-slate-500">
                        {new Date(t.created_at).toLocaleString("ko-KR")}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

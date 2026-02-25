"use client";

import { useMemo, useState } from "react";

type Period = "day" | "month" | "year";
type Metric = "posts" | "cost" | "net";

const PERIOD_LABEL: Record<Period, string> = {
  day: "하루",
  month: "한달",
  year: "1년",
};

const DAYS: Record<Period, number> = {
  day: 1,
  month: 30,
  year: 365,
};

function formatWon(v: number) {
  return Math.round(v).toLocaleString("ko-KR");
}

function formatCompact(v: number, isWon: boolean) {
  const suffix = isWon ? "원" : "개";
  if (v >= 100000000) return `${(v / 100000000).toFixed(1)}억${suffix}`;
  if (v >= 10000) return `${(v / 10000).toFixed(0)}만${suffix}`;
  return `${formatWon(v)}${suffix}`;
}

export default function ImpactBarPanel() {
  const [manualPerDay] = useState(10);
  const [autoPerDay] = useState(40);
  const [costPerPost] = useState(20);

  const [period, setPeriod] = useState<Period>("day");
  const [metric, setMetric] = useState<Metric>("posts");

  const [hourWage, setHourWage] = useState(10000);
  const [manualHoursPerDay, setManualHoursPerDay] = useState(5);
  const [profitPerPost, setProfitPerPost] = useState(0);

  const { data, maxVal } = useMemo(() => {
    const d = DAYS[period];

    const manualPosts = manualPerDay * d;
    const autoPosts = autoPerDay * d;

    const manualLaborCost = hourWage * manualHoursPerDay * d;
    const autoServiceCost = autoPosts * costPerPost;

    const manualRevenue = manualPosts * profitPerPost;
    const autoRevenue = autoPosts * profitPerPost;

    const manualNet = manualRevenue - manualLaborCost;
    const autoNet = autoRevenue - autoServiceCost;

    let manualVal: number;
    let autoVal: number;

    if (metric === "posts") {
      manualVal = manualPosts;
      autoVal = autoPosts;
    } else if (metric === "cost") {
      manualVal = manualLaborCost;
      autoVal = autoServiceCost;
    } else {
      manualVal = manualNet;
      autoVal = autoNet;
    }

    const max = Math.max(Math.abs(manualVal), Math.abs(autoVal), 1);
    return {
      data: [
        { name: "수작업", value: manualVal, color: "#64748b" },
        { name: "프로그램", value: autoVal, color: "rgba(249, 115, 22, 0.95)" },
      ],
      maxVal: max,
    };
  }, [
    period,
    metric,
    manualPerDay,
    autoPerDay,
    costPerPost,
    hourWage,
    manualHoursPerDay,
    profitPerPost,
  ]);

  const title = useMemo(() => {
    if (metric === "posts") return `포스팅 개수 비교 (${PERIOD_LABEL[period]})`;
    if (metric === "cost") return `비용 비교 (${PERIOD_LABEL[period]})`;
    return `예상 순수익 비교 (${PERIOD_LABEL[period]})`;
  }, [metric, period]);

  return (
    <div className="rounded-2xl border border-slate-700/60 bg-slate-800/60 p-5 shadow-xl backdrop-blur md:p-6">
      {/* 헤더 */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <div className="text-sm text-slate-400">타이밍 임팩트</div>
          <div className="mt-1 text-lg font-bold text-white md:text-xl">{title}</div>
          <div className="mt-1 text-xs text-slate-500">
            수작업 하루 10개 vs 프로그램 하루 40개 · 프로그램 1개 20원 · 수작업 하루 {manualHoursPerDay}시간 기준
          </div>
        </div>

        {/* 기간 탭 */}
        <div className="flex shrink-0 rounded-xl bg-slate-700/50 p-1">
          {(["day", "month", "year"] as Period[]).map((p) => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              className={`rounded-lg px-3 py-1.5 text-xs transition ${
                period === p ? "bg-slate-600 text-white" : "text-slate-400 hover:text-white"
              }`}
            >
              {PERIOD_LABEL[p]}
            </button>
          ))}
        </div>
      </div>

      {/* 보기 탭 */}
      <div className="mt-3 flex flex-wrap gap-2">
        {([
          { k: "posts" as Metric, label: "포스팅 개수" },
          { k: "cost" as Metric, label: "비용 차이" },
          { k: "net" as Metric, label: "예상 순수익" },
        ]).map((m) => (
          <button
            key={m.k}
            onClick={() => setMetric(m.k)}
            className={`rounded-xl border px-3 py-2 text-xs transition ${
              metric === m.k
                ? "border-orange-500/60 bg-orange-500/20 text-orange-400"
                : "border-slate-600 bg-slate-800/50 text-slate-400 hover:text-white"
            }`}
          >
            {m.label}
          </button>
        ))}
      </div>

      {/* 입력 영역 */}
      {(metric === "cost" || metric === "net") && (
        <div className="mt-4 grid grid-cols-1 gap-2 sm:grid-cols-3">
          <label className="rounded-xl border border-slate-600 bg-slate-800/50 p-3">
            <div className="text-xs text-slate-400">시급(원)</div>
            <input
              type="number"
              value={hourWage}
              onChange={(e) => setHourWage(Number(e.target.value || 0))}
              className="mt-1 w-full bg-transparent text-white outline-none"
            />
          </label>
          <label className="rounded-xl border border-slate-600 bg-slate-800/50 p-3">
            <div className="text-xs text-slate-400">수작업 시간/일</div>
            <input
              type="number"
              value={manualHoursPerDay}
              onChange={(e) => setManualHoursPerDay(Number(e.target.value || 0))}
              className="mt-1 w-full bg-transparent text-white outline-none"
            />
          </label>
          <label className="rounded-xl border border-slate-600 bg-slate-800/50 p-3">
            <div className="text-xs text-slate-400">포스팅 1개당 평균 순수익(원)</div>
            <input
              type="number"
              value={profitPerPost}
              onChange={(e) => setProfitPerPost(Number(e.target.value || 0))}
              className="mt-1 w-full bg-transparent text-white outline-none"
            />
          </label>
        </div>
      )}

      {/* SVG 막대그래프 (그룹드: 수작업 회색, 프로그램 주황) */}
      <div className="mt-4 h-72 min-h-[300px] md:h-80 md:min-h-[340px]">
        <BarChartSvg data={data} maxVal={maxVal} metric={metric} />
      </div>

      {/* 하단 임팩트 문구 */}
      <div className="mt-3 flex flex-col gap-2 rounded-xl border border-slate-700/60 bg-slate-800/40 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="text-sm text-slate-300">
          {metric === "posts" && (
            <>
              프로그램은 <span className="font-bold text-white">수작업 대비 4배</span>로 누적됩니다.
            </>
          )}
          {metric === "cost" && (
            <>
              같은 기간 기준, 비용 구조가 <span className="font-bold text-white">완전히 달라집니다</span>.
            </>
          )}
          {metric === "net" && (
            <>
              시작 시점이 빠를수록 <span className="font-bold text-white">누적 격차가 벌어집니다</span>.
            </>
          )}
        </div>
        <div className="text-xs text-slate-500">* 시뮬레이션(입력값 기반)</div>
      </div>
    </div>
  );
}

function BarChartSvg({
  data,
  maxVal,
  metric,
}: {
  data: { name: string; value: number; color: string }[];
  maxVal: number;
  metric: Metric;
}) {
  const w = 560;
  const h = 320;
  const pad = { top: 56, right: 48, bottom: 52, left: 48 };
  const chartW = w - pad.left - pad.right;
  const chartH = h - pad.top - pad.bottom;
  const barW = 96;
  const gap = 64;
  const totalBarW = data.length * barW + (data.length - 1) * gap;
  const startX = pad.left + (chartW - totalBarW) / 2 + barW / 2;

  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="w-full h-full min-w-0" preserveAspectRatio="xMidYMid meet">
      {/* Grid */}
      {[0, 1, 2, 3, 4].map((i) => (
        <line
          key={i}
          x1={pad.left}
          y1={pad.top + (chartH / 4) * i}
          x2={pad.left + chartW}
          y2={pad.top + (chartH / 4) * i}
          stroke="rgba(255,255,255,0.08)"
          strokeDasharray="3 3"
        />
      ))}

      {/* Bars */}
      {data.map((item, i) => {
        const ratio = maxVal > 0 ? Math.abs(item.value) / maxVal : 0;
        const barH = Math.max(6, ratio * chartH);
        const x = startX + i * (barW + gap) - barW / 2;
        const y = pad.top + chartH - barH;
        const labelText = formatCompact(item.value, metric !== "posts");
        return (
          <g key={item.name}>
            <rect
              x={x}
              y={y}
              width={barW}
              height={barH}
              fill={item.color}
              rx={10}
              ry={10}
            />
            <text x={x + barW / 2} y={h - 16} textAnchor="middle" fill="#94a3b8" fontSize={15} fontWeight={500}>
              {item.name}
            </text>
            {/* 값 라벨 - 막대 위에 여유 있게 표시 */}
            <text
              x={x + barW / 2}
              y={Math.max(pad.top - 12, y - 16)}
              textAnchor="middle"
              fill="#ffffff"
              fontSize={16}
              fontWeight={700}
              style={{ textShadow: "0 1px 2px rgba(0,0,0,0.8)" }}
            >
              {labelText}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

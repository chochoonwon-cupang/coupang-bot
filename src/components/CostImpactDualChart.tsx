"use client";

function won(n: number) {
  return Math.round(n).toLocaleString("ko-KR");
}

const WAGE_PER_HOUR = 10320; // 최저임금
const MANUAL_HOURS_PER_DAY = 5;
const MANUAL_POSTS_PER_DAY = 10;

const AUTO_POSTS_PER_DAY = 40;
const AUTO_COST_PER_POST = 20;
const AUTO_COST_PER_DAY = AUTO_POSTS_PER_DAY * AUTO_COST_PER_POST; // 800원

const periods = [
  { key: "하루", days: 1 },
  { key: "한달", days: 30 },
  { key: "1년", days: 365 },
];

function formatCompact(v: number, isWon: boolean) {
  const suffix = isWon ? "원" : "개";
  if (v >= 100000000) return `${(v / 100000000).toFixed(1)}억${suffix}`;
  if (v >= 10000) return `${(v / 10000).toFixed(0)}만${suffix}`;
  return `${won(v)}${suffix}`;
}

function DualBarChartSvg({
  data,
  format,
}: {
  data: { period: string; manual: number; program: number }[];
  format: "count" | "won";
}) {
  const w = 400;
  const h = 260;
  const pad = { top: 52, right: 28, bottom: 52, left: 28 };
  const chartW = w - pad.left - pad.right;
  const chartH = h - pad.top - pad.bottom;

  const maxVal = Math.max(...data.flatMap((d) => [d.manual, d.program]), 1);
  const barW = 36;
  const gap = 16;

  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="w-full h-full min-h-[260px]" preserveAspectRatio="xMidYMid meet">
      {data.map((d, i) => {
        const groupWidth = chartW / data.length;
        const groupX = pad.left + (i + 0.5) * groupWidth;
        const manualH = Math.max(6, (d.manual / maxVal) * chartH);
        const programH = Math.max(6, (d.program / maxVal) * chartH);

        const manualY = pad.top + chartH - manualH;
        const programY = pad.top + chartH - programH;

        const fmt = (v: number) => (format === "count" ? `${won(v)}개` : formatCompact(v, true));

        return (
          <g key={d.period}>
            {/* 수작업 */}
            <rect
              x={groupX - barW - gap / 2}
              y={manualY}
              width={barW}
              height={manualH}
              fill="rgba(148,163,184,0.9)"
              rx={8}
            />
            <text
              x={groupX - barW / 2 - gap / 2}
              y={Math.max(pad.top - 14, manualY - 16)}
              textAnchor="middle"
              fill="#ffffff"
              fontSize={14}
              fontWeight={700}
              style={{ textShadow: "0 1px 2px rgba(0,0,0,0.8)" }}
            >
              {fmt(d.manual)}
            </text>
            {/* 프로그램 */}
            <rect
              x={groupX + gap / 2}
              y={programY}
              width={barW}
              height={programH}
              fill="rgba(249,115,22,0.95)"
              rx={8}
            />
            <text
              x={groupX + barW / 2 + gap / 2}
              y={Math.max(pad.top - 14, programY - 16)}
              textAnchor="middle"
              fill="#ffffff"
              fontSize={14}
              fontWeight={700}
              style={{ textShadow: "0 1px 2px rgba(0,0,0,0.8)" }}
            >
              {fmt(d.program)}
            </text>
            {/* X축 라벨 */}
            <text x={groupX} y={h - 14} textAnchor="middle" fill="#94a3b8" fontSize={15} fontWeight={500}>
              {d.period}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

export default function CostImpactDualChart() {
  const manualCostPerDay = WAGE_PER_HOUR * MANUAL_HOURS_PER_DAY; // 103,200원/일

  const postsData = periods.map((p) => ({
    period: p.key,
    manual: MANUAL_POSTS_PER_DAY * p.days,
    program: AUTO_POSTS_PER_DAY * p.days,
  }));

  const costData = periods.map((p) => ({
    period: p.key,
    manual: manualCostPerDay * p.days,
    program: AUTO_COST_PER_DAY * p.days,
  }));

  const monthManualCost = manualCostPerDay * 30;
  const monthProgramCost = AUTO_COST_PER_DAY * 30;
  const saveMonth = monthManualCost - monthProgramCost;

  const yearManualCost = manualCostPerDay * 365;
  const yearProgramCost = AUTO_COST_PER_DAY * 365;
  const saveYear = yearManualCost - yearProgramCost;

  const costMultiplier = monthProgramCost > 0 ? monthManualCost / monthProgramCost : 0;

  return (
    <div className="rounded-2xl border border-slate-700/60 bg-slate-800/60 p-5 shadow-xl backdrop-blur md:p-6">
      {/* 헤더 */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <div className="text-sm text-slate-400">시간 대비 비용 비교</div>
          <div className="mt-1 text-lg font-bold text-white">
            수작업(10개/일) vs 프로그램(40개/일)
          </div>
          <div className="mt-1 text-xs text-slate-500">
            수작업: {won(WAGE_PER_HOUR)}원/시간 × {MANUAL_HOURS_PER_DAY}시간 = {won(manualCostPerDay)}원/일 · 프로그램: 20원 × 40개 = {won(AUTO_COST_PER_DAY)}원/일
          </div>
        </div>

        {/* 우측 임팩트 배지 */}
        <div className="flex shrink-0 flex-wrap gap-2">
          <div className="rounded-xl border border-slate-600/60 bg-slate-800/80 px-3 py-2 text-right">
            <div className="text-xs text-slate-400">한달 기준 절감</div>
            <div className="text-base font-bold text-emerald-400">{won(saveMonth)}원</div>
          </div>
          <div className="rounded-xl border border-slate-600/60 bg-slate-800/80 px-3 py-2 text-right">
            <div className="text-xs text-slate-400">일년 기준 절감</div>
            <div className="text-base font-bold text-emerald-400">{won(saveYear)}원</div>
          </div>
        </div>
      </div>

      {/* 그래프 2개: 포스팅 + 비용 */}
      <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-2">
        {/* 1) 포스팅 개수 */}
        <div className="rounded-xl border border-slate-700/60 bg-slate-800/40 p-4">
          <div className="mb-2 flex items-center justify-between">
            <div className="text-sm font-semibold text-white">포스팅 개수</div>
            <div className="text-xs text-slate-500">하루 · 한달 · 1년</div>
          </div>

          <div className="h-56 min-h-[260px]">
            <DualBarChartSvg data={postsData} format="count" />
          </div>

          <div className="mt-2 text-xs text-slate-500">
            프로그램은 수작업 대비 <span className="font-semibold text-white">4배</span> 누적됩니다.
          </div>
        </div>

        {/* 2) 비용 */}
        <div className="rounded-xl border border-slate-700/60 bg-slate-800/40 p-4">
          <div className="mb-2 flex items-center justify-between">
            <div className="text-sm font-semibold text-white">비용</div>
            <div className="text-xs text-slate-500">하루 · 한달 · 1년</div>
          </div>

          <div className="h-56 min-h-[260px]">
            <DualBarChartSvg data={costData} format="won" />
          </div>

          <div className="mt-2 text-xs text-slate-500">
            한달 기준 수작업 <span className="font-semibold text-white">{won(monthManualCost)}원</span> vs 프로그램{" "}
            <span className="font-semibold text-white">{won(monthProgramCost)}원</span>
            {costMultiplier > 0 && (
              <span className="ml-1 text-emerald-400">
                · 수작업이 <span className="font-bold">{costMultiplier.toFixed(1)}배</span> 비쌈
              </span>
            )}
          </div>
        </div>
      </div>

      {/* 하단 한 줄 임팩트 */}
      <div className="mt-4 rounded-xl border border-slate-700/60 bg-slate-800/40 px-4 py-3 text-sm text-slate-300">
        지금 시작하면, 같은 기간에 <span className="font-semibold text-white">포스팅은 더 많이</span>,{" "}
        <span className="font-semibold text-white">비용은 훨씬 적게</span> 누적됩니다.
      </div>
    </div>
  );
}

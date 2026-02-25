"use client";

const demoSystemUsage = [10, 18, 25, 35, 42, 52, 58, 65, 72, 76, 82, 80];
const demoManualPosting = [70, 65, 58, 52, 48, 42, 38, 32, 28, 25, 22, 20];
const demoSideIncomeInterest = [45, 48, 55, 62, 68, 72, 78, 82, 85, 88, 90, 92];
const MONTHS = ["1월", "2월", "3월", "4월", "5월", "6월", "7월", "8월", "9월", "10월", "11월", "12월"];

type ChartConfig = {
  data: number[];
  color: string;
  title: string;
  desc: string;
};

const CHART_CONFIGS: ChartConfig[] = [
  { data: demoSystemUsage, color: "#f97316", title: "시스템 이용률 추세", desc: "반복 작업은 자동화로 이동" },
  { data: demoManualPosting, color: "#64748b", title: "직접 포스팅(수동) 추세", desc: "수동 작성은 점점 비효율" },
  { data: demoSideIncomeInterest, color: "#22c55e", title: "부업/재테크 관심도 추세", desc: "아는 사람은 시스템으로 운영" },
];

function SvgAreaChart({ data, color, id }: { data: number[]; color: string; id: string }) {
  const w = 280;
  const h = 140;
  const pad = { top: 8, right: 8, bottom: 24, left: 8 };
  const chartW = w - pad.left - pad.right;
  const chartH = h - pad.top - pad.bottom;
  const max = 100;
  const min = 0;

  const points = data.map((v, i) => {
    const x = pad.left + (i / Math.max(1, data.length - 1)) * chartW;
    const y = pad.top + chartH - ((v - min) / (max - min)) * chartH;
    return `${x},${y}`;
  });
  const areaPath = `M ${points.join(" L ")} L ${pad.left + chartW},${pad.top + chartH} L ${pad.left},${pad.top + chartH} Z`;
  const linePath = `M ${points.join(" L ")}`;

  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="w-full h-full min-h-[140px]" preserveAspectRatio="none">
      <defs>
        <linearGradient id={id} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity={0.4} />
          <stop offset="100%" stopColor={color} stopOpacity={0} />
        </linearGradient>
      </defs>
      <path d={areaPath} fill={`url(#${id})`} />
      <path d={linePath} fill="none" stroke={color} strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function ChartCard({ config, index }: { config: ChartConfig; index: number }) {
  return (
    <div className="rounded-2xl border border-slate-700/60 bg-slate-800/60 p-6 shadow-xl backdrop-blur transition-transform duration-200 hover:-translate-y-1">
      <h3 className="text-base font-semibold text-white md:text-lg">{config.title}</h3>
      <p className="mt-1 text-xs text-slate-400 md:text-sm">{config.desc}</p>
      <div className="mt-4 h-40 w-full md:h-48">
        <SvgAreaChart data={config.data} color={config.color} id={`chart-grad-${index}`} />
      </div>
      <div className="mt-2 flex justify-between gap-1 overflow-hidden">
        {MONTHS.map((m, i) => (
          <span key={m} className="text-[9px] text-slate-500 md:text-[10px]">
            {i % 3 === 0 ? m : ""}
          </span>
        ))}
      </div>
    </div>
  );
}

export default function TrendCharts() {
  return (
    <section className="mt-28 md:mt-36">
      <h2 className="text-center text-2xl font-bold text-white md:text-3xl lg:text-4xl">
        추세로 보는 자동화의 시대
      </h2>
      <p className="mx-auto mt-4 max-w-2xl text-center text-sm text-slate-400 md:text-base">
        반복 작업은 자동화로 이동 · 수동 작성은 점점 비효율
        <br />
        아는 사람은 시스템으로 운영
      </p>
      <div className="mt-12 grid gap-6 sm:grid-cols-2 xl:grid-cols-3">
        {CHART_CONFIGS.map((config, i) => (
          <ChartCard key={config.title} config={config} index={i} />
        ))}
      </div>
    </section>
  );
}

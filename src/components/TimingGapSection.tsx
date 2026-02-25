"use client";

// 나중에 Supabase에서 가져올 수 있도록 구조화, 현재는 하드코딩
const ADOPTION_RATE = 23;

const simulationData = [
  { month: "1개월", manual: 10, auto: 18 },
  { month: "2개월", manual: 18, auto: 38 },
  { month: "3개월", manual: 28, auto: 65 },
  { month: "4개월", manual: 40, auto: 95 },
  { month: "5개월", manual: 55, auto: 130 },
  { month: "6개월", manual: 72, auto: 170 },
];

function LineChartSvg() {
  const w = 600;
  const h = 280;
  const pad = { top: 20, right: 20, bottom: 40, left: 50 };
  const chartW = w - pad.left - pad.right;
  const chartH = h - pad.top - pad.bottom;

  const maxVal = Math.max(...simulationData.flatMap((d) => [d.manual, d.auto]));
  const minVal = 0;

  const toPoint = (val: number, i: number) => {
    const x = pad.left + (i / (simulationData.length - 1)) * chartW;
    const y = pad.top + chartH - ((val - minVal) / (maxVal - minVal)) * chartH;
    return { x, y };
  };

  const manualPath = simulationData.map((d, i) => toPoint(d.manual, i)).map((p) => `${p.x},${p.y}`).join(" L ");
  const autoPath = simulationData.map((d, i) => toPoint(d.auto, i)).map((p) => `${p.x},${p.y}`).join(" L ");

  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="w-full h-full min-h-[280px]" preserveAspectRatio="xMidYMid meet">
      {/* Grid */}
      {[0, 1, 2, 3, 4].map((i) => (
        <line
          key={i}
          x1={pad.left}
          y1={pad.top + (chartH / 4) * i}
          x2={pad.left + chartW}
          y2={pad.top + (chartH / 4) * i}
          stroke="#1e293b"
          strokeDasharray="3 3"
        />
      ))}
      {/* Manual line (gray) */}
      <path d={`M ${manualPath}`} fill="none" stroke="#64748b" strokeWidth={3} strokeLinecap="round" strokeLinejoin="round" />
      {/* Auto line (green) - slightly thicker */}
      <path
        d={`M ${autoPath}`}
        fill="none"
        stroke="#10b981"
        strokeWidth={4}
        strokeLinecap="round"
        strokeLinejoin="round"
        filter="url(#glow)"
      />
      <defs>
        <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
          <feGaussianBlur stdDeviation="2" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
      {/* X-axis labels */}
      {simulationData.map((d, i) => {
        const x = pad.left + (i / (simulationData.length - 1)) * chartW;
        return (
          <text key={d.month} x={x} y={h - 12} textAnchor="middle" fill="#94a3b8" fontSize={12}>
            {d.month}
          </text>
        );
      })}
    </svg>
  );
}

export default function TimingGapSection() {
  return (
    <div className="w-full rounded-2xl border border-slate-700/60 bg-slate-800/60 p-6 shadow-xl backdrop-blur md:p-8">
      {/* 상단 도입률 영역 */}
      <div className="mb-6">
        <div className="text-2xl font-bold text-emerald-400 md:text-3xl">
          자동화 도입률 {ADOPTION_RATE}%
        </div>
        <div className="mt-2 text-base text-slate-300 md:text-lg">
          지금 시작한 그룹이 가장 빠른 구간입니다.
        </div>
      </div>

      {/* 격차 그래프 */}
      <div className="h-80">
        <LineChartSvg />
      </div>

      {/* 범례 */}
      <div className="mt-4 flex gap-6 text-sm">
        <span className="flex items-center gap-2">
          <span className="h-0.5 w-6 rounded bg-slate-500" />
          <span className="text-slate-400">수동 운영</span>
        </span>
        <span className="flex items-center gap-2">
          <span className="h-0.5 w-6 rounded bg-emerald-500" />
          <span className="text-slate-400">자동화 운영</span>
        </span>
      </div>

      <div className="mt-4 text-sm text-slate-500">
        * 위 수치는 운영 패턴 기반 시뮬레이션 예시입니다.
      </div>
    </div>
  );
}

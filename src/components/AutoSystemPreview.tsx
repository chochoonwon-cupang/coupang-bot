"use client";

import { useState, useEffect } from "react";

const STATUS_TEXTS = ["자동 생성 중…", "링크 변환 중…", "게시 대기열…"] as const;

const BADGES = [
  { value: "20", unit: "원" },
  { value: "800", unit: "원" },
] as const;

export default function AutoSystemPreview() {
  const [statusIndex, setStatusIndex] = useState(0);
  const [pulseIndex, setPulseIndex] = useState(0);

  useEffect(() => {
    const id = setInterval(() => setStatusIndex((i) => (i + 1) % STATUS_TEXTS.length), 2500);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    const id = setInterval(() => setPulseIndex((i) => (i + 1) % BADGES.length), 1500);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="rounded-2xl border border-slate-600/60 bg-slate-800/80 p-4 shadow-2xl backdrop-blur md:p-6">
      {/* Top skeleton boxes with shimmer */}
      <div className="flex gap-2">
        <div className="skeleton-shimmer h-12 flex-1 overflow-hidden rounded-lg bg-slate-700/80" />
        <div className="skeleton-shimmer animation-delay-200 h-12 flex-1 overflow-hidden rounded-lg bg-slate-700/80" />
        <div className="skeleton-shimmer animation-delay-400 h-12 w-10 overflow-hidden rounded-lg bg-slate-700/80" />
      </div>

      {/* Status text */}
      <p className="mt-3 text-xs text-slate-400 transition-opacity duration-300 md:text-sm">
        {STATUS_TEXTS[statusIndex]}
      </p>

      {/* Graph area with moving bars */}
      <div className="mt-3 flex h-20 items-end gap-1 rounded-lg bg-slate-700/60 p-2">
        {[40, 55, 45, 70, 60, 85, 75, 90, 80, 95, 88, 100].map((h, i) => (
          <div
            key={i}
            className="animate-bar-rise flex-1 rounded-sm bg-gradient-to-t from-orange-500/80 to-orange-400/60"
            style={{
              height: `${h}%`,
              animationDelay: `${i * 80}ms`,
              animationFillMode: "both",
            }}
          />
        ))}
      </div>

      {/* Badges with pulse */}
      <div className="mt-3 flex gap-2">
        {BADGES.map((b, i) => (
          <span
            key={b.value}
            className={`inline-flex items-center rounded-lg px-3 py-1.5 text-xs font-semibold transition-all duration-500 ${
              pulseIndex === i
                ? "animate-pulse-badge bg-orange-500/40 text-orange-300 ring-1 ring-orange-400/50"
                : "bg-slate-600/80 text-slate-400"
            }`}
          >
            {b.value}
            <span className="ml-0.5 text-[10px] opacity-80">{b.unit}</span>
          </span>
        ))}
      </div>
    </div>
  );
}

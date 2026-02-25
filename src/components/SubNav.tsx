"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const MENU_ITEMS = [
  { href: "/", label: "자동화시스템" },
  { href: "/work-history", label: "작업내역" },
  { href: "/work-settings", label: "작업설정" },
  { href: "/youtube", label: "유튜브방송" },
] as const;

export default function SubNav() {
  const pathname = usePathname();

  return (
    <nav className="sticky top-[57px] z-40 border-b border-slate-700/60 bg-slate-800/60 backdrop-blur">
      <div className="mx-auto max-w-6xl px-4 py-2 md:px-8">
        <div
          className="flex justify-start gap-2 overflow-x-auto scrollbar-hide md:justify-center md:overflow-visible"
          style={{
            WebkitOverflowScrolling: "touch",
            scrollbarWidth: "none",
            msOverflowStyle: "none",
          }}
        >
          {MENU_ITEMS.map(({ href, label }) => {
            const isActive = pathname === href || (pathname === "/auto-system" && href === "/");
            return (
              <Link
                key={href}
                href={href}
                className={`min-h-[44px] shrink-0 rounded-full px-4 py-3 text-sm font-medium transition md:min-h-0 md:px-6 md:py-2.5 md:text-base ${
                  isActive
                    ? "bg-indigo-600 text-white"
                    : "bg-slate-700/60 text-slate-300 hover:bg-slate-700 hover:text-white"
                }`}
              >
                {label}
              </Link>
            );
          })}
        </div>
      </div>
    </nav>
  );
}

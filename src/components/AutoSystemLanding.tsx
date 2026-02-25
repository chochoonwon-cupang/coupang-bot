import Link from "next/link";
import FadeInScroll from "@/components/FadeInScroll";
import CostImpactDualChart from "@/components/CostImpactDualChart";
import TimingGapSection from "@/components/TimingGapSection";
import TrendCharts from "@/components/TrendCharts";

const STEPS = [
  { step: 1, title: "상품 자동 수집", desc: "쿠팡 상품 데이터를 자동으로 불러옵니다." },
  { step: 2, title: "파트너 링크 자동 생성", desc: "쿠팡파트너스 수익 링크로 자동 변환합니다." },
  { step: 3, title: "콘텐츠 자동 구성", desc: "상품 정보 기반으로 게시 가능한 형태로 자동 구성합니다." },
  { step: 4, title: "자동 게시 및 수익 연결", desc: "설정된 플랫폼에 자동 게시하고 수익 구조를 완성합니다." },
] as const;

const WHY_ITEMS = [
  { title: "반복 작업 제거", desc: "수작업 등록 시간을 대폭 단축" },
  { title: "대량 처리 가능", desc: "여러 상품을 동시에 관리" },
  { title: "수익 구조 확장", desc: "클릭 기반 수익 모델 자동 확장" },
] as const;

const FEATURES = [
  "클릭 유도 구조 설계",
  "파트너 링크 최적화",
  "자동화 기반 대량 운영",
  "장기 운영 가능한 시스템 구조",
] as const;

export default function AutoSystemLanding() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 text-slate-100">
      <main className="mx-auto max-w-7xl px-4 py-16 md:px-8 md:py-20 lg:py-28">
        {/* Hero - 2 columns on desktop */}
        <section className="flex flex-col items-center gap-12 lg:flex-row lg:items-center lg:justify-center lg:gap-16">
          <div className="flex-1 text-center">
            <h1 className="animate-fade-slide-up text-3xl font-bold tracking-tight text-white md:text-4xl lg:text-5xl xl:text-6xl">
              쿠팡파트너스
              <br />
              수익을 자동화하다
            </h1>
            <p className="animate-fade-slide-up animate-delay-100 mx-auto mt-5 max-w-xl text-base text-slate-300 md:text-lg">
              상품 수집부터 파트너 링크 생성
              <br />
              자동 게시까지 수익 구조를 자동화하는 플랫폼
            </p>
            <p className="animate-fade-slide-up animate-delay-300 mt-8 text-base font-bold text-orange-400 md:text-lg">
              하루 40개 기준 800원
            </p>
          </div>
        </section>

        {/* Price Impact - 타이밍 임팩트 패널 (기간/보기 탭, 막대그래프) */}
        <section className="mt-28 md:mt-36">
          <h2 className="text-center text-2xl font-bold text-white md:text-3xl lg:text-4xl">
            시간 대비 비용 비교
          </h2>
          <p className="mt-3 text-center text-base text-slate-500 md:text-lg">
            단돈 800원, 당신의 소중한 20시간을
              <br />
              되찾기에 가장 완벽한 금액 입니다.
          </p>
          <div className="mx-auto mt-12 max-w-5xl">
            <CostImpactDualChart />
          </div>
        </section>

        {/* Manual vs Auto comparison */}
        <section className="mt-28 md:mt-36">
          <h2 className="text-center text-2xl font-bold text-white md:text-3xl lg:text-4xl">
            시간 대비 임팩트
          </h2>
          <p className="mx-auto mt-4 max-w-2xl text-center text-sm text-slate-400 md:text-base">
            사람이 직접 하루 10개 작성하려면 약 5시간 소요
            <br />
            이 시스템은 40개를 800원으로 자동 생성/게시
          </p>
          <div className="mt-12 grid gap-6 sm:grid-cols-2">
            <div className="card-hover-lift rounded-2xl border border-slate-700/60 bg-slate-800/60 p-8 shadow-xl backdrop-blur">
              <p className="text-sm font-medium text-slate-400">수동 작성</p>
              <p className="mt-3 text-3xl font-bold text-slate-300 md:text-4xl">
                10개 <span className="text-slate-500">/</span> 5시간
              </p>
              <p className="mt-2 text-sm text-slate-500">직접 작성 시 대략 소요 시간</p>
            </div>
            <div className="card-hover-lift rounded-2xl border-2 border-orange-500/60 bg-orange-500/10 p-8 shadow-xl shadow-orange-500/10 backdrop-blur">
              <span className="inline-block rounded-full bg-orange-500/30 px-3 py-1 text-xs font-semibold text-orange-400">
                추천
              </span>
              <p className="mt-3 text-sm font-medium text-slate-400">자동화</p>
              <p className="mt-2 text-3xl font-bold text-white md:text-4xl">
                40개 <span className="text-orange-400">/</span> 800원
              </p>
              <p className="mt-2 text-sm text-slate-400">자동 생성 · 게시 흐름까지 지원</p>
            </div>
          </div>
        </section>

        <FadeInScroll>
          <TrendCharts />
        </FadeInScroll>

        {/* 6개월 격차 시뮬레이션 */}
        <FadeInScroll>
          <section className="mt-28 md:mt-36">
            <h2 className="mb-4 text-center text-2xl font-bold text-white md:text-3xl">
              6개월 누적 격차 시뮬레이션
            </h2>
            <div className="mx-auto max-w-4xl">
              <TimingGapSection />
            </div>
          </section>
        </FadeInScroll>

        {/* Trend / Insight section */}
        <section className="mt-28 md:mt-36">
          <h2 className="text-center text-2xl font-bold text-white md:text-3xl lg:text-4xl">
            트렌드와 인사이트
          </h2>
          <div className="mx-auto mt-12 max-w-3xl">
            <div className="rounded-2xl border border-slate-700/60 bg-slate-800/60 p-8 shadow-xl backdrop-blur md:p-10">
              <ul className="space-y-4 text-slate-300 md:text-lg">
                <li className="flex items-start gap-3">
                  <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-orange-500" />
                  <span>올해 파트너스의 가장 큰 이슈는 <strong className="text-white">AI 자동발행 시스템</strong>입니다.</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-orange-500" />
                  <span>AI 자동화가 표준이 되는 중이며, 수동으로 하는 사람은 점점 줄어듭니다.</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-orange-500" />
                  <span>아는 사람만 먼저 쓰는 방식 — <strong className="text-white">정보 격차</strong>가 수익 격차로 이어집니다.</span>
                </li>
              </ul>
            </div>
          </div>
        </section>

        {/* Why Automation */}
        <section className="mt-28 md:mt-36">
          <h2 className="text-center text-2xl font-bold text-white md:text-3xl lg:text-4xl">
            왜 자동화가 필요한가?
          </h2>
          <div className="mt-12 grid gap-6 sm:grid-cols-3">
            {WHY_ITEMS.map(({ title, desc }) => (
              <div
                key={title}
                className="card-hover-lift rounded-2xl border border-slate-700/60 bg-slate-800/60 p-6 shadow-xl backdrop-blur"
              >
                <h3 className="text-lg font-semibold text-white">{title}</h3>
                <p className="mt-2 text-sm text-slate-400">{desc}</p>
              </div>
            ))}
          </div>
        </section>

        {/* WOW section */}
        <section className="mt-28 md:mt-36 text-center">
          <h2 className="text-2xl font-bold text-white md:text-3xl lg:text-4xl">
            이제는 &apos;포스팅&apos;이 아니라 &apos;시스템&apos;입니다.
          </h2>
          <p className="mx-auto mt-4 max-w-2xl text-base text-slate-400 md:text-lg">
            상품 수집 → 링크 생성 → 콘텐츠 구성 → 게시 흐름을 한 번에 자동화합니다.
          </p>
        </section>

        {/* System Steps */}
        <section className="mt-28 md:mt-36">
          <h2 className="text-center text-2xl font-bold text-white md:text-3xl lg:text-4xl">
            자동화 수익 구조
          </h2>
          <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {STEPS.map(({ step, title, desc }) => (
              <div
                key={step}
                className="card-hover-lift rounded-2xl border border-slate-700/60 bg-slate-800/60 p-6 shadow-xl backdrop-blur"
              >
                <span className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-orange-500/20 text-sm font-bold text-orange-400">
                  {step}
                </span>
                <h3 className="mt-4 text-lg font-semibold text-white">{title}</h3>
                <p className="mt-2 text-sm text-slate-400">{desc}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Revenue Platform Features */}
        <section className="mt-28 md:mt-36">
          <h2 className="text-center text-2xl font-bold text-white md:text-3xl lg:text-4xl">
            수익 중심 설계
          </h2>
          <div className="mx-auto mt-12 max-w-2xl">
            <div className="rounded-2xl border border-slate-700/60 bg-slate-800/60 p-8 shadow-xl backdrop-blur">
              <ul className="space-y-4">
                {FEATURES.map((item) => (
                  <li key={item} className="flex items-center gap-3 text-slate-200">
                    <span className="h-2 w-2 shrink-0 rounded-full bg-orange-500" />
                    <span className="text-base md:text-lg">{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </section>

        {/* Bottom CTA */}
        <section className="mt-28 text-center md:mt-36">
          <p className="text-slate-400">수익 자동화를 시작해 보세요</p>
          <p className="mt-1 text-xs text-slate-500 md:text-sm">
            하루 40개 기준 800원 — 수동 작성 대비 시간을 절약하세요
          </p>
          <div className="mt-6 flex flex-col items-center justify-center gap-4 sm:flex-row">
            <Link
              href="/work-settings"
              className="inline-flex min-h-[52px] min-w-[160px] items-center justify-center rounded-xl bg-orange-500 px-8 py-3.5 text-base font-semibold text-white shadow-lg shadow-orange-500/25 transition hover:bg-orange-600"
            >
              지금 시작하기
            </Link>
            <Link
              href="/work-history"
              className="inline-flex min-h-[52px] min-w-[160px] items-center justify-center rounded-xl border border-slate-600 bg-slate-800/80 px-8 py-3.5 text-base font-semibold text-slate-200 transition hover:bg-slate-700 hover:text-white"
            >
              작업내역 보기
            </Link>
          </div>
        </section>
      </main>
    </div>
  );
}

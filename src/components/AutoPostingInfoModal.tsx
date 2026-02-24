"use client";

const ACCENT = "#22c55e";

export default function AutoPostingInfoModal({
  isOpen,
  onClose,
  onStart,
}: {
  isOpen: boolean;
  onClose: () => void;
  onStart?: () => void;
}) {
  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-[200] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
      onClick={onClose}
    >
      <div
        className="flex max-h-[90vh] w-full max-w-[420px] flex-col overflow-hidden rounded-2xl border border-slate-700/60 bg-slate-800/95 shadow-xl md:max-w-[560px]"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex-shrink-0 border-b border-slate-700/60 bg-slate-800/80 px-4 py-4">
          <h2 className="text-center text-lg font-bold text-white md:text-xl">
            쿠팡파트너스 자동포스팅 안내
          </h2>
        </div>

        <div className="flex-1 overflow-y-auto overscroll-contain p-4">
          <div className="space-y-4">
            {/* 고민 해결 */}
            <section className="rounded-xl border border-slate-600/60 bg-slate-800/60 p-4">
              <h3 className="mb-3 text-sm font-semibold text-slate-200">
                아이디가 없어서 고민이신가요?
              </h3>
              <ul className="space-y-2 text-sm text-slate-300">
                <li className="flex items-start gap-2">
                  <span className="text-[#22c55e]">✔</span>
                  <span>
                    <strong className="text-[#22c55e]">아이디 한달 포스팅 대행</strong>
                    <br />
                    하루 40개 × 한달 약 1,200개 자동 포스팅
                  </span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-[#22c55e]">✔</span>
                  <span>
                    <strong className="text-[#22c55e]">아이디 한달 임대</strong>
                    <br />
                    월 10,000원 (노출 걱정 없이 사용)
                  </span>
                </li>
              </ul>
            </section>

            {/* 자동포스팅 비용 */}
            <section className="rounded-xl border border-slate-600/60 bg-slate-800/60 p-4">
              <h3 className="mb-3 text-sm font-semibold text-slate-200">
                자동포스팅 비용 안내
              </h3>
              <p className="mb-4 text-sm text-slate-300">
                포스팅 1개 = <strong className="text-[#22c55e]">10원</strong>
                <br />
                카페 자동가입 1회 = <strong className="text-[#22c55e]">10원</strong>
              </p>
              <p className="mb-4 text-sm text-slate-300">
                하루 80개 포스팅
                <br />
                (유료회원 40개 + 본인글 40개)
              </p>
              <ul className="space-y-1 text-sm">
                <li className="flex items-center gap-2">
                  <span className="text-[#22c55e]">✔</span>
                  <span>
                    하루 비용: <strong className="text-[#22c55e]">800원</strong>
                  </span>
                </li>
                <li className="flex items-center gap-2">
                  <span className="text-[#22c55e]">✔</span>
                  <span>
                    한달 비용: <strong className="text-[#22c55e]">약 24,000원</strong>
                  </span>
                </li>
              </ul>
            </section>

            {/* 카페가입 비용 */}
            <section className="rounded-xl border border-slate-600/60 bg-slate-800/60 p-4">
              <h3 className="mb-3 text-sm font-semibold text-slate-200">
                카페가입 비용
              </h3>
              <p className="text-sm text-slate-300">
                카페가입 50개 × 3회
              </p>
              <p className="mt-2 flex items-center gap-2">
                <span className="text-[#22c55e]">✔</span>
                <span>한달 약 <strong className="text-[#22c55e]">1,500원</strong></span>
              </p>
            </section>

            {/* 서버 이용료 */}
            <section className="rounded-xl border border-slate-600/60 bg-slate-800/60 p-4">
              <h3 className="mb-3 text-sm font-semibold text-slate-200">
                서버 이용료
              </h3>
              <p className="text-sm text-slate-300">
                서버(컴퓨터) 한달 이용료
              </p>
              <p className="mt-2 flex items-center gap-2">
                <span className="text-[#22c55e]">✔</span>
                <span><strong className="text-[#22c55e]">30,000원</strong></span>
              </p>
            </section>

            {/* 한달 총 정리 */}
            <section className="rounded-xl border border-slate-600/60 bg-slate-800/60 p-4">
              <h3 className="mb-3 text-sm font-semibold text-slate-200">
                한달 총 정리
              </h3>
              <ul className="mb-4 space-y-1 text-sm text-slate-300">
                <li className="flex items-center gap-2">
                  <span className="text-[#22c55e]">✔</span>
                  <span>한달 1,200개 자동포스팅</span>
                </li>
                <li className="flex items-center gap-2">
                  <span className="text-[#22c55e]">✔</span>
                  <span>내글 600개 직접 운영</span>
                </li>
              </ul>
              <div className="rounded-lg bg-slate-900/80 p-4 text-center">
                <p className="text-xs text-slate-400">총 예상 비용</p>
                <p className="mt-1 text-2xl font-bold" style={{ color: ACCENT }}>
                  55,500원
                </p>
              </div>
            </section>

            {/* 마지막 강조 */}
            <section className="rounded-xl border border-slate-600/60 bg-slate-800/60 p-4">
              <p className="text-center text-sm leading-relaxed text-slate-300">
                아이디 + 키워드 + 카페가입 설정
                <br />
                내 파트너스 링크 클릭 한번이면
                <br />
                <strong className="text-white">자동으로 포스팅 진행됩니다.</strong>
              </p>
              <p className="mt-4 text-center text-xs font-medium text-[#22c55e]">
                👉 아이디가 없으면 자동 시스템은 의미가 없습니다. 지금 준비하세요.
              </p>
            </section>
          </div>
        </div>

        <div className="flex-shrink-0 flex flex-col gap-2 border-t border-slate-700/60 p-4">
          <button
            onClick={() => {
              onStart?.();
              onClose();
            }}
            className="w-full rounded-xl py-3.5 text-sm font-semibold text-white transition"
            style={{ backgroundColor: ACCENT }}
          >
            지금 시작하기
          </button>
          <button
            onClick={onClose}
            className="w-full rounded-xl border border-slate-600 bg-slate-800/80 py-3 text-sm font-medium text-slate-300 transition hover:bg-slate-700 hover:text-white"
          >
            닫기
          </button>
        </div>
      </div>
    </div>
  );
}

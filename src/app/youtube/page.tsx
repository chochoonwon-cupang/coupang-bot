import Link from "next/link";

export default function YoutubePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 text-slate-100">
      <main className="mx-auto max-w-6xl px-4 py-8 md:px-8">
        <h1 className="text-xl font-bold text-white md:text-2xl">유튜브방송</h1>
        <p className="mt-2 text-sm text-slate-400">
          <Link href="/" className="text-indigo-400 hover:underline">← 홈으로</Link>
        </p>
      </main>
    </div>
  );
}

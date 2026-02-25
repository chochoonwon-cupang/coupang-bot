import Link from "next/link";

export default function SettingsPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900">
      <div className="text-center">
        <h1 className="text-xl font-bold text-white">설정</h1>
        <p className="mt-2 text-sm text-slate-400">
          <Link href="/" className="text-indigo-400 hover:underline">← 홈으로</Link>
        </p>
      </div>
    </div>
  );
}

import { NextResponse } from "next/server";
import { supabaseAdmin } from "@/lib/supabase";

export const runtime = "nodejs"; // (안전하게 Node 런타임 고정)

async function sleep(ms: number) {
  return new Promise((r) => setTimeout(r, ms));
}

export async function GET() {
  const ts = new Date().toISOString();
  console.log("[cron] /api/request called", ts);

  // 1) pending 1개 가져오기 (가장 오래된 것)
  const { data: job, error: pickErr } = await supabaseAdmin
    .from("job_queue")
    .select("*")
    .eq("status", "pending")
    .order("created_at", { ascending: true })
    .limit(1)
    .maybeSingle();

  if (pickErr) {
    console.error("[cron] pick error:", pickErr);
    return NextResponse.json({ ok: false, step: "pick", error: pickErr.message }, { status: 500 });
  }

  if (!job) {
    console.log("[cron] no pending job");
    return NextResponse.json({ ok: true, msg: "no pending job" });
  }

  // 2) processing으로 전환 (간단 잠금)
  const { error: lockErr } = await supabaseAdmin
    .from("job_queue")
    .update({ status: "processing", started_at: new Date().toISOString() })
    .eq("id", job.id)
    .eq("status", "pending");

  if (lockErr) {
    console.error("[cron] lock error:", lockErr);
    return NextResponse.json({ ok: false, step: "lock", error: lockErr.message }, { status: 500 });
  }

  try {
    console.log("[cron] processing job:", job.id, job.payload);

    // ✅ 여기부터 "실제 작업" 넣는 자리
    // 지금은 테스트로 1초 쉬기만 함
    await sleep(1000);

    // 3) done 처리
    const { error: doneErr } = await supabaseAdmin
      .from("job_queue")
      .update({ status: "done", finished_at: new Date().toISOString(), error: null })
      .eq("id", job.id);

    if (doneErr) throw doneErr;

    console.log("[cron] done job:", job.id);
    return NextResponse.json({ ok: true, jobId: job.id, status: "done" });
  } catch (e: any) {
    console.error("[cron] job failed:", job.id, e?.message || e);

    await supabaseAdmin
      .from("job_queue")
      .update({
        status: "error",
        finished_at: new Date().toISOString(),
        error: String(e?.message || e),
      })
      .eq("id", job.id);

    return NextResponse.json({ ok: false, jobId: job.id, status: "error" }, { status: 500 });
  }
}

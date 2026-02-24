import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { supabaseAdmin } from "@/lib/supabase";

export async function GET() {
  try {
    const cookieStore = await cookies();
    const sessionCookie = cookieStore.get("auth_session");
    if (!sessionCookie?.value) {
      return NextResponse.json({ error: "로그인이 필요합니다." }, { status: 401 });
    }

    const { data, error } = await supabaseAdmin
      .from("cafe_join_policy")
      .select("*")
      .eq("id", 1)
      .single();

    if (error && error.code !== "PGRST116") throw error;
    const row = data ?? {};
    return NextResponse.json({
      run_days: row.run_days ?? [4, 14, 24],
      start_time: row.start_time ?? "09:00",
      created_year_min: row.created_year_min ?? row.min_created_year ?? 2020,
      created_year_max: row.created_year_max ?? row.max_created_year ?? 2025,
      recent_post_days: row.recent_post_days ?? 7,
      recent_post_enabled: row.recent_post_enabled ?? row.require_no_recent_posts ?? true,
      target_count: row.target_count ?? 50,
      search_keyword: row.search_keyword ?? "",
    });
  } catch (e) {
    console.error("[API] cafe_join_policy get error:", e);
    return NextResponse.json({ error: "정책 조회 실패" }, { status: 500 });
  }
}

export async function PUT(request: Request) {
  try {
    const cookieStore = await cookies();
    const sessionCookie = cookieStore.get("auth_session");
    if (!sessionCookie?.value) {
      return NextResponse.json({ error: "로그인이 필요합니다." }, { status: 401 });
    }

    const body = await request.json();
    const run_days = Array.isArray(body.run_days) ? body.run_days.map(Number) : [4, 14, 24];
    const start_time = String(body.start_time ?? "09:00").trim() || "09:00";
    const created_year_min = Number(body.created_year_min) || 2020;
    const created_year_max = Number(body.created_year_max) || 2025;
    const recent_post_days = Number(body.recent_post_days) || 7;
    const recent_post_enabled = Boolean(body.recent_post_enabled);
    const target_count = Number(body.target_count) || 50;
    const search_keyword = String(body.search_keyword ?? "").trim();

    // 실제 DB 컬럼명(min_created_year 등) 또는 표준명 지원. search_keyword 없으면 제외 후 재시도
    const baseAlt = {
      id: 1,
      run_days,
      start_time,
      min_created_year: created_year_min,
      max_created_year: created_year_max,
      recent_post_days,
      require_no_recent_posts: recent_post_enabled,
      target_count,
      updated_at: new Date().toISOString(),
    };
    const baseStd = {
      id: 1,
      run_days,
      start_time,
      created_year_min,
      created_year_max,
      recent_post_days,
      recent_post_enabled,
      target_count,
      search_keyword,
      updated_at: new Date().toISOString(),
    };
    const { start_time: _st, ...baseStdNoTime } = baseStd;
    const payloads = [
      { ...baseAlt, search_keyword },
      baseAlt,
      baseStd,
      baseStdNoTime, // start_time 컬럼 없을 때
    ];
    let lastError: unknown = null;
    for (const payload of payloads) {
      const { error } = await supabaseAdmin
        .from("cafe_join_policy")
        .upsert(payload, { onConflict: "id" });
      if (!error) {
        return NextResponse.json({ ok: true });
      }
      lastError = error;
    }
    const errMsg = lastError && typeof lastError === "object" && "message" in lastError
      ? String((lastError as { message?: string }).message)
      : String(lastError);
    console.error("[API] cafe_join_policy put error:", errMsg);
    return NextResponse.json({ error: `정책 저장 실패: ${errMsg}` }, { status: 500 });
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    console.error("[API] cafe_join_policy put error:", e);
    return NextResponse.json({ error: `정책 저장 실패: ${msg}` }, { status: 500 });
  }
}

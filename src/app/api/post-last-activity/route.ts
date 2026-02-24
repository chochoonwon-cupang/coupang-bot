import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { supabaseAdmin } from "@/lib/supabase";

export async function GET(request: Request) {
  try {
    const cookieStore = await cookies();
    const sessionCookie = cookieStore.get("auth_session");
    if (!sessionCookie?.value) {
      return NextResponse.json({ error: "로그인이 필요합니다." }, { status: 401 });
    }
    const session = JSON.parse(sessionCookie.value);
    const username = session?.username;
    if (!username) {
      return NextResponse.json({ error: "로그인이 필요합니다." }, { status: 401 });
    }

    const { searchParams } = new URL(request.url);
    const accountsParam = searchParams.get("accounts");
    const accounts: string[] = accountsParam
      ? accountsParam.split(",").map((s) => s.trim()).filter(Boolean)
      : [username];

    if (accounts.length === 0) {
      return NextResponse.json([]);
    }

    // post_logs에서 각 program_username별 최신 created_at 조회
    const { data, error } = await supabaseAdmin
      .from("post_logs")
      .select("program_username, created_at")
      .in("program_username", accounts)
      .order("created_at", { ascending: false });

    if (error) throw error;

    // program_username별 가장 최근 created_at만 유지
    const map = new Map<string, string>();
    for (const row of data || []) {
      const un = row.program_username;
      if (un && !map.has(un)) {
        map.set(un, row.created_at);
      }
    }

    const result = accounts.map((un) => ({
      program_username: un,
      last_job_at: map.get(un) || null,
    }));
    return NextResponse.json(result);
  } catch (e) {
    console.error("[API] post_last_activity error:", e);
    return NextResponse.json(
      { error: "마지막 활동 조회 실패" },
      { status: 500 }
    );
  }
}

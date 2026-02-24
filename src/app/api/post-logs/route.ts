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
    const account = searchParams.get("account")?.trim() || username;

    const { data, error } = await supabaseAdmin
      .from("post_logs")
      .select("id, keyword, post_type, partner_id, posting_url, created_at")
      .eq("program_username", account)
      .order("created_at", { ascending: false })
      .limit(200);

    if (error) throw error;

    const rows = (data || []).map((row: { id: string; keyword: string; post_type?: string; partner_id?: string | null; posting_url: string | null; created_at: string }) => ({
      id: row.id,
      keyword: row.keyword,
      post_type: row.post_type || "self",
      partner_id: row.partner_id || null,
      status: "완료",
      posting_url: row.posting_url || null,
      created_at: row.created_at,
    }));
    return NextResponse.json(rows);
  } catch (e) {
    console.error("[API] post_logs fetch error:", e);
    return NextResponse.json(
      { error: "포스팅 로그를 불러오지 못했습니다." },
      { status: 500 }
    );
  }
}

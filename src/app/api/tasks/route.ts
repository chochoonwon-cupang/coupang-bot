import { NextResponse } from "next/server";
import { getSupabaseAdmin } from "@/lib/supabase";

export async function GET() {
  try {
    const supabaseAdmin = getSupabaseAdmin();
    const { data, error } = await supabaseAdmin
      .from("tasks")
      .select("id, keyword, status, result_url, error_message, created_at, updated_at")
      .order("created_at", { ascending: false })
      .limit(100);

    if (error) throw error;
    return NextResponse.json(data);
  } catch (e) {
    console.error("[API] tasks fetch error:", e);
    return NextResponse.json(
      { error: "작업 목록을 불러오지 못했습니다." },
      { status: 500 }
    );
  }
}

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const keyword = (body.keyword || "").trim();
    if (!keyword) {
      return NextResponse.json(
        { error: "키워드를 입력해주세요." },
        { status: 400 }
      );
    }

    const supabaseAdmin = getSupabaseAdmin();
    const { data, error } = await supabaseAdmin
      .from("tasks")
      .insert({ keyword, status: "pending" })
      .select("id, keyword, status, created_at")
      .single();

    if (error) throw error;
    return NextResponse.json(data);
  } catch (e) {
    console.error("[API] tasks insert error:", e);
    return NextResponse.json(
      { error: "작업 등록에 실패했습니다." },
      { status: 500 }
    );
  }
}

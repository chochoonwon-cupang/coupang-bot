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
    const ownerUserId = session?.id;
    const username = session?.username;
    if (!ownerUserId || !username) {
      return NextResponse.json({ error: "로그인이 필요합니다." }, { status: 401 });
    }

    const { searchParams } = new URL(request.url);
    const account = searchParams.get("account")?.trim() || username;

    const { data, error } = await supabaseAdmin
      .from("agent_configs")
      .select("config")
      .eq("owner_user_id", ownerUserId)
      .eq("program_username", account)
      .single();

    if (error && error.code !== "PGRST116") throw error;
    return NextResponse.json(data?.config ?? {});
  } catch (e) {
    console.error("[API] agent_configs get error:", e);
    return NextResponse.json(
      { error: "설정 조회 실패" },
      { status: 500 }
    );
  }
}

export async function PUT(request: Request) {
  try {
    const cookieStore = await cookies();
    const sessionCookie = cookieStore.get("auth_session");
    if (!sessionCookie?.value) {
      return NextResponse.json({ error: "로그인이 필요합니다." }, { status: 401 });
    }
    const session = JSON.parse(sessionCookie.value);
    const ownerUserId = session?.id;
    const username = session?.username;
    if (!ownerUserId || !username) {
      return NextResponse.json({ error: "로그인이 필요합니다." }, { status: 401 });
    }

    const body = await request.json();
    const programUsername = (body.program_username ?? username).trim() || username;
    const config = body.config ?? {};

    if (!programUsername) {
      return NextResponse.json({ error: "선택된 아이디가 없습니다." }, { status: 400 });
    }

    const updatedAt = new Date().toISOString();
    const { data, error } = await supabaseAdmin
      .from("agent_configs")
      .upsert(
        {
          owner_user_id: ownerUserId,
          program_username: programUsername,
          config,
          updated_at: updatedAt,
        },
        { onConflict: "owner_user_id,program_username" }
      )
      .select();

    if (error) {
      console.error("[API] agent_configs upsert error:", error);
      return NextResponse.json(
        {
          error: "설정 저장 실패",
          message: error.message,
          details: error.details,
        },
        { status: 500 }
      );
    }
    return NextResponse.json({ ok: true, updated_at: updatedAt });
  } catch (e) {
    console.error("[API] agent_configs upsert error:", e);
    return NextResponse.json(
      { error: "설정 저장 실패", message: String(e) },
      { status: 500 }
    );
  }
}

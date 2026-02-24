import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { supabaseAdmin } from "@/lib/supabase";

export async function POST(request: Request) {
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

    const { command, payload } = body;
    if (!command) {
      return NextResponse.json({ error: "command가 필요합니다." }, { status: 400 });
    }

    // command는 항상 문자열만 저장 (apply_config, start, stop, restart 등)
    const commandStr = typeof command === "string" ? command : String(command);
    const payloadObj = payload ?? {};

    const { error } = await supabaseAdmin
      .from("agent_commands")
      .insert({
        owner_user_id: ownerUserId,
        program_username: programUsername,
        command: commandStr,
        payload: payloadObj,
        status: "pending",
      });

    if (error) {
      console.error("[API] agent_commands insert error:", error);
      return NextResponse.json(
        { error: "명령 전송 실패", message: error.message, details: error.details },
        { status: 500 }
      );
    }
    return NextResponse.json({ ok: true });
  } catch (e) {
    console.error("[API] agent_commands insert error:", e);
    return NextResponse.json(
      { error: "명령 전송 실패", message: String(e) },
      { status: 500 }
    );
  }
}

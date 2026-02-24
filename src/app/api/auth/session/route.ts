import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { supabaseAdmin } from "@/lib/supabase";

export async function GET() {
  try {
    const cookieStore = await cookies();
    const sessionCookie = cookieStore.get("auth_session");
    if (!sessionCookie?.value) {
      return NextResponse.json({ ok: false, user: null });
    }
    const session = JSON.parse(sessionCookie.value);
    if (!session?.id || !session?.username) {
      return NextResponse.json({ ok: false, user: null });
    }

    // managed_usernames 조회 (users 테이블)
    try {
      const { data: row } = await supabaseAdmin
        .from("users")
        .select("managed_usernames")
        .eq("id", session.id)
        .single();
      const managed = (row?.managed_usernames ?? "")
        .split(",")
        .map((s: string) => s.trim())
        .filter(Boolean);
      return NextResponse.json({
        ok: true,
        user: { ...session, managed_usernames: managed },
      });
    } catch {
      return NextResponse.json({
        ok: true,
        user: { ...session, managed_usernames: [] },
      });
    }
  } catch {
    return NextResponse.json({ ok: false, user: null });
  }
}

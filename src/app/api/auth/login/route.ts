import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { createHash, timingSafeEqual } from "crypto";
import { supabaseAdmin } from "@/lib/supabase";

function verifyPassword(password: string, stored: string): boolean {
  if (!stored || !stored.includes(":")) return false;
  const [salt, hash] = stored.split(":", 2);
  const computed = createHash("sha256")
    .update(salt + password)
    .digest("hex");
  if (hash.length !== computed.length) return false;
  try {
    return timingSafeEqual(
      Buffer.from(hash, "hex"),
      Buffer.from(computed, "hex")
    );
  } catch {
    return false;
  }
}

export async function POST(request: Request) {
  try {
    const url = process.env.SUPABASE_URL || process.env.NEXT_PUBLIC_SUPABASE_URL;
    const key = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.SUPABASE_SERVICE_KEY;
    if (!url || !key) {
      return NextResponse.json(
        {
          error:
            "서버 설정 오류: .env.local에 SUPABASE_URL, SUPABASE_SERVICE_KEY(또는 SUPABASE_SERVICE_ROLE_KEY)를 설정하세요.",
        },
        { status: 500 }
      );
    }

    const body = await request.json();
    const username = (body.username || "").trim();
    const password = (body.password || "").trim();

    if (!username || !password) {
      return NextResponse.json(
        { error: "아이디와 비밀번호를 입력하세요." },
        { status: 400 }
      );
    }

    const { data: rows, error } = await supabaseAdmin
      .from("users")
      .select("id, username, password_hash, free_use_until")
      .eq("username", username)
      .limit(1);

    if (error) throw error;
    if (!rows || rows.length === 0) {
      return NextResponse.json(
        { error: "아이디 또는 비밀번호가 올바르지 않습니다." },
        { status: 401 }
      );
    }

    const row = rows[0];
    if (!verifyPassword(password, row.password_hash || "")) {
      return NextResponse.json(
        { error: "아이디 또는 비밀번호가 올바르지 않습니다." },
        { status: 401 }
      );
    }

    // 사용 기간 체크 (메인 프로그램과 동일)
    const freeUntil = row.free_use_until || "";
    if (freeUntil) {
      try {
        const end = new Date(String(freeUntil).slice(0, 10));
        if (new Date() > end) {
          return NextResponse.json(
            { error: "사용 가능 기간이 만료되었습니다." },
            { status: 403 }
          );
        }
      } catch {
        // ignore
      }
    }

    const session = {
      id: row.id,
      username: row.username,
    };

    const cookieStore = await cookies();
    cookieStore.set("auth_session", JSON.stringify(session), {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      maxAge: 60 * 60 * 24 * 7, // 7일
      path: "/",
    });

    return NextResponse.json({ ok: true, user: session });
  } catch (e) {
    console.error("[API] login error:", e);
    return NextResponse.json(
      { error: "로그인 처리 중 오류가 발생했습니다." },
      { status: 500 }
    );
  }
}
